"""«عندك فكرة»: Auto Start/Stop — light theme, single image, title only (details live in the caption).

usage: python3 idea_start_stop.py <brand-kit dir> <out.png>
Background: Canva (idea-start-stop-scene.jpg), scaled into a matching light field under the title.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['CALLRENT_KIT'] = sys.argv[1]
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, HERE)
import news_carousel as nc
from news_carousel import W, H, O, LOGONAVY, F, AR_BLACK, w_ar, w_lt
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

nc.THEME = 'light'; nc.SECTION = 'idea'

scene = Image.open(os.path.join(HERE, 'idea-start-stop-scene.jpg')).convert('RGB')
A = np.array(scene).astype(np.float32)
top_c = A[:40].reshape(-1, 3).mean(0); bot_c = A[-40:].reshape(-1, 3).mean(0)
ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
field = top_c*(1-ys) + bot_c*ys
cv = Image.fromarray(np.repeat(field, W, 1).astype(np.uint8)).convert('RGBA')

# scene: scaled down and set low, its edges melted into the field
k = 0.84; sw, sh = round(W*k), round(H*k)
sc = scene.resize((sw, sh), Image.LANCZOS)
mask = Image.new('L', (sw, sh), 0); ImageDraw.Draw(mask).rectangle((50, 50, sw-50, sh-50), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(40))
cv.paste(sc, ((W-sw)//2, H - sh - 40), mask)

d = ImageDraw.Draw(cv)
nc.chrome(cv, d, 1, 1)                                  # navy logo, «عندك فكرة» badge, navy footer

# title: small Arabic lead, big Latin name in orange, Arabic question in navy
cx = W/2
d.text((cx, 236), 'ما هو نظام', font=F(AR_BLACK, 50), fill=LOGONAVY+(255,), anchor='ms', direction='rtl', language='ar')
fl = F('Oxanium-800.ttf', 104); t = 'Auto Start/Stop'
while w_lt(t, fl) > W - 2*nc.M: fl = F('Oxanium-800.ttf', fl.size - 2)
d.text((cx, 352), t, font=fl, fill=O+(255,), anchor='ms')
d.text((cx, 442), 'وهل يضرّ سيارتك؟', font=F(AR_BLACK, 62), fill=LOGONAVY+(255,), anchor='ms', direction='rtl', language='ar')
d.rectangle((cx-60, 498, cx+60, 506), fill=O+(255,))

cv.convert('RGB').save(sys.argv[2], optimize=True); print(sys.argv[2], cv.size)
