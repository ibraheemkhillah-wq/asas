"""«من خدماتنا»: eight single-image service posts (two ideas per service), 2160x2700.

usage: python3 services_nov.py <brand-kit dir> <out dir>
Themes are the opposite of October's: airport + insurance DARK (were light), open km + child seat LIGHT (were dark).
Photos: Canva AI (*.jpg here); the child seat in seat-a is the company's own seat (../carseat-green-studio.png).
All services are paid extras: every post carries «برسوم إضافية · وفق الشروط والأحكام».
Layout in 1080 units; every line is placed from its measured ink box with at least 24 units clear.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'news')); sys.path.insert(0, sys.argv[1])
import idea_tyre_code as tc
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY as N, SOFT, AR_BLACK, AR_BOLD, CT_FONT
from brand import LOGO_WHITE, LOGO_NAVY, load_icons
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

K = nc.K
F, D, ar, lt, ink, shade, layer, glass = tc.F, tc.D, tc.ar, tc.lt, tc.ink, tc.shade, tc.layer, tc.glass
OX, OX6 = tc.OX, tc.OX6
INK = (84, 102, 124); PAPER = (248, 250, 252); GREEN = (46, 170, 110)
TERMS = 'برسوم إضافية · وفق الشروط والأحكام'


def photo(name, shift=0, scale=1.0):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA')
    s = max(W*K/im.width, H*K/im.height)*scale; im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l = (im.width - W*K)//2; t = (im.height - H*K)//2 - round(shift*K)
    cv = Image.new('RGBA', (W*K, H*K)); cv.paste(im, (-l, -t))
    if shift > 0:                                               # the strip freed at the top continues the top rows
        top = im.crop((l, 0, l + W*K, 24*K)).resize((W*K, round(shift*K) + 2)).filter(ImageFilter.GaussianBlur(10*K))
        cv.paste(top, (0, 0))
    return cv


def halo(cv, draws, col, r=16, alpha=1.6):
    lay = Image.new('L', (W*K, H*K), 0); ld = ImageDraw.Draw(lay)
    for (x, y), t, f, anchor in draws:
        ld.text((x*K, y*K), t, font=f.real, fill=255, anchor=anchor, direction='rtl', language='ar')
    lay = lay.filter(ImageFilter.MaxFilter(2*round(r*0.6*K/2) + 1)).filter(ImageFilter.GaussianBlur(r*K))
    c = Image.new('RGBA', (W*K, H*K), col + (0,)); c.putalpha(lay.point(lambda v: min(255, int(v*alpha)))); cv.alpha_composite(c)


def header(cv, dark):
    lg = Image.open(LOGO_WHITE if dark else LOGO_NAVY).convert('RGBA'); lw = 270
    cv.alpha_composite(lg.resize((lw*K, round(lw*K*lg.height/lg.width)), Image.LANCZOS), ((M - 6)*K, 46*K))
    d = D(cv); fb = F(AR_BOLD, 26); bh = 58; by = 50; label = 'من خدماتنا'
    u, dn, w = ink(label, fb); bw = w + 64; bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=6, fill=N + (255,), outline=(Wh + (90,)) if dark else None, width=2 if dark else 0)
    d.polygon([(bx, by + bh - 22), (bx, by + bh), (bx + 22, by + bh)], fill=O + (255,))
    ar(d, (bx + bw/2, by + bh/2 + (u - dn)/2), label, fb, Wh, 'ms')


def footer(cv, dark):
    col = Wh if dark else N
    ic = load_icons(34*K)
    if not dark:
        for k, im in ic.items():
            a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
            a[..., :3] = np.array(N, np.float32)*L + 255*(1 - L); ic[k] = Image.fromarray(a.astype(np.uint8), 'RGBA')
    d = D(cv); fc = F(CT_FONT, 29); y = 1292; x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (round(x*K), round((y - 17)*K))); x += 44
    d = D(cv); d.text((x + 6, y + 2), 'callrenttr', font=fc, fill=col + (255,), anchor='lm', direction='ltr', language='en')
    t = '+90 555 034 22 00'; d.text((R_, y + 2), t, font=fc, fill=col + (255,), anchor='rm', direction='ltr', language='en')
    x = R_ - nc.w_lt(t, fc) - 18 - 34
    for k in ('ph', 'wa'):
        cv.alpha_composite(ic[k], (round(x*K), round((y - 17)*K))); x -= 44


def headline(cv, lines, top, dark, x=None, anchor=None, gap=24, glow=True):
    """lines: [(text, colour, size)]; right-aligned at R_ (or centred). Returns the ink bottom."""
    x = R_ if x is None else x; anchor = anchor or ('rs' if x == R_ else 'ms')
    y = top - gap; draws = []
    for t, col, size in lines:
        f = F(AR_BLACK, size); u, dn, w = ink(t, f); assert w <= R_ - M + 2, t
        b = y + gap + u; draws.append(((x, b), t, f, anchor, col)); y = b + dn
    if glow: halo(cv, [(xy, t, f, an) for xy, t, f, an, _ in draws], DEEP if dark else (255, 255, 255), alpha=1.5 if dark else 1.9)
    d = D(cv)
    for xy, t, f, an, col in draws: ar(d, xy, t, f, col, an)
    return y


def para(cv, t, top, size, col, x=R_, maxw=None, anchor='rs', gap=14, font=AR_BOLD):
    f = F(font, size); d = D(cv); u, dn, _ = ink('ألإ', f); y = top
    words, cur, lines = t.split(), '', []
    for wd in words:
        c = (cur + ' ' + wd).strip()
        if cur and ink(c, f)[2] > (maxw or R_ - M): lines.append(cur); cur = wd
        else: cur = c
    lines.append(cur)
    for ln in lines:
        b = y + u; ar(d, (x, b), ln, f, col, anchor); y = b + dn + gap
    return y - gap


def terms(cv, y, dark, x=None):
    """The orange «paid extra» chip, centred (or right-aligned at x). Returns its bottom."""
    f = F(AR_BOLD, 25); u, dn, w = ink(TERMS, f); h = u + dn + 22; cw = w + 52
    x1 = (W/2 + cw/2) if x is None else x
    d = D(cv); d.rounded_rectangle((x1 - cw, y, x1, y + h), radius=h/2, fill=O + (255,))
    ar(d, (x1 - cw/2, y + 11 + u), TERMS, f, Wh if dark else N, 'ms')
    return y + h


def floor(cv, dark, start=1150, span=110):
    shade(cv, [(lambda y: np.clip((y - start)/span, 0, 1)*0.95, DEEP if dark else (255, 255, 255))])


def pin(d, x, y, r=16, col=O):
    d.ellipse((x - r, y - r*2.6, x + r, y - r*0.6), fill=col + (255,))
    d.polygon([(x - r*0.82, y - r*1.25), (x + r*0.82, y - r*1.25), (x, y)], fill=col + (255,))
    d.ellipse((x - r*0.42, y - r*2.02, x + r*0.42, y - r*1.18), fill=Wh + (255,))


# ======================================================================== airport (dark)
def air_a():
    cv = photo('air-a.jpg')
    shade(cv, [(lambda y: (1 - y/560)**1.2*0.88, DEEP)]); floor(cv, True, 900, 200)
    header(cv, True)
    end = headline(cv, [('وصلت إلى إسطنبول؟', Wh, 74), ('سيارتك بانتظارك', O, 74)], 300, True)
    # an arrivals board: the status column says the car is ready
    rows = [('مطار إسطنبول', 'IST'), ('مطار صبيحة', 'SAW'), ('فندقك أو منزلك', '')]
    b0 = 935; rh = 54; bx0, bx1 = M, R_
    glass(cv, (bx0, b0, bx1, b0 + 56 + 3*rh + 12), radius=18, fill=(6, 14, 24, 240), outline=(255, 255, 255, 40))
    d = D(cv); fh = F(AR_BOLD, 22)
    ar(d, (bx1 - 28, b0 + 36), 'الوجهة', fh, SOFT); ar(d, (bx0 + 210, b0 + 36), 'الحالة', fh, SOFT, 'ms')
    d.line([(bx0 + 20, b0 + 52), (bx1 - 20, b0 + 52)], fill=(255, 255, 255, 50), width=2)
    for i, (name, code) in enumerate(rows):
        y = b0 + 56 + i*rh; cy = y + rh/2
        for j in range(18):                                    # split-flap tiles behind the destination
            tx = bx1 - 28 - (j + 1)*28
            if tx < bx0 + 400: break
            d.rounded_rectangle((tx, cy - 19, tx + 24, cy + 19), radius=3, fill=(18, 30, 44, 255))
            d.line([(tx, cy), (tx + 24, cy)], fill=(6, 12, 20, 255), width=2)
        fn = F(AR_BLACK, 27); u, dn, w = ink(name, fn); ar(d, (bx1 - 36, cy + (u - dn)/2), name, fn, (255, 214, 150))
        if code:
            fc = F(OX, 24); u2, d2, w2 = ink(code, fc, False); lt(d, (bx1 - 36 - w - 16 - w2, cy + (u2 - d2)/2), code, fc, SOFT)
        ft = F(AR_BLACK, 23); t = 'سيارتك جاهزة'; u3, d3, w3 = ink(t, ft)
        d.rounded_rectangle((bx0 + 210 - w3/2 - 22, cy - 19, bx0 + 210 + w3/2 + 22, cy + 19), radius=19, fill=GREEN + (255,))
        ar(d, (bx0 + 210, cy + (u3 - d3)/2), t, ft, Wh, 'ms')
        if i < 2: d.line([(bx0 + 20, y + rh), (bx1 - 20, y + rh)], fill=(255, 255, 255, 25), width=1)
    bend = b0 + 56 + 3*rh + 12
    c = terms(cv, bend + 26, True)
    footer(cv, True)
    print('air-a: title 300 -', round(end), '| board', b0, '-', bend, '| chip to', round(c))
    return cv


def air_b():
    cv = photo('air-b.jpg')
    shade(cv, [(lambda y: (1 - y/600)**1.2*0.90, DEEP), (lambda y: np.full_like(y, 0.25), DEEP)]); floor(cv, True, 1100, 120)
    header(cv, True)
    end = headline(cv, [('من المطار..', Wh, 80), ('حتى باب منزلك', O, 80)], 300, True)
    t = 'في المطار أو في أي مكان داخل إسطنبول'; f = F(AR_BOLD, 32); u, dn, w = ink(t, f); b = end + 30 + u
    halo(cv, [((R_, b), t, f, 'rs')], DEEP, r=12, alpha=1.5); ar(D(cv), (R_, b), t, f, Wh)
    # the route: a glowing dashed path from the airport to a pin on the shore, with stops on the way
    pts = [(150, 640), (260, 700), (330, 800), (470, 860), (620, 930), (760, 1010)]
    from scipy.interpolate import splprep, splev
    P = np.array(pts, float); tck, _ = splprep([P[:, 0], P[:, 1]], s=0, k=3); uu = np.linspace(0, 1, 400); px, py = splev(uu, tck)
    g, gd = layer(); gd.line(list(zip(px, py)), fill=O + (160,), width=14, joint='curve'); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(10*K)))
    d = D(cv)
    for i in range(0, 400, 14): d.line([(px[i], py[i]), (px[min(i + 8, 399)], py[min(i + 8, 399)])], fill=O + (255,), width=5)
    # airport badge at the start
    ax, ay = pts[0]; d.ellipse((ax - 40, ay - 40, ax + 40, ay + 40), fill=O + (255,), outline=Wh + (255,), width=3)
    pl = [(0, -22), (5, -6), (24, 4), (24, 10), (5, 4), (4, 16), (11, 22), (11, 26), (0, 22), (-11, 26), (-11, 22), (-4, 16), (-5, 4), (-24, 10), (-24, 4), (-5, -6)]
    d.polygon([(ax + px_*1.15, ay + py_*1.15) for px_, py_ in pl], fill=N + (255,))
    f = F(AR_BOLD, 24); t = 'المطار'; u, dn, w = ink(t, f)
    d.rounded_rectangle((ax - w/2 - 16, ay + 50, ax + w/2 + 16, ay + 50 + u + dn + 16), radius=12, fill=DEEP + (230,))
    ar(d, (ax, ay + 58 + u), t, f, Wh, 'ms')
    for (sx, sy), lab in (((330, 800), 'الفندق'), ((620, 930), 'المكتب')):
        d.ellipse((sx - 11, sy - 11, sx + 11, sy + 11), fill=Wh + (255,), outline=O + (255,), width=4)
        u, dn, w = ink(lab, f); d.rounded_rectangle((sx + 20, sy - u/2 - 12 - 26, sx + 20 + w + 28, sy + u/2 + dn - 26), radius=10, fill=DEEP + (220,))
        ar(d, (sx + 34 + w, sy - 26 + u/2 - 2), lab, f, Wh)
    ex, ey = pts[-1]; g, gd = layer(); gd.ellipse((ex - 60, ey - 60, ex + 60, ey + 20), fill=O + (140,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(20*K)))
    d = D(cv); pin(d, ex, ey, 24)
    t = 'بابك'; fb = F(AR_BLACK, 30); u, dn, w = ink(t, fb)
    d.rounded_rectangle((ex - w/2 - 22, ey + 16, ex + w/2 + 22, ey + 16 + u + dn + 22), radius=14, fill=O + (255,))
    ar(d, (ex, ey + 27 + u), t, fb, N, 'ms')
    c = terms(cv, 1180, True)
    footer(cv, True)
    print('air-b: title 300 -', round(end), '| chip', 1180, '-', round(c))
    return cv


# ======================================================================== open km (light)
def okm_a():
    cv = photo('okm-a.jpg')
    floor(cv, False, 1130, 90)
    header(cv, False)
    end = headline(cv, [('وجهات كثيرة..', N, 74), ('والعدّاد مفتوح', O, 84)], 300, False)
    # destination stamps across the sky
    dests = [('شيله', 'ŞİLE'), ('صبانجة', 'SAPANCA'), ('بورصة', 'BURSA'), ('كارتبه', 'KARTEPE')]
    sw, sh, gap = 206, 150, 18; tot = 4*sw + 3*gap; x = R_; y0 = end + 50
    rng = np.random.default_rng(4)
    for i, (ar_, la) in enumerate(dests):
        x0 = x - sw; rot = rng.uniform(-4, 4)
        st = Image.new('RGBA', (sw*K, sh*K), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rectangle((0, 0, sw*K, sh*K), fill=(255, 255, 255, 255))
        for k in range(0, sw*K, 14*K):                          # perforated edges
            for yy in (0, sh*K): sd.ellipse((k + 2*K, yy - 5*K, k + 12*K, yy + 5*K), fill=(0, 0, 0, 0))
        for k in range(0, sh*K, 14*K):
            for xx in (0, sw*K): sd.ellipse((xx - 5*K, k + 2*K, xx + 5*K, k + 12*K), fill=(0, 0, 0, 0))
        sd.rectangle((12*K, 12*K, sw*K - 12*K, sh*K - 12*K), outline=O + (255,), width=3*K)
        f = F(AR_BLACK, 34).real; sd.text((sw*K/2, 66*K), ar_, font=f, fill=N + (255,), anchor='ms', direction='rtl', language='ar')
        f2 = F(OX6, 18).real; sd.text((sw*K/2, 96*K), la, font=f2, fill=INK + (255,), anchor='ms')
        sd.text((sw*K/2, 124*K), 'بلا حدود', font=F(AR_BOLD, 17).real, fill=O + (255,), anchor='ms', direction='rtl', language='ar')
        sh_ = Image.new('RGBA', st.size, (0, 0, 0, 0)); sh_.putalpha(st.getchannel('A').point(lambda v: v*0.35))
        sh_ = Image.merge('RGBA', (*Image.new('RGB', st.size, (20, 40, 60)).split(), sh_.getchannel('A')))
        r1 = sh_.rotate(rot, expand=True, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(8*K)); r2 = st.rotate(rot, expand=True, resample=Image.BICUBIC)
        px_ = round((x0 + sw/2)*K - r2.width/2); py_ = round((y0 + sh/2)*K - r2.height/2)
        cv.alpha_composite(r1, (px_ + 6*K, py_ + 10*K)); cv.alpha_composite(r2, (px_, py_))
        x -= sw + gap
    send = y0 + sh + 10
    c = terms(cv, 1160, False)
    footer(cv, False)
    print('okm-a: title 300 -', round(end), '| stamps', round(y0), '-', round(send), '| chip 1160 -', round(c))
    return cv


def okm_b():
    cv = photo('okm-b.jpg')
    floor(cv, False, 1140, 90)
    header(cv, False)
    end = headline(cv, [('خطّط لعطلتك..', N, 74), ('ولا تحسب الكيلومترات', O, 66)], 300, False)
    # an itinerary card over the lake
    days = [('الجمعة', 'من إسطنبول إلى صبانجة'), ('السبت', 'جولة في كارتبه'), ('الأحد', 'شيله ثم العودة')]
    cx0, cx1, cy0 = M, 640, end + 50; rh = 96; ch = 74 + 3*rh + 20
    glass(cv, (cx0, cy0, cx1, cy0 + ch), radius=24, fill=(255, 255, 255, 236), outline=(255, 255, 255, 255))
    d = D(cv); fh = F(AR_BLACK, 30); u, dn, w = ink('خطة العطلة', fh); ar(d, (cx1 - 30, cy0 + 26 + u), 'خطة العطلة', fh, N)
    f8 = F(AR_BOLD, 22); t8 = 'عدّاد مفتوح'; u8, d8, w8 = ink(t8, f8)
    d.rounded_rectangle((cx0 + 26, cy0 + 22, cx0 + 26 + w8 + 30, cy0 + 22 + u8 + d8 + 18), radius=16, fill=O + (255,))
    ar(d, (cx0 + 41 + w8, cy0 + 31 + u8), t8, f8, N)
    lx = cx1 - 52
    d.line([(lx, cy0 + 74 + rh/2), (lx, cy0 + 74 + 2.5*rh)], fill=O + (255,), width=3)
    for i, (day, plan) in enumerate(days):
        cy = cy0 + 74 + i*rh + rh/2
        d.ellipse((lx - 12, cy - 12, lx + 12, cy + 12), fill=O + (255,), outline=Wh + (255,), width=3)
        fd = F(AR_BOLD, 22); u, dn, w = ink(day, fd); ar(d, (lx - 30, cy - 8), day, fd, INK)
        fp = F(AR_BLACK, 28); u2, d2, w2 = ink(plan, fp); assert w2 <= cx1 - cx0 - 110, plan
        ar(d, (lx - 30, cy + 8 + u2), plan, fp, N)
    cend = cy0 + ch
    c = terms(cv, 1180, False)
    footer(cv, False)
    print('okm-b: title 300 -', round(end), '| card', round(cy0), '-', round(cend), '| chip 1180 -', round(c))
    return cv


# ======================================================================== insurance (dark)
def shield_path(cx, top, w, h):
    pts = []
    for t in np.linspace(0, 1, 40):                             # top edge with a slight dip
        pts.append((cx - w/2 + w*t, top + 10*math.sin(math.pi*t)*0 + 0))
    for t in np.linspace(0, 1, 60):                             # right flank down to the point
        a = t*math.pi/2; pts.append((cx + w/2*math.cos(a)**1.4 if t < 1 else cx, top + h*0.42 + (h*0.58)*math.sin(a)))
    for t in np.linspace(1, 0, 60):
        a = t*math.pi/2; pts.append((cx - w/2*math.cos(a)**1.4 if t < 1 else cx, top + h*0.42 + (h*0.58)*math.sin(a)))
    pts.insert(40, (cx + w/2, top + h*0.42)); pts.append((cx - w/2, top + h*0.42))
    return pts


def kasko_a():
    cv = photo('kasko-a.jpg', shift=60)
    shade(cv, [(lambda y: (1 - y/620)**1.2*0.92, DEEP)]); floor(cv, True, 1090, 130)
    header(cv, True)
    end = headline(cv, [('مطر وزحام ومفاجآت..', Wh, 70), ('والتأمين الشامل معك', O, 74)], 300, True)
    # a protective shield of light behind the car
    sp = shield_path(540, end + 60, 840, 560)
    g, gd = layer(); gd.polygon(sp, fill=O + (34,)); cv.alpha_composite(g)
    g, gd = layer(); gd.line(sp + [sp[0]], fill=O + (200,), width=10, joint='curve'); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(14*K)))
    d = D(cv); d.line(sp + [sp[0]], fill=O + (255,), width=4, joint='curve')
    c = terms(cv, 1180, True)
    footer(cv, True)
    print('kasko-a: title 300 -', round(end), '| shield', round(end + 60), '-', round(end + 620), '| chip 1180 -', round(c))
    return cv


def kasko_b():
    cv = photo('kasko-b.jpg', shift=110)
    shade(cv, [(lambda y: (1 - y/560)**1.2*0.6, DEEP)]); floor(cv, True, 1150, 100)
    header(cv, True)
    end = headline(cv, [('مفتاح سيارتك..', Wh, 80), ('ومعه راحة بالك', O, 80)], 300, True)
    e2 = para(cv, 'أضِف التأمين الشامل إلى حجزك، وانطلق في إسطنبول مطمئناً', end + 30, 32, Wh, maxw=R_ - M - 120)
    # a small check stamped on the shield keychain (photo shield ~ x 697-911, y 810-1046 before the shift)
    sx, sy = 806, 940 + 110; d = D(cv)
    g, gd = layer(); gd.ellipse((sx - 40, sy - 40, sx + 40, sy + 40), fill=O + (110,)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(10*K)))
    d = D(cv); d.line([(sx - 20, sy + 2), (sx - 6, sy + 17), (sx + 22, sy - 16)], fill=O + (255,), width=8, joint='curve')
    c = terms(cv, 1180, True)
    footer(cv, True)
    print('kasko-b: title 300 -', round(end), '| para to', round(e2), '| chip 1180 -', round(c))
    return cv


# ======================================================================== child seat (light)
def seat_a():
    cv = photo('seat-a.jpg', shift=140)
    header(cv, False)
    # right column is empty in the flat lay: a stacked headline there
    x = R_; lines = [('حقيبة طفلك', N, 50), ('ممتلئة..', N, 50), ('اترك الكرسي', O, 54), ('علينا', O, 54)]
    end = headline(cv, lines, 330, False, x=R_, gap=20, glow=False)
    # the empty slot (lower right): dashed outline with our seat in it
    sx0, sy0, sx1, sy1 = 540, 880, 1000, 1166
    d = D(cv)
    for xx in range(int(sx0), int(sx1), 22): d.line([(xx, sy0), (min(xx + 12, sx1), sy0)], fill=O + (255,), width=3); d.line([(xx, sy1), (min(xx + 12, sx1), sy1)], fill=O + (255,), width=3)
    for yy in range(int(sy0), int(sy1), 22): d.line([(sx0, yy), (sx0, min(yy + 12, sy1))], fill=O + (255,), width=3); d.line([(sx1, yy), (sx1, min(yy + 12, sy1))], fill=O + (255,), width=3)
    seat = Image.open(os.path.join(HERE, '..', 'carseat-green-studio.png')).convert('RGBA'); seat = seat.crop(seat.getbbox())
    sh = 250; sw = round(sh*seat.width/seat.height); px_ = (sx0 + sx1)/2 - sw/2; py_ = sy1 - 18 - sh
    g, gd = layer(); gd.ellipse((px_ + 20, py_ + sh - 24, px_ + sw - 10, py_ + sh + 14), fill=(40, 50, 60, 120)); cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(12*K)))
    cv.alpha_composite(seat.resize((round(sw*K), round(sh*K)), Image.LANCZOS), (round(px_*K), round(py_*K)))
    d = D(cv); t = 'علينا ✓'; t = 'جاهز مع السيارة'; f = F(AR_BLACK, 24); u, dn, w = ink(t, f)
    d.rounded_rectangle((sx1 - w - 40, sy0 - 22, sx1 + 4, sy0 + 22), radius=22, fill=O + (255,))
    ar(d, (sx1 - 18, sy0 + (u - dn)/2), t, f, N)
    c = terms(cv, 1196, False)
    footer(cv, False)
    print('seat-a: title 330 -', round(end), '| slot', sy0, '-', sy1, '| chip 1196 -', round(c))
    return cv


def seat_b():
    cv = photo('seat-b.jpg', shift=200)
    shade(cv, [(lambda y: (1 - y/560)**1.1*0.94, (255, 255, 255))]); floor(cv, False, 1000, 120)
    header(cv, False)
    end = headline(cv, [('كرسي طفلك..', N, 74), ('جاهز مع سيارتك', O, 80)], 300, False)
    steps = [('1', 'اطلبه مع حجزك'), ('2', 'أخبرنا بعمر طفلك'), ('3', 'نجهّزه لك')]
    y0 = 1036; cw = (R_ - M - 2*18)/3; ch = 112
    for i, (n, t) in enumerate(steps):
        x1 = R_ - i*(cw + 18); x0 = x1 - cw
        glass(cv, (x0, y0, x1, y0 + ch), radius=20, fill=(255, 255, 255, 245), outline=(214, 222, 232, 255))
        d = D(cv); cx, cy = x1 - 38, y0 + ch/2
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=O + (255,))
        f = F(OX, 26); u, dn, w = ink(n, f, False); lt(d, (cx - w/2, cy + (u - dn)/2), n, f, N)
        ft = F(AR_BLACK, 24); u2, d2, w2 = ink(t, ft)
        if w2 > cw - 84:
            words = t.split(); a_, b_ = ' '.join(words[:-1]), words[-1]
            ar(d, (cx - 34, cy - 6), a_, ft, N); ar(d, (cx - 34, cy + 6 + u2), b_, ft, N)
        else: ar(d, (cx - 34, cy + (u2 - d2)/2), t, ft, N)
        if i < 2:
            ax = x0 - 9; d.polygon([(ax + 6, cy - 9), (ax - 6, cy), (ax + 6, cy + 9)], fill=O + (255,))
    c = terms(cv, y0 + ch + 30, False)
    footer(cv, False)
    print('seat-b: title 300 -', round(end), '| steps', y0, '-', y0 + ch, '| chip to', round(c))
    return cv


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    for name, fn in (('air-a', air_a), ('air-b', air_b), ('okm-a', okm_a), ('okm-b', okm_b),
                     ('kasko-a', kasko_a), ('kasko-b', kasko_b), ('seat-a', seat_a), ('seat-b', seat_b)):
        cv = fn(); p = os.path.join(out, f'svc-{name}.png'); cv.convert('RGB').save(p, optimize=True); print(p, cv.size)
