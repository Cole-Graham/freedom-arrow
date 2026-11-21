from PIL import Image as I, ImageFilter as F, ImageDraw as D
import numpy as np, sys
from collections import deque
S=3
im=I.open('ref.png').convert('RGB');W0,H0=im.size;im=im.resize((W0*S,H0*S),I.LANCZOS)
a=np.asarray(im).astype(float);r,g,b=a[...,0],a[...,1],a[...,2];lum=0.3*r+0.59*g+0.11*b;sat=a.max(-1)-a.min(-1)
H,W=lum.shape
poly=[(108,72),(140,90),(175,125),(200,150),(230,160),(255,148),(280,160),(312,150),(338,125),(372,92),(418,78),(402,118),(384,158),(420,180),(468,228),(442,250),(482,300),(452,322),(472,380),(442,402),(432,458),(382,472),(334,500),(302,526),(255,538),(208,526),(176,500),(128,472),(78,458),(68,402),(38,380),(58,322),(28,300),(68,250),(42,228),(90,180),(126,160),(110,120)]
P=I.new('L',(W,H),0);D.Draw(P).polygon([(x*S,y*S) for x,y in poly],fill=255)
Pa=np.asarray(P.filter(F.MaxFilter(15)))>0
red=(r>100)&(r>g*1.4)&(r>b*1.4)
ribbon=(lum>190)&(sat<45)&(np.mgrid[0:H,0:W][0]>470*S)
M=Pa&~red&~ribbon
# fill holes (eyes, mouth) = everything not reachable from the border through ~M
Mi=I.fromarray((M*255).astype('uint8')).filter(F.MedianFilter(7));Ma=np.asarray(Mi)>0
out=np.zeros_like(Ma);q=deque();
for x in range(W):
    for y in (0,H-1):
        if not Ma[y,x] and not out[y,x]:out[y,x]=True;q.append((y,x))
for y in range(H):
    for x in (0,W-1):
        if not Ma[y,x] and not out[y,x]:out[y,x]=True;q.append((y,x))
while q:
    y,x=q.popleft()
    for y2,x2 in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
        if 0<=y2<H and 0<=x2<W and not Ma[y2,x2] and not out[y2,x2]:out[y2,x2]=True;q.append((y2,x2))
body=~out
B=I.fromarray((body*255).astype('uint8')).filter(F.MaxFilter(5)).filter(F.MinFilter(9)).filter(F.GaussianBlur(2.5)).point(lambda v:255 if v>128 else 0).filter(F.GaussianBlur(1.2))
Bf=np.asarray(B).astype(float)/255
L=I.fromarray(np.clip(lum,0,255).astype('uint8')).filter(F.UnsharpMask(radius=5,percent=200,threshold=2));l=np.asarray(L).astype(float)
inside=l[Bf>0.9];lo=np.percentile(inside,float(sys.argv[1]));hi=np.percentile(inside,float(sys.argv[2]))
t=np.clip((l-lo)/(hi-lo),0,1)**float(sys.argv[3]);floor=float(sys.argv[4])
# bright-red/orange eyes count as glowing white
eyes=(r>200)&(g>60)&(b<90)&(np.mgrid[0:H,0:W][0]>330*S)&(np.mgrid[0:H,0:W][0]<420*S)
eyes=np.asarray(I.fromarray((eyes*255).astype("uint8")).filter(F.MaxFilter(7)))>0;t=np.maximum(t,eyes.astype(float))
alpha=(np.clip((t*(1-floor)+floor)*Bf,0,1)*255).astype('uint8')
A=I.fromarray(alpha);bb=A.point(lambda v:255 if v>20 else 0).getbbox();A=A.crop(bb)
side=int(max(A.size)*1.03);sq=I.new('L',(side,side),0);sq.paste(A,((side-A.size[0])//2,(side-A.size[1])//2))
for sz in (512,128):
    sm=sq.resize((sz,sz),I.LANCZOS)
    if sz==128: sm=sm.filter(F.UnsharpMask(radius=1,percent=120,threshold=1))
    rg=I.new('RGBA',(sz,sz),(255,255,255,0));rg.putalpha(sm);rg.save(f'H{sz}.png')
big=I.new('RGBA',(560+330,540),(40,46,52,255));big.alpha_composite(I.open('H512.png'),(10,10))
s=I.open('H128.png');big.alpha_composite(s,(590,40));big.alpha_composite(s.resize((64,64),I.LANCZOS),(622,190))
for i,n in enumerate(['FA_CHINA_MOTORIZED','FA_CHINA_ARMORED']):
    big.alpha_composite(I.open('../../091-wt/releases/0.6/source/runtime-qa/icons/'+n+'.png').convert('RGBA'),(740,40+i*140))
big.save('prevH2.png');print('lo/hi',lo,hi,'bbox',bb)
