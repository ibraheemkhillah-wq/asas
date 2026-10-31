"""Light, elegant Turkey map drawn from world-atlas TopoJSON (50m) — base for the «خريطة بخط واحد» reel."""
import json, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
W,H=1080,1920
TOPO=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'dl/countries-50m.json')))
SC,TR=TOPO['transform']['scale'],TOPO['transform']['translate']
ARCS=[]
for arc in TOPO['arcs']:
    a=np.cumsum(np.array(arc,dtype=np.float64),0); ARCS.append(np.c_[a[:,0]*SC[0]+TR[0],a[:,1]*SC[1]+TR[1]])
def ring(idx):
    pts=[]
    for i in idx:
        a=ARCS[i] if i>=0 else ARCS[~i][::-1]
        pts.extend(a[1:] if pts else a)
    return np.array(pts)
def polys(geom):
    t=geom['type']; arcs=geom.get('arcs',[])
    if t=='Polygon': return [[ring(r) for r in arcs]]
    if t=='MultiPolygon': return [[ring(r) for r in p] for p in arcs]
    return []
COUNTRIES={g['properties']['name']:polys(g) for g in TOPO['objects']['countries']['geometries'] if 'properties' in g}

# view: Turkey centred, vertical frame; equirectangular with cos(lat) correction
LON0,LAT0=35.2,39.0; KX=np.cos(np.radians(LAT0))
def proj(lon,lat,scale=58.0,cx=W/2,cy=H/2):
    return cx+(lon-LON0)*KX*scale, cy-(lat-LAT0)*scale
SEA=(214,232,242); LAND=(246,243,236); NEIGH=(236,233,226); TURK=(255,252,246); EDGE=(200,196,186)
def base_map(scale=58.0):
    im=Image.new('RGB',(W,H),SEA); d=ImageDraw.Draw(im)
    for name,ps in COUNTRIES.items():
        for p in ps:
            for k,r in enumerate(p):
                xy=[proj(lo,la,scale) for lo,la in r]
                if len(xy)<3: continue
                fill=TURK if name=='Turkey' else NEIGH
                if k>0: fill=SEA
                d.polygon(xy,fill=fill)
    # coastline/borders, then a soft shadow lift on Turkey
    for name,ps in COUNTRIES.items():
        for p in ps:
            for r in p:
                xy=[proj(lo,la,scale) for lo,la in r]
                if len(xy)>2: d.line(xy+[xy[0]],fill=EDGE if name!='Turkey' else (190,180,165),width=2 if name!='Turkey' else 3)
    return im
CITIES={'إسطنبول':(28.98,41.01),'كبادوكيا':(34.83,38.64),'أنطاليا':(30.71,36.89),'طرابزون':(39.72,41.0),'أوزنجول':(40.29,40.62)}
if __name__=='__main__':
    im=base_map(); d=ImageDraw.Draw(im)
    for n,(lo,la) in CITIES.items():
        x,y=proj(lo,la); d.ellipse((x-8,y-8,x+8,y+8),fill=(244,141,87))
    im.save('map_chk.png'); print('ok')
