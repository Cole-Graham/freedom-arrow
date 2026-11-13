"""ZTQ-15 digital camo (Osama 13 Nov 11:44): PLAGF Recon = woodland digital, Motorized = desert digital.
Only the green paint of the hull/turret atlas (tex1) changes. Camo is triplanar in world space (blocks run continuously across
UV seams), modulated by the source luminance so dirt, panel lines, shading and markings stay. Normal and mask maps unchanged."""
import numpy as np,sys
from PIL import Image,ImageFilter
SCHEME,SRC,RASTER,OUT=sys.argv[1:5]
COL={'woodland':[[60,72,45],[97,106,66],[140,134,98],[38,38,32]],      # PLA Type 07 woodland digital (as ZSL-92 pilot)
     'desert':[[120,96,66],[163,138,100],[201,181,142],[78,62,45]]}[SCHEME]  # PLA Type 07 desert digital: brown, khaki, sand, dark brown
COL=np.array(COL,np.float32)/255
im=Image.open(SRC);alpha=np.asarray(im.convert('RGBA'))[...,3:];a=np.asarray(im.convert('RGB')).astype(np.float32)/255;R=a.shape[0]
d=np.load(RASTER);pos,nrm,cov=d['pos'],d['nrm'],d['cov']
r,g,b=a[...,0],a[...,1],a[...,2];mx=a.max(2);mn=a.min(2);dd=mx-mn+1e-6
h=np.where(mx==r,((g-b)/dd)%6,np.where(mx==g,(b-r)/dd+2,(r-g)/dd+4))*60;s=dd/np.maximum(mx,1e-6)
paint=(h>=28)&(h<110)&(s>0.06)&(mx>0.08)
Pimg=Image.fromarray((paint*255).astype(np.uint8)).filter(ImageFilter.MedianFilter(7))
paint=np.asarray(Pimg)>127
L=0.3*r+0.59*g+0.11*b
def vnoise(n,cells,seed):
    gg=np.random.default_rng(seed).random((cells+1,cells+1))
    x=np.linspace(0,cells,n,endpoint=False);i=x.astype(int);f=x-i;f=f*f*(3-2*f)
    A=gg[np.ix_(i,i)];B=gg[np.ix_(i,i+1)];C=gg[np.ix_(i+1,i)];E=gg[np.ix_(i+1,i+1)]
    fx=f[None,:];fy=f[:,None];return (A*(1-fx)+B*fx)*(1-fy)+(C*(1-fx)+E*fx)*fy
N=1024;TILE=3.0;BL=16
hh=0.55*vnoise(N,6,1)+0.3*vnoise(N,16,2)+0.15*vnoise(N,48,3);h2=0.6*vnoise(N,9,4)+0.4*vnoise(N,30,5)
hh=np.kron(hh.reshape(N//BL,BL,N//BL,BL).mean((1,3)),np.ones((BL,BL)));h2=np.kron(h2.reshape(N//BL,BL,N//BL,BL).mean((1,3)),np.ones((BL,BL)))
q=np.quantile;cls=np.where(hh<q(hh,0.40),0,np.where(hh<q(hh,0.72),1,2));cls=np.where(h2>q(h2,0.86),3,cls);pat=COL[cls]
def sample(u,v):x=(np.floor(u/TILE*N)%N).astype(int);y=(np.floor(v/TILE*N)%N).astype(int);return pat[y,x]
P=paint&cov;p=pos[P];w=np.abs(nrm[P])**4;w/=w.sum(1,keepdims=True)
camo=sample(p[:,2],p[:,1])*w[:,0:1]+sample(p[:,0],p[:,2])*w[:,1:2]+sample(p[:,0],p[:,1])*w[:,2:3]
ref=np.median(L[P]);detail=np.clip(L[P]/ref,0.35,1.5)[:,None]
# dirt: how far the pixel's colour has drifted from clean paint towards brown; keep that share of the source colour
clean=np.median(a[P],0);drift=np.clip(np.linalg.norm(a[P]-clean*(L[P]/ref)[:,None],axis=1)*3.0,0,0.6)[:,None]
out=a.copy();out[P]=np.clip(camo*detail*(1-drift)+a[P]*drift,0,1)
mark=((r>0.45)&(r>g*1.6)&(r>b*1.6))|((mx>0.55)&(s<0.15))   # red stars, white numbers: keep the source pixels
out[mark&cov]=a[mark&cov]
# feather: blend 1 px at the paint edge
O=Image.fromarray(np.concatenate([(out*255).astype(np.uint8),alpha],-1),'RGBA');O.save(OUT)
print(SCHEME,'paint share',round(float(P.mean()),3),'of covered',round(float(P.sum()/cov.sum()),3))
