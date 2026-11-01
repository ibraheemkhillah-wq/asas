"""«عندك فكرة»: what the fluid caps under the bonnet mean — four dark slides, 2160x2700.

usage: python3 idea_fluid_caps.py <brand-kit dir> <out dir>
Photos: Canva AI. caps-1-cover.jpg / caps-4-ask.jpg are scenes; res-*.jpg are product shots of each reservoir
with its cap on the same deep navy as the page, feathered in so they sit on the slide without a frame.
Slides 2-3 zig-zag: photo on one side, its text on the other. Layout is in 1080 units (news_carousel.hires
scales by K). Every text line is placed from its measured ink box with at least 24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'dark'; nc.SECTION = 'idea'
K = nc.K; TOTAL = 4
PAGE = (3, 20, 43)                       # the product shots' backdrop, so photos melt into the page
IDEA = nc.IDEA_BLUE
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')


def ink(t, f):
    """(above, below) the baseline in 1080 units."""
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', direction='rtl', language='ar'); return -b[1]/K, b[3]/K


def wrap(t, f, maxw):
    lines, cur = [], ''
    for w in t.split(' '):
        c = (cur + ' ' + w).strip()
        if cur and nc.w_ar(c, f) > maxw: lines.append(cur); cur = w
        else: cur = c
    lines = lines + [cur]
    if len(lines) == 2:                                   # balance two lines so no word is left alone
        ws = t.split(' '); best = None
        for k in range(1, len(ws)):
            a, b = ' '.join(ws[:k]), ' '.join(ws[k:])
            wa, wb = nc.w_ar(a, f), nc.w_ar(b, f)
            if max(wa, wb) <= maxw and (best is None or abs(wa - wb) < best[0]): best = (abs(wa - wb), [a, b])
        if best: lines = best[1]
    return lines


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


def page():
    """Flat product-shot navy with a soft key light from the top centre."""
    ys, xs = np.mgrid[0:H*K, 0:W*K].astype(np.float32)/K
    g = np.exp(-(((xs - 540)/700)**2 + ((ys - 420)/620)**2))[..., None]
    bg = np.array(PAGE, np.float32) + (np.array((16, 44, 76), np.float32) - np.array(PAGE, np.float32))*g*0.6
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA')


def product(cv, name, cx, cy, size, glow):
    """The reservoir shot, feathered with a radial mask; a faint glow of the fluid colour behind it."""
    g, gd = layer(); gd.ellipse((cx - size*0.36, cy - size*0.30, cx + size*0.36, cy + size*0.36), fill=glow+(70,))
    cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(40*K)))
    s = round(size*K)
    src = Image.open(os.path.join(HERE, name)).convert('RGB'); c = round(src.width*0.13)   # trim the empty backdrop
    im = src.crop((c, c, src.width - c, src.height - c)).resize((s, s), Image.LANCZOS)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)/s - 0.5
    r = np.sqrt(xx**2 + yy**2)
    m = np.clip((0.50 - r)/0.12, 0, 1)**1.4
    im = im.convert('RGBA'); im.putalpha(Image.fromarray((m*255).astype(np.uint8)))
    cv.alpha_composite(im, (round((cx - size/2)*K), round((cy - size/2)*K)))


CAPS = [  # photo, glow colour, name, what it does, tip
    ('res-oil.jpg', (200, 150, 40), 'زيت المحرك', 'يزيّت أجزاء المحرك ويقلّل الاحتكاك', 'افحص مستواه بالعصا مرة كل شهر'),
    ('res-cool.jpg', (236, 92, 120), 'سائل التبريد', 'يحافظ على حرارة المحرك ضمن الحد الطبيعي', 'لا تفتح غطاءه والمحرك ساخن'),
    ('res-brake.jpg', (226, 176, 60), 'سائل الفرامل', 'ينقل ضغط الدواسة إلى نظام الفرامل', 'يُغيَّر حسب الموعد في دليل سيارتك'),
    ('res-washer.jpg', (52, 132, 220), 'سائل المساحات', 'لتنظيف الزجاج الأمامي ووضوح الرؤية', 'استخدم سائلاً لا يتجمّد في الشتاء'),
    ('res-steer.jpg', (190, 200, 70), 'زيت الباور', 'يشغّل نظام التوجيه الهيدروليكي', 'سيارات حديثة كثيرة توجيهها كهربائي بلا خزان'),
]


def item(cv, i, num, it, top, bh):
    """One band: photo on the right for even rows, left for odd; text block centred vertically beside it."""
    photo, glow, name, what, tip = it
    right = i % 2 == 0; size = bh + 30; cy = top + bh/2
    pcx = R_ - size/2 + 30 if right else M + size/2 - 30
    product(cv, photo, pcx, cy, size, glow)
    d = D(cv)
    tx = (pcx - size/2 + 10) if right else R_                     # right edge of the text column
    tl = M if right else (pcx + size/2 - 10)                      # left edge
    maxw = tx - tl
    fn, f1, f2, f3 = F('Oxanium-800.ttf', 34), F(AR_BLACK, 46), F(AR_BOLD, 28), F(AR_BOLD, 26)
    rows = [(f'{num:02d}', fn, O, 'num'), (name, f1, Wh, 'name')]
    rows += [(l, f2, SOFT, 'what') for l in wrap(what, f2, maxw)]
    rows += [(l, f3, O, 'tip') for l in wrap(tip, f3, maxw - 30)]
    gaps = {'num': 0, 'name': 14, 'what': 22, 'tip': 26}
    ext = []
    for t, f, c, k in rows:
        if k == 'num':
            b = _m.textbbox((0, 0), t, font=f.real, anchor='ls'); ext.append((-b[1]/K, b[3]/K))
        else: ext.append(ink(t, f))
    total = sum(u + dn for u, dn in ext); prev = None
    for (t, f, c, k), (u, dn) in zip(rows, ext):
        g = 0 if prev is None else (gaps[k] if k != prev else 12); total += g; prev = k
    y = cy - total/2; prev = None
    for (t, f, c, k), (u, dn) in zip(rows, ext):
        g = 0 if prev is None else (gaps[k] if k != prev else 12)
        b = y + g + u
        if k == 'num':
            d.text((tx, b), t, font=f, fill=c+(255,), anchor='rs')
            d.rectangle((tx - nc.w_lt(t, f) - 70, b - u*0.45 - 2, tx - nc.w_lt(t, f) - 16, b - u*0.45 + 2), fill=O+(160,))
        elif k == 'tip':
            first = prev != 'tip'
            if first: d.ellipse((tx - 14, b - u*0.55 - 7, tx, b - u*0.55 + 7), fill=O+(255,))
            ar(d, (tx - 26, b), t, f, c)
        else:
            ar(d, (tx, b), t, f, c)
        y = b + dn; prev = k
    return round(cy - total/2), round(y)


def tips_box(cv, top, title_, lines_):
    pad = 28; f0, f1 = F(AR_BLACK, 34), F(AR_BOLD, 26)
    u0, d0 = ink(title_, f0); hs = [ink(t, f1) for t in lines_]
    h = pad + u0 + d0 + sum(22 + u + dd for u, dd in hs) + pad
    lay, ld = layer()
    ld.rounded_rectangle((M, top, R_, top + h), radius=28, fill=IDEA+(120,), outline=(255, 255, 255, 46), width=1)
    cv.alpha_composite(lay); d = D(cv)
    d.rectangle((R_ - 8, top + 28, R_, top + h - 28), fill=O+(255,))
    b = top + pad + u0; ar(d, (R_ - 40, b), title_, f0, Wh); y = b + d0
    for t, (u, dd) in zip(lines_, hs):
        b = y + 22 + u
        d.ellipse((R_ - 54, b - u*0.55 - 7, R_ - 40, b - u*0.55 + 7), fill=O+(255,))
        ar(d, (R_ - 66, b), t, f1, Wh); y = b + dd
    return top + h


def caps_slide(n, label, title, items, first, bh, note=None):
    cv = page(); d = D(cv); nc.chrome(cv, d, n, TOTAL); d = D(cv)
    y = stack(d, [(label, F(AR_BOLD, 30), O), (title, F(AR_BLACK, 62), Wh)], 160, R_, 'rs', gap=24)
    top = y + 34
    for i, it in enumerate(items):
        t0, t1 = item(cv, i, first + i, it, top + i*bh, bh)
        print(f'  item {first + i}: text {t0}-{t1} in band {round(top + i*bh)}-{round(top + (i + 1)*bh)}')
    end = top + len(items)*bh
    if note: end = tips_box(cv, end + 8, *note)
    print('slide', n, 'ends', round(end))
    return cv


def cover():
    cv = nc.bg('caps-1-cover.jpg')
    shade(cv, [(lambda y: (1 - y/800)**1.1*0.95, DEEP), (lambda y: (y - 1080)/200*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    y = stack(d, [('هل تعرف رموز', F(AR_BLACK, 84), Wh), ('أغطية السوائل', F(AR_BLACK, 104), O),
                  ('في سيارتك؟', F(AR_BLACK, 84), Wh)], 270, W/2, 'ms')
    t = '5 أغطية تحت الكبوت.. ولكل رمز معنى'; fs = F(AR_BOLD, 32); up, dn = ink(t, fs); tw = nc.w_ar(t, fs) + 70
    c0 = y + 36; ch = up + dn + 30
    lay, ld = layer(); ld.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, fill=DEEP+(210,)); cv.alpha_composite(lay); d = D(cv)
    d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, outline=O+(255,), width=3)
    ar(d, (W/2, c0 + 15 + up), t, fs, Wh, 'ms')
    print('cover text', 270, '-', round(c0 + ch))
    return cv


def ask():
    cv = nc.bg('caps-4-ask.jpg')
    shade(cv, [(lambda y: (1 - (y - 160)/720)**1.1*0.95, DEEP), (lambda y: (y - 1150)/170*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, TOTAL, TOTAL); d = D(cv)
    fe = F(AR_BOLD, 30); ew = nc.w_ar('شاركنا', fe) + 52
    d.rectangle((W/2 - ew/2, 290, W/2 + ew/2, 348), fill=O+(255,))
    ar(d, (W/2, 320), 'شاركنا', fe, N, 'mm')
    y = stack(d, [('أيّ هذه الأغطية', F(AR_BLACK, 84), Wh), ('تفحصه بنفسك؟', F(AR_BLACK, 96), O),
                  ('اكتب لنا في التعليقات', F(AR_BOLD, 38), SOFT)], 376, W/2, 'ms')
    print('ask text 290 -', round(y))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(),
              caps_slide(2, 'تحت الكبوت', 'السوائل الأساسية', CAPS[:3], 1, 300),
              caps_slide(3, 'تحت الكبوت', 'سوائل لا تنسَها', CAPS[3:], 4, 312,
                         note=('قبل أن تفتح أي غطاء', ['افحص السوائل والمحرك بارد والسيارة على أرض مستوية',
                                                       'لا تخلط السوائل ببعضها، فلكل غطاء سائله فقط',
                                                       'إذا انخفض أي سائل بسرعة، افحص السيارة عند فني مختص'])),
              ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-fluid-caps-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
