"""«عندك فكرة»: how to read the numbers on a tyre (255/55 R20 110V + DOT date) — seven DARK slides, 2160x2700.

usage: python3 idea_tyre_code.py <brand-kit dir> <out dir>
Photos: Canva AI (tyre-*.jpg): Istanbul cover (Galata Tower), a real studio wheel for the size slide,
a Chery on the Bosphorus highway carrying our plate (logo + TR strip) for the speed slide. The full code «255/55 R20 110V» runs through the carousel as a strip; each slide
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



def halo(cv, draws, r=16, alpha=235):
    """A dark blurred halo behind text so orange/white reads on any photo. draws: [(xy, text, font, anchor)]."""
    lay = Image.new('L', (W*K, H*K), 0); ld = ImageDraw.Draw(lay)
    for (x, y), t, f, anchor in draws:
        ld.text((x*K, y*K), t, font=f.real, fill=255, anchor=anchor, direction='rtl', language='ar')
    lay = lay.filter(ImageFilter.MaxFilter(2*round(r*0.6*K/2) + 1)).filter(ImageFilter.GaussianBlur(r*K))
    dark = Image.new('RGBA', (W*K, H*K), DEEP + (0,)); dark.putalpha(lay.point(lambda v: min(255, int(v*alpha/255*1.6))))
    cv.alpha_composite(dark)


def perspective_coeffs(dst, src):
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]]
    return np.linalg.solve(np.array(A, float), np.array(src, float).reshape(8)).tolist()


def plate(im, seed):
    """Our navy logo on the blank white plate around `seed` (px), and «TR» on the plate's blue strip."""
    from scipy import ndimage
    a = np.asarray(im.convert('L')).astype(int); x, y = seed
    win = a[y-120:y+120, x-220:x+220] > 150
    lab, _ = ndimage.label(win); vals, cnt = np.unique(lab[lab > 0], return_counts=True)
    ys, xs = np.where(lab == vals[cnt.argmax()]); xs = xs + x - 220; ys = ys + y - 120
    sm, df = xs + ys, xs - ys
    quad = [(xs[sm.argmin()], ys[sm.argmin()]), (xs[df.argmax()], ys[df.argmax()]), (xs[sm.argmax()], ys[sm.argmax()]), (xs[df.argmin()], ys[df.argmin()])]
    tone = a[ys, xs].mean()/255
    pw, ph = 1000, 280; flat = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    lg = Image.open(nc.LOGO_NAVY).convert('RGBA'); lh = round(ph*0.64); lw = round(lh*lg.width/lg.height)
    if lw > pw*0.80: lw = round(pw*0.80); lh = round(lw*lg.height/lg.width)
    lg = lg.resize((lw, lh), Image.LANCZOS); r, g, b, al = lg.split()
    lg = Image.merge('RGBA', tuple(c.point(lambda v: int(v*tone)) for c in (r, g, b)) + (al,))
    flat.alpha_composite(lg, ((pw - lw)//2, (ph - lh)//2))
    out = im.convert('RGBA')
    out.alpha_composite(flat.transform(im.size, Image.PERSPECTIVE, perspective_coeffs(quad, [(0, 0), (pw, 0), (pw, ph), (0, ph)]), Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.6)))
    # «TR» in the blue strip just left of the white field (same height, about a ninth of its width)
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = quad
    bw = (x1 - x0)*0.115; sw, sh = 200, 280
    strip = Image.new('RGBA', (sw, sh), (0, 0, 0, 0)); sd = ImageDraw.Draw(strip)
    sd.text((sw/2, sh*0.66), 'TR', font=nc.F(OX, 30).real.font_variant(size=96), fill=(235, 238, 245, 235), anchor='ms')
    q2 = [(x0 - bw, y0), (x0 - 2, y0), (x3 - 2, y3), (x3 - bw, y3)]
    out.alpha_composite(strip.transform(im.size, Image.PERSPECTIVE, perspective_coeffs(q2, [(0, 0), (sw, 0), (sw, sh), (0, sh)]), Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.6)))
    print('plate quad', quad)
    return out.convert('RGB')


def shifted(name, shift):
    """The photo moved down by `shift` units; the strip it frees at the top continues the photo's own top rows."""
    im = Image.open(os.path.join(HERE, name)).convert('RGB').resize((W*K, H*K), Image.LANCZOS)
    cv = Image.new('RGB', (W*K, H*K)); cv.paste(im, (0, round(shift*K)))
    top = im.crop((0, 0, W*K, 40*K)).resize((W*K, round(shift*K) + 8*K)).filter(ImageFilter.GaussianBlur(14*K))
    cv.paste(top, (0, 0))
    fade = Image.new('L', (1, 60*K)); fade.putdata([int(255*(1 - i/(60*K))) for i in range(60*K)])
    cv.paste(top.crop((0, top.height - 2, W*K, top.height)).resize((W*K, 60*K)), (0, round(shift*K)), fade.resize((W*K, 60*K)))
    return cv.convert('RGBA')


# ---------------------------------------------------------------------------------------------------------------
def moulded(cv, pts, size, text='255/55 R20 110V'):
    """Mould `text` into the rubber along the polyline `pts` (units, the sidewall's mid-line, left to right),
    centred on it; letter tops point away from the hub, as on a real tyre."""
    from scipy.interpolate import splprep, splev
    P = np.array(pts, float); tck, _ = splprep([P[:, 0], P[:, 1]], s=0, k=3)
    u = np.linspace(0, 1, 4000); px, py = splev(u, tck)
    arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(px), np.diff(py)))])
    f = F(OX, size).real; adv = [f.getlength(ch)/K for ch in text]; total = sum(adv)
    # soften the sidewall's own fine print under the text: blur a band along the path
    band = Image.new('L', (W*K, H*K), 0); ImageDraw.Draw(band).line([(x*K, y*K) for x, y in zip(px[::40], py[::40])], fill=255, width=round(size*1.5*K))
    cv.paste(cv.filter(ImageFilter.GaussianBlur(6*K)), (0, 0), band.filter(ImageFilter.GaussianBlur(5*K)))
    lay = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0)); s0 = (arc[-1] - total)/2
    for ch, a in zip(text, adv):
        sc = s0 + a/2; j = min(max(int(np.searchsorted(arc, sc)), 1), len(px) - 2)
        ang = math.degrees(math.atan2(py[j + 1] - py[j - 1], px[j + 1] - px[j - 1]))
        g = Image.new('RGBA', (int(a*K*1.8) + 30, int(size*K*2.2)), (0, 0, 0, 0)); gd = ImageDraw.Draw(g); gx, gy = g.width/2, g.height/2
        for (ox, oy), col in (((-1.4, -1.4), (138, 134, 126, 255)), ((1.4, 1.4), (6, 6, 8, 255)), ((0, 0), (58, 58, 62, 255))):
            gd.text((gx + ox*K, gy + oy*K), ch, font=f, fill=col, anchor='mm')
        r = g.rotate(-ang, resample=Image.BICUBIC, expand=True)
        lay.alpha_composite(r, (round(px[j]*K - r.width/2), round(py[j]*K - r.height/2)))
        s0 += a
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.4*K)))
    print('moulded: path length', round(arc[-1]), 'text', round(total))


def cover():
    cv = shifted('tyre-1-cover-istanbul.jpg', 330)
    # the code moulded into the sidewall's upper-right band (the user's circled spot), before the grading
    moulded(cv, [(690, 720), (745, 729), (797, 751), (838, 790), (866, 838), (884, 892)], 29)
    shade(cv, [(lambda y: (1 - y/620)**1.2*0.90, DEEP), (lambda y: ((y - 1110)/150)*0.92, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    lines = [('ماذا تعني الأرقام', Wh, 74), ('على إطار سيارتك؟', O, 92)]
    y = 300; draws = []
    for t, col, size in lines:
        f = F(AR_BLACK, size); u, dn, _ = ink(t, f); b = y + u; draws.append(((W/2, b), t, f, 'ms', col)); y = b + dn + 26
    y -= 26
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws]); d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    pw, ph = 620, 116; p0 = 1110
    glass(cv, (W/2 - pw/2, p0, W/2 + pw/2, p0 + ph), radius=58, fill=DEEP + (225,), outline=O + (220,))
    code_strip(cv, W/2, p0 + ph/2 + 25, 60)
    print('cover: title 300 -', round(y), '| plate', p0, '-', p0 + ph)
    return cv


def code_map():
    cv = nc.bg('tyre-2-code-macro.jpg')
    shade(cv, [(lambda y: (1 - y/420)**1.3*0.80, DEEP), (lambda y: ((y - 790)/90)*0.94, DEEP)])
    d = D(cv); nc.chrome(cv, d, 2, TOTAL); d = D(cv)
    lines = [('كل رقم على الإطار', F(AR_BLACK, 62), Wh), ('له معنى', F(AR_BLACK, 62), O)]
    y = 210 - 24; draws = []
    for t, f, col in lines:
        u, dn, _ = ink(t, f); b = y + 24 + u; draws.append(((R_, b), t, f, 'rs', col)); y = b + dn
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws], r=14); d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    # the parts as moulded in the photo (units): x range and the ink bottom of each
    parts = [(60, 270, 682), (345, 500, 678), (530, 608, 688), (612, 755, 696), (795, 935, 720), (940, 1052, 735)]
    for n, (x0, x1, yb) in enumerate(parts, 1):
        cx = (x0 + x1)/2; yl = yb + 16
        d.line([(x0 + 4, yl), (x1 - 4, yl)], fill=O + (255,), width=4)
        d.line([(cx, yl), (cx, yl + 16)], fill=O + (255,), width=3)
        badge(d, cx, yl + 16 + 22, n)
    print('code_map: title 210 -', round(y), '| badges to', 735 + 16 + 16 + 44)
    items = [('255', 'عرض الإطار', 'بالمليمتر'), ('55', 'ارتفاع الجانب', 'نسبةً إلى العرض'), ('R', 'إطار شعاعي', 'Radial'),
             ('20', 'قطر الجنط', 'بالإنش'), ('110', 'مؤشر الحمولة', 'أقصى وزن للإطار'), ('V', 'رمز السرعة', 'أقصى سرعة له')]
    g0 = 840; gw = (R_ - M - 2*20)/3; gh = 190
    for i, (code, name, sub) in enumerate(items):
        col, row = i % 3, i//3
        x1 = R_ - col*(gw + 20); x0 = x1 - gw; y0 = g0 + row*(gh + 20)
        glass(cv, (x0, y0, x1, y0 + gh), fill=CARD + (230,))
        d = D(cv); badge(d, x1 - 32, y0 + 32, i + 1, 17)
        fc = F(OX, 54); u, dn, w = ink(code, fc, False); b = y0 + 30 + u
        lt(d, (x0 + gw/2 - w/2, b), code, fc, O)
        fn = F(AR_BLACK, 28); u2, d2, _ = ink(name, fn); b2 = b + dn + 24 + u2; ar(d, (x0 + gw/2, b2), name, fn, Wh, 'ms')
        fs = F(AR_BOLD, 21) if not sub.isascii() else F(OX6, 21)
        u3, d3, _ = ink(sub, fs, not sub.isascii()); b3 = b2 + d2 + 16 + u3
        (ar if not sub.isascii() else lt)(d, (x0 + gw/2, b3), sub, fs, SOFT, 'ms')
        if i in (0, 3): print(f'  card row {row}: {y0}-{y0 + gh}, sub ends {round(b3 + d3)}')
    return cv


def size_slide():
    """A real wheel (Canva studio photo) with its dimensions marked on it and explained in callouts."""
    S_, ox, oy = 0.80, -19, 300                              # photo scale and origin; wheel spans ~80-733 x, 400-1180 y
    src = Image.open(os.path.join(HERE, 'tyre-3-studio.jpg')).convert('RGB')
    base = src.resize((W*K, H*K), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40*K))
    cv = Image.blend(base, Image.new('RGB', base.size, DEEP), 0.55).convert('RGBA')
    ph_ = src.resize((round(W*K*S_), round(H*K*S_)), Image.LANCZOS).convert('RGBA')
    m = np.ones((ph_.height, ph_.width), np.float32); f_ = 60*K
    yy, xx = np.mgrid[0:ph_.height, 0:ph_.width].astype(np.float32)
    m = np.minimum.reduce([xx/f_ + 1, (ph_.width - 1 - xx)/f_, yy/f_]).clip(0, 1)
    ph_.putalpha(Image.fromarray((m*255).astype(np.uint8))); cv.alpha_composite(ph_, (round(ox*K), round(oy*K)))
    shade(cv, [(lambda y: (1 - y/420)**1.3*0.92, DEEP), (lambda y: ((y - 1150)/110)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 3, TOTAL); d = D(cv)
    k_end = kicker(d, 'المقاس')
    code_strip(cv, W/2, k_end + 34 + 64, 64, lit=('w', 'h', 'r', 'd')); d = D(cv)
    P = lambda x, y: (ox + S_*x, oy + S_*y)                  # photo units (1080-wide frame) -> slide units

    def arrow(p, q, w=4):
        d.line([p, q], fill=O + (255,), width=w)
        for a_, b_ in ((p, q), (q, p)):
            ang = math.atan2(b_[1] - a_[1], b_[0] - a_[0]); L = 15
            d.polygon([a_, (a_[0] + L*math.cos(ang + 0.45), a_[1] + L*math.sin(ang + 0.45)), (a_[0] + L*math.cos(ang - 0.45), a_[1] + L*math.sin(ang - 0.45))], fill=O + (255,))

    def dot(p): d.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=O + (255,))

    def callout(y0, code, line1, line2, target):
        x0, x1 = 772, R_; f1 = F(OX, 46); u, dn, w = ink(code, f1, False)
        f2 = F(AR_BOLD, 25); u2, d2, w2 = ink(line1, f2); u3, d3, w3 = ink(line2, f2)
        assert max(w, w2, w3) <= x1 - x0 - 44, (code, w2, w3)
        h = 22 + u + dn + 18 + u2 + d2 + 12 + u3 + d3 + 22
        glass(cv, (x0, y0, x1, y0 + h), radius=18, fill=DEEP + (225,), outline=O + (170,))
        dd = D(cv); b = y0 + 22 + u; lt(dd, (x1 - 22 - w, b), code, f1, O)
        b2 = b + dn + 18 + u2; ar(dd, (x1 - 22, b2), line1, f2, Wh); b3 = b2 + d2 + 12 + u3; ar(dd, (x1 - 22, b3), line2, f2, SOFT)
        dd.line([(x0, y0 + 22 + u/2 + 6), (target[0] + 10, target[1])], fill=O + (200,), width=2)
        return y0 + h

    # sidewall height: from the rim's top edge up to the tread, at the hub's x
    s_top, s_bot = P(410, 152), P(410, 236)
    arrow(s_top, s_bot); d.line([(s_top[0] - 18, s_top[1]), (s_top[0] + 18, s_top[1])], fill=O + (255,), width=3)
    # rim diameter: across the rim through the hub
    r_l, r_r = P(182, 624), P(620, 624)
    arrow(r_l, r_r)
    # tread width: across the tread band on the right
    t_l, t_r = (500, 650), (728, 650)                           # across the tread band, above the rim arrow
    arrow(t_l, t_r)
    d = D(cv)
    y = 400
    y = callout(y, '55%', 'ارتفاع الجانب', 'من عرض الإطار', ((s_top[0] + s_bot[0])/2, (s_top[1] + s_bot[1])/2)) + 30
    y = callout(y, '255', 'عرض الإطار', 'بالمليمتر', (t_r[0], t_r[1])) + 30
    y = callout(y, 'R20', 'جنط 20 إنشاً', 'إطار شعاعي', (r_r[0] - 40, r_r[1]))
    print('size: callouts 400 -', round(y), '| arrows', [tuple(round(v) for v in p) for p in (s_top, s_bot, r_l, r_r, t_l, t_r)])
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
    im = plate(Image.open(os.path.join(HERE, 'tyre-4-chery.jpg')).convert('RGB'), (830, 1798))
    im.save('/tmp/sm/chery-plate.jpg')
    cv = im.resize((W*K, H*K), Image.LANCZOS).convert('RGBA')
    shade(cv, [(lambda y: (1 - y/660)**1.1*0.88, DEEP), (lambda y: ((y - 1040)/120)*0.94, DEEP)])
    d = D(cv); nc.chrome(cv, d, 5, TOTAL); d = D(cv)
    k_end = kicker(d, 'رمز السرعة')
    pos, up = code_strip(cv, W/2, k_end + 34 + 46, 46, lit=('speed',)); y = k_end + 34 + 46 + 12
    d = D(cv)
    fb = F(OX, 190); u, dn, w = ink('V', fb, False); b = y + 40 + u
    fn = F(OX, 64); t = '= 240 km/h'; u3, d3, w3 = ink(t, fn, False)
    gap = 30; tot = w + gap + w3; x0 = W/2 - tot/2
    g, gd = layer(); gd.rounded_rectangle((x0 - 60, b - u - 30, x0 + tot + 40, b + 30), radius=60, fill=DEEP + (200,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(26*K)))
    g, gd = layer(); gd.ellipse((x0 - 40, b - u - 10, x0 + w + 40, b + 20), fill=O + (90,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(30*K))); d = D(cv)
    lt(d, (x0, b), 'V', fb, O); lt(d, (x0 + w + gap, b - 10), t, fn, Wh)
    y = b + dn
    t = 'أقصى سرعة يتحمّلها الإطار بأمان'; f = F(AR_BOLD, 34); u, dn, _ = ink(t, f); b = y + 24 + u
    halo(cv, [((W/2, b), t, f, 'ms')], r=14); d = D(cv); ar(d, (W/2, b), t, f, Wh, 'ms'); y = b + dn
    print('speed: big letter to', round(y))
    # the common symbols, V lit
    syms = [('Q', 160), ('R', 170), ('S', 180), ('T', 190), ('H', 210), ('V', 240), ('W', 270), ('Y', 300)]
    cw_ = 108; gap = 12; tot = 8*cw_ + 7*gap
    x = W/2 - tot/2; t0 = 1066; th = 104
    for s, v in syms:
        on = s == 'V'
        glass(cv, (x, t0, x + cw_, t0 + th), radius=14, fill=(O if on else CARD) + (255 if on else 225,), outline=(255, 255, 255, 40))
        d = D(cv); f1 = F(OX, 40); u, dn, w = ink(s, f1, False); b = t0 + 16 + u
        lt(d, (x + cw_/2 - w/2, b), s, f1, N if on else Wh)
        f2 = F(OX6, 22); u2, d2, w2 = ink(str(v), f2, False); b2 = b + dn + 14 + u2
        lt(d, (x + cw_/2 - w2/2, b2), str(v), f2, N if on else SOFT)
        x += cw_ + gap
    t = 'السرعة القصوى للإطار، وليست سرعة يُنصح بالقيادة بها'; f = F(AR_BOLD, 26); u, dn, w = ink(t, f); b = t0 + th + 26 + u
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
    shade(cv, [(lambda y: (1 - y/960)*0.95, DEEP), (lambda y: ((y - 1120)/160)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 7, TOTAL); d = D(cv)
    fe = F(AR_BOLD, 30); u, dn, w = ink('شاركنا رأيك', fe); eh = 58; y = 330
    lines = [('هل سبق أن تحققت', F(AR_BLACK, 74), Wh), ('من تاريخ صنع', F(AR_BLACK, 74), Wh), ('إطارات سيارتك؟', F(AR_BLACK, 96), O)]
    yy = y + eh + 40 - 26; draws = []
    for t, f, col in lines:
        u2, d2, _ = ink(t, f); b = yy + 26 + u2; draws.append(((W/2, b), t, f, 'ms', col)); yy = b + d2
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws]); d = D(cv)
    d.rectangle((W/2 - w/2 - 26, y, W/2 + w/2 + 26, y + eh), fill=O + (255,))
    ar(d, (W/2, y + eh/2 + (u - dn)/2), 'شاركنا رأيك', fe, N, 'ms')
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    print('ask: chip', y, '| title to', round(yy))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(), code_map(), size_slide(), load_slide(), speed_slide(), date_slide(), ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-tyre-code-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
