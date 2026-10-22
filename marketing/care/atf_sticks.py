"""«اعتنِ بسيارتك»: what the transmission fluid colour means — two LIGHT slides, 2160x2700.

usage: python3 atf_sticks.py <brand-kit dir> <out dir>
One Canva dipstick photo (atf-stick.jpg) recoloured four ways (atf-stick-<name>.jpg) so every row
shows the same stick and only the fluid changes. Sticks are multiplied onto the light page, so the
photo's white background disappears.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageChops
import numpy as np
from brand import ORANGE as O, LOGONAVY as N, WHITE as Wh, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT, LOGO_NAVY, load_icons, w_ar, w_lt

K = 2; W, H = 1080*K, 1350*K; M = 64*K; R_ = W - M
TEAL = (22, 138, 128); SOFTN = (96, 114, 136); PAGE = (244, 247, 250)
def S(v): return round(v*K)
def ar(d, xy, t, f, fill, anchor='rs'): d.text(xy, t, font=f, fill=fill, anchor=anchor, direction='rtl', language='ar')

ROWS = [  # stick, name, meaning, status, status colour
    ('red', 'أحمر صافٍ / وردي', 'زيت جديد يعمل بكفاءة تامة', 'ممتاز', (46, 160, 90)),
    ('darkred', 'أحمر داكن / بني فاتح', 'مستهلك جزئياً، اقترب موعد تغييره', 'طبيعي', (214, 160, 30)),
    ('black', 'بني غامق / أسود', 'زيت محترق، غيّره فوراً وافحص القير', 'خطر', (232, 110, 40)),
    ('milky', 'وردي حليبي', 'تسرّب سائل التبريد، أوقف القيادة', 'خطر جداً', (214, 40, 40)),
]


def page():
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.clip(np.sqrt(((xs - W/2)/W)**2 + ((ys - H*0.5)/H)**2)/0.75, 0, 1)[..., None]
    bg = np.array((255, 255, 255), np.float32)*(1 - g) + np.array((230, 236, 243), np.float32)*g
    return Image.fromarray(bg.astype(np.uint8)).convert('RGB')


def navy_icon(im):
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(N, np.float32)*L + 255*(1 - L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def chrome(cv, n, total):
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = S(270)
    cv.paste(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)), lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'اعتنِ بسيارتك'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=S(6), fill=TEAL)
    d.polygon([(bx, by + bh - S(22)), (bx, by + bh), (bx + S(22), by + bh)], fill=O)
    ar(d, (bx + bw/2, by + bh/2 + S(2)), label, fb, Wh, 'mm')
    ic = load_icons(S(34)); fc = F(CT_FONT, S(29)); y = S(1292); x = M
    for k in ('ig', 'fb'):
        im = navy_icon(ic[k]); cv.paste(im, (x, y - S(17)), im); x += S(44)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=N, anchor='lm')
    fp = F(LT_TEXT, S(24)); t = f'{n:02d} / {total:02d}'
    d.text((R_, y + S(2)), t, font=fp, fill=SOFTN, anchor='rm')
    if n < total:
        ax = R_ - w_lt(t, fp) - S(22)
        d.polygon([(ax, y - S(9)), (ax - S(14), y + S(1)), (ax, y + S(11))], fill=O)


def stick(name, width, keep=1.0):
    im = Image.open(os.path.join(HERE, f'atf-stick-{name}.jpg')).convert('RGB')
    im = im.crop((0, int(im.height*0.28), int(im.width*keep), int(im.height*0.80)))   # tip end only, no empty white
    return im.resize((width, round(im.height*width/im.width)), Image.LANCZOS)


def put(cv, im, xy):
    """Multiply the stick onto the page so its white background vanishes."""
    x, y = xy; box = (x, y, x + im.width, y + im.height)
    base = cv.crop(box); mixed = ImageChops.multiply(base, im)
    ramp = np.clip((im.width - np.arange(im.width, dtype=np.float32))/(im.width*0.22), 0, 1)   # cut end fades out
    mask = Image.fromarray((np.repeat(ramp[None, :], im.height, 0)*255).astype(np.uint8))
    cv.paste(Image.composite(mixed, base, mask), box)


def cover(out):
    cv = page(); d = ImageDraw.Draw(cv)
    ar(d, (W/2, S(236)), 'ماذا يعني لون', F(AR_BLACK, S(84)), N, 'ms')
    ar(d, (W/2, S(408)), 'زيت القير؟', F(AR_BLACK, S(118)), O, 'ms')
    t = 'افحص العصا… واعرف حالة ناقل الحركة'; fs = F(AR_BOLD, S(30)); tw = w_ar(t, fs) + S(60)
    d.rounded_rectangle((W/2 - tw/2, S(474), W/2 + tw/2, S(528)), radius=S(28), outline=O, width=S(3))
    ar(d, (W/2, S(502)), t, fs, N, 'mm')
    # the four sticks fanned like a colour chart, tips toward the left
    y = S(566)
    for name, *_ in ROWS:
        st = stick(name, S(640), 0.86); put(cv, st, ((W - st.width)//2, y)); y += S(166)
    chrome(cv, 1, 2)
    cv.save(out, optimize=True); print(out, cv.size)


def guide(out):
    cv = page(); d = ImageDraw.Draw(cv)
    t1, t2 = 'ماذا يعني لون', 'زيت القير؟'; fh = F(AR_BLACK, S(54))
    ar(d, (R_, S(220)), t1, fh, N)
    ar(d, (R_ - w_ar(t1, fh) - S(18), S(220)), t2, fh, O)
    top = S(262); rh = S(214); gap = S(16)
    for i, (name, title, meaning, status, scol) in enumerate(ROWS):
        y0 = top + i*(rh + gap)
        d.rounded_rectangle((M, y0, R_, y0 + rh), radius=S(24), fill=(255, 255, 255), outline=(222, 229, 238), width=S(2))
        d.rectangle((R_ - S(8), y0 + S(24), R_, y0 + rh - S(24)), fill=scol)
        st = stick(name, S(420), 0.62); put(cv, st, (M + S(14), y0 + (rh - st.height)//2))
        d = ImageDraw.Draw(cv)
        tx = R_ - S(36)
        d.text((tx, y0 + S(64)), f'0{i+1}', font=F('Oxanium-800.ttf', S(28)), fill=O, anchor='rs')
        ar(d, (tx - S(50), y0 + S(66)), title, F(AR_BLACK, S(38)), N)
        ar(d, (tx, y0 + S(118)), meaning, F(AR_BOLD, S(26)), SOFTN)
        fs = F(AR_BOLD, S(26)); cw_ = w_ar(status, fs) + S(44)
        d.rounded_rectangle((tx - cw_, y0 + S(142), tx, y0 + S(190)), radius=S(24), fill=scol)
        ar(d, (tx - cw_/2, y0 + S(167)), status, fs, Wh, 'mm')
    ny = top + 4*rh + 3*gap + S(46)
    ar(d, (W/2, ny), 'سيارات كثيرة بلا عصا قياس للقير، افحصه عند فني مختص', F(AR_BOLD, S(26)), SOFTN, 'ms')
    chrome(cv, 2, 2)
    cv.save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    cover(os.path.join(sys.argv[2], 'atf-sticks-1.png'))
    guide(os.path.join(sys.argv[2], 'atf-sticks-2.png'))
