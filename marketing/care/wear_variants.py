"""Make four worn versions of the Canva tread photo (wear-tread.png): the bald parts are the same rubber with
its grooves filled and polished (blurred, slightly lighter and greyer), feathered into the intact tread.

usage: python3 wear_variants.py   -> wear-centre.png, wear-edges.png, wear-side.png, wear-cupping.png
"""
import os
from PIL import Image, ImageFilter
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, 'wear-tread.png')).convert('RGBA')
a = np.asarray(src).astype(np.float32); h, w = a.shape[:2]; alpha = a[..., 3:]
rgb = a[..., :3]
smooth = np.asarray(src.convert('RGB').filter(ImageFilter.GaussianBlur(26)), np.float32)
L = smooth.mean(2, keepdims=True)
bald = L*0.5 + 74 + (smooth - L)*0.3                        # flat grey worn rubber with the photo's own shading
g0 = np.random.default_rng(3).normal(0, 1, (h, w)).astype(np.float32)
grain = np.asarray(Image.fromarray(((g0 - g0.min())/(g0.max() - g0.min())*255).astype(np.uint8)).filter(ImageFilter.BoxBlur(1)), np.float32)[..., None]
grain = (grain - grain.mean())*0.35                           # fine abraded rubber texture
bald = bald + grain
x = np.linspace(0, 1, w)[None, :, None]; y = np.linspace(0, 1, h)[:, None, None]
# tread face spans roughly 0.06-0.94 of the width
def band(c, half, soft=0.05):
    return np.clip((half - np.abs(x - c))/soft, 0, 1)
masks = {
 'centre': band(0.5, 0.17),
 'edges': np.maximum(band(0.12, 0.11), band(0.88, 0.11)),
 'side': np.clip((0.46 - x)/0.12, 0, 1),
}
rng = np.random.default_rng(7); cup = np.zeros((h, w, 1), np.float32)
for cy in np.cumsum(rng.uniform(0.09, 0.16, 12)):
    if cy > 0.95: break
    cx = rng.choice([0.28, 0.5, 0.72]) + rng.uniform(-0.06, 0.06); r = rng.uniform(0.035, 0.06)
    cup = np.maximum(cup, np.clip(1 - np.sqrt(((x - cx)/0.24)**2 + ((y - cy)/r)**2), 0, 1)**0.5)
masks['cupping'] = np.clip(cup*1.6, 0, 1)
for name, m in masks.items():
    m = np.asarray(Image.fromarray((m[..., 0]*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None]/255*0.97
    out = rgb*(1 - m) + (bald*0.82 + rgb*0.18)*m              # a ghost of the old grooves stays visible
    Image.fromarray(np.concatenate([np.clip(out, 0, 255), alpha], 2).astype(np.uint8), 'RGBA').save(os.path.join(HERE, f'wear-{name}.png'), optimize=True)
    print(name)
