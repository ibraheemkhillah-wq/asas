"""Storyboards for two open-km ideas (red i20): «سؤال الزبون» POV and «خريطة بخط واحد»."""
import sys, os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','brand-kit')); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','map'))
import brand as B, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
W,H=1080,1920; F=B.F; OR=B.ORANGE; NAVY=B.LOGONAVY
EMOJI='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
def img(n): return Image.open(f'src/{n}.png').convert('RGBA')
def tint(m,c): L=Image.new('RGBA',m.size,c+(255,)); L.putalpha(m); return L
def emoji(ch,size):
    f=ImageFont.truetype(EMOJI,109); im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=f,embedded_color=True)
    im=im.crop(im.getbbox()); return im.resize((int(im.width*size/im.height),size),Image.LANCZOS)
_d=ImageDraw.Draw(Image.new('L',(4,4)))
def tw(s,f): bb=_d.textbbox((0,0),s,font=f,direction='rtl',language='ar'); return bb[2]-bb[0]
def text(fr,t,cy,size,color,font=None,glow=(255,255,255),k=0.9,x=W/2,anchor='mm'):
    f=font or F(B.AR_BLACK,size); ov=Image.new('RGBA',fr.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    d.text((x,cy),t,font=f,fill=color+(255,),anchor=anchor,direction='rtl',language='ar')
    g=Image.new('RGBA',fr.size,glow+(0,)); g.putalpha(ov.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v:int(v*k))); fr.alpha_composite(g); fr.alpha_composite(ov)
def frosted(fr,box,r=40,k=0.8,col=(255,255,255)):
    x0,y0,x1,y1=box; reg=fr.crop(box).filter(ImageFilter.GaussianBlur(18)); reg.alpha_composite(Image.new('RGBA',reg.size,col+(int(255*k),)))
    m=Image.new('L',reg.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,reg.width-1,reg.height-1),radius=r,fill=255)
    sh=Image.new('RGBA',(W,H),(20,30,45,0)); sm=Image.new('L',(W,H),0); sm.paste(m,(x0,y0+10)); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.3))); fr.alpha_composite(sh)
    fr.paste(reg,(x0,y0),m)
def contacts(L,y,col=NAVY):
    fc=F(B.CT_FONT,40); d=ImageDraw.Draw(L); ic={k:tint(v.split()[3],col) for k,v in B.load_icons(42).items()}
    items=[(('ig','fb'),'callrenttr'),(('wa','ph'),'+90 555 034 22 00')]
    ws=[2*42+10+12+_d.textbbox((0,0),t,font=fc)[2] for k,t in items]; gap=56; x=(W-(sum(ws)+gap))//2
    for (keys,t),w in zip(items,ws):
        xx=x
        for k in keys: L.alpha_composite(ic[k],(int(xx),y-21)); xx+=52
        d.text((xx+12,y),t,font=fc,fill=col+(255,),anchor='lm'); x+=w+gap
def footer(fr,note):
    frosted(fr,(90,1560,990,1870))
    lg=Image.open(B.LOGO_NAVY).convert('RGBA'); lg=lg.resize((360,int(360*lg.height/lg.width)),Image.LANCZOS); fr.alpha_composite(lg,((W-360)//2,1590))
    contacts(fr,1760); text(fr,note,1830,26,(90,105,125),F('NotoKufiArabic-Regular.ttf',26))
def top_wash(fr,h=520,k=240):
    wm=np.clip(1-np.arange(H)/h,0,1)**1.1*k; w=Image.new('RGBA',(W,H),(255,255,255,0)); w.putalpha(Image.fromarray(np.repeat(wm[:,None],W,1).astype('uint8'))); fr.alpha_composite(w)

# ======================= «سؤال الزبون» (POV) =======================
def pov_card(bg,lines,blur=True):
    fr=bg.copy()
    if blur: fr=fr.filter(ImageFilter.GaussianBlur(14)); fr.alpha_composite(Image.new('RGBA',(W,H),(255,255,255,110)))
    return fr
def bubble(fr,txt,y,side='me',emo=None,size=52):
    f=F('NotoKufiArabic-Medium.ttf',size); w=tw(txt,f)+(size+16 if emo else 0)+80; h=size+64
    x1=W-70 if side=='me' else 70+w; x0=x1-w
    col=(255,255,255) if side=='me' else (26,32,44)
    sh=Image.new('L',(W,H),0); ImageDraw.Draw(sh).rounded_rectangle((x0,y+8,x1,y+h+8),radius=h//2,fill=90)
    s=Image.new('RGBA',(W,H),(0,0,0,0)); s.putalpha(sh.filter(ImageFilter.GaussianBlur(16))); fr.alpha_composite(s)
    d=ImageDraw.Draw(fr); d.rounded_rectangle((x0,y,x1,y+h),radius=h//2,fill=col+(255,))
    tc=(26,32,44) if side=='me' else (255,255,255)
    d.text((x1-40,y+h/2),txt,font=f,fill=tc,anchor='rm',direction='rtl',language='ar')
    if emo: e=emoji(emo,size+6); fr.alpha_composite(e,(int(x1-40-tw(txt,f)-12-e.width),int(y+h/2-e.height/2)))
def pov_tag(fr):
    d=ImageDraw.Draw(fr); d.rounded_rectangle((70,150,250,226),radius=38,fill=(26,32,44,255)); d.text((160,188),'POV',font=F(B.LT_BOLD,44),fill=(255,255,255),anchor='mm')
def stamp(fr,place,y=1500):
    f=F(B.AR_BLACK,78); t=place; w=tw(t,f)+150
    x0=(W-w)//2; frosted(fr,(x0,y,x0+w,y+130),r=65,k=0.85)
    d=ImageDraw.Draw(fr); d.text((x0+w-50,y+65),t,font=f,fill=NAVY,anchor='rm',direction='rtl',language='ar')
    cx,cy=x0+60,y+65; d.ellipse((cx-30,cy-30,cx+30,cy+30),fill=(39,174,96)); d.line([(cx-14,cy+1),(cx-4,cy+12),(cx+16,cy-12)],fill=(255,255,255),width=8,joint='curve')
def pov_frames():
    out=[]; office=img('office_i20')
    f=pov_card(office,[]); pov_tag(f); bubble(f,'سألت الموظف…',520); out.append((f,'0:00 – 0:01.5','POV: سألت الموظف…','على خلفية مكتبنا مغبّشة'))
    f=pov_card(office,[]); pov_tag(f); bubble(f,'سألت الموظف…',520); bubble(f,'كم كيلومتر مسموح لي؟',700,emo='🤔'); out.append((f,'0:01.5 – 0:03','كم كيلومتر مسموح لي؟','وقفة… وصوت كتابة'))
    f=pov_card(office,[]); pov_tag(f); bubble(f,'سألت الموظف…',520); bubble(f,'كم كيلومتر مسموح لي؟',700,emo='🤔'); bubble(f,'قدّ ما بدك',900,side='them',emo='😎',size=64)
    out.append((f,'0:03 – 0:04.5','الجواب: «قدّ ما بدك» 😎','ضربة صوت + بيرجع واضح'))
    for n,place,tm,cap in (('blacksea','شيلي','0:04.5 – 0:06','مونتاج على الإيقاع'),('sapanca','سابانجا','0:06 – 0:07.5','كل لقطة عليها اسم المكان'),
                           ('autumn','غابات الخريف','0:07.5 – 0:09','لقطات أسرع'),('uludag','بورصة','0:09 – 0:10.5',''),('sunset','وأكثر…','0:10.5 – 0:12.5','الغروب على البحر')):
        f=img(n); stamp(f,place); out.append((f,tm,place+(' ✓' if place!='وأكثر…' else ''),cap))
    f=img('office_i20'); top_wash(f,470,240)
    text(f,'عدّاد مفتوح',150,100,NAVY); text(f,'بلا رسوم كيلومترات إضافية',268,58,OR,F(B.AR_BOLD,58)); text(f,'اسأل… والجواب دايماً «قدّ ما بدك»',352,38,(70,85,105),F('NotoKufiArabic-Medium.ttf',38))
    footer(f,'خدمة الكيلومترات المفتوحة وفق الشروط والأحكام'); out.append((f,'0:12.5 – 0:16','الخاتمة قدام مكتبنا','عدّاد مفتوح بلا رسوم إضافية'))
    return out

# ======================= «خريطة بخط واحد» =======================
import geo
ROUTE=[('إسطنبول',28.98,41.01),('سابانجا',30.4,40.69),('كبادوكيا',34.83,38.64),('أنطاليا',30.71,36.89),('طرابزون',39.72,41.0),('إسطنبول',28.98,41.01)]
def route_pts(scale):
    pts=[]
    ctrl=[(lo,la) for _,lo,la in ROUTE]
    for (a,b) in zip(ctrl,ctrl[1:]):
        mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2; nx,ny=-(b[1]-a[1]),(b[0]-a[0]); c=(mx+nx*0.18,my+ny*0.18)
        for t in np.linspace(0,1,60):
            lo=(1-t)**2*a[0]+2*(1-t)*t*c[0]+t*t*b[0]; la=(1-t)**2*a[1]+2*(1-t)*t*c[1]+t*t*b[1]; pts.append(geo.proj(lo,la,scale))
    return pts
SCALE=78.0
BASE=geo.base_map(SCALE).convert('RGBA')
def map_frame(upto,label_upto,inf=0.0,car=True,zoom=None):
    fr=BASE.copy(); d=ImageDraw.Draw(fr); pts=route_pts(SCALE); n=int(len(pts)*upto)
    if inf>0: n=0; label_upto=-1; car=False          # the ∞ replaces the route: one clean shape over Turkey
    if n>1:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).line(pts[:n],fill=(244,141,87,90),width=26,joint='curve'); fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d=ImageDraw.Draw(fr); d.line(pts[:n],fill=OR,width=10,joint='curve')
        for i in range(0,n,18): pass
    for i,(nm,lo,la) in enumerate(ROUTE[:-1]):
        if i>label_upto: break
        x,y=geo.proj(lo,la,SCALE); d.ellipse((x-16,y-16,x+16,y+16),fill=(255,255,255),outline=OR,width=7)
        f=F(B.AR_BOLD,36); w=tw(nm,f)+40; bx=x-w/2; by=y-78 if i!=1 else y+26   # Sapanca label below so it doesn't sit on Istanbul's
        d.rounded_rectangle((bx,by,bx+w,by+54),radius=27,fill=NAVY); d.text((x,by+27),nm,font=f,fill=(255,255,255),anchor='mm',direction='rtl',language='ar')
    if car and n>1:
        x,y=pts[n-1]; d.ellipse((x-22,y-22,x+22,y+22),fill=(205,30,40),outline=(255,255,255),width=6)
    if inf>0:
        cx,cy=geo.proj(35.0,39.0,SCALE); L=Image.new('RGBA',(W,H),(0,0,0,0)); dl=ImageDraw.Draw(L)
        th=np.linspace(0,2*np.pi*inf,int(400*inf)+2); den=1+np.sin(th)**2; rx=380
        p=[(cx+rx*np.cos(t)/q, cy+rx*0.9*np.sin(t)*np.cos(t)/q) for t,q in zip(th,den)]
        dl.line(p,fill=OR+(255,),width=16,joint='curve')
        g=Image.new('RGBA',(W,H),(255,170,110,0)); g.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(26))); fr.alpha_composite(g); fr.alpha_composite(L)
    if zoom:
        z,(lo,la)=zoom; x,y=geo.proj(lo,la,SCALE); w,h=W/z,H/z; x0=min(max(x-w/2,0),W-w); y0=min(max(y-h/2,0),H-h)
        fr=fr.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+w,y0+h))
    return fr
def map_frames():
    out=[]
    f=map_frame(0.0,0,car=False,zoom=(2.6,(28.98,41.01))); d=ImageDraw.Draw(f)
    text(f,'من هون بلّشنا…',330,74,NAVY); out.append((f,'0:00 – 0:01.5','الخريطة: المكتب بإسطنبول','قلم برتقالي بيحط أول نقطة'))
    f=map_frame(0.18,1,zoom=(1.5,(31.5,40.0))); text(f,'والخط ما وقف',330,74,NAVY); out.append((f,'0:01.5 – 0:03','الخط بيطلع من المدينة','بيمرق بسابانجا'))
    f=img('cappadocia'); frosted(f,(240,140,840,270),r=60,k=0.85); text(f,'كبادوكيا',205,70,NAVY); out.append((f,'0:03 – 0:05','وصل كبادوكيا','الخريطة بتفتح على اللقطة'))
    f=map_frame(0.6,3,zoom=(1.25,(33.0,39.2))); out.append((f,'0:05 – 0:06','الخط بينزل جنوب','على أنطاليا'))
    f=img('antalya'); frosted(f,(270,140,810,270),r=60,k=0.85); text(f,'أنطاليا',205,70,NAVY); out.append((f,'0:06 – 0:08','أنطاليا والبحر الأزرق',''))
    f=img('uzungol'); frosted(f,(150,140,930,270),r=60,k=0.85); text(f,'طرابزون · أوزنجول',205,64,NAVY); out.append((f,'0:08 – 0:10','الجبال الخضرا بالبحر الأسود','الخط بيطلع شمال'))
    f=map_frame(1.0,4,inf=1.0); text(f,'رحلة… بلا نهاية',300,80,NAVY); out.append((f,'0:10 – 0:12','الخط بيرجع وبيرسم ∞','فوق تركيا كلها'))
    f=img('office_i20'); top_wash(f,470,240)
    text(f,'ارسم رحلتك بلا حدود',160,76,NAVY); text(f,'الكيلومترات علينا مفتوحة',262,60,OR,F(B.AR_BOLD,60))
    footer(f,'خدمة الكيلومترات المفتوحة وفق الشروط والأحكام'); out.append((f,'0:12 – 0:16','الخاتمة قدام مكتبنا','ارسم رحلتك بلا حدود'))
    return out

def sheet(frames,title,sub,out):
    PW,PH=405,720; GAP=30; CAP=190; COLS=4
    Wd=COLS*PW+(COLS+1)*GAP; Hd=200+2*(PH+CAP)+3*GAP
    s=Image.new('RGB',(Wd,Hd),(236,243,249)); d=ImageDraw.Draw(s)
    d.text((Wd/2,70),title,font=F(B.AR_BLACK,46),fill=NAVY,anchor='mm',direction='rtl',language='ar')
    d.text((Wd/2,140),sub,font=F('NotoKufiArabic-Regular.ttf',30),fill=OR,anchor='mm',direction='rtl',language='ar')
    for i,(im,tm,l1,l2) in enumerate(frames[:8]):
        r=i//COLS; c=COLS-1-(i%COLS); x=GAP+c*(PW+GAP); y=200+GAP+r*(PH+CAP+GAP)
        s.paste(im.convert('RGB').resize((PW,PH),Image.LANCZOS),(x,y)); d.rectangle((x,y,x+PW-1,y+PH-1),outline=(190,205,220),width=2)
        d.ellipse((x+14,y+14,x+66,y+66),fill=OR); d.text((x+40,y+40),str(i+1),font=F(B.LT_BOLD,32),fill=(255,255,255),anchor='mm')
        d.text((x+PW/2,y+PH+36),tm,font=F(B.LT_TEXT,28),fill=OR,anchor='mm')
        d.text((x+PW/2,y+PH+92),l1.replace(' 😎','').replace(' ✓','').replace(' ∞',''),font=F(B.AR_BOLD,30),fill=NAVY,anchor='mm',direction='rtl',language='ar')
        d.text((x+PW/2,y+PH+144),l2,font=F('NotoKufiArabic-Regular.ttf',25),fill=(90,110,130),anchor='mm',direction='rtl',language='ar')
    s.save(out,quality=90)

if __name__=='__main__':
    pv=pov_frames()
    # 10 POV beats -> keep the 8 that tell the story
    keep=[pv[0],pv[1],pv[2],pv[3],pv[4],pv[5],pv[7],pv[8]]
    sheet(keep,'ستوري بورد · الكيلومترات المفتوحة · سؤال الزبون (POV)','16 ثانية · هونداي i20 حمرا 2026 · فاتح · الخاتمة قدام المكتب','../final/OPENKM-POV-storyboard.jpg')
    mp=map_frames()
    sheet(mp,'ستوري بورد · الكيلومترات المفتوحة · خريطة بخط واحد','16 ثانية · هونداي i20 حمرا 2026 · خريطة تركيا فاتحة · الخاتمة قدام المكتب','../final/OPENKM-MAP-storyboard.jpg')
    print('ok')
