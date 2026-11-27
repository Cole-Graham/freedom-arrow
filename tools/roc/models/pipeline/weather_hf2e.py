"""Moderate weathering for the ROC Hsiung Feng IIE textures (Shawn 26 Nov 19:56 PST: "Mud ... around the lower hull and wheel areas, while worn metal and
chipped paint can be added to the upper parts ... do not make it look too old or overly damaged"). Runs in Blender (numpy + image IO, no render):
blender -b -P weather_hf2e.py -- TEXDIR GEODIR OUTDIR [SEED]
Inputs per material: hf2e_<mat>_{BaseColor,Normal,AO,Metallic,Roughness}.png and geo_<mat>.exr (baked on Vengeance by bake.py: R = height / 3 m,
G = up-facing, B = pointiness). Mud follows height (full below ~0.3 m, gone by ~1.0 m) and crevices (AO); the 12 wheels get an even coat.
Worn metal follows baked bevel edges (edge_<mat>.exr) above 0.75 m; chips and a light dust on up-facing surfaces. Coverage is printed."""
import bpy,sys,os,shutil,numpy as np
a=sys.argv[sys.argv.index('--')+1:];TD,GD,OD=a[:3];seed=int(a[3]) if len(a)>3 else 7;os.makedirs(OD,exist_ok=True)
def load(p,ch=4):
    im=bpy.data.images.load(p);im.colorspace_settings.name='Non-Color';w,h=im.size;x=np.empty(w*h*4,np.float32);im.pixels.foreach_get(x);bpy.data.images.remove(im);return x.reshape(h,w,4)
def save(p,arr):
    h,w=arr.shape[:2];im=bpy.data.images.new(os.path.basename(p),w,h,alpha=False);im.colorspace_settings.name='Non-Color'
    if arr.ndim==2:arr=np.stack([arr,arr,arr],-1)
    rgba=np.concatenate([np.clip(arr[...,:3],0,1),np.ones((h,w,1),np.float32)],-1);im.pixels.foreach_set(rgba.astype(np.float32).ravel());im.filepath_raw=p;im.file_format='PNG';im.save();bpy.data.images.remove(im)
rng=np.random.default_rng(seed)
def up(g,N):
    n=g.shape[0];c=np.linspace(0,n-1,N);i0=np.floor(c).astype(int);i1=np.minimum(i0+1,n-1);f=c-i0;f=f*f*(3-2*f)
    r=g[i0]*(1-f)[:,None]+g[i1]*f[:,None];return r[:,i0]*(1-f)[None]+r[:,i1]*f[None]
def fbm(N,cells,oct=4):
    s=0;t=0;amp=1
    for o in range(oct):s=s+amp*up(rng.random((cells*2**o+1,cells*2**o+1)),N);t+=amp;amp*=0.5
    s/=t;return (s-s.min())/(np.ptp(s)+1e-6)
def blur(x,r):
    for ax in (0,1):
        c=np.cumsum(np.pad(x,[(r+1,r) if i==ax else (0,0) for i in range(2)],mode='edge'),axis=ax);x=(np.take(c,range(2*r+1,c.shape[ax]),axis=ax)-np.take(c,range(0,c.shape[ax]-2*r-1),axis=ax))/(2*r+1)
    return x
ss=lambda e0,e1,x:np.clip((x-e0)/(e1-e0),0,1)**2*(3-2*np.clip((x-e0)/(e1-e0),0,1))
mats=sorted({f.split('hf2e_')[1].rsplit('_',1)[0] for f in os.listdir(TD) if f.endswith('_BaseColor.png')})
for m in mats:
    p=lambda k:f'{TD}/hf2e_{m}_{k}.png'
    base=load(p('BaseColor'))[...,:3];N=base.shape[0];nrm=load(p('Normal'))[...,:3];ao=load(p('AO'))[...,0];met=load(p('Metallic'))[...,0];rou=load(p('Roughness'))[...,0]
    geo=load(f'{GD}/geo_{m}.exr');H=geo[...,0]*3;upf=geo[...,1]*2-1;valid=(geo[...,0]>0.001)|(geo[...,2]>0.001)
    NL,NM,NF,NF2=fbm(N,4),fbm(N,16),fbm(N,64,3),fbm(N,128,2)
    wheel=m=='standardSurface1_Inst_5'
    # mud: lower hull by height, crevices by AO, wheels evenly
    mh=np.full_like(H,0.45) if wheel else np.clip((0.9-H)/0.65,0,1)
    mud=mh*(0.65+0.7*(NM-0.5))+(1-ao)*0.22*np.clip((1.3-H)/0.6,0,1)
    mudA=ss(0.32,0.62,mud+(NF-0.5)*0.38)*(0.6 if wheel else 0.72)*valid
    mudc=np.stack([np.interp(NL,[0,1],[0.50,0.31]),np.interp(NL,[0,1],[0.43,0.25]),np.interp(NL,[0,1],[0.34,0.19])],-1)
    # light dust on up-facing surfaces
    dustA=(0 if wheel else 1)*np.clip((upf-0.55)/0.45,0,1)*0.16*(0.4+NM)*valid
    # worn metal on bevelled edges (normal map), upper body only
    edge=load(f'{GD}/edge_{m}.exr')[...,0]   # baked bevel edges (Vengeance, bake.py EDGE=1)
    ed=np.clip((blur(edge,1)-0.9)/1.8,0,1)
    upper=ss(0.7,0.95,H)*(0 if wheel else 1)*valid
    wear=np.clip(ed*ss(0.52,0.78,NF2+(NM-0.5)*0.3),0,1)*upper*0.9
    cs=NF2*0.6+NF*0.4;q=np.quantile(cs[valid],[0.965,0.985]) if valid.any() else [1,1];chip=ss(q[0],q[1],cs)*(NM>0.4)*upper*0.7
    c=base.copy();r=rou.copy();mt=met.copy()
    dust=np.array([0.60,0.56,0.48]);c=c*(1-dustA[...,None])+dust*dustA[...,None];r=r+dustA*0.25
    c=c*(1-chip[...,None])+np.array([0.27,0.27,0.24])*chip[...,None];r=r*(1-chip)+0.75*chip;mt=mt*(1-chip)
    c=c*(1-wear[...,None])+np.array([0.58,0.57,0.55])*wear[...,None];r=r*(1-wear)+0.38*wear;mt=mt*(1-wear)+0.8*wear
    c=c*(1-mudA[...,None])+mudc*mudA[...,None];r=r*(1-mudA)+0.92*mudA;mt=mt*(1-mudA)
    save(f'{OD}/hf2e_{m}_BaseColor.png',c);save(f'{OD}/hf2e_{m}_Roughness.png',np.clip(r,0,1));save(f'{OD}/hf2e_{m}_Metallic.png',np.clip(mt,0,1))
    for k in ('Normal','AO'):shutil.copy(p(k),f'{OD}/hf2e_{m}_{k}.png')
    v=valid.mean()+1e-6
    print('WEATHER',m,'mud %.1f%%'%(100*(mudA>0.3).sum()/valid.sum()),'wear %.1f%%'%(100*(wear>0.3).sum()/valid.sum()),'chips %.1f%%'%(100*(chip>0.3).sum()/valid.sum()),'dust %.1f%%'%(100*(dustA>0.08).sum()/valid.sum()))
