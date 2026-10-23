"""«اعتنِ بسيارتك»: 8 signs your spark plugs need replacing — five LIGHT slides, 2160x2700.

usage: python3 spark_plugs.py <brand-kit dir> <out dir>
Photos: Canva (plug-*.jpg). Each sign gets a drawn line icon. Every text line is placed from its measured
ink extents (Kufi inks ~1.0x size above the baseline, up to 0.5x below) with at least 24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
TEAL = (22, 138, 128); SOFTN = (90, 108, 130); LINE = (222, 229, 238); TINT = (232, 244, 242)
TOTAL = 5
def S(v): return round(v*K)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))


def ink(t, f):
    """(above, below) the baseline in pixels."""
    b = _m.textbbox((0, 0), t, font=f, anchor='ls', direction='rtl', language='ar'); return -b[1], b[3]


def stack(d, lines, top, x, anchor, gap=S(26)):
    """Draw lines downward from `top`; each baseline = previous ink bottom + gap + own ink top. Returns ink bottom."""
    y = top - gap
    for t, f, col in lines:
        up, dn = ink(t, f); b = y + gap + up
        ar(d, (x, b), t, f, col, anchor); y = b + dn
    return y


def page():
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.clip(np.sqrt(((xs - W/2)/W)**2 + ((ys - H*0.45)/H)**2)/0.75, 0, 1)[..., None]
    bg = np.array((255, 255, 255), np.float32)*(1 - g) + np.array((229, 235, 242), np.float32)*g
    return Image.fromarray(bg.astype(np.uint8)).convert('RGBA')


def photo(name, fade_top=None, fade_bot=None):
    cv = Image.open(os.path.join(HERE, name)).convert('RGBA').resize((W, H), Image.LANCZOS)
    ys = np.arange(H, dtype=np.float32)/K
    with np.errstate(invalid='ignore'):
        a = np.zeros(H, np.float32)
        if fade_top: a = np.maximum(a, np.clip((fade_top[0] - ys)/fade_top[1], 0, 1)*fade_top[2])
        if fade_bot: a = np.maximum(a, np.clip((ys - fade_bot[0])/fade_bot[1], 0, 1)*fade_bot[2])
    lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay); return cv


def place(cv, name, scale, cx, bottom, crop=None):
    """Multiply a white-background studio photo onto the page (its white disappears), scaled, centred at cx,
    with its bottom edge at `bottom` (units)."""
    im = Image.open(os.path.join(HERE, name)).convert('RGB').resize((W, H), Image.LANCZOS)
    if crop: im = im.crop(tuple(S(v) for v in crop))
    im = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); bgw = np.percentile(a, 92)          # studio white -> pure white
    im = Image.fromarray(np.clip(a*255/bgw, 0, 255).astype(np.uint8))
    x0 = round(S(cx) - im.width/2); y0 = S(bottom) - im.height
    box = (x0, y0, x0 + im.width, y0 + im.height)
    base = cv.crop(box).convert('RGB')
    cv.paste(ImageChops.multiply(base, im).convert('RGBA'), box)
    return y0/K


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1 - L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def chrome(cv, n):
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
    cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'اعتنِ بسيارتك'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=TEAL+(255,))
    d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=O+(255,))
    ar(d, (bx + bw/2, by + bh/2 + S(2)), label, fb, Wh, 'mm')
    ic = load_icons(S(34)); fc = F(CT_FONT, S(29)); y = S(1292); x = M
    for k in ('ig', 'fb'):
        im = navy_icon(ic[k]); cv.alpha_composite(im, (x, y - S(17))); x += S(44)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=N+(255,), anchor='lm')
    fp = F(LT_TEXT, S(24)); t = f'{n:02d} / {TOTAL:02d}'
    d.text((R_, y + S(2)), t, font=fp, fill=SOFTN+(255,), anchor='rm')
    if n < TOTAL:
        ax = R_ - w_lt(t, fp) - S(22)
        d.polygon([(ax, y - S(9)), (ax - S(14), y + S(1)), (ax, y + S(11))], fill=O+(255,))


# ---- line icons (centre cx, cy; s = icon box) --------------------------------------------------------------
def _w(s): return max(2, round(s*0.075))

def ic_key(d, cx, cy, s, c):
    w = _w(s); r = s*0.20
    d.ellipse((cx - s*0.42, cy - r, cx - s*0.42 + 2*r, cy + r), outline=c, width=w)
    d.line([(cx - s*0.02, cy), (cx + s*0.44, cy)], fill=c, width=w)
    for x in (cx + s*0.22, cx + s*0.36): d.line([(x, cy), (x, cy + s*0.16)], fill=c, width=w)

def ic_shake(d, cx, cy, s, c):
    w = _w(s); pts = []
    for i in range(9): pts.append((cx - s*0.40 + i*s*0.10, cy + (s*0.16 if i % 2 else -s*0.16)))
    d.line(pts, fill=c, width=w, joint='curve')
    for x in (cx - s*0.48, cx + s*0.48): d.line([(x, cy - s*0.26), (x, cy + s*0.26)], fill=O, width=w)

def ic_gauge_low(d, cx, cy, s, c):
    w = _w(s); r = s*0.40
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=c, width=w)
    for a in (200, 240, 270, 300, 340):
        v = np.radians(a); d.line([(cx + np.cos(v)*r*0.78, cy + np.sin(v)*r*0.78), (cx + np.cos(v)*r*0.95, cy + np.sin(v)*r*0.95)], fill=c, width=max(2, w//2))
    v = np.radians(205); d.line([(cx, cy), (cx + np.cos(v)*r*0.70, cy + np.sin(v)*r*0.70)], fill=O, width=w)
    d.ellipse((cx - w, cy - w, cx + w, cy + w), fill=c)
    d.line([(cx - r, cy + s*0.16), (cx + r, cy + s*0.16)], fill=c, width=w)

def ic_pedal(d, cx, cy, s, c):
    w = _w(s)
    d.polygon([(cx - s*0.16, cy - s*0.38), (cx + s*0.18, cy - s*0.30), (cx + s*0.10, cy + s*0.32), (cx - s*0.24, cy + s*0.24)], outline=c, width=w)
    for k in (-0.12, 0.0, 0.12): d.line([(cx - s*0.12, cy + k*s*1.6 - s*0.02), (cx + s*0.08, cy + k*s*1.6 + s*0.02)], fill=c, width=max(2, w//2))
    d.line([(cx + s*0.30, cy - s*0.20), (cx + s*0.30, cy + s*0.16)], fill=O, width=w)
    d.polygon([(cx + s*0.22, cy + s*0.10), (cx + s*0.38, cy + s*0.10), (cx + s*0.30, cy + s*0.26)], fill=O)

def ic_fuel(d, cx, cy, s, c):
    w = _w(s)
    d.rounded_rectangle((cx - s*0.34, cy - s*0.36, cx + s*0.06, cy + s*0.40), radius=s*0.05, outline=c, width=w)
    d.rectangle((cx - s*0.26, cy - s*0.26, cx - s*0.02, cy - s*0.08), outline=c, width=max(2, w//2))
    d.line([(cx + s*0.06, cy - s*0.10), (cx + s*0.18, cy - s*0.10), (cx + s*0.18, cy + s*0.22)], fill=c, width=w)
    d.line([(cx + s*0.36, cy + s*0.30), (cx + s*0.36, cy - s*0.18)], fill=O, width=w)
    d.polygon([(cx + s*0.27, cy - s*0.12), (cx + s*0.45, cy - s*0.12), (cx + s*0.36, cy - s*0.32)], fill=O)

def ic_smoke(d, cx, cy, s, c):
    w = _w(s)
    d.rounded_rectangle((cx + s*0.04, cy + s*0.06, cx + s*0.46, cy + s*0.26), radius=s*0.08, outline=c, width=w)
    for x, y, r in ((-0.06, 0.10, 0.13), (-0.26, 0.00, 0.15), (-0.30, -0.24, 0.12), (-0.08, -0.20, 0.11)):
        d.ellipse((cx + x*s - r*s, cy + y*s - r*s, cx + x*s + r*s, cy + y*s + r*s), fill=(70, 78, 90))

def ic_rpm(d, cx, cy, s, c):
    w = _w(s); r = s*0.38
    d.arc((cx - r, cy - r, cx + r, cy + r), 150, 390, fill=c, width=w)
    for a in range(150, 391, 40):
        v = np.radians(a); d.line([(cx + np.cos(v)*r*0.74, cy + np.sin(v)*r*0.74), (cx + np.cos(v)*r*0.92, cy + np.sin(v)*r*0.92)], fill=c, width=max(2, w//2))
    for a, col in ((255, (190, 198, 210)), (285, O)):
        v = np.radians(a); d.line([(cx, cy), (cx + np.cos(v)*r*0.66, cy + np.sin(v)*r*0.66)], fill=col, width=w)
    d.ellipse((cx - w, cy - w, cx + w, cy + w), fill=c)
    d.text((cx, cy + r*0.55), 'RPM', font=F(LT_TEXT, round(s*0.16)), fill=c, anchor='mm')

def ic_idle(d, cx, cy, s, c):
    w = _w(s)
    d.rounded_rectangle((cx - s*0.34, cy - s*0.06, cx + s*0.34, cy + s*0.16), radius=s*0.07, outline=c, width=w)
    d.polygon([(cx - s*0.20, cy - s*0.06), (cx - s*0.12, cy - s*0.24), (cx + s*0.14, cy - s*0.24), (cx + s*0.22, cy - s*0.06)], outline=c, width=w)
    for x in (cx - s*0.20, cx + s*0.20): d.ellipse((x - s*0.08, cy + s*0.10, x + s*0.08, cy + s*0.26), fill=c)
    for sx in (-1, 1):
        for k in (0, 1): d.arc((cx + sx*s*(0.36 + k*0.08) - s*0.10, cy - s*0.14, cx + sx*s*(0.36 + k*0.08) + s*0.10, cy + s*0.10),
                               (300 if sx > 0 else 120), (60 if sx > 0 else 240), fill=O, width=max(2, w//2))

SIGNS = [  # icon, title, detail
    (ic_key, 'صعوبة في تشغيل المحرك', 'خاصةً في الصباح أو في الطقس البارد'),
    (ic_shake, 'تقطيع واهتزاز أثناء السير', 'يشعر به السائق عند التسارع'),
    (ic_gauge_low, 'ضعف العزم وبطء التسارع', 'السيارة لا تستجيب كعادتها'),
    (ic_pedal, 'ضعف استجابة دواسة الوقود', 'تضغط أكثر ولا تحصل على قوة'),
    (ic_fuel, 'زيادة استهلاك الوقود', 'بشكل ملحوظ دون تغيير في القيادة'),
    (ic_smoke, 'دخان داكن من العادم', 'بسبب احتراق غير كامل للوقود'),
    (ic_rpm, 'تذبذب مؤشر الدوران RPM', 'الإبرة لا تثبت أثناء الوقوف'),
    (ic_idle, 'رجّة واضحة عند الوقوف', 'أو عند السرعات المنخفضة'),
]


def cover(out):
    cv = page()
    top = place(cv, 'plug-1-cover.jpg', 0.62, 540, 1262)
    chrome(cv, 1); d = ImageDraw.Draw(cv)
    y = stack(d, [('شمعات الاحتراق «البواجي»', F(AR_BLACK, S(54)), N),
                  ('8 علامات', F(AR_BLACK, S(132)), O),
                  ('تخبرك أنها تحتاج إلى تغيير', F(AR_BLACK, S(54)), N)], S(240), W/2, 'ms')
    t = 'اسحب لتعرفها'; fs = F(AR_BOLD, S(30)); tw = w_ar(t, fs) + S(110); c0 = y + S(34)
    d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + S(60)), radius=S(30), fill=TEAL+(255,))
    ar(d, (W/2 + S(22), c0 + S(30)), t, fs, Wh, 'mm')
    ax = W/2 - tw/2 + S(38); ay = c0 + S(30)
    d.polygon([(ax, ay), (ax + S(16), ay - S(11)), (ax + S(16), ay + S(11))], fill=Wh+(255,))
    print('cover text ends', round((c0 + S(60))/K), '| plug photo frame top', round(top), '(plug ink starts ~', round(top + 416*0.62), ')')
    return cv


def signs(n, part, title, items, first):
    cv = page(); chrome(cv, n); d = ImageDraw.Draw(cv)
    y = stack(d, [(part, F(AR_BOLD, S(30)), TEAL), (title, F(AR_BLACK, S(62)), N)], S(150), R_, 'rs', gap=S(24))
    top = y + S(40); rh = S(196); gap = S(22)
    for i, (icon, t1, t2) in enumerate(items):
        y0 = top + i*(rh + gap)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((M + S(4), y0 + S(10), R_ + S(4), y0 + rh + S(10)), radius=S(28), fill=(30, 60, 90, 40))
        cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(14)))); d = ImageDraw.Draw(cv)
        d.rounded_rectangle((M, y0, R_, y0 + rh), radius=S(28), fill=(255, 255, 255, 255), outline=LINE+(255,), width=S(2))
        # icon disc on the right
        cr = S(62); cx = R_ - S(30) - cr; cy = y0 + rh/2
        d.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=TINT+(255,))
        icon(d, cx, cy, S(92), N+(255,))
        # number badge on the left, title + detail between
        num = f'{first + i:02d}'; fn = F('Oxanium-800.ttf', S(64))
        d.text((M + S(40), cy + S(4)), num, font=fn, fill=O+(255,), anchor='lm')
        tx = cx - cr - S(30)
        f1, f2 = F(AR_BLACK, S(40)), F(AR_BOLD, S(29))
        u1, d1 = ink(t1, f1); u2, d2 = ink(t2, f2); g = S(20)
        blk = u1 + d1 + g + u2 + d2; b1 = cy - blk/2 + u1
        ar(d, (tx, b1), t1, f1, N); ar(d, (tx, b1 + d1 + g + u2), t2, f2, SOFTN)
    end = top + 4*rh + 3*gap
    print('slide', n, 'cards end', round(end/K))
    if n == 3:
        ar(d, (W/2, end + S(60)), 'هذه العلامات قد تنتج عن أعطال أخرى، لذا افحص سيارتك عند فني مختص', F(AR_BOLD, S(26)), SOFTN, 'ms')
    return cv


def when(out):
    cv = page()
    place(cv, 'plug-2-types.jpg', 0.60, 540, 820, crop=(0, 270, 1080, 1030))
    chrome(cv, 4); d = ImageDraw.Draw(cv)
    stack(d, [('العمر التقريبي', F(AR_BOLD, S(30)), TEAL), ('متى تغيّر البواجي؟', F(AR_BLACK, S(70)), N)], S(150), R_, 'rs', gap=S(24))
    rows = [('نيكل / نحاس', 'كل 30 – 50 ألف كم', 50), ('بلاتين', 'كل 60 – 100 ألف كم', 100), ('إيريديوم', 'كل 100 – 120 ألف كم', 120)]
    top = S(860); rh = S(104)
    for i, (name, rng, v) in enumerate(rows):
        y0 = top + i*rh
        fn_, fr = F(AR_BLACK, S(38)), F(AR_BOLD, S(30))
        ar(d, (R_, y0 + S(40)), name, fn_, N)
        ar(d, (M + w_ar(rng, fr), y0 + S(40)), rng, fr, SOFTN)
        d.rounded_rectangle((M, y0 + S(60), R_, y0 + S(76)), radius=S(8), fill=LINE+(255,))
        d.rounded_rectangle((R_ - (R_ - M)*v/120, y0 + S(60), R_, y0 + S(76)), radius=S(8), fill=(O if i == 2 else TEAL)+(255,))
    ar(d, (W/2, top + 3*rh + S(44)), 'أرقام تقريبية، والمرجع دائماً دليل سيارتك', F(AR_BOLD, S(28)), SOFTN, 'ms')
    print('when rows end', round((top + 3*rh + S(44))/K))
    return cv


def ask(out):
    cv = page(); dy = S(420)
    ph = Image.open(os.path.join(HERE, 'plug-3-mechanic.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS).crop((0, 0, W, H - dy))
    a = np.clip(np.arange(ph.height, dtype=np.float32)/S(220), 0, 1)                   # feather the top edge
    ph.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(ph, (0, dy))
    ys = np.arange(H, dtype=np.float32)/K; b = np.clip((ys - 1170)/80, 0, 1)*0.94       # white floor for the footer
    lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(b[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)
    chrome(cv, 5); d = ImageDraw.Draw(cv)
    fe = F(AR_BOLD, S(30)); ew = w_ar('شاركنا', fe) + S(52)
    d.rectangle((W/2 - ew/2, S(250), W/2 + ew/2, S(308)), fill=O+(255,))
    ar(d, (W/2, S(280)), 'شاركنا', fe, N, 'mm')
    y = stack(d, [('هل لاحظت إحدى هذه', F(AR_BLACK, S(70)), N), ('العلامات في سيارتك؟', F(AR_BLACK, S(80)), O),
                  ('البواجي التالفة تزيد استهلاك الوقود وتُرهق المحرك', F(AR_BOLD, S(32)), SOFTN)], S(308) + S(10), W/2, 'ms')
    print('ask text ends', round(y/K))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(None),
              signs(2, 'العلامات 1 – 4', 'أثناء التشغيل والقيادة', SIGNS[:4], 1),
              signs(3, 'العلامات 5 – 8', 'في الاستهلاك وعند الوقوف', SIGNS[4:], 5),
              when(None), ask(None)]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'spark-plugs-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
