"""Brand-tinted real basemap (Esri Light Gray Base, recoloured) at three zooms around the CALL & RENT office."""
import os, numpy as np
from PIL import Image, ImageFilter
import tiles
D=os.path.dirname(os.path.abspath(__file__))
OFFICE=(41.1253817,28.7696167)     # exact, from the client's Google Maps link
W,H=1080,1920
# grey -> colour ramp: water 208, land 239, roads/white above
_K=np.array([0,190,208,214,226,236,239,242,255],np.float32)
_C=np.array([(150,185,210),(176,212,234),(190,222,240),(206,214,214),(226,221,212),(244,240,232),(250,247,240),(255,255,255),(255,255,255)],np.float32)
LUT=np.stack([np.interp(np.arange(256),_K,_C[:,c]) for c in range(3)],1).astype(np.uint8)
def recolor(im):
    g=np.asarray(im.convert('L')); return Image.fromarray(LUT[g])
def level(name,lat,lon,z,render_w,out_w=W,out_h=H):
    """mosaic at integer zoom z rendered render_w wide, resampled to out_w (fractional effective zoom)"""
    fn=os.path.join(D,f'lvl_{name}.png')
    k=render_w/out_w; rh=int(out_h*k)
    im,org=tiles.mosaic(lat,lon,z,render_w,rh)
    if not os.path.exists(fn):
        im=recolor(im).resize((out_w,out_h),Image.LANCZOS)
        a=np.asarray(im,np.float32)+np.random.default_rng(3).normal(0,1.2,(out_h,out_w,1)); Image.fromarray(a.clip(0,255).astype('uint8')).save(fn)
    x0,y0,_=org
    def P(la,lo):
        x,y=tiles.ll2px(la,lo,z); return (x-x0)/k,(y-y0)/k
    return Image.open(fn).convert('RGBA'),P
LEVELS={}
def get(name):
    if name not in LEVELS:
        spec={'street':(OFFICE[0],OFFICE[1],15,1080),
              'city':(41.07,28.93,11,1300),
              'region':(40.70,29.47,10,1320)}[name]
        LEVELS[name]=level(name,*spec)
    return LEVELS[name]
if __name__=='__main__':
    for n in ('street','city','region'):
        im,P=get(n); im.convert('RGB').resize((270,480)).save(f'real_{n}_s.jpg'); print(n,P(*OFFICE))
