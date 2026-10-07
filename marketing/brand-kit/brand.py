"""CALL & RENT — new visual identity, shared by every ending."""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, os

HERE = os.path.dirname(os.path.abspath(__file__))   # paths resolve inside the kit

W, H = 1080, 1920

# measured from the supplied logo files, pixel for pixel
ORANGE   = (244, 141, 87)     # #F48D57
LOGONAVY = ( 29,  69, 99)     # #1D4563
WHITE    = (255, 255, 255)
SOFT     = (203, 216, 228)

LOGO_WHITE = os.path.join(HERE, 'logo', 'callrent-logo-white.png')
LOGO_NAVY  = os.path.join(HERE, 'logo', 'callrent-logo-navy.png')
AR_BLACK   = 'NotoKufiArabic-Black.ttf'   # squared kufic — matches the wordmark
AR_BOLD    = 'NotoKufiArabic-ExtraBold.ttf'
LT_BOLD    = 'Oxanium-800.ttf'            # closest free match to the wordmark
LT_TEXT    = 'Oxanium-600.ttf'
LT_REG     = 'Oxanium-400.ttf'            # slogan: regular weight, not bold
CT_FONT    = 'Tajawal-Bold.ttf'           # contacts keep the original face
SLOGAN     = 'Drive Your Dreams, Discover Istanbul'

def F(name, size): return ImageFont.truetype(os.path.join(HERE, 'fonts', name), size)

_m = ImageDraw.Draw(Image.new('RGB', (10, 10)))
def w_lt(t, f):
    b = _m.textbbox((0,0), t, font=f, direction='ltr', language='en'); return b[2]-b[0]
def w_ar(t, f):
    b = _m.textbbox((0,0), t, font=f, direction='rtl', language='ar'); return b[2]-b[0]

def navy_field(cy=1000.0, seed=7):
    """A graded navy backdrop: one soft key light, deep corners, fine grain."""
    KEY  = np.array([46,104,150], np.float32)
    DEEP = np.array([ 8, 24, 41], np.float32)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    R  = np.sqrt((xs-W/2)**2 + (ys-H/2)**2)
    RL = np.sqrt(((xs-W/2)/1.42)**2 + ((ys-cy)/1.0)**2) / 1101.0
    bg = DEEP[None,None,:] + (KEY-DEEP)[None,None,:]*np.exp(-0.5*(RL/0.47)**2)[...,None]
    bg = bg * (1.0 - 0.34*np.clip(R/1101.0, 0, 1)**2.3)[...,None]
    rng = np.random.default_rng(seed)
    return np.clip(bg + rng.normal(0, 2.0, (H,W,1)).astype(np.float32), 0, 255)

def load_logo(width):
    lg = Image.open(LOGO_WHITE).convert('RGBA')
    return lg.resize((width, round(width*lg.height/lg.width)), Image.LANCZOS)

def load_icons(size=46):
    return {k: Image.open(os.path.join(HERE, 'icons', v)).convert('RGBA').resize((size,size), Image.LANCZOS)
            for k, v in (('ig','icon-instagram.png'), ('fb','icon-facebook.png'),
                         ('wa','icon-whatsapp-white.png'), ('ph','icon-call-white.png'))}

ROWS = [(('ig','fb'), 'callrenttr'), (('wa','ph'), '+90 555 034 22 00')]

def spaced(d, txt, cx, cy, font, fill, track):
    wtot = sum(w_lt(c, font) for c in txt) + track*(len(txt)-1)
    x = cx - wtot/2
    for c in txt:
        d.text((x, cy), c, font=font, fill=fill, anchor='lm',
               direction='ltr', language='en')
        x += w_lt(c, font) + track

def draw_slogan(d, cy, size=42, track=1.0, fill=ORANGE+(255,)):
    spaced(d, SLOGAN, W//2, cy, F(LT_REG, size), fill, track)

def draw_contacts(d, ov, top, font, icons, step=84, isz=46, fill=WHITE+(255,)):
    y = top
    for keys, txt in ROWS:
        wt = w_lt(txt, font); x = W//2 - (isz*2 + 14 + 22 + wt)//2
        for k in keys:
            ov.alpha_composite(icons[k], (x, y - isz//2)); x += isz + 14
        d.text((x+10, y), txt, font=font, fill=fill, anchor='lm',
               direction='ltr', language='en')
        y += step
