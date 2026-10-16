"""CALL & RENT winter offer, rebuilt from scratch at high resolution, post + story.

usage: python3 winter_offer.py <brand-kit dir> <post bg> <story bg> <out dir>
Layout is written at 1080 wide and rendered K times larger (K=2 -> 2160 wide).
Neon type: orange outline glyphs with a warm bloom, like the original poster.
"""
import sys, os
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
from brand import ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_WHITE, load_icons, w_ar, w_lt

K = 2
NEON = (255, 170, 110)          # hot core of the orange tube
GLOW = (244, 141, 87)           # brand orange bloom
OFFER_RED = (200, 30, 45)       # «وفّر معنا» plate (fixed offers badge)


def S(v): return round(v*K)


def fit(src, w, h, focus_y=0.5):
    im = Image.open(src).convert('RGB')
    s = max(w/im.width, h/im.height)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l = (im.width-w)//2; t = int((im.height-h)*focus_y)
    return im.crop((l, t, l+w, t+h)).convert('RGBA')


def grade(cv, top_dark, bottom_from, bottom_k=0.85):
    w, h = cv.size; ys = np.arange(h, dtype=np.float32)
    for a in (np.clip(1-ys/(h*top_dark), 0, 1)**1.4*0.55, np.clip((ys-h*bottom_from)/(h*(1-bottom_from)), 0, 1)**1.1*bottom_k):
        lay = Image.new('RGBA', (w, h), (8, 20, 36, 0))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], w, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)


def neon_text(cv, xy, text, size, anchor='rs', rtl=True, stroke=None, glow=1.0):
    """Outline 'tube' lettering: hollow glyphs, bright core stroke, two-step bloom."""
    w, h = cv.size
    f = F(AR_BLACK, size) if rtl else F('Oxanium-800.ttf', size)
    kw = dict(direction='rtl', language='ar') if rtl else dict(direction='ltr', language='en')
    sw = stroke or max(2, round(size*0.045))
    tube = Image.new('L', (w, h), 0); td = ImageDraw.Draw(tube)
    td.text(xy, text, font=f, fill=255, anchor=anchor, stroke_width=sw, stroke_fill=255, **kw)
    hole = Image.new('L', (w, h), 0)
    ImageDraw.Draw(hole).text(xy, text, font=f, fill=255, anchor=anchor, **kw)
    hole = hole.filter(ImageFilter.MinFilter(max(3, (sw//2)*2+1)))   # keep a ring of tube inside each glyph
    ring = ImageChops.subtract(tube, hole)
    for radius, strength, col in ((S(26), 0.55*glow, GLOW), (S(9), 0.85*glow, GLOW)):
        b = ring.filter(ImageFilter.GaussianBlur(radius))
        lay = Image.new('RGBA', (w, h), col+(0,)); lay.putalpha(b.point(lambda v: min(255, int(v*strength*2.2))))
        cv.alpha_composite(lay)
    core = Image.new('RGBA', (w, h), NEON+(0,)); core.putalpha(ring)
    cv.alpha_composite(core)
    hot = Image.new('RGBA', (w, h), (255, 236, 214, 0)); hot.putalpha(ring.filter(ImageFilter.MinFilter(3)).point(lambda v: v//2))
    cv.alpha_composite(hot)
    return f


def neon_logo(cv, x, y, width):
    lg = Image.open(LOGO_WHITE).convert('RGBA')
    lg = lg.resize((width, round(width*lg.height/lg.width)), Image.LANCZOS)
    a = lg.getchannel('A')
    for radius, col, k in ((S(18), GLOW, 0.55), (S(6), (255, 220, 190), 0.7)):
        lay = Image.new('RGBA', cv.size, col+(0,)); m = Image.new('L', cv.size, 0); m.paste(a, (x, y))
        lay.putalpha(m.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v*k)))); cv.alpha_composite(lay)
    cv.alpha_composite(lg, (x, y))


def badge(cv, right, top):
    d = ImageDraw.Draw(cv); fb = F(AR_BOLD, S(26)); bh = S(58); label = 'وفّر معنا'
    bw = w_ar(label, fb) + S(64); bx = right - bw
    d.rounded_rectangle((bx, top, right, top+bh), radius=S(6), fill=OFFER_RED+(255,))
    d.polygon([(bx, top+bh-S(22)), (bx, top+bh), (bx+S(22), top+bh)], fill=LOGONAVY+(255,))
    d.text((bx+bw/2, top+bh/2+S(2)), label, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')


def footer(cv, y_contacts, y_terms):
    d = ImageDraw.Draw(cv); W = cv.width
    ic = load_icons(S(46)); fc = F(CT_FONT, S(40)); isz = S(46)
    groups = [(('ig', 'fb'), 'callrenttr'), (('wa', 'ph'), '+90 555 034 22 00')]
    widths = [2*isz + S(12) + S(14) + w_lt(t, fc) for _, t in groups]; sep = S(56)
    x = W/2 - (sum(widths) + sep)/2
    for gi, (keys, txt) in enumerate(groups):
        for k in keys:
            cv.alpha_composite(ic[k], (round(x), y_contacts - isz//2)); x += isz + S(12)
        d.text((x+S(2), y_contacts+S(2)), txt, font=fc, fill=WHITE+(255,), anchor='lm'); x += S(14) + w_lt(txt, fc)
        if gi == 0:
            d.line([(x+sep/2-S(6), y_contacts-S(22)), (x+sep/2-S(6), y_contacts+S(22))], fill=GLOW+(255,), width=S(3)); x += sep
    d.text((W/2, y_terms), 'من 15 أكتوبر حتى 15 نوفمبر · وفق الشروط والأحكام', font=F(AR_BOLD, S(26)),
           fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')


def headline(cv, right, top, scale=1.0):
    """عروض الشتاء / تبدأ من / 200$ / للأسبوع — right-aligned neon stack on the wall."""
    y = top
    neon_text(cv, (right, y + S(80*scale)), 'عروض الشتاء', S(92*scale), anchor='rs')
    cx = right - S(225*scale)                             # the price block sits centred under the title
    neon_text(cv, (cx, y + S(208*scale)), 'تبدأ من', S(70*scale), anchor='ms')
    neon_text(cv, (cx, y + S(398*scale)), '200$', S(180*scale), anchor='ms', rtl=False)
    neon_text(cv, (cx, y + S(508*scale)), 'للأسبوع', S(74*scale), anchor='ms')


def post(bg, out):
    W, H = S(1080), S(1350)
    cv = fit(bg, W, H); grade(cv, 0.22, 0.86)
    neon_logo(cv, S(58), S(56), S(290))
    badge(cv, W - S(64), S(64))
    headline(cv, W - S(76), S(180))
    footer(cv, S(1250), S(1318))
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def story(bg, out):
    W, H = S(1080), S(1920)
    cv = fit(bg, W, H); grade(cv, 0.16, 0.74, 0.94)
    neon_logo(cv, S(58), S(150), S(300))                  # story UI covers the top ~120px
    badge(cv, W - S(64), S(160))
    headline(cv, W - S(70), S(340), scale=1.3)
    footer(cv, S(1700), S(1770))                          # clear of the reply bar at the bottom
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    os.makedirs(sys.argv[4], exist_ok=True)
    post(sys.argv[2], os.path.join(sys.argv[4], 'winter-offer-post.png'))
    story(sys.argv[3], os.path.join(sys.argv[4], 'winter-offer-story.png'))
