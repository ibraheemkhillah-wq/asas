"""Airport pick-up reel «المفتاح على السير» — final edit (27 s, 24 fps), rendered once, muxed with three music beds."""
import sys, os, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
import sb
from sb import W,H,F,B,OR,WHITE,MUTED,text,shade,logo,contacts
FPS=24
def ramp(t,a,b): return float(np.clip((t-a)/(b-a),0,1))
def ease(x): return 1-(1-x)**3
def faded(L,a):
    if a>=1: return L
    L=L.copy(); L.putalpha(L.split()[3].point(lambda v:int(v*a))); return L
NF={c:len(os.listdir(f'clips/x{c}')) for c in ('1v2','2','3','4','5','6v2','7')}
def clip(c,ct):
    i=int(np.clip(round(ct*FPS),0,NF[c]-1))+1
    return Image.open(f'clips/x{c}/{i:03d}.jpg').convert('RGBA')
def zoom(im,s):
    if s<=1.0005: return im
    w,h=W/s,H/s; return im.resize((W,H),Image.BICUBIC,box=((W-w)/2,(H-h)/2,(W+w)/2,(H+h)/2))
# (timeline start, end, clip, clip-time at start)
EDL=[(0.0, 5.0,'1v2',0.0),     # carousel: belt carries the bags, tray arrives
     (5.0, 8.0,'2',  0.3),     # same shot: hand from the right takes the key
     (8.0,10.5,'3',  1.2),     # unlock press lands at ~10.2
     (10.5,14.0,'4', 0.0),     # car answers: indicators flash on the hit
     (14.0,17.0,'5', 0.3),     # traveller walks to the car
     (17.0,20.0,'6v2',1.6),    # bag in, tailgate shuts (~19.6) — first second skipped
     (20.0,23.5,'7', 0.0)]     # drive away past the control tower
FIN=23.5; DUR=27.0; N=int(DUR*FPS)
def layer(fn):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); fn(L); return L
HOOK1=layer(lambda L:text(L,'أوّل ما يصلك في المطار',240,72))
HOOK2=layer(lambda L:text(L,'ليس حقيبتك',360,100,OR))
E1=layer(lambda L:text(L,'حقيبتك تأخّرت؟',560,84))
E2=layer(lambda L:text(L,'سيارتك لا',680,96,OR))
E3=layer(lambda L:text(L,'استلام وتسليم في المطار',820,52,(225,230,238),F(B.AR_BOLD,52)))
LOGO=layer(lambda L:logo(L,1040)); _lh=Image.open(B.LOGO_WHITE).size; LH=int(620*_lh[1]/_lh[0])
CONT=layer(lambda L:contacts(L,1040+LH+110))
NOTE=layer(lambda L:text(L,'الخدمة برسوم إضافية · وفق الشروط والأحكام',1830,28,MUTED,F('NotoKufiArabic-Regular.ttf',28)))
def show(fr,L,a,rise=22):
    if a<=0: return
    fr.alpha_composite(faded(L,a),(0,int(rise*(1-a))))
END_BG=None
def finale_bg(v):
    global END_BG
    ct=3.5+v
    if ct<=5.0: base=clip('7',ct)
    else:
        if END_BG is None: END_BG=clip('7',5.0)
        base=END_BG
    k=ease(ramp(v,0.0,1.0))
    fr=base.filter(ImageFilter.GaussianBlur(14*k)) if k>0.02 else base.copy()
    fr.alpha_composite(Image.new('RGBA',(W,H),(6,9,14,int(175*k)))); return fr
def render(f):
    t=f/FPS
    if t<FIN:
        for a,b,c,c0 in EDL:
            if t<b: break
        u=(t-a)/(b-a)
        fr=zoom(clip(c,c0+(t-a)),1.0+0.025*u)          # gentle continuous push on every shot
        if c in ('1v2','2'):                             # hook text on the continuous carousel take
            ha=ease(ramp(t,3.0,3.5))*(1-ramp(t,6.6,7.1))
            if ha>0:
                sh=fr.copy(); shade(sh,top=560); fr=Image.blend(fr,sh,ha)
                show(fr,HOOK1,ease(ramp(t,3.0,3.5))*(1-ramp(t,6.6,7.1)))
                show(fr,HOOK2,ease(ramp(t,3.7,4.2))*(1-ramp(t,6.6,7.1)))
        if t<0.35: fr=Image.blend(Image.new('RGBA',(W,H),(0,0,0,255)),fr,ramp(t,0,0.35))
        if t>FIN-0.25: fr=Image.blend(fr,finale_bg(0.0),ramp(t,FIN-0.25,FIN))
    else:
        v=t-FIN; fr=finale_bg(v)
        show(fr,E1,ease(ramp(v,0.35,0.8))); show(fr,E2,ease(ramp(v,0.65,1.1)))
        show(fr,E3,ease(ramp(v,0.95,1.4)),12)
        la=ramp(v,1.25,1.85)
        if la>0:
            s=0.9+0.1*ease(la); L=faded(LOGO,min(1,la*1.6))
            if s<1: L=L.resize((int(W*s),int(H*s)),Image.LANCZOS); tmp=Image.new('RGBA',(W,H),(0,0,0,0)); tmp.alpha_composite(L,(int((W-L.width)/2),int((1040+LH/2)*(1-s)))); L=tmp
            fr.alpha_composite(L)
        show(fr,CONT,ease(ramp(v,1.7,2.15)),28); show(fr,NOTE,ease(ramp(v,2.0,2.4)),10)
        if v>DUR-FIN-0.4: fr=Image.blend(fr,Image.new('RGBA',(W,H),(0,0,0,255)),ramp(v,DUR-FIN-0.4,DUR-FIN)*0.0)
    return fr.convert('RGB')

# ---------------- sound ----------------
SR=48000
def aload(FF,fn,ss=None,d=None,af=None):
    cmd=[FF,'-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-t',str(d)] if d else [])+['-i',fn]+(['-af',af] if af else [])+['-ac','2','-ar',str(SR),'-f','s16le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,'<i2').reshape(-1,2).astype(np.float32)/32768
def rms(x): return float(np.sqrt((x**2).mean())+1e-9)
MUSIC={'A':('snd/music_679.mp3',70.4,'Epical Drums 04'),'B':('snd/music_614.mp3',69.6,'Silent Descent'),'C':('snd/music_770.mp3',204.4,'Autofahren')}
HIT=10.5
def refine_drop(FF,fn,tdrop):
    x=aload(FF,fn,tdrop-0.6,1.2).mean(1); e=np.array([rms(x[i:i+480]) for i in range(0,len(x)-480,240)])
    on=np.diff(e); return tdrop-0.6+(int(np.argmax(on))+1)*240/SR
def mix(FF,key,out_wav):
    Nn=int(DUR*SR); o=np.zeros((Nn,2),np.float32)
    def place(x,t,g,fin=0.0,fade=0.0):
        x=x.copy()
        if fin: k=min(len(x),int(fin*SR)); x[:k]*=np.linspace(0,1,k)[:,None]
        if fade: k=min(len(x),int(fade*SR)); x[-k:]*=np.linspace(1,0,k)[:,None]
        s=int(t*SR); n=min(len(x),Nn-s)
        if n>0: o[s:s+n]+=x[:n]*g
    # 1) native clip audio, cut exactly with the picture (it is synced: belt hum, key, click, chirp, steps, trunk slam, engine)
    nat=np.zeros_like(o)
    for a,b,c,c0 in EDL:
        x=aload(FF,f'clips/{c}.mp4',c0,b-a,af='highpass=f=60,lowpass=f=9000')
        x=x/ (np.abs(x).max()+1e-9)
        s=int(a*SR); n=min(len(x),Nn-s); k=int(0.03*SR)
        x[:k]*=np.linspace(0,1,k)[:,None]; x[n-k:n]*=np.linspace(1,0,k)[:,None]
        g={'1v2':0.30,'2':0.32,'3':0.42,'4':0.40,'5':0.30,'6v2':0.45,'7':0.42}[c]
        nat[s:s+n]+=x[:n]*g
    # the hook breath: native sound gets the room while the music dips
    o+=nat*0.55
    # 2) music: its strongest lift lands on the car flash (10.5 s)
    fn,td,_=MUSIC[key]; td=refine_drop(FF,fn,td); start=td-HIT
    m=aload(FF,fn,start,DUR+0.5)[:Nn]; m=m/rms(m)*0.11
    tt=np.arange(len(m))/SR
    env=np.clip(tt/1.2,0,1)                                   # fade in
    env*=1-0.72*np.clip((tt-2.9)/0.25,0,1)*np.clip((4.6-tt)/0.6,0,1)   # sudden hush when the tray appears
    env*=np.where(tt<HIT,0.75,1.0)                            # held back until the car answers
    env*=np.clip((DUR-tt)/2.2,0,1)                            # long tail into the end card
    place(m*env[:,None],0,1.0)
    # 3) accents
    imp=aload(FF,'snd/drum_impact.mp3'); imp=imp/rms(imp)*0.05; place(imp,HIT-0.03,1.0,fade=1.5)
    lg=aload(FF,'snd/logo_impact.mp3'); lg=lg/rms(lg)*0.05; place(lg,FIN+1.25,1.0,fade=2.0)
    mx=np.abs(o).max(); o=o/mx*0.95 if mx>0.95 else o
    with wave.open(out_wav,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(o,-1,1)*32767).astype('<i2').tobytes())
    subprocess.run([FF,'-v','error','-y','-i',out_wav,'-af','loudnorm=I=-14:TP=-1.0:LRA=9','-ar','48000',out_wav.replace('.wav','_n.wav')],check=True)
def chunk(FF,a,b):
    os.makedirs('rchunks',exist_ok=True)
    p=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','fast','-crf','10','-pix_fmt','yuv420p',f'rchunks/{a:05d}.mp4'],stdin=subprocess.PIPE)
    for f in range(a,b): p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
def video(FF):
    with open('rchunks/list.txt','w') as fh:
        for fn in sorted(x for x in os.listdir('rchunks') if x.endswith('.mp4')): fh.write(f"file '{fn}'\n")
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i','rchunks/list.txt','-c','copy','rall.mp4'],check=True)
    for p in (1,2):
        cmd=[FF,'-v','error','-y','-i','rall.mp4','-c:v','libx264','-b:v','7000k','-maxrate','11000k','-bufsize','14000k','-preset','veryslow','-tune','film','-pix_fmt','yuv420p','-pass',str(p),'-passlogfile','x264air','-an']
        cmd+=(['-f','mp4','/dev/null'] if p==1 else ['-movflags','+faststart','rvideo.mp4'])
        subprocess.run(cmd,check=True)
def mux(FF,key,out):
    mix(FF,key,f'mix_{key}.wav')
    subprocess.run([FF,'-v','error','-y','-i','rvideo.mp4','-i',f'mix_{key}_n.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],check=True)
if __name__=='__main__':
    import imageio_ffmpeg; FF=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=sys.argv[1]
    if cmd=='chunk': chunk(FF,int(sys.argv[2]),min(N,int(sys.argv[3])))
    elif cmd=='video': video(FF)
    elif cmd=='mux': mux(FF,sys.argv[2],sys.argv[3])
    elif cmd=='check':
        ts=[float(x) for x in sys.argv[2:]]; fr=[render(int(t*FPS)).resize((270,480)) for t in ts]
        s=Image.new('RGB',(270*len(fr),480))
        for i,im in enumerate(fr): s.paste(im,(270*i,0))
        s.save('/tmp/claude-0/-home-user-asas/d21a85a7-6665-5900-89b1-ab98434bf7ea/scratchpad/reel_chk.jpg'); print('ok')
