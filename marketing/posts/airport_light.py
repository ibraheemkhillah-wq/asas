"""«من خدماتنا»: airport pickup & delivery — light theme, rendered at 2160x2700.

usage: python3 airport_light.py <brand-kit dir> <out.png>
Background: Canva (airport-light-scene.jpg). Car: our Tiggo 8 cutout (tiggo8-cutout.png) with the logo plate.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
INK_SOFT = (84, 102, 124)
def S(v): return round(v*K)


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(LOGONAVY, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def plate_logo(car):
    A = np.array(car.convert('RGB')).astype(np.float32)
    px0, py0, px1, py1 = 241, 468, 469, 527
    plate = tuple(int(v) for v in A[py0+4:py1-4, px0+6:px1-6].reshape(-1, 3).mean(0))
    s = 4; pl = Image.new('RGBA', ((px1-px0)*s, (py1-py0)*s), plate+(255,))
    lg = Image.open(LOGO_NAVY).convert('RGBA')
    lh = round(pl.height*0.72); lw = round(lh*lg.width/lg.height)
    if lw > pl.width*0.86: lw = round(pl.width*0.86); lh = round(lw*lg.height/lg.width)
    lgs = lg.resize((lw, lh), Image.LANCZOS); k = plate[0]/226
    r, g, b, a = lgs.split()
    lgs = Image.merge('RGBA', tuple(c.point(lambda v: int(v*k)) for c in (r, g, b)) + (a,))
    pl.alpha_composite(lgs, ((pl.width-lw)//2, (pl.height-lh)//2))
    car.alpha_composite(pl.resize((px1-px0, py1-py0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5)), (px0, py0))
    return car


cv = Image.open(os.path.join(HERE, 'airport-light-scene.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)
ys = np.arange(H, dtype=np.float32)
a = np.clip((ys - S(1010))/S(170), 0, 1)**1.2*0.97                 # white floor for the info block
lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))

# car on the curb lane, a soft contact shadow under it
car = plate_logo(Image.open(os.path.join(HERE, 'tiggo8-cutout.png')).convert('RGBA'))
cw = S(640); car = car.resize((cw, round(car.height*cw/car.width)), Image.LANCZOS)
cx0 = S(400); cy1 = S(1060); cy0 = cy1 - car.height
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((cx0 + S(14), cy1 - S(30), cx0 + cw - S(14), cy1 + S(22)), fill=(20, 30, 40, 150))
cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(14))))
cv.alpha_composite(car, (cx0, cy0))
cv.alpha_composite(lay)

d = ImageDraw.Draw(cv)
# logo + «من خدماتنا» badge
lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=LOGONAVY+(255,))
d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=O+(255,))
d.text((bx+bw/2, by+bh/2+S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# headline in the open sky, right-aligned
d.text((R_, S(330)), 'استلام وتسليم', font=F(AR_BLACK, S(84)), fill=LOGONAVY+(255,), anchor='rs', direction='rtl', language='ar')
d.text((R_, S(430)), 'في مطار اسطنبول', font=F(AR_BLACK, S(74)), fill=O+(255,), anchor='rs', direction='rtl', language='ar')

# info block on the white floor
fi = F(AR_BLACK, S(44))
d.text((R_, S(1150)), 'نستقبلك عند الوصول… ونستلمها عند المغادرة', font=F(AR_BLACK, S(40)), fill=LOGONAVY+(255,), anchor='rs', direction='rtl', language='ar')
chip = 'برسوم إضافية · وفق الشروط والأحكام'; fc_ = F(AR_BOLD, S(26)); tw = w_ar(chip, fc_) + S(44)
d.rounded_rectangle((R_ - tw, S(1178), R_, S(1226)), radius=S(24), fill=O+(255,))
d.text((R_ - tw/2, S(1203)), chip, font=fc_, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# footer: socials left, phone right (navy)
ic = {k: navy_icon(v) for k, v in load_icons(S(36)).items()}; fc = F(CT_FONT, S(30)); y = S(1294); x = M
for k in ('ig', 'fb'):
    cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=LOGONAVY+(255,), anchor='lm')
t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=fc, fill=LOGONAVY+(255,), anchor='rm')
x = R_ - w_lt(t, fc) - S(18) - S(36)
for k in ('ph', 'wa'):
    cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)
d.line([(M, S(1250)), (R_, S(1250))], fill=O+(255,), width=S(2))

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
