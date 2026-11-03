"""Dark storyboards for the airport pick-up / drop-off reels (CALL & RENT, red i20)."""
import sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','..','brand-kit'))
import brand as B, numpy as np
from PIL import Image, ImageDraw, ImageFilter
os.chdir(HERE)
W,H=1080,1920; F=B.F; OR=B.ORANGE; WHITE=(255,255,255)
BG=(11,14,20); CARD=(20,25,34); MUTED=(150,160,175)
_d=ImageDraw.Draw(Image.new('L',(4,4)))
def tw(s,f): bb=_d.textbbox((0,0),s,font=f,direction='rtl',language='ar'); return bb[2]-bb[0]
def img(n): return Image.open(f'src/{n}.jpg').convert('RGBA').resize((W,H),Image.LANCZOS)
def text(fr,t,cy,size,color=WHITE,font=None,shadow=0.85,x=W/2):
    f=font or F(B.AR_BLACK,size); ov=Image.new('RGBA',fr.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    d.text((x,cy),t,font=f,fill=color+(255,),anchor='mm',direction='rtl',language='ar')
    g=Image.new('RGBA',fr.size,(0,0,0,0)); g.putalpha(ov.split()[3].filter(ImageFilter.GaussianBlur(16)).point(lambda v:int(v*shadow))); fr.alpha_composite(g); fr.alpha_composite(ov)
def shade(fr,top=0,bottom=0):
    a=np.zeros(H,np.float32)
    if top: a=np.maximum(a,np.clip(1-np.arange(H)/top,0,1)**1.2*200)
    if bottom: a=np.maximum(a,np.clip((np.arange(H)-(H-bottom))/bottom,0,1)**1.2*235)
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.putalpha(Image.fromarray(np.repeat(a[:,None],W,1).astype('uint8'))); fr.alpha_composite(L)
def contacts(fr,y,col=WHITE):
    fc=F(B.CT_FONT,50); isz=52; d=ImageDraw.Draw(fr)
    ic={k:Image.new('RGBA',(isz,isz),col+(255,)) for k in ('ig','fb','wa','ph')}
    for k,v in B.load_icons(isz).items():
        m=(np.asarray(v,np.float32)[...,3]*np.asarray(v.convert('L'),np.float32)/255).astype('uint8'); ic[k].putalpha(Image.fromarray(m))
    for keys,t in ((('ig','fb'),'callrenttr'),(('wa','ph'),'+90 555 034 22 00')):
        w=len(keys)*(isz+10)+8+d.textbbox((0,0),t,font=fc)[2]; x=(W-w)/2
        for k in keys: fr.alpha_composite(ic[k],(int(x),int(y-isz/2))); x+=isz+10
        d.text((x+8,y),t,font=fc,fill=col,anchor='lm'); y+=86
def logo(fr,y,w=620):
    lg=Image.open(B.LOGO_WHITE).convert('RGBA'); lg=lg.resize((w,int(w*lg.height/lg.width)),Image.LANCZOS); fr.alpha_composite(lg,((W-w)//2,y)); return lg.height
def sheet(frames,title,sub,out,cols=4):
    PW,PH=405,720; GAP=34; CAP=250; rows=(len(frames)+cols-1)//cols
    Wd=cols*PW+(cols+1)*GAP; Hd=230+rows*(PH+CAP)+(rows+1)*GAP
    s=Image.new('RGB',(Wd,Hd),BG); d=ImageDraw.Draw(s)
    d.text((Wd/2,78),title,font=F(B.AR_BLACK,50),fill=WHITE,anchor='mm',direction='rtl',language='ar')
    d.text((Wd/2,152),sub,font=F('NotoKufiArabic-Regular.ttf',30),fill=OR,anchor='mm',direction='rtl',language='ar')
    for i,(im,tm,l1,l2,l3) in enumerate(frames):
        r=i//cols; c=cols-1-(i%cols); x=GAP+c*(PW+GAP); y=230+GAP+r*(PH+CAP+GAP)
        d.rounded_rectangle((x-8,y-8,x+PW+8,y+PH+CAP-14),radius=22,fill=CARD)
        s.paste(im.convert('RGB').resize((PW,PH),Image.LANCZOS),(x,y))
        d.ellipse((x+14,y+14,x+66,y+66),fill=OR); d.text((x+40,y+40),str(i+1),font=F(B.LT_BOLD,30),fill=WHITE,anchor='mm')
        d.text((x+PW/2,y+PH+34),tm,font=F(B.LT_TEXT,28),fill=OR,anchor='mm')
        d.text((x+PW/2,y+PH+84),l1,font=F(B.AR_BOLD,30),fill=WHITE,anchor='mm',direction='rtl',language='ar')
        d.text((x+PW/2,y+PH+138),l2,font=F('NotoKufiArabic-Regular.ttf',24),fill=MUTED,anchor='mm',direction='rtl',language='ar')
        d.text((x+PW/2,y+PH+186),l3,font=F('NotoKufiArabic-Regular.ttf',24),fill=(120,190,230),anchor='mm',direction='rtl',language='ar')
    s.save(out,quality=92)

def idea1():
    f=[img(f'a{i}') for i in range(1,8)]
    shade(f[1],top=560); text(f[1],'أوّل ما يصلك في المطار…',240,72); text(f[1],'ليس حقيبتك',360,100,OR)
    end=f[6].copy().filter(ImageFilter.GaussianBlur(14)); end.alpha_composite(Image.new('RGBA',(W,H),(6,9,14,175)))
    text(end,'حقيبتك تأخّرت؟',560,84); text(end,'سيارتك لا',680,96,OR)
    text(end,'استلام وتسليم في المطار',820,52,(225,230,238),F(B.AR_BOLD,52))
    h=logo(end,1040); contacts(end,1040+h+110)
    text(end,'الخدمة برسوم إضافية · وفق الشروط والأحكام',1830,28,MUTED,F('NotoKufiArabic-Regular.ttf',28))
    fr=[(f[0],'0:00 – 0:01.5','سير الحقائب ليلاً','حقائب سوداء تدور · إضاءة خافتة','صوت: هدير السير وصدى الصالة'),
        (f[1],'0:01.5 – 0:03.5','الهوك: مفتاح على السير','بين الحقائب… مفتاح سيارة','صوت: رنّة معدنية خفيفة'),
        (f[2],'0:03.5 – 0:05','يدٌ تلتقط المفتاح','لقطة قريبة وبطيئة','صوت: خشخشة المفتاح'),
        (f[3],'0:05 – 0:06.5','ضغطة على زر الفتح','الإبهام على الريموت','صوت: نقرة الزر'),
        (f[4],'0:06.5 – 0:08.5','السيارة تردّ من الخارج','أضواء الـ i20 تومض أمام الوصول','صوت: صفّارة الفتح مرّتين'),
        (f[5],'0:08.5 – 0:11','المسافر يخرج إليها','حقيبة تُجرّ نحو السيارة','صوت: عجلات الحقيبة وخطوات'),
        (f[6],'0:11 – 0:13.5','الانطلاق من المطار','الأضواء الخلفية وبرج المراقبة','صوت: المحرك ينطلق بهدوء'),
        (end,'0:13.5 – 0:17','الخاتمة','النص + الشعار + التواصل','صوت: ضربة موسيقية ناعمة')]
    sheet(fr,'ستوري بورد · استلام وتسليم في المطار · «المفتاح على السير»','ريل 17 ثانية · ليلي غامق · بدون مطر · هونداي i20 حمراء','storyboard-1-key-carousel.jpg')

# ---------------- split-flap board ----------------
from PIL import ImageFont
MONO=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',46)
MONO_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',24)
AMBER=(255,196,92); RED_=(255,72,72); GREEN=(70,225,140)
COLS=(6,10,7); TW_,TH_=40,62; GAPC=18
def tile(ch,col,flip=0.0):
    t=Image.new('RGBA',(TW_,TH_),(0,0,0,0)); d=ImageDraw.Draw(t)
    d.rounded_rectangle((0,0,TW_-1,TH_-1),radius=5,fill=(28,30,34))
    d.rounded_rectangle((0,0,TW_-1,TH_//2),radius=5,fill=(36,38,43))
    if ch.strip(): d.text((TW_/2,TH_/2+1),ch,font=MONO,fill=col,anchor='mm')
    d.line((0,TH_//2,TW_,TH_//2),fill=(8,8,10),width=2)
    if flip>0:                                   # a flap caught mid-turn
        h=int(TH_/2*(1-flip)); d.rectangle((1,TH_//2-h,TW_-2,TH_//2),fill=(46,48,54))
    return t
def board(rows,flip_row=None,seed=0,title='DEPARTURES  ·  المغادرة',compact=False):
    rng=np.random.default_rng(seed)
    COLS_=COLS[1:] if compact else COLS
    if compact: rows=[(c[1:],k[1:]) for c,k in rows]
    n=sum(COLS_); bw=n*TW_+ (n-1)*3 + 2*GAPC + 60; bh=120+len(rows)*(TH_+16)+30
    b=Image.new('RGBA',(bw,bh),(10,11,13,255)); d=ImageDraw.Draw(b)
    d.rectangle((0,0,bw-1,bh-1),outline=(60,62,68),width=4)
    d.text((30,52),'DEPARTURES',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',40),fill=AMBER,anchor='lm')
    x=30; hx=[]
    for c in COLS_: hx.append(x); x+=c*(TW_+3)+GAPC
    for lbl,xx in zip((('DESTINATION','STATUS') if compact else ('FLIGHT','DESTINATION','STATUS')),hx): d.text((xx,100),lbl,font=MONO_S,fill=(150,150,150),anchor='lm')
    for r,(cells,cols) in enumerate(rows):
        y=124+r*(TH_+16)
        if cols[-1]==GREEN: d.rounded_rectangle((18,y-8,bw-18,y+TH_+8),radius=8,outline=OR,width=3)
        for ci,(txt,ncol) in enumerate(zip(cells,COLS_)):
            txt=txt.ljust(ncol)[:ncol]
            for k,ch in enumerate(txt):
                fl=0.0; c=cols[ci]
                if flip_row==r:
                    ch=chr(int(rng.integers(65,91))) if rng.random()<0.8 else ch; fl=float(rng.random())*0.9
                b.alpha_composite(tile(ch,c,fl),(hx[ci]+k*(TW_+3),y))
    return b
DLY=lambda f,d:((f,d,'DELAYED'),(AMBER,AMBER,RED_))
ROWS=[DLY('AX 204','LONDON'),DLY('BN 318','DUBAI'),DLY('KD 771','PARIS'),DLY('MS 902','ROME'),DLY('QF 115','BERLIN'),DLY('ZL 640','AMSTERDAM')]
READY_ROW=(('CR 001','CALL&RENT','READY'),(AMBER,OR,GREEN))
def board_frame(bg,brd,y0=560,scale=None):
    fr=bg.copy().filter(ImageFilter.GaussianBlur(10)); fr.alpha_composite(Image.new('RGBA',(W,H),(4,6,10,150)))
    s=scale or (W-40)/brd.width; bb=brd.resize((int(brd.width*s),int(brd.height*s)),Image.LANCZOS)
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); glow.alpha_composite(Image.new('RGBA',bb.size,(255,180,90,60)),((W-bb.width)//2,y0))
    fr.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40))); fr.alpha_composite(bb,((W-bb.width)//2,y0)); return fr
def idea2():
    hall=img('b1')
    f1=board_frame(hall,board(ROWS,compact=True),y0=520); shade(f1,top=520); text(f1,'كل شيء قد يتأخّر…',300,80)
    rows2=list(ROWS); f2=board_frame(hall,board(rows2,flip_row=3,seed=4,compact=True),y0=520); shade(f2,top=520); text(f2,'كل شيء قد يتأخّر…',300,80)
    rows3=list(ROWS); rows3[3]=READY_ROW; f3=board_frame(hall,board(rows3,compact=True),y0=520); shade(f3,top=520); text(f3,'كل شيء قد يتأخّر…',260,72); text(f3,'إلا سيارتك',380,104,OR)
    # wide: the hall with the board on its wall (tilt down starts here)
    f4=hall.copy(); brd=board(rows3); s=900/brd.width; bb=brd.resize((900,int(brd.height*s)),Image.LANCZOS); f4.alpha_composite(bb,(70,190))
    f5,f6,f7=img('b2'),img('b3'),img('b4')
    end=board_frame(img('b3'),board([READY_ROW],title='',compact=True),y0=1300)
    text(end,'سيارتك جاهزة',420,96,OR); text(end,'لحظة وصولك',540,84)
    text(end,'استلام وتسليم في المطار',680,52,(225,230,238),F(B.AR_BOLD,52))
    h=logo(end,820,560); contacts(end,820+h+90)
    text(end,'الخدمة برسوم إضافية · وفق الشروط والأحكام',1830,28,MUTED,F('NotoKufiArabic-Regular.ttf',28))
    fr=[(f1,'0:00 – 0:02','الهوك: لوحة المغادرة','كل الرحلات «DELAYED» بالأحمر','صوت: طقطقة الحروف + صدى الصالة'),
        (f2,'0:02 – 0:03','سطر واحد يتقلّب','الحروف تدور بسرعة','صوت: تكتكة متسارعة'),
        (f3,'0:03 – 0:05','CALL & RENT · READY','«إلا سيارتك» بالبرتقالي','صوت: توقّف الحروف + نغمة'),
        (f4,'0:05 – 0:06.5','الكاميرا تنزل من اللوحة','الصالة والمسافرون تحتها','صوت: إعلان مطار خافت'),
        (f5,'0:06.5 – 0:08.5','خطوات سريعة في الممر','حقيبة تُجرّ بثقة','صوت: عجلات الحقيبة وخطوات'),
        (f6,'0:08.5 – 0:10.5','الأبواب تنفتح','الـ i20 بانتظاره بالأضواء','صوت: انزلاق الباب الآلي'),
        (f7,'0:10.5 – 0:13','تسليم المفتاح','موظّفنا يسلّمه المفتاح','صوت: رنّة المفتاح + صفّارة الفتح'),
        (end,'0:13 – 0:17','الخاتمة','سطر READY + الشعار + التواصل','صوت: نغمة ختام ناعمة')]
    sheet(fr,'ستوري بورد · استلام وتسليم في المطار · «لوحة المغادرة»','ريل 17 ثانية · ليلي غامق · هونداي i20 حمراء · اللوحة تُصمَّم بالمونتاج','storyboard-2-departure-board.jpg')

def idea1v2():
    f={k:img(k) for k in ('h1','f2','f3','g4','c5','n6','t7','t8','a7')}
    shade(f['f2'],top=560); text(f['f2'],'أوّل ما يصلك في المطار…',240,72); text(f['f2'],'ليس حقيبتك',360,100,OR)
    end=f['a7'].copy().filter(ImageFilter.GaussianBlur(14)); end.alpha_composite(Image.new('RGBA',(W,H),(6,9,14,175)))
    text(end,'حقيبتك تأخّرت؟',560,84); text(end,'سيارتك لا',680,96,OR)
    text(end,'استلام وتسليم في المطار',820,52,(225,230,238),F(B.AR_BOLD,52))
    h=logo(end,1040); contacts(end,1040+h+110)
    text(end,'الخدمة برسوم إضافية · وفق الشروط والأحكام',1830,28,MUTED,F('NotoKufiArabic-Regular.ttf',28))
    fr=[(f['h1'],'0:00 – 0:03','سير الحقائب ليلاً','لقطة متّصلة 1/3 · السلّة قادمة','صوت: صدى الصالة + نبض باص خفيف'),
        (f['f2'],'0:03 – 0:06','الهوك: سلّة التفتيش','لقطة متّصلة 2/3 · تظهر الكتابة','صوت: سكون مفاجئ + رنّة المفتاح'),
        (f['f3'],'0:06 – 0:08','يدٌ تأخذ المفتاح','لقطة متّصلة 3/3 · اليد من اليمين','صوت: خشخشة المفتاح'),
        (f['g4'],'0:08 – 0:10.5','ضغطة على زر الفتح','مفتاح هونداي · الشعار على الميدالية','صوت: «كليك» واضحة'),
        (f['c5'],'0:10.5 – 0:14','السيارة تردّ من الخارج','أضواء الـ i20 تومض · علم تركيا','صوت: صفّارة الفتح + ضربة الموسيقى'),
        (f['n6'],'0:14 – 0:17','المسافر يخرج إليها','حقيبة كحلية تُجرّ نحو السيارة','صوت: عجلات الحقيبة خفيفة'),
        (f['t7'],'0:17 – 0:18.5','الحقيبة داخل الصندوق','بداية اللقطة · حقيبة مقصورة صغيرة','صوت: الحقيبة تنزلق للداخل'),
        (f['t8'],'0:18.5 – 0:19.5','الصندوق يُغلق','نهاية اللقطة · مغلق تماماً','صوت: «طَق» على الإيقاع'),
        (f['a7'],'0:19.5 – 0:23','الانطلاق من المطار','الأضواء الخلفية وبرج المراقبة','صوت: المحرك منخفض + ذروة الموسيقى'),
        (end,'0:23 – 0:26.5','الخاتمة','النص + الشعار + التواصل','صوت: ضربة أخيرة عميقة وصدى')]
    sheet(fr,'ستوري بورد · استلام وتسليم في المطار · «المفتاح على السير» · نسخة 10','ريل 26 ثانية · ليلي غامق · أول 3 لقطات مشهد واحد متّصل · حقيبة كحلية · هونداي i20 حمراء','storyboard-1-key-carousel-v10.jpg',cols=5)

if __name__=='__main__':
    import sys as _s
    {'idea2':idea2,'idea1v2':idea1v2}.get(_s.argv[-1],idea1)(); print('ok')
