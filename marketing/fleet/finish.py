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
    # v3: as v2, nudged right so there is less empty ground beside the rear
    'i20-black-v3': [(210, 1380), (318, 1415), (314, 1448), (208, 1412)],
    'bayon-teal-v3': [(211, 1377), (339, 1412), (335, 1469), (209, 1429)],
    'tiggo-grey-v3': [(210, 1388), (327, 1420), (325, 1470), (209, 1432)],
    'clio5-white-v3': [(205, 1443), (339, 1480), (335, 1534), (203, 1493)],
    'clio6-grey-v3': [(221, 1441), (356, 1475), (353, 1528), (219, 1490)],
    'omoda-grey-v3': [(210, 1400), (334, 1434), (330, 1482), (208, 1447)],
    'i20-red-v3':    [(201, 1360), (319, 1390), (317, 1438), (199, 1407)],
    'sandero-white-v3': [(226, 1381), (350, 1403), (347, 1455), (225, 1431)],
    'megane-grey-v3': [(205, 1437), (335, 1465), (332, 1513), (203, 1483)],
    'omoda-redtrim-v3': [(200, 1416), (330, 1446), (332, 1496), (200, 1471)],
    'egea-blue-v3': [(203, 1408), (331, 1429), (331, 1483), (204, 1453)],
    'taliant-blue-v3': [(215, 1398), (348, 1431), (346, 1477), (214, 1446)],
    'mokka-grey-v3': [(212, 1393), (342, 1420), (344, 1474), (214, 1441)],
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
    a = np.asarray(pl, np.float32); a[..., :3] *= max(0.86, min(1.0, white / 240.0))   # floor: a dark source plate must not darken ours
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
