"""«من خدماتنا»: airport pickup & delivery as a boarding pass — light theme, rendered at 2160x2700.

usage: python3 airport_pass.py <brand-kit dir> <out.png> [tiggo|orange]
Car: our Tiggo 8 cutout (default) or the Canva orange SUV (car-orange-cutout.png), logo on the plate.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import (ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LT_BOLD, LT_TEXT,
                   LOGO_NAVY, load_icons, w_ar, w_lt)

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
SOFTN = (110, 128, 150); RED = (227, 10, 23); PAPER = (255, 255, 255); BG_TOP = (226, 238, 248); BG_BOT = (248, 250, 252)
def S(v): return round(v*K)
def ar(d, xy, t, f, fill, anchor): d.text(xy, t, font=f, fill=fill, anchor=anchor, direction='rtl', language='ar')


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


CARS = {'tiggo': ('tiggo8-cutout.png', (241, 468, 469, 527), 560),
        'orange': ('car-orange-cutout.png', (262, 834, 554, 942), 640)}
CAR = CARS[sys.argv[3] if len(sys.argv) > 3 else 'tiggo']


def plate_logo(car):
    A = np.array(car.convert('RGB')).astype(np.float32)
    px0, py0, px1, py1 = CAR[1]
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


def plane(d, cx, cy, s, col, ang=0):
    """Side-view airliner glyph pointing along `ang` (radians, 0 = left, RTL travel)."""
    pts = [(-50, 0), (-40, -6), (40, -6), (50, -2), (50, 2), (40, 6), (-40, 6),          # fuselage
           (-6, 6), (14, 40), (24, 40), (12, 6), (-6, -6), (14, -40), (24, -40), (12, -6),  # wings
           (34, -6), (44, -22), (50, -22), (46, -6), (34, 6), (44, 22), (50, 22), (46, 6)]  # tail
    def tr(x, y):
        x, y = x*s/100, y*s/100
        return (cx + x*math.cos(ang) - y*math.sin(ang), cy + x*math.sin(ang) + y*math.cos(ang))
    body = [tr(*p) for p in pts[:7]]; d.polygon(body, fill=col)
    for i in (7, 11, 15, 19):
        d.polygon([tr(*p) for p in pts[i:i+4]], fill=col)


def tr_flag(d, x0, y0, w, h):
    d.rounded_rectangle((x0, y0, x0+w, y0+h), radius=max(2, h//10), fill=RED)
    cx, cy, r = x0 + w*0.40, y0 + h/2, h*0.26
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=Wh)
    r2 = r*0.8; c2 = cx + r*0.28
    d.ellipse((c2-r2, cy-r2, c2+r2, cy+r2), fill=RED)
    sx, sy, R1, R2 = x0 + w*0.62, cy, h*0.13, h*0.055
    d.polygon([(sx + (R1 if i % 2 == 0 else R2)*math.cos(-math.pi/2 + i*math.pi/5 + math.pi/2),
                sy + (R1 if i % 2 == 0 else R2)*math.sin(-math.pi/2 + i*math.pi/5 + math.pi/2)) for i in range(10)], fill=Wh)


# ---- background: soft sky, a dotted flight path and a small plane ------------------
ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
bg = np.array(BG_TOP, np.float32)*(1-ys) + np.array(BG_BOT, np.float32)*ys
cv = Image.fromarray(np.repeat(bg, W, 1).astype(np.uint8)).convert('RGBA')
d = ImageDraw.Draw(cv)

# ---- chrome ---------------------------------------------------------------------------
lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=N+(255,))
d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=O+(255,))
ar(d, (bx+bw/2, by+bh/2+S(2)), label, fb, Wh+(255,), 'mm')

ar(d, (R_, S(222)), 'استلام وتسليم', F(AR_BLACK, S(78)), N+(255,), 'rs')
ar(d, (R_, S(306)), 'في مطار اسطنبول', F(AR_BLACK, S(62)), O+(255,), 'rs')

# ---- the boarding pass -----------------------------------------------------------------
tx0, ty0, tx1, ty1 = M, S(372), R_, S(842)
stub = S(300)                               # stub on the left (tear-off part)
px = tx0 + stub
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((tx0+S(8), ty0+S(22), tx1-S(8), ty1+S(18)), radius=S(36), fill=N+(70,))
cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(22))))
d = ImageDraw.Draw(cv)
d.rounded_rectangle((tx0, ty0, tx1, ty1), radius=S(36), fill=PAPER+(255,))
# header band
hb = S(86)
d.rounded_rectangle((tx0, ty0, tx1, ty0+hb+S(36)), radius=S(36), fill=N+(255,))
d.rectangle((tx0, ty0+hb, tx1, ty0+hb+S(36)), fill=PAPER+(255,))
d.text((tx1 - S(34), ty0 + hb/2 + S(2)), 'BOARDING PASS', font=F(LT_BOLD, S(34)), fill=Wh+(255,), anchor='rm')
ar(d, (px + S(30), ty0 + hb/2 + S(4)), 'بطاقة استلام', F(AR_BOLD, S(28)), O+(255,), 'lm')
plane(d, tx0 + stub/2, ty0 + hb/2, S(70), Wh+(255,), ang=math.pi)
# perforation: notches + dashed line
for ny in (ty0, ty1):
    d.ellipse((px - S(22), ny - S(22), px + S(22), ny + S(22)), fill=tuple(int(v) for v in (bg[int(ny)][0]))+(255,))
for y in range(int(ty0 + hb + S(30)), int(ty1 - S(30)), S(22)):
    d.line([(px, y), (px, y + S(11))], fill=(196, 206, 218, 255), width=S(3))

# route: IST (from, right) ---> بابك (to, left)
mx0, mx1 = px + S(40), tx1 - S(40)
lab = F(AR_BOLD, S(24)); sub = F(AR_BOLD, S(24))
ar(d, (mx1, ty0 + S(150)), 'من', lab, SOFTN+(255,), 'rs')
d.text((mx1, ty0 + S(250)), 'IST', font=F(LT_BOLD, S(108)), fill=N+(255,), anchor='rs')
tr_flag(d, mx1 - w_ar('من', lab) - S(66), ty0 + S(124), S(48), S(32))
ar(d, (mx1, ty0 + S(292)), 'مطار اسطنبول', sub, SOFTN+(255,), 'rs')
ar(d, (mx0, ty0 + S(150)), 'إلى', lab, SOFTN+(255,), 'ls')
ar(d, (mx0, ty0 + S(250)), 'بابك', F(AR_BLACK, S(84)), O+(255,), 'ls')
ar(d, (mx0, ty0 + S(292)), 'أو أي عنوان في اسطنبول', sub, SOFTN+(255,), 'ls')
lx0, lx1, ly = mx0 + S(190), mx1 - S(250), ty0 + S(218)
for x in range(int(lx0), int(lx1), S(18)):
    d.line([(x, ly), (x + S(9), ly)], fill=O+(255,), width=S(3))
plane(d, (lx0 + lx1)/2, ly, S(60), O+(255,), ang=0)

# detail fields
d.line([(mx0, ty0 + S(322)), (mx1, ty0 + S(322))], fill=(226, 232, 240, 255), width=S(2))
fields = [('المسافر', 'ضيفنا العزيز'), ('البوابة', 'صالة الوصول'), ('الموعد', 'مع هبوط رحلتك')]
colw = (mx1 - mx0)/3
for i, (k, v) in enumerate(fields):
    x = mx1 - i*colw
    ar(d, (x, ty0 + S(366)), k, lab, SOFTN+(255,), 'rs')
    if v.isascii():
        d.text((x, ty0 + S(412)), v, font=F(LT_BOLD, S(28)), fill=N+(255,), anchor='rs')
    else:
        fv = F(AR_BLACK, S(30))
        while w_ar(v, fv) > colw - S(24): fv = F(AR_BLACK, fv.size - 2)
        ar(d, (x, ty0 + S(414)), v, fv, N+(255,), 'rs')

# stub: seat + barcode
scx = tx0 + stub/2
ar(d, (scx, ty0 + S(160)), 'المقعد', lab, SOFTN+(255,), 'ms')
ar(d, (scx, ty0 + S(222)), 'السائق', F(AR_BLACK, S(52)), N+(255,), 'ms')
rng = np.random.default_rng(11); x = tx0 + S(46); bx1 = tx0 + stub - S(46)
while x < bx1:
    bwid = int(rng.choice([2, 2, 4, 6]))*K
    d.rectangle((x, ty0 + S(262), min(x + bwid, bx1), ty0 + S(372)), fill=N+(255,)); x += bwid + int(rng.choice([2, 4]))*K
d.text((scx, ty0 + S(412)), 'CALL & RENT', font=F(LT_TEXT, S(22)), fill=SOFTN+(255,), anchor='ms')

# ---- the car drives out of the pass ----------------------------------------------------
car = plate_logo(Image.open(os.path.join(HERE, CAR[0])).convert('RGBA'))
cw = S(CAR[2]); car = car.resize((cw, round(car.height*cw/car.width)), Image.LANCZOS)
cx0 = round((px + tx1)/2 - cw/2); cy1 = S(1180); cy0 = cy1 - car.height
shd = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shd).ellipse((cx0 + S(16), cy1 - S(26), cx0 + cw - S(16), cy1 + S(20)), fill=(20, 30, 45, 140))
cv.alpha_composite(shd.filter(ImageFilter.GaussianBlur(S(14))))
cv.alpha_composite(car, (cx0, cy0))
d = ImageDraw.Draw(cv)

# ---- footer --------------------------------------------------------------------------
chip = 'برسوم إضافية · وفق الشروط والأحكام'; fc_ = F(AR_BOLD, S(26)); tw = w_ar(chip, fc_) + S(44)
d.rounded_rectangle((W/2 - tw/2, S(1198), W/2 + tw/2, S(1242)), radius=S(23), fill=O+(255,))
ar(d, (W/2, S(1221)), chip, fc_, Wh+(255,), 'mm')
d.line([(M, S(1262)), (R_, S(1262))], fill=O+(255,), width=S(2))
ic = {k: navy_icon(v) for k, v in load_icons(S(36)).items()}; fc = F(CT_FONT, S(30)); y = S(1298); x = M
for k in ('ig', 'fb'):
    cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=N+(255,), anchor='lm')
t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=fc, fill=N+(255,), anchor='rm')
x = R_ - w_lt(t, fc) - S(18) - S(36)
for k in ('ph', 'wa'):
    cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
