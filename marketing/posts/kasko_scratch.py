"""«من خدماتنا»: comprehensive insurance — "small scratch, big bill?" — light theme, 2160x2700.

usage: python3 kasko_scratch.py <brand-kit dir> <out.png>
Background: Canva (kasko-scratch-scene.jpg): white SUV by a bollard in Karaköy, Galata Tower on the left.
Vertical positions come from measured ink extents (Kufi inks ~1.0x size above the baseline, up to 0.5x below)
with at least 24 units clear between neighbours.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
def S(v): return round(v*K)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def ink(t, f):
    """(above, below) the baseline, in pixels, for Arabic text."""
    b = ImageDraw.Draw(Image.new('RGB', (8, 8))).textbbox((0, 0), t, font=f, anchor='ls', direction='rtl', language='ar')
    return -b[1], b[3]


cv = Image.open(os.path.join(HERE, 'kasko-scratch-scene.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)

# our logo on the blank plate
px0, py0, px1, py1 = S(58), S(955), S(149), S(985)
pl = cv.crop((px0, py0, px1, py1)).convert('RGB'); plate = tuple(int(v) for v in np.array(pl).reshape(-1, 3).mean(0))
lg = Image.open(LOGO_NAVY).convert('RGBA'); lh = round((py1-py0)*0.70); lw = round(lh*lg.width/lg.height)
if lw > (px1-px0)*0.86: lw = round((px1-px0)*0.86); lh = round(lw*lg.height/lg.width)
cv.alpha_composite(lg.resize((lw, lh), Image.LANCZOS), (px0 + (px1-px0-lw)//2, py0 + (py1-py0-lh)//2))

# soft white floor for the bottom line and footer
ys = np.arange(H, dtype=np.float32)
a = np.clip((ys - S(1120))/S(70), 0, 1)**1.2*0.96
lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
cv.alpha_composite(lay)

d = ImageDraw.Draw(cv)
# logo + «من خدماتنا» badge
lg2 = Image.open(LOGO_NAVY).convert('RGBA'); lw2 = S(270)
cv.alpha_composite(lg2.resize((lw2, round(lw2*lg2.height/lg2.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=N+(255,))
d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=O+(255,))
d.text((bx+bw/2, by+bh/2+S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# headline stack in the open sky, right-aligned; each baseline = previous ink bottom + gap + this ink top
GAP = S(26)
stack = [('خدش صغير..', F(AR_BLACK, S(84)), N),
         ('فاتورة كبيرة؟', F(AR_BLACK, S(108)), O),
         ('مع التأمين الشامل.. قُد وأنت مطمئن', F(AR_BOLD, S(40)), N)]
y_bottom = S(150)
for t, f, col in stack:
    up, dn = ink(t, f); base = y_bottom + GAP + up
    ar(d, (R_, base), t, f, col); y_bottom = base + dn
chip = 'برسوم إضافية · وفق الشروط والأحكام'; fc_ = F(AR_BOLD, S(26)); tw = w_ar(chip, fc_) + S(44)
c0 = y_bottom + S(30)
d.rounded_rectangle((R_ - tw, c0, R_, c0 + S(48)), radius=S(24), fill=O+(255,))
d.text((R_ - tw/2, c0 + S(24)), chip, font=fc_, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
print('sky text ends at', round((c0 + S(48))/K), '(car roof ~675)')

# callout on the scratch: orange ring, short leader, label on the door panel
sx, sy, r = S(602), S(960), S(46)
d.ellipse((sx-r, sy-r, sx+r, sy+r), outline=O+(255,), width=S(5))
lx, ly = S(690), S(905)
d.line([(sx + r*0.72, sy - r*0.72), (lx, ly)], fill=O+(255,), width=S(4))
fl = F(AR_BLACK, S(30)); lt_ = 'خدش؟'; lw3 = w_ar(lt_, fl) + S(36)
d.rounded_rectangle((lx, ly - S(26), lx + lw3, ly + S(26)), radius=S(26), fill=O+(255,))
ar(d, (lx + lw3/2, ly + S(1)), lt_, fl, Wh, 'mm')

# bottom line on the white floor
t = 'أضِف التأمين الشامل إلى حجزك في اسطنبول'; f = F(AR_BLACK, S(38)); up, dn = ink(t, f)
ar(d, (R_, S(1170) + up), t, f, N)
print('bottom line', round((S(1170))/K), '-', round((S(1170)+up+dn)/K))
d.line([(M, S(1250)), (R_, S(1250))], fill=O+(255,), width=S(2))

# footer: socials left, phone right (navy)
ic = {k: navy_icon(v) for k, v in load_icons(S(36)).items()}; fc = F(CT_FONT, S(30)); y = S(1294); x = M
for k in ('ig', 'fb'):
    cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=N+(255,), anchor='lm')
t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=fc, fill=N+(255,), anchor='rm')
x = R_ - w_lt(t, fc) - S(18) - S(36)
for k in ('ph', 'wa'):
    cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
