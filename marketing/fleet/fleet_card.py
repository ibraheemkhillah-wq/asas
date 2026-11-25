"""Fleet stories: a spec card (make, model, year, fuel, gearbox, seats, luggage) over each 1080x1920 fleet photo,
set in the sky above the shop sign. Output 2160x3840.
usage: python3 fleet_card.py <brand-kit dir> <out dir> [ids]"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = sys.argv[1]
K = 2; W, H = 1080, 1920
NAVY = (16, 32, 52); ORANGE = (244, 141, 87); WHITE = (255, 255, 255)
FT = lambda n, s: ImageFont.truetype(os.path.join(KIT, 'fonts', n), round(s*K))
OX8, OX6, KUFI = 'Oxanium-800.ttf', 'Oxanium-600.ttf', 'NotoKufiArabic-ExtraBold.ttf'

# id: (make, model, year, fuel, gearbox, seats, bags)
CARS = {
    '05': ('RENAULT', 'Clio', '2024', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
}


def icon(name, px, col):
    a = Image.open(os.path.join(HERE, 'icons', name + '.png')).split()[3]; a = a.crop(a.getbbox())
    k = px/max(a.size); a = a.resize((round(a.width*k), round(a.height*k)), Image.LANCZOS)
    im = Image.new('RGBA', a.size, col + (0,)); im.putalpha(a); return im


def ink(d, t, f, rtl=False):
    kw = dict(direction='rtl', language='ar') if rtl else {}
    l, tp, r, b = d.textbbox((0, 0), t, font=f, anchor='ls', **kw); return -tp, b, r - l   # up, down, width (px)


def card(cid):
    make, model, year, fuel, gear, seats, bags = CARS[cid]
    im = Image.open(os.path.join(HERE, 'src', cid + '.png')).convert('RGB').resize((W*K, H*K), Image.LANCZOS).convert('RGBA')
    x0, y0, x1, y1 = 90, 196, 990, 456                         # card (units): below Instagram's story header, above the sign (~490 at the left)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle(
        (x0*K, (y0 + 14)*K, x1*K, (y1 + 18)*K), radius=34*K, fill=(0, 10, 25, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22*K)))
    blur = im.crop((x0*K, y0*K, x1*K, y1*K)).filter(ImageFilter.GaussianBlur(18*K))
    m = Image.new('L', blur.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, blur.width - 1, blur.height - 1), radius=34*K, fill=255)
    im.paste(blur, (x0*K, y0*K), m)
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle((x0*K, y0*K, x1*K, y1*K), radius=34*K, fill=NAVY + (212,), outline=WHITE + (60,), width=2*K)
    im.alpha_composite(ov); d = ImageDraw.Draw(im)
    cx = (x0 + x1)/2*K
    # make (spaced caps), model + year chip
    fm = FT(OX6, 30); sp = '  '.join(make); u, dn, w = ink(d, sp, fm); y = (y0 + 26)*K + u
    d.text((cx, y), sp, font=fm, fill=WHITE + (190,), anchor='ms'); y += dn
    fM = FT(OX8, 66); uM, dM, wM = ink(d, model, fM)
    fy = FT(OX8, 30); uy, dy, wy = ink(d, year, fy); cw, ch = wy + 36*K, uy + dy + 22*K
    gap = 26*K; tot = wM + gap + cw; xm = cx - tot/2
    base = y + 18*K + uM
    d.text((xm, base), model, font=fM, fill=WHITE, anchor='ls')
    chx = xm + wM + gap; chy = base - uM/2 - ch/2 + 6*K
    d.rounded_rectangle((chx, chy, chx + cw, chy + ch), radius=ch/2, fill=ORANGE)
    d.text((chx + cw/2, chy + ch/2), year, font=fy, fill=NAVY, anchor='mm')
    y = base + dM + 20*K
    d.line([((x0 + 70)*K, y), ((x1 - 70)*K, y)], fill=WHITE + (55,), width=2*K); y += 20*K
    # specs, right to left
    specs = [('local_gas_station', fuel), ('auto_transmission', gear), ('airline_seat_recline_normal', seats), ('luggage', bags)]
    fl = FT(KUFI, 23); colw = (x1 - x0 - 80)/4*K
    for i, (ic, lab) in enumerate(specs):
        mx = (x1 - 40)*K - colw*(i + 0.5)
        g = icon(ic, 38*K, ORANGE); im.alpha_composite(g, (round(mx - g.width/2), round(y)))
        u, dn, w = ink(d, lab, fl, True); d.text((mx, y + g.height + 16*K + u), lab, font=fl, fill=WHITE, anchor='ms', direction='rtl', language='ar')
        if i: d.line([(mx + colw/2, y + 6*K), (mx + colw/2, y + 38*K + 16*K + u + dn)], fill=WHITE + (45,), width=2*K)
    bottom = (y + 38*K + 16*K + u + dn)/K
    print(cid, 'card', y0, '-', y1, '| content bottom', round(bottom), '| margin', round(y1 - bottom))
    return im.convert('RGB')


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    ids = sys.argv[3].split(',') if len(sys.argv) > 3 else list(CARS)
    for cid in ids:
        card(cid).save(os.path.join(out, f'fleet-{cid}.png'), optimize=True)
