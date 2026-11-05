"""Fleet album base image: red i20 at the CALL & RENT shop, with a hanging Turkish-flag banner,
a light front plate carrying the logo, an empty sky for copy, and a branded contact footer."""
import sys, os, math
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','brand-kit')); os.chdir(HERE)
import numpy as np, brand as B
from PIL import Image, ImageDraw, ImageFilter
W,H=1080,1920; NAVY=B.LOGONAVY; OR=B.ORANGE

def tr_flag(G=600):
    Wf=int(G*1.5); im=Image.new('RGB',(Wf,G),(227,10,23)); d=ImageDraw.Draw(im)
    cy=G/2; ox=0.5*G; r1=0.25*G; ix=ox+0.0625*G; r2=0.2*G
    d.ellipse((ox-r1,cy-r1,ox+r1,cy+r1),fill=(255,255,255)); d.ellipse((ix-r2,cy-r2,ix+r2,cy+r2),fill=(227,10,23))
    sx=0.5*G+0.0625*G+0.2*G+G/3*0.5; sr=0.125*G
    d.polygon([(sx+(sr if k%2==0 else sr*0.382)*math.cos(math.pi+k*math.pi/5),cy+(sr if k%2==0 else sr*0.382)*math.sin(math.pi+k*math.pi/5)) for k in range(10)],fill=(255,255,255))
    return im

def banner(w,h):
    """vertical hanging banner (hoist at the top) with soft vertical folds and a gently waving hem"""
    f=tr_flag(h*2//3).rotate(-90,expand=True).resize((w,h),Image.LANCZOS)
    a=np.asarray(f,np.float32); xs=np.arange(w,dtype=np.float32); ys=np.arange(h,dtype=np.float32)[:,None]
    v=ys/h                                              # 0 at the rod, 1 at the hem
    fold=np.sin(2*np.pi*xs/(w/3.2)+0.6)[None,:]*(0.35+0.65*v) # folds deepen toward the free end
    shift=(fold*6*v).astype(np.float32)                 # cloth sways sideways a little
    src=np.clip(xs[None,:]+shift,0,w-1).astype(int)
    a=np.take_along_axis(a,np.repeat(src[...,None],3,2),1)
    light=1+0.26*np.sin(2*np.pi*xs/(w/3.2)+0.6+0.9)[None,:]*(0.45+0.55*v)   # sun catches one side of each fold
    light*=1+0.10*np.sin(2*np.pi*xs/(w/1.1)+2.0)[None,:]                        # one broad ripple across the cloth
    light*=1-0.10*v                                     # slightly darker toward the hem
    a=np.clip(a*light[...,None],0,255)
    grey=a.mean(2,keepdims=True); a=grey+(a-grey)*0.86                  # match the slightly hazy photo
    a=a*0.93+np.random.default_rng(2).normal(0,3.0,a.shape[:2]+(1,))
    hem=h-6-6*np.sin(2*np.pi*xs/(w/3.2)+0.6)            # wavy bottom edge
    alpha=(ys<hem[None,:]).astype(np.float32)*255
    im=Image.fromarray(np.dstack([np.clip(a,0,255),alpha]).astype('uint8'),'RGBA').filter(ImageFilter.GaussianBlur(0.7))
    return im

def solve_persp(dst,src):
    """coefficients for Image.transform(PERSPECTIVE): maps output (dst quad) to input (src quad)"""
    A=[];bv=[]
    for (x,y),(u,v) in zip(dst,src):
        A.append([x,y,1,0,0,0,-u*x,-u*y]); bv.append(u)
        A.append([0,0,0,x,y,1,-v*x,-v*y]); bv.append(v)
    return np.linalg.solve(np.array(A,float),np.array(bv,float)).tolist()

def plate(pw=520,ph=112):
    p=Image.new('RGBA',(pw,ph),(0,0,0,0)); d=ImageDraw.Draw(p)
    d.rounded_rectangle((0,0,pw-1,ph-1),radius=14,fill=(246,246,242,255),outline=(40,40,44,255),width=5)
    lg=Image.open(B.LOGO_NAVY).convert('RGBA'); lw=400; lg=lg.resize((lw,int(lw*lg.height/lg.width)),Image.LANCZOS)
    if lg.height>ph-22: lg=lg.resize((int(lg.width*(ph-22)/lg.height),ph-22),Image.LANCZOS)
    p.alpha_composite(lg,((pw-lg.width)//2,(ph-lg.height)//2))
    g=np.linspace(1.0,0.82,ph)[:,None,None]; a=np.asarray(p,np.float32); a[...,:3]*=g
    return Image.fromarray(np.clip(a,0,255).astype('uint8'),'RGBA')

def contacts_footer(fr):
    top=1650
    band=np.zeros((H-top,W,4),np.float32); t=np.linspace(0,1,H-top)[:,None]
    band[...,0]=NAVY[0]*0.55; band[...,1]=NAVY[1]*0.55; band[...,2]=NAVY[2]*0.55
    band[...,3]=np.clip(t*3.0,0,1)*235                  # fades in from the photo, solid at the bottom
    fr.alpha_composite(Image.fromarray(band.astype('uint8'),'RGBA'),(0,top))
    d=ImageDraw.Draw(fr)
    d.rounded_rectangle((W/2-150,top+78,W/2+150,top+84),radius=3,fill=OR+(255,))   # orange accent line
    fc=B.F(B.CT_FONT,50); isz=54
    ic={}
    for k,v in B.load_icons(isz).items():
        m=(np.asarray(v,np.float32)[...,3]*np.asarray(v.convert('L'),np.float32)/255).astype('uint8')
        t_=Image.new('RGBA',(isz,isz),(255,255,255,255)); t_.putalpha(Image.fromarray(m)); ic[k]=t_
    y=top+140
    for keys,txt in ((('wa','ph'),'+90 555 034 22 00'),(('ig','fb'),'callrenttr')):
        w=len(keys)*(isz+12)+10+d.textbbox((0,0),txt,font=fc)[2]; x=(W-w)/2
        for k in keys: fr.alpha_composite(ic[k],(int(x),int(y-isz/2))); x+=isz+12
        d.text((x+10,y),txt,font=fc,fill=(255,255,255),anchor='lm'); y+=82

def build(out='i20-red-album.jpg'):
    fr=Image.open('i20-red-full.png').convert('RGBA')   # lamp post removed + natural flag (AI edit, blended back into the original photo)
    # --- light front plate with the logo, warped onto the old plate
    dst=[(113,1400),(241,1433),(239,1485),(111,1451)]
    pl=plate(); pw,ph=pl.size
    coeff=solve_persp(dst,[(0,0),(pw,0),(pw,ph),(0,ph)])
    warped=pl.transform((W,H),Image.PERSPECTIVE,coeff,resample=Image.BICUBIC)
    warped=warped.filter(ImageFilter.GaussianBlur(0.5))
    fr.alpha_composite(warped)
    contacts_footer(fr)
    fr.convert('RGB').save(out,quality=95); return out

if __name__=='__main__':
    print(build())
