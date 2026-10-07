from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os

W,H,FPS = 1080,1920,24
DUR = 7.6; N = int(DUR*FPS)
os.makedirs('ap_out', exist_ok=True)

# ---- exact brand values sampled from the new logo file -----------------------
ORANGE = (244,141,87)     # #F48D57  — measured modal colour of the logo wedge
LOGONAVY = (29,69,99)     # #1D4563  — measured navy of the dark logo
WHITE  = (255,255,255)
SOFT   = (203,216,228)

# ---- cinematic navy field ----------------------------------------------------
# One continuous Gaussian key light on a deep navy ground, a wide anamorphic
# falloff, a corner vignette and fine grain. No banding, no visible edges.
KEY  = np.array([ 46,104,150], np.float32)   # where the light lands
DEEP = np.array([  8, 24, 41], np.float32)   # the ground it falls off to

ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
CX, CY = W/2.0, H/2.0
R  = np.sqrt((xs-CX)**2 + (ys-CY)**2)          # true radius — the iris uses this
# the light pool is drawn on a stretched radius, so it reads anamorphic, not round
LCY = 1000.0
RL = np.sqrt(((xs-CX)/1.42)**2 + ((ys-LCY)/1.00)**2) / 1101.0
key = np.exp(-0.5*(RL/0.47)**2)[...,None]
bg  = DEEP[None,None,:] + (KEY-DEEP)[None,None,:]*key

# warm ember left behind where the point was born
ember = np.exp(-0.5*(R/230.0)**2)[...,None]
bg = bg + np.array(ORANGE,np.float32)[None,None,:]*ember*0.07

# corner vignette, on the true radius so all four corners sink equally
vg = np.clip(R/1101.0, 0, 1)
bg = bg * (1.0 - 0.34*(vg**2.3))[...,None]

# fine grain so the gradient never bands under h.264
rng = np.random.default_rng(7)
bg = np.clip(bg + rng.normal(0, 2.0, (H,W,1)).astype(np.float32), 0, 255)
NAVY_BG = bg

# ---- type --------------------------------------------------------------------
def T(n,s): return ImageFont.truetype('fonts/'+n, s)
_m = ImageDraw.Draw(Image.new('RGB',(10,10)))
def w_ar(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='rtl',language='ar'); return b[2]-b[0]
def w_lt(t,f):
    b=_m.textbbox((0,0),t,font=f,direction='ltr',language='en'); return b[2]-b[0]

L1, L2 = 'من طيارتك', 'لسيارتك'
# Noto Kufi Arabic Black: squared, flat-terminal, open counters — the Arabic
# equivalent of the logo's geometric squared Latin.
fL = T('NotoKufiArabic-Black.ttf', 112)
fS = T('Oxanium-800.ttf', 36)
fC = T('Oxanium-600.ttf', 42)
SLOGAN = 'DRIVE YOUR DREAMS, DISCOVER ISTANBUL'

logo = Image.open('newlogo_59.png').convert('RGBA')
LW   = 840
logo = logo.resize((LW, round(LW*logo.height/logo.width)), Image.LANCZOS)
LY   = 690
ICON = 46
ic = {k: Image.open(v).convert('RGBA').resize((ICON,ICON), Image.LANCZOS) for k,v in
      (('ig','icon-instagram.png'), ('fb','icon-facebook.png'),
       ('wa','icon-whatsapp-white.png'), ('ph','icon-call-white.png'))}
ROWS = [(('ig','fb'), 'callrenttr'), (('wa','ph'), '+90 555 034 22 00')]

last = Image.open('ap_last.png').convert('RGB').resize((W,H), Image.LANCZOS)
LAST = np.asarray(last, np.float32)

def ramp(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    x=(t-a)/(b-a); return x*x*(3-2*x)
def ease_out(x): return 1-(1-x)**3
def layer(fn,al):
    if al<=0.004: return None
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); fn(ImageDraw.Draw(ov),ov)
    if al<1.0: ov.putalpha(ov.split()[3].point(lambda v:int(v*al)))
    return ov
def glow(fr,g,rad,amt):
    fr.alpha_composite(Image.merge('RGBA', g.split()[:3] +
        (g.split()[3].filter(ImageFilter.GaussianBlur(rad)).point(lambda v:int(v*amt)),)))
    fr.alpha_composite(g)
def spaced(d, txt, cx, cy, font, fill, track):
    wtot = sum(w_lt(c,font) for c in txt) + track*(len(txt)-1)
    x = cx - wtot/2
    for c in txt:
        d.text((x, cy), c, font=font, fill=fill, anchor='lm', direction='ltr', language='en')
        x += w_lt(c,font) + track

def head_line(fr, text, cy, alpha, lift, col):
    if alpha <= 0.004: return
    ov = Image.new('RGBA',(W,H),(0,0,0,0)); d = ImageDraw.Draw(ov)
    d.text((W//2, cy + lift), text, font=fL, fill=col+(255,),
           anchor='mm', direction='rtl', language='ar')
    ov.putalpha(ov.split()[3].point(lambda v:int(v*alpha)))
    glow(fr, ov, 28, 0.45)

# ---- iris geometry -----------------------------------------------------------
T0, T1 = 0.22, 1.30          # the bloom
RMAX   = 1180.0
ORA    = np.array(ORANGE, np.float32)

for i in range(N):
    t = i/FPS
    p = ramp(t, T0, T1)
    r = ease_out(p) * RMAX

    if p >= 1.0:
        base = NAVY_BG.copy()
    else:
        # the held frame pushes in very slightly behind the reveal
        pu = ramp(t, 0.0, T1)
        sc = 1.0 + 0.055*pu
        if sc > 1.001:
            nw, nh = int(W*sc), int(H*sc)
            bgf = np.asarray(last.resize((nw,nh), Image.LANCZOS)
                             .crop(((nw-W)//2,(nh-H)//2,(nw-W)//2+W,(nh-H)//2+H)), np.float32)
        else:
            bgf = LAST
        a = np.clip((r - R)/2.5, 0, 1)[...,None]
        base = bgf*(1-a) + NAVY_BG*a

        if r > 0.5:
            fade = 1.0 - ramp(p, 0.80, 1.0)
            # wide bloom around the leading edge
            g2 = np.exp(-0.5*((R-r)/30.0)**2)[...,None]
            base = base + ORA[None,None,:]*g2*(0.62*fade)
            # the hard rim itself
            g1 = np.clip(1.0 - np.abs(R-r)/4.0, 0, 1)[...,None]*fade
            base = base*(1-g1) + ORA[None,None,:]*g1
            # a thinner ring running ahead of it, dissipating
            rip = 1.0 - ramp(p, 0.10, 0.62)
            if rip > 0.01:
                g3 = np.exp(-0.5*((R-r*1.22)/16.0)**2)[...,None]
                base = base + ORA[None,None,:]*g3*(0.30*rip)
        else:
            # the point itself, before it opens
            q   = ramp(t, 0.02, T0)
            sig = 4.0 + 20.0*q
            g0  = np.exp(-0.5*(R/sig)**2)[...,None]
            base = base + ORA[None,None,:]*g0*(0.35 + 0.65*q)
            gh  = np.exp(-0.5*(R/(sig*0.35))**2)[...,None]
            base = base*(1-gh) + np.array([255,232,214],np.float32)[None,None,:]*gh

    fr = Image.fromarray(np.clip(base,0,255).astype('uint8')).convert('RGBA')

    a1 = ramp(t,1.35,2.10) * (1.0 - ramp(t,3.45,4.05))
    a2 = ramp(t,1.62,2.37) * (1.0 - ramp(t,3.50,4.10))
    head_line(fr, L1, 786, a1, int(44*(1-ramp(t,1.35,2.10))), WHITE)
    head_line(fr, L2, 968, a2, int(44*(1-ramp(t,1.62,2.37))), ORANGE)

    aLogo = ramp(t,4.00,4.90)
    if aLogo > 0.004:
        sc = 0.93 + 0.07*ease_out(min(1.0,(t-4.00)/0.9))
        lw, lh = int(LW*sc), int(logo.height*sc)
        lg = logo.resize((lw,lh), Image.LANCZOS)
        ov = Image.new('RGBA',(W,H),(0,0,0,0))
        ov.alpha_composite(lg, (W//2-lw//2, LY + (logo.height-lh)//2))
        ov.putalpha(ov.split()[3].point(lambda v:int(v*aLogo)))
        glow(fr, ov, 30, 0.35)

    aR = ramp(t,4.70,5.20)
    if aR > 0.004:
        g = layer(lambda d,ov: d.rectangle(
            [W//2-int(170*aR),1038,W//2+int(170*aR),1041], fill=ORANGE+(255,)), 1.0)
        fr.alpha_composite(g)
    aS = ramp(t,4.95,5.55)
    if aS > 0.004:
        g = layer(lambda d,ov: spaced(d, SLOGAN, W//2, 1102, fS, ORANGE+(255,), 3.2), aS)
        fr.alpha_composite(g)

    aC = ramp(t,5.45,6.15)
    if aC > 0.004:
        def dC(d,ov):
            y2 = 1262
            for icons, txt in ROWS:
                wt = w_lt(txt,fC); x = W//2 - (ICON*2+14+22+wt)//2
                for nm in icons:
                    ov.alpha_composite(ic[nm], (x, y2-ICON//2)); x += ICON+14
                d.text((x+10, y2), txt, font=fC, fill=WHITE+(255,), anchor='lm',
                       direction='ltr', language='en')
                y2 += 84
        g = layer(dC,aC); fr.alpha_composite(g)

    fr.convert('RGB').save(f'ap_out/{i:04d}.png')
print('frames', N)
