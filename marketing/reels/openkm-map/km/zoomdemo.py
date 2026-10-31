"""Zoom-out demo: office photo -> real satellite top-down (z18) -> clouds -> brand map street -> Istanbul -> region.
One continuous logarithmic zoom; the photo->satellite and satellite->map swaps hide behind passing clouds."""
import sys, os, math, subprocess, wave
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','map'))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import tiles, real
import mapboard3 as MB, boards as BD
from mapboard3 import W,H,F,B,NAVY,OFFICE
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
FPS=30; DUR=8.0; N=int(DUR*FPS)
def ramp(t,a,b): return float(np.clip((t-a)/(b-a),0,1))
def eio(x): return x*x*(3-2*x)

# ---- satellite + map layers as big canvases at a common "world zoom" ----
def sat_tile(z,x,y):
    os.makedirs('../map/sat',exist_ok=True)
    fn=os.path.join('../map/sat',f'{z}_{x}_{y}.jpg')
    if not os.path.exists(fn):
        subprocess.run(['curl','-sS','-m','30','-A','CallRentReel/1.0','-o',fn,f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],check=True)
    return Image.open(fn).convert('RGB')
def mosaic(src,z,w,h):
    cx,cy=tiles.ll2px(*OFFICE,z); x0,y0=cx-w/2,cy-h/2
    tx0,ty0,tx1,ty1=int(x0//256),int(y0//256),int((x0+w)//256),int((y0+h)//256)
    big=Image.new('RGB',((tx1-tx0+1)*256,(ty1-ty0+1)*256))
    for tx in range(tx0,tx1+1):
        for ty in range(ty0,ty1+1): big.paste(src(z,tx,ty),((tx-tx0)*256,(ty-ty0)*256))
    ox,oy=x0-tx0*256,y0-ty0*256; return big.crop((int(ox),int(oy),int(ox)+w,int(oy)+h))
def map_tile(z,x,y):
    a=np.asarray(real.recolor(tiles.tile(z,x,y)),np.float32); return Image.fromarray(np.clip(255-(255-a)*1.7,0,255).astype('uint8'))  # deeper tones so the map reads under clouds
# zoom pyramid centred on the office; each level covers the frame at its own zoom, z = "camera altitude"
LV={}
def level(kind,z):
    k=(kind,z)
    if k not in LV:
        LV[k]=mosaic(sat_tile if kind=='sat' else map_tile,z,1540,2740)
    return LV[k]
def view(kind,zf):
    """frame at fractional zoom zf: take integer level ceil(zf) and scale down"""
    zi=min(18,int(round(zf))); im=level(kind,zi); s=2**(zf-zi)          # 0.71..1.41
    w,h=W/s,H/s; cx,cy=im.width/2,im.height/2
    return im.resize((W,H),Image.BICUBIC,box=(cx-w/2,cy-h/2,cx+w/2,cy+h/2)).convert('RGBA')
# clouds: soft procedural layers that sweep outward as we rise
RNG=np.random.default_rng(7)
def cloud_tex(seed,size=(1080,1920)):
    r=np.random.default_rng(seed); a=np.zeros(size[::-1],np.float32)
    for sc,amp in ((8,1),(16,0.5),(32,0.25),(64,0.12)):
        n=r.random((size[1]//(size[0]//sc)+2,sc+2)).astype(np.float32)
        a+=np.asarray(Image.fromarray((n*255).astype('uint8')).resize(size,Image.BICUBIC),np.float32)/255*amp
    a=(a-a.min())/(a.max()-a.min()); return a
CLOUDS=[cloud_tex(s) for s in (1,2,3)]
def clouds(fr,k,t):
    """k: 0..1..0 cloud density (peaks at the swap)"""
    if k<=0: return fr
    out=fr.copy()
    for i,c in enumerate(CLOUDS):
        s=1.0+1.4*ramp(t%3,0,3)*(0.6+0.3*i)                                    # clouds rush past / outward
        cs=Image.fromarray((np.clip((c-0.56+0.22*k)*2.4,0,1)*255*min(0.92,k)).astype('uint8')).resize((int(W*s),int(H*s)),Image.BICUBIC)
        x0,y0=(cs.width-W)//2,(cs.height-H)//2; cs=cs.crop((x0,y0,x0+W,y0+H)).filter(ImageFilter.GaussianBlur(6))
        L=Image.new('RGBA',(W,H),(250,252,255,0)); L.putalpha(cs); out.alpha_composite(L)
    return out
OFFICE_IMG=MB.img('office_sunny_black')
def pin_on(fr,zf):
    s=0.9+0.3*ramp(zf,12,16); MB.office_pin(fr,W/2,H/2,s); return fr
T_START=Image.new('RGBA',(W,H),(0,0,0,0)); BD.text(T_START,'من هنا تبدأ الرحلة…',300,76,NAVY)
# timeline: 0-1.6 photo rising | 1.6-2.2 clouds -> satellite | 2.2-4.4 satellite zoom 18->15.6 | 4.4-5.0 clouds -> map | 5.0-8 map 15.6->10.2
def zf_at(t):
    if t<2.2: return 18.0
    u=ramp(t,2.2,8.0); return 18.0-7.8*eio(u)                                   # slow lift-off, fast climb, settles on the region
def render(f):
    t=f/FPS
    if t<1.9:
        u=ramp(t,0,1.9); fr=MB.cam if False else None
        z=1.15-0.25*eio(u); cy=1150-260*eio(u)
        w,h=W/z,H/z; x0=min(max(540-w/2,0),W-w); y0=min(max(cy-h/2,0),H-h)
        fr=OFFICE_IMG.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+w,y0+h)) if z>=1 else OFFICE_IMG.copy()
        if z<1:
            s=z; bg=view('sat',18); im=OFFICE_IMG.resize((int(W*s),int(H*s)),Image.BICUBIC); bg.alpha_composite(im,(int((W-W*s)/2),int((H-H*s)/2))); fr=bg
        fr=clouds(fr,math.sin(math.pi*ramp(t,1.3,2.5)),t)
    else:
        zf=zf_at(t)
        sat=view('sat',max(zf,15.0));
        if zf<15.0: sat=None
        m=view('map',zf) if zf<16.2 else None
        mix=ramp(zf,15.4,16.0)                                                   # 1 = satellite, 0 = map
        if m is None: fr=sat
        elif sat is None or mix<=0: fr=m
        else: fr=Image.blend(m,sat,mix)
        if t<2.5: fr=Image.blend(OFFICE_IMG,fr,ramp(t,1.9,2.5)) if False else fr
        fr=clouds(fr,max(math.sin(math.pi*ramp(t,1.3,2.5)),0.75*math.sin(math.pi*ramp(t,3.8,4.9))),t)
        if zf<16.6: pin_on(fr,zf)
        if t>5.6:
            a=ramp(t,5.6,6.0); L=T_START.copy(); L.putalpha(L.split()[3].point(lambda v:int(v*a))); fr.alpha_composite(L)
        MB.attribution(fr)
    return fr.convert('RGB')
SR=48000
def sound(FF,out):
    Nn=int(DUR*SR); o=np.zeros((Nn,2),np.float32)
    def place(x,t,g):
        s=int(t*SR); n=min(len(x),Nn-s); o[s:s+n]+=x[:n]*g
    def aload(fn,ss=None,d=None):
        cmd=[FF,'-v','error']+(['-ss',str(ss)] if ss else [])+(['-t',str(d)] if d else [])+['-i',fn,'-ac','2','-ar',str(SR),'-f','s16le','-']
        return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,'<i2').reshape(-1,2).astype(np.float32)/32768
    lvl=lambda x,r: x/(np.sqrt((x**2).mean())+1e-9)*r
    b=lvl(aload('sfx/s2472.mp3',20,2.5),0.05); b[-int(0.8*SR):]*=np.linspace(1,0,int(0.8*SR))[:,None]; place(b,0,1)
    # long airy rise: band-limited noise swelling with the climb
    nz=np.random.default_rng(1).normal(0,1,int(7.5*SR)); k=np.ones(60)/60; nz=np.convolve(nz,k,'same'); tt=np.arange(len(nz))/SR
    env=np.clip(tt/1.2,0,1)*np.clip((7.5-tt)/2.0,0,1)*(0.6+0.4*np.sin(np.pi*np.clip((tt-1.3)/1.2,0,1))+0.4*np.sin(np.pi*np.clip((tt-3.9)/1.2,0,1)))
    w=lvl(np.stack([nz,nz],1).astype(np.float32),0.06)*env[:,None]; place(w,0.5,1)
    m=lvl(aload('../seat/snd/m_180.mp3',0,DUR),0.03); place(m,0,1)
    tt=np.arange(int(0.35*SR))/SR; pop=(np.sin(2*np.pi*880*tt)*np.exp(-tt*14)); place(np.stack([pop,pop],1).astype(np.float32),5.0,0.05)
    mx=np.abs(o).max(); o=o/mx*0.95 if mx>0.95 else o
    with wave.open('zmix.wav','wb') as wv: wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((np.clip(o,-1,1)*32767).astype('<i2').tobytes())
    subprocess.run([FF,'-v','error','-y','-i','zmix.wav','-af','loudnorm=I=-16:TP=-1:LRA=9','-ar','48000','zmix_n.wav'],check=True)
    subprocess.run([FF,'-v','error','-y','-framerate',str(FPS),'-i','outz/%04d.png','-i','zmix_n.wav','-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],check=True)
if __name__=='__main__':
    import imageio_ffmpeg; FF=imageio_ffmpeg.get_ffmpeg_exe()
    if len(sys.argv)>1 and sys.argv[1]=='sound': sound(FF,'../final/CALLRENT-zoomout-demo.mp4'); print('encoded')
    else:
        os.makedirs('outz',exist_ok=True); a=int(sys.argv[1]) if len(sys.argv)>1 else 0; b=int(sys.argv[2]) if len(sys.argv)>2 else N
        for f in range(a,b): render(f).save(f'outz/{f:04d}.png',compress_level=1)
        print('rendered',a,b)
