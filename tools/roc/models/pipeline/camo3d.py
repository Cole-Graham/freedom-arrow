"""3D camouflage repaint of a converted ROC model, on famconv's output textures (Shawn 27 Nov 02:2x: "port the CM26 Woodland textures to [CM-22]
... and do similar camouflage texture redrawing for the CM-21"; CM-32 gets the CM-34 sets). Per textured material: world position of every texel
(uvpos.py on the same GLB); texels close to one of the model's own camo colours (OLD) are repainted with a pattern laid out in 3D, so patches run
across UV seams. Each texel keeps its shading relative to its old camo colour (panel lines, AO), clipped 0.75-1.25.
PATTERN woodland: base colour + 3 blob layers (fractal noise thresholds, ~1-2 m patches). PATTERN blocks: square blocks (~0.25 m) like the CM-34
mosaic. Writes Arsenal + battle colour textures; originals in x/<slug>/pre-camo/ (reruns start from them). Run weather_fam.py afterwards.
usage: python camo3d.py SLUG GLB LENGTH_M SPEC.json [SCHEME]   SPEC: {"old": [[r,g,b],...], "pattern": "woodland"|"blocks",
       "colors": [[base],[layer1],[layer2],[layer3]], "cover": [0.30,0.20,0.15], "size": 1.4, "radius": 38}
SCHEME given: writes <tex>@SCHEME.png beside the default instead of replacing it (paint-button option)."""
import sys,os,json,shutil,numpy as np
from PIL import Image
from pygltflib import GLTF2
s,glb,L,spec=sys.argv[1],sys.argv[2],float(sys.argv[3]),json.load(open(sys.argv[4]));SCH=sys.argv[5] if len(sys.argv)>5 else ''
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';M=V+'/models';X=f'{V}/x/{s}';BK=X+'/pre-camo';os.makedirs(BK,exist_ok=True)
mats=[m.name for m in GLTF2().load(glb).materials]
rng=np.random.default_rng(31);LAT=[rng.random((48,48,48)) for _ in range(9)]
def vnoise(p,lat):
    n=lat.shape[0]-1;q=np.mod(p,n);i=np.floor(q).astype(int);f=q-i;f=f*f*(3-2*f);j=np.minimum(i+1,n);out=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2])
                out=out+w*lat[(j if dx else i)[:,0],(j if dy else i)[:,1],(j if dz else i)[:,2]]
    return out
def fbm(p,k):return vnoise(p,LAT[k])*0.6+vnoise(p*2.03+7.1,LAT[k+1])*0.28+vnoise(p*4.1+3.3,LAT[k+2])*0.12
pos={};allp=[]
for i,m in enumerate(mats):
    f=f'{X}/pos/pos_{m.split(".")[0]}.npy'
    if os.path.exists(f):pos[i]=np.load(f).astype(np.float32)[::-1];allp.append(pos[i][~np.isnan(pos[i][...,0])][:,:3])
A=np.concatenate(allp);mn,mx=A.min(0),A.max(0);sc=L/max((mx-mn)[0],(mx-mn)[1])
OLD=np.array(spec['old'],float);COL=np.array(spec['colors'],float);cover=spec.get('cover',[0.3,0.2,0.15]);size=spec.get('size',1.4);rad=spec.get('radius',38)
# thresholds so each layer covers about 'cover' of a random sample of the vehicle volume
smp=(np.random.default_rng(4).uniform(mn,mx,(150000,3))-mn)*sc/size
if spec['pattern']=='woodland':
    T=[np.quantile(fbm(smp+40*k,k*3 if k<3 else 0),1-c) for k,c in enumerate(cover)]
lum=lambda c:c[...,0]*0.3+c[...,1]*0.59+c[...,2]*0.11
out_names=[]
def src_of(name):
    p=f'{M}/{name}'
    if not os.path.exists(f'{BK}/{name}') and os.path.exists(p):shutil.copy(p,f'{BK}/{name}')
    return f'{BK}/{name}'
for i,P in pos.items():
    st=f'm_roc_{s}_static_tex{i}';lo=f'm_roc_{s}_lo_static_tex{i}'
    if not os.path.exists(f'{M}/{st}.png'):continue
    if i in spec.get('skip',[]):continue   # e.g. track sheets
    full_exists=os.path.exists(f'{M}/tex_full/{st}.png')
    if full_exists and not os.path.exists(f'{BK}/tex_full_{st}.png'):shutil.copy(f'{M}/tex_full/{st}.png',f'{BK}/tex_full_{st}.png')
    stat_src=src_of(f'{st}.png');lo_src=src_of(f'{lo}.png') if os.path.exists(f'{M}/{lo}.png') else None
    img=Image.open(f'{BK}/tex_full_{st}.png' if full_exists else stat_src).convert('RGBA');Wd,Hd=img.size;S=Wd;alpha=np.asarray(img)[...,3]
    c=np.asarray(img.convert('RGB'),float)
    Q=P[np.arange(Hd)*P.shape[0]//Hd][:,np.arange(Wd)*P.shape[1]//Wd];ok=~np.isnan(Q[...,0]);W=(np.nan_to_num(Q[...,:3])-mn)*sc/size
    d=np.linalg.norm(c[...,None,:]-OLD[None,None],axis=-1);near=d.argmin(-1);mask=(d.min(-1)<rad)&ok
    shade=np.clip(lum(c)/np.maximum(lum(OLD[near]),1),0.75,1.25)
    flat=W.reshape(-1,3)
    if spec['pattern']=='woodland':
        col=np.empty_like(c);col[:]=COL[0]
        for k in range(len(cover)):
            n=fbm(flat+40*k,k*3 if k<3 else 0).reshape(Hd,Wd);col[n>T[k]]=COL[k+1]
    else:   # blocks: integer cells, a hashed value picks the colour; cell size 'size' metres (pattern scale)
        cell=np.floor(flat*spec.get('block',4.0)).astype(np.int64);h=((cell[:,0]*73856093)^(cell[:,1]*19349663)^(cell[:,2]*83492791))%1000/1000.0
        big=fbm(flat,0);v=(0.55*h+0.45*big).reshape(Hd,Wd);edges=np.cumsum([0]+list(spec['weights']))/sum(spec['weights'])
        col=COL[np.clip(np.searchsorted(edges,v,side='right')-1,0,len(COL)-1)]
    newc=np.where(mask[...,None],np.clip(col*shade[...,None],0,255),c)
    res=Image.fromarray(np.dstack([newc.round().astype(np.uint8),alpha]),'RGBA')
    tag=(f'@{SCH}' if SCH else '')
    dst=lambda n:f'{X}/schemes/{n}{tag}.png' if SCH else f'{M}/{n}.png'
    if SCH:os.makedirs(f'{X}/schemes',exist_ok=True)
    if full_exists and not SCH:res.save(f'{M}/tex_full/{st}.png')
    res.resize(Image.open(stat_src).size,Image.LANCZOS).save(dst(st));out_names.append(os.path.basename(dst(st)))
    if lo_src:res.resize(Image.open(lo_src).size,Image.LANCZOS).save(dst(lo));out_names.append(os.path.basename(dst(lo)))
    print('CAMO3D',s,'tex%d'%i,mats[i][:30],'repainted %.0f%% of the used texels (%dpx)'%(100*mask.sum()/max(ok.sum(),1),S),file=sys.stderr)
print('\n'.join(out_names))
