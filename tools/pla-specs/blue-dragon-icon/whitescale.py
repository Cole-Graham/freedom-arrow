from PIL import Image as I, ImageFilter as F
import numpy as np, sys
from collections import deque
def flood(Ma,seed):
    h,w=Ma.shape;seen=np.zeros_like(Ma);q=deque([seed]);seen[seed]=True
    while q:
        y,x=q.popleft()
        for yy,xx in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
            if 0<=yy<h and 0<=xx<w and Ma[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
    return seen
def run(src,out,maskfn,seed_frac,lo,hi,floor):
    im=I.open(src).convert('RGB');a=np.asarray(im).astype(float);r,g,b=a[...,0],a[...,1],a[...,2]
    lum=0.3*r+0.59*g+0.11*b
    m=maskfn(r,g,b,lum)
    M=np.asarray(I.fromarray((m*255).astype('uint8')).filter(F.MedianFilter(5)))>0
    h,w=M.shape;body=flood(M,(int(h*seed_frac[0]),int(w*seed_frac[1])))
    B=I.fromarray((body*255).astype('uint8')).filter(F.GaussianBlur(1))
    al=np.clip((lum-lo)/(hi-lo),0,1)*(1-floor)+floor
    alpha=(al*np.asarray(B)/255.0*255).astype('uint8')
    A=I.fromarray(alpha);bb=A.point(lambda v:255 if v>20 else 0).getbbox();A=A.crop(bb)
    side=int(max(A.size)*1.04);sq=I.new('L',(side,side),0);sq.paste(A,((side-A.size[0])//2,(side-A.size[1])//2))
    res={}
    for sz in (512,128):
        rg=I.new('RGBA',(sz,sz),(255,255,255,0));rg.putalpha(sq.resize((sz,sz),I.LANCZOS));rg.save(f'{out}{sz}.png');res[sz]=rg
    return res
# front dragon head: drop the red badge (red) and keep the head from the centre
fa=run('ref.png','WA',lambda r,g,b,l:~((r>110)&(r>g*1.5)&(r>b*1.5)),(0.62,0.5),25,215,0.18)
# twin dragons sticker: drop the light grey page and the white sticker border
fb=run('ref2.png','WB',lambda r,g,b,l:~((l>205)&((np.max([r,g,b],0)-np.min([r,g,b],0))<30)),(0.5,0.5),20,200,0.22)
big=I.new('RGBA',(1100,700),(40,46,52,255))
for i,(f,n) in enumerate(((fa,'A'),(fb,'B'))):
    big.alpha_composite(f[512],(i*550,4));big.alpha_composite(f[128],(i*550+60,560));big.alpha_composite(f[128].resize((64,64),I.LANCZOS),(i*550+220,590))
mo=I.open('../../091-wt/releases/0.6/source/runtime-qa/icons/FA_CHINA_MOTORIZED.png').convert('RGBA');big.alpha_composite(mo,(400,560));big.save('prev_white.png')
