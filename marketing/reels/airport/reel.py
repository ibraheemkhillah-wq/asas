"""Airport pick-up reel «المفتاح على السير» — final edit (26.5 s, 24 fps), rendered once, muxed with three music beds."""
import sys, os, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import sb
from sb import W,H,F,B,OR,WHITE,MUTED,text,shade,logo,contacts
FPS=24
def ramp(t,a,b): return float(np.clip((t-a)/(b-a),0,1))
def ease(x): return 1-(1-x)**3
def faded(L,a):
    if a>=1: return L
    L=L.copy(); L.putalpha(L.split()[3].point(lambda v:int(v*a))); return L
NF={c:len(os.listdir(f'clips/x{c}')) for c in ('1v2','2','3','4','5','6v2','7')}
def clip(c,ct):
    i=int(np.clip(round(ct*FPS),0,NF[c]-1))+1
    return Image.open(f'clips/x{c}/{i:03d}.jpg').convert('RGBA')
def zoom(im,s):
    if s<=1.0005: return im
    w,h=W/s,H/s; return im.resize((W,H),Image.BICUBIC,box=((W-w)/2,(H-h)/2,(W+w)/2,(H+h)/2))
# (timeline start, end, clip, clip-time at start, speed, zoom group)
EDL=[(0.0, 5.0,'1v2',0.0,1.0,'A'),   # carousel: belt carries the bags, tray arrives
     (5.0, 5.75,'2', 0.3,4.0,'A'),   # same take continues: hand takes the key (4x)
     (5.75,7.0,'3',  1.2,2.0,'B'),   # unlock press (2x), lands at ~6.85
     (7.0,11.0,'4',  0.0,1.0,'C'),   # car answers: indicators flash on the hit — full clip, runs with the music
     (11.0,14.0,'5', 0.3,1.0,'D'),   # traveller walks to the car (soft dissolve in)
     (14.0,17.0,'6v2',1.6,1.0,'E'),  # bag in, tailgate shuts — first second skipped
     (17.0,20.5,'7', 0.0,1.0,'F')]   # drive away; the same shot keeps running under the end card
FIN=20.5; DUR=24.5; N=int(DUR*FPS); HIT=7.0
ZG={'A':(0.0,5.75,0.035),'B':(5.75,7.0,0.02),'C':(7.0,11.0,0.03),'D':(11.0,14.0,0.025),'E':(14.0,17.0,0.025),'F':(17.0,DUR,0.06)}
def zf(g,t):
    a,b,k=ZG[g]; return 1.0+k*np.clip((t-a)/(b-a),0,1)
XF=0.3                                    # dissolve 1->2 so the carousel reads as one take
def layer(fn):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); fn(L); return L
HOOK1=layer(lambda L:text(L,'أوّل ما يصلك في المطار',240,72))
HOOK2=layer(lambda L:text(L,'ليس حقيبتك',360,100,OR))
T1='حــقــيــبــتــك تــأخــرت؟'; T2='ســيــارتــك لا!'
E1=layer(lambda L:text(L,T1,470,84))
E2_Y=600; E2_FONT=F(B.AR_BLACK,124)
E2=layer(lambda L:text(L,T2,E2_Y,124,OR,E2_FONT))
E3=layer(lambda L:(text(L,'احجز سيارتك واستلمها',755,54,(235,238,244),F(B.AR_BOLD,54)),text(L,'من مطار اسطنبول أو صبيحة',830,54,(235,238,244),F(B.AR_BOLD,54))))
LOGO_Y=1000
LOGO=layer(lambda L:logo(L,LOGO_Y)); _lh=Image.open(B.LOGO_WHITE).size; LH=int(620*_lh[1]/_lh[0])
CONT=layer(lambda L:contacts(L,LOGO_Y+LH+100))
NOTE=layer(lambda L:text(L,'الخدمة برسوم إضافية · وفق الشروط والأحكام',1720,28,MUTED,F('NotoKufiArabic-Regular.ttf',28)))
# red paint-brush stroke under «سيارتك لا !»
def brush(w,h,seed=7):
    """bold red paint stroke: solid wet core, ragged bristle edges, dry split tail"""
    r=np.random.default_rng(seed); xs=np.arange(w,dtype=np.float32); yy=np.arange(h,dtype=np.float32)[:,None]
    def smooth(n,k):
        v=r.normal(0,1,n+2*k); return np.convolve(v,np.ones(k)/k,'same')[k:-k]
    u=xs/w
    center=h*0.5+smooth(w,90)*h*0.05+(u-0.5)*h*-0.10           # slight wobble and upward slant
    half=h*0.34*(0.75+0.25*np.sin(np.pi*np.clip(u*1.1,0,1)))*(1+0.12*smooth(w,40))
    half*=np.clip(np.minimum(u/0.035,1),0,1)**0.6               # blunt start (right side after flip)
    half*=np.clip((1-u)/0.18,0.15,1)                            # thinning dry tail
    d=np.abs(yy-center[None,:])/np.maximum(half[None,:],1)
    edge=1+0.18*r.normal(0,1,(h,w))                             # ragged bristle edge
    a=np.clip((1.0-d*edge)*6,0,1)
    streak=np.repeat(np.clip(r.normal(0.75,0.35,(h,1)),0,1),w,1) # bristle lines along the stroke
    dry=np.clip((u-0.62)/0.38,0,1)[None,:]                      # tail breaks into streaks
    a*=1-dry*(1-streak)*1.1
    a*=np.clip(1-dry*np.clip(r.random((h,w))-0.55,0,1)*2.5,0,1)
    a=np.clip(a,0,1)
    a=np.asarray(Image.fromarray((a*255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8)),np.float32)/255
    shade_=0.82+0.18*np.clip(1-d,0,1)[...,None]                 # wet sheen in the middle
    rgb=np.array([214,22,34],np.float32)*shade_*(0.92+0.08*r.random((h,w,1)))
    im=Image.fromarray(np.dstack([rgb,a*255]).clip(0,255).astype('uint8'),'RGBA')
    return im.transpose(Image.FLIP_LEFT_RIGHT)                  # heavy start on the right (Arabic reading)
E2W=sb.tw(T2,E2_FONT)
BR=brush(int(E2W*1.22),96)
BR_X=int((W-BR.width)/2); BR_Y=E2_Y+74
def brush_at(fr,p):
    if p<=0: return
    vis=int(BR.width*ease(p))                              # painted right-to-left, like Arabic
    if vis<2: return
    piece=BR.crop((BR.width-vis,0,BR.width,BR.height))
    fr.alpha_composite(piece,(BR_X+BR.width-vis,BR_Y))
def show(fr,L,a,rise=22):
    if a<=0: return
    fr.alpha_composite(faded(L,a),(0,int(rise*(1-a))))
def pop(fr,L,p,cy):
    """strong entrance: punch in from 1.35x with a tiny overshoot"""
    if p<=0: return
    if p>=1: fr.alpha_composite(L); return
    s=1+0.35*(1-ease(p))-0.06*np.sin(np.pi*p)
    crop=L.crop((0,int(cy-120),W,int(cy+120)))
    cw,ch=int(W*s),int(240*s); c=crop.resize((cw,ch),Image.LANCZOS)
    c=faded(c,min(1,p*2.2))
    fr.alpha_composite(c,(int((W-cw)/2),int(cy-ch/2)))
HV=0.85                                    # «سيارتك لا!» impact time inside the end card
_r=np.random.default_rng(21)
SPLAT=[(BR_X+BR.width*float(u),BR_Y+BR.height*0.5+float(_r.normal(0,46)),float(_r.uniform(3,11)),float(u)) for u in _r.uniform(0,1,46)]
def glow_layer(a):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); g=Image.new('L',(W,H),0)
    from PIL import ImageDraw
    ImageDraw.Draw(g).ellipse((W/2-460,E2_Y-150,W/2+460,E2_Y+150),fill=int(255*a))
    L.putalpha(g.filter(ImageFilter.GaussianBlur(70))); L2=Image.new('RGBA',(W,H),(230,40,40,255)); L2.putalpha(L.split()[3]); return L2
GLOW=glow_layer(1.0)
def splat_at(fr,p):
    if p<=0: return
    from PIL import ImageDraw
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for x,y,rr,u in SPLAT:
        if (1-u)<=p:                                   # droplets appear as the stroke passes (right-to-left)
            d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(206,24,36,230))
    fr.alpha_composite(L)
def punch(fr,L,p,cy):
    """slam in: 1.9x -> 0.96x -> 1.0x"""
    if p<=0: return
    if p>=1: fr.alpha_composite(L); return
    q=min(1,p/0.55); s=1.9-0.94*ease(q) if p<0.55 else 0.96+0.04*ease((p-0.55)/0.45)
    crop=L.crop((0,int(cy-130),W,int(cy+130)))
    cw,ch=int(W*s),int(260*s); c=crop.resize((cw,ch),Image.LANCZOS)
    if p<0.4: c=c.filter(ImageFilter.GaussianBlur(6*(1-p/0.4)))
    c=faded(c,min(1,p*3))
    fr.alpha_composite(c,(int((W-cw)/2),int(cy-ch/2)))
def shake(fr,v):
    d=v-HV
    if d<0 or d>0.35: return fr
    amp=22*np.exp(-d*11); r=np.random.default_rng(int(d*1000))
    dx,dy=int(r.normal(0,amp)),int(r.normal(0,amp*0.6))
    out=Image.new('RGBA',(W,H),(0,0,0,255)); out.alpha_composite(zoom(fr,1.04),(dx,dy)); return out
LAST7=None
def clip_at(c,ct):
    global LAST7
    if c=='7' and ct>=(NF['7']-1)/FPS:
        if LAST7 is None: LAST7=clip('7',5.0)
        return LAST7
    return clip(c,ct)
def render(f):
    t=f/FPS
    for a,b,c,c0,sp,g in EDL:
        if t<b: break
    else: a,b,c,c0,sp,g=EDL[-1]
    fr=zoom(clip_at(c,c0+(t-a)*sp),zf(g,t))
    if c=='1v2' and t>5.0-XF:                              # dissolve into the hand shot (no visible cut)
        a2,b2,c2,c02,sp2,g2=EDL[1]
        nxt=zoom(clip(c2,c02),zf('A',t)); fr=Image.blend(fr,nxt,eio(ramp(t,5.0-XF,5.0)))
    if c=='4' and t>11.0-0.35:                             # dissolve car-flash -> traveller, no hard cut
        a5,b5,c5,c05,sp5,g5=EDL[4]
        nxt=zoom(clip(c5,c05),zf('D',11.0)); fr=Image.blend(fr,nxt,eio(ramp(t,11.0-0.35,11.0)))
    if c in ('1v2','2'):
        ha=ease(ramp(t,3.0,3.5))*(1-ramp(t,5.3,5.72))
        if ha>0:
            sh=fr.copy(); shade(sh,top=560); fr=Image.blend(fr,sh,ha)
            show(fr,HOOK1,ease(ramp(t,3.0,3.5))*(1-ramp(t,5.3,5.72)))
            show(fr,HOOK2,ease(ramp(t,3.7,4.2))*(1-ramp(t,5.3,5.72)))
    if t<0.35: fr=Image.blend(Image.new('RGBA',(W,H),(0,0,0,255)),fr,ramp(t,0,0.35))
    if t>=FIN-0.4:                                         # end card grows out of the same running shot
        v=t-FIN; k=ease(ramp(v,-0.4,0.8))
        if k>0.02: fr=fr.filter(ImageFilter.GaussianBlur(14*k))
        fr.alpha_composite(Image.new('RGBA',(W,H),(6,9,14,int(170*k))))
        show(fr,E1,ease(ramp(v,0.2,0.55)))
        if HV-0.25<v<HV:                                  # breath before the hit: the room darkens
            fr.alpha_composite(Image.new('RGBA',(W,H),(0,0,0,int(90*ramp(v,HV-0.25,HV)))))
        if v>=HV:
            g=np.exp(-(v-HV)*6)*0.9+0.14+0.04*np.sin((v-HV)*5)
            fr.alpha_composite(faded(GLOW,min(1,g)))
        punch(fr,E2,ramp(v,HV,HV+0.28),E2_Y)
        if v>=HV:                                         # light burst on impact
            fl=np.exp(-(v-HV)*9)*0.42
            if fl>0.01: fr.alpha_composite(Image.new('RGBA',(W,H),(255,120,90,int(255*fl))))
        fr=shake(fr,v)
        show(fr,E3,ease(ramp(v,1.55,1.95)),12)
        la=ramp(v,1.9,2.45)
        if la>0:
            s=0.9+0.1*ease(la); L=faded(LOGO,min(1,la*1.6))
            if s<1:
                L=L.resize((int(W*s),int(H*s)),Image.LANCZOS); tmp=Image.new('RGBA',(W,H),(0,0,0,0))
                tmp.alpha_composite(L,(int((W-L.width)/2),int((LOGO_Y+LH/2)*(1-s)))); L=tmp
            fr.alpha_composite(L)
        show(fr,CONT,ease(ramp(v,2.3,2.7)),28); show(fr,NOTE,ease(ramp(v,2.6,3.0)),10)
    return fr.convert('RGB')
def eio(x): return x*x*(3-2*x)

# ---------------- sound ----------------
SR=48000
def aload(FF,fn,ss=None,d=None,af=None):
    cmd=[FF,'-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-t',str(d)] if d else [])+['-i',fn]+(['-af',af] if af else [])+['-ac','2','-ar',str(SR),'-f','s16le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,'<i2').reshape(-1,2).astype(np.float32)/32768
def rms(x): return float(np.sqrt((x**2).mean())+1e-9)
MUSIC={'A':('snd/music_679.mp3',70.4,'Epical Drums 04'),'B':('snd/music_614.mp3',69.6,'Silent Descent'),'C':('snd/music_770.mp3',204.4,'Autofahren')}
def refine_drop(FF,fn,tdrop):
    x=aload(FF,fn,tdrop-0.6,1.2).mean(1); e=np.array([rms(x[i:i+480]) for i in range(0,len(x)-480,240)])
    on=np.diff(e); return tdrop-0.6+(int(np.argmax(on))+1)*240/SR
MUSIC_LUFS=-20.0; FINAL_GAIN=[0.0]
def mix(FF,key,out_wav):
    Nn=int(DUR*SR); o=np.zeros((Nn,2),np.float32)
    def place(x,t,g,fin=0.0,fade=0.0):
        x=x.copy()
        if fin: k=min(len(x),int(fin*SR)); x[:k]*=np.linspace(0,1,k)[:,None]
        if fade: k=min(len(x),int(fade*SR)); x[-k:]*=np.linspace(1,0,k)[:,None]
        s=int(t*SR); n=min(len(x),Nn-s)
        if n>0: o[s:s+n]+=x[:n]*g
    # 1) native clip audio, cut exactly with the picture (it is synced: belt hum, key, click, chirp, steps, trunk slam, engine)
    nat=np.zeros_like(o); XO=0.15
    XOS={4:0.3}                                                  # longer blend into the traveller shot
    G={'1v2':1.0,'2':1.0,'3':1.15,'4':1.1,'5':0.95,'6v2':1.15,'7':1.1}
    for idx,(a,b,c,c0,sp,g) in enumerate(EDL):
        pre=XOS.get(idx,XO) if idx>0 else 0.0; post=XOS.get(idx+1,XO) if idx<len(EDL)-1 else 0.0
        pre=min(pre,c0/sp) if idx>0 else 0.0
        tempo=','.join(['atempo=2.0']*(int(np.log2(sp))) ) if sp in (2.0,4.0) else (f'atempo={sp}' if sp!=1 else '')
        af='highpass=f=60,lowpass=f=9000'+(','+tempo if tempo else '')
        ss=max(0.0,c0-pre*sp); x=aload(FF,f'clips/{c}.mp4',ss,(b-a+pre+post)*sp,af=af)
        x=x/rms(x)*0.09*G[c]                                     # level by loudness, not by peak
        if c=='4':                                               # clip 4's own sound dies in its last 0.6 s: carry its ambience on
            L=int(0.8*SR); n0=len(x)-L; src=x[n0-int(1.2*SR):n0-int(1.2*SR)+L]
            w=np.clip(np.linspace(-0.2,1.2,L),0,1)[:,None]; x[n0:]=x[n0:]*(1-w)+src*w
        x=np.tanh(x*2.2)/2.2                                     # tame single spikes so nothing jumps out
        n=len(x); k1=int(pre*SR*2) or 1; k2=int(post*SR*2) or 1
        if pre: x[:k1]*=np.sqrt(np.linspace(0,1,k1))[:,None]          # equal-power crossfade
        if post: x[n-k2:]*=np.sqrt(np.linspace(1,0,k2))[:,None]
        s0=int((a-pre)*SR); s0=max(0,s0); m_=min(n,Nn-s0); nat[s0:s0+m_]+=x[:m_]
    # level-rider: even out the native track so no shot change leaves a hole or a jump
    mono=np.abs(nat).mean(1); w=int(0.35*SR)
    env_=np.sqrt(np.convolve(mono**2,np.ones(w)/w,'same'))+1e-5
    tgt=np.median(env_[int(0.5*SR):int((FIN-0.5)*SR)])
    gn=np.clip(tgt/env_,0.6,4.0); gn=np.convolve(gn,np.ones(int(0.25*SR))/int(0.25*SR),'same')
    nat=nat*gn[:,None]
    w2=int(0.05*SR); e2=np.sqrt(np.convolve((np.abs(nat).mean(1))**2,np.ones(w2)/w2,'same'))+1e-6
    lim=np.minimum(1.0,(tgt*1.5)/e2); lim=np.convolve(lim,np.ones(int(0.04*SR))/int(0.04*SR),'same')
    nat=nat*lim[:,None]                                          # fast soft limiter: no sudden bursts after a cut
    o+=nat*0.85
    fn,td,_=MUSIC[key]; td=refine_drop(FF,fn,td); start=td-HIT
    m=aload(FF,fn,start,DUR+0.5)[:Nn]; m=m/rms(m)*0.06
    tt=np.arange(len(m))/SR
    env=np.clip(tt/1.2,0,1)
    env*=1-0.72*np.clip((tt-2.9)/0.25,0,1)*np.clip((4.6-tt)/0.6,0,1)    # hush when the tray appears
    env*=0.75+0.25*np.clip((tt-(HIT-0.4))/0.9,0,1)       # smooth lift into the hit, no step
    env*=np.clip((DUR-tt)/2.2,0,1)
    mus=m*env[:,None]
    acc=np.zeros_like(o)
    def put(x,t,g,fade=0.0):
        x=x.copy()
        if fade: k=min(len(x),int(fade*SR)); x[-k:]*=np.linspace(1,0,k)[:,None]
        s0=int(t*SR); n=min(len(x),Nn-s0)
        if n>0: acc[s0:s0+n]+=x[:n]*g
    imp=aload(FF,'snd/drum_impact.mp3'); imp=imp/rms(imp)*0.04; put(imp,HIT-0.03,1.0,fade=1.5)
    lg=aload(FF,'snd/logo_impact.mp3'); lg=lg/rms(lg)*0.04; put(lg,FIN+1.9,1.0,fade=2.0)
    # set the music to exactly the requested loudness inside the final -14 LUFS mix
    def lufs(x):
        p='lufs_tmp.wav'
        with wave.open(p,'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x,-1,1)*32767).astype('<i2').tobytes())
        r=subprocess.run([FF,'-hide_banner','-i',p,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
        return float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
    g=1.0
    for _ in range(3):
        tot=o+mus*g+acc; sc=0.5/ (np.abs(tot).max()+1e-9)
        Lt=lufs(tot*sc); Lm=lufs(mus*g*sc); gain=-14-Lt
        g*=10**((MUSIC_LUFS-(Lm+gain))/20)
    tot=o+mus*g+acc; sc=0.5/(np.abs(tot).max()+1e-9); Lt=lufs(tot*sc); Lm=lufs(mus*g*sc)
    print(f'music in final mix: {Lm+(-14-Lt):.1f} LUFS')
    o=tot*sc; FINAL_GAIN[0]=-14-Lt
    with wave.open(out_wav,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(o,-1,1)*32767).astype('<i2').tobytes())
    subprocess.run([FF,'-v','error','-y','-i',out_wav,'-af',f'volume={FINAL_GAIN[0]:.2f}dB,alimiter=limit=0.891:level=disabled','-ar','48000',out_wav.replace('.wav','_n.wav')],check=True)
def chunk(FF,a,b):
    os.makedirs('rchunks',exist_ok=True)
    p=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','fast','-crf','10','-pix_fmt','yuv420p',f'rchunks/{a:05d}.mp4'],stdin=subprocess.PIPE)
    for f in range(a,b): p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
def video(FF):
    with open('rchunks/list.txt','w') as fh:
        for fn in sorted(x for x in os.listdir('rchunks') if x.endswith('.mp4')): fh.write(f"file '{fn}'\n")
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i','rchunks/list.txt','-c','copy','rall.mp4'],check=True)
    for p in (1,2):
        cmd=[FF,'-v','error','-y','-i','rall.mp4','-c:v','libx264','-b:v','7000k','-maxrate','11000k','-bufsize','14000k','-preset','veryslow','-tune','film','-pix_fmt','yuv420p','-pass',str(p),'-passlogfile','x264air','-an']
        cmd+=(['-f','mp4','/dev/null'] if p==1 else ['-movflags','+faststart','rvideo.mp4'])
        subprocess.run(cmd,check=True)
def mux(FF,key,out):
    mix(FF,key,f'mix_{key}.wav')
    subprocess.run([FF,'-v','error','-y','-i','rvideo.mp4','-i',f'mix_{key}_n.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],check=True)
if __name__=='__main__':
    import imageio_ffmpeg; FF=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=sys.argv[1]
    if cmd=='chunk': chunk(FF,int(sys.argv[2]),min(N,int(sys.argv[3])))
    elif cmd=='video': video(FF)
    elif cmd=='mux': mux(FF,sys.argv[2],sys.argv[3])
    elif cmd=='check':
        ts=[float(x) for x in sys.argv[2:]]; fr=[render(int(t*FPS)).resize((270,480)) for t in ts]
        s=Image.new('RGB',(270*len(fr),480))
        for i,im in enumerate(fr): s.paste(im,(270*i,0))
        s.save('/tmp/claude-0/-home-user-asas/d21a85a7-6665-5900-89b1-ab98434bf7ea/scratchpad/reel_chk.jpg'); print('ok')
