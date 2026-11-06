"""Predict where a car's front plate lands after moveback.py, then draw it on a crop to check."""
import sys
import numpy as np
from PIL import Image, ImageDraw
import finish as F, moveback as M

def predict(name, quad):
    a = np.asarray(Image.open(f'ai/{name}-cut.png'))[..., 3]
    xs = np.nonzero(a > 128)[1]; cx = (xs.min() + xs.max()) / 2
    return [(round(cx + (x - cx) * M.S + M.DX), round(M.HORIZON + (y - M.HORIZON) * M.S)) for x, y in quad]

if __name__ == '__main__':
    name, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
    base = {'i20-red': [(113, 1400), (241, 1433), (239, 1485), (111, 1451)]}.get(name) or F.PLATES[name]
    q = predict(name, base); print(q)
    im = Image.open(scene).convert('RGB'); x0, y0 = min(p[0] for p in q) - 50, min(p[1] for p in q) - 50
    c = im.crop((x0, y0, x0 + 260, y0 + 180)); d = ImageDraw.Draw(c)
    d.polygon([(x - x0, y - y0) for x, y in q], outline=(255, 0, 0))
    c.resize((520, 360)).save(out)
