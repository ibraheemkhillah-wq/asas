import sys
KIT, SCENE, OUT = sys.argv[1:4]
sys.path.insert(0, KIT)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE, LOGONAVY, WHITE, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar

W, H = 1080, 1350
sc = Image.open(SCENE).convert('RGB')

# --- plate with the new logo (source pixels, before scaling) --------------------
px0, py0, px1, py1 = 592, 592, 711, 625
S = 6
pl = Image.new('RGBA', ((px1-px0)*S, (py1-py0)*S), (226, 228, 231, 255))
lg = Image.open(LOGO_NAVY).convert('RGBA')
lh = round(pl.height*0.74); lw = round(lh*lg.width/lg.height)
if lw > pl.width*0.88: lw = round(pl.width*0.88); lh = round(lw*lg.height/lg.width)
pl.alpha_composite(lg.resize((lw, lh), Image.LANCZOS), ((pl.width-lw)//2, (pl.height-lh)//2))
pl = pl.resize((px1-px0, py1-py0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.35))
sc = sc.convert('RGBA'); sc.alpha_composite(pl, (px0, py0))

cv = sc.resize((W, round(sc.height*W/sc.width)), Image.LANCZOS)   # 1080 x 1350
cv = cv.crop((0, 0, W, H))

# --- pale bottom like the original: soft white fade under the car ---------------
ys = np.arange(H, dtype=np.float32)
al = np.clip((ys-900)/240, 0, 1)**1.3*0.86
fade = Image.new('RGBA', (W, H), (238, 241, 245, 0))
fade.putalpha(Image.fromarray((np.repeat(al[:, None], W, 1)*255).astype(np.uint8)))
cv.alpha_composite(fade)
# and a light veil behind the logo for contrast on the cloudy sky
top = np.clip(1-(ys/260), 0, 1)**1.5*0.45
veil = Image.new('RGBA', (W, H), (240, 243, 247, 0))
veil.putalpha(Image.fromarray((np.repeat(top[:, None], W, 1)*255).astype(np.uint8)))
cv.alpha_composite(veil)

d = ImageDraw.Draw(cv)
lg2 = lg.resize((280, round(280*lg.height/lg.width)), Image.LANCZOS)
cv.alpha_composite(lg2, (56, 58))

fb = F(AR_BOLD, 28); bt = 'من خدماتنا'
bw = w_ar(bt, fb) + 70; bh = 66; bx = W-40-bw; by = 58
d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=LOGONAVY+(255,))
d.polygon([(bx, by+bh-24), (bx, by+bh), (bx+24, by+bh)], fill=ORANGE+(255,))
d.text((bx+bw/2, by+bh/2+2), bt, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')

R_ = W-72
d.text((R_, 1016), 'الطريق إلك...', font=F(AR_BLACK, 58), fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
d.text((R_, 1100), 'والمسؤولية علينا', font=F(AR_BLACK, 68), fill=LOGONAVY+(255,), anchor='rs', direction='rtl', language='ar')
d.line([(430, 1138), (R_, 1138)], fill=LOGONAVY+(70,), width=2)
d.rectangle((690, 1134, 742, 1142), fill=ORANGE+(255,))
d.text((R_, 1190), 'تأمين شامل على كل حجز: حوادث، خدوش، وطرف ثالث', font=F(AR_BOLD, 27), fill=(48,70,92,255), anchor='rs', direction='rtl', language='ar')

ic = load_icons(22); fc = F(CT_FONT, 31)
for i, (keys, txt) in enumerate([(('fb','ig'), 'callrenttr'), (('ph','wa'), '+90 555 034 22 00')]):
    y = 1240 + i*60; x = 50
    for k in keys:
        d.ellipse((x, y-19, x+38, y+19), fill=LOGONAVY+(255,))
        cv.alpha_composite(ic[k], (x+8, y-11)); x += 38+14
    d.text((x+6, y+2), txt, font=fc, fill=LOGONAVY+(255,), anchor='lm', direction='ltr', language='en')

cv.convert('RGB').save(OUT, quality=95); print('ok')
