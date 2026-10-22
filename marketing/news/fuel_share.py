"""«أخبار السيارات»: gasoline-only cars fall below half of global new-car sales (H1 2026).
Dark, data-led carousel, three slides at 2160x2700.

usage: python3 fuel_share.py <brand-kit dir> <out dir>
  1) cover: Canva pump-vs-charger scene (fuel-share-cover.jpg), giant 49% with a half-ring gauge
  2) data: donut of the H1 2026 mix + the 73% -> 49% slide since 2021
  3) ask: open question
Source on every slide (Nikkei Asia, Mobility Global data).
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import (ORANGE as O, LOGONAVY as N, WHITE as Wh, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_BOLD, LT_TEXT,
                   LOGO_WHITE, load_icons, w_ar, w_lt)

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
DEEP = (8, 24, 41); CARD = (14, 36, 58)
MINT = (96, 196, 160); SKY = (92, 166, 232); GREY = (120, 136, 156)
SOURCE = 'المصدر: نيكاي آسيا · بيانات Mobility Global'
MIX = [('بنزين فقط', 49, O), ('هايبرد', 18, MINT), ('كهربائية بالكامل', 17, SKY), ('أخرى*', 16, GREY)]
def S(v): return round(v*K)
def ar(d, xy, t, f, fill, anchor='rs'): d.text(xy, t, font=f, fill=fill, anchor=anchor, direction='rtl', language='ar')


def field():
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    KEY = np.array((40, 92, 136), np.float32); DK = np.array(DEEP, np.float32)
    r = np.sqrt(((xs - W/2)/1.3)**2 + ((ys - H*0.48))**2)/(W*0.9)
    bg = DK + (KEY - DK)*np.exp(-0.5*(r/0.42)**2)[..., None]
    bg += np.random.default_rng(7).normal(0, 1.6, (H, W, 1))
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA')


def chrome(cv, n, total):
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_WHITE).convert('RGBA'); lw = S(270)
    cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'أخبار السيارات'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=O+(255,))
    d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=N+(255,))
    ar(d, (bx + bw/2, by + bh/2 + S(2)), label, fb, N+(255,), 'mm')
    ar(d, (R_, S(1250)), SOURCE, F(AR_BOLD, S(24)), SOFT+(255,))
    ic = load_icons(S(34)); fc = F(CT_FONT, S(29)); y = S(1292); x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, y - S(17))); x += S(44)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=Wh+(255,), anchor='lm')
    fp = F(LT_TEXT, S(24)); t = f'{n:02d} / {total:02d}'
    d.text((R_, y + S(2)), t, font=fp, fill=SOFT+(255,), anchor='rm')
    if n < total:
        ax = R_ - w_lt(t, fp) - S(22)
        d.polygon([(ax, y - S(9)), (ax - S(14), y + S(1)), (ax, y + S(11))], fill=O+(255,))


def ring(d, cx, cy, r, w, start, end, col):
    d.arc((cx - r, cy - r, cx + r, cy + r), start, end, fill=col, width=w)


def cover(out):
    cv = Image.open(os.path.join(HERE, 'fuel-share-cover.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)
    ys = np.arange(H, dtype=np.float32)
    for a in (np.clip(1 - ys/S(760), 0, 1)**1.1*0.86, np.clip((ys - S(1120))/S(200), 0, 1)*0.9):
        lay = Image.new('RGBA', (W, H), DEEP+(0,)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv); cx = W/2
    ar(d, (cx, S(222)), 'لأول مرة..', F(AR_BLACK, S(54)), O+(255,), 'ms')
    ar(d, (cx, S(306)), 'سيارات البنزين أقل من', F(AR_BLACK, S(66)), Wh+(255,), 'ms')
    ar(d, (cx, S(386)), 'نصف المبيعات عالمياً', F(AR_BLACK, S(66)), Wh+(255,), 'ms')
    # half-ring gauge: 49 of 100, with a white tick at the 50% mark
    gcy = S(760); gr = S(250); gw = S(36)
    tr = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ring(ImageDraw.Draw(tr), cx, gcy, gr, gw, 180, 360, (255, 255, 255, 60))
    cv.alpha_composite(tr); d = ImageDraw.Draw(cv)
    ring(d, cx, gcy, gr, gw, 180, 180 + 180*0.49, O+(255,))
    tx = cx; d.line([(tx, gcy - gr - S(30)), (tx, gcy - gr + S(30))], fill=Wh+(255,), width=S(4))
    d.text((tx + S(16), gcy - gr - S(18)), '50%', font=F(LT_TEXT, S(24)), fill=SOFT+(255,), anchor='ls')
    d.text((cx, gcy - S(10)), '49%', font=F(LT_BOLD, S(150)), fill=Wh+(255,), anchor='ms')
    ar(d, (cx, gcy + S(52)), 'حصة سيارات البنزين فقط · النصف الأول 2026', F(AR_BOLD, S(28)), SOFT+(255,), 'ms')
    chrome(cv, 1, 3)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def data(out):
    cv = field(); d = ImageDraw.Draw(cv)
    ar(d, (R_, S(214)), 'مبيعات السيارات الجديدة عالمياً', F(AR_BLACK, S(48)), Wh+(255,))
    ar(d, (R_, S(262)), 'النصف الأول من 2026', F(AR_BOLD, S(28)), O+(255,))
    # donut on the left, legend on the right
    cx, cy, r, w = M + S(250), S(560), S(210), S(70)
    a0 = -90
    for name, pct, col in MIX:
        a1 = a0 + 360*pct/100
        d.arc((cx - r, cy - r, cx + r, cy + r), a0 + 0.8, a1 - 0.8, fill=col+(255,), width=w); a0 = a1
    d.text((cx, cy + S(14)), '84%', font=F(LT_BOLD, S(64)), fill=Wh+(255,), anchor='ms')
    ar(d, (cx, cy + S(56)), 'ما زالت بمحرّك', F(AR_BOLD, S(22)), SOFT+(255,), 'ms')
    ly = S(400)
    for name, pct, col in MIX:
        d.rounded_rectangle((R_ - S(28), ly - S(30), R_, ly - S(2)), radius=S(6), fill=col+(255,))
        ar(d, (R_ - S(44), ly), name, F(AR_BOLD, S(30)), Wh+(255,))
        d.text((S(590), ly), f'{pct}%', font=F(LT_BOLD, S(46)), fill=col+(255,), anchor='ls')
        ly += S(86)
    ar(d, (R_, S(770)), '* تشمل الديزل والهايبرد القابل للشحن وفئات أخرى', F(AR_BOLD, S(22)), SOFT+(255,))
    # the slide since 2021: two bars, with an arrow between
    top = S(830); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle((M, top, R_, top + S(330)), radius=S(26), fill=CARD+(230,), outline=(255, 255, 255, 34), width=S(1))
    cv.alpha_composite(lay); d = ImageDraw.Draw(cv)
    ar(d, (R_ - S(30), top + S(62)), 'حصة البنزين فقط تراجعت', F(AR_BLACK, S(38)), Wh+(255,))
    bx0, bx1 = M + S(40), R_ - S(40); full = bx1 - bx0
    for i, (yr, v, col) in enumerate((('2021', 73, GREY), ('2026', 49, O))):
        y = top + S(120) + i*S(96)
        tr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(tr).rounded_rectangle((bx0, y, bx1, y + S(52)), radius=S(26), fill=(255, 255, 255, 30))
        cv.alpha_composite(tr); d = ImageDraw.Draw(cv)
        d.rounded_rectangle((bx1 - full*v/100, y, bx1, y + S(52)), radius=S(26), fill=col+(255,))
        d.text((bx1 - S(24), y + S(27)), yr, font=F(LT_BOLD, S(30)), fill=DEEP+(255,) if col == O else Wh+(255,), anchor='rm')
        d.text((bx1 - full*v/100 - S(20), y + S(27)), f'{v}%', font=F(LT_BOLD, S(40)), fill=col+(255,), anchor='rm')
    ar(d, (R_ - S(30), top + S(312)), 'تراجع بـ 24 نقطة خلال خمس سنوات', F(AR_BOLD, S(26)), SOFT+(255,))
    chrome(cv, 2, 3)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def ask(out):
    cv = field(); d = ImageDraw.Draw(cv); cx = W/2
    fe = F(AR_BOLD, S(30)); ew = w_ar('شاركنا رأيك', fe) + S(48)
    d.rectangle((cx - ew/2, S(330), cx + ew/2, S(388)), fill=O+(255,))
    ar(d, (cx, S(361)), 'شاركنا رأيك', fe, N+(255,), 'mm')
    ar(d, (cx, S(500)), 'في السنوات القادمة..', F(AR_BLACK, S(60)), Wh+(255,), 'ms')
    ar(d, (cx, S(600)), 'من سيأخذ حصة أكبر', F(AR_BLACK, S(70)), Wh+(255,), 'ms')
    ar(d, (cx, S(700)), 'من البنزين؟', F(AR_BLACK, S(96)), O+(255,), 'ms')
    for i, (lab, col) in enumerate((('الهايبرد', MINT), ('الكهرباء', SKY))):
        x0 = cx + (S(30) if i == 0 else -S(30) - S(380)); y0 = S(820)
        d.rounded_rectangle((x0, y0, x0 + S(380), y0 + S(130)), radius=S(65), fill=CARD+(255,), outline=col+(255,), width=S(4))
        ar(d, (x0 + S(190), y0 + S(68)), lab, F(AR_BLACK, S(50)), col+(255,), 'mm')
    ar(d, (cx, S(1060)), 'اكتب اختيارك في التعليقات', F(AR_BOLD, S(30)), SOFT+(255,), 'ms')
    chrome(cv, 3, 3)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    cover(os.path.join(sys.argv[2], 'fuel-share-1.png'))
    data(os.path.join(sys.argv[2], 'fuel-share-2.png'))
    ask(os.path.join(sys.argv[2], 'fuel-share-3.png'))
