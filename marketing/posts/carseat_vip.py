"""«من خدماتنا»: child car seat — "a private seat for the most precious passenger" — dark, 2160x2700.

usage: python3 carseat_vip.py <brand-kit dir> <out.png>
Background: Canva (carseat-vip-scene.jpg): child seat in a dark cabin, Bosphorus Bridge lights through the window,
a blank place card on the cushion. A larger card with «محجوز» is drawn flat and warped over it.
Vertical positions come from measured ink extents with at least 24 units clear between neighbours.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_WHITE, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
DEEP = (8, 24, 41)
def S(v): return round(v*K)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')


def ink(t, f):
    b = ImageDraw.Draw(Image.new('RGB', (8, 8))).textbbox((0, 0), t, font=f, anchor='ls', direction='rtl', language='ar')
    return -b[1], b[3]


def shade(cv, fn, rgb):
    ys = np.arange(H, dtype=np.float32)/K
    with np.errstate(invalid='ignore'):
        a = np.clip(np.nan_to_num(fn(ys), nan=0.0), 0, 1)
    lay = Image.new('RGBA', (W, H), rgb+(0,))
    lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)


def perspective_coeffs(dst, src):
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]]
    return np.linalg.solve(np.array(A, float), np.array(src, float).reshape(8)).tolist()


cv = Image.open(os.path.join(HERE, 'carseat-vip-scene.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)

# «محجوز» on a larger place card: the photo's card corners, scaled up about its base so it still stands on the
# cushion and covers the original; the card is drawn flat (paper tone, edge, text) and warped onto that quad
quad0 = [(869, 1879), (1141, 1903), (1153, 2084), (846, 2055)]          # TL, TR, BR, BL of the photo's card
SC = 1.55
bxm, bym = (quad0[2][0] + quad0[3][0])/2, (quad0[2][1] + quad0[3][1])/2  # base midpoint stays put
quad = [(bxm + (x - bxm)*SC, bym + (y - bym)*SC) for x, y in quad0]
arr = np.asarray(cv.convert('RGB')).astype(np.float32)
paper = tuple(int(v) for v in arr[1950:2010, 960:1040].reshape(-1, 3).mean(0))
cw, ch = 900, 600
flat = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); fd = ImageDraw.Draw(flat)
g = np.linspace(1.04, 0.90, ch)[:, None, None]                          # warm light from above, a touch darker at the base
card = np.clip(np.array(paper, np.float32)[None, None, :]*g, 0, 255).repeat(cw, 1)
flat.paste(Image.fromarray(card.astype(np.uint8)), (0, 0))
fd.rectangle((0, 0, cw-1, ch-1), outline=(255, 255, 255, 120), width=3)
fcard = F(AR_BLACK, 210); up, dn = ink('محجوز', fcard)
base = (ch - (up + dn))//2 + up - 22
fd.text((cw/2, base), 'محجوز', font=fcard, fill=N+(255,), anchor='ms', direction='rtl', language='ar')
fd.rectangle((cw/2 - 110, base + dn + 36, cw/2 + 110, base + dn + 48), fill=O+(255,))
src = [(0, 0), (cw, 0), (cw, ch), (0, ch)]
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))                            # soft shadow behind the card
ImageDraw.Draw(sh).polygon([(x + 22, y + 26) for x, y in quad], fill=(0, 0, 0, 150))
cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
warp = flat.transform((W, H), Image.PERSPECTIVE, perspective_coeffs(quad, src), Image.BICUBIC)
cv.alpha_composite(warp.filter(ImageFilter.GaussianBlur(0.6)))
print('card top', round(min(y for _, y in quad)/K), 'bottom', round(max(y for _, y in quad)/K))

# darken the cabin roof for the headline and the floor for the info line
shade(cv, lambda y: ((560 - y)/300)**0.8*0.85, DEEP)
shade(cv, lambda y: (y - 1080)/120*0.92, DEEP)

d = ImageDraw.Draw(cv)
lg = Image.open(LOGO_WHITE).convert('RGBA'); lw = S(270)
cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=N+(255,), outline=(255, 255, 255, 60), width=S(1))
d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=O+(255,))
d.text((bx+bw/2, by+bh/2+S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# headline, centred over the dark roof; each baseline = previous ink bottom + gap + this ink top
GAP = S(26); y_bottom = S(150)
for t, f, col in (('مقعدٌ خاص', F(AR_BLACK, S(96)), Wh), ('لأغلى راكب', F(AR_BLACK, S(104)), O)):
    up, dn = ink(t, f); b = y_bottom + GAP + up
    ar(d, (W/2, b), t, f, col, 'ms'); y_bottom = b + dn
print('headline ends at', round(y_bottom/K))

# info line + chip over the darkened floor
t = 'اطلب كرسي الأطفال مع حجزك في اسطنبول'; f = F(AR_BLACK, S(36)); up, dn = ink(t, f)
b = S(1120) + up; ar(d, (W/2, b), t, f, Wh, 'ms'); y_bottom = b + dn
chip = 'برسوم إضافية · وفق الشروط والأحكام'; fc_ = F(AR_BOLD, S(26)); tw = w_ar(chip, fc_) + S(44)
c0 = y_bottom + S(26)
d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + S(48)), radius=S(24), fill=O+(255,))
d.text((W/2, c0 + S(24)), chip, font=fc_, fill=N+(255,), anchor='mm', direction='rtl', language='ar')
print('info', 1120, '-', round(y_bottom/K), 'chip', round(c0/K), '-', round((c0 + S(48))/K))

# footer: socials left, phone right (white)
ic = load_icons(S(36)); fc = F(CT_FONT, S(30)); y = S(1294); x = M
for k in ('ig', 'fb'):
    cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=Wh+(255,), anchor='lm')
t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=fc, fill=Wh+(255,), anchor='rm')
x = R_ - w_lt(t, fc) - S(18) - S(36)
for k in ('ph', 'wa'):
    cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
