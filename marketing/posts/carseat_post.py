import sys, os
KIT = sys.argv[1]; SRC = sys.argv[2]; OUT = sys.argv[3]
sys.path.insert(0, KIT)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, cv2
from brand import ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, LT_REG, CT_FONT, SLOGAN, LOGO_NAVY, load_icons, w_ar, w_lt

W, H = 1080, 1350
src = Image.open(SRC).convert('RGB')

# 1) remove the old logo + badge from the photo (inpaint the plain ceiling)
a = np.array(src)
g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
mask = np.zeros(g.shape, np.uint8)
logo_box = (30, 30, 400, 192)            # x0,y0,x1,y1 in source pixels
x0,y0,x1,y1 = logo_box
mask[y0:y1, x0:x1] = (g[y0:y1, x0:x1] < 190).astype(np.uint8)*255
mask = cv2.dilate(mask, np.ones((9,9),np.uint8))
mask[44:124, 728:1050] = 255             # old badge
a = cv2.inpaint(a, mask, 9, cv2.INPAINT_TELEA)
photo = Image.fromarray(a).resize((W, round(src.height*W/src.width)), Image.LANCZOS)

canvas = Image.new('RGBA', (W, H), (0,0,0,255))
canvas.paste(photo, (0,0))

# 2) graded navy panel with a curved top edge (always above the old panel's curve)
def edge(x): return 790 + 50*((W-x)/W)**2
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
KEY  = np.array([46,104,150], np.float32); DEEP = np.array([8,24,41], np.float32)
RL = np.sqrt(((xs-W*0.62)/1.3)**2 + ((ys-1000)/0.9)**2)/900
bg = DEEP + (KEY-DEEP)*np.exp(-0.5*(RL/0.5)**2)[...,None]
R = np.sqrt((xs-W/2)**2 + (ys-1070)**2)/900
bg = bg*(1-0.30*np.clip(R,0,1)**2.2)[...,None]
bg = np.clip(bg + np.random.default_rng(7).normal(0,2.0,(H,W,1)), 0, 255).astype(np.uint8)
panel = Image.fromarray(bg).convert('RGBA')
pm = Image.new('L', (W*4, H*4), 0)
pts = [(x*4, edge(x)*4) for x in range(0, W+1, 4)] + [(W*4, H*4), (0, H*4)]
ImageDraw.Draw(pm).polygon(pts, fill=255)
pm = pm.resize((W, H), Image.LANCZOS)
# soft shadow onto the photo
sh = Image.new('RGBA', (W,H), (4,12,22,0)); sh.putalpha(pm.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.55)))
sh = sh.transform((W,H), Image.AFFINE, (1,0,0,0,1,10))
canvas.alpha_composite(sh)
panel.putalpha(pm); canvas.alpha_composite(panel)
# orange hairline on the curve
ln = Image.new('RGBA', (W*4,H*4), (0,0,0,0))
ImageDraw.Draw(ln).line([(x*4, edge(x)*4) for x in range(0, W+1, 4)], fill=ORANGE+(255,), width=14)
canvas.alpha_composite(ln.resize((W,H), Image.LANCZOS))

d = ImageDraw.Draw(canvas)
M = 64; R_ = W - M

# 3) navy logo on the light ceiling
lg = Image.open(LOGO_NAVY).convert('RGBA'); LW = 300
lg = lg.resize((LW, round(LW*lg.height/lg.width)), Image.LANCZOS)
canvas.alpha_composite(lg, (M, 62))

# 4) badge: navy plate, white text, the logo's orange corner
fb = F(AR_BOLD, 30); bt = 'من خدماتنا'
bw = w_ar(bt, fb) + 56; bh = 66; bx = R_ - bw; by = 58
d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=8, fill=LOGONAVY+(255,))
d.polygon([(bx, by+bh-26), (bx, by+bh), (bx+26, by+bh)], fill=ORANGE+(255,))
d.text((bx+bw/2, by+bh/2+2), bt, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')

# 5) headline: white, key words orange
f1 = F(AR_BLACK, 70)
d.text((R_, 905), 'أصغر راكب عندك', font=f1, fill=WHITE+(255,), anchor='rs', direction='rtl', language='ar')
hot, rest = 'أهم مقعد', 'بالسيارة'
d.text((R_, 1010), hot, font=f1, fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
gap = w_ar(hot+' ', f1) - w_ar(hot, f1)
d.text((R_ - w_ar(hot, f1) - max(gap, 18), 1010), rest, font=f1, fill=WHITE+(255,), anchor='rs', direction='rtl', language='ar')

f3 = F(AR_BOLD, 31)
d.text((R_, 1078), 'كرسي معتمد ومثبّت قبل ما تستلم السيارة', font=f3, fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')

# 6) rule + contacts (left) + slogan (right)
d.line([(M, 1140), (R_, 1140)], fill=ORANGE+(150,), width=2)
ic = load_icons(38); fc = F(CT_FONT, 34)
for i, (keys, txt) in enumerate([(('ig','fb'), 'callrenttr'), (('wa','ph'), '+90 555 034 22 00')]):
    y = 1205 + i*68; x = M
    for k in keys:
        canvas.alpha_composite(ic[k], (x, y-19)); x += 38+12
    d.text((x+8, y+2), txt, font=fc, fill=WHITE+(255,), anchor='lm', direction='ltr', language='en')
fs = F(LT_REG, 25)
d.text((R_, 1239), SLOGAN, font=fs, fill=ORANGE+(255,), anchor='rm', direction='ltr', language='en')

canvas.convert('RGB').save(OUT, quality=95)
print('ok', OUT)
