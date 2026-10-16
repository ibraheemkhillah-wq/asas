"""CALL & RENT «عدّاد مفتوح» (unlimited km): two separate service posts, rendered at 2160x2700.

usage: python3 okm_posts.py <brand-kit dir> <tiggo cutout png> <out dir>
  1) okm-sign:     Istanbul highway, overhead sign reading OPEN km, our Tiggo 8 underneath
  2) okm-odometer: cockpit view, the instrument display reads OPEN km
Backgrounds: Canva (okm-sign-scene.jpg, okm-odo-scene.jpg).
"""
import sys, os
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import (ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_BOLD, LT_TEXT,
                   LOGO_WHITE, LOGO_NAVY, load_icons, w_ar, w_lt)

HERE = os.path.dirname(os.path.abspath(__file__))
K = 2; W, H = 1080*K, 1350*K
M = 64*K; R_ = W - M
DEEP = (8, 24, 41)


def S(v): return round(v*K)


def shade(cv, bands):
    ys = np.arange(H, dtype=np.float32)
    for f, col in bands:                                    # f gets a 0..∞ ramp; clip before any power
        lay = Image.new('RGBA', (W, H), col+(0,))
        a = np.nan_to_num(np.clip(f(np.clip(ys, 0, None)), 0, 1))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)


def chrome(cv):
    """Logo top-left, «من خدماتنا» badge top-right (navy plate, orange corner)."""
    d = ImageDraw.Draw(cv)
    lg = Image.open(LOGO_WHITE).convert('RGBA'); lw = S(270)
    cv.alpha_composite(lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS), (M - S(6), S(46)))
    fb = F(AR_BOLD, S(26)); bh = S(58); by = S(50); label = 'من خدماتنا'
    bw = w_ar(label, fb) + S(64); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by+bh), radius=S(6), fill=LOGONAVY+(255,), outline=(255, 255, 255, 60), width=S(1))
    d.polygon([(bx, by+bh-S(22)), (bx, by+bh), (bx+S(22), by+bh)], fill=ORANGE+(255,))
    d.text((bx+bw/2, by+bh/2+S(2)), label, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')


def footer(cv, y):
    d = ImageDraw.Draw(cv)
    d.line([(M, y - S(44)), (R_, y - S(44))], fill=ORANGE+(255,), width=S(2))
    ic = load_icons(S(40)); fc = F(CT_FONT, S(31)); x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, y - S(20))); x += S(50)
    d.text((x + S(6), y + S(2)), 'callrenttr', font=fc, fill=WHITE+(255,), anchor='lm')
    t = '+90 555 034 22 00'; tx = R_ - w_lt(t, fc)
    d.text((R_, y + S(2)), t, font=fc, fill=WHITE+(255,), anchor='rm')
    x = tx - S(18) - S(40)
    for k in ('ph', 'wa'):
        cv.alpha_composite(ic[k], (round(x), y - S(20))); x -= S(50)


def headline(cv, y, sub=True):
    d = ImageDraw.Draw(cv)
    f1 = F(AR_BLACK, S(96)); t1 = 'عدّاد'; t2 = 'مفتوح'
    d.text((R_, y), t1, font=f1, fill=WHITE+(255,), anchor='rs', direction='rtl', language='ar')
    d.text((R_ - w_ar(t1, f1) - S(26), y), t2, font=f1, fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
    if sub:
        d.text((R_, y + S(88)), 'سوق بكل اسطنبول على راحتك، بدون حد للمسافة', font=F(AR_BOLD, S(32)),
               fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')
        d.text((R_, y + S(128)), 'مطابق للشروط والأحكام', font=F(AR_BOLD, S(22)),
               fill=(150, 170, 190, 255), anchor='rs', direction='rtl', language='ar')


def plate_logo(car):
    """Our navy logo on the Tiggo's blank plate, matched to the plate's exposure."""
    A = np.array(car.convert('RGB')).astype(np.float32)
    px0, py0, px1, py1 = 241, 468, 469, 527                 # plate box inside the cutout
    plate = tuple(int(v) for v in A[py0+4:py1-4, px0+6:px1-6].reshape(-1, 3).mean(0))
    s = 4; pl = Image.new('RGBA', ((px1-px0)*s, (py1-py0)*s), plate+(255,))
    lg = Image.open(LOGO_NAVY).convert('RGBA')
    lh = round(pl.height*0.72); lw = round(lh*lg.width/lg.height)
    if lw > pl.width*0.86: lw = round(pl.width*0.86); lh = round(lw*lg.height/lg.width)
    lgs = lg.resize((lw, lh), Image.LANCZOS); k = plate[0]/226
    r, g, b, a = lgs.split()
    lgs = Image.merge('RGBA', tuple(c.point(lambda v: int(v*k)) for c in (r, g, b)) + (a,))
    pl.alpha_composite(lgs, ((pl.width-lw)//2, (pl.height-lh)//2))
    car.alpha_composite(pl.resize((px1-px0, py1-py0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5)), (px0, py0))
    return car


def sign_post(cut_path, out):
    cv = Image.open(os.path.join(HERE, 'okm-sign-scene.jpg')).convert('RGBA')
    d = ImageDraw.Draw(cv)
    # repaint the blank gantry sign: Turkish motorway green, white border, ∞ km
    x0, y0, x1, y1 = 438, 473, 1848, 846
    A = np.array(cv.convert('RGB')).astype(np.float32)
    g = tuple(int(v) for v in A[y0+60:y1-60, x0+80:x1-80].reshape(-1, 3).mean(0))
    sign = Image.new('RGBA', (x1-x0, y1-y0), g+(255,)); sd = ImageDraw.Draw(sign)
    sd.rounded_rectangle((14, 14, x1-x0-15, y1-y0-15), radius=22, outline=(236, 240, 236, 255), width=10)
    sh = y1 - y0; cy = sh/2
    fs = F(LT_BOLD, 180); gap = 60                                       # OPEN km: one face, one size, sign white
    tw = w_lt('OPEN', fs) + gap + w_lt('km', fs); gx = (x1-x0)/2 + 70 - tw/2
    sd.text((gx, cy + 10), 'OPEN', font=fs, fill=(240, 244, 240, 255), anchor='lm')
    sd.text((gx + w_lt('OPEN', fs) + gap, cy + 10), 'km', font=fs, fill=(240, 244, 240, 255), anchor='lm')
    # arrow (straight ahead) on the left
    ax = 170; sd.polygon([(ax, cy-120), (ax-70, cy-30), (ax-24, cy-30), (ax-24, cy+120), (ax+24, cy+120), (ax+24, cy-30), (ax+70, cy-30)],
                         fill=(240, 244, 240, 255))
    # light it like the scene: warm from below-left, slight grain and softness
    ys, xs = np.mgrid[0:sh, 0:x1-x0].astype(np.float32)
    light = 0.86 + 0.18*(ys/sh)
    arr = np.array(sign).astype(np.float32); arr[..., :3] = np.clip(arr[..., :3]*light[..., None] + np.random.default_rng(2).normal(0, 2.2, arr[..., :3].shape), 0, 255)
    sign = Image.fromarray(arr.astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(0.8))
    cv.alpha_composite(sign, (x0, y0))
    # car on the road, coming toward us
    car = plate_logo(Image.open(cut_path).convert('RGBA'))
    cw = S(700); car = car.resize((cw, round(car.height*cw/car.width)), Image.LANCZOS)
    cx0 = (W - cw)//2; cy1 = S(1000); cy0 = cy1 - car.height
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((cx0 + S(10), cy1 - S(34), cx0 + cw - S(10), cy1 + S(26)), fill=(0, 0, 0, 210))
    cv.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(S(16))))
    cv.alpha_composite(car, (cx0, cy0))
    shade(cv, [(lambda ys: np.clip(1 - ys/S(260), 0, 1)**1.4*0.55, DEEP), (lambda ys: np.clip((ys - S(960))/S(190), 0, 1)**1.1*0.95, DEEP)])
    chrome(cv)
    headline(cv, S(1088))
    footer(cv, S(1300))
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


def odometer_post(out):
    cv = Image.open(os.path.join(HERE, 'okm-odo-scene.jpg')).convert('RGBA')
    shade(cv, [(lambda ys: np.clip(1 - ys/S(240), 0, 1)**1.4*0.55, DEEP), (lambda ys: np.clip((ys - S(960))/S(190), 0, 1)**1.1*0.94, DEEP)])
    # the display reads like a real cluster odometer line: ODO  OPEN  km, thin white digital type
    cx, cy = W/2, S(722)
    INK = (236, 244, 252); BLUE = (110, 170, 255)
    fv = F('Oxanium-400.ttf', S(118)); fl = F(LT_TEXT, S(30)); fu = F('Oxanium-400.ttf', S(46))
    track = S(6)
    def spaced_w(t, f): return sum(w_lt(c, f) for c in t) + track*(len(t)-1)
    lab, val, unit = 'ODO', 'OPEN', 'km'; g1, g2 = S(34), S(22)
    tw = w_lt(lab, fl) + g1 + spaced_w(val, fv) + g2 + w_lt(unit, fu); x = cx - tw/2
    txt = Image.new('RGBA', (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
    td.text((x, cy + S(18)), lab, font=fl, fill=(150, 172, 196, 255), anchor='ls'); x += w_lt(lab, fl) + g1
    for c in val:
        td.text((x, cy + S(18)), c, font=fv, fill=INK+(255,), anchor='ls'); x += w_lt(c, fv) + track
    x += g2 - track
    td.text((x, cy + S(18)), unit, font=fu, fill=INK+(230,), anchor='ls')
    # thin scale line under the reading, like the cluster's trip bar
    bw = S(420); td.line([(cx - bw/2, cy + S(66)), (cx + bw/2, cy + S(66))], fill=BLUE+(170,), width=S(3))
    halo = Image.new('RGBA', (W, H), BLUE+(0,)); halo.putalpha(txt.getchannel('A').filter(ImageFilter.GaussianBlur(S(14))).point(lambda v: v*55//100))
    cv.alpha_composite(halo); cv.alpha_composite(txt)
    chrome(cv)
    headline(cv, S(1088))
    footer(cv, S(1300))
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    os.makedirs(sys.argv[3], exist_ok=True)
    sign_post(sys.argv[2], os.path.join(sys.argv[3], 'okm-sign-post.png'))
    odometer_post(os.path.join(sys.argv[3], 'okm-odometer-post.png'))
