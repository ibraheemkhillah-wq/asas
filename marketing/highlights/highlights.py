"""Instagram highlight covers for the four content sections, 2160x2160 (Instagram shows the centre circle).
Section colour as a soft radial field, a fine inner ring, and a Material Symbols (rounded) icon in the middle.
Also writes mockup.png: the covers placed on a profile screenshot (pass its path as the 2nd argument).
usage: python3 highlights.py <out dir> [profile screenshot] [styles: medallion,field,split]"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
S = 2160
NAVY = (31, 59, 95)
SECTIONS = [   # file, label, colour, icon, icon colour
    ('offer', 'وفّر معنا', (200, 30, 45), 'sell', (255, 255, 255)),
    ('care', 'اعتنِ بسيارتك', (22, 138, 128), 'build', (255, 255, 255)),
    ('idea', 'عندك فكرة', (46, 104, 150), 'lightbulb', (255, 255, 255)),
    ('news', 'أخبار السيارات', (244, 141, 87), 'newspaper', NAVY),
]


TOP, BOT = (33, 120, 155), (30, 62, 96)            # the profile picture's teal-blue to navy


def backdrop(seed=1):
    """The profile picture's field: diagonal teal-to-navy gradient with a fan of fine light-blue lines."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    t = np.clip(((S - xx)*0.35 + yy)/(S*1.25), 0, 1)[..., None]
    px = np.array(TOP, np.float32)*(1 - t) + np.array(BOT, np.float32)*t
    im = Image.fromarray(px.astype(np.uint8), 'RGB').convert('RGBA')
    rng = np.random.default_rng(seed); lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fx, fy = S*1.02, S*0.70
    for ang in np.concatenate([np.linspace(196, 232, 46), np.linspace(160, 195, 26)]):
        ang += rng.normal(0, 0.6); r0, r1 = S*rng.uniform(0.15, 0.45), S*rng.uniform(0.9, 1.4)
        a_ = math.radians(ang); al = int(rng.uniform(110, 220) if ang > 196 else rng.uniform(60, 130))
        d.line([(fx + r0*math.cos(a_), fy + r0*math.sin(a_)), (fx + r1*math.cos(a_), fy + r1*math.sin(a_))],
               fill=(60, 160, 240, al), width=int(rng.choice([3, 4, 5, 6])))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))
    return im


def cover_medallion(col, icon, icol):
    im = backdrop()
    # a medallion in the section colour: soft glow, gradient disc, fine white rim
    R = S*0.355; cx = cy = S/2
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - R*1.12, cy - R*1.12, cx + R*1.12, cy + R*1.12), fill=col + (150,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70)))
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    tt = np.clip(((xx - (cx - R)) + (yy - (cy - R)))/(4*R), 0, 1)[..., None]
    c = np.array(col, np.float32); disc = np.clip(c*1.22 + 14, 0, 255)*(1 - tt) + c*0.80*tt
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=255)
    im.paste(Image.fromarray(disc.astype(np.uint8), 'RGB'), (0, 0), m)
    d = ImageDraw.Draw(im); w = 14
    d.ellipse((cx - R - w*2.2, cy - R - w*2.2, cx + R + w*2.2, cy + R + w*2.2), outline=(255, 255, 255, 230), width=w)
    ic = Image.open(os.path.join(HERE, 'icons', icon + '.png')).convert('RGBA'); a = ic.split()[3]
    sz = round(S*0.34); a = a.crop(a.getbbox()); k = sz/max(a.size); a = a.resize((round(a.width*k), round(a.height*k)), Image.LANCZOS)
    pos = ((S - a.width)//2, (S - a.height)//2)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (pos[0], pos[1] + 16), a)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    im.paste(icol, pos, a)
    # the logo's corner: a small right triangle in the section colour, tucked under the icon's lower left

    return im.convert('RGB')


def fan(seed=1, col=(60, 160, 240), k=1.0):
    rng = np.random.default_rng(seed); lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fx, fy = S*1.02, S*0.70
    for ang in np.concatenate([np.linspace(196, 232, 46), np.linspace(160, 195, 26)]):
        ang += rng.normal(0, 0.6); r0, r1 = S*rng.uniform(0.15, 0.45), S*rng.uniform(0.9, 1.4)
        a_ = math.radians(ang); al = int((rng.uniform(110, 220) if ang > 196 else rng.uniform(60, 130))*k)
        d.line([(fx + r0*math.cos(a_), fy + r0*math.sin(a_)), (fx + r1*math.cos(a_), fy + r1*math.sin(a_))],
               fill=col + (min(255, al),), width=int(rng.choice([3, 4, 5, 6])))
    return lay.filter(ImageFilter.GaussianBlur(0.8))


def put_icon(im, icon, icol, frac=0.40):
    ic = Image.open(os.path.join(HERE, 'icons', icon + '.png')).convert('RGBA'); a = ic.split()[3]
    sz = round(S*frac); a = a.crop(a.getbbox()); k = sz/max(a.size); a = a.resize((round(a.width*k), round(a.height*k)), Image.LANCZOS)
    pos = ((S - a.width)//2, (S - a.height)//2)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 100), (pos[0], pos[1] + 18), a)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26))); im.paste(icol, pos, a)


def cover_field(col, icon, icol):
    """The section colour fills the cover, shaded like the profile picture (light top, deep toward navy at the bottom),
    with the same fan of fine lines in a lighter tint; a fine white ring and a white icon."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    t = np.clip(((S - xx)*0.35 + yy)/(S*1.25), 0, 1)[..., None]
    c = np.array(col, np.float32); top = np.clip(c*1.16 + 12, 0, 255); bot = c*0.74
    im = Image.fromarray((top*(1 - t) + bot*t).astype(np.uint8), 'RGB').convert('RGBA')
    tint = tuple(int(min(255, v*0.5 + 150)) for v in col)
    im.alpha_composite(fan(col=tint, k=0.55))
    rr = S*0.40; ImageDraw.Draw(im).ellipse((S/2 - rr, S/2 - rr, S/2 + rr, S/2 + rr), outline=(255, 255, 255, 150), width=12)
    put_icon(im, icon, (255, 255, 255) if icol == (255, 255, 255) else icol, 0.38)
    return im.convert('RGB')


def cover_split(col, icon, icol):
    """Brand navy backdrop; a wide band of the section colour sweeps across it along the logo's line direction."""
    im = backdrop()
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = ((xx - S/2)*math.cos(math.radians(-32)) + (yy - S/2)*math.sin(math.radians(-32)))
    v = (-(xx - S/2)*math.sin(math.radians(-32)) + (yy - S/2)*math.cos(math.radians(-32)))
    band = np.clip(1 - np.abs(v)/(S*0.25), 0, 1)**0.6
    c = np.array(col, np.float32); tt = np.clip((u + S/2)/S, 0, 1)[..., None]
    bc = np.clip(c*1.2 + 12, 0, 255)*(1 - tt) + c*0.85*tt
    lay = Image.fromarray(np.dstack([bc, (band*235)[..., None]]).astype(np.uint8), 'RGBA')
    im.alpha_composite(lay)
    im.alpha_composite(fan(col=(255, 255, 255), k=0.18))
    put_icon(im, icon, icol, 0.38)
    return im.convert('RGB')


def cover_inverse(col, icon, icol):
    """The medallion inverted: the section colour (shaded, with the fine-line fan) fills the outside, and the brand's
    teal-navy field sits in the framed disc with a white icon."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    t = np.clip(((S - xx)*0.35 + yy)/(S*1.25), 0, 1)[..., None]
    c = np.array(col, np.float32); top = np.clip(c*1.16 + 12, 0, 255); bot = c*0.74
    im = Image.fromarray((top*(1 - t) + bot*t).astype(np.uint8), 'RGB').convert('RGBA')
    im.alpha_composite(fan(col=tuple(int(min(255, v*0.5 + 150)) for v in col), k=0.6))
    R = S*0.355; cx = cy = S/2
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - R*1.1, cy - R*1.05, cx + R*1.1, cy + R*1.2), fill=(10, 20, 35, 120))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=255)
    im.paste(backdrop().convert('RGB'), (0, 0), m)
    w = 14; ImageDraw.Draw(im).ellipse((cx - R - w*2.2, cy - R - w*2.2, cx + R + w*2.2, cy + R + w*2.2), outline=(255, 255, 255, 235), width=w)
    put_icon(im, icon, (255, 255, 255), 0.34)
    return im.convert('RGB')


def cover_ring(col, icon, icol):
    """Brand teal-navy field throughout; the section colour is a bold ring round the centre disc (soft glow,
    light-to-deep gradient, fine white rims), white icon in the middle."""
    im = backdrop(); cx = cy = S/2; Ro, Ri = S*0.40, S*0.335
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - Ro*1.05, cy - Ro*1.05, cx + Ro*1.05, cy + Ro*1.05), outline=col + (170,), width=int(S*0.06))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(45)))
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); rr = np.hypot(xx - cx, yy - cy)
    tt = np.clip(((xx - (cx - Ro)) + (yy - (cy - Ro)))/(4*Ro), 0, 1)[..., None]
    c = np.array(col, np.float32); ringc = np.clip(c*1.25 + 16, 0, 255)*(1 - tt) + c*0.78*tt
    m = Image.fromarray(((rr <= Ro) & (rr >= Ri)).astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(1.2))
    im.paste(Image.fromarray(ringc.astype(np.uint8), 'RGB'), (0, 0), m)
    d = ImageDraw.Draw(im)
    d.ellipse((cx - Ro, cy - Ro, cx + Ro, cy + Ro), outline=(255, 255, 255, 200), width=8)
    d.ellipse((cx - Ri, cy - Ri, cx + Ri, cy + Ri), outline=(255, 255, 255, 200), width=8)
    put_icon(im, icon, (255, 255, 255), 0.32)
    return im.convert('RGB')


def cover_gauge(col, icon, icol):
    """A dashboard gauge: brand teal-navy field, the section colour as a glowing 270-degree arc (light to full),
    fine white tick marks round it like a speedometer, white icon in the middle."""
    im = backdrop(); cx = cy = S/2; R = S*0.37; wd = int(S*0.055)
    a0, a1 = 135, 405                                          # PIL degrees, clockwise from 3 o'clock; gap at the bottom
    box = (cx - R, cy - R, cx + R, cy + R)
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).arc(box, a0, a1, fill=col + (200,), width=int(wd*1.6))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    ImageDraw.Draw(im).arc(box, a0, a1, fill=(255, 255, 255, 38), width=wd)          # faint track
    c = np.array(col, np.float32); lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    n = 90
    for i in range(n):                                         # the arc, lightening along its sweep
        t = i/(n - 1); cc = np.clip(c*(0.85 + 0.45*t) + 22*t, 0, 255).astype(int)
        s_ = a0 + (a1 - a0)*i/n; e_ = a0 + (a1 - a0)*(i + 1.6)/n
        ld.arc(box, s_, min(e_, a1), fill=tuple(cc) + (255,), width=wd)
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im); rt0, rt1, rt2 = R + wd*0.95, R + wd*1.55, R + wd*1.9
    for k in range(28):                                        # speedometer ticks just outside the arc
        ang = math.radians(a0 + (a1 - a0)*k/27); long_ = k % 3 == 0
        r1 = rt2 if long_ else rt1
        d.line([(cx + rt0*math.cos(ang), cy + rt0*math.sin(ang)), (cx + r1*math.cos(ang), cy + r1*math.sin(ang))],
               fill=(255, 255, 255, 230 if long_ else 150), width=10 if long_ else 6)
    ang = math.radians(a1); d.ellipse((cx + R*math.cos(ang) - wd*0.42, cy + R*math.sin(ang) - wd*0.42,
                                       cx + R*math.cos(ang) + wd*0.42, cy + R*math.sin(ang) + wd*0.42), fill=(255, 255, 255, 255))
    put_icon(im, icon, (255, 255, 255), 0.30)
    return im.convert('RGB')


def cover_corner(col, icon, icol):
    """The logo's corner: brand teal-navy field, and the section colour fills the lower-left segment, cut at 45 degrees
    like the orange corner under the logo's R, with a fine white edge; white icon a little above centre."""
    im = backdrop(); yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    k = S*0.30                                                 # cut line: y - x = k  (45 degrees, lower-left side coloured)
    side = (yy - xx - k)/math.sqrt(2)
    c = np.array(col, np.float32); tt = np.clip((yy - xx - k)/(S*0.9), 0, 1)[..., None]
    fill = np.clip(c*1.2 + 14, 0, 255)*(1 - tt) + c*0.78*tt
    m = Image.fromarray((np.clip(side/1.5 + 0.5, 0, 1)*255).astype(np.uint8))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(Image.fromarray((np.clip((side + 60)/60, 0, 1)*110).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30)))
    im.alpha_composite(sh)
    lay = Image.fromarray(fill.astype(np.uint8), 'RGB').convert('RGBA'); lay.alpha_composite(fan(col=tuple(int(min(255, v*0.5 + 150)) for v in col), k=0.35))
    im.paste(lay.convert('RGB'), (0, 0), m)
    d = ImageDraw.Draw(im); L = S*1.5
    d.line([(-L, -L + k), (L, L + k)], fill=(255, 255, 255, 220), width=12)
    ic = Image.open(os.path.join(HERE, 'icons', icon + '.png')).convert('RGBA'); a = ic.split()[3]
    sz = round(S*0.34); a = a.crop(a.getbbox()); kk = sz/max(a.size); a = a.resize((round(a.width*kk), round(a.height*kk)), Image.LANCZOS)
    pos = (round(S*0.56 - a.width/2), round(S*0.42 - a.height/2))
    shd = Image.new('RGBA', im.size, (0, 0, 0, 0)); shd.paste((0, 0, 0, 100), (pos[0], pos[1] + 18), a)
    im.alpha_composite(shd.filter(ImageFilter.GaussianBlur(26))); im.paste((255, 255, 255), pos, a)
    return im.convert('RGB')


STYLES = {'corner': cover_corner, 'gauge': cover_gauge, 'ring': cover_ring, 'inverse': cover_inverse, 'medallion': cover_medallion, 'field': cover_field, 'split': cover_split}


def mockup(shot, covers, out, xs=(398, 644, 890, 1136), cy=1625, ly=1765):
    im = Image.open(shot).convert('RGB'); d = ImageDraw.Draw(im); R = 75
    f = ImageFont.truetype(os.path.join(HERE, '..', 'brand-kit', 'fonts', 'Tajawal-Regular.ttf'), 38)
    for x, (name, label, *_), cv in zip(xs, SECTIONS, covers):
        d.rectangle((x - 123, cy - R - 2, x + 123, cy + R + 2), fill=(255, 255, 255))
        d.ellipse((x - 96, cy - 96, x + 96, cy + 96), fill=(219, 222, 228)); d.ellipse((x - 88, cy - 88, x + 88, cy + 88), fill=(255, 255, 255))
        m = Image.new('L', (4*R, 4*R), 0); ImageDraw.Draw(m).ellipse((0, 0, 4*R, 4*R), fill=255); m = m.resize((2*R, 2*R), Image.LANCZOS)
        im.paste(cv.resize((2*R, 2*R), Image.LANCZOS), (x - R, cy - R), m)
        d.rectangle((x - 123, ly - 40, x + 123, ly + 25), fill=(255, 255, 255))
        d.text((x, ly), label, font=f, fill=(20, 20, 20), anchor='ms', direction='rtl', language='ar')
    im.save(out)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    styles = sys.argv[3].split(',') if len(sys.argv) > 3 else ['medallion']
    for st in styles:
        covers = []
        for name, label, col, icon, icol in SECTIONS:
            cv = STYLES[st](col, icon, icol); cv.save(os.path.join(out, f'highlight-{st}-{name}.png'), optimize=True); covers.append(cv)
        if len(sys.argv) > 2: mockup(sys.argv[2], covers, os.path.join(out, f'mockup-{st}.png'))
    print('done')
