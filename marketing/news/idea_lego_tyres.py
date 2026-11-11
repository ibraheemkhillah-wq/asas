"""«عندك فكرة»: the world's biggest tyre maker is a toy company — DARK single post, 2160x2700.

usage: python3 idea_lego_tyres.py <brand-kit dir> <out.png>
Photo: Canva (idea-tyres-bg.jpg): a full-size tyre with a tiny toy tyre in front of it.
Logos: the four companies' own marks (logo-*.png), each on a plate in its row.
Figures: tyres made in 2011 (the year is not printed, at the user's request) — LEGO 318 m, Bridgestone 190 m, Michelin 184 m, Goodyear 181 m; Guinness World
Records lists LEGO as the largest toy tyre manufacturer by annual volume.
The photo is scaled down into the top-left so the headline has the dark right side to itself; the canvas
around it is the same photo enlarged and blurred. Layout in 1080 units; every line is placed from its
measured ink box with at least 24 units clear.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, HERE); sys.path.insert(0, sys.argv[1])
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, LOGONAVY as N, AR_BLACK, AR_BOLD, SOFT, DEEP, IDEA_BLUE
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.hires(); nc.THEME = 'dark'; nc.SECTION = 'idea'
K = nc.K; OX = 'Oxanium-800.ttf'
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))
def F(name, size): return nc.F(name, size)


def ink(t, f, ar=True):
    """(above, below, width) of the ink around the baseline, in units."""
    kw = dict(direction='rtl', language='ar') if ar else {}
    b = _m.textbbox((0, 0), t, font=f.real, anchor='ls', **kw); return -b[1]/K, b[3]/K, (b[2] - b[0])/K


def background():
    src = Image.open(os.path.join(HERE, 'idea-tyres-bg.jpg')).convert('RGB')
    S, OY = 0.60, 100                                   # photo scale and top edge: tyre 148-691, toy tyre at (219, 705)
    big = src.resize((round(W*K*1.5), round(H*K*1.5)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(50*K))
    cv = big.crop((big.width - W*K, 0, big.width, H*K))             # the photo's dark blue right side
    cv = Image.blend(cv, Image.new('RGB', cv.size, DEEP), 0.45).convert('RGBA')
    pw, ph = round(W*K*S), round(H*K*S)
    im = src.resize((pw, ph), Image.LANCZOS).convert('RGBA')
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    m = np.minimum.reduce([(pw - 1 - xx)/(150*K), yy/(50*K), (ph - 1 - yy)/(70*K)]).clip(0, 1)
    im.putalpha(Image.fromarray((m*255).astype(np.uint8)))
    cv.alpha_composite(im, (0, OY*K))
    ys = np.arange(H*K, dtype=np.float32)/K                         # deep floor for the table and footer
    a = np.clip((ys - 700)/160, 0, 1)**1.2*0.80
    lay = Image.new('RGBA', (W*K, H*K), DEEP + (0,)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)
    return cv


def headline(d):
    """Right-aligned on the dark side, starting low (y=320); returns where the ink ends."""
    maxw = R_ - 440; y = 320
    for t, col, size in (('أكبر مصنّع إطارات', Wh, 62), ('في العالم..', Wh, 62), ('شركة ألعاب!', O, 92)):
        f = F(AR_BLACK, size)
        while ink(t, f)[2] > maxw: size -= 2; f = F(AR_BLACK, size)
        up, dn, _ = ink(t, f); b = y + up
        d.text((R_, b), t, font=f, fill=col + (255,), anchor='rs', direction='rtl', language='ar'); y = b + dn + 26
    y -= 26
    t = 'رقم قياسي في موسوعة غينيس'; f = F(AR_BOLD, 26); up, dn, tw = ink(t, f)
    c0 = y + 34; ch = up + dn + 26
    d.rounded_rectangle((R_ - tw - 56, c0, R_, c0 + ch), radius=ch/2, outline=O + (255,), width=3)
    d.text((R_ - 28, c0 + 13 + up), t, font=f, fill=Wh + (255,), anchor='rs', direction='rtl', language='ar')
    return y, c0 + ch


# name, million tyres a year, logo file, colour of the plate the logo sits on
ROWS = [('ليغو', 318, 'logo-lego.png', (227, 0, 11)), ('بريدجستون', 190, 'logo-bridgestone.png', (255, 255, 255)),
        ('ميشلان', 184, 'logo-michelin.png', (255, 255, 255)), ('غوديير', 181, 'logo-goodyear.png', (0, 70, 150))]
Y0, RH, GAP = 778, 90, 12


def table(cv):
    glow = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0))               # soft orange glow under the winner
    ImageDraw.Draw(glow).rounded_rectangle((M*K, (Y0 + 6)*K, R_*K, (Y0 + RH + 10)*K), radius=18*K, fill=O + (120,))
    cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22*K)))
    d = nc.Draw(cv); fn = F(AR_BLACK, 38); fv = F(OX, 58); fu = F(AR_BOLD, 24); fr = F(OX, 40)
    for i, (name, val, logo, plate) in enumerate(ROWS):
        y = Y0 + i*(RH + GAP); cy = y + RH/2; top = i == 0
        d.rounded_rectangle((M, y, R_, y + RH), radius=16, fill=(12, 34, 56, 235), outline=(255, 255, 255, 34), width=2)
        x0 = R_ - (R_ - M)*val/ROWS[0][1]                             # bar length is the share of the winner's output
        d.rounded_rectangle((x0, y, R_, y + RH), radius=16, fill=(O if top else IDEA_BLUE) + (255,))
        q = 62; qx = R_ - 14 - q                                      # rank square
        d.rounded_rectangle((qx, cy - q/2, qx + q, cy + q/2), radius=10, fill=(N if top else DEEP) + (255,))
        up, dn, tw = ink(str(i + 1), fr, False)
        d.text((qx + q/2 - tw/2, cy + (up - dn)/2), str(i + 1), font=fr, fill=(Wh if top else O) + (255,), anchor='ls')
        pw, pp = 176, 62; lx1 = qx - 16                               # the company's logo on its own plate
        d.rounded_rectangle((lx1 - pw, cy - pp/2, lx1, cy + pp/2), radius=10, fill=plate + (255,))
        lg = Image.open(os.path.join(HERE, logo)).convert('RGBA')
        sc = min((pw - 24)*K/lg.width, (pp - (4 if lg.width == lg.height else 18))*K/lg.height)
        lg = lg.resize((round(lg.width*sc), round(lg.height*sc)), Image.LANCZOS)
        cv.alpha_composite(lg, (round((lx1 - pw/2)*K - lg.width/2), round(cy*K - lg.height/2)))
        nx = lx1 - pw - 22; up, dn, nw = ink(name, fn)
        d.text((nx, cy + (up - dn)/2), name, font=fn, fill=(N if top else Wh) + (255,), anchor='rs', direction='rtl', language='ar')
        if top:
            t = 'شركة ألعاب'; ft = F(AR_BOLD, 24); up, dn, tw = ink(t, ft); ph = 46; px1 = nx - nw - 20
            d.rounded_rectangle((px1 - tw - 40, cy - ph/2, px1, cy + ph/2), radius=ph/2, fill=N + (255,))
            d.text((px1 - 20, cy + (up - dn)/2), t, font=ft, fill=Wh + (255,), anchor='rs', direction='rtl', language='ar')
        u = 'مليون إطار'; up, dn, uw = ink(u, fu); ux = (x0 if top else M) + 26     # unit, then the number to its right
        d.text((ux + uw, cy + (up - dn)/2), u, font=fu, fill=(N if top else SOFT) + (255,), anchor='rs', direction='rtl', language='ar')
        up, dn, vw = ink(str(val), fv, False)
        d.text((ux + uw + 16, cy + (up - dn)/2), str(val), font=fv, fill=(N if top else Wh) + (255,), anchor='ls')
        print(f'row {i + 1}: {y}-{y + RH}, bar from x={round(x0)}, name/tag start x={round(px1 - tw - 40) if top else round(nx - nw)}, value block ends x={round(ux + uw + 16 + vw)}')
    return Y0 + len(ROWS)*(RH + GAP) - GAP


if __name__ == '__main__':
    cv = background(); d = nc.Draw(cv); nc.chrome(cv, d, 1, 1)
    d = nc.Draw(cv)
    d.ellipse((219 - 44, 705 - 44, 219 + 44, 705 + 44), outline=O + (255,), width=3)     # the toy tyre
    t_end, c_end = headline(d)
    end = table(cv); d = nc.Draw(cv)
    t = 'الإنتاج السنوي التقريبي · إطارات ليغو صغيرة تُصنع لألعابها'; f = F(AR_BOLD, 24); up, dn, _ = ink(t, f)
    d.text((W/2, end + 26 + up), t, font=f, fill=SOFT + (255,), anchor='ms', direction='rtl', language='ar')
    print(f'headline 320-{round(t_end)}, chip ends {round(c_end)}, table {Y0}-{end}, note {end + 26}-{round(end + 26 + up + dn)}, footer icons from 1275')
    cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
