"""Instagram highlight covers for the four content sections, 2160x2160 (Instagram shows the centre circle).
Section colour as a soft radial field, a fine inner ring, and a Material Symbols (rounded) icon in the middle.
Also writes mockup.png: the covers placed on a profile screenshot (pass its path as the 2nd argument).
usage: python3 highlights.py <out dir> [profile screenshot]"""
import sys, os
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


def cover(col, icon, icol):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); r = np.hypot(xx - S/2, yy - S*0.44)/(S*0.72)
    c = np.array(col, np.float32); light = np.clip(c*1.18 + 18, 0, 255); dark = c*0.78
    t = np.clip(r, 0, 1)[..., None]; px = light*(1 - t) + c*t*1.0
    px = np.where(t > 0.75, px*(1 - (t - 0.75)*0.9) + dark*((t - 0.75)*0.9), px)
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    d = ImageDraw.Draw(im); rr = S*0.405                         # fine ring inside the visible circle
    d.ellipse((S/2 - rr, S/2 - rr, S/2 + rr, S/2 + rr), outline=icol + (90,), width=10)
    ic = Image.open(os.path.join(HERE, 'icons', icon + '.png')).convert('RGBA'); a = ic.split()[3]
    sz = round(S*0.42); a = a.crop(a.getbbox()); k = sz/max(a.size); a = a.resize((round(a.width*k), round(a.height*k)), Image.LANCZOS)
    pos = ((S - a.width)//2, (S - a.height)//2)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 70), (pos[0], pos[1] + 18), a)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    im.paste(icol, pos, a)
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
