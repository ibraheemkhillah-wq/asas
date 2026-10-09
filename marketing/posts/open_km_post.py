import sys
KIT, SCENE, OUT = sys.argv[1:4]
sys.path.insert(0, KIT)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from brand import ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, LOGO_WHITE, load_icons, w_ar, w_lt

W, H = 1080, 1350
sc = Image.open(SCENE).convert('RGBA')
A = np.array(sc.convert('RGB')).astype(np.float32)

# --- plate: new navy logo on the blank plate, matched to the night exposure ---
px0, py0, px1, py1 = 566, 1209, 794, 1268
plate_rgb = tuple(int(v) for v in A[py0+4:py1-4, px0+6:px1-6].reshape(-1,3).mean(0))
S = 4
pl = Image.new('RGBA', ((px1-px0)*S, (py1-py0)*S), plate_rgb+(255,))
lg = Image.open(LOGO_NAVY).convert('RGBA')
lh = round(pl.height*0.72); lw = round(lh*lg.width/lg.height)
if lw > pl.width*0.86: lw = round(pl.width*0.86); lh = round(lw*lg.height/lg.width)
lgs = lg.resize((lw, lh), Image.LANCZOS)
r, g, b, a = lgs.split()
k = plate_rgb[0]/226
lgs = Image.merge('RGBA', (r.point(lambda v: int(v*k)), g.point(lambda v: int(v*k)), b.point(lambda v: int(v*k)), a))
pl.alpha_composite(lgs, ((pl.width-lw)//2, (pl.height-lh)//2))
pl = pl.resize((px1-px0, py1-py0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
sc.alpha_composite(pl, (px0, py0))

cv = sc.resize((W, H), Image.LANCZOS)

# --- grade: deep navy floor for the type, soft top for the logo ---------------
ys = np.arange(H, dtype=np.float32)
def band(alpha_col, rgb):
    lay = Image.new('RGBA', (W, H), rgb+(0,))
    lay.putalpha(Image.fromarray((np.repeat(alpha_col[:, None], W, 1)*255).astype(np.uint8)))
    cv.alpha_composite(lay)
band(np.clip((ys-850)/290, 0, 1)**1.1*0.86, (8, 24, 41))
band(np.clip(1-ys/210, 0, 1)**1.5*0.42, (8, 24, 41))
# corner vignette
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vg = np.clip(np.sqrt(((xx-W/2)/(W*0.75))**2 + ((yy-H*0.45)/(H*0.75))**2), 0, 1)**2.4*0.32
lay = Image.new('RGBA', (W, H), (4, 12, 22, 0)); lay.putalpha(Image.fromarray((vg*255).astype(np.uint8))); cv.alpha_composite(lay)

d = ImageDraw.Draw(cv)
M = 64; R_ = W - M

lw_ = Image.open(LOGO_WHITE).convert('RGBA'); LW = 290
lw_ = lw_.resize((LW, round(LW*lw_.height/lw_.width)), Image.LANCZOS)
cv.alpha_composite(lw_, (M-6, 40))

fb = F(AR_BOLD, 26); bt = 'من خدماتنا'
bw = w_ar(bt, fb) + 64; bh = 58; bx = R_ - bw; by = 46
d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=LOGONAVY+(255,), outline=(255,255,255,70), width=1)
d.polygon([(bx+1, by+bh-24), (bx+1, by+bh-1), (bx+24, by+bh-1)], fill=ORANGE+(255,))
d.text((bx+bw/2, by+bh/2+2), bt, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')

# eyebrow
fe = F(AR_BOLD, 26); et = 'كيلومترات مفتوحة'
d.text((R_, 930), et, font=fe, fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
ex = R_ - w_ar(et, fe) - 18
d.line([(ex-70, 920), (ex, 920)], fill=ORANGE+(255,), width=3)

d.text((R_, 1010), 'الطريق مفتوح...', font=F(AR_BLACK, 64), fill=WHITE+(255,), anchor='rs', direction='rtl', language='ar')
d.text((R_, 1096), 'والكيلومترات كمان', font=F(AR_BLACK, 72), fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
d.text((R_, 1150), 'سوق من اسطنبول لوين ما بدك، بدون حد للمسافة', font=F(AR_BOLD, 28), fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')

d.line([(M, 1200), (R_, 1200)], fill=ORANGE+(140,), width=2)
ic = load_icons(38); fc = F(CT_FONT, 32); y = 1262
x = M
for kk in ('ig','fb'):
    cv.alpha_composite(ic[kk], (x, y-19)); x += 38+12
d.text((x+8, y+2), 'callrenttr', font=fc, fill=WHITE+(255,), anchor='lm', direction='ltr', language='en')
num = '+90 555 034 22 00'
x = R_ - w_lt(num, fc) - 8 - 2*(38+12)
for kk in ('wa','ph'):
    cv.alpha_composite(ic[kk], (x, y-19)); x += 38+12
d.text((R_, y+2), num, font=fc, fill=WHITE+(255,), anchor='rm', direction='ltr', language='en')

cv.convert('RGB').save(OUT, quality=95); print('ok', plate_rgb)
