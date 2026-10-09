import sys
KIT, SCENE, CAR, GMASK, OUT = sys.argv[1:6]
sys.path.insert(0, KIT)
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import numpy as np, cv2
from brand import ORANGE, LOGONAVY, WHITE, SOFT, F, AR_BLACK, AR_BOLD, CT_FONT, LOGO_NAVY, load_icons, w_ar

W, H = 1080, 1350
src = Image.open(SCENE).convert('RGB')
a = np.array(src)
g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)

# --- 1) clean the plate: old logo, old badge, the Genesis --------------------
mask = np.zeros(g.shape, np.uint8)
x0,y0,x1,y1 = 25, 40, 350, 175
mask[y0:y1, x0:x1] = (g[y0:y1, x0:x1] < 200).astype(np.uint8)*255
mask = cv2.dilate(mask, np.ones((9,9),np.uint8))
mask[50:135, 740:1056] = 255
gm = np.array(Image.open(GMASK).convert('L'))
gm[885:, :] = 0; gm[:, 860:] = 0
gm = cv2.dilate((gm > 20).astype(np.uint8)*255, np.ones((25,25),np.uint8))
mask = np.maximum(mask, gm)
a = cv2.inpaint(a, mask, 15, cv2.INPAINT_TELEA)

# rebuild the floor (clean pale plaza) and the water band behind the car
FL = 812
rng = np.random.default_rng(3)
for y in range(FL, a.shape[0]):
    t = (y-FL)/(a.shape[0]-FL)
    col = np.array([218,218,224])*(1-0.10*t) + np.array([-2,-1,2])*t
    a[y,:,:] = np.clip(col + rng.normal(0,1.2,(a.shape[1],3)), 0, 255)
WB = 725
# behind the hood: tile the real skyline from the clean right edge, feathered in
Y0, X0 = 440, 400
band = a[Y0:WB].astype(np.float32)
xs_src = 880 + (np.arange(a.shape[1]) % 200)
T = a[Y0:WB][:, xs_src].astype(np.float32)
T = cv2.GaussianBlur(T, (0,0), 1.6)
wm = (gm[Y0:WB] > 0).astype(np.float32); wm[:, :X0] = 0
wm = np.clip(cv2.GaussianBlur(cv2.dilate(wm, np.ones((15,15),np.uint8)), (0,0), 9)*1.4, 0, 1)
wm[(gm[Y0:WB] > 0) & (np.arange(a.shape[1])[None,:] >= X0)] = 1
a[Y0:WB] = (band*(1-wm[...,None]) + T*wm[...,None]).astype(np.uint8)
for y in range(WB, FL):
    xs_ = np.where(gm[y] > 0)[0]
    for x in xs_:
        a[y, x] = a[y, 860 + (x % 220)]
scene = Image.fromarray(a).convert('RGBA')

# --- 2) the real car ----------------------------------------------------------
car = Image.open(CAR).convert('RGBA'); car = car.crop(car.getbbox())
rgb = car.convert('RGB')
rgb = ImageEnhance.Brightness(rgb).enhance(1.05)
r_, g_, b_ = rgb.split()
rgb = Image.merge('RGB', (r_.point(lambda v: v*0.98), g_, b_.point(lambda v: min(255, v*1.03))))
car = Image.merge('RGBA', (*rgb.split(), car.getchannel('A')))
S = 0.82
car = car.resize((round(car.width*S), round(car.height*S)), Image.LANCZOS)
cx = 60
cy = round(832 - 385*S)                  # rear tyre lands on the floor line
# ground shadow from the car's own silhouette
al = Image.new('L', scene.size, 0); al.paste(car.getchannel('A'), (cx, cy+8))
cut = Image.new('L', scene.size, 0)
ImageDraw.Draw(cut).rectangle((0, cy+round(car.height*0.62), scene.width, scene.height), fill=255)
al = ImageChops.multiply(al, cut).filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v*0.55))
dark = Image.new('RGBA', scene.size, (30,38,50,0)); dark.putalpha(al)
scene.alpha_composite(dark)
scene.alpha_composite(car, (cx, cy))

# --- 3) layout ------------------------------------------------------------------
OFF = -46
photo = scene.resize((W, round(scene.height*W/scene.width)), Image.LANCZOS)
canvas = Image.new('RGBA', (W, H), (0,0,0,255))
canvas.alpha_composite(photo, (0, OFF))

def edge(x): return 958 + 20*(x/W)**2
ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
KEY = np.array([46,104,150], np.float32); DEEP = np.array([8,24,41], np.float32)
RL = np.sqrt(((xs-W*0.62)/1.3)**2 + ((ys-1110)/0.9)**2)/900
bg = DEEP + (KEY-DEEP)*np.exp(-0.5*(RL/0.5)**2)[...,None]
R = np.sqrt((xs-W/2)**2 + (ys-1110)**2)/900
bg = bg*(1-0.30*np.clip(R,0,1)**2.2)[...,None]
bg = np.clip(bg + np.random.default_rng(7).normal(0,2.0,(H,W,1)), 0, 255).astype(np.uint8)
panel = Image.fromarray(bg).convert('RGBA')
pm = Image.new('L', (W*4, H*4), 0)
ImageDraw.Draw(pm).polygon([(x*4, edge(x)*4) for x in range(0, W+1, 4)] + [(W*4, H*4), (0, H*4)], fill=255)
pm = pm.resize((W, H), Image.LANCZOS)
sh = Image.new('RGBA', (W,H), (4,12,22,0)); sh.putalpha(pm.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.45)))
canvas.alpha_composite(sh.transform((W,H), Image.AFFINE, (1,0,0,0,1,10)))
panel.putalpha(pm); canvas.alpha_composite(panel)
ln = Image.new('RGBA', (W*4,H*4), (0,0,0,0))
ImageDraw.Draw(ln).line([(x*4, edge(x)*4) for x in range(0, W+1, 4)], fill=ORANGE+(255,), width=14)
canvas.alpha_composite(ln.resize((W,H), Image.LANCZOS))

d = ImageDraw.Draw(canvas); M = 64; R_ = W - M
lg = Image.open(LOGO_NAVY).convert('RGBA'); LW = 300
lg = lg.resize((LW, round(LW*lg.height/lg.width)), Image.LANCZOS)
canvas.alpha_composite(lg, (M, 62))

fb = F(AR_BOLD, 30); bt = 'من خدماتنا'
bw = w_ar(bt, fb) + 56; bh = 66; bx = R_ - bw; by = 58
d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=8, fill=LOGONAVY+(255,))
d.polygon([(bx, by+bh-26), (bx, by+bh), (bx+26, by+bh)], fill=ORANGE+(255,))
d.text((bx+bw/2, by+bh/2+2), bt, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')

f1 = F(AR_BLACK, 58)
d.text((R_, 1046), 'الطريق إلك...', font=f1, fill=WHITE+(255,), anchor='rs', direction='rtl', language='ar')
d.text((R_, 1128), 'والمسؤولية علينا', font=f1, fill=ORANGE+(255,), anchor='rs', direction='rtl', language='ar')
f3 = F(AR_BOLD, 27)
d.text((R_, 1186), 'تأمين شامل على كل حجز: حوادث، خدوش، وطرف ثالث', font=f3, fill=SOFT+(255,), anchor='rs', direction='rtl', language='ar')

d.line([(M, 1226), (R_, 1226)], fill=ORANGE+(150,), width=2)
ic = load_icons(38); fc = F(CT_FONT, 32); y = 1284
x = M
for k in ('ig','fb'):
    canvas.alpha_composite(ic[k], (x, y-19)); x += 38+12
d.text((x+8, y+2), 'callrenttr', font=fc, fill=WHITE+(255,), anchor='lm', direction='ltr', language='en')
num = '+90 555 034 22 00'
from brand import w_lt
x = R_ - w_lt(num, fc) - 8 - 2*(38+12)
for k in ('wa','ph'):
    canvas.alpha_composite(ic[k], (x, y-19)); x += 38+12
d.text((R_, y+2), num, font=fc, fill=WHITE+(255,), anchor='rm', direction='ltr', language='en')

canvas.convert('RGB').save(OUT, quality=95)
print('ok')
