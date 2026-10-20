"""«عندك فكرة»: Auto Start/Stop — light theme, single image, title only (details live in the caption).

usage: python3 idea_start_stop.py <brand-kit dir> <out.png>
Photo: real Auto Start/Stop button (Perodua Myvi), Bindydad123, CC BY-SA 4.0 — credited on the image.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, HERE)
import news_carousel as nc
from news_carousel import W, H, M, R_, O, LOGONAVY, F, AR_BLACK, AR_BOLD, LT_TEXT, w_ar, w_lt
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.THEME = 'light'; nc.SECTION = 'idea'

# light field: white centre, cool grey edges
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
g = np.clip(np.sqrt(((xs-W/2)/W)**2 + ((ys-H*0.55)/H)**2)/0.7, 0, 1)[..., None]
bg = np.array((255, 255, 255), np.float32)*(1-g) + np.array((226, 233, 241), np.float32)*g
cv = Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
d = ImageDraw.Draw(cv)
nc.chrome(cv, d, 1, 1)                                  # navy logo, «عندك فكرة» badge, navy footer

# title
cx = W/2
d.text((cx, 236), 'ما هو نظام', font=F(AR_BLACK, 50), fill=LOGONAVY+(255,), anchor='ms', direction='rtl', language='ar')
fl = F('Oxanium-800.ttf', 104); t = 'Auto Start/Stop'
while w_lt(t, fl) > W - 2*M: fl = F('Oxanium-800.ttf', fl.size - 2)
d.text((cx, 352), t, font=fl, fill=O+(255,), anchor='ms')
d.text((cx, 442), 'وهل يضرّ سيارتك؟', font=F(AR_BLACK, 62), fill=LOGONAVY+(255,), anchor='ms', direction='rtl', language='ar')
d.rectangle((cx-60, 498, cx+60, 506), fill=O+(255,))

# photo card: the real button, framed, with a soft shadow
src = Image.open(os.path.join(HERE, 'src-start-stop-button-bindydad123.jpg')).convert('RGB')
crop = (190, 90, 1150, 810)                             # the A-OFF button centred
cw, ch = 900, 675; x0 = (W-cw)//2; y0 = 560
ph = src.crop(crop).resize((cw, ch), Image.LANCZOS)
ph = Image.blend(ph, Image.new('RGB', ph.size, (255, 255, 255)), 0.06)    # lift the blacks a touch
mask = Image.new('L', (cw, ch), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw-1, ch-1), radius=34, fill=255)
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((x0+10, y0+24, x0+cw-10, y0+ch+18), radius=40, fill=(29, 69, 99, 90))
cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
cv.paste(ph, (x0, y0), mask)
d = ImageDraw.Draw(cv)
d.rounded_rectangle((x0, y0, x0+cw-1, y0+ch-1), radius=34, outline=(255, 255, 255, 255), width=6)

# orange ring on the button's A-arrow icon (icon centre in source ≈ (660, 430))
sx = cw/(crop[2]-crop[0]); ix = x0 + (660-crop[0])*sx; iy = y0 + (452-crop[1])*sx; r = 150
for k, a in ((10, 70), (5, 255)):
    d.ellipse((ix-r-k, iy-r-k, ix+r+k, iy+r+k), outline=O+(a,), width=6 if k == 5 else 3)

# credit (the licence asks for it)
d.text((cx, y0+ch+44), 'Photo: Bindydad123 · CC BY-SA 4.0', font=F(LT_TEXT, 19), fill=(120, 138, 158, 255), anchor='ms')

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
