"""«اعتنِ بسيارتك»: when to replace car parts — two slides, dark theme, rendered at 2160x2700.

usage: python3 parts_guide.py <brand-kit dir> <out dir>
  1) cover: workshop scene (Canva, parts-workshop.jpg) + headline
  2) guide: six cards (hand-drawn icons, part name, interval) + 'your manual comes first' note
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE as O, LOGONAVY, WHITE as Wh, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT, LOGO_WHITE, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K
M = 64*K; R_ = W - M
DEEP = (8, 24, 41); TEAL = (22, 138, 128); CARD = (14, 36, 58)


def S(v): return round(v*K)


def shade(cv, bands):
    ys = np.arange(H, dtype=np.float32)
    for f, col in bands:
        a = np.nan_to_num(np.clip(f(ys), 0, 1))
        lay = Image.new('RGBA', (W, H), col+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)


def chrome(cv, page, total):
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_WHITE).convert('RGBA'); lw = S(270)
    cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'اعتنِ بسيارتك'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=TEAL+(255,))
    d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=O+(255,))
    d.text((bx+bw/2, by+bh/2+S(2)), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    ic = load_icons(S(34)); fc = F(CT_FONT, S(29)); y = S(1292); x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, y - S(17))); x += S(44)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=Wh+(255,), anchor='lm')
    fp = F(LT_TEXT, S(24)); t = f'{page:02d} / {total:02d}'
    d.text((R_, y + S(2)), t, font=fp, fill=SOFT+(255,), anchor='rm')
    if page < total:
        ax = R_ - w_lt(t, fp) - S(22)
        d.polygon([(ax, y - S(9)), (ax - S(14), y + S(1)), (ax, y + S(11))], fill=O+(255,))


# ---- icons: drawn in a 100x100 box, scaled by s ------------------------------------
def ic_oil(d, cx, cy, s, c):
    p = lambda x, y: (cx + (x-50)*s/100, cy + (y-50)*s/100)
    d.polygon([p(22, 40), p(58, 40), p(70, 52), p(84, 46), p(88, 50), p(72, 66), p(72, 82), p(22, 82)], fill=c)
    d.rectangle([p(34, 30), p(46, 40)], fill=c)
    d.ellipse([p(80, 70), p(90, 84)], fill=c); d.polygon([p(85, 58), p(80, 72), p(90, 72)], fill=c)


def ic_filter(d, cx, cy, s, c):
    p = lambda x, y: (cx + (x-50)*s/100, cy + (y-50)*s/100)
    d.rounded_rectangle([p(18, 22), p(82, 78)], radius=s*0.06, outline=c, width=max(2, round(s*0.07)))
    for x in range(30, 74, 9):
        d.line([p(x, 30), p(x+4, 50), p(x, 70)], fill=c, width=max(2, round(s*0.05)), joint='curve')


def ic_plug(d, cx, cy, s, c):
    p = lambda x, y: (cx + (x-50)*s/100, cy + (y-50)*s/100)
    d.rectangle([p(44, 12), p(56, 30)], fill=c)
    d.polygon([p(36, 30), p(64, 30), p(64, 46), p(36, 46)], fill=c)
    d.rectangle([p(40, 48), p(60, 66)], fill=c)
    d.rectangle([p(47, 66), p(53, 80)], fill=c); d.line([p(53, 82), p(62, 82), p(62, 88)], fill=c, width=max(2, round(s*0.05)))
    d.polygon([p(70, 20), p(80, 34), p(73, 34), p(80, 46), p(66, 30), p(73, 30)], fill=c)


def ic_brake(d, cx, cy, s, c):
    r = s*0.36; w = max(2, round(s*0.08))
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=w)
    d.ellipse([cx-r*0.32, cy-r*0.32, cx+r*0.32, cy+r*0.32], fill=c)
    for a in range(0, 360, 60):
        t = np.deg2rad(a); x, y = cx + np.cos(t)*r*0.62, cy + np.sin(t)*r*0.62
        d.ellipse([x-s*0.04, y-s*0.04, x+s*0.04, y+s*0.04], fill=c)
    d.pieslice([cx-r*1.25, cy-r*1.25, cx+r*1.25, cy+r*1.25], 200, 250, fill=c)


def ic_tire(d, cx, cy, s, c):
    r = s*0.40
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=max(3, round(s*0.13)))
    d.ellipse([cx-r*0.42, cy-r*0.42, cx+r*0.42, cy+r*0.42], outline=c, width=max(2, round(s*0.06)))
    for a in range(0, 360, 72):
        t = np.deg2rad(a)
        d.line([(cx + np.cos(t)*r*0.42, cy + np.sin(t)*r*0.42), (cx + np.cos(t)*r*0.72, cy + np.sin(t)*r*0.72)], fill=c, width=max(2, round(s*0.05)))


def ic_battery(d, cx, cy, s, c):
    p = lambda x, y: (cx + (x-50)*s/100, cy + (y-50)*s/100)
    d.rounded_rectangle([p(16, 32), p(84, 80)], radius=s*0.05, outline=c, width=max(2, round(s*0.07)))
    d.rectangle([p(26, 24), p(36, 32)], fill=c); d.rectangle([p(64, 24), p(74, 32)], fill=c)
    w = max(2, round(s*0.06))
    d.line([p(26, 54), p(38, 54)], fill=c, width=w); d.line([p(32, 48), p(32, 60)], fill=c, width=w)
    d.line([p(62, 54), p(74, 54)], fill=c, width=w)


PARTS = [  # right-to-left reading order: (icon, name, interval, note)
    (ic_oil, 'زيت المحرك', '5,000 – 10,000 كم', 'حسب نوع الزيت'),
    (ic_filter, 'فلتر الهواء', '15,000 – 20,000 كم', 'أقل في الأجواء المغبرة'),
    (ic_brake, 'فحمات الفرامل', '30,000 – 60,000 كم', 'حسب أسلوب القيادة'),
    (ic_tire, 'الإطارات', '40,000 – 60,000 كم', 'أو كل 5 سنوات'),
    (ic_plug, 'البواجي', '40,000 – 100,000 كم', 'حسب نوعها'),
    (ic_battery, 'البطارية', 'كل 3 – 5 سنوات', 'حسب الاستخدام والحرارة'),
]


def cover(out):
    cv = Image.open(os.path.join(HERE, 'parts-workshop.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)
    shade(cv, [(lambda ys: np.clip(1 - ys/S(520), 0, 1)**1.2*0.85, DEEP), (lambda ys: np.clip((ys - S(1060))/S(260), 0, 1)*0.92, DEEP)])
    d = ImageDraw.Draw(cv); cx = W/2
    d.text((cx, S(250)), 'متى تعمل', font=F(AR_BLACK, S(88)), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    t2 = 'صيانة دورية لسيارتك؟'; s2 = S(100)
    while w_ar(t2, F(AR_BLACK, s2)) > W - 2*M: s2 -= S(2)
    d.text((cx, S(372)), t2, font=F(AR_BLACK, s2), fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    # odometer-style subtitle chip
    t = 'دليل سريع بالكيلومترات'; fs = F(AR_BOLD, S(32)); tw = w_ar(t, fs) + S(60)
    d.rounded_rectangle((cx - tw/2, S(408), cx + tw/2, S(464)), radius=S(30), outline=O+(255,), width=S(3))
    d.text((cx, S(437)), t, font=fs, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    chrome(cv, 1, 2)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def guide(out):
    base = Image.open(os.path.join(HERE, 'parts-workshop.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
    cv = Image.blend(base.filter(ImageFilter.GaussianBlur(S(18))), Image.new('RGB', (W, H), DEEP), 0.78).convert('RGBA')
    d = ImageDraw.Draw(cv); cx = W/2
    t1, t2 = 'متى تعمل', 'صيانة دورية لسيارتك؟'; hs = S(54)
    while w_ar(t1, F(AR_BLACK, hs)) + S(18) + w_ar(t2, F(AR_BLACK, hs)) > R_ - M: hs -= S(2)
    fh = F(AR_BLACK, hs)
    d.text((R_, S(220)), t1, font=fh, fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
    d.text((R_ - w_ar(t1, fh) - S(18), S(220)), t2, font=fh, fill=O+(255,), anchor='rs', direction='rtl', language='ar')
    gap = S(22); cw = (R_ - M - gap)/2; ch = S(270); top = S(270)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    cells = []
    for i in range(6):
        col, row = i % 2, i // 2
        x1 = R_ - col*(cw + gap); x0 = x1 - cw; y0 = top + row*(ch + gap)
        ld.rounded_rectangle((x0, y0, x1, y0 + ch), radius=S(22), fill=CARD+(235,), outline=(255, 255, 255, 34), width=S(1))
        cells.append((x0, y0, x1))
    cv.alpha_composite(lay); d = ImageDraw.Draw(cv)
    for (x0, y0, x1), (icon, name, interval, note) in zip(cells, PARTS):
        ccx = (x0 + x1)/2
        r = S(46); icy = y0 + S(70)
        d.ellipse((ccx - r, icy - r, ccx + r, icy + r), fill=(28, 52, 78, 255), outline=O+(255,), width=S(3))
        icon(d, ccx, icy, S(76), O+(255,))
        d.text((ccx, y0 + S(160)), name, font=F(AR_BLACK, S(36)), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
        fi = F(AR_BOLD, S(32))
        d.text((ccx, y0 + S(212)), interval, font=fi, fill=O+(255,), anchor='ms', direction='rtl', language='ar')
        d.text((ccx, y0 + S(250)), note, font=F(AR_BOLD, S(22)), fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')
    ny = top + 3*ch + 2*gap + S(52)
    d.text((cx, ny), 'أرقام تقريبية، والمرجع الأول دائماً دليل سيارتك', font=F(AR_BOLD, S(26)), fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')
    chrome(cv, 2, 2)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    cover(os.path.join(sys.argv[2], 'parts-guide-1.png'))
    guide(os.path.join(sys.argv[2], 'parts-guide-2.png'))
