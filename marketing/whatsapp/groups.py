"""WhatsApp group icons for the internal teams: the white CALL & RENT logo on the profile picture's field
(diagonal gradient + fan of fine lines), one colour per team. 2160x2160; the logo sits inside the circle WhatsApp shows.
usage: python3 groups.py <brand-kit dir> <out dir>"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
EN = {'operations': 'OPERATIONS', 'bookings': 'BOOKINGS', 'shifts': 'SHIFTS', 'maintenance': 'MAINTENANCE', 'extensions': 'EXTENSIONS'}
S = 2160
GROUPS = [   # file, name, top colour, bottom colour, line colour  (English label = EN below)
    ('operations', 'قسم العمليات', (226, 164, 44), (150, 84, 12), (255, 222, 140)),   # gold-amber
    ('bookings', 'الحجوزات', (24, 140, 120), (12, 70, 66), (80, 220, 190)),
    ('shifts', 'المناوبات', (92, 70, 160), (40, 30, 86), (160, 140, 255)),
    ('maintenance', 'الصيانات', (196, 52, 52), (96, 20, 30), (255, 130, 120)),
    ('extensions', 'تمديد العقود', (196, 48, 128), (88, 18, 64), (255, 150, 210)),   # magenta
]


def field(top, bot, line, seed=1):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    t = np.clip(((S - xx)*0.35 + yy)/(S*1.25), 0, 1)[..., None]
    im = Image.fromarray((np.array(top, np.float32)*(1 - t) + np.array(bot, np.float32)*t).astype(np.uint8), 'RGB').convert('RGBA')
    rng = np.random.default_rng(seed); lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fx, fy = S*1.02, S*0.70
    for ang in np.concatenate([np.linspace(196, 232, 46), np.linspace(160, 195, 26)]):
        ang += rng.normal(0, 0.6); r0, r1 = S*rng.uniform(0.15, 0.45), S*rng.uniform(0.9, 1.4); a = math.radians(ang)
        al = int(rng.uniform(80, 170) if ang > 196 else rng.uniform(45, 100))
        d.line([(fx + r0*math.cos(a), fy + r0*math.sin(a)), (fx + r1*math.cos(a), fy + r1*math.sin(a))], fill=line + (al,), width=int(rng.choice([3, 4, 5, 6])))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))
    return im


if __name__ == '__main__':
    kit, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    lg = Image.open(os.path.join(kit, 'logo', 'callrent-logo-white.png')).convert('RGBA'); lg = lg.crop(lg.getbbox())
    lw = round(S*0.60); lg = lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS)
    for name, label, top, bot, line in GROUPS:
        im = field(top, bot, line)
        pos = ((S - lg.width)//2, round(S*0.43 - lg.height/2))
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (pos[0], pos[1] + 16), lg.split()[3])
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24))); im.alpha_composite(lg, pos)
        f = ImageFont.truetype(os.path.join(kit, 'fonts', 'Oxanium-800.ttf'), 150); t = ' '.join(EN[name])
        d = ImageDraw.Draw(im); l, tp, r, b = d.textbbox((0, 0), t, font=f, anchor='ls'); y = pos[1] + lg.height + 150 - tp
        while r - l > S*0.70:                                  # stay inside the circle
            f = f.font_variant(size=f.size - 4); l, tp, r, b = d.textbbox((0, 0), t, font=f, anchor='ls')
        ln = Image.new('RGBA', im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(ln)
        ld.text((S/2, y + 10), t, font=f, fill=(0, 0, 0, 110), anchor='ms'); im.alpha_composite(ln.filter(ImageFilter.GaussianBlur(14)))
        d = ImageDraw.Draw(im); d.text((S/2, y), t, font=f, fill=(255, 255, 255), anchor='ms')
        d.rounded_rectangle((S/2 - 90, pos[1] + lg.height + 66, S/2 + 90, pos[1] + lg.height + 78), radius=6, fill=(255, 255, 255, 200))
        im.convert('RGB').save(os.path.join(out, f'group-{name}.png'), optimize=True)
    print('done')
