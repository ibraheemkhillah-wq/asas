"""CALL & RENT «اعتنِ بسيارتك» (maintenance) single-image posts.

usage: python3 care_posts.py <brand-kit dir> <out dir>
Reuses the news template's chrome (logo, teal 'care' badge, footer) so every section stays one system.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.join(HERE, '..', 'news'))
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT, w_ar
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.SECTION = 'care'; nc.THEME = 'dark'
TEAL = nc.CARE_TEAL
WRONG = (214, 64, 64)


def shade(cv, bands):
    ys = np.arange(H, dtype=np.float32)
    for f in bands:
        a = f(ys)
        lay = Image.new('RGBA', (W, H), DEEP+(0,))
        lay.putalpha(Image.fromarray((np.repeat(np.clip(a, 0, 1)[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)


def centered_lines(d, runs, font, cx, y, maxw, lh, colour=Wh):
    """Wrap Arabic text and centre each line under cx."""
    lines, sp = nc.wrap(nc.tokens(runs), font, maxw)
    for ln in lines:
        lw = sum(ww for _, _, ww in ln) + sp*(len(ln)-1)
        nc.draw_lines(d, [ln], sp, font, cx + lw/2, y, lh)
        y += lh
    return y


def tip_bar(cv, d, y, text, accent, size=36):
    f = F(AR_BLACK, size); pad = 30
    lines, sp = nc.wrap(nc.tokens(text), f, R_ - M - 2*pad - 10)
    h = len(lines)*62 + 2*pad - 6
    d.rectangle((M, y, R_, y+h), fill=LOGONAVY+(255,))
    d.rectangle((R_-10, y, R_, y+h), fill=accent+(255,))
    nc.draw_lines(d, lines, sp, f, R_-pad-10, y+pad+round(size*1.1), 62)
    return y + h


def oil(out):
    cv = nc.bg('../care/care-oil.jpg')
    shade(cv, [lambda ys: np.clip(1-ys/760, 0, 1)**1.2*0.55, lambda ys: (ys-1050)/220*0.9])
    d = ImageDraw.Draw(cv)
    nc.chrome(cv, d, 1, 1)
    d.text((W/2, 236), 'ماذا يعني الرقم على عبوة الزيت؟', font=F(AR_BLACK, 50), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    code = F(LT_TEXT, 210); txt = '5W-30'
    tw = code.getlength(txt); x0 = W/2 - tw/2; base = 448
    d.text((x0, base), txt, font=code, fill=O+(255,), anchor='ls')
    parts = [(code.getlength('5')/2, '5'), (code.getlength('5') + code.getlength('W')/2, 'W'),
             (code.getlength('5W-') + code.getlength('30')/2, '30')]
    cards = [
        ('5', [('رقم البرودة: كلما ', Wh), ('قلّ', O), ('كان الزيت أسرع تدفّقاً عند التشغيل البارد', Wh)]),
        ('W', [('Winter', O), ('أي الشتاء، فالزيت مناسب للأجواء الباردة', Wh)]),
        ('30', [('اللزوجة عند حرارة التشغيل: كلما ', Wh), ('زاد', O), ('كان الزيت أسمك وأقوى تحمّلاً للحرارة', Wh)]),
    ]
    gap = 22; cw = (R_ - M - 2*gap)/3; top = 520; ch = 350
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i in range(3):
        cx0 = M + i*(cw+gap)
        ld.rectangle((cx0, top, cx0+cw, top+ch), fill=DEEP+(222,), outline=(255, 255, 255, 40), width=1)
    cv.alpha_composite(lay); d = ImageDraw.Draw(cv)
    for i, ((gx, key), (_, body)) in enumerate(zip(parts, cards)):
        cx0 = M + i*(cw+gap); ccx = cx0 + cw/2; gx = x0 + gx
        # elbow connector: glyph -> card
        y1 = base + 18; y2 = top - 26
        d.line([(gx, y1), (gx, (y1+y2)/2), (ccx, (y1+y2)/2), (ccx, top)], fill=O+(255,), width=3, joint='curve')
        d.ellipse((gx-6, y1-6, gx+6, y1+6), fill=O+(255,))
        d.rectangle((cx0, top, cx0+cw, top+6), fill=O+(255,))
        d.text((ccx, top+70), key, font=F(LT_TEXT, 50), fill=O+(255,), anchor='ms')
        centered_lines(d, body, F(CT_FONT, 30), ccx, top+128, cw-30, 46)
    tip_bar(cv, d, 1104, [('لا تعتمد على التخمين:', O), ('استخدم دائماً الزيت الموصى به في دليل سيارتك', Wh)], TEAL)
    cv.convert('RGB').save(out, quality=95); print(out)


def panel(name, box, good):
    x0, y0, x1, y1 = box
    im = Image.open(os.path.join(HERE, name)).convert('RGB')
    s = max((x1-x0)/im.width, (y1-y0)/im.height)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l = (im.width-(x1-x0))//2; t = (im.height-(y1-y0))//2
    return im.crop((l, t, l+x1-x0, t+y1-y0))


def tires(out):
    back = Image.open(os.path.join(HERE, 'care-tires-wrong.jpg')).convert('RGB').resize((W, round(W*1200/900)))
    back = back.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(28))
    cv = Image.blend(back, Image.new('RGB', (W, H), DEEP), 0.72).convert('RGBA')
    d = ImageDraw.Draw(cv)
    nc.chrome(cv, d, 1, 1)
    d.text((W/2, 222), 'كيف تُخزَّن الإطارات', font=F(AR_BLACK, 62), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, 314), 'بالطريقة الصحيحة؟', font=F(AR_BLACK, 72), fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    gap = 24; pw = (R_ - M - gap)//2; top = 362; ph = 490
    specs = [  # right panel first (read RTL): the mistake, then the fix
        (R_-pw, 'care-tires-wrong.jpg', False, 'مكدّسة فوق بعضها', WRONG),
        (M, 'care-tires-right.jpg', True, 'واقفة جنباً إلى جنب', TEAL),
    ]
    for x0, name, good, label, col in specs:
        p = panel(name, (x0, top, x0+pw, top+ph), good)
        cv.paste(p, (x0, top))
        d.rectangle((x0, top, x0+pw, top+ph), outline=col+(255,), width=5)
        # verdict disc
        r = 40; cx = x0+pw-24-r; cy = top+24+r
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col+(255,), outline=Wh+(255,), width=3)
        (nc.icon_check if good else nc.icon_x)(d, cx, cy, 64, Wh)
        # label strip
        fl = F(AR_BLACK, 34); lh = 74
        d.rectangle((x0, top+ph-lh, x0+pw, top+ph), fill=col+(255,))
        d.text((x0+pw/2, top+ph-lh/2+4), label, font=fl, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    # why
    y = top + ph + 30
    fb = F(CT_FONT, 33)
    lines, sp = nc.wrap(nc.tokens([('تكديس الإطارات', Wh), ('بارتفاعات كبيرة', O),
                                   ('يضغط على الإطارات السفلية ويشوّه جدرانها، فيقصر عمرها قبل أن تُركَّب على سيارتك.', Wh)]),
                        fb, R_ - M - 20)
    nc.draw_lines(d, lines, sp, fb, R_-10, y+38, 54)
    y += len(lines)*54 + 26
    tip_bar(cv, d, y, [('نصيحة:', O), ('قبل الشراء تحقّق من تاريخ تصنيع الإطار عبر رمز', Wh), ('DOT', O),
                       ('المطبوع على جانبه', Wh)], TEAL, size=33)
    cv.convert('RGB').save(out, quality=95); print(out)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    oil(os.path.join(sys.argv[2], 'care-oil-5w30.png'))
    tires(os.path.join(sys.argv[2], 'care-tire-storage.png'))
