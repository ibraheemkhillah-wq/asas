"""«عندك فكرة»: why the Renault logo is a diamond — seven LIGHT slides, 2160x2700.

usage: python3 idea_renault.py <brand-kit dir> <out dir>
Photos: Higgsfield GPT Image (at the user's request), renault-*.jpg; the 2021 logo is a real photo the user supplied. Each logo is the subject, so the text sits
at the top on a white fade and the photo is lowered just enough that the logo starts below the text; the strip
this frees at the top is the photo's own calm top rows, blurred. Layout in 1080 units; every line is placed
from its measured ink box with at least 24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, LOGONAVY as N, AR_BLACK, AR_BOLD
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'light'; nc.SECTION = 'idea'
K = nc.K; TOTAL = 7; SOFTN = (84, 102, 124)
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))
# logo box (x0, y0, x1, y1) in units of the photo scaled to 1080 wide
LOGO = {'renault-1-cover.jpg': (290, 610, 760, 1290), 'renault-2-1923.jpg': (168, 560, 920, 1345),
        'renault-3-1925.jpg': (300, 600, 780, 1325), 'renault-4-1972.jpg': (280, 600, 920, 1300),
        'renault-6-2021-real.jpg': (371, 199, 701, 634)}
BOTTOM = 1200                                   # logos end here, clear of the footer fade


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)


def ink(t, f):
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', direction='rtl', language='ar'); return -b[1]/K, b[3]/K


def scene(name, text_end):
    """Scale the photo (never up) so its whole logo fits between the text and BOTTOM, centred; the canvas
    around it is the same photo enlarged and blurred, so the picture continues without a frame."""
    src = Image.open(os.path.join(HERE, name)).convert('RGB')
    ph = 1080*src.height/src.width                                   # photo height in units at 1080 wide
    lx0, ly0, lx1, ly1 = LOGO[name]; top = text_end + 60
    s = min(1.0, (BOTTOM - top)/(ly1 - ly0))
    oy = top + ((BOTTOM - top) - s*(ly1 - ly0))/2 - s*ly0             # photo origin so the logo is centred in the box
    ox = 540 - s*(lx0 + lx1)/2
    sc = max(W/1080, H/ph)*1.15
    bgim = src.resize((round(1080*sc*K), round(ph*sc*K)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40*K))
    cv = bgim.crop(((bgim.width - W*K)//2, (bgim.height - H*K)//2, (bgim.width - W*K)//2 + W*K, (bgim.height - H*K)//2 + H*K)).convert('RGBA')
    pw, phh = round(1080*s*K), round(ph*s*K)
    im = src.resize((pw, phh), Image.LANCZOS).convert('RGBA')
    f = 70*K*s                                                        # feather the photo's edges into the blur
    yy, xx = np.mgrid[0:phh, 0:pw].astype(np.float32)
    m = np.minimum.reduce([xx/f, (pw - 1 - xx)/f, yy/f, (phh - 1 - yy)/f]).clip(0, 1)
    im.putalpha(Image.fromarray((m*255).astype(np.uint8)))
    cv.alpha_composite(im, (round(ox*K), round(oy*K)))
    ys = np.arange(H*K, dtype=np.float32)/K                           # white fade behind the text, and the footer
    a = np.maximum(np.clip((text_end + 60 - ys)/90, 0, 1)**0.8*0.9, np.clip((ys - 1236)/34, 0, 1)*0.94)
    lay = Image.new('RGBA', (W*K, H*K), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)
    return cv, f'scale {s:.2f}, logo {round(top + ((BOTTOM - top) - s*(ly1 - ly0))/2)}-{BOTTOM - round(((BOTTOM - top) - s*(ly1 - ly0))/2)}'


def measure(title, body, chip):
    """Lay the text block out from y=150 without drawing; return the draw list and where the ink ends."""
    ops = []; y = 150
    if chip:
        fe = F('Oxanium-800.ttf', 30); h = 52
        ops.append(('chip', chip, fe, y, h)); y += h + 30
    ft = F(AR_BLACK, 62)
    for t, col in title:
        up, dn = ink(t, ft); b = y + up; ops.append(('line', t, ft, b, col)); y = b + dn + 18
    y += 14
    fb = F(AR_BOLD, 30); lines, sp = nc.wrap(nc.tokens(body), fb, R_ - M - 10)
    bb = _m.textbbox((0, 0), 'ألإ', font=fb.real, anchor='ls', direction='rtl', language='ar')
    up, dn = -bb[1]/K, bb[3]/K; lh = up + dn + 18
    ops.append(('body', lines, sp, fb, y + up, lh)); y = y + up + (len(lines) - 1)*lh + dn
    return ops, y


def draw(cv, ops):
    d = D(cv)
    for op in ops:
        if op[0] == 'chip':
            _, t, f, y, h = op; w = nc.w_lt(t, f) + 44
            d.rounded_rectangle((R_ - w, y, R_, y + h), radius=8, fill=O+(255,))
            d.text((R_ - w/2, y + h/2 + 2), t, font=f, fill=N+(255,), anchor='mm')
        elif op[0] == 'line':
            _, t, f, b, col = op
            d.text((R_, b), t, font=f, fill=col+(255,), anchor='rs', direction='rtl', language='ar')
        else:
            _, lines, sp, f, b0, lh = op
            nc.draw_lines(d, lines, sp, f, R_, b0, lh, on_light=True)


def slide(n, bg, chip, title, body):
    ops, end = measure(title, body, chip)
    cv, shift = scene(bg, end)
    d = D(cv); nc.chrome(cv, d, n, TOTAL); draw(cv, ops)
    print(f'slide {n}: text 150-{round(end)}, {shift}')
    return cv


def cover():
    t = [('لماذا شعار رينو', N), ('على شكل ماسة؟', O)]
    f1, f2 = F(AR_BLACK, 92), F(AR_BLACK, 100)
    y = 340
    u, dn = ink(t[0][0], f1); b1 = y + u; y = b1 + dn + 26
    u, dn = ink(t[1][0], f2); b2 = y + u; end = b2 + dn
    cv, shift = scene('renault-1-cover.jpg', end + 70)
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    d.text((W/2, b1), t[0][0], font=f1, fill=N+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, b2), t[1][0], font=f2, fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    fs = F(AR_BOLD, 32); s = 'قصة شعار تغيّر 9 مرات منذ 1925'; u, dn = ink(s, fs); c0 = end + 34; ch = u + dn + 28
    tw = nc.w_ar(s, fs) + 70
    d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, outline=O+(255,), width=3)
    d.text((W/2, c0 + 14 + u), s, font=fs, fill=N+(255,), anchor='ms', direction='rtl', language='ar')
    print(f'cover: text 340-{round(c0 + ch)}, {shift}')
    return cv


def ask():
    lines = [('أيّ شعار لرينو', N, 70), ('هو الأجمل برأيك:', N, 70), ('القديم أم الحالي؟', O, 92)]
    fe = F(AR_BOLD, 30); y = 300; eh = 58
    ops = []; y2 = y + eh + 36
    for t, col, sz in lines:
        f = F(AR_BLACK, sz); u, dn = ink(t, f); b = y2 + u; ops.append((t, f, col, b)); y2 = b + dn + 26
    end = y2 - 26
    cv, shift = scene('renault-6-2021-real.jpg', end)
    d = D(cv); nc.chrome(cv, d, TOTAL, TOTAL); d = D(cv)
    ew = nc.w_ar('شاركنا رأيك', fe) + 52
    d.rectangle((W/2 - ew/2, y, W/2 + ew/2, y + eh), fill=O+(255,))
    d.text((W/2, y + eh/2 + 2), 'شاركنا رأيك', font=fe, fill=N+(255,), anchor='mm', direction='rtl', language='ar')
    for t, f, col, b in ops:
        d.text((W/2, b), t, font=f, fill=col+(255,), anchor='ms', direction='rtl', language='ar')
    print(f'ask: text 300-{round(end)}, {shift}')
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    slides = [cover(),
              slide(2, 'renault-2-1923.jpg', '1923', [('في البداية..', N), ('لم يكن ماسة', O)],
                    [('في عام', Wh), ('1923', O), ('وضعت رينو أول شعار على مقدمة سياراتها، وكان', Wh),
                     ('دائرياً على شكل شبك', O), ('يحمل اسم رينو.', Wh), ('\n', Wh),
                     ('والغريب أن هذا الشبك كان', Wh), ('يُخفي خلفه بوق السيارة!', O)]),
              slide(3, 'renault-3-1925.jpg', '1925', [('غطاء المحرك', N), ('هو السبب', O)],
                    [('كان غطاء المحرك مكوّناً من', Wh), ('سطحين مائلين', O),
                     ('بينهما خط في المنتصف، فناسبته زوايا الماسة أكثر من الدائرة.', Wh), ('\n', Wh),
                     ('ظهرت الماسة عام', Wh), ('1924', O), ('واعتُمدت رسمياً عام', Wh), ('1925.', O)]),
              slide(4, 'renault-3-1925.jpg', '1929', [('بدأت مع', N), ('السيارات الفاخرة', O)],
                    [('منذ عام', Wh), ('1929', O), ('وضعت رينو الماسة على سياراتها الرياضية الفاخرة', Wh),
                     ('«ستيلا»،', O), ('ثم انتشرت على بقية سياراتها', Wh), ('خلال الثلاثينيات.', O)]),
              slide(5, 'renault-4-1972.jpg', '1972', [('فنان أعاد', N), ('رسم الماسة', O)],
                    [('استعانت رينو بالفنان', Wh), ('فيكتور فازاريلي', O),
                     ('وابنه، فصمّما ماسة من خطوط متوازية بلا اسم رينو، وكانت', Wh), ('رينو 5', O), ('أول سيارة تحملها.', Wh)]),
              slide(6, 'renault-6-2021-real.jpg', '2021', [('تغيّر 9 مرات..', N), ('وبقيت الماسة', O)],
                    [('النسخة الحالية', Wh), ('ماستان متداخلتان', O), ('بتصميم مسطّح يناسب الشاشات.', Wh), ('\n', Wh),
                     ('ومنذ عام', Wh), ('1925', O), ('أعادت رينو تصميم شعارها', Wh), ('9 مرات،', O), ('وبقيت الماسة أساس هويتها.', Wh)]),
              ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-renault-diamond-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
