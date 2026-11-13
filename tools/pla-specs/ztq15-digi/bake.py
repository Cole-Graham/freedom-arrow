"""Rasterise world position and normal per texel of m_ztq15_green_tex1 (hull/turret atlas) for triplanar digital camo."""
import numpy as np,sys
from PIL import Image
from famread import read_fam
FAM,TEX,OUT=sys.argv[1],sys.argv[2],sys.argv[4];WH=sys.argv[3].split('x');RW,RH=int(WH[0]),int(WH[-1]);FLIP=sys.argv[5]=="flip"
pos=np.zeros((RH,RW,3),np.float32);nrm=np.zeros((RH,RW,3),np.float32);cov=np.zeros((RH,RW),bool);uvs=[]
for bone,subs in read_fam(FAM):
    for s in subs:
        if s['tex']!=TEX:continue
        P=np.array(s['pos'],np.float32).reshape(-1,3);N=np.array(s['nrm'],np.float32).reshape(-1,3);UV=np.array(s['uv'],np.float32).reshape(-1,2);I=np.array(s['idx']).reshape(-1,3);uvs.append(UV)
        for t in I:
            p,n,uv=P[t],N[t],UV[t];x=uv[:,0]*RW-0.5;y=((1-uv[:,1]) if FLIP else uv[:,1])*RH-0.5
            x0,x1=max(int(np.floor(x.min())),0),min(int(np.ceil(x.max())),RW-1);y0,y1=max(int(np.floor(y.min())),0),min(int(np.ceil(y.max())),RH-1)
            if x1<x0 or y1<y0:continue
            gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
            d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
            if abs(d)<1e-12:continue
            w0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d;w1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d;w2=1-w0-w1
            m=(w0>=-0.02)&(w1>=-0.02)&(w2>=-0.02)
            if not m.any():continue
            yy,xx=gy[m],gx[m];W=np.stack([w0[m],w1[m],w2[m]],1)
            pos[yy,xx]=W@p;nn=W@n;nrm[yy,xx]=nn/np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-6);cov[yy,xx]=True
uv=np.concatenate(uvs);print('uv range',uv.min(0).round(3),uv.max(0).round(3),'coverage',cov.mean().round(3))
np.savez_compressed(OUT,pos=pos,nrm=nrm,cov=cov)
