"""«وفّر معنا»: Chery Tiggo 8 Pro winter offer — three LIGHT post layouts, 2160x2700.

usage: python3 tiggo_winter.py <brand-kit dir> <out dir>
Scenes: Canva, generated from our real Tiggo 8 Pro photo (tiggo-winter-a/b/c.jpg).
  A  classic, centred: title, model, big monthly price, detail line, snowy forest
  B  editorial right column over the snowy Istanbul waterfront (mosque on the left)
  C  minimal: title on white fog, a frosted price card with day / month split
Every line is placed from its measured ink box with at least 24 units clear between neighbours.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
RED = (200, 30, 45); SOFTN = (84, 102, 124)
OX = 'Oxanium-800.ttf'; OX6 = 'Oxanium-600.ttf'
def S(v): return round(v*K)
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))

MODEL = 'CHERY TIGGO 8 PRO'
DATES = 'من 1 نوفمبر 2026 حتى 1 يناير 2027'
TERMS = 'وفق الشروط والأحكام'


def box(t, f, rtl=True):
    """(above, below, width) around the baseline, in pixels."""
    kw = dict(direction='rtl', language='ar') if rtl else dict(direction='ltr', language='en')
    b = _m.textbbox((0, 0), t, font=f, anchor='ls', **kw); return -b[1], b[3], b[2] - b[0]


def ar(d, xy, t, f, col, anchor='ms'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
def lt(d, xy, t, f, col, anchor='ms'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='ltr', language='en')


def spaced(d, cx, y, t, f, col, track):
    """Latin caps with letter-spacing, centred on cx."""
    ws = [w_lt(c, f) if c != ' ' else w_lt('M', f)*0.45 for c in t]
    tot = sum(ws) + track*(len(t) - 1); x = cx - tot/2
    for c, w in zip(t, ws):
        if c != ' ': d.text((x, y), c, font=f, fill=col+(255,), anchor='ls')
        x += w + track
    return tot


def perspective_coeffs(dst, src):
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]]
    return np.linalg.solve(np.array(A, float), np.array(src, float).reshape(8)).tolist()


def plate_logo(im, seed):
    """Find the blank plate around `seed` (full-res px) and set our navy logo on it in perspective."""
    from scipy import ndimage
    a = np.asarray(im.convert('L')).astype(int); x, y = seed
    win = a[y-160:y+160, x-260:x+260] > 150
    lab, _ = ndimage.label(win); vals, cnt = np.unique(lab[lab > 0], return_counts=True)
    ys, xs = np.where(lab == vals[cnt.argmax()]); xs = xs + x - 260; ys = ys + y - 160
    sm, df = xs + ys, xs - ys
    quad = [(xs[sm.argmin()], ys[sm.argmin()]), (xs[df.argmax()], ys[df.argmax()]), (xs[sm.argmax()], ys[sm.argmax()]), (xs[df.argmin()], ys[df.argmin()])]
    tone = a[ys, xs].mean()/255
    pw, ph = 1000, 280; flat = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    lg = Image.open(LOGO_NAVY).convert('RGBA'); lh = round(ph*0.66); lw = round(lh*lg.width/lg.height)
    if lw > pw*0.82: lw = round(pw*0.82); lh = round(lw*lg.height/lg.width)
    lg = lg.resize((lw, lh), Image.LANCZOS); r, g, b, al = lg.split()
    lg = Image.merge('RGBA', tuple(c.point(lambda v: int(v*tone)) for c in (r, g, b)) + (al,))
    flat.alpha_composite(lg, ((pw - lw)//2, (ph - lh)//2))
    warp = flat.transform(im.size, Image.PERSPECTIVE, perspective_coeffs(quad, [(0, 0), (pw, 0), (pw, ph), (0, ph)]), Image.BICUBIC)
    out = im.convert('RGBA'); out.alpha_composite(warp.filter(ImageFilter.GaussianBlur(0.7))); return out.convert('RGB')


def scene(name, shift, plate=None):
    """Photo moved up by `shift` units; the strip it frees at the bottom is the last snow rows, blurred."""
    im = Image.open(os.path.join(HERE, name)).convert('RGB').resize((W, H), Image.LANCZOS)
    if plate: im = plate_logo(im, plate)
    cv = Image.new('RGB', (W, H)); cv.paste(im, (0, -S(shift)))
    if shift:
        strip = im.crop((0, H - S(40), W, H)).resize((W, S(shift) + S(4))).filter(ImageFilter.GaussianBlur(S(10)))
        cv.paste(strip, (0, H - S(shift) - S(2)))
    return cv.convert('RGBA')


def veil(cv, fn, rgb=(255, 255, 255)):
    ys = np.arange(H, dtype=np.float32)/K
    with np.errstate(invalid='ignore'):
        a = np.clip(np.nan_to_num(fn(ys), nan=0.0), 0, 1)
    lay = Image.new('RGBA', (W, H), rgb+(0,)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)


def frost(cv, rect, radius, alpha=200, blur=18):
    x0, y0, x1, y1 = [S(v) for v in rect]
    region = cv.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(S(blur)))
    lay = Image.new('RGBA', region.size, (255, 255, 255, alpha)); region.alpha_composite(lay)
    m = Image.new('L', region.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, region.width-1, region.height-1), radius=S(radius), fill=255)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + S(10), x1, y1 + S(14)), radius=S(radius), fill=(20, 40, 60, 60))
    cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S(18))))
    cv.paste(region, (x0, y0), m)
    ImageDraw.Draw(cv).rounded_rectangle((x0, y0, x1, y1), radius=S(radius), outline=(255, 255, 255, 255), width=S(2))


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1 - L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def header(cv):
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
    cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'وفّر معنا'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=RED+(255,))
    d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=N+(255,))
    ar(d, (bx + bw/2, by + bh/2 + S(2)), label, fb, Wh, 'mm')


def footer(cv, y=1294):
    d = ImageDraw.Draw(cv)
    ic = {k: navy_icon(v) for k, v in load_icons(S(36)).items()}; fc = F(CT_FONT, S(30)); y = S(y); x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, y - S(18))); x += S(46)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=N+(255,), anchor='lm')
    t = '+90 555 034 22 00'; d.text((R_, y + S(2)), t, font=fc, fill=N+(255,), anchor='rm')
    x = R_ - w_lt(t, fc) - S(18) - S(36)
    for k in ('ph', 'wa'):
        cv.alpha_composite(ic[k], (round(x), y - S(18))); x -= S(46)


def dates_line(d, cx, top, col=SOFTN):
    """'from … to … · terms' on one line; returns ink bottom (units)."""
    t = f'{DATES}  ·  {TERMS}'; f = F(AR_BOLD, S(27)); up, dn, _ = box(t, f)
    ar(d, (S(cx), S(top) + up), t, f, col); return (S(top) + up + dn)/K


def flake_field(cv, seed, n=70, top=0, bottom=1350):
    """A few soft snowflakes in the open sky, never over the text column's own ink (drawn first)."""
    rng = np.random.default_rng(seed); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(S(top), S(bottom)); r = rng.uniform(S(1.5), S(4))
        ld.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(rng.uniform(120, 220))))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(S(0.8))))


# ---------------------------------------------------------------------------------------------------------
def model_a(bg='tiggo-winter-a.jpg', shift=130, plate=(746, 2220), roof=335*1350//600, glow=0, glow_floor=0):
    cv = scene(bg, shift, plate=plate)
    veil(cv, lambda y: ((660 - y)/520)**0.9*0.55)                       # brighten the sky behind the type
    veil(cv, lambda y: (y - 1150 + glow_floor)/90*0.92)                 # white floor for dates + footer
    if glow:                                                            # soft white halo behind the type block
        g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse((S(150), S(110), S(930), S(640)), fill=int(255*glow))
        lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(g.filter(ImageFilter.GaussianBlur(S(70)))); cv.alpha_composite(lay)
    header(cv); d = ImageDraw.Draw(cv); cx = W/2; GAP = S(26)
    # eyebrow with hairlines
    f = F(AR_BLACK, S(44)); up, dn, tw = box('عروض الشتاء', f); b = S(146) + up
    ar(d, (cx, b), 'عروض الشتاء', f, O)
    for sx in (-1, 1):
        x0 = cx + sx*(tw/2 + S(22)); d.line([(x0, b - up*0.42), (x0 + sx*S(120), b - up*0.42)], fill=O+(255,), width=S(3))
    y = b + dn
    # model, tracked
    f = F(OX6, S(34)); up, dn, _ = box(MODEL, f, False); b = y + GAP + up
    spaced(d, cx, b, MODEL, f, N, S(7)); y = b + dn
    # monthly price
    f = F(OX, S(150)); up, dn, _ = box('1500$', f, False); b = y + S(28) + up
    lt(d, (cx, b), '1500$', f, N); y = b + dn
    f = F(AR_BLACK, S(40)); up, dn, _ = box('للشهر كاملاً', f); b = y + GAP + up
    ar(d, (cx, b), 'للشهر كاملاً', f, O); y = b + dn
    # detail chip
    t = '30 يوماً  ·  50$ في اليوم'; f = F(AR_BOLD, S(30)); up, dn, tw = box(t, f)
    c0 = y + S(28); ch = up + dn + S(28)
    d.rounded_rectangle((cx - tw/2 - S(30), c0, cx + tw/2 + S(30), c0 + ch), radius=ch/2, fill=N+(255,))
    ar(d, (cx, c0 + S(14) + up), t, f, Wh)
    print('A top block ends', round((c0 + ch)/K), '| car roof ~', roof - shift)
    y2 = dates_line(d, 540, 1204)
    print('A dates', 1204, '-', round(y2))
    footer(cv)
    return cv


def model_b():
    cv = scene('tiggo-winter-b.jpg', 80, plate=(682, 2160))
    veil(cv, lambda y: np.clip((560 - y)/120, 0, 1)*0.62)                # calm white behind the column
    veil(cv, lambda y: (y - 1160)/80*0.94)
    header(cv); d = ImageDraw.Draw(cv); GAP = S(24)
    # right column, right-aligned
    f = F(AR_BOLD, S(30)); up, dn, tw = box('عروض الشتاء', f); b = S(150) + up
    ar(d, (R_, b), 'عروض الشتاء', f, O, 'rs')
    d.line([(R_ - tw - S(20), b - up*0.42), (R_ - tw - S(150), b - up*0.42)], fill=O+(255,), width=S(3))
    y = b + dn
    for t, size, col in (('شهرٌ كامل', 80, N), ('1500$ فقط', 80, O)):
        f = F(AR_BLACK, S(size)); up, dn, _ = box(t, f); b = y + GAP + up
        ar(d, (R_, b), t, f, col, 'rs'); y = b + dn
    t = '50$ في اليوم لمدة 30 يوماً'; f = F(AR_BOLD, S(30)); up, dn, tw = box(t, f)
    c0 = y + S(28); ch = up + dn + S(28)                                  # navy pill keeps the lamp post out of the type
    d.rounded_rectangle((R_ - tw - S(60), c0, R_, c0 + ch), radius=ch/2, fill=N+(255,))
    ar(d, (R_ - S(30), c0 + S(14) + up), t, f, Wh, 'rs'); y = c0 + ch
    print('B column ends', round(y/K), '| car roof ~', 290*1350//600 - 80)
    f = F(OX6, S(26)); up, dn, _ = box(MODEL, f, False)                  # model under the logo, left
    tot = sum(w_lt(c, f) if c != ' ' else w_lt('M', f)*0.45 for c in MODEL) + S(5)*(len(MODEL) - 1)
    d.rectangle((M, S(150), M + S(5), S(150) + up + dn), fill=O+(255,))
    spaced(d, M + S(20) + tot/2, S(150) + up, MODEL, f, N, S(5))
    y2 = dates_line(d, 540, 1210)
    print('B dates', 1210, '-', round(y2))
    footer(cv)
    return cv


def model_c():
    cv = scene('tiggo-winter-c.jpg', 130, plate=(688, 1895))
    flake_field(cv, 7, 60, 120, 560)
    header(cv); d = ImageDraw.Draw(cv); cx = W/2
    f = F(AR_BLACK, S(96)); up, dn, _ = box('عروض الشتاء', f); b = S(150) + up
    ar(d, (cx, b), 'عروض الشتاء', f, N); y = b + dn
    f = F(OX6, S(32)); up, dn, _ = box(MODEL, f, False); b = y + S(26) + up
    spaced(d, cx, b, MODEL, f, O, S(8)); y = b + dn
    print('C title ends', round(y/K), '| car roof ~', 235*1350//600 - 130, '| car bottom ~', 500*1350//600 - 130)
    # frosted price card on the snow below the car: day | month
    top, bot = 1040, 1190
    frost(cv, (M, top, 1080 - 64, bot), 30, alpha=215)
    d = ImageDraw.Draw(cv)
    d.line([(cx, S(top + 30)), (cx, S(bot - 30))], fill=(200, 210, 222, 255), width=S(2))
    for colx, big, small, col in ((540 + 238, '50$', 'في اليوم', N), (540 - 238, '1500$', 'للشهر · 30 يوماً', O)):
        fb_, fs = F(OX, S(86)), F(AR_BOLD, S(30))
        u1, d1, _ = box(big, fb_, False); u2, d2, _ = box(small, fs)
        blk = u1 + d1 + S(20) + u2 + d2; b1 = S((top + bot)/2) - blk/2 + u1
        lt(d, (S(colx), b1), big, fb_, col); ar(d, (S(colx), b1 + d1 + S(20) + u2), small, fs, SOFTN)
    t = f'{DATES}  ·  {TERMS}'; f = F(AR_BOLD, S(24)); up, dn, _ = box(t, f)
    footer(cv)
    ar(d, (cx, S(bot) + S(26) + up), t, f, SOFTN)
    print('C dates', bot + 26, '-', round((S(bot) + S(26) + up + dn)/K), '| footer icons from 1276')
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    # A on the snowy Istanbul waterfront (the approved layout with model B's setting), snow and frost on the car
    a_ist = lambda: model_a('tiggo-winter-a-istanbul-snowy.jpg', 170, plate=(794, 2338), roof=385*1350//600, glow=0.55, glow_floor=40)
    for k, fn in (('a', model_a), ('b', model_b), ('c', model_c), ('a-istanbul', a_ist)):
        cv = fn(); p = os.path.join(out, f'tiggo-winter-{k}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
