"""«اعتنِ بسيارتك»: how to check your headlight aim — seven DARK slides, 2160x2700.

usage: python3 headlight_aim.py <brand-kit dir> <out dir>
Photos: Canva AI (lamp-*.jpg); the side-view car in the diagrams is a Canva cutout (lamp-car-side.png).
Guidance: level ground, normal load, mark the lamp centres on a wall close up, back off 10 m: the low beam's
cut-off should sit a little below the mark (about 10 cm, a 1% drop) or as the owner's manual says; in Turkey
(right-hand traffic) the cut-off steps up on the right. Reuses the dark helpers of ../news/idea_tyre_code.py.
Layout in 1080 units; every line is placed from its measured ink box with at least 24 units clear.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'news')); sys.path.insert(0, sys.argv[1])
import idea_tyre_code as tc
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.SECTION = 'care'; K = nc.K; TOTAL = 7
F, D, ar, lt, ink, shade, layer, glass, stack, kicker, halo = tc.F, tc.D, tc.ar, tc.lt, tc.ink, tc.shade, tc.layer, tc.glass, tc.stack, tc.kicker, tc.halo
CARD = tc.CARD; OX = tc.OX
GREEN = (46, 190, 120); RED = (232, 76, 68); BEAM = (255, 236, 180)
CAR = Image.open(os.path.join(HERE, 'lamp-car-side.png')).convert('RGBA')
LAMP = (0.972, 0.507)                                           # headlight front in the cutout (fractions)


def photo(name):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA')
    sc = max(W*K/im.width, H*K/im.height); im = im.resize((round(im.width*sc), round(im.height*sc)), Image.LANCZOS)
    l = (im.width - W*K)//2; t = (im.height - H*K)//2
    return im.crop((l, t, l + W*K, t + H*K))


def lamp_at(box, car_w):
    """Where the lamp and the floor fall for a scene in `box` (no drawing)."""
    x0, y0, x1, y1 = box; floor = y1 - 40; ch = round(car_w*CAR.height/CAR.width)
    return x0 + 34 + LAMP[0]*car_w, floor - ch + 2 + LAMP[1]*ch, floor


def bg(name, top=0.86, bottom=0.92, t_end=520, b_start=1080):
    cv = photo(name)
    shade(cv, [(lambda y: (1 - y/t_end)**1.2*top, DEEP), (lambda y: ((y - b_start)/(1240 - b_start))*bottom, DEEP)])
    return cv


def head(cv, page, kick, lines, top=None):
    """Chrome, the orange kicker plate, and the headline (with a halo) below it. Returns the ink bottom."""
    d = D(cv); nc.chrome(cv, d, page, TOTAL); d = D(cv)
    y = kicker(d, kick) if kick else 170
    y += 30 - 24; draws = []
    for t, col, size in lines:
        f = F(AR_BLACK, size); u, dn, w = ink(t, f); assert w <= R_ - M, t
        b = y + 24 + u; draws.append(((R_, b), t, f, 'rs', col)); y = b + dn
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws], r=14); d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    return y


def wrap(t, f, maxw):
    out, cur = [], ''
    for wd in t.split():
        c = (cur + ' ' + wd).strip()
        if cur and ink(c, f)[2] > maxw: out.append(cur); cur = wd
        else: cur = c
    return out + [cur]


def para(cv, t, top, size=30, col=Wh, x=R_, maxw=None, gap=14, anchor='rs'):
    f = F(AR_BOLD, size); lines = wrap(t, f, maxw or (R_ - M)); d = D(cv)
    u, dn, _ = ink('ألإ', f); y = top
    for ln in lines:
        b = y + u; ar(d, (x, b), ln, f, col, anchor); y = b + dn + gap
    return y - gap


def icon(d, cx, cy, ok, r=24):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(GREEN if ok else RED) + (255,))
    if ok: d.line([(cx - r*0.45, cy + r*0.02), (cx - r*0.1, cy + r*0.38), (cx + r*0.5, cy - r*0.35)], fill=Wh + (255,), width=6, joint='curve')
    else:
        for s in (-1, 1): d.line([(cx - r*0.38, cy - s*r*0.38), (cx + r*0.38, cy + s*r*0.38)], fill=Wh + (255,), width=6)


# ---- diagram -----------------------------------------------------------------------------------------------
def scene(cv, box, car_w, wall_x, beam_top, beam_bot, mark=True, dist=None, kick_up=False, cut_col=BEAM, label_mark=True):
    """Side view inside `box`: floor, the car (front to the right), the wall at wall_x, a light beam from the lamp
    to the wall between beam_top and beam_bot (units at the wall), the tape mark at lamp height, a distance arrow."""
    x0, y0, x1, y1 = box; floor = y1 - 40
    glass(cv, box, radius=24, fill=(10, 26, 44, 235))
    lay, ld = layer()
    for i in range(0, int(x1 - x0 - 40), 18):                  # floor tiles
        ld.line([(x0 + 20 + i, floor + 2), (x0 + 20 + i - 10, floor + 26)], fill=(255, 255, 255, 18), width=2)
    ld.line([(x0 + 20, floor), (x1 - 20, floor)], fill=(255, 255, 255, 90), width=2)
    ld.rectangle((wall_x, y0 + 26, wall_x + 22, floor), fill=(150, 162, 178, 255))
    ld.rectangle((wall_x, y0 + 26, wall_x + 4, floor), fill=(220, 228, 238, 255))
    cv.alpha_composite(lay)
    ch = round(car_w*CAR.height/CAR.width); car = CAR.resize((round(car_w*K), round(ch*K)), Image.LANCZOS)
    cx0 = x0 + 34; cy0 = floor - ch + 2
    lx, ly = cx0 + LAMP[0]*car_w, cy0 + LAMP[1]*ch
    # beam: a translucent wedge, brighter near the lamp
    bl = Image.new('L', (W*K, H*K), 0); ImageDraw.Draw(bl).polygon([(lx*K, (ly - 4)*K), (wall_x*K, beam_top*K), (wall_x*K, beam_bot*K), (lx*K, (ly + 4)*K)], fill=255)
    xs = np.arange(W*K, dtype=np.float32)/K
    ramp = np.clip(1 - (xs - lx)/max(1, wall_x - lx)*0.55, 0.35, 1)
    a = (np.asarray(bl, np.float32)/255*ramp[None, :]*235).astype(np.uint8)
    beam = Image.new('RGBA', (W*K, H*K), BEAM + (0,)); beam.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(3*K)))
    cv.alpha_composite(beam)
    g, gd = layer(); gd.ellipse((lx - 26, ly - 20, lx + 26, ly + 20), fill=BEAM + (200,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(10*K)))
    cv.alpha_composite(car, (round(cx0*K), round(cy0*K)))
    d = D(cv)
    # the lit patch on the wall
    d.rectangle((wall_x - 2, beam_top, wall_x + 6, beam_bot), fill=cut_col + (255,))
    if mark:                                                    # tape mark at lamp height, dashed guide
        for xx in range(int(lx + 30), int(wall_x - 6), 22):
            d.line([(xx, ly), (min(xx + 12, wall_x - 6), ly)], fill=O + (255,), width=3)
        d.rectangle((wall_x - 14, ly - 3, wall_x + 30, ly + 3), fill=O + (255,))
        d.rectangle((wall_x + 8, ly - 16, wall_x + 14, ly + 16), fill=O + (255,))
    if dist:
        ay = y0 + 46
        d.line([(lx, ay), (wall_x - 4, ay)], fill=Wh + (230,), width=3)
        for xx, s in ((lx, 1), (wall_x - 4, -1)):
            d.polygon([(xx, ay), (xx + s*14, ay - 8), (xx + s*14, ay + 8)], fill=Wh + (230,))
            d.line([(xx, ay - 14), (xx, ay + 14)], fill=Wh + (230,), width=2)
        f = F(AR_BLACK, 28); u, dn, w = ink(dist, f); mx = (lx + wall_x)/2
        d.rounded_rectangle((mx - w/2 - 16, ay - u/2 - dn/2 - 12, mx + w/2 + 16, ay + u/2 + dn/2 + 12), radius=10, fill=DEEP + (255,), outline=Wh + (120,), width=2)
        ar(d, (mx, ay + (u - dn)/2), dist, f, Wh, 'ms')
    return lx, ly, floor


def wall_pattern(cv, box, drop_ok=True, kick=True):
    """Front view of the wall: tape line, the two lit patches and their cut-off (stepping up on the right)."""
    x0, y0, x1, y1 = box
    glass(cv, box, radius=20, fill=(150, 162, 178, 255), outline=(255, 255, 255, 60))
    mid = (y0 + y1)/2 - 10; tape = mid - 20; cut = mid + 18
    for cx in (x0 + (x1 - x0)*0.46, x0 + (x1 - x0)*0.80):
        g = Image.new('L', (W*K, H*K), 0); gd = ImageDraw.Draw(g)
        gd.ellipse(((cx - 92)*K, (cut - 30)*K, (cx + 92)*K, (cut + 70)*K), fill=255)
        g = g.filter(ImageFilter.GaussianBlur(16*K))
        cl = Image.new('L', (W*K, H*K), 0); cd = ImageDraw.Draw(cl)       # keep only what is under the cut-off line
        poly = [((cx - 130)*K, cut*K), ((cx + 8)*K, cut*K), ((cx + 40)*K, (cut - 22)*K), ((cx + 130)*K, (cut - 22)*K), ((cx + 130)*K, (y1 - 4)*K), ((cx - 130)*K, (y1 - 4)*K)]
        cd.polygon(poly if kick else poly[:2] + [((cx + 130)*K, cut*K)] + poly[4:], fill=255)
        a = Image.fromarray((np.asarray(g, np.float32)*np.asarray(cl.filter(ImageFilter.GaussianBlur(1.2*K)), np.float32)/255).astype(np.uint8))
        lay = Image.new('RGBA', (W*K, H*K), (255, 246, 214, 0)); lay.putalpha(a.point(lambda v: min(255, int(v*1.25))))
        cv.alpha_composite(lay)
    d = D(cv)
    d.line([(x0 + 18, tape), (x1 - 18, tape)], fill=O + (255,), width=4)
    for cx in (x0 + (x1 - x0)*0.46, x0 + (x1 - x0)*0.80):
        d.line([(cx, tape - 16), (cx, tape + 16)], fill=O + (255,), width=4)
    # the drop between the tape line and the cut-off
    bx = x0 + 34
    d.line([(bx, tape + 4), (bx, cut - 4)], fill=N + (255,), width=3)
    for yy, s in ((tape + 4, 1), (cut - 4, -1)): d.polygon([(bx, yy), (bx - 7, yy + s*11), (bx + 7, yy + s*11)], fill=N + (255,))
    f = F(AR_BLACK, 24); u, dn, w = ink('نحو 10 سم', f)
    ly0 = cut + 18                                             # the label sits under the drop, clear of the tape line
    d.rounded_rectangle((bx - 14, ly0, bx - 14 + w + 24, ly0 + u + dn + 18), radius=8, fill=N + (255,))
    ar(d, (bx - 14 + 12 + w, ly0 + 9 + u), 'نحو 10 سم', f, Wh)
    return tape, cut


# ---- slides ------------------------------------------------------------------------------------------------
def cover():
    cv = bg('lamp-1-cover.jpg', top=0.92, t_end=620, b_start=1060)
    d = D(cv); nc.chrome(cv, d, 1, TOTAL)
    lines = [('هل أنوار سيارتك', Wh, 78), ('مضبوطة بشكل صحيح؟', O, 80)]
    y = 300 - 26; draws = []
    for t, col, size in lines:
        f = F(AR_BLACK, size); u, dn, w = ink(t, f); assert w <= R_ - M, t
        b = y + 26 + u; draws.append(((W/2, b), t, f, 'ms', col)); y = b + dn
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws]); d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    t = 'دليل مبسّط لضبطها خطوة بخطوة'; f = F(AR_BOLD, 32); u, dn, w = ink(t, f); c0 = 1120; ch = u + dn + 30
    glass(cv, (W/2 - w/2 - 40, c0, W/2 + w/2 + 40, c0 + ch), radius=ch/2, fill=DEEP + (225,), outline=O + (220,)); d = D(cv)
    ar(d, (W/2, c0 + 15 + u), t, f, Wh, 'ms')
    print('cover: title 300 -', round(y), '| chip', c0, '-', round(c0 + ch))
    return cv


def prep():
    cv = bg('lamp-2-wall.jpg', top=0.92, t_end=700, b_start=900)
    shade(cv, [(lambda y: np.full_like(y, 0.35), DEEP)])
    end = head(cv, 2, 'قبل أن تبدأ', [('جهّز سيارتك أولاً', Wh, 64)])
    items = ['أوقف السيارة على أرض مستوية أمام جدار',
             'اضبط ضغط الإطارات وفق توصيات الشركة',
             'حمولة عادية: وقود كافٍ وشخص في مقعد السائق',
             'اضبط مفتاح ارتفاع الأنوار داخل السيارة على 0',
             'شغّل الأضواء المنخفضة (العادية)']
    y = end + 48; rh = 122; gap = 20
    for i, t in enumerate(items):
        glass(cv, (M, y, R_, y + rh), radius=20, fill=CARD + (225,)); d = D(cv)
        f = F(OX, 34); u, dn, w = ink(str(i + 1), f, False); cx, cy = R_ - 48, y + rh/2
        d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=O + (255,)); lt(d, (cx - w/2, cy + (u - dn)/2), str(i + 1), f, N)
        ft = F(AR_BOLD, 31); u2, d2, w2 = ink(t, ft); assert w2 <= R_ - M - 120, t
        ar(d, (R_ - 96, cy + (u2 - d2)/2), t, ft, Wh)
        y += rh + gap
    print('prep: title to', round(end), '| rows end', round(y - gap))
    return cv


def step1():
    cv = Image.new('RGBA', (W*K, H*K), DEEP + (255,))
    base = photo('lamp-2-wall.jpg').filter(ImageFilter.GaussianBlur(26*K)); cv = Image.blend(base, cv, 0.62)
    end = head(cv, 3, 'الخطوة 1', [('حدّد ارتفاع المصباح', Wh, 62), ('على الجدار', O, 62)])
    box = (M, end + 44, R_, end + 44 + 470)
    lx, ly, floor = scene(cv, box, 560, 690, 0, 0, mark=True)
    d = D(cv)                                                   # close-up glow on the wall instead of a beam
    g, gd = layer(); gd.ellipse((690 - 30, ly - 56, 690 + 30, ly + 60), fill=BEAM + (190,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(14*K)))
    d = D(cv); f = F(AR_BOLD, 24); t = 'مركز المصباح'; u, dn, w = ink(t, f)
    ar(d, (R_ - 30, ly - 40), t, f, O)
    y = para(cv, 'قرّب مقدمة السيارة من الجدار، وضع علامة بشريط لاصق عند مركز كل مصباح، ثم صل بين العلامتين بخط أفقي.', box[3] + 40, 32)
    print('step1: title to', round(end), '| diagram', box[1], '-', box[3], '| text ends', round(y))
    return cv


def step2():
    cv = Image.new('RGBA', (W*K, H*K), DEEP + (255,))
    base = photo('lamp-2-wall.jpg').filter(ImageFilter.GaussianBlur(26*K)); cv = Image.blend(base, cv, 0.62)
    end = head(cv, 4, 'الخطوة 2', [('ابتعد 10 أمتار', Wh, 62), ('وراقب حدّ الضوء', O, 62)])
    box = (M, end + 40, R_, end + 40 + 330)
    lx, ly, floor = lamp_at(box, 300)                           # the beam: top edge a little below the mark
    lx, ly, floor = scene(cv, box, 300, R_ - 70, ly + 16, floor - 6, mark=True, dist='10 م')
    pb = (M + 120, box[3] + 34, R_ - 120, box[3] + 34 + 250)
    tape, cut = wall_pattern(cv, pb)
    d = D(cv); f = F(AR_BOLD, 22)
    ar(d, (pb[2] - 20, pb[1] + 34), 'شكل الضوء على الجدار', f, N)
    y = para(cv, 'يجب أن يكون الحدّ العلوي للضوء أسفل خط العلامة بقليل، نحو 10 سم (ميل 1%)، أو وفق ما يحدده دليل سيارتك.', pb[3] + 34, 30)
    print('step2: title to', round(end), '| diagram', box[1], '-', box[3], '| wall', pb[1], '-', pb[3], '| text ends', round(y))
    return cv


def compare():
    cv = Image.new('RGBA', (W*K, H*K), DEEP + (255,))
    base = photo('lamp-1-cover.jpg').filter(ImageFilter.GaussianBlur(26*K)); cv = Image.blend(base, cv, 0.66)
    end = head(cv, 5, 'صحيح أم خطأ؟', [('أين يجب أن يقع الضوء؟', Wh, 58)])
    rows = [(True, 'أسفل الخط بقليل', 'رؤية واضحة دون إزعاج أحد', 10, 4),
            (False, 'مرتفع جداً', 'يُبهر السائقين القادمين', -46, 1.0),
            (False, 'منخفض جداً', 'يقصّر مدى رؤيتك للطريق ليلاً', 30, 4)]
    y = end + 36; rh = 262; gap = 18
    for ok, t1, t2, off, _ in rows:
        box = (M, y, R_, y + rh)
        wall = M + 500
        lx, ly, floor = lamp_at(box, 340); top = ly + off
        lx, ly, floor = scene(cv, (M, y, R_, y + rh), 340, wall, top, min(floor - 6, top + 70) if off < 0 else max(top + 10, floor - 4), mark=True,
                              cut_col=BEAM if ok else (255, 190, 170))
        d = D(cv); icon(d, R_ - 50, y + 52, ok)
        f1 = F(AR_BLACK, 34); u, dn, w = ink(t1, f1); b = y + 52 + (u - dn)/2
        ar(d, (R_ - 92, b), t1, f1, GREEN if ok else (255, 120, 110))
        f2 = F(AR_BOLD, 24); tx = R_ - 24; mw = R_ - (wall + 50)
        lines = wrap(t2, f2, mw); u2, d2, _ = ink('ألإ', f2); b2 = b + dn + 24 + u2
        for ln in lines: ar(d, (tx, b2), ln, f2, Wh); b2 += u2 + d2 + 10
        y += rh + gap
    print('compare: title to', round(end), '| rows end', round(y - gap))
    return cv


def tips():
    cv = bg('lamp-3-screw.jpg', top=0.95, t_end=760, b_start=880)
    shade(cv, [(lambda y: np.full_like(y, 0.30), DEEP)])
    end = head(cv, 6, 'نصائح مهمة', [('حافظ على ضبط', Wh, 62), ('أنوار سيارتك', O, 62)])
    items = [('الضبط عبر براغي خلف المصباح', 'ويُفضّل إجراؤه في مركز صيانة بجهاز خاص'),
             ('استخدم مفتاح ارتفاع الأنوار', 'عند تحميل السيارة بالركاب أو الأمتعة'),
             ('أعد الفحص بعد تغيير اللمبة', 'أو بعد أي حادث ولو كان بسيطاً'),
             ('نظّف عدسات المصابيح', 'فالأوساخ تُضعف الإضاءة وتشتّتها')]
    y = end + 40; rh = 150; gap = 16
    for t1, t2 in items:
        glass(cv, (M, y, R_, y + rh), radius=20, fill=CARD + (230,)); d = D(cv)
        d.rounded_rectangle((R_ - 12, y + 24, R_ - 4, y + rh - 24), radius=4, fill=O + (255,))
        f1 = F(AR_BLACK, 32); u, dn, w = ink(t1, f1); b = y + 26 + u; ar(d, (R_ - 34, b), t1, f1, Wh)
        f2 = F(AR_BOLD, 26); u2, d2, w2 = ink(t2, f2); b2 = b + dn + 22 + u2; ar(d, (R_ - 34, b2), t2, f2, SOFT)
        assert b2 + d2 <= y + rh - 16, (t1, b2 + d2, y + rh)
        y += rh + gap
    print('tips: title to', round(end), '| rows end', round(y - gap))
    return cv


def ask():
    cv = bg('lamp-4-ask.jpg', top=0.80, t_end=900, b_start=1150)
    d = D(cv); nc.chrome(cv, d, 7, TOTAL); d = D(cv)
    fe = F(AR_BOLD, 30); u, dn, w = ink('شاركنا رأيك', fe); eh = 58; y = 330
    lines = [('متى آخر مرة', F(AR_BLACK, 76), Wh), ('فحصت ضبط أنوار', F(AR_BLACK, 76), Wh), ('سيارتك؟', F(AR_BLACK, 100), O)]
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
    for i, fn in enumerate((cover, prep, step1, step2, compare, tips, ask), 1):
        cv = fn(); p = os.path.join(out, f'care-headlight-aim-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
