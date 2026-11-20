"""«اعتنِ بسيارتك»: what the tyre wear pattern says about your car — six DARK slides, 2160x2700.

usage: python3 tyre_wear.py <brand-kit dir> <out dir>
Photos: Canva AI. wear-cover.jpg; the four worn tyres are Canva edits of one tread photo (wear-tread.png), each
showing a real wear pattern (wear-centre/edges/side/cupping.png); the parts are Canva cutouts (wear-gauge/arm/shock.png).
Causes (standard tyre-wear guidance): centre = over-inflation; both edges = under-inflation; one side =
wheel alignment (camber/toe) or worn suspension arms; cupping = worn shock absorbers or unbalanced wheels.
Reuses the dark helpers of ../news/idea_tyre_code.py. Layout in 1080 units; lines placed from measured ink.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'news')); sys.path.insert(0, sys.argv[1])
import idea_tyre_code as tc
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.SECTION = 'care'; K = nc.K; TOTAL = 6
F, D, ar, lt, ink, shade, layer, glass, kicker, halo = tc.F, tc.D, tc.ar, tc.lt, tc.ink, tc.shade, tc.layer, tc.glass, tc.kicker, tc.halo
CARD = tc.CARD; OX = tc.OX; RED = (232, 76, 68)

# key, pattern name, worn zone (x fractions of the tread), part image, cause, fix
TYPES = [('centre', 'تآكل في الوسط', [(0.33, 0.67)], 'wear-gauge.png',
          'ضغط الهواء مرتفع', 'اضبط الضغط وفق الرقم المدوّن على إطار باب السائق'),
         ('edges', 'تآكل في الطرفين', [(0.04, 0.24), (0.76, 0.96)], 'wear-gauge.png',
          'ضغط الهواء منخفض', 'افحص الضغط مرة كل شهر والإطارات باردة'),
         ('side', 'تآكل في جهة واحدة', [(0.04, 0.45)], 'wear-arm.png',
          'خلل في زوايا العجلات (الميزان) أو تلف أذرعة التعليق', 'افحص ضبط زوايا العجلات وحالة الأذرعة'),
         ('cupping', 'تآكل متقطّع غير منتظم', [(0.10, 0.90)], 'wear-shock.png',
          'ضعف المساعدات (الممتصات) أو عدم توازن العجلات', 'افحص المساعدات واطلب موازنة العجلات')]


def photo(name):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA')
    sc = max(W*K/im.width, H*K/im.height); im = im.resize((round(im.width*sc), round(im.height*sc)), Image.LANCZOS)
    l = (im.width - W*K)//2; t = (im.height - H*K)//2
    return im.crop((l, t, l + W*K, t + H*K))


def field():
    """Dark backdrop: the cover photo, heavily blurred and dimmed, so every slide shares its light."""
    base = photo('wear-cover.jpg').filter(ImageFilter.GaussianBlur(30*K))
    return Image.blend(base, Image.new('RGBA', base.size, DEEP + (255,)), 0.60)


def wrap(t, f, maxw):
    out, cur = [], ''
    for wd in t.split():
        c = (cur + ' ' + wd).strip()
        if cur and ink(c, f)[2] > maxw: out.append(cur); cur = wd
        else: cur = c
    return out + [cur]


def lines_at(d, t, f, x, top, maxw, col, gap=12, anchor='rs'):
    u, dn, _ = ink('ألإ', f); y = top
    for ln in wrap(t, f, maxw):
        b = y + u; ar(d, (x, b), ln, f, col, anchor); y = b + dn + gap
    return y - gap


def paste_fit(cv, name, box, glow=None):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA'); x0, y0, x1, y1 = box
    s = min((x1 - x0)/im.width, (y1 - y0)/im.height); w, h = im.width*s, im.height*s
    px, py = x0 + (x1 - x0 - w)/2, y0 + (y1 - y0 - h)/2
    if glow:
        g, gd = layer(); gd.ellipse((px - 20, py + h*0.2, px + w + 20, py + h + 30), fill=glow); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(40*K)))
    sh, sd = layer(); sd.ellipse((px + w*0.1, py + h - 10, px + w*0.9, py + h + 22), fill=(0, 0, 0, 160)); cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12*K)))
    cv.alpha_composite(im.resize((round(w*K), round(h*K)), Image.LANCZOS), (round(px*K), round(py*K)))
    return px, py, w, h


def cover():
    ph = photo('wear-cover.jpg'); SH = 230                    # photo lowered so the tyres start under the chip
    cv = Image.new('RGBA', ph.size, DEEP + (255,)); cv.alpha_composite(ph, (0, SH*K))
    top = ph.crop((0, 0, W*K, 30*K)).resize((W*K, SH*K + 60*K)).filter(ImageFilter.GaussianBlur(20*K))
    fade = Image.new('L', (1, SH*K + 60*K)); fade.putdata([255 if i < SH*K else int(255*(1 - (i - SH*K)/(60*K))) for i in range(SH*K + 60*K)])
    cv.paste(top, (0, 0), fade.resize((W*K, SH*K + 60*K)))
    shade(cv, [(lambda y: (1 - y/640)**1.2*0.88, DEEP), (lambda y: ((y - 1160)/100)*0.9, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, TOTAL)
    lines = [('شكل تآكل الإطار', Wh, 80), ('يكشف عطل سيارتك', O, 80)]
    y = 300 - 26; draws = []
    for t, col, size in lines:
        f = F(AR_BLACK, size); u, dn, w = ink(t, f); assert w <= R_ - M, t
        b = y + 26 + u; draws.append(((W/2, b), t, f, 'ms', col)); y = b + dn
    halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws]); d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    t = '4 أنماط شائعة وما تشير إليه'; f = F(AR_BOLD, 32); u, dn, w = ink(t, f); c0 = y + 36; ch = u + dn + 30
    glass(cv, (W/2 - w/2 - 40, c0, W/2 + w/2 + 40, c0 + ch), radius=ch/2, fill=DEEP + (225,), outline=O + (220,)); d = D(cv)
    ar(d, (W/2, c0 + 15 + u), t, f, Wh, 'ms')
    print('cover: title 300 -', round(y), '| chip', round(c0), '-', round(c0 + ch))
    return cv


def pattern(n):
    key, name, zones, part, cause, fix = TYPES[n]
    cv = field(); d = D(cv); nc.chrome(cv, d, n + 2, TOTAL); d = D(cv)
    k_end = kicker(d, f'النمط {n + 1}')
    f = F(AR_BLACK, 64); u, dn, w = ink(name, f); assert w <= R_ - M, name
    b = k_end + 30 + u; halo(cv, [((R_, b), name, f, 'rs')], r=14); d = D(cv); ar(d, (R_, b), name, f, Wh); top = b + dn + 44
    # the tyre on the right, with the worn zone bracketed
    tx0, tx1, ty0, ty1 = 590, R_ + 10, top + 70, 1230
    px, py, pw, ph = paste_fit(cv, f'wear-{key}.png', (tx0, ty0, tx1, ty1), glow=O + (60,))
    d = D(cv); by = ty0 - 22
    for a, b_ in zones:
        x0, x1 = px + pw*a, px + pw*b_
        d.line([(x0, by), (x1, by)], fill=O + (255,), width=4)
        for xx in (x0, x1): d.line([(xx, by), (xx, by + 18)], fill=O + (255,), width=4)
        d.line([((x0 + x1)/2, by), ((x0 + x1)/2, by - 14)], fill=O + (255,), width=4)
    t = 'منطقة التآكل'; fl = F(AR_BOLD, 24); u, dn, w = ink(t, fl)
    ar(d, (px + pw/2, by - 22 - dn), t, fl, O, 'ms')
    # left column: cause (with the part) and fix
    cx0, cx1 = M, 560; y = top
    glass(cv, (cx0, y, cx1, y + 560), radius=24, fill=CARD + (225,)); d = D(cv)
    fc = F(AR_BOLD, 26); u, dn, w = ink('السبب', fc); ch = u + dn + 22
    d.rounded_rectangle((cx1 - 24 - w - 40, y + 24, cx1 - 24, y + 24 + ch), radius=ch/2, fill=RED + (255,))
    ar(d, (cx1 - 24 - 20, y + 24 + 11 + u), 'السبب', fc, Wh)
    paste_fit(cv, part, (cx0 + 40, y + 24 + ch + 24, cx1 - 40, y + 24 + ch + 24 + 250)); d = D(cv)
    end = lines_at(d, cause, F(AR_BLACK, 32), cx1 - 26, y + 24 + ch + 24 + 250 + 28, cx1 - cx0 - 52, Wh)
    assert end <= y + 560 - 20, (name, end)
    y2 = y + 560 + 24
    glass(cv, (cx0, y2, cx1, y2 + 240), radius=24, fill=(14, 60, 58, 230), outline=(22, 138, 128, 200)); d = D(cv)
    fh = F(AR_BOLD, 26); u, dn, w = ink('الحل', fh); ch2 = u + dn + 22
    d.rounded_rectangle((cx1 - 24 - w - 40, y2 + 22, cx1 - 24, y2 + 22 + ch2), radius=ch2/2, fill=(22, 138, 128, 255))
    ar(d, (cx1 - 24 - 20, y2 + 22 + 11 + u), 'الحل', fh, Wh)
    end2 = lines_at(d, fix, F(AR_BOLD, 28), cx1 - 26, y2 + 22 + ch2 + 22, cx1 - cx0 - 52, Wh)
    assert end2 <= y2 + 240 - 16, (name, end2)
    print(f'pattern {n + 1}: title to {round(top - 44)} | cause card {round(y)}-{round(y + 560)} text to {round(end)} | fix {round(y2)}-{round(y2 + 240)} text to {round(end2)} | tyre {round(py)}-{round(py + ph)}')
    return cv


def summary():
    cv = field(); d = D(cv); nc.chrome(cv, d, TOTAL, TOTAL); d = D(cv)
    k_end = kicker(d, 'الخلاصة')
    t = 'افحص إطاراتك.. واقرأ رسالتها'; f = F(AR_BLACK, 56); u, dn, w = ink(t, f); assert w <= R_ - M
    b = k_end + 30 + u; ar(d, (R_, b), t, f, Wh); y = b + dn + 36
    cw = (R_ - M - 24)/2; chh = 330
    short = {'centre': 'ضغط مرتفع', 'edges': 'ضغط منخفض', 'side': 'زوايا العجلات', 'cupping': 'المساعدات'}
    for i, (key, name, *_r) in enumerate(TYPES):
        x1 = R_ - (i % 2)*(cw + 24); x0 = x1 - cw; y0 = y + (i//2)*(chh + 24)
        glass(cv, (x0, y0, x1, y0 + chh), radius=22, fill=CARD + (225,))
        paste_fit(cv, f'wear-{key}.png', (x0 + 16, y0 + 16, x0 + 130, y0 + chh - 16))
        d = D(cv); fn = F(AR_BLACK, 28); lines_at(d, name, fn, x1 - 20, y0 + 30, cw - 170, Wh, gap=8)
        fs = F(AR_BOLD, 24); u2, d2, w2 = ink('السبب', fs); yy = y0 + chh - 30 - 50
        d.rounded_rectangle((x1 - 20 - w2 - 24, yy - 46, x1 - 20, yy - 6), radius=20, fill=RED + (255,))
        ar(d, (x1 - 20 - 12, yy - 26 + (u2 - d2)/2), 'السبب', fs, Wh)
        fv = F(AR_BLACK, 30); u3, d3, w3 = ink(short[key], fv); ar(d, (x1 - 20, yy + 14 + u3), short[key], fv, O)
    end = y + 2*chh + 24
    q = 'هل لاحظت تآكلاً غير طبيعي في إطاراتك؟'; fq = F(AR_BLACK, 34); u, dn, w = ink(q, fq); assert w <= R_ - M
    qh = u + dn + 34; q0 = end + 34
    glass(cv, (M, q0, R_, q0 + qh), radius=qh/2, fill=O + (255,), outline=(0, 0, 0, 0)); d = D(cv)
    ar(d, (W/2, q0 + 17 + u), q, fq, N, 'ms')
    print('summary: grid', round(y), '-', round(end), '| question', round(q0), '-', round(q0 + qh))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover()] + [pattern(i) for i in range(4)] + [summary()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'care-tyre-wear-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
