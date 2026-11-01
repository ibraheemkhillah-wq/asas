"""Open-km reel, final: key ignition -> office launch -> continuous zoom-out (photo -> satellite -> map) -> red route,
map/place alternation over 4 stops -> red ∞ with big logo + contacts entering under it (no box)."""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import zoomdemo as Z
import mapboard3 as MB, boards as BD
import tiles
from mapboard3 import W,H,F,B,OR,NAVY,RED,OFFICE,STOPS
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
FPS=24
def ramp(t,a,b): return float(np.clip((t-a)/(b-a),0,1))
def ease(x): return 1-(1-x)**3
def eio(x): return x*x*(3-2*x)
def faded(L,a):
    if a>=1: return L
    L=L.copy(); L.putalpha(L.split()[3].point(lambda v:int(v*a))); return L

# ---------------- clips ----------------
CL={'key':'1-key','office':'2-office-clean','forest':'3-forest','sile':'4-sile','sapanca':'5-sapanca','uludag':'6-uludag'}
NFR={k:len(os.listdir(f'../hf/fr_{v}')) for k,v in CL.items()}
def clip(k,ct):
    i=int(np.clip(round(ct*FPS),0,NFR[k]-1))+1
    return Image.open(f'../hf/fr_{CL[k]}/{i:04d}.jpg').convert('RGBA')
def scaled(im,s,cx=W/2,cy=H/2):
    if abs(s-1)<1e-3: return im
    w,h=W/s,H/s; return im.resize((W,H),Image.BICUBIC,box=(cx-w/2,cy-h/2,cx+w/2,cy+h/2))

# ---------------- timeline (s) ----------------
K0,K1,KOFF=0.0,3.5,0.4               # key clip 0.4..3.9 (engine catches at 2.25)
O0,OOFF,OSPD=K1,1.9,1.3   # 1.3x faster launch;                     # office clip from 1.9 s: no unlock blink / engine thump, lights pop on, car pulls away at 2.4 s
O1=O0+(9.3-OOFF)/OSPD
Z0,Z1=O1,O1+6.6                      # zoom-out
MAP_D=1.5
PLACES=[('forest','غابة بلغراد',0.6,3.4),('sile','شيلي',0.8,3.4),('sapanca','بحيرة سابانجا',0.6,2.4),('uludag','بورصة · أولوداغ',0.0,5.0)]
SEGS=[]; m0=Z1
for i,(k,lbl,off,d) in enumerate(PLACES):
    SEGS.append((m0,m0+MAP_D,m0+MAP_D,m0+MAP_D+d,k,lbl,off)); m0+=MAP_D+d
F0=SEGS[-1][3]; DUR=F0+6.0; N=int(round(DUR*FPS))

# ---------------- map camera ----------------
def wpx(lat,lon): return tiles.ll2px(lat,lon,0)
TC={}
def tile_img(kind,z,x,y):
    k=(kind,z,x,y)
    if k not in TC: TC[k]=Z.sat_tile(z,x,y) if kind=='sat' else Z.map_tile(z,x,y)
    return TC[k]
def view(kind,cw,zf):
    zi=min(int(round(zf)),18 if kind=='sat' else 16); s=2**(zf-zi)
    cx,cy=cw[0]*2**zi,cw[1]*2**zi; w,h=W/s,H/s; x0,y0=cx-w/2,cy-h/2
    tx0,ty0,tx1,ty1=int(x0//256),int(y0//256),int((x0+w)//256),int((y0+h)//256)
    big=Image.new('RGB',((tx1-tx0+1)*256,(ty1-ty0+1)*256))
    for tx in range(tx0,tx1+1):
        for ty in range(ty0,ty1+1): big.paste(tile_img(kind,zi,tx,ty),((tx-tx0)*256,(ty-ty0)*256))
    ox,oy=x0-tx0*256,y0-ty0*256
    return big.resize((W,H),Image.BICUBIC,box=(ox,oy,ox+w,oy+h)).convert('RGBA')
def projector(cw,zf):
    k=2**zf
    def P(lat,lon):
        x,y=wpx(lat,lon); return (x-cw[0])*k+W/2,(y-cw[1])*k+H/2
    return P
OFF_W=wpx(*OFFICE); REG_W=wpx(40.70,29.47); ZREG=10-math.log2(1320/1080)
FIN_W=wpx(40.38,29.49)
def lerpw(a,b,u): return (a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)
def dive_cam(stop_ll,dz):
    """camera zoomed by dz above the region view, keeping the stop fixed on screen"""
    sw=wpx(*stop_ll); s=2**dz; return (sw[0]-(sw[0]-REG_W[0])/s, sw[1]-(sw[1]-REG_W[1])/s), ZREG+dz
SAT_ATTR='Esri, Maxar, Earthstar Geographics'
def attribution(fr,sat=False):
    return
    ImageDraw.Draw(fr).text((24,H-24),SAT_ATTR if sat else MB.ATTR,font=F(B.LT_TEXT,20),fill=(235,235,235) if sat else (140,150,160),anchor='ls')
def layer(fn):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); fn(L); return L
T_START=layer(lambda L:BD.text(L,'من هنا تبدأ الرحلة',300,76,NAVY))
T_GO=layer(lambda L:BD.text(L,'مسار لا يتوقف',300,76,NAVY))
def show(fr,L,a,rise=18):
    if a<=0: return
    fr.alpha_composite(faded(L,a),(0,int(rise*(1-a))))

# ---------------- route map ----------------
def route_pts(P,n_done,frac,ret=0.0):
    pts=MB.route(P,n_done+1,frac) if frac>0 else MB.route(P,n_done,1.0)
    if ret>0:
        a=P(*STOPS[-1][1:]); b=P(*OFFICE); mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2; nx,ny=-(b[1]-a[1]),(b[0]-a[0]); cx,cy=mx+nx*0.18,my+ny*0.18
        pts=pts+[((1-u)**2*a[0]+2*(1-u)*u*cx+u*u*b[0],(1-u)**2*a[1]+2*(1-u)*u*cy+u*u*b[1]) for u in np.linspace(0,ret,max(2,int(80*ret)))]
    return pts
def draw_route(fr,pts,alpha=1.0):
    if len(pts)<2 or alpha<=0: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); sh=Image.new('RGBA',(W,H),(0,0,0,0))
    ImageDraw.Draw(sh).line(pts,fill=RED+(90,),width=30,joint='curve'); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(L).line(pts,fill=RED+(255,),width=11,joint='curve'); fr.alpha_composite(faded(L,alpha))
def map_frame(cw,zf,n_done,frac,ret=0.0,route_a=1.0,head=True,pins_a=1.0,labels_a=1.0):
    fr=view('map',cw,zf); P=projector(cw,zf)
    if labels_a>0: L=Image.new('RGBA',(W,H),(0,0,0,0)); MB.labels(L,P,('sea',)); fr.alpha_composite(faded(L,labels_a))
    pts=route_pts(P,n_done,frac,ret); draw_route(fr,pts,route_a)
    reached=n_done+(1 if frac>=1 else 0)
    if pins_a>0:
        L=Image.new('RGBA',(W,H),(0,0,0,0))
        for nm,la,lo in STOPS[:reached]:
            x,y=P(la,lo); MB.stop_pin(L,x,y,nm,below=nm=='سابانجا')
        fr.alpha_composite(faded(L,pins_a))
    x,y=P(*OFFICE); MB.office_pin(fr,x,y,0.8,label=False)
    if head and len(pts)>1 and 0<frac<1 and route_a>0: x,y=pts[-1]; ImageDraw.Draw(fr).ellipse((x-24,y-24,x+24,y+24),fill=(255,255,255),outline=RED,width=9)
    return fr,P

# ---------------- zoom-out (local time u) ----------------
OFFICE_LAST=None
def zoom_frame(u):
    global OFFICE_LAST
    if OFFICE_LAST is None: OFFICE_LAST=clip('office',OOFF+(O1-O0)*OSPD-1/FPS)
    zf=18-7.7*eio(ramp(u,1.0,5.2))
    k1=math.sin(math.pi*ramp(u,0.35,1.9)); k2=0.75*math.sin(math.pi*ramp(u,1.95,3.1)); k=max(k1,k2)
    if u<5.2:
        cw=OFF_W; z=zf
        sat=view('sat',cw,max(z,15.0)) if z>15.0 else None
        m=view('map',cw,z) if z<16.2 else None
        mix=ramp(z,15.4,16.0)
        fr=sat if m is None else (m if (sat is None or mix<=0) else Image.blend(m,sat,mix))
        if u<1.6:                                              # the last office frame shrinks away into the satellite view
            s=1-0.4*eio(ramp(u,0,1.6)); a=1-ramp(u,0.85,1.45)
            im=OFFICE_LAST.resize((int(W*s),int(H*s)),Image.BICUBIC)
            fe=int(90*ramp(u,0.1,0.9))                         # edges feather away as it shrinks
            if fe>2:
                mk=Image.new('L',im.size,0); ImageDraw.Draw(mk).rectangle((fe,fe,im.width-fe,im.height-fe),fill=255); im.putalpha(mk.filter(ImageFilter.GaussianBlur(fe/2)))
            L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(im,(int((W-W*s)/2),int((H-H*s)/2)))
            fr.alpha_composite(faded(L,a))
        P=projector(cw,z)
    else:                                                      # glide from the office to the whole region
        a=eio(ramp(u,5.2,6.6)); cw=lerpw(OFF_W,REG_W,a); z=10.3+(ZREG-10.3)*a
        fr=view('map',cw,z); P=projector(cw,z)
        L=Image.new('RGBA',(W,H),(0,0,0,0)); MB.labels(L,P,('sea',)); fr.alpha_composite(faded(L,a))
    fr=Z.clouds(fr,k,u)
    if zf<16.6:
        x,y=P(*OFFICE); pa=ease(ramp(zf,16.6,16.1)); s=(0.9+0.3*ramp(zf,12,16))*(0.6+0.4*pa)
        if u>5.2: s=1.0-0.2*eio(ramp(u,5.2,6.6))
        L=Image.new('RGBA',(W,H),(0,0,0,0)); MB.office_pin(L,x,y,s,label=u<5.6); fr.alpha_composite(faded(L,pa))
    show(fr,T_START,ease(ramp(u,3.8,4.2))*(1-ramp(u,5.6,6.1)))
    attribution(fr,sat=zf>15.7)
    return fr

# ---------------- places ----------------
def pill(fr,label,a):
    if a<=0: return fr
    p=fr.copy(); ww=BD.tw(label,F(B.AR_BLACK,70))+140; x0=(W-ww)//2
    BD.frosted(p,(x0,140,x0+ww,270),r=60,k=0.85); BD.text(p,label,205,70,NAVY)
    if a<1:
        sh=int(16*(1-a)); p=Image.blend(fr,p,a)
    return p

# ---------------- finale (local time v from F0) ----------------
LOGO=Image.open(B.LOGO_NAVY).convert('RGBA'); LW=700; LOGO=LOGO.resize((LW,int(LW*LOGO.height/LOGO.width)),Image.LANCZOS)
def contacts_big(y,col=NAVY):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); fc=F(B.CT_FONT,54); d=ImageDraw.Draw(L); isz=56
    ic={k:BD.tint(Image.fromarray((np.asarray(v,np.float32)[...,3]*np.asarray(v.convert('L'),np.float32)/255).astype('uint8')),col) for k,v in B.load_icons(isz).items()}
    items=[(('ig','fb'),'callrenttr'),(('wa','ph'),'+90 555 034 22 00')]
    out=[]
    for keys,t in items:
        w=len(keys)*(isz+10)+8+d.textbbox((0,0),t,font=fc)[2]; out.append((keys,t,w))
    return L,out,fc,ic,isz
def contact_layer(y,keys,t,fc,ic,isz,col=NAVY):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    w=len(keys)*(isz+10)+8+d.textbbox((0,0),t,font=fc)[2]; x=(W-w)/2
    for k in keys: L.alpha_composite(ic[k],(int(x),int(y-isz/2))); x+=isz+10
    d.text((x+8,y),t,font=fc,fill=col+(255,),anchor='lm')
    g=Image.new('RGBA',(W,H),(255,255,255,0)); g.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.8)))
    out=Image.new('RGBA',(W,H),(0,0,0,0)); out.alpha_composite(g); out.alpha_composite(L); return out
_, CITEMS, CFONT, CICONS, CISZ = contacts_big(0)
LOGO_Y=1150
C_LAYERS=[contact_layer(1500,k,t,CFONT,CICONS,CISZ) for k,t,_ in CITEMS[:1]]+[contact_layer(1600,k,t,CFONT,CICONS,CISZ) for k,t,_ in CITEMS[1:]]
NOTE=layer(lambda L:BD.text(L,'خدمة العداد المفتوح وفق الشروط والأحكام',1700,30,(90,105,125),F('NotoKufiArabic-Regular.ttf',30)))
T_END1=layer(lambda L:BD.text(L,'رحــلـة بـلا نـهايـة',150,92,NAVY))
T_END2=layer(lambda L:BD.text(L,'عداد مفتوح',262,60,OR,F(B.AR_BOLD,60)))
def bottom_wash(fr,a):
    y=np.arange(H); wm=(np.clip((y-960)/280,0,1)**1.3*228)*a
    w=Image.new('RGBA',(W,H),(255,255,255,0)); w.putalpha(Image.fromarray(np.repeat(wm[:,None],W,1).astype('uint8'))); fr.alpha_composite(w)
def logo_in(fr,a):
    if a<=0: return
    s=0.86+0.14*ease(a); lg=LOGO.resize((int(LW*s),int(LOGO.height*s)),Image.LANCZOS)
    b=(1-ease(min(1,a*1.3)))*10
    if b>0.3: lg=lg.filter(ImageFilter.GaussianBlur(b))
    y=LOGO_Y+int(46*(1-ease(a)))+int((LOGO.height-lg.height)/2)
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(lg,(int((W-lg.width)/2),y)); fr.alpha_composite(faded(L,min(1,a*1.6)))
def finale_frame(v):
    # 0..0.5 pull out of Bursa ; 0.35..1.1 return leg ; 1.1..2.4 ∞ draws while the camera drifts down ; 2.3.. titles ; 2.7.. logo ; 3.2.. contacts
    if v<0.5:
        cw,zf=dive_cam(STOPS[-1][1:],1.3*(1-eio(ramp(v,0,0.5))))
    else:
        a=eio(ramp(v,1.0,2.6)); cw=lerpw(REG_W,FIN_W,a); zf=ZREG
    ret=eio(ramp(v,0.35,1.1)); k=ease(ramp(v,1.1,2.4))
    fr,P=map_frame(cw,zf,4,0,ret=ret,route_a=1-min(1,k*1.5),head=False,pins_a=1-min(1,k*1.2),labels_a=1-ramp(v,1.9,2.4))
    if ret<1 and v>0.35: x,y=route_pts(P,4,0,ret)[-1]; ImageDraw.Draw(fr).ellipse((x-24,y-24,x+24,y+24),fill=(255,255,255),outline=RED,width=9)
    if k>0:
        xs=[P(la,lo)[0] for _,la,lo in STOPS]+[P(*OFFICE)[0]]; ys=[P(la,lo)[1] for _,la,lo in STOPS]+[P(*OFFICE)[1]]
        cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2; rx=(max(xs)-min(xs))/2+60
        th=np.linspace(np.pi/2,np.pi/2+2*np.pi*k,max(2,int(420*k))); den=1+np.sin(th)**2
        p=[(cx+rx*np.cos(t)/q, cy+rx*0.85*np.sin(t)*np.cos(t)/q) for t,q in zip(th,den)]
        L=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(L).line(p,fill=RED+(255,),width=20,joint='curve')
        tt=max(0,v-2.4); glow=1.0+0.6*np.exp(-tt*3)*ramp(v,2.35,2.4)+0.12*np.sin(tt*4)
        g=Image.new('RGBA',(W,H),(255,90,90,0)); g.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(30)).point(lambda q,gg=glow:int(min(255,q*gg)))); fr.alpha_composite(g); fr.alpha_composite(L)
        if k<1: x,y=p[-1]; ImageDraw.Draw(fr).ellipse((x-24,y-24,x+24,y+24),fill=(255,255,255),outline=RED,width=9)
        x,y=P(*OFFICE); MB.office_pin(fr,x,y,0.8,label=False)
    wa=ease(ramp(v,2.2,2.8))
    if wa>0:
        p2=fr.copy(); BD.top_wash(p2,430,225); fr=Image.blend(fr,p2,wa)
    show(fr,T_END1,ease(ramp(v,2.3,2.75))); show(fr,T_END2,ease(ramp(v,2.55,3.0)))
    bottom_wash(fr,ease(ramp(v,2.5,3.1)))
    logo_in(fr,ramp(v,2.7,3.45))
    for i,L in enumerate(C_LAYERS): show(fr,L,ease(ramp(v,3.2+0.15*i,3.65+0.15*i)),rise=30)
    show(fr,NOTE,ease(ramp(v,3.6,4.0)),rise=10)
    attribution(fr); return fr

# ---------------- headlights switching on (first 0.7 s of the exterior) ----------------
HL_BOXES=[(370,1370,625,1530),(88,1355,165,1465)]
def lights_on(fr,u):
    if u>0.7: return fr
    a=np.asarray(fr.convert('RGB'),np.float32).copy(); k=ease(ramp(u,0.16,0.3))
    glow=np.zeros(a.shape[:2],np.float32)
    for x0,y0,x1,y1 in HL_BOXES:
        reg=a[y0:y1,x0:x1]; m=np.clip((reg.mean(2)-150)/60,0,1)
        a[y0:y1,x0:x1]=reg*(1-m*0.78*(1-k))[...,None]
        glow[y0:y1,x0:x1]=m
    inten=k*(0.25+0.9*np.exp(-max(0,u-0.3)*7))*(1-ramp(u,0.5,0.7))
    if inten>0.01:
        g=np.asarray(Image.fromarray((glow*255).astype('uint8')).filter(ImageFilter.GaussianBlur(22)),np.float32)/255*inten
        a=a+g[...,None]*np.array([235,242,255],np.float32)*1.4
    return Image.fromarray(np.clip(a,0,255).astype('uint8')).convert('RGBA')

# ---------------- render ----------------
def place_clip_frame(i,t):
    m0,m1,p0,p1,k,lbl,off=SEGS[i]; u=ramp(t,p0,p1)
    return scaled(clip(k,off+(t-p0)),1.0+0.04*eio(u))
def render(f):
    t=f/FPS
    if t<K1: fr=clip('key',KOFF+t)
    elif t<O1: fr=lights_on(clip('office',OOFF+(t-O0)*OSPD),t-O0)
    elif t<Z1: fr=zoom_frame(t-Z0)
    elif t<F0:
        for i,(m0,m1,p0,p1,k,lbl,off) in enumerate(SEGS):
            if t<m1:                                            # map leg to stop i
                if i>0 and t<m0+0.5: cw,zf=dive_cam(STOPS[i-1][1:],1.3*(1-eio(ramp(t,m0,m0+0.5))))
                elif t>m1-0.3: cw,zf=dive_cam(STOPS[i][1:],1.4*ramp(t,m1-0.3,m1)**2)
                else: cw,zf=REG_W,ZREG
                frac=eio(ramp(t,m0+(0.4 if i>0 else 0.1),m1-0.35))
                fr,_=map_frame(cw,zf,i,max(0.001,frac))
                if i==2: show(fr,T_GO,ease(ramp(t,m0+0.4,m0+0.7)))
                attribution(fr)
                if i>0 and t<m0+0.25:                           # out of the previous place
                    prev=place_clip_frame(i-1,SEGS[i-1][3]); fr=Image.blend(prev,fr,eio(ramp(t,m0,m0+0.25)))
                break
            if t<p1:                                            # place
                fr=place_clip_frame(i,t)
                if t<p0+0.3:
                    a=ramp(t,p0,p0+0.3); cw,zf=dive_cam(STOPS[i][1:],1.4+0.8*a); mp,_=map_frame(cw,zf,i,1.0); attribution(mp)
                    fr=Image.blend(mp,scaled(fr,1.12-0.12*ease(a)),ease(a))
                fr=pill(fr,lbl,ease(ramp(t,p0+0.3,p0+0.7)))
                break
    else:
        v=t-F0; fr=finale_frame(v)
        if v<0.3: fr=Image.blend(place_clip_frame(3,F0),fr,eio(ramp(v,0,0.3)))
    return fr.convert('RGB')

# ---------------- sound ----------------
SR=48000
def aload(FF,fn,ss=None,d=None,af=None):
    cmd=[FF,'-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-t',str(d)] if d else [])+['-i',fn]+(['-af',af] if af else [])+['-ac','2','-ar',str(SR),'-f','s16le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,'<i2').reshape(-1,2).astype(np.float32)/32768
def lvl(x,r): return x/(np.sqrt((x**2).mean())+1e-9)*r
def pk(x,r): return x/(np.abs(x).max()+1e-9)*r
def tone(f0,dur,decay,parts=(1,2,3.01)):
    tt=np.arange(int(dur*SR))/SR; x=sum(np.sin(2*np.pi*f0*m*tt)*np.exp(-tt*(decay+m))/m for m in parts)*np.minimum(1,tt/0.008)
    x=x/np.abs(x).max(); return np.stack([x,x],1).astype(np.float32)
def noise(dur,lp=400,seed=0):
    x=np.random.default_rng(seed).normal(0,1,int(dur*SR)); k=max(1,int(SR/lp)); x=np.convolve(x,np.ones(k)/k,'same'); x=x/np.abs(x).max(); return np.stack([x,x],1).astype(np.float32)
def sound(FF):
    Nn=int(DUR*SR); out=np.zeros((Nn,2),np.float32)
    def place(x,t,g,fin=0.0,fade=0.0,dur=None):
        x=x.copy()
        if dur: x=x[:int(dur*SR)]
        if fin: k=min(len(x),int(fin*SR)); x[:k]*=np.linspace(0,1,k)[:,None]
        if fade: k=min(len(x),int(fade*SR)); x[-k:]*=np.linspace(1,0,k)[:,None]
        s=int(t*SR); n=min(len(x),Nn-s)
        if n>0: out[s:s+n]+=x[:n]*g
    S='sfx/'; H_='../hf/'
    m=lvl(aload(FF,'../seat/snd/m_180.mp3',0,DUR),0.028); kk=np.minimum(1,np.arange(len(m))/SR/2.5)*np.clip((DUR-np.arange(len(m))/SR)/2.0,0,1); place(m*kk[:,None],0,1.0)
    # native, motion-synced clip audio: key clicks + engine start, unlock chirps + engine + drive-off
    place(pk(aload(FF,H_+'1-key.mp4',KOFF,K1-K0+0.15),0.55),K0,1.0,fade=0.2)
    place(pk(aload(FF,H_+'2-office-clean.mp4',0.3,9.3,af=f'atempo={OSPD}'),0.6)[int((OOFF-0.3)/OSPD*SR):],O0-0.05,1.0,fin=0.15,fade=1.0)
    # zoom-out: air rising, birds below, pin pop, title tick
    nz=noise(6.6,180,1); tt=np.arange(len(nz))/SR
    env=(0.25+0.75*np.sin(np.pi*np.clip((tt-0.35)/1.55,0,1))+0.6*np.sin(np.pi*np.clip((tt-1.95)/1.15,0,1)))*np.clip(tt/0.6,0,1)*np.clip((6.6-tt)/1.5,0,1)
    place(lvl(nz,0.05)*env[:,None],Z0,1.0)
    place(tone(880,0.35,14,(1,2)),Z0+2.3,0.05); place(tone(1320,0.25,20,(1,)),Z0+3.85,0.03)
    for i,(m0,m1,p0,p1,k,lbl,off) in enumerate(SEGS):
        place(tone(1046,0.9,6),m1-0.35,0.05)
        PL_D=p1-p0; fi,fo=min(0.8,PL_D*0.3),min(0.9,PL_D*0.35)
        car=aload(FF,H_+CL[k]+'.mp4',off,PL_D,af='lowpass=f=700,acompressor=threshold=0.05:ratio=4:attack=20:release=300')
        place(lvl(car,0.003 if k=='sile' else 0.006),p0,1.0,fin=fi,fade=fo)                                              # the car on the road: barely there
        if k=='sile': place(lvl(aload(FF,S+'s1194.mp3',10,PL_D,af='lowpass=f=2500'),0.016),p0,1.0,fin=fi,fade=fo)   # waves, soft
        elif k=='sapanca': place(lvl(aload(FF,S+'s1194.mp3',30,PL_D),0.015),p0,1.0,fin=fi,fade=fo)    # soft lake water
        elif k=='forest': place(lvl(noise(PL_D+0.2,500,7),0.01),p0,1.0,fin=fi,fade=fo)                # leaves in the wind
        else: place(lvl(noise(PL_D+0.3,450,5),0.016),p0,1.0,fin=fi,fade=fo)                           # mountain wind
    place(tone(784,2.4,2.2),F0+2.4,0.08); place(tone(1175,2.0,2.8),F0+2.45,0.045)
    place(tone(523,2.2,2.0,(1,2)),F0+2.75,0.05)                                          # logo lands
    mx=np.abs(out).max(); out=out/mx*0.95 if mx>0.95 else out
    with wave.open('fmix.wav','wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out,-1,1)*32767).astype('<i2').tobytes())
    subprocess.run([FF,'-v','error','-y','-i','fmix.wav','-af','loudnorm=I=-15:TP=-1.0:LRA=9','-ar','48000','fmix_n.wav'],check=True)
def chunk(FF,a,b):
    os.makedirs('fchunks',exist_ok=True)
    p=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','fast','-crf','10','-pix_fmt','yuv420p',f'fchunks/{a:05d}.mp4'],stdin=subprocess.PIPE)
    for f in range(a,b): p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
def encode(FF,out,kbps):
    with open('fchunks/list.txt','w') as fh:
        for fn in sorted(x for x in os.listdir('fchunks') if x.endswith('.mp4')): fh.write(f"file '{fn}'\n")
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i','fchunks/list.txt','-c','copy','fall.mp4'],check=True)
    for p in (1,2):
        cmd=[FF,'-v','error','-y','-i','fall.mp4','-i','fmix_n.wav','-map','0:v','-map','1:a','-c:v','libx264','-b:v',f'{kbps}k','-maxrate',f'{int(kbps*1.6)}k','-bufsize',f'{kbps*2}k',
             '-preset','veryslow','-tune','film','-pix_fmt','yuv420p','-pass',str(p),'-passlogfile','x264fin']
        cmd+=(['-an','-f','mp4','/dev/null'] if p==1 else ['-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out])
        subprocess.run(cmd,check=True)
if __name__=='__main__':
    import imageio_ffmpeg; FF=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=sys.argv[1] if len(sys.argv)>1 else ''
    if cmd=='info': print('DUR',DUR,'N',N,'SEGS',SEGS,'F0',F0)
    elif cmd=='prefetch':
        for f in range(int(Z0*FPS),N,3): render(f)
        print('prefetched')
    elif cmd=='chunk': chunk(FF,int(sys.argv[2]),min(N,int(sys.argv[3])))
    elif cmd=='sound': sound(FF); print('mixed')
    elif cmd=='encode': encode(FF,sys.argv[2],int(sys.argv[3])); print('encoded')
    elif cmd=='check':
        ts=[float(x) for x in sys.argv[2:]]; fr=[render(int(t*FPS)).resize((270,480)) for t in ts]
        s=Image.new('RGB',(270*len(fr),480))
        for i,im in enumerate(fr): s.paste(im,(270*i,0))
        s.save('final_chk.jpg'); print('ok')
