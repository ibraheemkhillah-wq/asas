"""Move a car cut-out (ai/<car>-cut.png, cut from its AI scene) slightly back on the empty shop photo
and give it a full, soft sunlight shadow. Output: ai/<car>-moved.png (scene without footer).
Moving back on the ground plane = scaling about a point on the horizon."""
import sys
import numpy as np
from PIL import Image, ImageFilter

HORIZON = 900          # rough eye-level line in the shop photo
S = 0.92               # 'a little further away'

def squash(mask, y0, f, dx=0, dy=0):
    """flatten a mask vertically about line y0 (factor f) and shift it - a cheap ground projection"""
    w, h = mask.size
    m = mask.transform((w, h), Image.AFFINE, (1, 0, -dx, 0, 1 / f, y0 - y0 / f - dy / f), resample=Image.BILINEAR)
    return m

def build(name, bg='shop-empty.png'):
    car = Image.open(f'ai/{name}-cut.png').convert('RGBA')
    W, H = car.size
    a = np.asarray(car)[..., 3]
    ys, xs = np.nonzero(a > 128)
    cx = (xs.min() + xs.max()) / 2
    nw, nh = int(W * S), int(H * S)
    small = car.resize((nw, nh), Image.LANCZOS)
    ox = int(round(cx - cx * S)); oy = int(round(HORIZON - HORIZON * S))
    moved = Image.new('RGBA', (W, H), (0, 0, 0, 0)); moved.alpha_composite(small, (ox, oy))
    alpha = moved.getchannel('A')
    bottom = int(np.nonzero(np.asarray(alpha).max(1) > 128)[0].max())

    scene = Image.open(bg).convert('RGB').resize((W, H), Image.LANCZOS)
    s = np.asarray(scene, np.float32)
    # 1) broad cast shadow, falling toward the camera and a little to the left (sun behind-right)
    cast = squash(alpha, bottom, 0.30, dx=-55, dy=28).filter(ImageFilter.GaussianBlur(22))
    # 2) ambient occlusion right under the body
    ao = squash(alpha, bottom, 0.10, dy=4).filter(ImageFilter.GaussianBlur(7))
    c = np.asarray(cast, np.float32)[..., None] / 255; o = np.asarray(ao, np.float32)[..., None] / 255
    s *= (1 - 0.50 * c); s *= (1 - 0.60 * o)
    s[..., 2:] *= 1 + 0.04 * c[..., :1]            # shadows on sunny stone are a touch blue
    out = Image.fromarray(np.clip(s, 0, 255).astype('uint8')).convert('RGBA')
    out.alpha_composite(moved)
    out.save(f'ai/{name}-moved.png')
    return f'ai/{name}-moved.png', bottom

if __name__ == '__main__':
    for n in sys.argv[1:]:
        print(build(n))
