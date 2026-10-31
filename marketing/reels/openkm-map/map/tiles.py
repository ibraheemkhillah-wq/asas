"""Real basemap mosaics (Esri World Light Gray Base, no labels) — Esri, HERE, Garmin, © OpenStreetMap contributors.
Labels are drawn in Arabic on top, so the map stays clean and in standard Arabic."""
import os, math, time, subprocess
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(D,'tiles'); os.makedirs(CACHE,exist_ok=True)
URL='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
TS=256
def ll2px(lat,lon,z):
    s=TS*2**z; x=(lon+180)/360*s
    y=(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*s; return x,y
def px2ll(x,y,z):
    s=TS*2**z; return math.degrees(math.atan(math.sinh(math.pi*(1-2*y/s)))), x/s*360-180
def tile(z,x,y):
    fn=os.path.join(CACHE,f'{z}_{x}_{y}.png')
    if not os.path.exists(fn):
        u=URL.format(z=z,x=x,y=y)
        subprocess.run(['curl','-sS','-m','30','-A','CallRentReel/1.0 (one-off marketing render)','-o',fn,u],check=True); time.sleep(0.05)
    return Image.open(fn).convert('RGB')
def mosaic(lat,lon,z,w,h):
    """w x h px image centred on lat/lon at zoom z; returns image and the pixel origin (for projecting points)"""
    cx,cy=ll2px(lat,lon,z); x0,y0=cx-w/2,cy-h/2
    tx0,ty0,tx1,ty1=int(x0//TS),int(y0//TS),int((x0+w)//TS),int((y0+h)//TS)
    big=Image.new('RGB',((tx1-tx0+1)*TS,(ty1-ty0+1)*TS))
    for tx in range(tx0,tx1+1):
        for ty in range(ty0,ty1+1): big.paste(tile(z,tx,ty),((tx-tx0)*TS,(ty-ty0)*TS))
    ox,oy=x0-tx0*TS,y0-ty0*TS
    return big.crop((int(ox),int(oy),int(ox)+w,int(oy)+h)), (x0,y0,z)
def proj(origin,lat,lon):
    x0,y0,z=origin; x,y=ll2px(lat,lon,z); return x-x0,y-y0
