"""«عندك فكرة»: why the Renault logo is a diamond — seven LIGHT slides, 2160x2700.

usage: python3 idea_renault.py <brand-kit dir> <out dir>
Photos: Higgsfield GPT Image (at the user's request), renault-*.jpg. Each logo is the subject, so the text sits
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
SUBJECT = {'renault-1-cover.jpg': 620, 'renault-2-1923.jpg': 600, 'renault-3-1925.jpg': 710,
           'renault-4-1972.jpg': 660, 'renault-5-2021.jpg': 760}           # where each logo starts (units)


def F(name, size): return nc.F(name, size)
def D(cv): return nc.Draw(cv)


def ink(t, f):
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', direction='rtl', language='ar'); return -b[1]/K, b[3]/K


def scene(name, text_end):
    """Photo lowered so its logo starts >= 70 units under the text; the top is filled from its own top rows."""
    shift = max(0, round(text_end + 70 - SUBJECT[name]))
    im = Image.open(os.path.join(HERE, name)).convert('RGB').resize((W*K, H*K), Image.LANCZOS)
    cv = Image.new('RGB', (W*K, H*K))
    if shift:
        top = im.crop((0, 0, W*K, 60*K)).resize((W*K, shift*K + 4*K)).filter(ImageFilter.GaussianBlur(30*K))
        cv.paste(top, (0, 0))
    cv.paste(im, (0, shift*K))
    cv = cv.convert('RGBA')
    ys = np.arange(H*K, dtype=np.float32)/K                                # white fade behind the text, and the footer
    a = np.maximum(np.clip((text_end + 50 - ys)/220, 0, 1)**0.8*0.88, np.clip((ys - 1230)/40, 0, 1)*0.94)
    lay = Image.new('RGBA', (W*K, H*K), (255, 255, 255, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)
    return cv, shift


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
    print(f'slide {n}: text 150-{round(end)}, photo lowered {shift}, logo from {SUBJECT[bg] + shift}')
    return cv


def cover():
    t = [('لماذا شعار رينو', N), ('على شكل ماسة؟', O)]
    f1, f2 = F(AR_BLACK, 92), F(AR_BLACK, 100)
    y = 340
    u, dn = ink(t[0][0], f1); b1 = y + u; y = b1 + dn + 26
    u, dn = ink(t[1][0], f2); b2 = y + u; end = b2 + dn
    cv, shift = scene('renault-1-cover.jpg', end + 60)
    d = D(cv); nc.chrome(cv, d, 1, TOTAL); d = D(cv)
    d.text((W/2, b1), t[0][0], font=f1, fill=N+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, b2), t[1][0], font=f2, fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    fs = F(AR_BOLD, 32); s = 'قصة شعار تغيّر 9 مرات منذ 1925'; u, dn = ink(s, fs); c0 = end + 34; ch = u + dn + 28
    tw = nc.w_ar(s, fs) + 70
    d.rounded_rectangle((W/2 - tw/2, c0, W/2 + tw/2, c0 + ch), radius=ch/2, outline=O+(255,), width=3)
    d.text((W/2, c0 + 14 + u), s, font=fs, fill=N+(255,), anchor='ms', direction='rtl', language='ar')
    print(f'cover: text 340-{round(c0 + ch)}, photo lowered {shift}')
    return cv


def ask():
    lines = [('أيّ شعار لرينو', N, 70), ('هو الأجمل برأيك:', N, 70), ('القديم أم الحالي؟', O, 92)]
    fe = F(AR_BOLD, 30); y = 300; eh = 58
    ops = []; y2 = y + eh + 36
    for t, col, sz in lines:
        f = F(AR_BLACK, sz); u, dn = ink(t, f); b = y2 + u; ops.append((t, f, col, b)); y2 = b + dn + 26
    end = y2 - 26
    cv, shift = scene('renault-5-2021.jpg', end)
    d = D(cv); nc.chrome(cv, d, TOTAL, TOTAL); d = D(cv)
    ew = nc.w_ar('شاركنا رأيك', fe) + 52
    d.rectangle((W/2 - ew/2, y, W/2 + ew/2, y + eh), fill=O+(255,))
    d.text((W/2, y + eh/2 + 2), 'شاركنا رأيك', font=fe, fill=N+(255,), anchor='mm', direction='rtl', language='ar')
    for t, f, col, b in ops:
        d.text((W/2, b), t, font=f, fill=col+(255,), anchor='ms', direction='rtl', language='ar')
    print(f'ask: text 300-{round(end)}, photo lowered {shift}')
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
              slide(6, 'renault-5-2021.jpg', '2021', [('تغيّر 9 مرات..', N), ('وبقيت الماسة', O)],
                    [('النسخة الحالية', Wh), ('ماستان متداخلتان', O), ('بتصميم مسطّح يناسب الشاشات.', Wh), ('\n', Wh),
                     ('ومنذ عام', Wh), ('1925', O), ('أعادت رينو تصميم شعارها', Wh), ('9 مرات،', O), ('وبقيت الماسة أساس هويتها.', Wh)]),
              ask()]
    for i, cv in enumerate(slides, 1):
        p = os.path.join(out, f'idea-renault-diamond-{i}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
