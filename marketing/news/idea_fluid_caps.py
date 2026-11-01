"""«عندك فكرة»: what the fluid caps under the bonnet mean — four dark slides, 2160x2700.

usage: python3 idea_fluid_caps.py <brand-kit dir> <out dir>
Photos: Canva AI (caps-1-cover.jpg, caps-4-ask.jpg). Each cap is drawn: a ridged dark cap with its symbol,
sitting on a disc of its fluid's colour. Layout is in 1080 units (news_carousel.hires scales by K).
Every text line is placed from its measured ink box with at least 24 units clear.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'dark'; nc.SECTION = 'idea'
K = nc.K; TOTAL = 4
CARD = (14, 34, 56); YEL = (255, 196, 40); IDEA = nc.IDEA_BLUE
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')


def ink(t, f):
    """(above, below) the baseline in 1080 units."""
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', direction='rtl', language='ar'); return -b[1]/K, b[3]/K


def stack(d, lines, top, x, anchor, gap=26):
    y = top - gap
    for t, f, col in lines:
        up, dn = ink(t, f); b = y + gap + up
        ar(d, (x, b), t, f, col, anchor); y = b + dn
    return y


def shade(cv, bands):
    ys = np.arange(H*K, dtype=np.float32)/K
    for fn, rgb in bands:
        with np.errstate(invalid='ignore'):
            a = np.clip(np.nan_to_num(fn(ys), nan=0.0), 0, 1)
        lay = Image.new('RGBA', (W*K, H*K), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)


def layer():
    lay = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0)); return lay, D(lay)


def field():
    return nc.field()


# ---- symbols (centre cx, cy; s = symbol box; colour c) ---------------------------------------------------
def sym_oil(d, cx, cy, s, c):
    """Classic oil can: body, spout up to the left, a drop falling from its tip."""
    w = s*0.075
    d.rounded_rectangle((cx - s*0.10, cy - s*0.06, cx + s*0.38, cy + s*0.24), radius=s*0.04, fill=c)       # body
    d.polygon([(cx - s*0.10, cy - s*0.04), (cx - s*0.10, cy + s*0.08), (cx - s*0.44, cy - s*0.16), (cx - s*0.42, cy - s*0.22)], fill=c)  # spout
    d.rectangle((cx + s*0.06, cy - s*0.14, cx + s*0.18, cy - s*0.06), fill=c)                             # cap on top
    d.arc((cx + s*0.30, cy - s*0.04, cx + s*0.50, cy + s*0.18), -90, 90, fill=c, width=round(w))          # handle
    r = s*0.055; x0, y0 = cx - s*0.43, cy - s*0.04
    d.polygon([(x0, y0), (x0 - r, y0 + r*1.4), (x0 + r, y0 + r*1.4)], fill=c)
    d.ellipse((x0 - r, y0 + r*0.9, x0 + r, y0 + r*2.9), fill=c)

def sym_cool(d, cx, cy, s, c):
    w = s*0.08
    d.rounded_rectangle((cx - s*0.06, cy - s*0.42, cx + s*0.06, cy + s*0.04), radius=s*0.06, fill=c)
    d.ellipse((cx - s*0.12, cy - s*0.04, cx + s*0.12, cy + s*0.20), fill=c)
    for k in (-0.30, -0.18): d.line([(cx + s*0.08, cy + k*s), (cx + s*0.20, cy + k*s)], fill=c, width=round(w*0.7))
    for row in (0.30, 0.44):
        pts = [(cx - s*0.44 + i*s*0.11, cy + row*s + (s*0.04 if i % 2 else -s*0.04)) for i in range(9)]
        d.line(pts, fill=c, width=round(w*0.8), joint='curve')

def sym_brake(d, cx, cy, s, c):
    w = s*0.08; r = s*0.26
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=round(w))
    for sx in (-1, 1):
        R = s*0.40; box = (cx - R, cy - R, cx + R, cy + R)
        d.arc(box, 135 if sx < 0 else -45, 225 if sx < 0 else 45, fill=c, width=round(w))
    d.rounded_rectangle((cx - s*0.04, cy - s*0.16, cx + s*0.04, cy + s*0.05), radius=s*0.03, fill=c)
    d.ellipse((cx - s*0.045, cy + s*0.09, cx + s*0.045, cy + s*0.18), fill=c)

def sym_washer(d, cx, cy, s, c):
    w = s*0.07
    d.polygon([(cx - s*0.44, cy + s*0.30), (cx - s*0.34, cy - s*0.06), (cx + s*0.34, cy - s*0.06), (cx + s*0.44, cy + s*0.30)], outline=c, width=round(w))
    d.line([(cx, cy + s*0.30), (cx - s*0.24, cy + s*0.04)], fill=c, width=round(w*0.8))
    for a in range(-60, 61, 30):
        v = math.radians(a - 90); r1 = s*0.22
        for k, rr in enumerate((r1, r1*1.45)):
            x, y = cx + math.cos(v)*rr, cy - s*0.10 + math.sin(v)*rr
            d.ellipse((x - s*0.035, y - s*0.035, x + s*0.035, y + s*0.035), fill=c)

def sym_steer(d, cx, cy, s, c):
    w = s*0.08; r = s*0.30; yc = cy - s*0.08
    d.ellipse((cx - r, yc - r, cx + r, yc + r), outline=c, width=round(w))
    d.ellipse((cx - s*0.08, yc - s*0.08, cx + s*0.08, yc + s*0.08), fill=c)
    for a in (180, 0, 90):
        v = math.radians(a); d.line([(cx, yc), (cx + math.cos(v)*r, yc + math.sin(v)*r)], fill=c, width=round(w))
    pts = [(cx - s*0.40 + i*s*0.10, cy + s*0.38 + (s*0.035 if i % 2 else -s*0.035)) for i in range(9)]
    d.line(pts, fill=c, width=round(w*0.7), joint='curve')


def cap(cv, cx, cy, r, fluid, sym, sym_col=YEL):
    """A ridged dark cap seen from above on a disc of its fluid's colour, with a soft glow."""
    g, gd = layer(); gd.ellipse((cx - r*1.35, cy - r*1.35, cx + r*1.35, cy + r*1.35), fill=fluid+(90,))
    cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(18*K)))
    lay, d = layer()
    d.ellipse((cx - r*1.12, cy - r*1.12, cx + r*1.12, cy + r*1.12), fill=fluid+(255,))
    n = 16                                                            # ridges
    pts = []
    for i in range(n*2):
        v = math.pi*i/n; rr = r if i % 2 == 0 else r*0.92
        pts.append((cx + math.cos(v)*rr, cy + math.sin(v)*rr))
    d.polygon(pts, fill=(28, 30, 34, 255))
    d.ellipse((cx - r*0.80, cy - r*0.80, cx + r*0.80, cy + r*0.80), fill=(18, 20, 24, 255), outline=(70, 74, 82, 255), width=2)
    d.arc((cx - r*0.80, cy - r*0.80, cx + r*0.80, cy + r*0.80), 200, 300, fill=(120, 126, 136, 255), width=2)   # highlight
    sym(d, cx, cy, r*1.05, sym_col+(255,))
    cv.alpha_composite(lay)


CAPS = [  # symbol, fluid colour, symbol colour, name, what it does, tip
    (sym_oil, (40, 42, 46), YEL, 'زيت المحرك', 'يزيّت أجزاء المحرك ويقلّل الاحتكاك', 'افحص مستواه بالعصا مرة كل شهر'),
    (sym_cool, (236, 92, 120), YEL, 'سائل التبريد', 'يحافظ على حرارة المحرك ضمن الحد الطبيعي', 'لا تفتح غطاءه والمحرك ساخن'),
    (sym_brake, (226, 196, 90), YEL, 'سائل الفرامل', 'ينقل ضغط الدواسة إلى نظام الفرامل', 'يُغيَّر حسب الموعد في دليل سيارتك'),
    (sym_washer, (52, 132, 220), Wh, 'سائل المساحات', 'لتنظيف الزجاج الأمامي ووضوح الرؤية', 'استخدم سائلاً لا يتجمّد في الشتاء'),
    (sym_steer, (214, 214, 70), Wh, 'زيت الباور', 'يشغّل نظام التوجيه الهيدروليكي', 'سيارات حديثة كثيرة توجيهها كهربائي بلا خزان'),
]


def card(cv, y0, rh, i, item):
    sym, fluid, scol, name, what, tip = item
    lay, ld = layer()
    ld.rounded_rectangle((M, y0, R_, y0 + rh), radius=28, fill=CARD+(235,), outline=(255, 255, 255, 34), width=1)
    cv.alpha_composite(lay)
    cr = 74; cx = R_ - 36 - cr*1.12; cy = y0 + rh/2
    cap(cv, cx, cy, cr, fluid, sym, scol)
    d = D(cv); tx = cx - cr*1.12 - 34
    num = f'{i:02d}'; d.text((M + 34, y0 + 52), num, font=F('Oxanium-800.ttf', 30), fill=O+(255,), anchor='ls')
    f1, f2, f3 = F(AR_BLACK, 40), F(AR_BOLD, 27), F(AR_BOLD, 25)
    u1, d1 = ink(name, f1); u2, d2 = ink(what, f2); u3, d3 = ink(tip, f3)
    g1, g2 = 18, 24
    blk = u1 + d1 + g1 + u2 + d2 + g2 + u3 + d3; b1 = cy - blk/2 + u1
    ar(d, (tx, b1), name, f1, Wh)
    b2 = b1 + d1 + g1 + u2; ar(d, (tx, b2), what, f2, SOFT)
    b3 = b2 + d2 + g2 + u3
    tw = nc.w_ar(tip, f3)
    d.ellipse((tx - 16, b3 - u3*0.55 - 7, tx - 2, b3 - u3*0.55 + 7), fill=O+(255,))
    ar(d, (tx - 28, b3), tip, f3, O)
    return tx - 28 - tw


def cover():
    cv = nc.bg('caps-1-cover.jpg')
    shade(cv, [(lambda y: (1 - y/720)**1.1*0.95, DEEP), (lambda y: (y - 1060)/200*0.92, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    y = stack(d, [('هل تعرف رموز', F(AR_BLACK, 84), Wh), ('أغطية السوائل', F(AR_BLACK, 104), O),
                  ('في سيارتك؟', F(AR_BLACK, 84), Wh)], 190, W/2, 'ms')
    t = '5 أغطية تحت الكبوت.. ولكل رمز معنى'; fs = F(AR_BOLD, 32); up, dn = ink(t, fs); tw = nc.w_ar(t, fs) + 70
    c0 = y + 34; ch = up + dn + 30
    lay, ld = layer(); ld.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, fill=DEEP+(210,)); cv.alpha_composite(lay); d = D(cv)
    d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, outline=O+(255,), width=3)
    ar(d, (W/2, c0 + 15 + up), t, fs, Wh, 'ms')
    # the five caps in a row along the bottom
    xs = [W/2 + k*190 for k in (2, 1, 0, -1, -2)]
    for x, (sym, fluid, scol, *_r) in zip(xs, CAPS): cap(cv, x, 1150, 58, fluid, sym, scol)
    print('cover text ends', round(c0 + ch), '| caps 1085 - 1215')
    return cv


def caps_slide(n, label, title, items, first, note=None):
    cv = field(); d = D(cv); nc.chrome(cv, d, n, TOTAL); d = D(cv)
    y = stack(d, [(label, F(AR_BOLD, 30), O), (title, F(AR_BLACK, 62), Wh)], 160, R_, 'rs', gap=24)
    top = y + 40; rh = 272; gap = 24
    for i, it in enumerate(items):
        left = card(cv, top + i*(rh + gap), rh, first + i, it)
        if left < M + 90: print('  WARNING card', first + i, 'text reaches', round(left))
    end = top + len(items)*(rh + gap) - gap
    if note:                                                          # tips box: title + bullet lines
        title_, lines_ = note; top2 = end + gap; pad = 34
        f0, f1 = F(AR_BLACK, 38), F(AR_BOLD, 28)
        u0, d0 = ink(title_, f0); hs = [ink(t, f1) for t in lines_]
        h = pad + u0 + d0 + sum(26 + u + dd for u, dd in hs) + pad
        lay, ld = layer()
        ld.rounded_rectangle((M, top2, R_, top2 + h), radius=28, fill=IDEA+(150,), outline=(255, 255, 255, 50), width=1)
        cv.alpha_composite(lay); d = D(cv)
        d.rectangle((R_ - 8, top2 + 30, R_, top2 + h - 30), fill=O+(255,))
        b = top2 + pad + u0; ar(d, (R_ - 40, b), title_, f0, Wh); y = b + d0
        for t, (u, dd) in zip(lines_, hs):
            b = y + 26 + u
            d.ellipse((R_ - 54, b - u*0.55 - 7, R_ - 40, b - u*0.55 + 7), fill=O+(255,))
            ar(d, (R_ - 66, b), t, f1, Wh); y = b + dd
        end = top2 + h
    print('slide', n, 'ends', round(end))
    return cv


def ask():
    cv = nc.bg('caps-4-ask.jpg')
    shade(cv, [(lambda y: (1 - (y - 120)/700)**1.1*0.95, DEEP), (lambda y: (y - 1150)/170*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, TOTAL, TOTAL); d = D(cv)
    fe = F(AR_BOLD, 30); ew = nc.w_ar('شاركنا', fe) + 52
    d.rectangle((W/2 - ew/2, 220, W/2 + ew/2, 278), fill=O+(255,))
    ar(d, (W/2, 250), 'شاركنا', fe, N, 'mm')
    y = stack(d, [('أيّ هذه الأغطية', F(AR_BLACK, 84), Wh), ('تفحصه بنفسك؟', F(AR_BLACK, 96), O),
                  ('اكتب لنا في التعليقات', F(AR_BOLD, 38), SOFT)], 300, W/2, 'ms')
    print('ask text ends', round(y))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(),
              caps_slide(2, 'تحت الكبوت', 'السوائل الأساسية', CAPS[:3], 1),
              caps_slide(3, 'تحت الكبوت', 'سوائل لا تنسَها', CAPS[3:], 4,
                         note=('قبل أن تفتح أي غطاء', ['افحص السوائل والمحرك بارد والسيارة على أرض مستوية',
                                                       'لا تخلط السوائل ببعضها، فلكل غطاء سائله فقط',
                                                       'إذا انخفض أي سائل بسرعة، افحص السيارة عند فني مختص'])),
              ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-fluid-caps-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
