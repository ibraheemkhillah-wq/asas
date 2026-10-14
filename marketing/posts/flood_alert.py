"""CALL & RENT urgent weather alert (single image).

usage: python3 flood_alert.py <brand-kit dir> <background.jpg> <out.png>
Alerts are not a content section, so they carry an 'عاجل' warning plate instead of a section badge.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.join(HERE, '..', 'news'))
import news_carousel as nc
from news_carousel import W, H, M, R_, O, Wh, DEEP, LOGONAVY, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, w_ar
from brand import LOGO_WHITE, load_icons
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ALERT = (214, 40, 40)
ALERT_HI = (255, 72, 60)             # brighter red for type on dark
BLOOD = (38, 6, 10)                  # red-black shade for the photo
nc.THEME = 'dark'


def shade(cv):
    ys = np.arange(H, dtype=np.float32)
    for a, tone in ((np.clip(1-ys/300, 0, 1)**1.3*0.70, DEEP), (np.clip((ys-430)/420, 0, 1)**1.1*0.93, BLOOD)):
        lay = Image.new('RGBA', (W, H), tone+(0,))
        lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, 1)*255).astype(np.uint8)))
        cv.alpha_composite(lay)


def warn_triangle(d, cx, cy, s, fill, mark):
    d.polygon([(cx, cy-s*0.52), (cx-s*0.58, cy+s*0.46), (cx+s*0.58, cy+s*0.46)], fill=fill)
    d.rounded_rectangle((cx-s*0.06, cy-s*0.20, cx+s*0.06, cy+s*0.17), radius=3, fill=mark)
    d.ellipse((cx-s*0.07, cy+s*0.24, cx+s*0.07, cy+s*0.38), fill=mark)


def icon_no_entry(d, cx, cy, s, col):
    r = s/2
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col+(255,))
    d.rounded_rectangle((cx-r*0.62, cy-r*0.16, cx+r*0.62, cy+r*0.16), radius=4, fill=Wh+(255,))


def icon_waves(d, cx, cy, s, col):
    r = s/2
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col+(255,))
    for k in (-1, 0, 1):
        y = cy + k*s*0.19
        xs = np.linspace(-r*0.58, r*0.58, 40)
        pts = [(cx+x, y + s*0.045*np.sin(x/(r*0.58)*2*np.pi)) for x in xs]
        d.line(pts, fill=Wh+(255,), width=max(3, round(s*0.065)), joint='curve')


def main(bg_path, out):
    im = Image.open(bg_path).convert('RGBA')
    s = max(W/im.width, H/im.height)
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    cv = im.crop(((im.width-W)//2, (im.height-H)//2, (im.width-W)//2+W, (im.height-H)//2+H))
    shade(cv)
    tint = Image.new('RGBA', (W, H), ALERT+(46,)); cv.alpha_composite(tint)      # whole scene leans red
    d = ImageDraw.Draw(cv)
    # logo
    lg = Image.open(LOGO_WHITE).convert('RGBA'); LW = 270
    cv.alpha_composite(lg.resize((LW, round(LW*lg.height/lg.width)), Image.LANCZOS), (M-6, 46))
    # 'عاجل' hazard banner: full width, the loudest thing on the page
    by, bh = 424, 134
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).rectangle((M-10, by-10, R_+10, by+bh+10), fill=ALERT_HI+(200,))
    cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(34)))
    stripe = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(stripe)
    sd.rectangle((M, by, R_, by+bh), fill=ALERT+(255,))
    for x in range(M-bh, R_+bh, 44):                           # red-black hazard tape on both ends
            sd.polygon([(x, by+bh), (x+22, by+bh), (x+22+bh, by), (x+bh, by)], fill=(20, 20, 24, 255))
    tape = Image.new('L', (W, H), 0); td = ImageDraw.Draw(tape)
    td.rectangle((M, by, M+130, by+bh), fill=255); td.rectangle((R_-130, by, R_, by+bh), fill=255)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(base)
    bd.rectangle((M, by, R_, by+bh), fill=ALERT+(255,))
    stripes_only = Image.new('RGBA', (W, H), (0, 0, 0, 0)); stripes_only.paste(stripe, (0, 0), tape)
    cv.alpha_composite(base); cv.alpha_composite(stripes_only)
    d = ImageDraw.Draw(cv)
    fa = F(AR_BLACK, 92); label = 'عاجل'
    lw = w_ar(label, fa); gapx = 30; ts = 78
    total = lw + 2*(ts+gapx); cx0 = W/2 - total/2
    warn_triangle(d, cx0 + ts/2, by+bh/2+2, ts, Wh+(255,), ALERT+(255,))
    d.text((W/2, by+bh/2+6), label, font=fa, fill=Wh+(255,), anchor='mm', direction='rtl', language='ar')
    warn_triangle(d, cx0 + total - ts/2, by+bh/2+2, ts, Wh+(255,), ALERT+(255,))
    # headline
    d.text((R_, 650), 'عملاءنا الكرام..', font=F(AR_BLACK, 70), fill=Wh+(255,), anchor='rs', direction='rtl', language='ar')
    d.text((R_, 752), 'لسلامتكم', font=F(AR_BLACK, 104), fill=ALERT_HI+(255,), anchor='rs', direction='rtl', language='ar')
    # message
    fb = F(CT_FONT, 38)
    lines, sp = nc.wrap(nc.tokens([('نرجو منكم أخذ الحيطة والحذر جراء', Wh), ('الأمطار الغزيرة والسيول', ALERT_HI),
                                   ('وإغلاقات بعض الشوارع.', Wh)]), fb, R_ - M - 40)
    y = 780
    d.rectangle((R_-8, y, R_, y+len(lines)*64+20), fill=ALERT_HI+(255,))
    nc.draw_lines(d, lines, sp, fb, R_-30, y+52, 64)
    # two do-not rules
    y = 780 + len(lines)*64 + 34
    rules = [(icon_no_entry, 'تجنّبوا جميع الطرق المغلقة'),
             (icon_waves, 'لا تدخلوا مناطق تجمّع المياه مهما كانت')]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rh = 104
    for i in range(len(rules)):
        ld.rectangle((M, y+i*(rh+14), R_, y+i*(rh+14)+rh), fill=BLOOD+(232,), outline=ALERT+(255,), width=2)
    cv.alpha_composite(lay); d = ImageDraw.Draw(cv)
    fr = F(AR_BLACK, 38)
    for i, (ic, txt) in enumerate(rules):
        ry = y + i*(rh+14)
        ic(d, R_-70, ry+rh/2, 64, ALERT)
        size = 38
        while w_ar(txt, F(AR_BLACK, size)) > R_-M-150: size -= 2
        d.text((R_-122, ry+rh/2+6), txt, font=F(AR_BLACK, size), fill=Wh+(255,), anchor='rm', direction='rtl', language='ar')
    # help line + footer
    y = y + len(rules)*(rh+14) + 30
    fh = F(AR_BOLD, 32)
    d.text((R_, y+30), 'للمساعدة أو الاستفسار تواصلوا معنا', font=fh, fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')
    ic = load_icons(34); fc = F(nc.CT_FONT, 29); fy = 1292; x = M
    for k in ('ig', 'fb'):
        cv.alpha_composite(ic[k], (x, fy-17)); x += 44
    d.text((x+6, fy+2), 'callrenttr', font=fc, fill=Wh+(255,), anchor='lm', direction='ltr', language='en')
    d.text((R_, fy+2), '+90 555 034 22 00', font=F(nc.CT_FONT, 34), fill=Wh+(255,), anchor='rm', direction='ltr', language='en')
    # red frame round the whole post
    d.rectangle((0, 0, W-1, H-1), outline=ALERT+(255,), width=14)
    d.rectangle((22, 22, W-23, H-23), outline=ALERT_HI+(140,), width=2)
    cv.convert('RGB').save(out, quality=95); print(out)


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[3])
