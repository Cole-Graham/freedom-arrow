"""Aged / muddy / worn look on an already converted ROC model (Shawn 27 Nov 02:2x: "for tk3, LT2000, and lsw2, make the textures look aged,
muddy, and more realistic, with materials, etc. - you can use the M60A3 or M110A2 as a reference"). Works on famconv's output textures, so the
geometry, LODs and glass are untouched. Per textured material: world position + face normal of every texel (uvpos.py on the same GLB), then
  - mud: low on the vehicle (full below ~0.3 m, gone by ~1.0 m), patchy; matte, not metallic
  - grime: darker crevices (the model's AO), dirt streaks running down vertical faces, light dust on up-facing faces
  - wear: bare metal on hard edges (face normals turning > ~35 deg), small paint chips on the upper body
Changes colour (+ the _mask metal / smoothness where the model has one), Arsenal and battle. Originals go to x/<slug>/pre-weather/ once.
usage: python weather_fam.py SLUG GLB LENGTH_M [STRENGTH=1.0]   -> prints the changed PNGs (for fat-all/conv.py)"""
import sys,os,json,shutil,numpy as np
from PIL import Image
from pygltflib import GLTF2
s,glb,L=sys.argv[1],sys.argv[2],float(sys.argv[3]);K=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';M=V+'/models';X=f'{V}/x/{s}';BK=X+'/pre-weather';os.makedirs(BK,exist_ok=True)
mats=[m.name for m in GLTF2().load(glb).materials]
rng=np.random.default_rng(23);LAT=[rng.random((48,48,48)) for _ in range(9)]
def vnoise(p,lat):
    n=lat.shape[0]-1;q=np.mod(p,n);i=np.floor(q).astype(int);f=q-i;f=f*f*(3-2*f);j=np.minimum(i+1,n);out=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2])
                out=out+w*lat[(j if dx else i)[:,0],(j if dy else i)[:,1],(j if dz else i)[:,2]]
    return out
def fbm(p,k):return vnoise(p,LAT[k])*0.55+vnoise(p*2.1+5.3,LAT[k+1])*0.3+vnoise(p*4.3+1.7,LAT[k+2])*0.15
ss=lambda e0,e1,x:np.clip((x-e0)/(e1-e0),0,1)**2*(3-2*np.clip((x-e0)/(e1-e0),0,1))
def blur(x,r):
    for ax in (0,1):
        c=np.cumsum(np.pad(x,[(r+1,r) if i==ax else (0,0) for i in range(2)],mode='edge'),axis=ax);x=(np.take(c,range(2*r+1,c.shape[ax]),axis=ax)-np.take(c,range(0,c.shape[ax]-2*r-1),axis=ax))/(2*r+1)
    return x
pos={};allp=[]
for i,m in enumerate(mats):
    f=f'{X}/pos/pos_{m.split(".")[0]}.npy'
    if os.path.exists(f):pos[i]=np.load(f).astype(np.float32)[::-1];allp.append(pos[i][~np.isnan(pos[i][...,0])][:,:3])
A=np.concatenate(allp);mn,mx=A.min(0),A.max(0);ext=mx-mn;sc=L/max(ext[0],ext[1]);z0=mn[2]
changed=[]
def load(p):return Image.open(p)
def put(name,im):   # back up once, then write
    p=f'{M}/{name}'
    if os.path.exists(p) and not os.path.exists(f'{BK}/{name}'):shutil.copy(p,f'{BK}/{name}')
    im.save(p);changed.append(name)
for i,P in pos.items():
    st=f'm_roc_{s}_static_tex{i}';lo=f'm_roc_{s}_lo_static_tex{i}'
    if not os.path.exists(f'{M}/{st}.png'):continue
    full=f'{M}/tex_full/{st}.png';src=full if os.path.exists(full) else f'{M}/{st}.png'
    if os.path.exists(f'{BK}/tex_full_{st}.png'):src=f'{BK}/tex_full_{st}.png'      # rerun: start from the original
    elif os.path.exists(f'{BK}/{st}.png') and not os.path.exists(full):src=f'{BK}/{st}.png'
    if os.path.exists(full) and not os.path.exists(f'{BK}/tex_full_{st}.png'):shutil.copy(full,f'{BK}/tex_full_{st}.png')
    img=load(src).convert('RGBA');Wd,Hd=img.size;S=Wd;alpha=np.asarray(img)[...,3];c=np.asarray(img.convert('RGB'),np.float32)/255
    Q=P[np.arange(Hd)*P.shape[0]//Hd][:,np.arange(Wd)*P.shape[1]//Wd];ok=~np.isnan(Q[...,0]);Qn=np.nan_to_num(Q)
    H=(Qn[...,2]-z0)*sc;nz=Qn[...,5];N=Qn[...,3:6]
    Wp=(Qn[...,:3]-mn)*sc   # metres
    flat=Wp.reshape(-1,3)
    n1=fbm(flat*1.3,0).reshape(Hd,Wd);n2=fbm(flat*6.0,3).reshape(Hd,Wd);streak=fbm(flat*np.array([7,7,0.8]),6).reshape(Hd,Wd)
    nmask=f'{M}/{st}_mask.png';msk=np.asarray(load(f'{BK}/{st}_mask.png' if os.path.exists(f'{BK}/{st}_mask.png') else nmask).convert('RGBA'),np.float32)/255 if os.path.exists(nmask) else None
    if msk is not None and msk.shape[:2]!=(Hd,Wd):msk=np.asarray(Image.fromarray((msk*255).astype(np.uint8)).resize((Wd,Hd),Image.LANCZOS),np.float32)/255
    ao=msk[...,1] if msk is not None else np.ones((Hd,Wd),np.float32)
    # hard edges: neighbouring texels whose face normals differ by > ~35 deg
    e=np.zeros((Hd,Wd),np.float32)
    for dy,dx in ((0,1),(1,0)):
        n2_=np.roll(N,(dy,dx),axis=(0,1));o2=np.roll(ok,(dy,dx),axis=(0,1));d=1-(N*n2_).sum(-1);e=np.maximum(e,np.where(ok&o2,d,0))
    edge=np.clip(blur(ss(0.10,0.26,e),2)*2.5,0,1)
    lum=c.mean(-1,keepdims=True)
    MT=float(os.environ.get('MUD_TOP','1.5'))   # mud fades out at this height (m); helicopters 0.5 (wheels only)
    mud=np.clip((MT-H)/(MT*0.8),0,1)**1.3*(0.6+0.8*(n1-0.5))+(1-ao)*0.4*np.clip((MT+0.5-H)/1.0,0,1)
    mudA=ss(0.26,0.58,mud+(n2-0.5)*0.4)*0.72*K*ok
    mudc=np.stack([np.interp(n1,[0,1],[0.47,0.30]),np.interp(n1,[0,1],[0.40,0.24]),np.interp(n1,[0,1],[0.31,0.18])],-1)
    grime=(np.clip(1-ao,0,1)*0.6+np.where(np.abs(nz)<0.4,ss(0.48,0.66,streak),0)*0.38+0.10*ss(0.3,0.8,n1))*K*ok      # crevices + streaks down vertical faces + overall dirt
    dustA=np.clip((nz-0.5)/0.5,0,1)*0.22*(0.5+n1)*K*ok
    upper=ss(0.6,1.0,H)*ok
    wear=np.clip(edge*ss(0.45,0.7,n2),0,1)*upper*0.75*K
    cs=n2*0.6+fbm(flat*14,1).reshape(Hd,Wd)*0.4;q=np.quantile(cs[ok],[0.955,0.975]) if ok.any() else [1,1]
    chip=ss(q[0],q[1],cs)*upper*0.6*K
    out=c*(1-0.16*K)+lum*0.16*K   # aged: faded paint
    out=out*(1-grime[...,None]*0.6)
    out=out*(1-dustA[...,None])+np.array([0.58,0.54,0.46])*dustA[...,None]
    out=out*(1-chip[...,None])+np.array([0.24,0.24,0.22])*chip[...,None]
    out=out*(1-wear[...,None])+np.clip(lum*0.6+0.38,0,1)*np.array([0.98,0.98,0.96])*wear[...,None]
    mshade=np.clip(lum[...,0]/np.maximum(blur(lum[...,0],8),0.02),0.65,1.35)[...,None]   # the surface's own detail (tread, bolts) shows through the mud
    out=out*(1-mudA[...,None])+mudc*mshade*mudA[...,None]
    res=Image.fromarray(np.dstack([np.clip(out*255,0,255).round().astype(np.uint8),alpha]),'RGBA')
    if os.path.exists(full):res.save(full);put(f'{st}.png',res.resize(load(f'{BK}/{st}.png' if os.path.exists(f'{BK}/{st}.png') else f'{M}/{st}.png').size,Image.LANCZOS))
    else:put(f'{st}.png',res)
    if os.path.exists(f'{M}/{lo}.png'):put(f'{lo}.png',res.resize(load(f'{M}/{lo}.png').size,Image.LANCZOS))
    if msk is not None:
        m2=msk.copy();m2[...,0]=m2[...,0]*(1-mudA)*(1-chip)+0.75*wear*(1-mudA);m2[...,3]=m2[...,3]*(1-mudA)+0.08*mudA;m2[...,3]=m2[...,3]*(1-wear)+0.55*wear;m2[...,3]*=1-dustA*0.5
        mi=Image.fromarray(np.clip(m2*255,0,255).round().astype(np.uint8),'RGBA');put(f'{st}_mask.png',mi.resize(load(nmask).size,Image.LANCZOS))
        if os.path.exists(f'{M}/{lo}_mask.png'):put(f'{lo}_mask.png',mi.resize(load(f'{M}/{lo}_mask.png').size,Image.LANCZOS))
    v=ok.sum()+1e-6
    print('WEATHER',s,'tex%d'%i,mats[i][:28],'mud %.0f%% wear %.1f%% chips %.1f%% grime %.0f%% (%dpx)'%(100*(mudA>0.3).sum()/v,100*(wear>0.3).sum()/v,100*(chip>0.3).sum()/v,100*(grime>0.15).sum()/v,S),file=sys.stderr)
print('\n'.join(sorted(set(changed))))
