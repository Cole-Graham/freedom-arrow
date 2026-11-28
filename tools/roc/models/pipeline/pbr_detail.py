"""Truck surface detail pass (Shawn 28 Nov 12:2x: "Enhance the basecolor texture and PBR of Land Sword II, Tien Kung III, Thunderbolt-2000
based on the vanilla NASAMS, make them more realistic!"). Measured 28 Nov: their masks are almost flat (smoothness std 3-6 of 255, AO 255
everywhere) and the Land Sword II has no normal maps, so paint, metal and grime all shine alike. The vanilla NASAMS reads as dark olive paint
with grime in the recesses, rougher dirty areas and fine surface relief. Per colour sheet (Arsenal and battle, sheets >= 512 px):
- relief: a height field from the colour's fine detail (luminance minus its 6 px blur at 2048) -> normal x/y (strength 3.0), added to the
  sheet's own normal map where it has one;
- ambient occlusion: concavity of that relief at 3 scales -> mask G and 60 % into the colour;
- colour: a large-scale +-9 % mottle (paint fade) and light dust (118, 108, 88) patches, grime darkening in the occluded areas;
- smoothness: mask A x (0.55 + 0.45 x cleanliness), cleanliness = AO x (1 - dust), so recesses and dusty parts are matt; metal unchanged.
Originals go to x/<slug>/pre-detail/ once and every run starts from them. usage: python pbr_detail.py SLUG [SLUG ...]  -> list for conv.py"""
import sys,os,glob,shutil
import numpy as np
from PIL import Image
T=os.path.dirname(os.path.abspath(__file__));M=T+'/../veh/models'
def blur(a,s):
    r=int(3*s)+1;k=np.exp(-0.5*(np.arange(-r,r+1)/s)**2);k/=k.sum();a=a.astype(np.float32)
    for ax in (0,1):
        p=np.pad(a,[(r,r) if i==ax else (0,0) for i in (0,1)],mode='edge');a=sum(k[i]*np.take(p,range(i,i+a.shape[ax]),axis=ax) for i in range(2*r+1))
    return a
def noise(H,cells,seed):
    g=np.random.default_rng(seed).random((cells,cells)).astype(np.float32);return np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize((H,H),Image.BICUBIC)).astype(np.float32)/255
out=[]
for slug in sys.argv[1:]:
    BK=f'{T}/../veh/x/{slug}/pre-detail';os.makedirs(BK,exist_ok=True)
    for f in sorted(glob.glob(f'{M}/m_roc_{slug}_*static_tex*.png')):
        b=os.path.basename(f)
        if any(b.endswith(x) for x in ('_n.png','_mask.png')) or '@' in b:continue
        stem=b[:-4];src={}
        for sfx in ('','_n','_mask'):
            p=f'{M}/{stem}{sfx}.png'
            if os.path.exists(p):
                if not os.path.exists(f'{BK}/{stem}{sfx}.png'):shutil.copy(p,f'{BK}/{stem}{sfx}.png')
                src[sfx]=f'{BK}/{stem}{sfx}.png'
        im=Image.open(src['']);H=im.size[0]
        if H<512 or im.size[0]!=im.size[1]:continue
        C=np.asarray(im.convert('RGBA')).astype(np.float32);sc=H/2048
        L=C[...,:3].mean(2)/255
        h=L-blur(L,max(0.8,6*sc))
        gy,gx=np.gradient(h);S=3.0*H/2048*8
        nx,ny=-gx*S,gy*S                                    # OpenGL (+y up = -row)
        if '_n' in src:
            N=np.asarray(Image.open(src['_n']).convert('RGB').resize((H,H))).astype(np.float32)/127.5-1;nx=nx+N[...,0];ny=ny+N[...,1]
        nz=np.ones_like(nx);n=np.stack([nx,ny,nz],2);n/=np.linalg.norm(n,axis=2,keepdims=True)
        div=np.gradient(n[...,0],axis=1)-np.gradient(n[...,1],axis=0)
        cav=sum(w*np.clip(-blur(div,max(0.6,s*sc))*s*sc,0,None) for s,w in ((2,0.5),(6,0.3),(16,0.2)))
        ao=blur(np.clip(1-3.5*cav,0.35,1.0),max(0.6,sc))
        mott=0.91+0.18*(0.6*noise(H,6,1)+0.4*noise(H,24,2))
        dust=np.clip((noise(H,10,3)-0.5)*2.5,0,1)*0.8
        C[...,:3]*=(mott*(1-0.6*(1-ao)))[...,None];C[...,:3]=C[...,:3]*(1-0.25*dust[...,None])+np.array([118,108,88],np.float32)*0.25*dust[...,None]
        K=np.asarray(Image.open(src['_mask']).convert('RGBA')).astype(np.float32) if '_mask' in src else np.dstack([np.zeros((H,H)),np.full((H,H),255.),np.zeros((H,H)),np.full((H,H),90.)]).astype(np.float32)
        if K.shape[0]!=H:K=np.asarray(Image.fromarray(K.astype(np.uint8),'RGBA').resize((H,H))).astype(np.float32)
        clean=ao*(1-dust)
        K[...,1]=np.minimum(K[...,1],ao*255);K[...,3]*=0.55+0.45*clean
        Image.fromarray(C.clip(0,255).round().astype(np.uint8),'RGBA').convert(im.mode).save(f'{M}/{stem}.png')
        Image.fromarray(((n+1)*127.5).clip(0,255).round().astype(np.uint8),'RGB').save(f'{M}/{stem}_n.png')
        Image.fromarray(K.clip(0,255).round().astype(np.uint8),'RGBA').save(f'{M}/{stem}_mask.png')
        out+= [f'{stem}.png',f'{stem}_n.png',f'{stem}_mask.png']
        print(f'{stem} {H}px AO mean {ao.mean():.3f}, smoothness std {K[...,3].std():.1f}',file=sys.stderr)
print('\n'.join(out))
