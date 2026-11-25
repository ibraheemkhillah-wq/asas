"""Fleet stories: a spec card (make, model, year, fuel, gearbox, seats, luggage) over each 1080x1920 fleet photo,
set in the sky above the shop sign. Output 2160x3840.
usage: python3 fleet_card.py <brand-kit dir> <out dir> [ids] [styles: float,glass,line,tag]"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = sys.argv[1]
K = 2; W, H = 1080, 1920
NAVY = (16, 32, 52); ORANGE = (244, 141, 87); WHITE = (255, 255, 255)
FT = lambda n, s: ImageFont.truetype(os.path.join(KIT, 'fonts', n), round(s*K))
OX8, OX6, KUFI = 'Oxanium-800.ttf', 'Oxanium-600.ttf', 'NotoKufiArabic-ExtraBold.ttf'

# id: (make, model, year, fuel, gearbox, seats, bags)
CARS = {   # make, model, year, fuel, gearbox, seats, luggage  - model read from the photo; the rest to be confirmed
    '01': ('CHERY', 'Omoda 5', '2024', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '02': ('RENAULT', 'Megane', '2024', 'ديزل', 'أوتوماتيك', '5 مقاعد', '3 حقائب'),
    '03': ('HYUNDAI', 'Bayon', '2023', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '04': ('RENAULT', 'Clio', '2023', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '05': ('RENAULT', 'Clio', '2024', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '06': ('FIAT', 'Egea', '2023', 'ديزل', 'أوتوماتيك', '5 مقاعد', '3 حقائب'),
    '07': ('HYUNDAI', 'i20', '2025', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '08': ('HYUNDAI', 'i20', '2026', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '09': ('OPEL', 'Mokka', '2024', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '10': ('CHERY', 'Omoda 5', '2024', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '11': ('DACIA', 'Sandero Stepway', '2023', 'بنزين', 'أوتوماتيك', '5 مقاعد', 'حقيبتان'),
    '12': ('RENAULT', 'Taliant', '2023', 'بنزين', 'أوتوماتيك', '5 مقاعد', '3 حقائب'),
    '13': ('CHERY', 'Tiggo 8 Pro', '2024', 'بنزين', 'أوتوماتيك', '7 مقاعد', '3 حقائب'),
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


def card_float(cid):
    """Light version: no box - the name floats on the sky in white with a soft shadow, the specs sit in four small
    white pills; the sky and clouds stay visible."""
    make, model, year, fuel, gear, seats, bags = CARS[cid]
    im = Image.open(os.path.join(HERE, 'src', cid + '.png')).convert('RGB').resize((W*K, H*K), Image.LANCZOS).convert('RGBA')
    cx = W/2*K; sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fm = FT(OX8, 30); spc = '  '.join(make); u, dn, w = ink(d, spc, fm); y = 218*K + u
    for dd in (sd, d): dd.text((cx, y + (6*K if dd is sd else 0)), spc, font=fm, fill=((8, 26, 55, 235) if dd is sd else WHITE + (255,)), anchor='ms')
    y += dn
    fM = FT(OX8, 104); uM, dM, wM = ink(d, model, fM); fy = FT(OX8, 32); uy, dy, wy = ink(d, year, fy)
    cw, ch = wy + 38*K, uy + dy + 24*K; gap = 24*K; xm = cx - (wM + gap + cw)/2; base = y + 22*K + uM
    sd.text((xm, base + 8*K), model, font=fM, fill=(10, 30, 60, 170), anchor='ls'); d.text((xm, base), model, font=fM, fill=WHITE, anchor='ls')
    chx = xm + wM + gap; chy = base - uM/2 - ch/2 + 4*K
    sd.rounded_rectangle((chx, chy + 6*K, chx + cw, chy + ch + 6*K), radius=ch/2, fill=(10, 30, 60, 110))
    d.rounded_rectangle((chx, chy, chx + cw, chy + ch), radius=ch/2, fill=ORANGE); d.text((chx + cw/2, chy + ch/2), year, font=fy, fill=WHITE, anchor='mm')
    y = base + dM + 34*K
    specs = [('local_gas_station', fuel), ('auto_transmission', gear), ('airline_seat_recline_normal', seats), ('luggage', bags)]
    fl = FT(KUFI, 22); isz = 30*K; ph = 62*K; items = []
    for ic, lab in specs:
        u, dn, w = ink(d, lab, fl, True); items.append((ic, lab, u, dn, w, w + isz + 12*K + 40*K))
    tot = sum(i[5] for i in items) + 14*K*3; x = cx + tot/2
    for ic, lab, u, dn, w, pw in items:                        # right to left
        x0 = x - pw
        sd.rounded_rectangle((x0, y + 6*K, x, y + ph + 6*K), radius=ph/2, fill=(10, 30, 60, 90))
        d.rounded_rectangle((x0, y, x, y + ph), radius=ph/2, fill=(255, 255, 255, 236))
        g = icon(ic, isz, ORANGE); lay.alpha_composite(g, (round(x - 20*K - g.width), round(y + ph/2 - g.height/2)))
        d.text((x - 20*K - isz - 12*K, y + ph/2 + (u - dn)/2), lab, font=fl, fill=NAVY + (255,), anchor='rs', direction='rtl', language='ar')
        x = x0 - 14*K
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10*K))); im.alpha_composite(lay)
    print(cid, 'float: make top 218 | pills bottom', round((y + ph)/K), '| pills width', round(tot/K))
    return im.convert('RGB')


def _base(cid):
    return Image.open(os.path.join(HERE, 'src', cid + '.png')).convert('RGB').resize((W*K, H*K), Image.LANCZOS).convert('RGBA')


def _specs(cid):
    make, model, year, fuel, gear, seats, bags = CARS[cid]
    return make, model, year, [('local_gas_station', fuel), ('auto_transmission', gear), ('airline_seat_recline_normal', seats), ('luggage', bags)]


def _shadow(im, box, r, a=90, blur=18, dy=10):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + dy*K, box[2], box[3] + dy*K), radius=r, fill=(8, 26, 55, a))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur*K)))


def _spec_row(im, d, specs, y, cx, width, icol, tcol, divcol, isz=34, fs=22):
    """four columns right to left: icon above label, thin dividers. Returns bottom (px)."""
    fl = FT(KUFI, fs); colw = width/4; bot = y
    for i, (ic, lab) in enumerate(specs):
        mx = cx + width/2 - colw*(i + 0.5)
        g = icon(ic, isz*K, icol); im.alpha_composite(g, (round(mx - g.width/2), round(y)))
        u, dn, w = ink(d, lab, fl, True); b = y + g.height + 14*K + u
        d.text((mx, b), lab, font=fl, fill=tcol, anchor='ms', direction='rtl', language='ar'); bot = max(bot, b + dn)
        if i: d.line([(mx + colw/2, y + 4*K), (mx + colw/2, b + dn - 2*K)], fill=divcol, width=2*K)
    return bot


def card_glass(cid):
    """1. Frosted glass: a light, see-through white panel over the sky; navy type, orange icons."""
    make, model, year, specs = _specs(cid); im = _base(cid)
    x0, y0, x1, y1 = 130*K, 196*K, 950*K, 452*K; r = 40*K
    _shadow(im, (x0, y0, x1, y1), r, a=60)
    blur = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(26*K)); m = Image.new('L', blur.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, blur.width - 1, blur.height - 1), radius=r, fill=255); im.paste(blur, (x0, y0), m)
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((x0, y0, x1, y1), radius=r, fill=(255, 255, 255, 150), outline=(255, 255, 255, 230), width=3*K)
    im.alpha_composite(ov); d = ImageDraw.Draw(im); cx = W/2*K
    fm = FT(OX8, 24); sp = '  '.join(make); u, dn, w = ink(d, sp, fm); y = y0 + 30*K + u
    d.text((cx, y), sp, font=fm, fill=(90, 110, 135), anchor='ms'); y += dn
    fy = FT(OX8, 28); uy, dy_, wy = ink(d, year, fy); cw, ch = wy + 34*K, uy + dy_ + 20*K; gap = 20*K; sz = 72
    while True:                                                # long names (Sandero Stepway) step down to fit
        fM = FT(OX8, sz); uM, dM, wM = ink(d, model, fM)
        if wM + gap + cw <= (x1 - x0) - 100*K or sz <= 44: break
        sz -= 2
    uM, dM = ink(d, 'Clio', FT(OX8, 72))[:2] if sz < 72 else (uM, dM)    # keep the row height of the 72 size
    xm = cx - (wM + gap + cw)/2; base = y + 16*K + uM
    d.text((xm, base), model, font=fM, fill=NAVY, anchor='ls')
    chx = xm + wM + gap; chy = base - uM/2 - ch/2 + 4*K
    d.rounded_rectangle((chx, chy, chx + cw, chy + ch), radius=ch/2, fill=ORANGE); d.text((chx + cw/2, chy + ch/2), year, font=fy, fill=WHITE, anchor='mm')
    y = base + dM + 24*K
    bot = _spec_row(im, d, specs, y, cx, (x1 - x0) - 80*K, ORANGE, NAVY, (150, 172, 196))
    print(cid, 'glass card', y0//K, '-', y1//K, '| content bottom', round(bot/K))
    return im.convert('RGB')


def card_line(cid):
    """2. Minimal: no box at all - white type straight on the sky, an orange hairline, and the specs as one line of
    white icons and words."""
    make, model, year, specs = _specs(cid); im = _base(cid)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = W/2*K; SH = (8, 26, 55, 200)
    fM = FT(OX8, 96); title = model; uM, dM, wM = ink(d, title, fM)
    fm = FT(OX8, 28); sp = '  '.join(make) + '   ·   ' + year; u, dn, w = ink(d, sp, fm)
    y = 230*K + u
    sd.text((cx, y + 5*K), sp, font=fm, fill=SH, anchor='ms'); d.text((cx, y), sp, font=fm, fill=WHITE, anchor='ms')
    base = y + dn + 22*K + uM
    sd.text((cx, base + 7*K), title, font=fM, fill=SH, anchor='ms'); d.text((cx, base), title, font=fM, fill=WHITE, anchor='ms')
    y = base + dM + 26*K
    d.rounded_rectangle((cx - 60*K, y, cx + 60*K, y + 5*K), radius=3*K, fill=ORANGE + (255,)); y += 5*K + 28*K
    fl = FT(KUFI, 24); isz = 30*K; parts = []
    for ic, lab in specs:
        uu, dd_, ww = ink(d, lab, fl, True); parts.append((ic, lab, uu, dd_, ww))
    gap = 46*K; tot = sum(p_[4] + isz + 10*K for p_ in parts) + gap*3; x = cx + tot/2
    for i, (ic, lab, uu, dd_, ww) in enumerate(parts):
        g = icon(ic, isz, WHITE); gs = icon(ic, isz, (8, 26, 55))
        sh.alpha_composite(gs, (round(x - g.width), round(y + 4*K))); lay.alpha_composite(g, (round(x - g.width), round(y)))
        tx = x - isz - 10*K; b = y + isz/2 + (uu - dd_)/2
        sd.text((tx, b + 4*K), lab, font=fl, fill=SH, anchor='rs', direction='rtl', language='ar')
        d.text((tx, b), lab, font=fl, fill=WHITE, anchor='rs', direction='rtl', language='ar')
        x = tx - ww - gap
        if i < 3: d.ellipse((x + gap/2 - 5*K, y + isz/2 - 5*K, x + gap/2 + 5*K, y + isz/2 + 5*K), fill=ORANGE + (255,))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9*K))); im.alpha_composite(lay)
    print(cid, 'line: top 230 | bottom', round((y + isz)/K))
    return im.convert('RGB')


def card_tag(cid):
    """3. Brand tag: a compact white card with the logo's orange corner, navy type - like our number plate."""
    make, model, year, specs = _specs(cid); im = _base(cid)
    x0, y0, x1, y1 = 170*K, 200*K, 910*K, 446*K; r = 22*K
    _shadow(im, (x0, y0, x1, y1), r, a=110, blur=16, dy=12)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=(255, 255, 255, 250))
    t = 34*K; d.polygon([(x0 + 22*K, y0 + 22*K), (x0 + 22*K + t, y0 + 22*K), (x0 + 22*K, y0 + 22*K + t)], fill=ORANGE)   # logo corner, top left
    cx = W/2*K
    fm = FT(OX8, 24); sp = '  '.join(make); u, dn, w = ink(d, sp, fm); y = y0 + 28*K + u
    d.text((cx, y), sp, font=fm, fill=(120, 135, 155), anchor='ms'); y += dn
    fM = FT(OX8, 70); txt = model; uM, dM, wM = ink(d, txt, fM); fy = FT(OX8, 70); uy, dy_, wy = ink(d, year, fy)
    gap = 22*K; xm = cx - (wM + gap + wy)/2; base = y + 16*K + uM
    d.text((xm, base), txt, font=fM, fill=NAVY, anchor='ls'); d.text((xm + wM + gap, base), year, font=fy, fill=ORANGE, anchor='ls')
    y = base + dM + 20*K
    d.line([(x0 + 60*K, y), (x1 - 60*K, y)], fill=(222, 228, 236), width=2*K); y += 20*K
    bot = _spec_row(im, d, specs, y, cx, (x1 - x0) - 70*K, ORANGE, NAVY, (222, 228, 236), isz=32, fs=21)
    print(cid, 'tag card', y0//K, '-', y1//K, '| content bottom', round(bot/K))
    return im.convert('RGB')


def card_glass2(cid):
    """Glass, refined: a brighter frosted panel with a soft top sheen; make in spaced caps, a large navy model with
    the year chip; the four specs each in its own white tile with the icon in a soft orange circle."""
    make, model, year, specs = _specs(cid); im = _base(cid)
    x0, y0, x1, y1 = 120*K, 184*K, 960*K, 474*K; r = 44*K
    _shadow(im, (x0, y0, x1, y1), r, a=70, blur=22, dy=14)
    blur = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(30*K)); m = Image.new('L', blur.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, blur.width - 1, blur.height - 1), radius=r, fill=255); im.paste(blur, (x0, y0), m)
    ov = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for i in range(ov.height):                                 # frosted white, a little brighter at the top
        od.line([(0, i), (ov.width, i)], fill=(255, 255, 255, int(200 - 45*i/ov.height)))
    ov.putalpha(Image.fromarray((np.asarray(ov.split()[3]).astype(np.float32)*np.asarray(m)/255).astype(np.uint8)))
    im.alpha_composite(ov, (x0, y0))
    ImageDraw.Draw(im).rounded_rectangle((x0, y0, x1, y1), radius=r, outline=(255, 255, 255, 255), width=3*K)
    d = ImageDraw.Draw(im); cx = W/2*K
    fm = FT(OX8, 22); sp = '   '.join(make); u, dn, w = ink(d, sp, fm); y = y0 + 30*K + u
    d.text((cx, y), sp, font=fm, fill=(74, 98, 128), anchor='ms'); y += dn
    fM = FT(OX8, 80); uM, dM, wM = ink(d, model, fM); fy = FT(OX8, 28); uy, dy_, wy = ink(d, year, fy)
    cw, ch = wy + 36*K, uy + dy_ + 22*K; gap = 22*K; xm = cx - (wM + gap + cw)/2; base = y + 16*K + uM
    d.text((xm, base), model, font=fM, fill=NAVY, anchor='ls')
    chx = xm + wM + gap; chy = base - uM/2 - ch/2 + 4*K
    d.rounded_rectangle((chx, chy, chx + cw, chy + ch), radius=ch/2, fill=ORANGE); d.text((chx + cw/2, chy + ch/2), year, font=fy, fill=WHITE, anchor='mm')
    y = base + dM + 24*K
    fl = FT(KUFI, 21); n = 4; g_ = 14*K; dd0 = ImageDraw.Draw(im)
    U = max(ink(dd0, l_, fl, True)[0] for _, l_ in specs); Dn = max(ink(dd0, l_, fl, True)[1] for _, l_ in specs)   # one baseline for all four
    tw = ((x1 - x0) - 2*34*K - (n - 1)*g_)/n; th = 16*K + 42*K + 12*K + U + Dn + 16*K; tx = x1 - 34*K
    for ic, lab in specs:                                      # right to left
        a0 = tx - tw
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((a0, y + 4*K, tx, y + th + 4*K), radius=22*K, fill=(8, 26, 55, 40))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6*K)))
        d = ImageDraw.Draw(im); d.rounded_rectangle((a0, y, tx, y + th), radius=22*K, fill=(255, 255, 255, 255))
        mx = (a0 + tx)/2; cr = 21*K; cy_ = y + 16*K + cr
        d.ellipse((mx - cr, cy_ - cr, mx + cr, cy_ + cr), fill=(253, 235, 224))
        gi = icon(ic, 26*K, ORANGE); im.alpha_composite(gi, (round(mx - gi.width/2), round(cy_ - gi.height/2)))
        d = ImageDraw.Draw(im)
        d.text((mx, cy_ + cr + 12*K + U), lab, font=fl, fill=NAVY, anchor='ms', direction='rtl', language='ar')
        bot = cy_ + cr + 12*K + U + Dn; tx = a0 - g_
    print(cid, 'glass2 card', y0//K, '-', y1//K, '| tiles', round(y/K), '-', round((y + th)/K), '| label bottom', round(bot/K))
    return im.convert('RGB')


STYLES = {'glass2': card_glass2, 'glass': card_glass, 'line': card_line, 'tag': card_tag, 'float': card_float}


if __name__ == '__main__':
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    ids = sys.argv[3].split(',') if len(sys.argv) > 3 else list(CARS)
    styles = sys.argv[4].split(',') if len(sys.argv) > 4 else ['glass']   # glass = the approved card
    for st in styles:
        for cid in ids:
            STYLES[st](cid).save(os.path.join(out, f'fleet-{cid}-{st}.png' if len(styles) > 1 else f'fleet-{cid}.png'), optimize=True)
