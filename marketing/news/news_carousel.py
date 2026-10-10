"""CALL & RENT news carousel: one template for every "أخبار السيارات" post.

usage: python3 news_carousel.py <brand-kit dir> <out dir>
Slides are defined in SLIDES below; backgrounds live next to this file.
"""
import sys, os
KIT, OUT = sys.argv[1:3]
sys.path.insert(0, KIT)
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw
import numpy as np
from brand import (ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LT_TEXT,
                   LOGO_WHITE, load_icons, w_ar, w_lt)

W, H = 1080, 1350
M = 64; R_ = W - M
DEEP = (8, 24, 41)
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

def draw_lines(d, lines, sp, f, x_right, y_base, lh):
    for i, ln in enumerate(lines):
        x = x_right
        for wd, col, ww in ln:
            draw_word(d, x, y_base + i*lh, wd, f, col); x -= ww + sp

def grade(cv, start, strength):
    ys = np.arange(H, dtype=np.float32)
    def band(a, rgb):
        lay = Image.new('RGBA', (W, H), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)
    band(np.clip((ys-start)/(H-start-120), 0, 1)**1.05*strength, DEEP)
    band(np.clip(1-ys/220, 0, 1)**1.5*0.45, DEEP)

def chrome(cv, d, page, total):
    lg = Image.open(LOGO_WHITE).convert('RGBA'); LW = 270
    cv.alpha_composite(lg.resize((LW, round(LW*lg.height/lg.width)), Image.LANCZOS), (M-6, 46))
    fb = F(AR_BOLD, 26)
    bw = w_ar(NEWS_BADGE, fb) + 64; bh = 58; bx = R_ - bw; by = 50
    d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=O+(255,))
    d.polygon([(bx, by+bh-22), (bx, by+bh), (bx+22, by+bh)], fill=LOGONAVY+(255,))
    d.text((bx+bw/2, by+bh/2+2), NEWS_BADGE, font=fb, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    ic = load_icons(34); fc = F(CT_FONT, 29); y = 1292; x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, y-17)); x += 34+10
    d.text((x+6, y+2), 'callrenttr', font=fc, fill=Wh+(255,), anchor='lm', direction='ltr', language='en')
    fp = F(LT_TEXT, 24)
    d.text((R_, y+2), f'{page:02d} / {total:02d}', font=fp, fill=SOFT+(255,), anchor='rm', direction='ltr', language='en')
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
    cv = bg(sl['bg']); grade(cv, 600, 0.93); d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    # stacked headline plates, right-aligned, bottom-up
    y = 1235
    for txt, fill, ink, size in reversed(sl['stack']):
        while size > 30 and w_ar(txt, F(AR_BLACK, size)) > (R_-M) - 64: size -= 2
        f = F(AR_BLACK, size); h = round(size*1.62); w = w_ar(txt, f) + 64
        d.rectangle((R_-w, y-h, R_, y), fill=fill+(255,))
        d.text((R_-30, y-h/2+size*0.10), txt, font=f, fill=ink+(255,), anchor='rm', direction='rtl', language='ar')
        y -= h
    return cv

def inner(sl, page, total):
    cv = bg(sl['bg']); grade(cv, 480, 0.94); d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    pad = 34; boxw = R_ - M
    fb_ = F(CT_FONT, 40); blines, bsp = wrap(tokens(sl['body']), fb_, boxw - 2*pad); blh = 70
    bh = len(blines)*blh + 2*pad + 4
    extra = 0
    if sl.get('source'):
        extra = 54
    btop = 1236 - bh - extra
    lay = Image.new('RGBA', (W, H), (0,0,0,0)); ld = ImageDraw.Draw(lay)
    ld.rectangle((M, btop, R_, btop+bh+extra), fill=DEEP+(225,), outline=(255,255,255,46), width=1)
    cv.alpha_composite(lay)
    draw_lines(d, blines, bsp, fb_, R_-pad, btop+pad+44, blh)
    if sl.get('source'):
        d.text((R_-pad, btop+bh+extra-26), sl['source'], font=F(AR_BOLD, 26), fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')
    # title plate
    ft = F(AR_BLACK, 62); tlines, tsp = wrap(tokens(sl['title']), ft, boxw - 2*pad); tlh = 96
    th = len(tlines)*tlh + 40
    ttop = btop - 14 - th
    d.rectangle((M, ttop, R_, ttop+th), fill=LOGONAVY+(255,))
    d.rectangle((R_-8, ttop, R_, ttop+th), fill=O+(255,))
    draw_lines(d, tlines, tsp, ft, R_-pad, ttop+20+70, tlh)
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

def poll(sl, page, total):
    cv = bg(sl['bg'])
    ys = np.arange(H, dtype=np.float32)
    for a_, rgb in ((np.clip(1-(ys-120)/560, 0, 1)**1.2*0.88, DEEP), (np.clip((ys-900)/300, 0, 1)*0.9, DEEP)):
        lay = Image.new('RGBA', (W, H), rgb+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a_[:, None], W, 1)*255).astype(np.uint8))); cv.alpha_composite(lay)
    d = ImageDraw.Draw(cv)
    chrome(cv, d, page, total)
    fe = F(AR_BOLD, 30); ew = w_ar(sl['chip'], fe) + 48; eh = 58
    d.rectangle((W/2-ew/2, 210, W/2+ew/2, 210+eh), fill=O+(255,))
    d.text((W/2, 210+eh/2+2), sl['chip'], font=fe, fill=LOGONAVY+(255,), anchor='mm', direction='rtl', language='ar')
    d.text((W/2, 380), sl['q1'], font=F(AR_BLACK, 62), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, 520), sl['q2'], font=F(AR_BLACK, 112), fill=O+(255,), anchor='ms', direction='rtl', language='ar')
    for label, ic, icol, cx in sl['options']:          # each tag sits above its car
        fl = F(AR_BLACK, 44); pw = w_ar(label, fl) + 150; ph = 92; y0 = sl.get('tag_y', 600)
        x0 = cx - pw/2
        d.rounded_rectangle((x0, y0, x0+pw, y0+ph), radius=46, fill=LOGONAVY+(235,), outline=icol+(255,), width=3)
        d.ellipse((x0+pw-84, y0+12, x0+pw-16, y0+80), fill=DEEP+(255,), outline=icol+(255,), width=2)
        (icon_bolt if ic == 'bolt' else icon_drop)(d, x0+pw-50, y0+46, 42, icol)
        d.text((x0+pw-100, y0+ph/2+6), label, font=fl, fill=Wh+(255,), anchor='rm', direction='rtl', language='ar')
        d.polygon([(cx-14, y0), (cx+14, y0), (cx, y0-18)], fill=icol+(255,))
    d.text((W/2, 1160), sl['cta'], font=F(AR_BLACK, 56), fill=Wh+(255,), anchor='ms', direction='rtl', language='ar')
    d.text((W/2, 1218), sl['hint'], font=F(AR_BOLD, 30), fill=SOFT+(255,), anchor='ms', direction='rtl', language='ar')
    return cv

NB = ' '
SLIDES = [
    dict(kind='cover', bg='bmw-1-cover.jpg', stack=[
        ('بي إم دبليو الفئة الثالثة 2027', LOGONAVY, Wh, 60),
        ('الكهربائية أرخص من البنزين', Wh, LOGONAVY, 80),
        ('بفارق 4,400 دولار', O, LOGONAVY, 72)]),
    dict(kind='inner', bg='bmw-2-prices.jpg', chip='الأسعار',
         title=[('الكهربائية أرخص بفارق', Wh), ('4,400 دولار', O)],
         body=[('تبدأ نسخة', Wh), (f'i3{NB}50{NB}xDrive', O), ('الكهربائية من', Wh), ('61,500 دولار،', O),
               ('مقابل', Wh), ('65,900 دولار', O), ('لنسخة البنزين', Wh), (f'M350{NB}xDrive،', O),
               ('ودون رسوم الشحن والتسليم.', Wh)]),
    dict(kind='inner', bg='bmw-3-charging.jpg', chip='المدى والشحن',
         title=[('468 ميلاً', O), ('بشحنة واحدة', Wh)],
         body=[('تصل', Wh), ('i3', O), ('الكهربائية إلى مدى', Wh), ('468 ميلاً', O), ('وفق أرقام بي إم دبليو، ويمكنها استعادة', Wh),
               ('208 أميال', O), ('من المدى خلال', Wh), ('10 دقائق', O), ('فقط من الشحن السريع.', Wh)]),
    dict(kind='inner', bg='bmw-4-market.jpg', chip='السوق', source='المصدر: تك كرانش',
         title=[('الكهربائية', Wh), ('تنافس البنزين', O), ('بالسعر', Wh)],
         body=[('تعتمد النسختان على منصتين مختلفتين. ويأتي ذلك مع استمرار انخفاض أسعار السيارات الكهربائية واقترابها من منافسة البنزين في', Wh),
               ('سعر الشراء الأولي،', O), ('وليس فقط في تكلفة التشغيل والملكية.', Wh)]),
    dict(kind='poll', bg='bmw-5-poll.jpg', chip='شاركنا رأيك', q1='لو الفرق 4,400 دولار...', q2='شو بتختار؟',
         options=[('كهربائية', 'bolt', O, 815), ('بنزين', 'drop', Wh, 262)], tag_y=950,
         cta='جاوبنا بالتعليقات', hint='اكتب: كهربائية أو بنزين'),
]

os.makedirs(OUT, exist_ok=True)
for i, sl in enumerate(SLIDES, 1):
    cv = {'cover': cover, 'inner': inner, 'poll': poll}[sl['kind']](sl, i, len(SLIDES))
    p = os.path.join(OUT, f'bmw-3series-{i}.png'); cv.convert('RGB').save(p, quality=95); print(p)
