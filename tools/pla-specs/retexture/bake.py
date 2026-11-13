"""ZSL-92 pilot: new 2048 px woodland-digital texture set baked from the model's own geometry (Osama 12 Nov 16:40)."""
import numpy as np,sys
from PIL import Image,ImageFilter
from famread import read_fam
R=2048;SRC='src/UserData/FAModels/'
parts=read_fam(SRC+'m_wz551_static.fam')
old=np.asarray(Image.open(SRC+'m_wz551_tex0.png').convert('RGB').resize((R,R),Image.LANCZOS)).astype(np.float32)/255
pos=np.zeros((R,R,3),np.float32);nrm=np.zeros((R,R,3),np.float32);isl=np.full((R,R),-1,np.int32);cov=np.zeros((R,R),bool)
# triangle islands by shared vertex index within each submesh
tri_all=[];base_island=0
for bone,subs in parts:
    for s in subs:
        if s['tex']!='m_wz551_tex0.png':continue
        P=np.array(s['pos'],np.float32).reshape(-1,3);N=np.array(s['nrm'],np.float32).reshape(-1,3);UV=np.array(s['uv'],np.float32).reshape(-1,2);I=np.array(s['idx']).reshape(-1,3)
        key={};wid=np.array([key.setdefault((round(float(u),5),round(float(v),5)),len(key)) for u,v in UV]);par=np.arange(len(key))
        def f(x):
            while par[x]!=x:par[x]=par[par[x]];x=par[x]
            return x
        for a,b,c in wid[I]:
            ra=f(a);par[f(b)]=ra;par[f(c)]=f(a)
        roots={};lab=np.array([roots.setdefault(f(w),len(roots)) for w in wid])+base_island;base_island=lab.max()+1
        for t in I:tri_all.append((P[t],N[t],UV[t],lab[t[0]]))
print('triangles',len(tri_all),'islands',base_island)
for P,N,UV,lab in tri_all:
    x=UV[:,0]*R-0.5;y=(-UV[:,1])*R-0.5
    x0,x1=int(np.floor(x.min())),int(np.ceil(x.max()));y0,y1=int(np.floor(y.min())),int(np.ceil(y.max()))
    x0,y0=max(x0,0),max(y0,0);x1,y1=min(x1,R-1),min(y1,R-1)
    if x1<x0 or y1<y0:continue
    gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
    d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
    if abs(d)<1e-12:continue
    w0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d;w1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d;w2=1-w0-w1
    m=(w0>=-0.02)&(w1>=-0.02)&(w2>=-0.02)
    if not m.any():continue
    yy,xx=gy[m],gx[m];W=np.stack([w0[m],w1[m],w2[m]],1)
    pos[yy,xx]=W@P;n=W@N;nrm[yy,xx]=n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-6);isl[yy,xx]=lab;cov[yy,xx]=True
print('coverage',cov.mean().round(3))
np.savez_compressed('raster.npz',pos=pos,nrm=nrm,isl=isl,cov=cov)
