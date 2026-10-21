"""«اعتنِ بسيارتك»: what the transmission fluid colour means — two dark slides, 2160x2700.

usage: python3 atf_colors.py <brand-kit dir> <out dir>
  1) cover: dipstick scene (Canva, atf-dipstick.jpg) + headline
  2) guide: four glossy fluid drops drawn in the real colours, meaning and a status chip each
Reuses the chrome of parts_guide.py so the section stays one system.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts_guide as pg
from parts_guide import W, H, M, R_, S, DEEP, CARD, O, Wh, SOFT, F, AR_BLACK, AR_BOLD, w_ar, shade, chrome
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ROWS = [  # colour, name, meaning, status, status colour
    ((214, 32, 58), 'أحمر صافٍ / وردي', 'زيت جديد يعمل بكفاءة تامة', 'ممتاز', (46, 160, 90)),
    ((150, 52, 40), 'أحمر داكن / بني فاتح', 'زيت مستهلك جزئياً، اقترب موعد تغييره', 'طبيعي', (222, 168, 40)),
    ((48, 30, 22), 'بني غامق / أسود', 'زيت محترق، غيّره فوراً وافحص القير', 'خطر', (232, 110, 40)),
    ((236, 176, 182), 'وردي حليبي', 'تسرّب سائل التبريد إلى الزيت، أوقف القيادة فوراً', 'خطر جداً', (214, 40, 40)),
]


def drop(size, col):
    """A glossy liquid drop: teardrop body, inner shading, specular highlight."""
    s = size*4; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, r = s/2, s*0.33; cy = s*0.62
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col+(255,))
    d.polygon([(cx, s*0.06), (cx - r*0.93, cy - r*0.36), (cx + r*0.93, cy - r*0.36)], fill=col+(255,))
    a = np.array(im).astype(np.float32); ys, xs = np.mgrid[0:s, 0:s].astype(np.float32)
    shadeK = np.clip(((xs - cx*1.25)**2 + (ys - cy*1.15)**2)**0.5/(r*1.6), 0, 1)       # darker toward lower right
    a[..., :3] *= (1.0 - 0.35*(1 - shadeK))[..., None]*0 + (0.72 + 0.38*shadeK)[..., None]
    a[..., :3] = np.clip(a[..., :3], 0, 255)
    im = Image.fromarray(a.astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(im)
    hl = Image.new('RGBA', (s, s), (0, 0, 0, 0)); hd = ImageDraw.Draw(hl)
    hd.ellipse((cx - r*0.62, cy - r*0.70, cx - r*0.18, cy - r*0.12), fill=(255, 255, 255, 170))
    hd.ellipse((cx + r*0.30, cy + r*0.30, cx + r*0.52, cy + r*0.52), fill=(255, 255, 255, 90))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(s*0.02)))
    return im.resize((size, size), Image.LANCZOS)


def cover(out):
    cv = Image.open(os.path.join(HERE, 'atf-dipstick.jpg')).convert('RGBA').resize((W, H), Image.LANCZOS)
    shade(cv, [(lambda ys: np.clip(1 - ys/S(560), 0, 1)**1.2*0.85, DEEP), (lambda ys: np.clip((ys - S(1080))/S(260), 0, 1)*0.92, DEEP)])
    d = ImageDraw.Draw(cv); cx = W/2
    d.text((cx, S(262)), 'ماذا يعني لون', font=F(AR_BLACK, S(84)), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((cx, S(388)), 'زيت القير؟', font=F(AR_BLACK, S(118)), fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    t = 'افحصه واعرف حالة ناقل الحركة'; fs = F(AR_BOLD, S(30)); tw = w_ar(t, fs) + S(60)
    d.rounded_rectangle((cx - tw/2, S(446), cx + tw/2, S(502)), radius=S(28), outline=O+(255,), width=S(3))
    d.text((cx, S(475)), t, font=fs, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    chrome(cv, 1, 2)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def guide(out):
    base = Image.open(os.path.join(HERE, 'atf-dipstick.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
    cv = Image.blend(base.filter(ImageFilter.GaussianBlur(S(18))), Image.new('RGB', (W, H), DEEP), 0.80).convert('RGBA')
    d = ImageDraw.Draw(cv)
    t1, t2 = 'ماذا يعني لون', 'زيت القير؟'; fh = F(AR_BLACK, S(54))
    d.text((R_, S(220)), t1, font=fh, fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
    d.text((R_ - w_ar(t1, fh) - S(18), S(220)), t2, font=fh, fill=O+(255,), anchor='rs', direction='rtl', language='ar')
    top = S(262); rh = S(196); gap = S(18)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i in range(4):
        y0 = top + i*(rh + gap)
        ld.rounded_rectangle((M, y0, R_, y0 + rh), radius=S(24), fill=CARD+(235,), outline=(255, 255, 255, 34), width=S(1))
    cv.alpha_composite(lay); d = ImageDraw.Draw(cv)
    for i, (col, name, meaning, status, scol) in enumerate(ROWS):
        y0 = top + i*(rh + gap)
        # drop on the right, sitting in a soft glow of its own colour
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        gcol = col if sum(col) > 200 else (150, 140, 135)                # a dark drop needs a light halo to read
        ImageDraw.Draw(glow).ellipse((R_ - S(170), y0 + S(30), R_ - S(30), y0 + S(170)), fill=gcol+(90,))
        cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S(18))))
        dr = drop(S(150), col); cv.alpha_composite(dr, (R_ - S(176), y0 + S(18)))
        d = ImageDraw.Draw(cv)
        tx = R_ - S(196)
        d.text((tx, y0 + S(66)), f'0{i+1}', font=F('Oxanium-800.ttf', S(26)), fill=O+(255,), anchor='rs')
        d.text((tx - S(52), y0 + S(68)), name, font=F(AR_BLACK, S(40)), fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
        fm = F(AR_BOLD, S(28))
        lines, sp = pg_wrap(meaning, fm, tx - M - S(40))
        for k, ln in enumerate(lines):
            d.text((tx, y0 + S(116) + k*S(40)), ln, font=fm, fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')
        # status chip, bottom-left of the card
        fs = F(AR_BOLD, S(26)); cw_ = w_ar(status, fs) + S(40)
        d.rounded_rectangle((M + S(28), y0 + S(26), M + S(28) + cw_, y0 + S(74)), radius=S(24), fill=scol+(255,))
        d.text((M + S(28) + cw_/2, y0 + S(51)), status, font=fs, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    ny = top + 4*rh + 3*gap + S(50)
    d.text((W/2, ny), 'سيارات كثيرة بلا عصا قياس للقير، افحصه عند فني مختص', font=F(AR_BOLD, S(26)), fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')
    chrome(cv, 2, 2)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def pg_wrap(text, f, maxw):
    words = text.split(' '); lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if cur and w_ar(t, f) > maxw: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines, None


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    cover(os.path.join(sys.argv[2], 'atf-colors-1.png'))
    guide(os.path.join(sys.argv[2], 'atf-colors-2.png'))
