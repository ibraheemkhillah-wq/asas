"""CALL & RENT Facebook page assets: profile picture + cover, matching the Instagram avatar.

usage: python3 fb_assets.py <brand-kit dir> <out dir>
"""
import sys, os, math
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE, WHITE, SOFT, F, LT_REG, CT_FONT, SLOGAN, LOGO_WHITE, load_icons, w_lt

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


def skyline(w, h, base, col, k=1.0):
    """Istanbul silhouette: Galata Tower, domes and minarets, drawn flat."""
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((0, base, w, h), fill=col)
    def mosque(cx, r, mh):
        d.pieslice((cx-r, base-r, cx+r, base+r), 180, 360, fill=col)
        d.rectangle((cx-r*1.5, base-r*0.35, cx+r*1.5, base), fill=col)
        for sx in (-1, 1):
            d.pieslice((cx+sx*r*1.15-r*0.45, base-r*0.8, cx+sx*r*1.15+r*0.45, base+r*0.1), 180, 360, fill=col)
        for sx in (-1, 1):
            mx = cx + sx*r*2.0
            d.rectangle((mx-4, base-mh, mx+4, base), fill=col)
            d.polygon([(mx-6, base-mh), (mx+6, base-mh), (mx, base-mh-22)], fill=col)
            d.rectangle((mx-8, base-mh*0.66, mx+8, base-mh*0.66+5), fill=col)
    def galata(cx, th):
        d.rectangle((cx-22, base-th, cx+22, base), fill=col)
        d.rectangle((cx-28, base-th-8, cx+28, base-th+5), fill=col)
        d.polygon([(cx-26, base-th-8), (cx+26, base-th-8), (cx, base-th-64)], fill=col)
    for cx, r, mh in ((170, 58, 150), (520, 78, 190), (1180, 70, 175), (1500, 52, 140)):
        mosque(cx, r*k, mh*k)
    galata(860, 150*k)
    return lay


def cover(out, w=1640, h=624):
    cv = field(w, h, (0.82, 0.0))
    cv.alpha_composite(rays(w, h, (w*1.18, h*0.70), 90, (math.pi*0.93, math.pi*1.16), alpha=(14, 55)))
    sk = skyline(w, h, h-34, (14, 44, 70, 255), k=0.62).filter(ImageFilter.GaussianBlur(0.6))
    fade = Image.new('L', (w, h), 0); fd = ImageDraw.Draw(fade)
    for y in range(h):                                     # skyline fades in toward the bottom edge
        fd.line([(0, y), (w, y)], fill=int(255*np.clip((y-(h-190))/140, 0, 1)*0.9))
    sk.putalpha(Image.fromarray(np.minimum(np.array(sk.getchannel('A')), np.array(fade))))
    cv.alpha_composite(sk)
    d = ImageDraw.Draw(cv); cx = w//2                       # keep everything in the mobile-safe centre
    lg = logo(500); cv.alpha_composite(lg, (cx - lg.width//2, 92))
    fs = F(LT_REG, 34); track = 1.6
    tw = sum(w_lt(c, fs) for c in SLOGAN) + track*(len(SLOGAN)-1); x = cx - tw/2
    for c in SLOGAN:
        d.text((x, 92+lg.height+52), c, font=fs, fill=ORANGE+(255,), anchor='lm'); x += w_lt(c, fs) + track
    # contacts on one line: [wa][call] number  |  [ig][fb] callrenttr
    ic = load_icons(40); fc = F(CT_FONT, 36); y = 92 + lg.height + 128
    groups = [(('wa', 'ph'), '+90 555 034 22 00'), (('ig', 'fb'), 'callrenttr')]
    widths = [2*40 + 10 + 16 + w_lt(t, fc) for _, t in groups]; sep = 56
    x = cx - (sum(widths) + sep)/2
    for gi, (keys, txt) in enumerate(groups):
        for k in keys:
            cv.alpha_composite(ic[k], (round(x), y-20)); x += 50
        d.text((x+6, y+2), txt, font=fc, fill=WHITE+(255,), anchor='lm'); x += 16 + w_lt(txt, fc) - 6
        if gi == 0:
            d.line([(x+sep/2, y-18), (x+sep/2, y+20)], fill=ORANGE+(255,), width=3); x += sep
    cv.convert('RGB').save(out, quality=95); print(out)


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    profile(os.path.join(sys.argv[2], 'fb-profile.png'))
    cover(os.path.join(sys.argv[2], 'fb-cover.png'))
