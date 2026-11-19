"""«اعتنِ بسيارتك»: what the exhaust smoke colour means — LIGHT single post, 2160x2700.

usage: python3 exhaust_smoke.py <brand-kit dir> <out.png>
Photos: Canva (smoke-*.jpg): the same car, angle and studio, one per smoke colour (the white one is the
reference the other three were edited from). Four cards in a 2x2 grid: photo, a colour pill on the photo,
then the meaning. Layout in 1080 units; every line is placed from its measured ink box with at least
24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
TEAL = (22, 138, 128); SOFTN = (84, 102, 124)
def S(v): return round(v*K)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))


def ink(t, f):
    """(above, below, width) of the ink around the baseline, in pixels."""
    b = _m.textbbox((0, 0), t, font=f, anchor='ls', direction='rtl', language='ar'); return -b[1], b[3], b[2] - b[0]


def wrap(t, f, maxw):
    lines, cur = [], ''
    for wd in t.split():
        cand = (cur + ' ' + wd).strip()
        if cur and ink(cand, f)[2] > maxw: lines.append(cur); cur = wd
        else: cur = cand
    return lines + [cur]


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def blur_layer(cv, draw_fn, radius):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(S(radius))))


# name, swatch colour, photo, meaning
CARDS = [('الدخان الأبيض', (246, 247, 249), 'smoke-white.jpg',
          'الخفيف طبيعي عند البرد، والكثيف المستمر قد يعني تسرّب سائل التبريد'),
         ('الدخان الأزرق', (92, 132, 196), 'smoke-blue.jpg',
          'يدل غالباً على احتراق زيت المحرك داخل غرفة الاحتراق'),
         ('الدخان الأسود', (30, 30, 34), 'smoke-black.jpg',
          'وقود زائد في الاحتراق، كفلتر هواء مسدود أو خلل في البخاخات'),
         ('الدخان الرمادي', (140, 143, 148), 'smoke-grey.jpg',
          'قد يعني احتراق الزيت أو خللاً في الشاحن التوربيني، ويحتاج إلى فحص')]

# light field: white centre, cool grey edges
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
g = np.clip(np.sqrt(((xs - W/2)/W)**2 + ((ys - H*0.55)/H)**2)/0.72, 0, 1)[..., None]
cv = Image.fromarray((np.array((255, 255, 255), np.float32)*(1 - g) + np.array((226, 233, 241), np.float32)*g).astype(np.uint8)).convert('RGBA')
d = ImageDraw.Draw(cv)

# logo + «اعتنِ بسيارتك» badge (teal plate, orange corner)
lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'اعتنِ بسيارتك'
bw = w_ar(label, fb) + S(64); bx = R_ - bw
d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=TEAL+(255,))
d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=O+(255,))
d.text((bx + bw/2, by + bh/2 + S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')

# headline, centred, starting low
y = S(222); f = F(AR_BLACK, S(64))
a1, a2 = 'ماذا يعني لون ', 'دخان العادم؟'
u1, d1, w1 = ink(a1, f); u2, d2, w2 = ink(a2, f); up, dn = max(u1, u2), max(d1, d2); b = y + up
x0 = W/2 + (w1 + w2)/2; ar(d, (x0, b), a1, f, N); ar(d, (x0 - w1, b), a2, f, O)
y = b + dn
print('headline 222 -', round(y/K))

# 2x2 cards
G0 = y + S(40); GAP = S(24); CW = (R_ - M - GAP)//2; PH = S(252); TXT = S(110); CH = PH + TXT
fn = F(AR_BLACK, S(26)); fm = F(AR_BOLD, S(22))
for i, (name, sw, photo, meaning) in enumerate(CARDS):
    cx0 = R_ - CW - (i % 2)*(CW + GAP); cy0 = G0 + (i//2)*(CH + GAP)
    blur_layer(cv, lambda q: q.rounded_rectangle((cx0 + S(6), cy0 + S(12), cx0 + CW - S(6), cy0 + CH + S(10)), radius=S(26), fill=(29, 69, 99, 60)), 14)
    card = Image.new('RGBA', (CW, CH), (255, 255, 255, 255))
    ph = Image.open(os.path.join(HERE, photo if os.path.exists(os.path.join(HERE, photo)) else 'smoke-white.jpg')).convert('RGB')
    s = max(CW/ph.width, PH/ph.height*1.0)
    pr = ph.resize((round(ph.width*s*1.12), round(ph.height*s*1.12)), Image.LANCZOS)
    ox = round((pr.width - CW)*0.40); oy = round((pr.height - PH)*0.55)          # the tip and the plume
    card.paste(pr.crop((ox, oy, ox + CW, oy + PH)), (0, 0))
    m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, CW - 1, CH - 1), radius=S(24), fill=255)
    cv.paste(card, (cx0, cy0), m)
    d = ImageDraw.Draw(cv)
    # colour pill on the photo's top-right: swatch + name
    up, dn, nw = ink(name, fn); pill_h = S(52); pw_ = nw + S(26) + S(28) + S(26)
    px1 = cx0 + CW - S(14); px0 = px1 - pw_; py0 = cy0 + S(14)
    d.rounded_rectangle((px0, py0, px1, py0 + pill_h), radius=pill_h//2, fill=(255, 255, 255, 240))
    ar(d, (px1 - S(22), py0 + pill_h/2 + (up - dn)/2), name, fn, N)
    r = S(13); sx = px0 + S(22) + r; sy = py0 + pill_h/2
    d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=sw + (255,), outline=(180, 190, 202, 255), width=S(2))
    # meaning
    lines = wrap(meaning, fm, CW - S(44)); assert len(lines) <= 2, (name, lines)
    up, dn, _ = ink('ألإ', fm); lh = up + dn + S(12); b = cy0 + PH + S(22) + up
    for ln in lines:
        ar(d, (cx0 + CW - S(22), b), ln, fm, N); b += lh
    print(name, 'card', round(cy0/K), '-', round((cy0 + CH)/K), '| text ends', round((b - lh + dn)/K), 'of', round((cy0 + CH)/K), '| lines', len(lines))
grid_end = G0 + 2*CH + GAP

# advice bar
t = 'إذا استمر الدخان، لا تؤجّل فحص سيارتك'; f = F(AR_BLACK, S(28)); up, dn, tw_ = ink(t, f)
bh2 = up + dn + S(28); b0 = grid_end + S(28); bw2 = tw_ + S(72)
d.rounded_rectangle((W/2 - bw2/2, b0, W/2 + bw2/2, b0 + bh2), radius=bh2//2, fill=N + (255,))
ar(d, (W/2 + tw_/2, b0 + S(14) + up), t, f, Wh)
print('grid ends', round(grid_end/K), '| advice', round(b0/K), '-', round((b0 + bh2)/K), '| footer icons from 1276')

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
