"""Woodland camouflage scheme for the ROC Hsiung Feng IIE (Shawn 26 Nov 21:5x: "add an optional camouflage similar to the other picture ... transplant
the camouflage pattern from the recent uploaded M60A3 model"). Colours = the M60A3 body texture's own camo colours (median of its green, brown and
dark-grey areas: 57,66,50 / 87,71,62 / 47,50,57). The pattern is laid out in 3D (world position of each texel from uvpos.py), so patches run across
UV seams and panel edges. Only painted texels change (near each material's main paint colour: blue-grey body, white cab); the original shading is kept
by scaling with the texel's brightness against that paint colour. Wheel hubs become plain green, as in the photo. Mud and wear are added afterwards
by weather_hf2e.py on these colours. usage: python camo_hf2e.py TEXDIR POSDIR OUTDIR"""
import sys,os,shutil,numpy as np
from PIL import Image
TD,PD,OD=sys.argv[1:4];os.makedirs(OD,exist_ok=True)
G,B,D=np.array([57,66,50.]),np.array([87,71,62.]),np.array([47,50,57.])
rng=np.random.default_rng(11);LAT=[rng.random((40,40,40)) for _ in range(6)]
def vnoise(p,lat):
    q=np.mod(p,39);i=np.floor(q).astype(int);f=q-i;f=f*f*(3-2*f);j=np.minimum(i+1,39);s=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2])
                s=s+w*lat[(j if dx else i)[:,0],(j if dy else i)[:,1],(j if dz else i)[:,2]]
    return s
def fbm(p,k):return (vnoise(p,LAT[k])*0.6+vnoise(p*2.03+7.1,LAT[k+1])*0.28+vnoise(p*4.1+3.3,LAT[k+2])*0.12)
FREQ=1/1.1          # one noise cell per 1.1 m: patches about 1-2 m on the 9.3 m model
smp=np.random.default_rng(3).uniform([-5,-1,0],[5,1,2.7],(200000,3))*FREQ
T1=np.quantile(fbm(smp,0),0.70);T2=np.quantile(fbm(smp+50,3),0.78)
ss=lambda e0,e1,x:np.clip((x-e0)/(e1-e0),0,1)**2*(3-2*np.clip((x-e0)/(e1-e0),0,1))
for f in sorted(os.listdir(TD)):
    if not f.endswith('_BaseColor.png'):
        shutil.copy(os.path.join(TD,f),OD);continue
    m=f[len('hf2e_'):-len('_BaseColor.png')];img=np.asarray(Image.open(os.path.join(TD,f)).convert('RGB'),float)
    pos=np.load(f'{PD}/pos_{m}.npy').astype(np.float32)[::-1]   # npy rows are bottom-up
    ok=~np.isnan(pos[...,0])
    # main paint colour: the most common bright, low-saturation colour (blue-grey body, white cab)
    q=(img[ok]//16).astype(int);sat=img[ok].max(1)-img[ok].min(1);cand=q[(img[ok].mean(1)>110)&(sat<60)]
    if len(cand)<1000:shutil.copy(os.path.join(TD,f),OD);print('CAMO',m,'no paint, unchanged');continue
    keys,cnt=np.unique(cand[:,0]*256+cand[:,1]*16+cand[:,2],return_counts=True);k=keys[cnt.argmax()];paint=np.array([k//256,(k//16)%16,k%16])*16+8
    d=np.linalg.norm(img-paint,axis=-1);mask=np.clip((70-d)/25,0,1)*ok
    lum=lambda c:c[...,0]*0.3+c[...,1]*0.59+c[...,2]*0.11
    shade=np.clip(lum(img)/max(lum(paint),1),0.55,1.25)[...,None]
    if m=='standardSurface1_Inst_5':col=np.broadcast_to(G,img.shape)
    else:
        P=np.nan_to_num(pos[...,:3]).reshape(-1,3)*FREQ;n1=fbm(P,0).reshape(img.shape[:2]);n2=fbm(P+50,3).reshape(img.shape[:2])
        br=ss(T1-0.006,T1+0.006,n1)[...,None];dk=ss(T2-0.006,T2+0.006,n2)[...,None]
        col=G*(1-br)+B*br;col=col*(1-dk)+D*dk
    out=img*(1-mask[...,None])+np.clip(col*shade,0,255)*mask[...,None]
    Image.fromarray(out.round().astype(np.uint8)).save(os.path.join(OD,f))
    print('CAMO',m,'paint',paint.tolist(),'painted %.0f%%'%(100*(mask>0.5).sum()/max(ok.sum(),1)))
