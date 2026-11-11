"""«من خدماتنا»: child car seat — "the green light for a safe trip" — LIGHT, 2160x2700.

usage: python3 carseat_green.py <brand-kit dir> <out.png>
Scene: Canva (carseat-green-street.jpg): a bright Istanbul street, zebra crossing in front, the Bosphorus Bridge
in the haze. Seat: the company's own green seat (carseat-green-src.jpg, photo from the user), cut out with
Canva's background remover (carseat-green-cutout.png); the straps hanging under its base are masked off.
The traffic light is drawn here (Canva's image quota was cooling down): only its green lamp is lit, and that
green is echoed in the headline. Layout in 1080 units; every line is placed from its measured ink box with at
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
    """The cutout without the straps that hang under the base, with a little more depth and colour."""
    im = Image.open(os.path.join(HERE, 'carseat-green-cutout.png')).convert('RGBA'); im = im.crop(im.getbbox())
    a = np.array(im); h = a.shape[0]; cut = round(h*0.868)                 # the base ends here
    lum = a[..., :3].mean(2); rows = np.arange(h)[:, None]
    a[..., 3] = np.where((rows > round(h*0.80)) & (lum < 62), 0, a[..., 3])   # black straps below the cushion
    a[cut:, :, 3] = 0
    im = Image.fromarray(a); al = im.getchannel('A').filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(im.convert('RGB')).enhance(1.10)).enhance(1.18)
    im = rgb.convert('RGBA'); im.putalpha(al)
    return im.crop(im.getbbox())


def traffic_light(cx, top, ground, hw=116, hh=284):
    """A signal on a pole, drawn at 2x and reduced: dark head, visors, red and amber off, green on. Units in, layer out."""
    Q = 2*K; lay = Image.new('RGBA', (W*2, H*2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    def q(v): return round(v*Q)
    # pole and foot
    pw = 16
    for i in range(q(pw)):
        t = i/q(pw); c = 46 + 70*np.exp(-((t - 0.32)/0.16)**2) - 22*t
        d.line([(q(cx - pw/2) + i, q(top + hh - 10)), (q(cx - pw/2) + i, q(ground))], fill=(int(c*0.80), int(c*0.92), int(c*1.05), 255))
    d.rounded_rectangle((q(cx - 26), q(ground - 12), q(cx + 26), q(ground + 4)), radius=q(5), fill=(34, 44, 56, 255))
    # head: back plate, body
    x0, x1 = cx - hw/2, cx + hw/2
    d.rounded_rectangle((q(x0 - 9), q(top - 9), q(x1 + 9), q(top + hh + 9)), radius=q(26), fill=(22, 30, 40, 255))
    body = Image.new('RGBA', (q(hw), q(hh)), (0, 0, 0, 0)); g = np.linspace(0, 1, q(hw))[None, :, None]
    col = np.array((58, 72, 88), np.float32)*(1 - g) + np.array((28, 38, 50), np.float32)*g
    body = Image.fromarray(np.repeat(col, q(hh), 0).astype(np.uint8)).convert('RGBA')
    mk = Image.new('L', body.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, q(hw) - 1, q(hh) - 1), radius=q(20), fill=255)
    lay.paste(body, (q(x0), q(top)), mk)
    r = 37; step = (hh - 2*r - 2*16)/2
    lamps = [((120, 44, 46), (62, 24, 28)), ((128, 98, 40), (70, 52, 22)), ((190, 255, 214), (26, 196, 104))]
    centres = []
    for i, (cin, cout) in enumerate(lamps):
        cy = top + 16 + r + i*step; centres.append(cy)
        d.ellipse((q(cx - r - 5), q(cy - r - 5), q(cx + r + 5), q(cy + r + 5)), fill=(12, 16, 22, 255))
        n = q(2*r); yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        rr = np.clip(np.sqrt((xx - n*0.42)**2 + (yy - n*0.40)**2)/(n*0.62), 0, 1)[..., None]
        lens = np.array(cin, np.float32)*(1 - rr) + np.array(cout, np.float32)*rr
        lm = Image.new('L', (n, n), 0); ImageDraw.Draw(lm).ellipse((0, 0, n - 1, n - 1), fill=255)
        lay.paste(Image.fromarray(lens.astype(np.uint8)).convert('RGBA'), (q(cx - r), q(cy - r)), lm)
        d.arc((q(cx - r - 8), q(cy - r - 9), q(cx + r + 8), q(cy + r + 7)), 195, 345, fill=(10, 14, 20, 255), width=q(9))   # visor
    return lay.resize((W, H), Image.LANCZOS), centres[2]


# the street, pushed 40 units down so the hazy skyline sits under the text; the sky above continues upward
src = Image.open(os.path.join(HERE, 'carseat-green-street.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
SHIFT = S(40); a = np.asarray(src)
cv = Image.fromarray(np.concatenate([np.repeat(a[:1], SHIFT, 0), a[:H - SHIFT]], 0)).convert('RGBA')
veil(cv, lambda y: (1 - y/620)*0.55)                                    # a brighter sky for the type
veil(cv, lambda y: np.clip((y - 1076)/52, 0, 1)**1.1*0.96)                           # white floor for the call to action and footer

# traffic light on the right, standing on the crossing
GROUND = 1092; TX, TTOP = 928, 730
tl, gy = traffic_light(TX, TTOP, GROUND)
blur_layer(cv, lambda d: d.ellipse((S(TX - 60), S(GROUND - 8), S(TX + 60), S(GROUND + 12)), fill=(30, 50, 70, 130)), 8)
blur_layer(cv, lambda d: d.ellipse((S(TX - 120), S(gy - 120), S(TX + 120), S(gy + 120)), fill=(40, 220, 120, 150)), 34)
cv.alpha_composite(tl)
blur_layer(cv, lambda d: d.ellipse((S(TX - 46), S(gy - 46), S(TX + 46), S(gy + 46)), fill=(120, 255, 180, 110)), 14)

# the seat on the left, on the crossing, with a contact shadow
st = seat(); SH = 600; sw = round(S(SH)*st.width/st.height); sx, sy = S(30), S(GROUND + 4 - SH)
st = st.resize((sw, S(SH)), Image.LANCZOS)
blur_layer(cv, lambda d: d.ellipse((sx + S(10), sy + S(SH) - S(40), sx + sw + S(20), sy + S(SH) + S(22)), fill=(25, 45, 65, 170)), 16)
cv.alpha_composite(st, (sx, sy))
print('seat x', round(sx/K), '-', round((sx + sw)/K), 'y', round(sy/K), '-', round(sy/K) + SH, '| light head', TTOP, '-', TTOP + 284, 'x', TX - 67, '-', TX + 67)

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
f2 = F(AR_BLACK, S(96)); up, dn, w2 = ink('لرحلة آمنة', f2); b = y + up; ar(d, (R_, b), 'لرحلة آمنة', f2, O); y = b + dn
print('headline 300 -', round(y/K), '| left edges', round(l1/K), round((R_ - w2)/K))
fs = F(AR_BOLD, S(32)); y += S(30)
for t in ('لا تنطلق قبل أن يجلس', 'طفلك في مقعده'):
    up, dn, ws = ink(t, fs); b = y + up; ar(d, (R_, b), t, fs, N); y = b + dn + S(18)
y -= S(18)
print('subline ends', round(y/K), 'left edge', round((R_ - ws)/K), '| seat top', round(sy/K), '| light top', TTOP - 9)

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
