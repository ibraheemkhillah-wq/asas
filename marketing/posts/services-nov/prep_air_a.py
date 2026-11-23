"""Airport photo for svc-air-a: the Canva rear three-quarter Chery shot (air-a-raw.jpg, 2160x2700) with
CALL & RENT + TR warped onto its blank rear plate, and the garbled badge lettering on the tailgate painted out.
Writes air-a.jpg.   usage: python3 prep_air_a.py <brand-kit dir>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter1d
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'news')); sys.argv = sys.argv[:2]
import idea_tyre_code as tc, news_carousel as nc

im = Image.open(os.path.join(HERE, 'air-a-raw.jpg')).convert('RGB')

# 1. paint out the fake lettering above the plate (vertical blend of the paint rows above and below)
for x0, x1, y0, y1 in ((282, 425, 1493, 1517), (288, 412, 1478, 1493)):
    a = np.asarray(im).astype(float)
    top = gaussian_filter1d(a[y0-3:y0, x0:x1].mean(0), 4, axis=0); bot = gaussian_filter1d(a[y1:y1+3, x0:x1].mean(0), 4, axis=0)
    fill = a.copy()
    for i, y in enumerate(range(y0, y1)):
        t = (i + .5)/(y1 - y0); fill[y, x0:x1] = (top*(1 - t) + bot*t)*0.85
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rectangle((x0 + 4, y0 + 2, x1 - 4, y1 - 2), fill=255)
    im = Image.composite(Image.fromarray(fill.clip(0, 255).astype('uint8')), im, m.filter(ImageFilter.GaussianBlur(3)))

# 2. plate: TR strip + navy logo, toned to the plate's light, warped onto the measured corners
quad = [(315.5, 1545.5), (395, 1547.5), (387.5, 1588), (309, 1588)]
tone = np.asarray(im).astype(float)[1555:1580, 325:380].mean(axis=(0, 1))/255
pw, ph = 1000, 520; flat = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(flat)
sw = int(pw*0.13); d.rectangle((0, 0, sw, ph), fill=(30, 70, 170, 255))
d.text((sw/2, ph*0.80), 'TR', font=nc.F(tc.OX, 30).real.font_variant(size=92), fill=(240, 242, 250, 255), anchor='ms')
lg = Image.open(nc.LOGO_NAVY).convert('RGBA'); lw = int((pw - sw)*0.82); lh = round(lw*lg.height/lg.width)
if lh > ph*0.7: lh = int(ph*0.7); lw = round(lh*lg.width/lg.height)
flat.alpha_composite(lg.resize((lw, lh), Image.LANCZOS), (sw + (pw - sw - lw)//2, (ph - lh)//2))
arr = np.asarray(flat).astype(float); arr[..., :3] *= tone*1.05; flat = Image.fromarray(np.clip(arr, 0, 255).astype('uint8'))
w = flat.transform(im.size, Image.PERSPECTIVE, tc.perspective_coeffs(quad, [(0, 0), (pw, 0), (pw, ph), (0, ph)]), Image.BICUBIC)
out = im.convert('RGBA'); out.alpha_composite(w.filter(ImageFilter.GaussianBlur(0.5)))
out.convert('RGB').save(os.path.join(HERE, 'air-a.jpg'), quality=95); print('air-a.jpg written')
