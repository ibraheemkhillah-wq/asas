"""CALL & RENT news carousel: one template for every "أخبار السيارات" post.

usage: python3 news_carousel.py <brand-kit dir> stories/<story>.py <out dir>
Each story file sets NAME, THEME ("dark" | "light") and SLIDES; backgrounds live next to this file.
"""
import sys, os
KIT = sys.argv[1] if __name__ == '__main__' else os.environ.get('CALLRENT_KIT', '')
sys.path.insert(0, KIT)
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw
import numpy as np
from brand import (ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT,
                   LOGO_WHITE, LOGO_NAVY, load_icons, w_ar, w_lt)

W, H = 1080, 1350
M = 64; R_ = W - M
DEEP = (8, 24, 41)
LIGHT = (244, 246, 249)
THEME = 'dark'                      # set per story: 'dark' | 'light'
SOURCE = None                       # set per story: shown on every slide
def light(): return THEME == 'light'

def source_line(d, x, y, anchor='rs'):
    if SOURCE:
        d.text((x, y), SOURCE, font=F(AR_BOLD, 26), fill=(INK_SOFT if light() else SOFT)+(255,), anchor=anchor, direction='rtl', language='ar')
INK_SOFT = (84, 102, 124)
NEWS_BADGE = 'أخبار السيارات'      # fixed: orange plate, navy type (services badge is the inverse)

O, Wh = ORANGE, WHITE
_m = ImageDraw.Draw(Image.new('RGB', (8, 8)))

def is_latin(t): return any('a' <= c.lower() <= 'z' or '0' <= c <= '9' for c in t)
def tw(t, f): return w_lt(t, f) if is_latin(t) else w_ar(t, f)

def draw_word(d, x_right, y, t, f, col):
    if is_latin(t):
        d.text((x_right, y), t.replace(' ', ' '), font=f, fill=col+(255,), anchor='rs', direction='ltr', language='en')
    else:
        d.text((x_right, y), t, font=f, fill=col+(255,), anchor='rs', direction='rtl', language='ar')

def tokens(runs):
    """runs: [(text, colour)] -> [(word, colour)]; keep Latin phrases glued with NBSP."""
    out = []
    for txt, col in runs:
        for wd in txt.split(' '):
            if wd: out.append((wd, col))
    return out

def wrap(tok, f, maxw):
    sp = w_ar(' ', f) or f.size*0.28
    lines, cur, cw = [], [], 0
    for wd, col in tok:
        ww = tw(wd.replace(' ', ' '), f)
        if cur and cw + sp + ww > maxw:
            lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + ww; cur.append((wd, col, ww))
    if cur: lines.append(cur)
    return lines, sp

def draw_lines(d, lines, sp, f, x_right, y_base, lh, on_light=False):
    for i, ln in enumerate(lines):
        x = x_right; prev_o = False
        for wd, col, ww in ln:
            if on_light and col == O:                      # orange is too weak on white: use a marker
                y = y_base + i*lh                          # (joined across the gap inside one phrase)
                d.rounded_rectangle((x-ww-8, y-f.size*0.92, x+(sp+2 if prev_o else 8), y+f.size*0.30), radius=6, fill=O+(90,))
                col = LOGONAVY; prev_o = True
            else:
                prev_o = False
                if on_light and col == Wh:
                    col = LOGONAVY
            draw_word(d, x, y_base + i*lh, wd, f, col); x -= ww + sp

def grade(cv, start, strength):
    ys = np.arange(H, dtype=np.float32)
    def band(a, rgb):
        lay = Image.new('RGBA', (W, H), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)
    tone = LIGHT if light() else DEEP
    band(np.clip((ys-start)/(H-start-120), 0, 1)**1.05*strength, tone)
    band(np.clip(1-ys/220, 0, 1)**1.5*(0.55 if light() else 0.45), tone)

def chrome(cv, d, page, total):
    lg = Image.open(LOGO_NAVY if light() else LOGO_WHITE).convert('RGBA'); LW = 270
    cv.alpha_composite(lg.resize((LW, round(LW*lg.height/lg.width)), Image.LANCZOS), (M-6, 46))
    fb = F(AR_BOLD, 26)
    bw = w_ar(NEWS_BADGE, fb) + 64; bh = 58; bx = R_ - bw; by = 50
    d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=O+(255,))
    d.polygon([(bx, by+bh-22), (bx, by+bh), (bx+22, by+bh)], fill=LOGONAVY+(255,))
    d.text((bx+bw/2, by+bh/2+2), NEWS_BADGE, font=fb, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    ink = LOGONAVY if light() else Wh
    ic = load_icons(34); fc = F(CT_FONT, 29); y = 1292; x = M
    for k in ('ig', 'fb'):
        im = ic[k]
        if light():                                # white glyphs -> navy, dark cut-outs -> white
            arr = np.array(im).astype(np.float32); L = arr[..., :3].mean(2, keepdims=True)/255
            arr[..., :3] = np.array(LOGONAVY, np.float32)*L + 255*(1-L)
            im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        cv.alpha_composite(im, (x, y-17)); x += 34+10
    d.text((x+6, y+2), 'callrenttr', font=fc, fill=ink+(255,), anchor='lm', direction='ltr', language='en')
    fp = F(LT_TEXT, 24)
    d.text((R_, y+2), f'{page:02d} / {total:02d}', font=fp, fill=(INK_SOFT if light() else SOFT)+(255,), anchor='rm', direction='ltr', language='en')
    if page < total:
        cx = R_ - w_lt(f'{page:02d} / {total:02d}', fp) - 22
        d.polygon([(cx, y-9), (cx-14, y+1), (cx, y+11)], fill=O+(255,))   # swipe cue (points left, RTL next)

def bg(name):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA')
    s = max(W/im.width, H/im.height)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l = (im.width-W)//2; t = (im.height-H)//2
    return im.crop((l, t, l+W, t+H))

def cover(sl, page, total):
    cv = bg(sl['bg']); grade(cv, 600, 0.90 if light() else 0.93); d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    # stacked headline plates, right-aligned, bottom-up
    y = 1200 if SOURCE else 1235
    for txt, fill, ink, size in reversed(sl['stack']):
        while size > 30 and w_ar(txt, F(AR_BLACK, size)) > (R_-M) - 64: size -= 2
        f = F(AR_BLACK, size); h = round(size*1.62); w = w_ar(txt, f) + 64
        if light() and fill == Wh:
            d.rectangle((R_-w, y-h, R_, y), fill=fill+(255,), outline=LOGONAVY+(255,), width=3)
        else:
            d.rectangle((R_-w, y-h, R_, y), fill=fill+(255,))
        d.text((R_-30, y-h/2+size*0.10), txt, font=f, fill=ink+(255,), anchor='rm', direction='rtl', language='ar')
        y -= h
    source_line(d, R_, 1252)
    return cv

def inner(sl, page, total):
    cv = bg(sl['bg']); grade(cv, 480, 0.90 if light() else 0.94); d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    pad = 34; boxw = R_ - M
    fb_ = F(CT_FONT, 40); blines, bsp = wrap(tokens(sl['body']), fb_, boxw - 2*pad); blh = 70
    bh = len(blines)*blh + 2*pad + 4
    extra = 0
    src = sl.get('source', SOURCE)
    if src:
        extra = 54
    btop = 1236 - bh - extra
    lay = Image.new('RGBA', (W, H), (0,0,0,0)); ld = ImageDraw.Draw(lay)
    if light():
        ld.rectangle((M, btop, R_, btop+bh+extra), fill=(255,255,255,238), outline=LOGONAVY+(70,), width=2)
    else:
        ld.rectangle((M, btop, R_, btop+bh+extra), fill=DEEP+(225,), outline=(255,255,255,46), width=1)
    cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv)
    draw_lines(d, blines, bsp, fb_, R_-pad, btop+pad+44, blh, on_light=light())
    if src:
        d.text((R_-pad, btop+bh+extra-26), src, font=F(AR_BOLD, 26), fill=(INK_SOFT if light() else SOFT)+(255,), anchor='rs', direction='rtl', language='ar')
    # title plate
    ts = 62                                   # keep the title on one line when it can stay readable
    while ts > 46 and len(wrap(tokens(sl['title']), F(AR_BLACK, ts), boxw - 2*pad)[0]) > 1: ts -= 2
    ft = F(AR_BLACK, ts); tlines, tsp = wrap(tokens(sl['title']), ft, boxw - 2*pad); tlh = round(ts*1.55)
    th = len(tlines)*tlh + 40
    ttop = btop - 14 - th
    d.rectangle((M, ttop, R_, ttop+th), fill=LOGONAVY+(255,))
    d.rectangle((R_-8, ttop, R_, ttop+th), fill=O+(255,))
    draw_lines(d, tlines, tsp, ft, R_-pad, ttop+20+round(ts*1.13), tlh)
    # eyebrow chip
    fe = F(AR_BOLD, 30); ew = w_ar(sl['chip'], fe) + 44; eh = 56
    d.rectangle((R_-ew, ttop-14-eh, R_, ttop-14), fill=O+(255,))
    d.text((R_-ew/2, ttop-14-eh/2+2), sl['chip'], font=fe, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    return cv


def field():
    """Graded brand navy, as on the approved end card."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    KEY = np.array([46,104,150], np.float32); DK = np.array(DEEP, np.float32)
    RL = np.sqrt(((xs-W/2)/1.3)**2 + ((ys-H*0.46)/1.0)**2)/900
    bgc = DK + (KEY-DK)*np.exp(-0.5*(RL/0.48)**2)[..., None]
    R = np.sqrt((xs-W/2)**2 + (ys-H/2)**2)/900
    bgc = bgc*(1-0.32*np.clip(R, 0, 1)**2.3)[..., None]
    bgc = np.clip(bgc + np.random.default_rng(7).normal(0, 2.0, (H, W, 1)), 0, 255).astype(np.uint8)
    return Image.fromarray(bgc).convert('RGBA')

def icon_bolt(d, cx, cy, s, col):
    p = [(0.12,-0.5),(-0.28,0.06),(-0.02,0.06),(-0.14,0.5),(0.28,-0.08),(0.02,-0.08)]
    d.polygon([(cx+x*s, cy+y*s) for x, y in p], fill=col+(255,))

def icon_drop(d, cx, cy, s, col):
    r = s*0.30
    d.ellipse((cx-r, cy+s*0.5-2*r, cx+r, cy+s*0.5), fill=col+(255,))
    d.polygon([(cx, cy-s*0.5), (cx-r*0.97, cy+s*0.5-r*1.15), (cx+r*0.97, cy+s*0.5-r*1.15)], fill=col+(255,))

def icon_plug(d, cx, cy, s, col):
    w, h = s*0.56, s*0.42
    d.rounded_rectangle((cx-w/2, cy-h/2, cx+w/2, cy+h/2), radius=s*0.08, fill=col+(255,))
    for dx in (-w*0.22, w*0.22):
        d.rectangle((cx+dx-s*0.05, cy-h/2-s*0.22, cx+dx+s*0.05, cy-h/2), fill=col+(255,))
    d.rectangle((cx-s*0.06, cy+h/2, cx+s*0.06, cy+h/2+s*0.22), fill=col+(255,))

ICONS = {'bolt': icon_bolt, 'drop': icon_drop, 'plug': icon_plug}

def poll(sl, page, total):
    cv = bg(sl['bg'])
    ys = np.arange(H, dtype=np.float32)
    tone = LIGHT if light() else DEEP
    for a_, rgb in ((np.clip(1-(ys-120)/560, 0, 1)**1.2*0.88, tone), (np.clip((ys-900)/300, 0, 1)*0.9, tone)):
        lay = Image.new('RGBA', (W, H), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a_[:, None], W, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    fe = F(AR_BOLD, 30); ew = w_ar(sl['chip'], fe) + 48; eh = 58
    d.rectangle((W/2-ew/2, 210, W/2+ew/2, 210+eh), fill=O+(255,))
    d.text((W/2, 210+eh/2+2), sl['chip'], font=fe, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    ink = LOGONAVY if light() else Wh
    fq = 62
    while w_ar(sl['q1'], F(AR_BLACK, fq)) > W - 2*M: fq -= 2
    d.text((W/2, 380), sl['q1'], font=F(AR_BLACK, fq), fill=ink+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, 520), sl['q2'], font=F(AR_BLACK, 112), fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    for label, ic, icol, cx in sl['options']:          # each tag sits above its car
        fl = F(AR_BLACK, 44); pw = w_ar(label, fl) + 150; ph = 92; y0 = sl.get('tag_y', 600)
        x0 = cx - pw/2
        d.rounded_rectangle((x0, y0, x0+pw, y0+ph), radius=46, fill=LOGONAVY+(235,), outline=icol+(255,), width=3)
        d.ellipse((x0+pw-84, y0+12, x0+pw-16, y0+80), fill=DEEP+(255,), outline=icol+(255,), width=2)
        ICONS[ic](d, x0+pw-50, y0+46, 42, icol)
        d.text((x0+pw-100, y0+ph/2+6), label, font=fl, fill=Wh+(255,), anchor='rm', direction='rtl', language='ar')
        if sl.get('tag_dir', 'up') == 'up':
            d.polygon([(cx-14, y0), (cx+14, y0), (cx, y0-18)], fill=icol+(255,))
        else:
            d.polygon([(cx-14, y0+ph), (cx+14, y0+ph), (cx, y0+ph+18)], fill=icol+(255,))
    if sl.get('cta'):
        d.text((W/2, 1185), sl['cta'], font=F(AR_BLACK, 56), fill=ink+(255,), anchor='ms', direction='rtl', language='ar')
    source_line(d, W/2, 1245, anchor='ms')
    if sl.get('hint'):
        d.text((W/2, 1218), sl['hint'], font=F(AR_BOLD, 30), fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')
    return cv


def render(story_path, out):
    global THEME
    ns = dict(O=O, Wh=Wh, LOGONAVY=LOGONAVY)
    exec(open(story_path, encoding='utf-8').read(), ns)
    THEME = ns.get('THEME', 'dark')
    global SOURCE
    SOURCE = ns.get('SOURCE')
    os.makedirs(out, exist_ok=True)
    for i, sl in enumerate(ns['SLIDES'], 1):
        cv = {'cover': cover, 'inner': inner, 'poll': poll}[sl['kind']](sl, i, len(ns['SLIDES']))
        p = os.path.join(out, f"{ns['NAME']}-{i}.png"); cv.convert('RGB').save(p, quality=95); print(p)

if __name__ == '__main__':
    render(sys.argv[2], sys.argv[3])
