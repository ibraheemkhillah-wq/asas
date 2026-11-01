"""CALL & RENT brand kit: colours, fonts, logos, icons, text measuring.

Rebuilt on 2026-11-01 after the scratchpad was lost: fonts from Google Fonts / Noto, logos and icons
extracted (with alpha) from the committed 2160px renders in marketing/*/out.
"""
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))   # paths resolve inside the kit

ORANGE   = (244, 141,  87)   # #F48D57
LOGONAVY = ( 29,  69,  99)   # #1D4563
WHITE    = (255, 255, 255)
SOFT     = (203, 216, 228)   # secondary text on dark

AR_BLACK = 'NotoKufiArabic-Black.ttf'
AR_BOLD  = 'NotoKufiArabic-ExtraBold.ttf'
CT_FONT  = 'Tajawal-Bold.ttf'                 # contacts
LT_TEXT  = 'Oxanium-600.ttf'                  # Latin
LT_BOLD  = 'Oxanium-800.ttf'
LT_REG   = 'Oxanium-400.ttf'

LOGO_WHITE = os.path.join(HERE, 'logo', 'callrent-logo-white.png')
LOGO_NAVY  = os.path.join(HERE, 'logo', 'callrent-logo-navy.png')
SLOGAN = 'Drive Your Dreams, Discover Istanbul'


def F(name, size): return ImageFont.truetype(os.path.join(HERE, 'fonts', name), size)

_m = ImageDraw.Draw(Image.new('RGB', (10, 10)))
def w_lt(t, f):
    b = _m.textbbox((0,0), t, font=f, direction='ltr', language='en'); return b[2]-b[0]
def w_ar(t, f):
    b = _m.textbbox((0,0), t, font=f, direction='rtl', language='ar'); return b[2]-b[0]


def navy_field(cy=1000.0, seed=7, w=1080, h=1350):
    """A graded navy backdrop: one soft key light, deep corners, fine grain."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    KEY = np.array([46, 104, 150], np.float32); DK = np.array((8, 24, 41), np.float32)
    RL = np.sqrt(((xs - w/2)/1.3)**2 + ((ys - cy)/1.0)**2)/900
    bg = DK + (KEY - DK)*np.exp(-0.5*(RL/0.48)**2)[..., None]
    bg = np.clip(bg + np.random.default_rng(seed).normal(0, 2.0, (h, w, 1)), 0, 255).astype(np.uint8)
    return Image.fromarray(bg).convert('RGBA')


def load_icons(size=46):
    return {k: Image.open(os.path.join(HERE, 'icons', v)).convert('RGBA').resize((size,size), Image.LANCZOS)
            for k, v in (('ig','icon-instagram.png'), ('fb','icon-facebook.png'),
                         ('wa','icon-whatsapp-white.png'), ('ph','icon-call-white.png'))}

ROWS = [(('ig','fb'), 'callrenttr'), (('wa','ph'), '+90 555 034 22 00')]
