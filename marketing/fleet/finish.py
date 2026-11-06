"""Fleet album: AI in-scene photos (ai/<car>-scene.png, made in Canva from the i20 shop photo with the car
swapped for the real car photo) get the same sharp CALL & RENT front plate as the i20 and the branded
contact footer, then are saved as <car>-album.jpg."""
import sys
import numpy as np
from PIL import Image, ImageFilter
import album as A

# front-plate corners in each AI scene: TL, TR, BR, BL
PLATES = {
    'bayon-teal':  [(124, 1418), (262, 1458), (258, 1515), (122, 1472)],
    'tiggo-grey':  [(122, 1430), (246, 1466), (245, 1517), (121, 1477)],
    'clio5-white': [(118, 1490), (262, 1530), (258, 1587), (116, 1542)],
    'clio6-grey':  [(134, 1488), (280, 1525), (276, 1582), (132, 1540)],
    'omoda-grey':  [(122, 1443), (256, 1480), (252, 1532), (120, 1493)],
    'i20-black':   [(122, 1415), (238, 1452), (236, 1495), (120, 1458)],
    # v2: car moved slightly back (moveback.py guide -> AI grounding), full natural shadow
    'i20-black-v2': [(155, 1372), (265, 1410), (261, 1445), (153, 1408)],
}

def grow(q, px=2):
    c = np.mean(q, 0)
    return [tuple(c + (np.array(p) - c) * (1 + px / np.linalg.norm(np.array(p) - c))) for p in q]

def put_plate(fr, quad):
    pl = A.plate(); pw, ph = pl.size
    # match the plate white to the light on the AI plate it replaces
    xs = [p[0] for p in quad]; ys = [p[1] for p in quad]
    reg = np.asarray(fr.convert('L').crop((min(xs), min(ys), max(xs), max(ys))), np.float32)
    white = np.percentile(reg, 90)
    a = np.asarray(pl, np.float32); a[..., :3] *= min(1.0, white / 240.0)
    pl = Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA')
    coeff = A.solve_persp(grow(quad), [(0, 0), (pw, 0), (pw, ph), (0, ph)])
    w = pl.transform((A.W, A.H), Image.PERSPECTIVE, coeff, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.6))
    g = np.asarray(w, np.float32)
    g[..., :3] += np.random.default_rng(3).normal(0, 2.5, g.shape[:2] + (1,))     # same grain as the photo
    fr.alpha_composite(Image.fromarray(np.clip(g, 0, 255).astype('uint8'), 'RGBA'))

def finish(name):
    fr = Image.open(f'ai/{name}-scene.png').convert('RGBA').resize((A.W, A.H), Image.LANCZOS)
    put_plate(fr, PLATES[name])
    A.contacts_footer(fr)
    out = f'{name}-album.jpg'
    fr.convert('RGB').save(out, quality=95)
    return out

if __name__ == '__main__':
    for n in (sys.argv[1:] or PLATES):
        print(finish(n))
