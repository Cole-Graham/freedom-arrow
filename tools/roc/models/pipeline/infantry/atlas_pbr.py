"""ROC infantry atlas v2 (Shawn 27 Nov 03:1x: "enhance the texture of all infantry PBR textures by following the latest Chinese paratroopers").
Same output names as atlas_roc.py (roc_<key>_<lod>.fas/.png/_n.png) plus a PBR mask, roc_<key>_<lod>_mask.png (HDRP: R metallic, G AO,
B 0, A smoothness), which FAModels already reads beside any texture. Changes against atlas_roc.py:
  - texel space by surface: each part's tile is sized by the square root of its 3D surface area (skyline-packed, then grown into the free space), instead of equal grid cells,
    so coat, trousers and vest get several times the pixels of goggles or straps;
  - the sources' own roughness / metal / AO maps are used: UE ORM (R AO, G rough, B metal), separate _Roughness/_Metallic, or GTA _spec_
    (specular -> smoothness); parts without them get matte cloth defaults;
  - AO is also multiplied into the colour (60 %), and downscaled tiles get a light unsharp mask, for depth and crisp detail.
ALPHA=1 keeps cut-out alpha (ghillie), as atlas_roc.py. usage: python atlas_pbr.py RIGS OUT"""
from pathlib import Path
import argparse,io,json,struct,math,os,re
from PIL import Image,ImageFilter
import numpy as np
from functools import lru_cache
ap=argparse.ArgumentParser();ap.add_argument('rigs',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def n(f):return struct.unpack('<i',f.read(4))[0]
def s(f):return f.read(n(f)).decode()
def ws(f,t):b=t.encode();f.write(struct.pack('<i',len(b))+b)
def find(base,subs):
    if not base:return None
    p=Path(base);d=p.parent;st=p.stem
    for a_,b_ in subs:
        if a_ in st:
            for e in ('.png','.PNG','.jpg','.tga','.jpeg'):
                q=d/(st.replace(a_,b_)+e)
                if q.exists():return str(q)
    return None
@lru_cache(maxsize=200)
def texture(path,size,keep_alpha=False):
    im=Image.open(path)
    if not (keep_alpha and im.mode in ('RGBA','LA')):im=im.convert('RGB')
    return im.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
@lru_cache(maxsize=200)
def maskmap(base,size):
    """(R metal, G AO, B 0, A smooth) for one material, as an RGBA image, from whatever maps the source has."""
    o=find(base,[('_Color','_ORM'),('_color','_ORM'),('_BaseColor','_OcclusionRoughnessMetallic')])
    if o:
        x=np.asarray(Image.open(o).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),np.float32)/255
        ao,rough,met=x[...,0],x[...,1],x[...,2]
    else:
        r=find(base,[('Base_Color','Roughness'),('_BaseColor','_Roughness'),('_Diffuse','_Roughness')]);m=find(base,[('Base_Color','Metallic'),('_BaseColor','_Metallic')])
        sp=find(base,[('_diff_','_spec_')])
        if not sp and base:   # GTA-style packs: uppr_diff_000_a_uni -> uppr_spec_000
            m_=re.match(r'(.+?)_diff_(\d+)',Path(base).stem)
            if m_:
                for e in ('.png','.PNG','.jpg'):
                    q=Path(base).parent/f'{m_[1]}_spec_{m_[2]}{e}'
                    if q.exists():sp=str(q);break
        L=lambda q:np.asarray(Image.open(q).convert('L').resize((size,size),Image.Resampling.LANCZOS),np.float32)/255
        ao=np.ones((size,size),np.float32)
        if r:rough=L(r)
        elif sp:v=L(sp);rough=1-np.clip(0.15+0.7*(v-v.min())/max(np.ptp(v),1e-3),0,0.85)
        else:rough=np.full((size,size),0.72,np.float32)
        met=L(m) if m else np.zeros((size,size),np.float32)
    return np.dstack([met,ao,np.zeros_like(ao),1-rough]),bool(o or r or m or sp)
audit=[]
ALPHA=bool(os.environ.get('ALPHA'))
for c in json.loads((a.rigs/'configurations.json').read_text()):
 for level,size in [(0,2048),(1,1024),(2,512)]:
  f=io.BytesIO((a.rigs/c['key']/f'lod{level}.fas').read_bytes());assert f.read(4)==b'FAS1';bones=[s(f) for _ in range(n(f))];parts=[]
  for _ in range(n(f)):
   mat=s(f);nv=n(f);raw=f.read(nv*64);ni=n(f);ix=struct.unpack('<'+'i'*ni,f.read(ni*4));parts.append((mat,raw,ix))
  assert not f.read();name=f"roc_{c['key']}_{level}.png";pad=max(2,size//512)
  ranges=[];areas=[]
  for mat,raw,ix in parts:
   P=np.frombuffer(raw,dtype=np.float32).reshape(-1,16);uv=P[:,6:8];X=P[:,0:3]
   ranges.append((min(0,float(uv[:,0].min())),max(1,float(uv[:,0].max())),min(0,float(uv[:,1].min())),max(1,float(uv[:,1].max()))))
   T=np.array(ix).reshape(-1,3);areas.append(0.5*np.linalg.norm(np.cross(X[T[:,1]]-X[T[:,0]],X[T[:,2]]-X[T[:,0]]),axis=1).sum()+1e-6)
  # tile side ~ sqrt(area) * k, largest k whose skyline packing fits in size x size; then each tile (largest area first) grows in 8 px steps
  # while everything still fits, so the sheet has little empty space (27 Nov v2: shelf packing left 23-42 % of the sheet empty)
  def pack(sides):
   rects={};H=np.zeros(size,np.int32)
   for j in sorted(range(len(sides)),key=lambda j:-sides[j]):
    w=sides[j];best=None
    if w>size:return None
    for x in range(0,size-w+1,8):
     y=int(H[x:x+w].max())
     if y+w<=size and (best is None or y<best[1]):best=(x,y)
    if best is None:return None
    rects[j]=(best[0],best[1],w);H[best[0]:best[0]+w]=best[1]+w
   return rects
  sd=lambda k:[max(32,int(math.sqrt(A)*k*size/2048)//8*8) for A in areas]
  lo_,hi_=1.0,size*4.0
  for _ in range(40):
   mid=(lo_+hi_)/2
   if pack(sd(mid)):lo_=mid
   else:hi_=mid
  sides=sd(lo_)
  for j in sorted(range(len(sides)),key=lambda j:-areas[j]):
   while True:
    t=list(sides);t[j]+=8
    if pack(t):sides=t
    else:break
  rects=pack(sides)
  for suffix,field,default in [('', 'base',(70,80,60,255)),('_n','normal',(128,128,255,255)),('_mask',None,(0,255,0,77))]:
   atlas=Image.new('RGBA',(size,size),default)
   for j,(mat,_,_) in enumerate(parts):
    x0,y0,w=rects[j];inner=w-2*pad;base=c['textures'][mat]['base']
    if field=='base':path=base;im=texture(path,max(inner,512),ALPHA) if path else None
    elif field=='normal':path=c['textures'][mat]['normal'];im=texture(path,max(inner,512)) if path else None
    else:
     mk,_=maskmap(base,max(inner,512)) if base else (None,False)
     im=Image.fromarray((np.clip(mk,0,1)*255).astype(np.uint8),'RGBA') if mk is not None else None
    if im is None:im=Image.new('RGBA',(max(inner,512),max(inner,512)),default)
    if field=='base' and base:   # AO into the colour (60 %)
     mk,_=maskmap(base,im.size[0]);px=np.asarray(im).astype(np.float32);px[...,:3]*=(0.4+0.6*mk[...,1:2]);im=Image.fromarray(np.clip(px,0,255).astype(np.uint8),'RGBA')
    u0,u1,v0,v1=ranges[j];W,H=im.size;pixels=np.asarray(im)
    xx=(((u0+(np.arange(inner)+.5)/inner*(u1-u0))%1)*W).astype(int);yy=(((1-(v1-(np.arange(inner)+.5)/inner*(v1-v0)))%1)*H).astype(int)
    im=Image.fromarray(pixels[yy[:,None],xx[None,:]])
    if field=='base' and inner<W:im=im.filter(ImageFilter.UnsharpMask(radius=1.2,percent=60,threshold=2))
    tile=Image.new('RGBA',(w,w),default);tile.paste(im,(pad,pad));tile.paste(im.crop((0,0,1,inner)).resize((pad,inner)),(0,pad));tile.paste(im.crop((inner-1,0,inner,inner)).resize((pad,inner)),(w-pad,pad));tile.paste(tile.crop((0,pad,w,pad+1)).resize((w,pad)),(0,0));tile.paste(tile.crop((0,w-pad-1,w,w-pad)).resize((w,pad)),(0,w-pad))
    atlas.paste(tile,(x0,y0))
   atlas.save(a.out/(Path(name).stem+suffix+'.png'),compress_level=1)
  records=[];indices=[];unique={}
  for j,(mat,raw,ix) in enumerate(parts):
   x0,y0,w=rects[j];inner=w-2*pad;mapping=[]
   for i in range(len(raw)//64):
    rec=bytearray(raw[i*64:(i+1)*64]);u,v=struct.unpack_from('<2f',rec,24)
    u0,u1,v0,v1=ranges[j];u=(u-u0)/(u1-u0);v=(v-v0)/(v1-v0)
    struct.pack_into('<2f',rec,24,(x0+pad+u*inner)/size,1-(y0+pad+(1-v)*inner)/size);rec=bytes(rec)
    if rec not in unique:unique[rec]=len(records);records.append(rec)
    mapping.append(unique[rec])
   indices.extend(mapping[i] for i in ix)
  out=a.out/f"roc_{c['key']}_{level}.fas"
  with out.open('wb') as f:
   f.write(b'FAS1'+struct.pack('<i',40))
   for b in bones:ws(f,b)
   f.write(struct.pack('<i',1));ws(f,name);f.write(struct.pack('<i',len(records)));f.write(b''.join(records));f.write(struct.pack('<i',len(indices))+struct.pack('<'+'i'*len(indices),*indices))
  pbr=sum(1 for mat,_,_ in parts if c['textures'][mat]['base'] and maskmap(c['textures'][mat]['base'],64)[1])
  audit.append({'unit':c['unit'],'key':c['key'],'lod':level,'triangles':len(indices)//3,'gpu_vertices':len(records),'materials':1,'atlas_size':size,'file':out.name,'pbr_parts':f'{pbr}/{len(parts)}','biggest_tile':max(r[2] for r in rects.values())})
(a.out/'rig-budget.json').write_text(json.dumps(audit,indent=2)+'\n');print('Packed',len(audit),'skinned LODs',[(x['key'],x['lod'],x['pbr_parts'],x['biggest_tile']) for x in audit if x['lod']==0])
