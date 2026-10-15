"""CALL & RENT Facebook page assets: profile picture + cover, matching the Instagram avatar.

usage: python3 fb_assets.py <brand-kit dir> <out dir>
"""
import sys, os, math
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE, WHITE, SOFT, LOGONAVY, F, LT_REG, LT_TEXT, CT_FONT, SLOGAN, LOGO_WHITE, LOGO_NAVY, load_icons, w_lt

TOP = np.array((36, 124, 166), np.float32)      # lit corner, as on the Instagram avatar
LOW = np.array((22, 66, 100), np.float32)       # deep corner
RAY = (110, 185, 240)


def field(w, h, light=(1.0, 0.0)):
    """Diagonal blue grade, brightest toward `light` (fractions of w, h)."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    lx, ly = light[0]*w, light[1]*h
    t = np.sqrt((xs-lx)**2 + (ys-ly)**2) / math.hypot(w, h)
    t = np.clip(t*1.25, 0, 1)[..., None]
    img = TOP*(1-t) + LOW*t
    img += np.random.default_rng(5).normal(0, 1.6, (h, w, 1))
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')


def rays(w, h, focus, n, spread, seed=3, alpha=(18, 70)):
    """Fine light lines fanning out of one focus point, like the avatar's backdrop."""
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(seed); fx, fy = focus; L = math.hypot(w, h)*1.3
    for i in range(n):
        a = spread[0] + (spread[1]-spread[0])*i/(n-1) + rng.normal(0, 0.004)
        d.line([(fx, fy), (fx + L*math.cos(a), fy + L*math.sin(a))],
               fill=RAY+(int(rng.uniform(*alpha)),), width=1 if rng.random() < 0.75 else 2)
    return lay


def logo(width):
    lg = Image.open(LOGO_WHITE).convert('RGBA')
    return lg.resize((width, round(width*lg.height/lg.width)), Image.LANCZOS)


def profile(out, S=1080):
    cv = field(S, S, (0.95, 0.05))
    cv.alpha_composite(rays(S, S, (S*1.08, S*0.62), 70, (math.pi*0.93, math.pi*1.30)))
    lg = logo(round(S*0.80))                               # stays inside the circular crop
    cv.alpha_composite(lg, ((S-lg.width)//2, (S-lg.height)//2 + round(S*0.01)))
    cv.convert('RGB').save(out, quality=95); print(out)


def navy_icon(im):
    """White glyph icons -> navy glyphs on white (same mapping as the light news theme)."""
    a = np.array(im).astype(np.float32); L = a[..., :3].mean(2, keepdims=True)/255
    a[..., :3] = np.array(LOGONAVY, np.float32)*L + 255*(1-L)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def cover(out, w=1640, h=624):
    """Clean light cover: navy logo, slogan, contacts. No artwork in the background."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xs-w/2)/w)**2 + ((ys-h*0.45)/h)**2)
    g = np.clip(r/0.75, 0, 1)[..., None]
    bg = np.array((255, 255, 255), np.float32)*(1-g) + np.array((228, 236, 243), np.float32)*g
    cv = Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(cv); cx = w//2                       # everything in the mobile-safe centre
    lg = Image.open(LOGO_NAVY).convert('RGBA'); lw = 520
    lg = lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS)
    top = 128; cv.alpha_composite(lg, (cx - lw//2, top))
    # slogan: bigger, navy, with orange rules either side
    fs = F(LT_TEXT, 46); track = 1.2; sy = top + lg.height + 62
    tw = sum(w_lt(c, fs) for c in SLOGAN) + track*(len(SLOGAN)-1); x = cx - tw/2
    for c in SLOGAN:
        d.text((x, sy), c, font=fs, fill=LOGONAVY+(255,), anchor='lm'); x += w_lt(c, fs) + track
    for sx in (-1, 1):
        x0 = cx + sx*(tw/2 + 28); d.line([(x0, sy), (x0 + sx*70, sy)], fill=ORANGE+(255,), width=4)
    # contacts on one line: [wa][call] number  |  [ig][fb] callrenttr
    ic = {k: navy_icon(v) for k, v in load_icons(40).items()}; fc = F(CT_FONT, 38); y = sy + 92
    groups = [(('wa', 'ph'), '+90 555 034 22 00'), (('ig', 'fb'), 'callrenttr')]
    widths = [2*40 + 10 + 16 + w_lt(t, fc) for _, t in groups]; sep = 60
    x = cx - (sum(widths) + sep)/2
    for gi, (keys, txt) in enumerate(groups):
        for k in keys:
            cv.alpha_composite(ic[k], (round(x), y-20)); x += 50
        d.text((x+6, y+2), txt, font=fc, fill=LOGONAVY+(255,), anchor='lm'); x += 16 + w_lt(txt, fc) - 6
        if gi == 0:
            d.line([(x+sep/2, y-20), (x+sep/2, y+22)], fill=ORANGE+(255,), width=3); x += sep
    cv.convert('RGB').save(out, quality=95); print(out)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    profile(os.path.join(sys.argv[2], 'fb-profile.png'))
    cover(os.path.join(sys.argv[2], 'fb-cover.png'))
