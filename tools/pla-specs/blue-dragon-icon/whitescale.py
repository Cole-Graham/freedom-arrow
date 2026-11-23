from PIL import Image as I, ImageFilter as F, ImageDraw as D, ImageOps as O
import numpy as np
from collections import deque
def flood(Ma,seed):
    h,w=Ma.shape;seen=np.zeros_like(Ma);q=deque([seed]);seen[seed]=True
    while q:
        y,x=q.popleft()
        for yy,xx in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
            if 0<=yy<h and 0<=xx<w and Ma[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
    return seen
def contrast_alpha(lum,body,lo,hi,gamma,floor):
    # local contrast boost (unsharp on luminance), then a hard curve
    L=I.fromarray(np.clip(lum,0,255).astype('uint8')).filter(F.UnsharpMask(radius=3,percent=160,threshold=2))
    l=np.asarray(L).astype(float)
    t=np.clip((l-lo)/(hi-lo),0,1)**gamma
    al=t*(1-floor)+floor
    return (al*body*255).astype('uint8')
def finish(alpha,name):
    A=I.fromarray(alpha);bb=A.point(lambda v:255 if v>25 else 0).getbbox();A=A.crop(bb)
    side=int(max(A.size)*1.04);sq=I.new('L',(side,side),0);sq.paste(A,((side-A.size[0])//2,(side-A.size[1])//2))
    out={}
    for sz in (512,128):
        sm=sq.resize((sz,sz),I.LANCZOS)
        if sz==128: sm=sm.filter(F.UnsharpMask(radius=1,percent=120,threshold=1))
        rg=I.new('RGBA',(sz,sz),(255,255,255,0));rg.putalpha(sm);rg.save(f'{name}{sz}.png');out[sz]=rg
    return out
# --- twin dragons
im=I.open('ref2.png').convert('RGB');a=np.asarray(im).astype(float);r,g,b=a[...,0],a[...,1],a[...,2]
lum=0.3*r+0.59*g+0.11*b;sat=a.max(-1)-a.min(-1)
m=~((lum>205)&(sat<30));M=np.asarray(I.fromarray((m*255).astype('uint8')).filter(F.MedianFilter(5)))>0
body=flood(M,(im.size[1]//2,im.size[0]//2)).astype(float)
body=np.asarray(I.fromarray((body*255).astype('uint8')).filter(F.GaussianBlur(0.8))).astype(float)/255
WB=finish(contrast_alpha(lum,body,40,150,1.0,0.12),'CB')
# --- single head: upscale first, mask the head only (no symmetrize), drop badge white/red
im=I.open('ref.png').convert('RGB');im=im.resize((im.size[0]*3,im.size[1]*3),I.LANCZOS).filter(F.UnsharpMask(radius=4,percent=120,threshold=2))
a=np.asarray(im).astype(float);r,g,b=a[...,0],a[...,1],a[...,2];lum=0.3*r+0.59*g+0.11*b
red=(r>100)&(r>g*1.45)&(r>b*1.45)
keep=I.new('L',im.size,0);d=D.Draw(keep);s=3
d.ellipse((45*s,125*s,375*s,445*s),fill=255)
d.polygon([(x*s,y*s) for x,y in [(80,40),(150,40),(176,150),(132,178)]],fill=255)
d.polygon([(x*s,y*s) for x,y in [(340,40),(270,40),(244,150),(288,178)]],fill=255)
d.rectangle((140*s,0,280*s,152*s),fill=0);d.rectangle((0,410*s,420*s,458*s),fill=0)
K=np.asarray(keep.filter(F.GaussianBlur(6)))/255.0
H,W=lum.shape;yy,xx=np.mgrid[0:H,0:W]
frame=(lum>215)&(np.abs(r-b)<35)&((np.abs(xx-210*s)>150*s)|(yy<75*s))
body=K*(~red&~frame)
body=np.asarray(I.fromarray((body*255).astype('uint8')).filter(F.MedianFilter(7)).filter(F.GaussianBlur(1.5))).astype(float)/255
WA=finish(contrast_alpha(lum,body,32,150,1.1,0.0),'CA')
big=I.new('RGBA',(1100,720),(40,46,52,255))
for i,f in enumerate((WA,WB)):
    big.alpha_composite(f[512],(i*550,4));big.alpha_composite(f[128],(i*550+60,570));big.alpha_composite(f[128].resize((64,64),I.LANCZOS),(i*550+220,600))
mo=I.open('../../091-wt/mod/source/runtime-qa/icons/FA_CHINA_MOTORIZED.png').convert('RGBA');big.alpha_composite(mo,(400,570));big.save('prev_contrast.png')
