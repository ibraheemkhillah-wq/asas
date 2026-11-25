"""Instagram highlight covers for the four content sections, 2160x2160 (Instagram shows the centre circle).
Section colour as a soft radial field, a fine inner ring, and a Material Symbols (rounded) icon in the middle.
Also writes mockup.png: the covers placed on a profile screenshot (pass its path as the 2nd argument).
usage: python3 highlights.py <out dir> [profile screenshot]"""
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


def cover(col, icon, icol):
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


def mockup(shot, covers, out):
    im = Image.open(shot).convert('RGB'); d = ImageDraw.Draw(im)
    xs = [384, 630, 876, 1122]; cy = 1259; R = 75
    f = ImageFont.truetype(os.path.join(HERE, '..', 'brand-kit', 'fonts', 'Tajawal-Regular.ttf'), 38)
    for x, (name, label, *_), cv in zip(xs, SECTIONS, covers):
        d.rectangle((x - 123, cy - R - 2, x + 123, cy + R + 2), fill=(255, 255, 255))
        d.ellipse((x - 96, cy - 96, x + 96, cy + 96), fill=(219, 222, 228)); d.ellipse((x - 88, cy - 88, x + 88, cy + 88), fill=(255, 255, 255))
        m = Image.new('L', (4*R, 4*R), 0); ImageDraw.Draw(m).ellipse((0, 0, 4*R, 4*R), fill=255); m = m.resize((2*R, 2*R), Image.LANCZOS)
        im.paste(cv.resize((2*R, 2*R), Image.LANCZOS), (x - R, cy - R), m)
        d.rectangle((x - 123, 1360, x + 123, 1425), fill=(255, 255, 255))
        d.text((x, 1400), label, font=f, fill=(20, 20, 20), anchor='ms', direction='rtl', language='ar')
    im.save(out)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); covers = []
    for name, label, col, icon, icol in SECTIONS:
        cv = cover(col, icon, icol); cv.save(os.path.join(out, f'highlight-{name}.png'), optimize=True); covers.append(cv)
    if len(sys.argv) > 2: mockup(sys.argv[2], covers, os.path.join(out, 'mockup.png'))
    print('done')
