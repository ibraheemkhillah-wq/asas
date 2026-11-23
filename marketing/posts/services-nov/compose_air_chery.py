"""Airport photo for svc-air-a: our own Chery Tiggo 8 Pro cutout (../tiggo8-cutout.png, CALL & RENT plate)
set on the empty Canva airport curb (air-empty.jpg), facing right like the curb, graded to the night light,
with a contact shadow and a wet-ground reflection.  Writes air-a.jpg (2160x2700).
usage: python3 compose_air_chery.py <brand-kit dir>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, sys.argv[1])
from brand import LOGO_NAVY

bg = Image.open(os.path.join(HERE, 'air-empty.jpg')).convert('RGBA')
car = Image.open(os.path.join(HERE, '..', 'tiggo8-cutout.png')).convert('RGBA')

# plate logo on the blank front plate (cutout px), then mirror so the car faces right
px0, py0, px1, py1 = 241, 468, 469, 527
A = np.array(car.convert('RGB')).astype(np.float32)
plate = tuple(int(v) for v in A[py0+4:py1-4, px0+6:px1-6].reshape(-1, 3).mean(0))
s = 4; pl = Image.new('RGBA', ((px1-px0)*s, (py1-py0)*s), plate + (255,))
lg = Image.open(LOGO_NAVY).convert('RGBA'); lh = round(pl.height*0.72); lw = round(lh*lg.width/lg.height)
if lw > pl.width*0.86: lw = round(pl.width*0.86); lh = round(lw*lg.height/lg.width)
lg = lg.resize((lw, lh), Image.LANCZOS); k = plate[0]/226; r, g, b, a = lg.split()
lg = Image.merge('RGBA', tuple(c.point(lambda v: int(v*k)) for c in (r, g, b)) + (a,))
pl.alpha_composite(lg, ((pl.width-lw)//2, (pl.height-lh)//2))
car.alpha_composite(pl.resize((px1-px0, py1-py0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5)), (px0, py0))

def mirror_plate(c):
    """mirror the car but keep the plate reading correctly"""
    m = c.transpose(Image.FLIP_LEFT_RIGHT)
    W_ = c.width; box = (W_ - px1, py0, W_ - px0, py1)
    m.paste(c.crop((px0, py0, px1, py1)), box[:2])
    return m
car = mirror_plate(car)

# night grade: darker, cooler shadows, warm terminal light kept in the highlights
rgb = np.asarray(car).astype(np.float32); al = rgb[..., 3:]
c = rgb[..., :3]/255; L = c.mean(-1, keepdims=True)
c = c**1.12*0.80
c = c*(1 - L*0.0) + (np.array([0.02, 0.03, 0.06]))*(1 - L)          # blue ambient in the darks
c[..., 0] *= 1.04; c[..., 2] *= 0.97
car = Image.fromarray(np.concatenate([np.clip(c*255, 0, 255), al], -1).astype(np.uint8), 'RGBA')
bb = car.getbbox(); car = car.crop(bb)

# place: wheels on the curb (units 1080 -> px x2)
cw = 1190; car = car.resize((cw, round(car.height*cw/car.width)), Image.LANCZOS)
cx0 = 1080 - cw//2 + 60; cy1 = 1816; cy0 = cy1 - car.height
out = bg.copy()

# contact shadow
sh = Image.new('RGBA', out.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
d.ellipse((cx0 + 20, cy1 - 60, cx0 + cw - 10, cy1 + 30), fill=(2, 3, 6, 245))
d.rounded_rectangle((cx0 + 120, cy1 - 190, cx0 + cw - 90, cy1 - 10), radius=60, fill=(1, 2, 4, 250))   # under the body
out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
sh = Image.new('RGBA', out.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
al_ = np.asarray(car.split()[3]) > 128
for x0_, x1_ in ((0, cw//3), (cw//3, 2*cw//3), (2*cw//3, cw)):
    cols = np.where(al_[:, x0_:x1_].any(0))[0]
    if not len(cols): continue
    bot = max(np.where(al_[:, x0_ + c_])[0].max() for c_ in cols)
    d.ellipse((cx0 + x0_ + 10, cy0 + bot - 22, cx0 + x1_ - 10, cy0 + bot + 16), fill=(0, 0, 0, 255))
out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))

# reflection on the wet pavement
ref = car.transpose(Image.FLIP_TOP_BOTTOM)
fade = Image.linear_gradient('L').resize(ref.size).point(lambda v: int(max(0, 255 - v*2.2)*0.42))
ra = ref.split()[3]; ref.putalpha(Image.fromarray((np.asarray(ra).astype(np.float32)*np.asarray(fade)/255).astype(np.uint8)))
ref = ref.filter(ImageFilter.GaussianBlur(4))
out.alpha_composite(ref, (cx0, cy1 - 14))

out.alpha_composite(car, (cx0, cy0))
out.convert('RGB').save(os.path.join(HERE, 'air-a.jpg'), quality=95)
print('car box', cx0, cy0, cx0 + cw, cy1)
