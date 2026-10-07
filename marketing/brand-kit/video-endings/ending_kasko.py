from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, glob
from brand import (ORANGE, WHITE, SOFT, AR_BLACK, AR_BOLD, LT_BOLD, LT_TEXT,
                   navy_field, load_logo, load_icons, draw_slogan, draw_contacts)

W,H,FPS = 1080,1920,24
LIVE = sorted(glob.glob('ks_src/*.png'))      # 11.90 -> 16.05, the pulsing shot
NL   = len(LIVE)
TAIL = 5.6                                     # the logo sequence after the film ends
NT   = int(TAIL*FPS)
T0   = 11.90                                   # world time of LIVE[0]

GOLD  = ORANGE                 # the brand accent replaces the old gold
SOFTG = WHITE + (255,)
RULEG = ORANGE

def T(n,s): return ImageFont.truetype('fonts/'+n, s)
_m = ImageDraw.Draw(Image.new('RGB',(10,10)))
def w_ar(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='rtl',language='ar'); return b[2]-b[0]
def w_lt(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='ltr',language='en'); return b[2]-b[0]
def fit(txt,name,maxw,start):
    s=start
    while s>24:
        f=T(name,s)
        if w_ar(txt,f)<=maxw: return f
        s-=2
    return T(name,24)

L1 = 'حماية كاملة'
L2 = 'تأمين شامل'
f1 = fit(L1,AR_BLACK, 900, 112)
f2 = fit(L2,AR_BLACK, 900, 100)
fC = T('Tajawal-Bold.ttf', 40)   # contacts: the original face

LW   = 820
logo = load_logo(LW)
LX, LY = (W-LW)//2, 672          # same layout as the approved end card
ICON = 46
ic   = load_icons(ICON)
NAVY = navy_field()            # graded cinematic navy, not a flat fill

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

# ---- measure the real golden pulse so the type breathes with the light ----
gold=[]
for p in LIVE:
    a=np.asarray(Image.open(p).convert('RGB').resize((160,284)),np.float32)
    gold.append(float(((a[...,0]+a[...,1])/2 - a[...,2]).clip(0).mean()))
gold=np.array(gold); gold=(gold-gold.min())/(gold.max()-gold.min()+1e-6)

def d1(d,ov): d.text((W//2,330), L1, font=f1, fill=WHITE+(255,), anchor='mm',
                     direction='rtl', language='ar')
def d2(d,ov): d.text((W//2,486), L2, font=f2, fill=GOLD+(255,), anchor='mm',
                     direction='rtl', language='ar')

# ================= part A : titles over the live pulses =================
for i,p in enumerate(LIVE):
    t = T0 + i/FPS
    fr = Image.open(p).convert('RGBA')
    g  = gold[i]
    a1 = pulse(t,11.98,12.35,15.35,15.95) * (0.50 + 0.50*g)   # rides pulse 1
    a2 = pulse(t,13.28,13.65,15.40,16.00) * (0.50 + 0.50*g)   # rides pulse 2
    L  = layer(d1,a1);  glow(fr,L,30,0.85) if L else None
    L  = layer(d2,a2);  glow(fr,L,26,0.85) if L else None
    fr.convert('RGB').save(f'ks_out/{i:04d}.png')

# ================= part B : the logo, revealed by a golden sweep =========
last = Image.open(LIVE[-1]).convert('RGB')
logo_rgb = logo.convert('RGB'); logo_a = np.asarray(logo.split()[3], np.float32)/255.0
xs = np.arange(W, dtype=np.float32)

for j in range(NT):
    t = j/FPS
    base = np.asarray(last, np.float32)
    dark = ramp(t,0.0,1.1)
    a = base*(1.0-dark) + NAVY*dark           # settle fully on navy — no ghost of the car
    fr = Image.fromarray(np.clip(a,0,255).astype('uint8')).convert('RGBA')

    sweep = ramp(t,0.8,2.2)
    if sweep > 0:
        edge = -260 + sweep*(W+520)                       # the light bar's position
        # logo revealed behind the bar
        revealed = np.clip((edge - (xs - LX))/90.0, 0, 1)[None,:]
        lay = Image.new('RGBA',(W,H),(0,0,0,0))
        la  = Image.fromarray((logo_a*revealed[:, LX:LX+LW]*255).astype('uint8'))
        chip = logo_rgb.copy(); chip.putalpha(la)
        lay.alpha_composite(chip,(LX,LY))
        glow(fr, lay, 34, 0.45)
        # the travelling light bar itself
        if sweep < 1.0:
            bar = Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(bar)
            bd.rectangle([edge-3, LY-70, edge+3, LY+logo.height+70], fill=GOLD+(255,))
            fr.alpha_composite(bar.filter(ImageFilter.GaussianBlur(26)))
            fr.alpha_composite(bar.filter(ImageFilter.GaussianBlur(4)))

    ru = ramp(t,2.50,3.00)
    if ru > 0.004:
        def dr(d,ov):
            half=int(170*ru); d.rectangle([W//2-half,983,W//2+half,986], fill=RULEG+(255,))
        fr.alpha_composite(layer(dr,1.0))

    sl = ramp(t,2.85,3.45)
    if sl > 0.004:
        fr.alpha_composite(layer(lambda d,ov: draw_slogan(d, 1045), sl))

    ct = ramp(t,3.40,4.20)
    if ct > 0.004:
        L=layer(lambda d,ov: draw_contacts(d, ov, 1180, fC, ic, isz=ICON), ct)
        fr.alpha_composite(L)

    fr.convert('RGB').save(f'ks_out/{NL+j:04d}.png')

print('frames', NL+NT, ' live', NL, ' tail', NT)
