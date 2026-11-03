"""Make the static carousel belt in clip 1 travel with the suitcases (flow-map scroll of the belt texture, masked to the empty belt)."""
import sys, os, numpy as np
from PIL import Image, ImageFilter
SRC='clips/fr1'; OUT='clips/fr1b'; os.makedirs(OUT,exist_ok=True)
W,H=1080,1920
T=np.array([-0.42,0.91]); T/=np.linalg.norm(T)          # travel direction (down-left, toward camera)
P=120.0; V=4.2                                          # slat period along travel, px per frame
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
region=((yy>(830-0.14*xx)) & (yy<1450) & (xx<900)).astype(np.float32)
def beltmask(a):
    lum=a.mean(2); sat=a.max(2)-a.min(2); r,g=a[...,0],a[...,1]
    obj=((lum>46)&(g>34)) | ((r-g>20)&(r>48)) | (sat>45)       # tray rim, red highlights, coloured bags
    obj&=(yy>(845-0.14*xx))
    firsty=np.full(W,1450.0,np.float32)
    for x in range(0,W):
        ys=np.nonzero(obj[:,x])[0]
        if len(ys): firsty[x]=ys[0]
    # smooth the boundary and keep a safety margin above objects
    k=31; pad=np.pad(firsty,(k//2,k//2),mode='edge'); firsty=np.array([np.min(pad[i:i+k]) for i in range(W)])-28
    m=((yy>(840-0.14*xx)) & (yy<firsty[None,:]) & (xx<880)).astype(np.float32)
    m=np.asarray(Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.GaussianBlur(10)),np.float32)/255
    return m
def shift(im,d):
    dx,dy=T*d
    return im.transform(im.size,Image.AFFINE,(1,0,-dx,0,1,-dy),resample=Image.BILINEAR)
def frame(i):
    im=Image.open(f'{SRC}/{i:03d}.jpg').convert('RGB'); a=np.asarray(im,np.float32)
    m=beltmask(a); mi=Image.fromarray((m*255).astype('uint8'))
    ph=(V*i/P)%1.0
    out=a.copy(); acc=np.zeros_like(a); wsum=np.zeros(a.shape[:2],np.float32)
    for off,w in ((ph,1-abs(1-2*ph)),((ph+0.5)%1.0,abs(1-2*ph))):
        d=off*P
        s=np.asarray(shift(im,d),np.float32); sm=np.asarray(shift(mi,d),np.float32)/255
        ww=w*sm; acc+=s*ww[...,None]; wsum+=ww
    moved=acc/np.maximum(wsum,1e-3)[...,None]
    k=np.clip(wsum,0,1)*m
    moved=np.asarray(Image.fromarray(np.clip(moved,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7)),np.float32)
    out=a*(1-k[...,None])+moved*k[...,None]
    Image.fromarray(np.clip(out,0,255).astype('uint8')).save(f'{OUT}/{i:03d}.jpg',quality=95)
if __name__=='__main__':
    a,b=int(sys.argv[1]),int(sys.argv[2])
    for i in range(a,b): frame(i)
