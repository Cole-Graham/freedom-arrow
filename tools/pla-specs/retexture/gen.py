"""ZSL-92 pilot texture set: woodland digital (Motorized/PLAGF), triplanar in world space, detail kept from the source."""
import numpy as np
from PIL import Image,ImageFilter
R=2048;SRC='src/UserData/FAModels/';OUT='out/';import os;os.makedirs(OUT,exist_ok=True)
d=np.load('raster.npz');pos,nrm,isl,cov=d['pos'],d['nrm'],d['isl'],d['cov']
oldimg=Image.open(SRC+'m_wz551_tex0.png').convert('RGB').resize((R,R),Image.LANCZOS)
old=np.asarray(oldimg).astype(np.float32)/255
rng=np.random.default_rng(92)
# --- painted islands: share of saturated (camo) pixels
mx,mn=old.max(2),old.min(2);sat=(mx-mn)/np.maximum(mx,1e-3)
painted=np.zeros(isl.max()+1,bool)
for i in range(isl.max()+1):
    m=isl==i
    if m.sum()<50:continue
    painted[i]=((sat[m]>0.22)&(mx[m]>0.12)).mean()>0.22
P=cov&painted[np.maximum(isl,0)]&(isl>=0)
print('painted share of used area',round(P.sum()/cov.sum(),3))
# --- digital camo pattern: blocky multi-scale value noise, 4 colours (approx. PLA Type 07 woodland)
def vnoise(n,cells,seed):
    g=np.random.default_rng(seed).random((cells+1,cells+1))
    x=np.linspace(0,cells,n,endpoint=False);i=x.astype(int);f=x-i;f=f*f*(3-2*f)
    a=g[np.ix_(i,i)];b=g[np.ix_(i,i+1)];c=g[np.ix_(i+1,i)];e=g[np.ix_(i+1,i+1)]
    fx=f[None,:];fy=f[:,None];return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+e*fx)*fy
N=1024;TILE=3.0   # 1024 px pattern covers 3 m; digital block = 12 px ~ 3.5 cm
h=0.55*vnoise(N,6,1)+0.3*vnoise(N,16,2)+0.15*vnoise(N,48,3)
h2=0.6*vnoise(N,9,4)+0.4*vnoise(N,30,5)
B=16;h=h.reshape(N//B,B,N//B,B).mean((1,3));h2=h2.reshape(N//B,B,N//B,B).mean((1,3))
h=np.kron(h,np.ones((B,B)));h2=np.kron(h2,np.ones((B,B)))
COL=np.array([[60,72,45],[97,106,66],[140,134,98],[38,38,32]],np.float32)/255
q=np.quantile
cls=np.where(h<q(h,0.40),0,np.where(h<q(h,0.72),1,2));cls=np.where(h2>q(h2,0.86),3,cls)
pat=COL[cls]
def sample(tex,u,v):
    n=tex.shape[0];x=(np.floor(u/TILE*n)%n).astype(int);y=(np.floor(v/TILE*n)%n).astype(int);return tex[y,x]
p=pos[P];nn=np.abs(nrm[P]);w=nn**4;w/=w.sum(1,keepdims=True)
camo=sample(pat,p[:,2],p[:,1])*w[:,0:1]+sample(pat,p[:,0],p[:,2])*w[:,1:2]+sample(pat,p[:,0],p[:,1])*w[:,2:3]
# --- detail from the source: fine high-pass of luminance (panel lines, bolts, hatches); markings kept
L=old.mean(2);Limg=Image.fromarray((L*255).astype(np.uint8))
hp=(L-np.asarray(Limg.filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255)
cav=np.asarray(Limg.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
r,g,b=old[...,0],old[...,1],old[...,2]
mark=((r>0.45)&(r>g*1.6)&(r>b*1.6))|((mx>0.75)&(sat<0.15))   # red star, white numbers
# --- weathering: dust low on the hull, edge wear from normal change, grime noise
ny=nrm[...,1];dust=np.clip((0.9-pos[...,1])/0.9,0,1)**1.5*0.55+np.clip(ny,0,1)*0.12
gn=np.zeros((R,R),np.float32)
for c,s in ((8,7),(32,8),(128,9)):gn+=vnoise(R,c,s)/3
gn=gn.astype(np.float32)
nimg=[Image.fromarray(((nrm[...,k]*0.5+0.5)*255).astype(np.uint8)) for k in range(3)]
edge=sum(np.abs(np.asarray(im.filter(ImageFilter.FIND_EDGES)).astype(np.float32)/255) for im in nimg)
inner=np.ones((R,R),bool)
for dy in(-2,-1,0,1,2):
    for dx in(-2,-1,0,1,2):inner&=(np.roll(np.roll(isl,dy,0),dx,1)==isl)
edge=np.clip(edge*2.5,0,1)*(gn>0.52)*inner
chip=np.clip(edge+(np.abs(hp)>0.08)*0.35*(gn>0.6),0,1)
alb=old.copy()
base=np.zeros_like(old);base[P]=camo
DUST=np.array([0.47,0.42,0.33],np.float32);STEEL=np.array([0.42,0.42,0.40],np.float32)
paint=base*(0.88+0.24*(gn[...,None]-0.5))
paint=paint*(1+1.6*hp[...,None])                         # bake panel detail
paint=paint*(0.82+0.18*np.clip(cav/0.25,0,1))[...,None]    # soft cavity from the old shading
paint=paint*(1-dust[...,None]*0.6)+DUST*dust[...,None]*0.6
paint=paint*(1-chip[...,None])+STEEL*chip[...,None]
alb[P]=paint[P]
alb[mark&P]=old[mark&P]
# unpainted parts (tyres, steel, rubber): sharpened source, slightly lifted from the old dark bake
up=np.asarray(oldimg.filter(ImageFilter.UnsharpMask(2,60,3))).astype(np.float32)/255
U=cov&~P;alb[U]=np.clip(up[U]*1.12+0.015,0,1)
alb=np.clip(alb,0,1)
# --- mask map (R metallic, G occlusion, B detail mask, A smoothness)
met=np.where(P,0.22,0.15)+chip*0.6;smo=np.where(P,0.36,0.25)-dust*0.2+chip*0.2
tyre=U&(mx<0.35)&(sat<0.12);met[tyre]=0;smo[tyre]=0.12
ao=np.clip(0.55+0.45*np.clip(cav/0.25,0,1)+np.clip(hp,-0.2,0)*1.5,0,1)
mask=np.stack([np.clip(met,0,1),ao,np.zeros_like(ao),np.clip(smo,0,1)],-1)
# --- normal map from a height field: source detail + paint chips + fine noise
H=hp*2.0-chip*0.15+(vnoise(R,256,11).astype(np.float32)-0.5)*0.04
gy,gx=np.gradient(H.astype(np.float32));k=6.0
nx,ny2=-gx*k*R/1024,gy*k*R/1024;nz=np.ones_like(nx);l=np.sqrt(nx*nx+ny2*ny2+nz*nz)
nmap=np.stack([nx/l*0.5+0.5,ny2/l*0.5+0.5,nz/l*0.5+0.5,np.ones_like(nx)],-1)
# --- pad islands outward (16 px) so mips do not bleed black
def pad(img,cov,n=16):
    img=img.copy();c=cov.copy()
    for _ in range(n):
        acc=np.zeros_like(img);cnt=np.zeros(c.shape,np.float32)
        for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
            sh=np.roll(np.roll(img,dy,0),dx,1);sc=np.roll(np.roll(c,dy,0),dx,1);acc[sc&~c]+=sh[sc&~c];cnt[sc&~c]+=1
        new=(cnt>0)&~c;img[new]=acc[new]/cnt[new][:,None];c|=new
    return img
alb=pad(alb,cov);mask=pad(mask,cov);nmap=pad(nmap,cov)
save=lambda a,n,mode:Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8),mode).save(OUT+n)
save(np.concatenate([alb,np.ones((R,R,1))],-1),'m_wz551_tex0.png','RGBA');save(mask,'m_wz551_tex0_mask.png','RGBA');save(nmap,'m_wz551_tex0_n.png','RGBA')
for n in('m_wz551_tex0.png','m_wz551_tex0_mask.png','m_wz551_tex0_n.png'):
    Image.open(OUT+n).resize((1024,1024),Image.LANCZOS).save(OUT+n.replace('m_wz551_','m_wz551_lo_'))
Image.fromarray((alb*255).astype(np.uint8)).resize((1024,1024)).save('new_albedo_view.jpg',quality=88)
print('done')
