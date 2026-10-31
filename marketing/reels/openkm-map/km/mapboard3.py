"""«خريطة بخط واحد» v3 — real map, real office location, start parked at the office -> zoom out -> map/place alternation -> ∞ finale."""
import sys, os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','brand-kit')); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','map'))
import brand as B, numpy as np
from PIL import Image, ImageDraw, ImageFilter
import boards as BD
import real
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
W,H=1080,1920; F=B.F; OR=B.ORANGE; NAVY=B.LOGONAVY; RED=(214,30,42)
text=BD.text; frosted=BD.frosted; img=BD.img; tw=BD.tw
OFFICE=real.OFFICE
STOPS=[('غابة بلغراد',41.205,28.975),('شيلي',41.175,29.610),('سابانجا',40.715,30.255),('بورصة',40.195,29.060)]
ATTR='Esri, HERE, Garmin, © OpenStreetMap'
def attribution(fr):
    ImageDraw.Draw(fr).text((24,H-24),ATTR,font=F(B.LT_TEXT,20),fill=(140,150,160),anchor='ls')
def labels(fr,P,which):
    d=ImageDraw.Draw(fr)
    L={'sea':[('البحر الأسود',41.36,30.05),('بحر مرمرة',40.72,28.95)],'city':[('إسطنبول',41.02,28.97)]}
    for k in which:
        for nm,la,lo in L[k]:
            x,y=P(la,lo)
            if -50<x<W+50 and -50<y<H+50:
                d.text((x,y),nm,font=F('NotoKufiArabic-Medium.ttf',44 if k=='sea' else 40),fill=(110,150,180) if k=='sea' else (120,110,100),anchor='mm',direction='rtl',language='ar')
def office_pin(fr,x,y,s=1.0,label=True):
    d=ImageDraw.Draw(fr); r=int(46*s)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).ellipse((x-r,y-r+10,x+r,y+r+10),fill=(20,30,45,110)); fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d.polygon([(x-r*0.55,y+r*0.6),(x+r*0.55,y+r*0.6),(x,y+r*1.55)],fill=NAVY)
    d.ellipse((x-r,y-r,x+r,y+r),fill=NAVY,outline=(255,255,255),width=max(3,int(7*s)))
    lg=Image.open(B.LOGO_WHITE).convert('RGBA'); w=int(r*1.4); lg=lg.resize((w,int(w*lg.height/lg.width)),Image.LANCZOS); fr.alpha_composite(lg,(int(x-w/2),int(y-lg.height/2)))
    if label:
        f=F(B.LT_BOLD,int(38*s)); t='Call & Rent'; w=ImageDraw.Draw(Image.new('L',(4,4))).textbbox((0,0),t,font=f)[2]+48; by=y-r-int(78*s)
        d.rounded_rectangle((x-w/2,by,x+w/2,by+int(58*s)),radius=int(29*s),fill=(255,255,255)); d.text((x,by+int(29*s)),t,font=f,fill=NAVY,anchor='mm')
def stop_pin(fr,x,y,nm,below=False):
    d=ImageDraw.Draw(fr); d.ellipse((x-17,y-17,x+17,y+17),fill=(255,255,255),outline=RED,width=8)
    f=F(B.AR_BOLD,38); w=tw(nm,f)+44; by=y+30 if below else y-92
    d.rounded_rectangle((x-w/2,by,x+w/2,by+58),radius=29,fill=NAVY); d.text((x,by+29),nm,font=f,fill=(255,255,255),anchor='mm',direction='rtl',language='ar')
def route(P,n_stops,frac=1.0):
    pts=[(OFFICE[0],OFFICE[1])]+[(la,lo) for _,la,lo in STOPS[:n_stops]]
    out=[]
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        ax,ay=P(*a); bx,by=P(*b); mx,my=(ax+bx)/2,(ay+by)/2; nx,ny=-(by-ay),(bx-ax); cx,cy=mx+nx*0.18,my+ny*0.18
        seg=[((1-t)**2*ax+2*(1-t)*t*cx+t*t*bx,(1-t)**2*ay+2*(1-t)*t*cy+t*t*by) for t in np.linspace(0,1,80)]
        if i==len(pts)-2: seg=seg[:max(2,int(len(seg)*frac))]
        out+=seg
    return out
def map_region(n_stops,frac=1.0,title=None):
    base,P=real.get('region'); fr=base.copy(); labels(fr,P,('sea',))
    pts=route(P,n_stops,frac)
    if len(pts)>1:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).line(pts,fill=RED+(90,),width=30,joint='curve'); fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        ImageDraw.Draw(fr).line(pts,fill=RED,width=11,joint='curve')
    below={'سابانجا'}
    for i,(nm,la,lo) in enumerate(STOPS[:n_stops]):
        if i<n_stops-1 or frac>=1: x,y=P(la,lo); stop_pin(fr,x,y,nm,below=nm in below)
    x,y=P(*OFFICE); office_pin(fr,x,y,0.8,label=False)
    if len(pts)>1: x,y=pts[-1]; ImageDraw.Draw(fr).ellipse((x-24,y-24,x+24,y+24),fill=(255,255,255),outline=RED,width=9)
    if title: text(fr,title,300,76,NAVY)
    attribution(fr); return fr
def place(n,label):
    f=img(n); ww=tw(label,F(B.AR_BLACK,70))+140; x0=(W-ww)//2
    frosted(f,(x0,140,x0+ww,270),r=60,k=0.85); text(f,label,205,70,NAVY); return f
def finale():
    base,P=real.get('region'); fr=base.copy(); labels(fr,P,('sea',))
    xs=[P(la,lo)[0] for _,la,lo in STOPS]+[P(*OFFICE)[0]]; ys=[P(la,lo)[1] for _,la,lo in STOPS]+[P(*OFFICE)[1]]
    cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2; rx=(max(xs)-min(xs))/2+60
    L=Image.new('RGBA',(W,H),(0,0,0,0)); dl=ImageDraw.Draw(L)
    th=np.linspace(0,2*np.pi,420); den=1+np.sin(th)**2
    p=[(cx+rx*np.cos(t)/q, cy+rx*0.85*np.sin(t)*np.cos(t)/q) for t,q in zip(th,den)]
    dl.line(p+[p[0]],fill=RED+(255,),width=20,joint='curve')
    g=Image.new('RGBA',(W,H),(255,90,90,0)); g.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(30))); fr.alpha_composite(g); fr.alpha_composite(L)
    x,y=P(*OFFICE); office_pin(fr,x,y,0.8,label=False)
    BD.top_wash(fr,430,225)
    text(fr,'رحلة… بلا نهاية',150,92,NAVY); text(fr,'الكيلومترات مفتوحة لدينا',262,60,OR,F(B.AR_BOLD,60))
    BD.footer(fr,'خدمة الكيلومترات المفتوحة وفق الشروط والأحكام'); attribution(fr); return fr
def frames():
    out=[]
    out.append((img('office_sunny_black'),'0:00 – 0:01.5','السيارة أمام مكتبنا','يوم مشمس · الكاميرا ترتفع'))
    s,Ps=real.get('street'); f=s.copy(); x,y=Ps(*OFFICE); office_pin(f,x,y,1.2); attribution(f)
    out.append((f,'0:01.5 – 0:02.5','لقطة علوية للمكتب','الكاميرا ترتفع أكثر'))
    c,Pc=real.get('city'); f=c.copy(); labels(f,Pc,('sea','city')); x,y=Pc(*OFFICE); office_pin(f,x,y,1.0); text(f,'من هنا تبدأ الرحلة…',300,76,NAVY); attribution(f)
    out.append((f,'0:02.5 – 0:03.5','خريطة إسطنبول','موقع مكتبنا الحقيقي'))
    out.append((map_region(1),'0:03.5 – 0:04.3','الخط إلى غابة بلغراد','الخريطة'))
    out.append((place('forest','غابة بلغراد'),'0:04.3 – 0:05.8','غابة بلغراد','المكان'))
    out.append((map_region(2,title='والخطّ لم يتوقف'),'0:05.8 – 0:06.6','الخط إلى شيلي','الخريطة'))
    out.append((place('blacksea','شيلي'),'0:06.6 – 0:08.1','شيلي والبحر الأسود','المكان'))
    out.append((map_region(3),'0:08.1 – 0:08.9','الخط إلى سابانجا','الخريطة'))
    out.append((place('sapanca','بحيرة سابانجا'),'0:08.9 – 0:10.4','بحيرة سابانجا','المكان'))
    out.append((map_region(4),'0:10.4 – 0:11.2','الخط إلى بورصة','الخريطة'))
    out.append((place('uludag','بورصة · أولوداغ'),'0:11.2 – 0:12.7','بورصة وجبل أولوداغ','المكان'))
    out.append((finale(),'0:12.7 – 0:17','النهاية: الخط يرسم ∞','الشعار والتواصل'))
    return out
def sheet12(frames,title,sub,out):
    PW,PH=405,720; GAP=30; CAP=190; COLS=4; ROWS=3
    Wd=COLS*PW+(COLS+1)*GAP; Hd=200+ROWS*(PH+CAP)+(ROWS+1)*GAP
    s=Image.new('RGB',(Wd,Hd),(236,243,249)); d=ImageDraw.Draw(s)
    d.text((Wd/2,70),title,font=F(B.AR_BLACK,46),fill=NAVY,anchor='mm',direction='rtl',language='ar')
    d.text((Wd/2,140),sub,font=F('NotoKufiArabic-Regular.ttf',30),fill=OR,anchor='mm',direction='rtl',language='ar')
    for i,(im,tm,l1,l2) in enumerate(frames):
        r=i//COLS; c=COLS-1-(i%COLS); x=GAP+c*(PW+GAP); y=200+GAP+r*(PH+CAP+GAP)
        s.paste(im.convert('RGB').resize((PW,PH),Image.LANCZOS),(x,y)); d.rectangle((x,y,x+PW-1,y+PH-1),outline=(190,205,220),width=2)
        d.ellipse((x+14,y+14,x+66,y+66),fill=OR); d.text((x+40,y+40),str(i+1),font=F(B.LT_BOLD,30),fill=(255,255,255),anchor='mm')
        d.text((x+PW/2,y+PH+36),tm,font=F(B.LT_TEXT,28),fill=OR,anchor='mm')
        d.text((x+PW/2,y+PH+92),l1.replace(' ∞',''),font=F(B.AR_BOLD,30),fill=NAVY,anchor='mm',direction='rtl',language='ar')
        d.text((x+PW/2,y+PH+144),l2,font=F('NotoKufiArabic-Regular.ttf',25),fill=(90,110,130),anchor='mm',direction='rtl',language='ar')
    s.save(out,quality=90)
if __name__=='__main__':
    sheet12(frames(),'ستوري بورد · الكيلومترات المفتوحة · خريطة بخط واحد','17 ثانية · خريطة حقيقية · موقع مكتبنا الفعلي · خريطة ثم مكان · والنهاية رمز اللانهاية','../final/OPENKM-MAP-storyboard-v4.jpg')
    print('ok')
