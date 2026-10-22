"""CALL & RENT news carousel: one template for every "أخبار السيارات" post.

usage: python3 news_carousel.py <brand-kit dir> stories/<story>.py <out dir>
Each story file sets NAME, THEME ("dark" | "light") and SLIDES; backgrounds live next to this file.
"""
import sys, os, re
KIT = sys.argv[1] if __name__ == '__main__' else os.environ.get('CALLRENT_KIT', '')
sys.path.insert(0, KIT)
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import (ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT,
                   LOGO_WHITE, LOGO_NAVY, load_icons, w_ar, w_lt)
from brand import F as _bF, w_ar as _bw_ar, w_lt as _bw_lt

# Layout is written in 1080x1350 units. K is the pixel scale: 1 when other scripts import these helpers,
# 2 (2160x2700) when a story is rendered; hires() swaps in fonts, measures and a Draw that scale by K.
K = 1
Draw = ImageDraw.Draw

def _sc(v):
    if isinstance(v, (list, tuple)): return [_sc(x) for x in v] if isinstance(v, list) else tuple(_sc(x) for x in v)
    return v*K

class _Font:
    def __init__(self, name, size): self.size = size; self.real = _bF(name, round(size*K))

class _Draw:
    def __init__(self, im): self.d = ImageDraw.Draw(im)
    def _kw(self, kw):
        if kw.get('width'): kw['width'] = max(1, round(kw['width']*K))
        return kw
    def text(self, xy, t, font, **kw): self.d.text(_sc(xy), t, font=font.real, **kw)
    def rectangle(self, box, **kw): self.d.rectangle(_sc(box), **self._kw(kw))
    def rounded_rectangle(self, box, radius=0, **kw): self.d.rounded_rectangle(_sc(box), radius=radius*K, **self._kw(kw))
    def ellipse(self, box, **kw): self.d.ellipse(_sc(box), **self._kw(kw))
    def polygon(self, pts, **kw): self.d.polygon(_sc(pts), **self._kw(kw))
    def line(self, pts, **kw): self.d.line(_sc(pts), **self._kw(kw))

def hires(k=2):
    global K, F, w_ar, w_lt, Draw
    K = k; Draw = _Draw
    F = lambda name, size: _Font(name, size)
    w_ar = lambda t, f: _bw_ar(t, f.real)/K
    w_lt = lambda t, f: _bw_lt(t, f.real)/K

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
IDEA_BADGE = 'عندك فكرة'            # fixed: brand steel-blue plate, white type, orange corner
IDEA_BLUE = (46, 104, 150)          # #2E6896, the key light of the brand's navy backdrop
CARE_BADGE = 'اعتنِ بسيارتك'        # fixed: teal plate, white type, orange corner
CARE_TEAL = (22, 138, 128)          # #168A80
OFFER_BADGE = 'وفّر معنا'           # fixed: crimson plate, white type, navy corner
OFFER_RED = (200, 30, 45)           # #C81E2D
SECTION = 'news'                    # set per story: 'news' | 'idea' | 'care' | 'offer'

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
        if txt == '\n':                                   # explicit line break inside a body
            out.append(('\n', col)); continue
        for wd in txt.split(' '):
            if wd: out.append((wd, col))
    return out

def wrap(tok, f, maxw):
    sp = w_ar(' ', f) or f.size*0.28
    lines, cur, cw = [], [], 0
    for i, (wd, col) in enumerate(tok):
        if wd == '\n':
            if cur: lines.append(cur)
            cur, cw = [], 0; continue
        ww = tw(wd.replace(' ', ' '), f)
        need = ww                                         # a number never ends a line: keep it with its unit
        if re.fullmatch(r'[\d.,]+', wd) and i + 1 < len(tok) and tok[i+1][0] != '\n':
            need += sp + tw(tok[i+1][0], f)
        if cur and cw + sp + need > maxw:
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
    ys = np.arange(H*K, dtype=np.float32)/K
    def band(a, rgb):
        lay = Image.new('RGBA', (W*K, H*K), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W*K, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)
    tone = LIGHT if light() else DEEP
    band(np.clip((ys-start)/(H-start-120), 0, 1)**1.05*strength, tone)
    band(np.clip(1-ys/220, 0, 1)**1.5*(0.55 if light() else 0.45), tone)

def icon_bulb(d, cx, cy, s, col):
    r = s*0.30
    d.ellipse((cx-r, cy-s*0.5, cx+r, cy-s*0.5+2*r), fill=col+(255,))
    d.polygon([(cx-r*0.62, cy-s*0.5+r*1.7), (cx+r*0.62, cy-s*0.5+r*1.7), (cx+r*0.42, cy+s*0.22), (cx-r*0.42, cy+s*0.22)], fill=col+(255,))
    for k in (0, 1):
        yy = cy+s*0.27+k*s*0.11
        d.rounded_rectangle((cx-r*0.42, yy, cx+r*0.42, yy+s*0.07), radius=2, fill=col+(255,))

def badge(d):
    fb = F(AR_BOLD, 26); bh = 58; by = 50
    plates = {'idea': (IDEA_BADGE, IDEA_BLUE, O), 'care': (CARE_BADGE, CARE_TEAL, O), 'offer': (OFFER_BADGE, OFFER_RED, LOGONAVY)}
    if SECTION in plates:
        label, plate, corner = plates[SECTION]
        bw = w_ar(label, fb) + 64; bx = R_ - bw
        d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=plate+(255,))
        d.polygon([(bx, by+bh-22), (bx, by+bh), (bx+22, by+bh)], fill=corner+(255,))
        d.text((bx+bw/2, by+bh/2+2), label, font=fb, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    else:
        bw = w_ar(NEWS_BADGE, fb) + 64; bx = R_ - bw
        d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=O+(255,))
        d.polygon([(bx, by+bh-22), (bx, by+bh), (bx+22, by+bh)], fill=LOGONAVY+(255,))
        d.text((bx+bw/2, by+bh/2+2), NEWS_BADGE, font=fb, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')

def chrome(cv, d, page, total):
    lg = Image.open(LOGO_NAVY if light() else LOGO_WHITE).convert('RGBA'); LW = 270
    cv.alpha_composite(lg.resize((LW*K, round(LW*K*lg.height/lg.width)), Image.LANCZOS), ((M-6)*K, 46*K))
    badge(d)
    ink = LOGONAVY if light() else Wh
    ic = load_icons(34*K); fc = F(CT_FONT, 29); y = 1292; x = M
    for k in ('ig', 'fb'):
        im = ic[k]
        if light():                                # white glyphs -> navy, dark cut-outs -> white
            arr = np.array(im).astype(np.float32); L = arr[..., :3].mean(2, keepdims=True)/255
            arr[..., :3] = np.array(LOGONAVY, np.float32)*L + 255*(1-L)
            im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        cv.alpha_composite(im, (x*K, (y-17)*K)); x += 34+10
    d.text((x+6, y+2), 'callrenttr', font=fc, fill=ink+(255,), anchor='lm', direction='ltr', language='en')
    if total == 1:
        return
    fp = F(LT_TEXT, 24)
    d.text((R_, y+2), f'{page:02d} / {total:02d}', font=fp, fill=(INK_SOFT if light() else SOFT)+(255,), anchor='rm', direction='ltr', language='en')
    if page < total:
        cx = R_ - w_lt(f'{page:02d} / {total:02d}', fp) - 22
        d.polygon([(cx, y-9), (cx-14, y+1), (cx, y+11)], fill=O+(255,))   # swipe cue (points left, RTL next)

def bg(name):
    im = Image.open(os.path.join(HERE, name)).convert('RGBA')
    s = max(W*K/im.width, H*K/im.height)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l = (im.width-W*K)//2; t = (im.height-H*K)//2
    return im.crop((l, t, l+W*K, t+H*K))

def cover(sl, page, total):
    cv = bg(sl['bg']); grade(cv, 600, 0.90 if light() else 0.93); d = Draw(cv)
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
    if sl.get('mark'):                                   # maker's wordmark, white, under the badge
        mk = Image.open(os.path.join(HERE, sl['mark'])).convert('RGBA'); mw = sl.get('mark_w', 240)
        mk = mk.resize((mw*K, round(mw*K*mk.height/mk.width)), Image.LANCZOS)
        cv.alpha_composite(mk, ((R_-mw)*K, 136*K))
    return cv

def inner(sl, page, total):
    cv = bg(sl['bg']); grade(cv, 480, 0.90 if light() else 0.94); d = Draw(cv)
    chrome(cv, d, page, total)
    pad = 34; boxw = R_ - M
    fb_ = F(CT_FONT, 40); blines, bsp = wrap(tokens(sl['body']), fb_, boxw - 2*pad); blh = 70
    bh = len(blines)*blh + 2*pad + 4
    extra = 0
    src = sl.get('source', SOURCE)
    if src:
        extra = 54
    btop = 1236 - bh - extra
    lay = Image.new('RGBA', (W*K, H*K), (0,0,0,0)); ld = Draw(lay)
    if light():
        ld.rectangle((M, btop, R_, btop+bh+extra), fill=(255,255,255,238), outline=LOGONAVY+(70,), width=2)
    else:
        ld.rectangle((M, btop, R_, btop+bh+extra), fill=DEEP+(225,), outline=(255,255,255,46), width=1)
    cv.alpha_composite(lay)
    d = Draw(cv)
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
    ys, xs = np.mgrid[0:H*K, 0:W*K].astype(np.float32)/K
    KEY = np.array([46,104,150], np.float32); DK = np.array(DEEP, np.float32)
    RL = np.sqrt(((xs-W/2)/1.3)**2 + ((ys-H*0.46)/1.0)**2)/900
    bgc = DK + (KEY-DK)*np.exp(-0.5*(RL/0.48)**2)[..., None]
    R = np.sqrt((xs-W/2)**2 + (ys-H/2)**2)/900
    bgc = bgc*(1-0.32*np.clip(R, 0, 1)**2.3)[..., None]
    bgc = np.clip(bgc + np.random.default_rng(7).normal(0, 2.0, (H*K, W*K, 1)), 0, 255).astype(np.uint8)
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

def icon_check(d, cx, cy, s, col):
    d.line([(cx-s*0.32, cy+s*0.02), (cx-s*0.08, cy+s*0.26), (cx+s*0.34, cy-s*0.24)], fill=col+(255,), width=round(s*0.15), joint='curve')

def icon_x(d, cx, cy, s, col):
    k = s*0.26; w = round(s*0.15)
    d.line([(cx-k, cy-k), (cx+k, cy+k)], fill=col+(255,), width=w)
    d.line([(cx-k, cy+k), (cx+k, cy-k)], fill=col+(255,), width=w)

ICONS = {'bolt': icon_bolt, 'drop': icon_drop, 'plug': icon_plug, 'check': icon_check, 'x': icon_x}

def poll(sl, page, total):
    cv = bg(sl['bg'])
    ys = np.arange(H*K, dtype=np.float32)/K
    tone = LIGHT if light() else DEEP
    for a_, rgb in ((np.clip(1-(ys-120)/560, 0, 1)**1.2*0.88, tone), (np.clip((ys-sl.get('fade_from', 900))/300, 0, 1)*0.9, tone)):
        lay = Image.new('RGBA', (W*K, H*K), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a_[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)
    d = Draw(cv)
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


def stats(sl, page, total):
    """One big total, then a ranked bar per market."""
    cv = bg(sl['bg']).filter(ImageFilter.GaussianBlur(9*K))      # backdrop only: keep the figures clean
    cv = Image.blend(cv, Image.new('RGBA', (W*K, H*K), DEEP+(255,)), 0.5); grade(cv, 260, 0.96); d = Draw(cv)
    chrome(cv, d, page, total)
    fe = F(AR_BOLD, 30); ew = w_ar(sl['chip'], fe) + 44; eh = 56; ey = 250
    d.rectangle((R_-ew, ey, R_, ey+eh), fill=O+(255,))
    d.text((R_-ew/2, ey+eh/2+2), sl['chip'], font=fe, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    fbig = F(LT_TEXT, 150)
    d.text((R_, ey+eh+170), sl['total'], font=fbig, fill=O+(255,), anchor='rs', direction='ltr', language='en')
    d.text((R_, ey+eh+250), sl['total_label'], font=F(AR_BLACK, 50), fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
    top = ey+eh+300; rh = 124; pad = 34
    lay = Image.new('RGBA', (W*K, H*K), (0,0,0,0)); ld = Draw(lay)
    ld.rectangle((M, top, R_, top+len(sl['rows'])*rh+2*pad-20), fill=DEEP+(225,), outline=(255,255,255,46), width=1)
    cv.alpha_composite(lay); d = Draw(cv)
    d.rectangle((R_-8, top, R_, top+len(sl['rows'])*rh+2*pad-20), fill=O+(255,))
    mx = max(v for _, _, v in sl['rows'])
    for i, (name, num, v) in enumerate(sl['rows']):
        y = top + pad + i*rh
        d.text((R_-pad, y+44), name, font=F(AR_BLACK, 42), fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
        d.text((M+pad, y+44), num, font=F(LT_TEXT, 46), fill=(O if i == 0 else Wh)+(255,), anchor='ls', direction='ltr', language='en')
        bx0, bx1, by = M+pad, R_-pad, y+66
        d.rounded_rectangle((bx0, by, bx1, by+14), radius=7, fill=(40,62,88,255))
        d.rounded_rectangle((bx1-(bx1-bx0)*v/mx, by, bx1, by+14), radius=7, fill=O+(255,))
    if sl.get('note'):
        d.text((R_, top+len(sl['rows'])*rh+2*pad+30), sl['note'], font=F(AR_BOLD, 28), fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')
    source_line(d, R_, 1252)
    return cv

def ask(sl, page, total):
    """Open question, no options: one line of setup, the question in orange."""
    cv = bg(sl['bg'])
    ys = np.arange(H*K, dtype=np.float32)/K; y0 = sl.get('top', 700)
    tone = LIGHT if light() else DEEP
    for a_ in (np.clip(1-ys/240, 0, 1)**1.4*0.75,
               np.exp(-0.5*((ys-(y0+110))/190)**2)*0.82,
               np.clip((ys-1200)/150, 0, 1)*0.85):
        lay = Image.new('RGBA', (W*K, H*K), tone+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a_[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)
    d = Draw(cv)
    chrome(cv, d, page, total)
    fe = F(AR_BOLD, 30); ew = w_ar(sl['chip'], fe) + 48; eh = 58
    d.rectangle((W/2-ew/2, y0-eh-40, W/2+ew/2, y0-40), fill=O+(255,))
    d.text((W/2, y0-40-eh/2+2), sl['chip'], font=fe, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    y = y0
    for txt, col, size in sl['lines']:
        while w_ar(txt, F(AR_BLACK, size)) > W - 2*M: size -= 2
        y += round(size*1.25)
        d.text((W/2, y), txt, font=F(AR_BLACK, size), fill=col+(255,), anchor='ms', direction='rtl', language='ar')
    if sl.get('versus'):
        versus(cv, sl['versus'])
    source_line(Draw(cv), W/2, 1245, anchor='ms')
    return cv

def star(cx, cy, r, rot=0):
    import math
    return [(cx + (r if i % 2 == 0 else r*0.40)*math.sin(math.radians(rot + i*36)),
             cy - (r if i % 2 == 0 else r*0.40)*math.cos(math.radians(rot + i*36))) for i in range(10)]

def mark_disc(cv, kind, cx, cy, r):
    """A round maker/country mark: an image file (roundel) or 'cn' for the Chinese flag."""
    d = Draw(cv)
    d.ellipse((cx-r-4, cy-r-4, cx+r+4, cy+r+4), fill=(255, 255, 255, 255), outline=LOGONAVY+(255,), width=2)
    if kind == 'cn':
        lay = Image.new('RGBA', (W*K, H*K), (0, 0, 0, 0)); ld = Draw(lay)
        ld.rectangle((cx-r, cy-r, cx+r, cy+r), fill=(222, 41, 16, 255))
        ld.polygon(star(cx-r*0.42, cy-r*0.30, r*0.36), fill=(255, 222, 0, 255))
        for dx, dy in ((0.02, -0.66), (0.24, -0.42), (0.24, -0.10), (0.02, 0.12)):
            ld.polygon(star(cx+dx*r, cy+dy*r, r*0.12, 20), fill=(255, 222, 0, 255))
        m = Image.new('L', (W*K, H*K), 0); Draw(m).ellipse((cx-r, cy-r, cx+r, cy+r), fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel('A')), np.asarray(m))))
        cv.alpha_composite(lay)
    else:
        mk = Image.open(os.path.join(HERE, kind)).convert('RGBA').resize((2*r*K, 2*r*K), Image.LANCZOS)
        cv.alpha_composite(mk, (round((cx-r)*K), round((cy-r)*K)))

def versus(cv, vs):
    """Two labelled marks face to face with an orange VS between: who is up against whom."""
    y = vs['y']; r = 44; fl = F(AR_BLACK, 34)
    for kind, label, cx in (vs['left'], vs['right']):
        pw = w_ar(label, fl) + 2*r + 64; x0 = cx - pw/2
        d = Draw(cv)
        d.rounded_rectangle((x0, y-r-10, x0+pw, y+r+10), radius=r+10, fill=(255, 255, 255, 245), outline=LOGONAVY+(255,), width=3)
        mark_disc(cv, kind, x0+pw-r-12, y, r)
        Draw(cv).text((x0+pw-2*r-40, y+4), label, font=fl, fill=LOGONAVY+(255,), anchor='rm', direction='rtl', language='ar')
    d = Draw(cv); cx = vs.get('vs_x', W/2)
    d.ellipse((cx-46, y-46, cx+46, y+46), fill=O+(255,))
    d.text((cx, y+2), 'VS', font=F(LT_TEXT, 40), fill=LOGONAVY+(255,), anchor='mm', direction='ltr', language='en')

def idea(sl, page, total):
    """Single image, one question. Headline sits in the calm top of the photo."""
    cv = bg(sl['bg'])
    ys = np.arange(H*K, dtype=np.float32)/K
    for a_ in (np.clip(1-(ys-80)/620, 0, 1)**1.3*0.80, np.clip((ys-1130)/220, 0, 1)*0.85):
        lay = Image.new('RGBA', (W*K, H*K), DEEP+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a_[:, None], W*K, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)
    d = Draw(cv)
    chrome(cv, d, page, total)
    y = sl.get('top', 300)
    for txt, col in sl['lines']:
        size = sl.get('size', 92)
        while w_ar(txt, F(AR_BLACK, size)) > W - 2*M: size -= 2
        d.text((W/2, y), txt, font=F(AR_BLACK, size), fill=col+(255,), anchor='ms', direction='rtl', language='ar')
        y += round(size*1.45)
    d.rectangle((W/2-60, y-round(size*1.45)+42, W/2+60, y-round(size*1.45)+50), fill=O+(255,))
    if sl.get('credit'):                                   # photo credit when the licence asks for one
        d.text((R_, 1294), sl['credit'], font=F(LT_TEXT, 20), fill=SOFT+(255,), anchor='rm', direction='ltr', language='en')
    return cv

def render(story_path, out):
    global THEME
    ns = dict(O=O, Wh=Wh, LOGONAVY=LOGONAVY)
    exec(open(story_path, encoding='utf-8').read(), ns)
    THEME = ns.get('THEME', 'dark')
    global SOURCE
    SOURCE = ns.get('SOURCE')
    global SECTION
    SECTION = ns.get('SECTION', 'news')
    os.makedirs(out, exist_ok=True)
    for i, sl in enumerate(ns['SLIDES'], 1):
        cv = {'cover': cover, 'inner': inner, 'poll': poll, 'idea': idea, 'stats': stats, 'ask': ask}[sl['kind']](sl, i, len(ns['SLIDES']))
        if sl.get('credit') and sl['kind'] != 'idea':      # photo credit when the licence asks for one
            Draw(cv).text((W/2, 1294), sl['credit'], font=F(LT_TEXT, 19), fill=(INK_SOFT if light() else SOFT)+(255,), anchor='mm', direction='ltr', language='en')
        p = os.path.join(out, f"{ns['NAME']}-{i}.png"); cv.convert('RGB').save(p, quality=95); print(p)

if __name__ == '__main__':
    hires()
    render(sys.argv[2], sys.argv[3])
