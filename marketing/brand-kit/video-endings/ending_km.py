from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, glob
from brand import (ORANGE, WHITE, SOFT, AR_BLACK, AR_BOLD, LT_BOLD, LT_TEXT,
                   navy_field, load_logo, load_icons, draw_slogan, draw_contacts)

W,H,FPS = 1080,1920,24
DUR = 6.2
N   = int(DUR*FPS)
LIVE = sorted(glob.glob('k_src/*.png'))
NL   = len(LIVE)
HOLD = Image.open(LIVE[-1]).convert('RGB')

GOLD  = ORANGE
SOFTG = WHITE + (255,)
NAVY = navy_field()           # graded cinematic navy, not a flat fill

def T(n,s): return ImageFont.truetype('fonts/'+n, s)
_m = ImageDraw.Draw(Image.new('RGB',(10,10)))
def w_ar(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='rtl',language='ar'); return b[2]-b[0]
def fit(txt, name, maxw, start):
    s=start
    while s>24:
        f=T(name,s)
        if w_ar(txt,f)<=maxw: return f
        s-=2
    return T(name,24)

L1 = 'من آسيا لأوروبا'
L2A = 'عدّاد مفتوح'
L2B = None
f1 = fit(L1,AR_BLACK, 930, 118)
f2 = fit(L2A,AR_BLACK, 900, 104)
fC = T('Tajawal-Bold.ttf', 40)   # contacts: the original face

LW   = 820
logo = load_logo(LW)
ICON = 46
ic   = load_icons(ICON)
def w_lt(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='ltr',language='en'); return b[2]-b[0]

_y   = np.arange(H, dtype=np.float32)
GRAD = np.repeat((np.clip(1.0-_y/1320.0,0,1)**1.15 * 0.78)[:,None], W, axis=1)

def ramp(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    x=(t-a)/(b-a); return x*x*(3-2*x)
def pulse(t,a,b,c,d): return ramp(t,a,b)*(1.0-ramp(t,c,d))
def layer(fn,al):
    if al<=0.004: return None
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); fn(ImageDraw.Draw(ov),ov)
    if al<1.0: ov.putalpha(ov.split()[3].point(lambda v:int(v*al)))
    return ov
def glow(fr,g,rad,amt):
    fr.alpha_composite(Image.merge('RGBA', g.split()[:3] +
        (g.split()[3].filter(ImageFilter.GaussianBlur(rad)).point(lambda v:int(v*amt)),)))
    fr.alpha_composite(g)

for i in range(N):
    t=i/FPS
    if i<NL:
        base=Image.open(LIVE[i]).convert('RGB')
    else:
        z=1.0+0.035*((i-NL)/(N-NL)); nw,nh=int(W*z),int(H*z)
        base=HOLD.resize((nw,nh),Image.LANCZOS).crop(((nw-W)//2,(nh-H)//2,(nw-W)//2+W,(nh-H)//2+H))
    a=np.asarray(base,np.float32)
    k1=ramp(t,0.3,1.2); k2=ramp(t,3.0,3.9)
    sc=(GRAD*k1)[:,:,None]
    a=a*(1.0-sc)+NAVY*sc
    a=a*(1.0-0.988*k2)+NAVY*(0.988*k2)   # settle on a clean navy field
    fr=Image.fromarray(np.clip(a,0,255).astype('uint8'))
    if k2>0.02: fr=Image.blend(fr, fr.filter(ImageFilter.GaussianBlur(8.0)), min(1.0,k2))
    fr=fr.convert('RGBA')

    a1=pulse(t,0.5,1.4,2.9,3.5); a2=pulse(t,1.6,2.4,3.0,3.6)
    a3=ramp(t,3.60,4.40); aR=ramp(t,4.25,4.70)
    aS=ramp(t,4.50,5.05); a4=ramp(t,5.00,5.65)

    def d1(d,ov): d.text((W//2,340), L1, font=f1, fill=WHITE+(255,), anchor='mm',
                         direction='rtl', language='ar')
    def d2(d,ov):
        d.text((W//2,528), L2A, font=f2, fill=GOLD+(255,), anchor='mm',
               direction='rtl', language='ar')
    def d3(d,ov): ov.alpha_composite(logo, ((W-LW)//2, 672))
    def dR(d,ov): d.rectangle([W//2-int(170*aR),983,W//2+int(170*aR),986], fill=ORANGE+(255,))
    def dS(d,ov): draw_slogan(d, 1045)
    def d4(d,ov): draw_contacts(d, ov, 1180, fC, ic, isz=ICON)

    g=layer(d1,a1);  glow(fr,g,26,0.75) if g else None
    g=layer(d2,a2);  glow(fr,g,28,0.85) if g else None
    g=layer(d3,a3);  glow(fr,g,38,0.50) if g else None
    if aR>0.004: fr.alpha_composite(layer(dR,1.0))
    if aS>0.004: fr.alpha_composite(layer(dS,aS))
    g=layer(d4,a4);  fr.alpha_composite(g) if g else None
    fr.convert('RGB').save(f'k_out/{i:04d}.png')
print('frames',N,'live',NL)
