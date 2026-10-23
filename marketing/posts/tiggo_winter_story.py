"""«وفّر معنا»: Chery Tiggo 8 Pro winter offer — STORY of the approved post (model A, snowy Istanbul), 2160x3840.

usage: python3 tiggo_winter_story.py <brand-kit dir> <out.png>
Reuses tiggo_winter.py helpers with the canvas height switched to 1920 units. The post background is placed
lower and the snowy sky above it is continued from its own top rows, so the type gets more room and size.
Instagram covers roughly the top 200 and bottom 200 units of a story; nothing important sits there.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tiggo_winter as tw
from tiggo_winter import S, K, W, M, R_, F, AR_BLACK, AR_BOLD, O, N, Wh, OX, OX6, MODEL, box, ar, lt, spaced, veil, plate_logo, footer, dates_line
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

tw.H = H = 1920*K
BG, PLATE, BG_TOP, SC = 'tiggo-winter-a-istanbul-snowy-light.jpg', (794, 2338), 200, 1.12   # bg top edge (units), zoom


def background():
    im = plate_logo(Image.open(os.path.join(HERE, BG)).convert('RGB').resize((W, 1350*K), Image.LANCZOS), PLATE)
    im = im.resize((round(W*SC), round(1350*K*SC)), Image.LANCZOS)          # zoom in, crop the sides evenly
    x0 = (im.width - W)//2; im = im.crop((x0, 0, x0 + W, im.height))
    a = np.asarray(im).astype(np.float32)
    top = S(BG_TOP)
    # sky above: the photo's own top rows, column by column, softly lightened upward
    row = a[:S(30)].mean(0)
    row = np.asarray(Image.fromarray(np.clip(row[None], 0, 255).astype(np.uint8)).resize((W, 1)).filter(ImageFilter.GaussianBlur(S(40)))).astype(np.float32)[0]
    t = np.linspace(1, 0, top)[:, None, None]
    sky = row[None]*(1 - 0.06*t) + 255*0.06*t
    out = np.zeros((H, W, 3), np.float32); out[:top] = sky
    out[top:top + a.shape[0]] = a
    seam = S(140)                                                   # feather the join
    w = np.linspace(0, 1, seam)[:, None, None]
    out[top:top + seam] = sky[-1][None]*(1 - w) + a[:seam]*w
    end = top + a.shape[0]                                          # snow below: last rows, blurred and stretched
    if end < H:
        strip = Image.fromarray(a[-S(40):].astype(np.uint8)).resize((W, H - end + S(4))).filter(ImageFilter.GaussianBlur(S(12)))
        out[end - S(4):] = np.asarray(strip).astype(np.float32)
    cv = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert('RGBA')
    return cv


def header(cv, y0=150):
    d = ImageDraw.Draw(cv)
    lg = Image.open(tw.LOGO_NAVY).convert('RGBA'); lw = S(300)
    lgr = lg.resize((lw, round(lw*lg.height/lg.width)), Image.LANCZOS); cv.alpha_composite(lgr, (M - S(6), S(y0)))
    fb = F(AR_BOLD, S(30)); bh = S(64); label = 'وفّر معنا'; by = S(y0) + (lgr.height - bh)//2
    bw = tw.w_ar(label, fb) + S(70); bx = R_ - bw
    d.rounded_rectangle((bx, by, R_, by + bh), radius=S(7), fill=tw.RED+(255,))
    d.polygon([(bx, by + bh - S(24)), (bx, by + bh), (bx + S(24), by + bh)], fill=N+(255,))
    ar(d, (bx + bw/2, by + bh/2 + S(2)), label, fb, Wh, 'mm')
    return (S(y0) + lgr.height)/K


def story(out):
    cv = background()
    veil(cv, lambda y: ((y - 1600)/112)**1.3*0.98)                         # white floor for dates + footer
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse((S(90), S(170), S(990), S(1130)), fill=int(255*0.6))
    lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(g.filter(ImageFilter.GaussianBlur(S(80)))); cv.alpha_composite(lay)
    hb = header(cv, 96); d = ImageDraw.Draw(cv); cx = W/2; GAP = S(32)
    f = F(AR_BLACK, S(62)); up, dn, tw_ = box('عروض الشتاء', f); b = S(hb + 90) + up
    ar(d, (cx, b), 'عروض الشتاء', f, O)
    for sx in (-1, 1):
        x0 = cx + sx*(tw_/2 + S(26)); d.line([(x0, b - up*0.42), (x0 + sx*S(140), b - up*0.42)], fill=O+(255,), width=S(3))
    y = b + dn
    f = F(OX6, S(44)); up, dn, _ = box(MODEL, f, False); b = y + GAP + up
    spaced(d, cx, b, MODEL, f, N, S(8)); y = b + dn
    f = F(OX, S(226)); up, dn, _ = box('1500$', f, False); b = y + S(40) + up
    lt(d, (cx, b), '1500$', f, N); y = b + dn
    f = F(AR_BLACK, S(58)); up, dn, _ = box('للشهر كاملاً', f); b = y + GAP + up
    ar(d, (cx, b), 'للشهر كاملاً', f, O); y = b + dn
    t = '30 يوماً  ·  50$ في اليوم'; f = F(AR_BOLD, S(42)); up, dn, tw_ = box(t, f)
    c0 = y + S(40); ch = up + dn + S(34)
    d.rounded_rectangle((cx - tw_/2 - S(38), c0, cx + tw_/2 + S(38), c0 + ch), radius=ch/2, fill=N+(255,))
    ar(d, (cx, c0 + S(17) + up), t, f, Wh)
    print('header ends', round(hb), '| text block', round(hb + 90), '-', round((c0 + ch)/K), '| car roof ~', round(BG_TOP + 385*1350/600*SC), '| car bottom ~', round(BG_TOP + 575*1350/600*SC))
    y2 = dates_line(d, 540, 1748)
    print('dates 1748 -', round(y2), '| footer at 1840')
    footer(cv, 1840)
    cv.convert('RGB').save(out, optimize=True); print(out, cv.size)


if __name__ == '__main__':
    story(sys.argv[2])
