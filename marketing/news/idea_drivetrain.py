"""«عندك فكرة»: front, rear or all-wheel drive? Six dark slides, 2160x2700.

usage: python3 idea_drivetrain.py <brand-kit dir> <out dir>
Photos: Canva AI (drive-*.jpg). Each drive type gets a drawn top-view chassis that lights up the driven wheels.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY, SOFT, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT
from PIL import Image, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'dark'; nc.SECTION = 'idea'
K = nc.K
GREY = (120, 136, 156); CARD = (14, 34, 56); RED = (232, 86, 70)
TYPES = {   # key: (title, latin, one-liner, pros, cons, where)
    'fwd': ('دفع أمامي', 'FWD', 'العجلات الأمامية تسحب السيارة',
            ['أخف وزناً', 'أرخص سعراً', 'أوفر في الوقود'], ['أقل متعة في القيادة الرياضية'],
            'الأكثر انتشاراً في السيارات اليومية'),
    'rwd': ('دفع خلفي', 'RWD', 'الخلفية تدفع، والأمامية توجّه فقط',
            ['توازن أفضل للسيارة', 'متعة أكبر في القيادة'], ['تماسك أقل على الطرق الزلقة'],
            'تجده في السيارات الرياضية والفاخرة'),
    'awd': ('دفع رباعي', 'AWD · 4x4', 'القوة تتوزع على العجلات الأربع',
            ['أقوى تماسك في الرمل', 'ثبات على الطرق الوعرة'], ['أثقل وزناً', 'أكثر استهلاكاً للوقود'],
            'تجده في سيارات الطرق الوعرة والصحراء'),
}


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)
def ar(d, xy, t, f, col, anchor='rs'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='rtl', language='ar')
def lt(d, xy, t, f, col, anchor='ls'): d.text(xy, t, font=f, fill=col+(255,), anchor=anchor, direction='ltr', language='en')


def shade(cv, bands):
    ys = np.arange(H*K, dtype=np.float32)/K
    for fn, rgb in bands:
        with np.errstate(invalid='ignore'):                    # negative base past the band -> NaN -> 0
            a = np.clip(np.nan_to_num(fn(ys), nan=0.0), 0, 1)
        lay = Image.new('RGBA', (W*K, H*K), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)


def layer():
    lay = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0)); return lay, D(lay)


def chassis(cv, cx, cy, s, kind, glow=True):
    """Top view, nose up. s = body length. Driven wheels orange with arrows, the rest outlined grey."""
    bw, bl = s*0.50, s; ww, wl = s*0.11, s*0.21
    x0, y0 = cx - bw/2, cy - bl/2
    front = cy - bl*0.30; rear = cy + bl*0.30
    driven = {'fwd': (front,), 'rwd': (rear,), 'awd': (front, rear)}[kind]
    if glow:
        g, gd = layer()
        for ay in driven:
            for sx in (-1, 1):
                wx = cx + sx*(bw/2 + ww*0.15)
                gd.ellipse((wx - wl*0.8, ay - wl*0.8, wx + wl*0.8, ay + wl*0.8), fill=O+(120,))
        cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(16*K)))
    lay, d = layer()
    d.rounded_rectangle((x0, y0, x0+bw, y0+bl), radius=bw*0.42, fill=(255, 255, 255, 18), outline=(255, 255, 255, 150), width=3)
    d.rounded_rectangle((x0+bw*0.16, y0+bl*0.30, x0+bw*0.84, y0+bl*0.42), radius=bw*0.08, outline=(255, 255, 255, 90), width=2)  # windscreen
    d.rounded_rectangle((x0+bw*0.20, y0+bl*0.06, x0+bw*0.80, y0+bl*0.20), radius=bw*0.06, fill=(255, 255, 255, 40))          # engine
    shaft = kind in ('rwd', 'awd')
    if shaft:
        d.line([(cx, y0+bl*0.20), (cx, rear)], fill=(O if kind == 'rwd' or kind == 'awd' else GREY)+(255,), width=5)
        d.ellipse((cx-s*0.045, rear-s*0.045, cx+s*0.045, rear+s*0.045), fill=O+(255,))
    for ay in (front, rear):
        on = ay in driven
        d.line([(cx - bw/2, ay), (cx + bw/2, ay)], fill=(O if on else GREY)+(255,), width=5 if on else 3)
        for sx in (-1, 1):
            wx = cx + sx*(bw/2 + ww*0.15)
            box = (wx - ww/2, ay - wl/2, wx + ww/2, ay + wl/2)
            if on: d.rounded_rectangle(box, radius=ww*0.35, fill=O+(255,))
            else: d.rounded_rectangle(box, radius=ww*0.35, fill=(30, 46, 66, 255), outline=GREY+(255,), width=2)
    if kind == 'fwd':                                     # engine sits over the driven axle
        d.ellipse((cx-s*0.045, front-s*0.045, cx+s*0.045, front+s*0.045), fill=O+(255,))
    for ay in driven:                                     # direction of drive, nose is up
        for sx in (-1, 1):
            ax = cx + sx*(bw/2 + ww*0.15 + ww*1.25)
            d.polygon([(ax, ay - wl*0.42), (ax - s*0.04, ay - wl*0.12), (ax + s*0.04, ay - wl*0.12)], fill=O+(255,))
            d.rectangle((ax - s*0.012, ay - wl*0.14, ax + s*0.012, ay + wl*0.30), fill=O+(255,))
    cv.alpha_composite(lay)


def cover(out):
    cv = nc.bg('drive-1-cover.jpg')
    shade(cv, [(lambda y: (1 - y/700)**1.2*0.92, DEEP), (lambda y: (y - 1020)/220*0.92, DEEP)])
    d = D(cv); nc.chrome(cv, d, 1, 6); d = D(cv)
    ar(d, (W/2, 300), 'دفع أمامي، خلفي', F(AR_BLACK, 96), Wh, 'ms')
    ar(d, (W/2, 430), 'أم رباعي؟', F(AR_BLACK, 124), O, 'ms')
    t = 'ما الفرق بينها؟ وأيّها يناسبك؟'; fs = F(AR_BOLD, 34); tw = nc.w_ar(t, fs) + 70
    lay, ld = layer(); ld.rounded_rectangle((W/2 - tw/2, 480, W/2 + tw/2, 540), radius=30, fill=DEEP+(200,)); cv.alpha_composite(lay); d = D(cv)
    d.rounded_rectangle((W/2 - tw/2, 480, W/2 + tw/2, 540), radius=30, outline=O+(255,), width=3)
    ar(d, (W/2, 511), t, fs, Wh, 'mm')
    # three small chassis along the bottom, each with its tag
    for cx, kind, tag in ((W/2 + 320, 'fwd', 'FWD'), (W/2, 'rwd', 'RWD'), (W/2 - 320, 'awd', 'AWD')):
        chassis(cv, cx, 1112, 150, kind, glow=False)
        d = D(cv); lt(d, (cx, 1218), tag, F('Oxanium-800.ttf', 30), Wh, 'ms')
    return cv


def drive(kind, page, bgname):
    title, latin, line, pros, cons, where = TYPES[kind]
    cv = nc.bg(bgname)
    shade(cv, [(lambda y: (1 - y/260)**1.4*0.70, DEEP), (lambda y: ((y - 470)/260)**1.1*0.96, DEEP)])
    d = D(cv); nc.chrome(cv, d, page, 6); d = D(cv)
    # headline block
    ft = F(AR_BLACK, 110); ar(d, (R_, 790), title, ft, Wh)
    tw = nc.w_ar(title, ft)
    d.rectangle((R_ - tw*0.45, 812, R_, 822), fill=O+(255,))
    fl = F('Oxanium-800.ttf', 54); lt(d, (M, 790), latin, fl, O)
    ar(d, (R_, 876), line, F(AR_BOLD, 40), SOFT)
    # body: diagram card on the left, pros and cons on the right
    top = 912; bot = 1196
    lay, ld = layer()
    ld.rounded_rectangle((M, top, M + 300, bot), radius=24, fill=CARD+(225,), outline=(255, 255, 255, 40), width=1)
    cv.alpha_composite(lay)
    chassis(cv, M + 150, (top + bot)/2 + 6, 236, kind)
    d = D(cv); fa = F(AR_BOLD, 22); aw = nc.w_ar('الأمام', fa)
    ar(d, (M + 150 + 10, top + 28), 'الأمام', fa, SOFT, 'mm')
    tx = M + 150 - aw/2 - 6; d.polygon([(tx, top + 18), (tx - 9, top + 34), (tx + 9, top + 34)], fill=SOFT+(255,))
    y = top + 60; fr = F(AR_BOLD, 36); x = R_
    for txt in pros:
        d.ellipse((x - 40, y - 30, x - 4, y + 6), fill=O+(255,))
        nc.icon_check(d, x - 22, y - 12, 30, LOGONAVY)
        ar(d, (x - 58, y), txt, fr, Wh); y += 62
    for txt in cons:
        d.ellipse((x - 40, y - 30, x - 4, y + 6), outline=RED+(255,), width=3)
        nc.icon_x(d, x - 22, y - 12, 26, RED)
        ar(d, (x - 58, y), txt, fr, SOFT); y += 62
    fw = F(AR_BOLD, 28)
    d.ellipse((R_ - 14, 1222, R_, 1236), fill=O+(255,))
    ar(d, (R_ - 26, 1240), where, fw, SOFT)
    return cv


def verdict(out_bg):
    base = nc.bg(out_bg).filter(ImageFilter.GaussianBlur(14*K))
    cv = Image.blend(base, Image.new('RGBA', (W*K, H*K), DEEP+(255,)), 0.72)
    d = D(cv); nc.chrome(cv, d, 5, 6); d = D(cv)
    ar(d, (W/2, 250), 'الخلاصة', F(AR_BOLD, 34), O, 'ms')
    ar(d, (W/2, 360), 'أيّها يناسبك؟', F(AR_BLACK, 100), Wh, 'ms')
    rows = [('fwd', 'للتوفير والاستخدام اليومي', 'دفع أمامي'),
            ('rwd', 'لمتعة القيادة والتوازن', 'دفع خلفي'),
            ('awd', 'للرمل والطرق الوعرة', 'دفع رباعي')]
    top = 430; rh = 236; gap = 24
    for i, (kind, need, ans) in enumerate(rows):
        y0 = top + i*(rh + gap)
        lay, ld = layer()
        ld.rounded_rectangle((M, y0, R_, y0 + rh), radius=26, fill=CARD+(235,), outline=(255, 255, 255, 36), width=1)
        cv.alpha_composite(lay); d = D(cv)
        d.rectangle((R_ - 8, y0 + 30, R_, y0 + rh - 30), fill=O+(255,))
        ar(d, (R_ - 44, y0 + 92), need, F(AR_BOLD, 38), SOFT)
        fa = F(AR_BLACK, 66); ar(d, (R_ - 44, y0 + 180), ans, fa, Wh)
        lt(d, (R_ - 44 - nc.w_ar(ans, fa) - 26, y0 + 176), TYPES[kind][1].split(' ')[0], F('Oxanium-800.ttf', 36), O, 'rs')
        chassis(cv, M + 130, y0 + rh/2, 190, kind)
    return cv


def ask(bgname):
    cv = nc.bg(bgname)
    shade(cv, [(lambda y: (1 - (y - 160)/680)**1.2*0.92, DEEP), (lambda y: (y - 1150)/170*0.88, DEEP)])
    d = D(cv); nc.chrome(cv, d, 6, 6); d = D(cv)
    fe = F(AR_BOLD, 30); ew = nc.w_ar('شاركنا', fe) + 52
    d.rectangle((W/2 - ew/2, 220, W/2 + ew/2, 278), fill=O+(255,))
    ar(d, (W/2, 250), 'شاركنا', fe, LOGONAVY, 'mm')
    ar(d, (W/2, 420), 'وسيارتك أنت؟', F(AR_BLACK, 112), Wh, 'ms')
    ar(d, (W/2, 530), 'دفع أمامي، خلفي أم رباعي؟', F(AR_BLACK, 68), O, 'ms')
    ar(d, (W/2, 610), 'اكتبها في التعليقات', F(AR_BOLD, 40), SOFT, 'ms')
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(None), drive('fwd', 2, 'drive-2-fwd.jpg'), drive('rwd', 3, 'drive-3-rwd.jpg'),
              drive('awd', 4, 'drive-4-awd.jpg'), verdict('drive-1-cover.jpg'), ask('drive-6-ask.jpg')]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-drivetrain-{i}.png'); cv.convert('RGB').save(p); print(p, cv.size)
