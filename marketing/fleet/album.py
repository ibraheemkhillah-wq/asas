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
    fr=Image.open('i20-red-base.png').convert('RGBA'); a0=np.asarray(fr.convert('RGB'),np.float32)
    # --- remove the street-lamp post (pole + head) by copying the background beside it
    a=a0.copy(); yy_,xx_=np.mgrid[0:H,0:W]
    xl=987-0.03*(yy_-625)                                   # pole centre leans slightly
    pole=(np.abs(xx_-xl)<24)&(yy_>=618)&(yy_<=1068)
    head=(xx_>=978)&(xx_<=1078)&(yy_>=616)&(yy_<=655)
    for msk,dx in ((pole,44),(head,-110)):
        ys_,xs_=np.nonzero(msk); src=np.clip(xs_+dx,0,W-1); a[ys_,xs_]=a0[ys_,src]
    m=np.asarray(Image.fromarray(((pole|head)*255).astype('uint8')).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3)),np.float32)[...,None]/255
    a0=a0*(1-m)+a*m
    fr=Image.fromarray(np.clip(a0,0,255).astype('uint8')).convert('RGBA')
    # --- real fabric flag (photo cut-out) hanging from the top of the right-hand fascia
    fl=Image.open('flag_cutout.png').convert('RGBA'); bw=176; bh=int(bw*fl.height/fl.width); bx,by=805,610
    fl=fl.resize((bw,bh),Image.LANCZOS)
    fa=np.asarray(fl,np.float32); grey=fa[...,:3].mean(2,keepdims=True); fa[...,:3]=(grey+(fa[...,:3]-grey)*0.9)*0.96   # match the photo
    bn=Image.fromarray(np.clip(fa,0,255).astype('uint8'),'RGBA').filter(ImageFilter.GaussianBlur(0.5))
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sm=Image.new('L',(W,H),0); sm.paste(bn.split()[3],(bx+9,by+7))
    sh.putalpha(sm.filter(ImageFilter.GaussianBlur(8)).point(lambda v:int(v*0.45)))
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); layer.alpha_composite(sh); layer.alpha_composite(bn,(bx,by))
    # occluders in front of the banner: the hedge (solid below its top contour) and the little conifer
    g=a0[...,1]; r=a0[...,0]; b=a0[...,2]
    fol=((g>b+25)&(g>r-8)).astype(np.float32)
    occ=np.zeros((H,W),np.float32)
    for x in range(bx-12,min(W,bx+bw+14)):
        col=fol[880:1080,x]; dens=np.convolve(col,np.ones(15)/15,'same')
        k=np.nonzero(dens>0.6)[0]
        if len(k): occ[880+k[0]+4:1080,x]=1                      # hedge runs down to the ground
    tops=np.array([np.argmax(occ[:,x]>0) if occ[:,x].any() else 1080 for x in range(W)],np.float32)
    sm_=np.convolve(np.pad(tops,(6,6),mode='edge'),np.ones(13)/13,'valid'); occ[:]=0
    for x in range(bx-12,min(W,bx+bw+14)): occ[int(sm_[x]):1080,x]=1
    con=(fol*((np.arange(W)[None,:]<872)&(np.arange(H)[:,None]>835))).astype('uint8')*255   # conifer on the left
    con=Image.fromarray(con).filter(ImageFilter.MedianFilter(11)).filter(ImageFilter.MaxFilter(3))
    occ=np.maximum(occ,np.asarray(con,np.float32)/255)
    occ=np.asarray(Image.fromarray((occ*255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5)),np.float32)/255
    la=np.asarray(layer,np.float32); la[...,3]*=1-occ; layer=Image.fromarray(la.astype('uint8'),'RGBA')
    fr.alpha_composite(layer)
    # --- light front plate with the logo, warped onto the old plate
    dst=[(139.5,1482.5),(284.5,1523),(284.5,1573),(139.5,1527.5)]
    pl=plate(); pw,ph=pl.size
    coeff=solve_persp(dst,[(0,0),(pw,0),(pw,ph),(0,ph)])
    warped=pl.transform((W,H),Image.PERSPECTIVE,coeff,resample=Image.BICUBIC)
    warped=warped.filter(ImageFilter.GaussianBlur(0.5))
    fr.alpha_composite(warped)
    contacts_footer(fr)
    fr.convert('RGB').save(out,quality=95); return out

if __name__=='__main__':
    print(build())
