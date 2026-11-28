"""ROC infantry PBR enhancement (Shawn 28 Nov 03:0x, list 7: "Enhance PBR textures of all the ROC infantry models following the Chinese Thunder
God Model"). Measured 28 Nov on the 2048 atlases: the Thunder Gods body (pla2_sf_goggles_down_desert_0) has normal relief of 12.1 deg mean
tilt (90th percentile 29.4 deg) and its fabric folds are shaded into the colour; ROC Infantry has 7.5 deg (19.1 deg) and a flat AO channel
(mask G mean 254 of 255, the source packs have no AO map), so the uniforms read flat in game.
For one body texture set (roc_<key>_<lod>{,_n,_mask}.png): normal x/y x1.55 (about the Thunder God relief), an ambient-occlusion term from
the normal map's concavity at three scales (2, 6 and 16 px at 2048, scaled for smaller sheets) into mask G and multiplied into the colour
(55 %), and crevices made rougher (mask A x (0.75 + 0.25 AO)). Alpha (cut-outs) and metal stay. Originals go to lod/pre-pbr2/ once;
the script always starts from them, so a re-run does not stack. usage: python pbr_enhance.py LODDIR STEM [STEM ...]"""
import sys,os,shutil
import numpy as np
from PIL import Image,ImageFilter
AO_K=float(os.environ.get("AO_K","3.2"));AO_C=float(os.environ.get("AO_C","0.75"));NK=float(os.environ.get("NK","1.8"));SM=float(os.environ.get("SM","0.8"))
L=sys.argv[1];BK=L+'/pre-pbr2';os.makedirs(BK,exist_ok=True)
def blur(a,s):                     # separable Gaussian (edge-clamped), float
    r=int(3*s)+1;k=np.exp(-0.5*(np.arange(-r,r+1)/s)**2);k/=k.sum();a=a.astype(np.float32)
    for ax in (0,1):
        p=np.pad(a,[(r,r) if i==ax else (0,0) for i in (0,1)],mode='edge');a=sum(k[i]*np.take(p,range(i,i+a.shape[ax]),axis=ax) for i in range(2*r+1))
    return a
for stem in sys.argv[2:]:
    for sfx in ('','_n','_mask'):
        if not os.path.exists(f'{BK}/{stem}{sfx}.png'):shutil.copy(f'{L}/{stem}{sfx}.png',f'{BK}/{stem}{sfx}.png')
    C=Image.open(f'{BK}/{stem}.png');mode=C.mode;C=np.asarray(C.convert('RGBA')).astype(np.float32)
    N=np.asarray(Image.open(f'{BK}/{stem}_n.png').convert('RGB')).astype(np.float32)/127.5-1
    K=np.asarray(Image.open(f'{BK}/{stem}_mask.png').convert('RGBA')).astype(np.float32)
    H=C.shape[0];f=H/2048
    flat=(np.abs(N[...,0])<0.02)&(np.abs(N[...,1])<0.02)          # untextured padding / flat tiles get nothing
    # concavity: divergence of the tangent-space normal (OpenGL: +y up = -row): negative in valleys
    div=np.gradient(N[...,0],axis=1)-np.gradient(N[...,1],axis=0)
    cav=sum(w*np.clip(-blur(div,max(0.6,s*f))*s*f,0,None) for s,w in ((2,0.5),(6,0.3),(16,0.2)))
    ao=np.clip(1-AO_K*cav,0.35,1.0);ao[flat]=1.0;ao=blur(ao,max(0.6,1.0*f))
    n2=N.copy();n2[...,:2]*=NK;n2/=np.linalg.norm(n2,axis=2,keepdims=True)
    C[...,:3]*=(1-AO_C*(1-ao))[...,None]
    K[...,1]=np.minimum(K[...,1],ao*255);K[...,3]*=SM*(0.75+0.25*ao)
    Image.fromarray(C.clip(0,255).round().astype(np.uint8),'RGBA').convert(mode).save(f'{L}/{stem}.png')
    Image.fromarray(((n2+1)*127.5).clip(0,255).round().astype(np.uint8),'RGB').save(f'{L}/{stem}_n.png')
    Image.fromarray(K.clip(0,255).round().astype(np.uint8),'RGBA').save(f'{L}/{stem}_mask.png')
    t=np.degrees(np.arccos(np.clip(n2[...,2],-1,1)))[~flat]
    print(stem,H,'AO mean %.3f (p5 %.2f), normal tilt mean %.1f deg p90 %.1f'%(ao[~flat].mean(),np.percentile(ao[~flat],5),t.mean(),np.percentile(t,90)))
