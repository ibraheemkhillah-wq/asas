"""«عندك فكرة»: how to read the numbers on a tyre (255/55 R20 110V + DOT date) — seven DARK slides, 2160x2700.

usage: python3 idea_tyre_code.py <brand-kit dir> <out dir>
Photos: Canva AI (tyre-*.jpg). The full code «255/55 R20 110V» runs through the carousel as a strip; each slide
lights up the part it explains. Facts: R = radial construction; load index 110 = 1,060 kg per tyre; speed
symbol V = 240 km/h; the last four DOT digits are week + year of manufacture.
Layout in 1080 units; every line is placed from its measured ink box with at least 24 units clear.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'dark'; nc.SECTION = 'idea'
K = nc.K; TOTAL = 7
OX = 'Oxanium-800.ttf'; OX6 = 'Oxanium-600.ttf'
CARD = (12, 32, 54); DIM = (96, 116, 140)
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))
# the code, split into the parts the slides explain; key -> index in PARTS
PARTS = [('255', 'w'), ('/', None), ('55', 'h'), (' ', None), ('R', 'r'), ('20', 'd'), (' ', None), ('110', 'load'), ('V', 'speed')]


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
def lt(d, xy, t, f, col, anchor='ls'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='ltr', language='en')


def ink(t, f, arab=True):
    """(above, below, width) of the ink around the baseline, in units."""
    kw = dict(direction='rtl', language='ar') if arab else dict(direction='ltr', language='en')
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', **kw); return -b[1]/K, b[3]/K, (b[2] - b[0])/K


def shade(cv, bands):
    ys = np.arange(H*K, dtype=np.float32)/K
    for fn, rgb in bands:
        with np.errstate(invalid='ignore'):
            a = np.clip(np.nan_to_num(fn(ys), nan=0.0), 0, 1)
        lay = Image.new('RGBA', (W*K, H*K), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)


def layer():
    lay = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0)); return lay, D(lay)


def glass(cv, box, radius=22, fill=CARD + (215,), outline=(255, 255, 255, 36)):
    lay, d = layer(); d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2); cv.alpha_composite(lay)


def stack(d, lines, top, x, anchor, gap=24):
    """Lines downward from `top`: each baseline = previous ink bottom + gap + own ink top. Returns the ink bottom."""
    y = top - gap
    for t, f, col in lines:
        up, dn, _ = ink(t, f); b = y + gap + up; ar(d, (x, b), t, f, col, anchor); y = b + dn
    return y


def code_strip(cv, cx, base, size, lit=(), emboss=False):
    """«255/55 R20 110V» centred on cx; lit parts orange (with a glow), the rest dim. Returns {key: (x0, x1)}."""
    f = F(OX, size); sp = size*0.30
    widths = [(sp if t == ' ' else ink(t, f, False)[2]) for t, _ in PARTS]
    gap = size*0.04; total = sum(widths) + gap*(len(PARTS) - 1); x = cx - total/2
    pos = {}
    up = ink('255', f, False)[0]
    if lit:                                                     # glow behind the lit parts
        g, gd = layer(); x2 = x
        for (t, k), w in zip(PARTS, widths):
            if k in lit: gd.rounded_rectangle((x2 - 8, base - up - 6, x2 + w + 8, base + 10), radius=10, fill=O + (120,))
            x2 += w + gap
        cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(18*K)))
    d = D(cv)
    for (t, k), w in zip(PARTS, widths):
        if t != ' ':
            if emboss and not (k in lit):                       # moulded rubber: light edge up-left, dark edge down-right
                lt(d, (x - 2, base - 2), t, f, (92, 100, 112)); lt(d, (x + 2, base + 2), t, f, (2, 6, 10))
                lt(d, (x, base), t, f, (46, 54, 66))
            else:
                lt(d, (x, base), t, f, O if k in lit else (DIM if lit else Wh))
        if k: pos[k] = (x, x + w)
        x += w + gap
    return pos, up


def badge(d, cx, cy, n, r=22):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=O + (255,))
    f = F(OX, 26); u, dn, w = ink(str(n), f, False); lt(d, (cx - w/2 - 1, cy + (u - dn)/2), str(n), f, N)


def kicker(d, t, y=196):
    """Small orange plate above a slide's headline (the part being explained)."""
    f = F(AR_BOLD, 26); u, dn, w = ink(t, f); h = u + dn + 24
    d.rounded_rectangle((R_ - w - 40, y, R_, y + h), radius=8, fill=O + (255,))
    ar(d, (R_ - 20, y + 12 + u), t, f, N)
    return y + h


# ---------------------------------------------------------------------------------------------------------------
def cover():
    cv = nc.bg('tyre-1-cover.jpg')
    shade(cv, [(lambda y: (1 - y/700)**1.2*0.96, DEEP), (lambda y: ((y - 1120)/150)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    y = 330
    for t, col, size in (('ماذا تعني الأرقام', Wh, 76), ('على إطار سيارتك؟', O, 92)):
        f = F(AR_BLACK, size); u, dn, _ = ink(t, f); b = y + u; ar(d, (W/2, b), t, f, col, 'ms'); y = b + dn + 26
    y -= 26
    # the code on a dark glass plate
    pw, ph = 640, 120; p0 = y + 44
    glass(cv, (W/2 - pw/2, p0, W/2 + pw/2, p0 + ph), radius=60, fill=DEEP + (200,), outline=O + (200,))
    pos, up = code_strip(cv, W/2, p0 + ph/2 + 26, 62)
    print('cover: title 330 -', round(y), '| plate', round(p0), '-', round(p0 + ph))
    return cv


def code_map():
    cv = nc.bg('tyre-2-sidewall.jpg')
    shade(cv, [(lambda y: (1 - y/360)**1.3*0.85, DEEP), (lambda y: ((y - 720)/120)*0.92, DEEP)])
    d = D(cv); nc.chrome(cv, d, 2, TOTAL); d = D(cv)
    end = stack(d, [('كل رقم على الإطار', F(AR_BLACK, 62), Wh), ('له معنى', F(AR_BLACK, 62), O)], 210, R_, 'rs')
    # the code moulded into the rubber band, with numbered markers under each part
    base = 600
    pos, up = code_strip(cv, W/2, base, 118, emboss=True)
    d = D(cv); keys = ['w', 'h', 'r', 'd', 'load', 'speed']
    for n, k in enumerate(keys, 1):
        x0, x1 = pos[k]; cx = (x0 + x1)/2
        d.line([(x0 + 2, base + 26), (x1 - 2, base + 26)], fill=O + (255,), width=4)
        d.line([(cx, base + 26), (cx, base + 52)], fill=O + (255,), width=3)
        badge(d, cx, base + 76, n)
    print('code_map: title 210 -', round(end), '| code ink', round(base - up), '-', base, '| badges to', base + 98)
    # six cards: number, the part in orange, what it means
    items = [('255', 'عرض الإطار', 'بالمليمتر'), ('55', 'ارتفاع الجانب', 'نسبةً إلى العرض'), ('R', 'إطار شعاعي', 'Radial'),
             ('20', 'قطر الجنط', 'بالإنش'), ('110', 'مؤشر الحمولة', 'أقصى وزن للإطار'), ('V', 'رمز السرعة', 'أقصى سرعة له')]
    g0 = 750; gw = (R_ - M - 2*20)/3; gh = 220
    for i, (code, name, sub) in enumerate(items):
        col, row = i % 3, i//3
        x1 = R_ - col*(gw + 20); x0 = x1 - gw; y0 = g0 + row*(gh + 20)
        glass(cv, (x0, y0, x1, y0 + gh))
        d = D(cv); badge(d, x1 - 34, y0 + 34, i + 1, 18)
        fc = F(OX, 62); u, dn, w = ink(code, fc, False); b = y0 + 40 + u
        lt(d, (x0 + gw/2 - w/2, b), code, fc, O)
        fn = F(AR_BLACK, 30); u2, d2, _ = ink(name, fn); b2 = b + dn + 26 + u2; ar(d, (x0 + gw/2, b2), name, fn, Wh, 'ms')
        fs = F(AR_BOLD, 22) if not sub.isascii() else F(OX6, 22)
        u3, d3, _ = ink(sub, fs, not sub.isascii()); b3 = b2 + d2 + 18 + u3
        (ar if not sub.isascii() else lt)(d, (x0 + gw/2, b3), sub, fs, SOFT, 'ms')
        if i in (0, 3): print(f'  card row {row}: {y0}-{y0 + gh}, code {round(b - u)}-{round(b + dn)}, name to {round(b2 + d2)}, sub to {round(b3 + d3)}')
    return cv


def size_slide():
    cv = nc.bg('tyre-1-cover.jpg')
    cv = cv.filter(ImageFilter.GaussianBlur(14*K))
    shade(cv, [(lambda y: np.full_like(y, 0.72), DEEP)])
    d = D(cv); nc.chrome(cv, d, 3, TOTAL); d = D(cv)
    k_end = kicker(d, 'المقاس')
    _, _ = code_strip(cv, 0, 0, 1) if False else (None, None)
    pos, up = code_strip(cv, W/2, k_end + 34 + 70, 70, lit=('w', 'h', 'r', 'd'))
    strip_end = k_end + 34 + 70 + 14
    d = D(cv)
    # side view (right) and tread view (left), real proportions: rim 508 mm, sidewall 140 mm, width 255 mm
    Ro = 235; Ri = Ro*254/394; cx, cy = 690, strip_end + 100 + Ro
    lay, ld = layer()
    ld.ellipse((cx - Ro, cy - Ro, cx + Ro, cy + Ro), fill=(20, 24, 30, 255), outline=(70, 80, 94, 255), width=3)
    ld.ellipse((cx - Ri, cy - Ri, cx + Ri, cy + Ri), fill=(52, 62, 76, 255), outline=(150, 162, 178, 255), width=3)
    for a in range(0, 360, 72):                                  # five spokes
        t = math.radians(a - 90)
        ld.line([(cx + math.cos(t)*Ri*0.18, cy + math.sin(t)*Ri*0.18), (cx + math.cos(t)*Ri*0.92, cy + math.sin(t)*Ri*0.92)], fill=(120, 132, 148, 255), width=14)
    ld.ellipse((cx - Ri*0.20, cy - Ri*0.20, cx + Ri*0.20, cy + Ri*0.20), fill=(90, 102, 118, 255))
    cv.alpha_composite(lay); d = D(cv)
    # rim diameter arrow (horizontal through the hub)
    def arrow(p, q, col=O, w=4):
        d.line([p, q], fill=col + (255,), width=w)
        for a_, b_ in ((p, q), (q, p)):
            ang = math.atan2(b_[1] - a_[1], b_[0] - a_[0]); L = 14
            d.polygon([a_, (a_[0] + L*math.cos(ang + 0.45), a_[1] + L*math.sin(ang + 0.45)), (a_[0] + L*math.cos(ang - 0.45), a_[1] + L*math.sin(ang - 0.45))], fill=col + (255,))
    ay = cy + Ri*0.62
    arrow((cx - Ri*0.78, ay), (cx + Ri*0.78, ay))
    f = F(OX, 34); u, dn, w = ink('20"', f, False)
    d.rounded_rectangle((cx - w/2 - 14, ay - u/2 - 14, cx + w/2 + 14, ay + u/2 + 14), radius=10, fill=DEEP + (255,), outline=O + (255,), width=2)
    lt(d, (cx - w/2, ay + u/2), '20"', f, O)
    # sidewall height arrow (vertical at the top, between rim and tread)
    arrow((cx, cy - Ro + 6), (cx, cy - Ri - 4))
    lt(d, (cx + 18, cy - (Ro + Ri)/2 + 12), '55%', F(OX, 34), O)
    # tread view (left): width 255 mm
    tw_ = Ro*255/394; tx = 300; t0, t1 = cy - Ro, cy + Ro
    lay, ld = layer()
    ld.rounded_rectangle((tx - tw_/2, t0, tx + tw_/2, t1), radius=40, fill=(20, 24, 30, 255), outline=(70, 80, 94, 255), width=3)
    for gx in (-0.28, 0, 0.28):                                  # tread grooves
        ld.line([(tx + gx*tw_, t0 + 20), (tx + gx*tw_, t1 - 20)], fill=(48, 56, 68, 255), width=6)
    cv.alpha_composite(lay); d = D(cv)
    arrow((tx - tw_/2, t0 - 26), (tx + tw_/2, t0 - 26))
    lt(d, (tx - ink('255', F(OX, 34), False)[2]/2, t0 - 44), '255', F(OX, 34), O)
    diag_end = cy + Ro
    print('size: strip ends', round(strip_end), '| diagram', round(t0 - 44 - 30), '-', round(diag_end))
    # three explanations
    rows = [('255', 'عرض الإطار 255 مليمتراً'), ('55', 'ارتفاع جانبه 55% من عرضه، أي نحو 140 مم'), ('R20', 'إطار شعاعي يُركّب على جنط قطره 20 إنشاً')]
    y = diag_end + 40; rh = 70
    for code, txt in rows:
        glass(cv, (M, y, R_, y + rh), radius=16); d = D(cv)
        fc = F(OX, 34); u, dn, w = ink(code, fc, False)
        d.rounded_rectangle((R_ - 16 - w - 28, y + 10, R_ - 16, y + rh - 10), radius=10, fill=O + (255,))
        lt(d, (R_ - 16 - 14 - w, y + rh/2 + (u - dn)/2), code, fc, N)
        ft = F(AR_BOLD, 28); u2, d2, _ = ink(txt, ft)
        ar(d, (R_ - 16 - w - 28 - 20, y + rh/2 + (u2 - d2)/2), txt, ft, Wh)
        y += rh + 14
    print('size: rows end', round(y - 14))
    return cv


def load_slide():
    cv = nc.bg('tyre-3-load.jpg')
    shade(cv, [(lambda y: (1 - y/820)**1.0*0.95, DEEP), (lambda y: ((y - 1150)/120)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 4, TOTAL); d = D(cv)
    k_end = kicker(d, 'مؤشر الحمولة')
    pos, up = code_strip(cv, W/2, k_end + 34 + 46, 46, lit=('load',)); y = k_end + 34 + 46 + 12
    d = D(cv)
    fb = F(OX, 190); u, dn, w = ink('110', fb, False); b = y + 40 + u
    fe = F(AR_BLACK, 54); t = '= 1,060 كغ'; u2, d2, w2 = ink('كغ', fe)
    fn = F(OX, 64); u3, d3, w3 = ink('= 1,060', fn, False)
    gap = 30; tot = w + gap + w3 + 14 + w2; x0 = W/2 - tot/2
    g, gd = layer(); gd.ellipse((x0 - 30, b - u - 10, x0 + w + 30, b + 20), fill=O + (90,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(30*K))); d = D(cv)
    lt(d, (x0, b), '110', fb, O)
    lt(d, (x0 + w + gap, b - 10), '= 1,060', fn, Wh)
    ar(d, (x0 + w + gap + w3 + 14 + w2, b - 10), 'كغ', fe, Wh)
    y = b + dn
    t = 'أقصى وزن يتحمّله الإطار الواحد'; f = F(AR_BOLD, 34); u, dn, _ = ink(t, f); b = y + 24 + u; ar(d, (W/2, b), t, f, SOFT, 'ms'); y = b + dn
    print('load: big number to', round(y))
    # mini table 108-112, 110 highlighted
    vals = [(108, '1,000'), (109, '1,030'), (110, '1,060'), (111, '1,090'), (112, '1,120')]
    tw_ = 150; gap = 14; tot = 5*tw_ + 4*gap; x = W/2 + tot/2; t0 = y + 40; th = 116
    for li, kg in vals:
        on = li == 110; x1 = x; x0_ = x1 - tw_
        glass(cv, (x0_, t0, x1, t0 + th), radius=16, fill=(O if on else CARD) + (255 if on else 215,), outline=(255, 255, 255, 40))
        d = D(cv); f1 = F(OX, 40); u, dn, w = ink(str(li), f1, False); b = t0 + 18 + u
        lt(d, (x0_ + tw_/2 - w/2, b), str(li), f1, N if on else Wh)
        f2 = F(OX6, 24); u2, d2, w2 = ink(kg + ' kg', f2, False); b2 = b + dn + 16 + u2
        lt(d, (x0_ + tw_/2 - w2/2, b2), kg + ' kg', f2, N if on else SOFT)
        x = x0_ - gap
    print('load: table', round(t0), '-', round(t0 + th))
    t = 'للإطارات الأربعة معاً: نحو 4,240 كغ'; f = F(AR_BOLD, 30); u, dn, w = ink(t, f); b0 = t0 + th + 30
    glass(cv, (W/2 - w/2 - 30, b0, W/2 + w/2 + 30, b0 + u + dn + 28), radius=30, fill=DEEP + (210,), outline=O + (200,)); d = D(cv)
    ar(d, (W/2, b0 + 14 + u), t, f, Wh, 'ms')
    print('load: note ends', round(b0 + u + dn + 28))
    return cv


def speed_slide():
    cv = nc.bg('tyre-4-speed.jpg')
    shade(cv, [(lambda y: (1 - y/700)**1.1*0.9, DEEP), (lambda y: ((y - 1000)/180)*0.94, DEEP)])
    d = D(cv); nc.chrome(cv, d, 5, TOTAL); d = D(cv)
    k_end = kicker(d, 'رمز السرعة')
    pos, up = code_strip(cv, W/2, k_end + 34 + 46, 46, lit=('speed',)); y = k_end + 34 + 46 + 12
    d = D(cv)
    fb = F(OX, 190); u, dn, w = ink('V', fb, False); b = y + 40 + u
    fn = F(OX, 64); t = '= 240 km/h'; u3, d3, w3 = ink(t, fn, False)
    gap = 30; tot = w + gap + w3; x0 = W/2 - tot/2
    g, gd = layer(); gd.ellipse((x0 - 40, b - u - 10, x0 + w + 40, b + 20), fill=O + (90,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(30*K))); d = D(cv)
    lt(d, (x0, b), 'V', fb, O); lt(d, (x0 + w + gap, b - 10), t, fn, Wh)
    y = b + dn
    t = 'أقصى سرعة يتحمّلها الإطار بأمان'; f = F(AR_BOLD, 34); u, dn, _ = ink(t, f); b = y + 24 + u; ar(d, (W/2, b), t, f, SOFT, 'ms'); y = b + dn
    print('speed: big letter to', round(y))
    # the common symbols, V lit
    syms = [('Q', 160), ('R', 170), ('S', 180), ('T', 190), ('H', 210), ('V', 240), ('W', 270), ('Y', 300)]
    cw_ = 108; gap = 12; tot = 8*cw_ + 7*gap
    x = W/2 - tot/2; t0 = 1010; th = 110
    for s, v in syms:
        on = s == 'V'
        glass(cv, (x, t0, x + cw_, t0 + th), radius=14, fill=(O if on else CARD) + (255 if on else 225,), outline=(255, 255, 255, 40))
        d = D(cv); f1 = F(OX, 40); u, dn, w = ink(s, f1, False); b = t0 + 16 + u
        lt(d, (x + cw_/2 - w/2, b), s, f1, N if on else Wh)
        f2 = F(OX6, 22); u2, d2, w2 = ink(str(v), f2, False); b2 = b + dn + 14 + u2
        lt(d, (x + cw_/2 - w2/2, b2), str(v), f2, N if on else SOFT)
        x += cw_ + gap
    t = 'السرعة القصوى للإطار، وليست سرعة يُنصح بالقيادة بها'; f = F(AR_BOLD, 26); u, dn, w = ink(t, f); b = t0 + th + 30 + u
    ar(d, (W/2, b), t, f, SOFT, 'ms')
    print('speed: symbols', t0, '-', t0 + th, '| note ends', round(b + dn))
    return cv


def date_slide():
    src = Image.open(os.path.join(HERE, 'tyre-5-date.jpg')).convert('RGB')
    cv = src.resize((W*K, H*K), Image.LANCZOS).convert('RGBA')
    shade(cv, [(lambda y: (1 - y/330)**1.3*0.85, DEEP), (lambda y: ((y - 900)/130)*0.95, DEEP)])
    # «DOT ... 1826» moulded into the oval: drawn flat, rotated to the oval's axis, embossed
    oc = (412, 642); ang = 63                                   # oval centre (units) and its tilt from horizontal
    fw, fh = 640, 170
    flat = Image.new('RGBA', (fw*K, fh*K), (0, 0, 0, 0)); fd = ImageDraw.Draw(flat)
    f = nc.F(OX, 118).real
    for off, col in (((-3, -3), (150, 120, 90, 255)), ((3, 3), (8, 6, 4, 255)), ((0, 0), (48, 40, 34, 255))):
        fd.text((fw*K/2 + off[0]*K, fh*K/2 + off[1]*K), '1826', font=f, fill=col, anchor='mm')
    rot = flat.rotate(ang, resample=Image.BICUBIC, expand=True)
    cv.alpha_composite(rot, (round(oc[0]*K - rot.width/2), round(oc[1]*K - rot.height/2)))
    d = D(cv); nc.chrome(cv, d, 6, TOTAL); d = D(cv)
    k_end = kicker(d, 'تاريخ الصنع')
    end = stack(d, [('آخر 4 أرقام بعد DOT', F(AR_BLACK, 52), Wh)], k_end + 30, R_, 'rs')
    # callouts on the right: 18 = week, 26 = year
    cx0 = 640
    lay, ld = layer()
    for (txt, sub, cy) in (('18', 'رقم الأسبوع', 560), ('26', 'عام 2026', 730)):
        ld.rounded_rectangle((cx0, cy - 66, R_, cy + 66), radius=20, fill=CARD + (225,), outline=(255, 255, 255, 40), width=2)
    cv.alpha_composite(lay); d = D(cv)
    for (txt, sub, cy) in (('18', 'رقم الأسبوع', 560), ('26', 'عام 2026', 730)):
        f1 = F(OX, 76); u, dn, w = ink(txt, f1, False); lt(d, (cx0 + 28, cy + (u - dn)/2), txt, f1, O)
        f2 = F(AR_BLACK, 34); u2, d2, w2 = ink(sub, f2); ar(d, (R_ - 26, cy + (u2 - d2)/2), sub, f2, Wh)
    print('date: title to', round(end), '| callouts 494-796')
    # result and advice on the dark floor
    t = 'أي أن الإطار صُنع في الأسبوع 18 من عام 2026'; f = F(AR_BLACK, 34); u, dn, w = ink(t, f)
    y0 = 980; ph = u + dn + 32
    glass(cv, (W/2 - w/2 - 36, y0, W/2 + w/2 + 36, y0 + ph), radius=ph/2, fill=O + (255,), outline=(0, 0, 0, 0)); d = D(cv)
    ar(d, (W/2, y0 + 16 + u), t, f, N, 'ms')
    end2 = stack(d, [('ويُنصح بفحص الإطار سنوياً بعد مرور 5 سنوات', F(AR_BOLD, 30), Wh),
                     ('على صنعه، حتى لو بدا سليماً', F(AR_BOLD, 30), Wh)], y0 + ph + 34, W/2, 'ms', gap=20)
    print('date: result', y0, '-', round(y0 + ph), '| advice to', round(end2))
    return cv


def ask():
    cv = nc.bg('tyre-6-shop.jpg')
    shade(cv, [(lambda y: (1 - y/900)*0.95, DEEP), (lambda y: ((y - 1120)/160)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 7, TOTAL); d = D(cv)
    fe = F(AR_BOLD, 30); u, dn, w = ink('شاركنا رأيك', fe); eh = 58; y = 330
    d.rectangle((W/2 - w/2 - 26, y, W/2 + w/2 + 26, y + eh), fill=O + (255,))
    ar(d, (W/2, y + eh/2 + (u - dn)/2), 'شاركنا رأيك', fe, N, 'ms')
    end = stack(d, [('هل سبق أن تحققت', F(AR_BLACK, 74), Wh), ('من تاريخ صنع', F(AR_BLACK, 74), Wh),
                    ('إطارات سيارتك؟', F(AR_BLACK, 96), O)], y + eh + 40, W/2, 'ms', gap=26)
    print('ask: chip', y, '| title to', round(end))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(), code_map(), size_slide(), load_slide(), speed_slide(), date_slide(), ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-tyre-code-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
