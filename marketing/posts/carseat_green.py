"""«من خدماتنا»: child car seat — "the green light for a safe trip" — LIGHT, 2160x2700.

usage: python3 carseat_green.py <brand-kit dir> <out.png>
Scene: Canva (carseat-green-street.jpg): a bright Istanbul street, zebra crossing in front, the Bosphorus Bridge
in the haze. Seat: the company's own green seat (carseat-green-src.jpg, photo from the user) re-shot by Canva as a
studio product photo at a better angle and cut out (carseat-green-studio.png). Traffic light: Canva, cut out
(carseat-green-light.png), only its green lamp lit; that green is echoed in the headline.
Layout in 1080 units; every line is placed from its measured ink box with at
least 24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
GREEN = (24, 160, 92)
def S(v): return round(v*K)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))


def ink(t, f):
    """(above, below, width) of the ink around the baseline, in pixels."""
    b = _m.textbbox((0, 0), t, font=f, anchor='ls', direction='rtl', language='ar'); return -b[1], b[3], b[2] - b[0]


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def blur_layer(cv, draw_fn, radius):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(S(radius))))


def veil(cv, fn, rgb=(255, 255, 255)):
    ys = np.arange(H, dtype=np.float32)/K
    a = np.clip(fn(ys), 0, 1)
    lay = Image.new('RGBA', (W, H), rgb + (0,)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)


def seat():
    """The studio re-shoot of the company's seat (Canva, from the user's photo), cut out."""
    im = Image.open(os.path.join(HERE, 'carseat-green-studio.png')).convert('RGBA')
    return im.crop(im.getbbox())


def traffic_light(head_h):
    """The Canva traffic light with its pole shortened (a uniform stretch of pole is dropped) so the head can be
    large; returns the image scaled so the head is head_h units tall, and the green lamp's centre in it (px)."""
    im = Image.open(os.path.join(HERE, 'carseat-green-light.png')).convert('RGBA'); im = im.crop(im.getbbox())
    top, bot = im.crop((0, 0, im.width, 1700)), im.crop((0, 3250, im.width, im.height))     # head + pole | pole + foot
    out = Image.new('RGBA', (im.width, top.height + bot.height), (0, 0, 0, 0)); out.paste(top, (0, 0)); out.paste(bot, (0, top.height))
    sc = S(head_h)/1500
    return out.resize((round(out.width*sc), round(out.height*sc)), Image.LANCZOS), (271*sc, 1178*sc)


# the street, pushed 40 units down so the hazy skyline sits under the text; the sky above continues upward
src = Image.open(os.path.join(HERE, 'carseat-green-street.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
SHIFT = S(40); a = np.asarray(src)
cv = Image.fromarray(np.concatenate([np.repeat(a[:1], SHIFT, 0), a[:H - SHIFT]], 0)).convert('RGBA')
veil(cv, lambda y: (1 - y/620)*0.55)                                    # a brighter sky for the type
veil(cv, lambda y: np.clip((y - 1076)/52, 0, 1)**1.1*0.96)                           # white floor for the call to action and footer

# traffic light on the right, standing on the crossing
GROUND = 1096; TX = 936
tl, (gcx, gcy) = traffic_light(280); lx, ly = S(TX) - tl.width//2, S(GROUND) - tl.height
gx, gy = lx + gcx, ly + gcy
blur_layer(cv, lambda d: d.ellipse((S(TX - 56), S(GROUND - 8), S(TX + 56), S(GROUND + 10)), fill=(30, 50, 70, 150)), 8)
blur_layer(cv, lambda d: d.ellipse((gx - S(120), gy - S(120), gx + S(120), gy + S(120)), fill=(40, 220, 120, 140)), 34)
cv.alpha_composite(tl, (lx, ly))
blur_layer(cv, lambda d: d.ellipse((gx - S(40), gy - S(40), gx + S(40), gy + S(40)), fill=(120, 255, 180, 90)), 14)

# the seat on the left, on the crossing, with a contact shadow
st = seat(); SH = 680; sw = round(S(SH)*st.width/st.height); sx, sy = S(24), S(GROUND + 6 - SH)
st = st.resize((sw, S(SH)), Image.LANCZOS)
blur_layer(cv, lambda d: d.ellipse((sx + S(20), sy + S(SH) - S(44), sx + sw + S(16), sy + S(SH) + S(18)), fill=(25, 45, 65, 170)), 16)
cv.alpha_composite(st, (sx, sy))
print('seat x', round(sx/K), '-', round((sx + sw)/K), 'y', round(sy/K), '-', round(sy/K) + SH, '| light x', round(lx/K), '-', round((lx + tl.width)/K), 'y', round(ly/K), '-', GROUND)

d = ImageDraw.Draw(cv)
# logo + «من خدماتنا» badge
lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=N+(255,))
d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=O+(255,))
d.text((bx + bw/2, by + bh/2 + S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# headline in the open sky, starting low (y=300), right-aligned: «الضوء الأخضر..» in navy + green, then orange
f1 = F(AR_BLACK, S(84)); y = S(300)
up = max(ink('الضوء', f1)[0], ink('الأخضر..', f1)[0]); dn = max(ink('الضوء', f1)[1], ink('الأخضر..', f1)[1]); b = y + up
ar(d, (R_, b), 'الضوء', f1, N); x2 = R_ - ink('الضوء', f1)[2] - S(24)
ar(d, (x2, b), 'الأخضر..', f1, GREEN); l1 = x2 - ink('الأخضر..', f1)[2]; y = b + dn + S(26)
f2 = F(AR_BLACK, S(88)); up, dn, w2 = ink('لرحلة آمنة', f2); b = y + up; ar(d, (R_, b), 'لرحلة آمنة', f2, O); y = b + dn
print('headline 300 -', round(y/K), '| left edges', round(l1/K), round((R_ - w2)/K))
fs = F(AR_BOLD, S(32)); y += S(30)
for t in ('لا تنطلق قبل أن يجلس', 'طفلك في مقعده'):
    up, dn, ws = ink(t, fs); b = y + up; ar(d, (R_, b), t, fs, N); y = b + dn + S(18)
y -= S(18)
print('subline ends', round(y/K), 'left edge', round((R_ - ws)/K), '| seat top', round(sy/K), '| light top', round(ly/K))

# call to action and the terms chip on the white floor
t = 'اطلب كرسي الأطفال مع حجزك في اسطنبول'; f = F(AR_BLACK, S(38)); up, dn, _ = ink(t, f); c_top = S(1126)
ar(d, (W/2, c_top + up), t, f, N, 'ms'); c_end = c_top + up + dn
chip = 'برسوم إضافية · وفق الشروط والأحكام'; fc = F(AR_BOLD, S(25)); cw = w_ar(chip, fc) + S(56); c0 = c_end + S(24); chh = S(44)
d.rounded_rectangle((W/2 - cw/2, c0, W/2 + cw/2, c0 + chh), radius=chh//2, fill=O+(255,))
d.text((W/2, c0 + chh/2), chip, font=fc, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
print('cta', round(c_top/K), '-', round(c_end/K), '| chip', round(c0/K), '-', round((c0 + chh)/K), '| footer icons from 1276')

# footer: socials left, phone right (navy)
ic = {k: navy_icon(v) for k, v in load_icons(S(36)).items()}; ff = F(CT_FONT, S(30)); y = S(1294); x = M
for k in ('ig', 'fb'):
    cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
d.text((x + S(6), y + S(2)), 'callrenttr', font=ff, fill=N+(255,), anchor='lm')
t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=ff, fill=N+(255,), anchor='rm')
x = R_ - w_lt(t, ff) - S(18) - S(36)
for k in ('ph', 'wa'):
    cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
