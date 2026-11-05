"""Place a real fleet car (background removed) in front of the CALL & RENT shop, with ground shadows and the contact footer."""
import sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import album as A
W,H=1080,1920
CARS={ # name: (target width, bottom y of tyres, centre x, colour tweak)
 'bayon-teal': (900,1600,520,1.00),
 'tiggo-grey': (900,1610,540,1.06),
 'clio5-white':(890,1600,525,1.00),
 'clio6-grey': (930,1605,530,1.04),
}
def compose(name):
    tw,by,cx,sat=CARS[name]
    bg=Image.open('shop-empty.png').convert('RGBA')
    car=Image.open(f'cars/{name}-cut.png').convert('RGBA')
    a=np.asarray(car)[...,3]; ys,xs=np.nonzero(a>40); car=car.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    s=tw/car.width; car=car.resize((tw,int(car.height*s)),Image.LANCZOS)
    rgb=car.convert('RGB'); rgb=ImageEnhance.Color(rgb).enhance(sat); rgb=ImageEnhance.Contrast(rgb).enhance(1.03)
    car=Image.merge('RGBA',(*rgb.split(),car.split()[3]))
    x0=int(cx-car.width/2); y0=int(by-car.height)
    # shadows: soft ambient pool + dark contact line under the tyres
    al=np.asarray(car.split()[3],np.float32)/255
    foot=np.zeros((H,W),np.float32)
    col=al.max(0)                                            # columns occupied by the car
    for k in range(car.width):
        if col[k]<0.3: continue
        rows=np.nonzero(al[:,k]>0.3)[0]; yb=y0+rows.max()
        foot[max(0,yb-10):min(H,yb+6),x0+k]=1.0
    pool=Image.fromarray((foot*255).astype('uint8')).filter(ImageFilter.GaussianBlur(4))
    amb=Image.new('L',(W,H),0)
    from PIL import ImageDraw
    ImageDraw.Draw(amb).ellipse((x0+10,by-95,x0+car.width-10,by+22),fill=235)          # dark pool under the body
    amb=amb.filter(ImageFilter.GaussianBlur(22))
    # cast shadow: the car silhouette flattened onto the ground, thrown toward the lower-left like the scene's sun
    sil=car.split()[3].resize((car.width,max(1,int(car.height*0.22))),Image.LANCZOS)
    cast=Image.new('L',(W,H),0); cast.paste(sil,(x0-70,by-int(sil.height*0.55)),sil)
    cast=cast.filter(ImageFilter.GaussianBlur(16))
    sh=np.maximum.reduce([np.asarray(amb,np.float32)/255*0.82,np.asarray(cast,np.float32)/255*0.55,np.asarray(pool,np.float32)/255*0.95])
    shl=Image.new('RGBA',(W,H),(12,10,8,0)); shl.putalpha(Image.fromarray((sh*255).astype('uint8')))
    bg.alpha_composite(shl); bg.alpha_composite(car,(x0,y0))
    A.contacts_footer(bg)
    out=f'{name}-album.jpg'; bg.convert('RGB').save(out,quality=95); return out
if __name__=='__main__':
    for n in (sys.argv[1:] or CARS): print(compose(n))
