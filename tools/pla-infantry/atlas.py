"""Atlas FAS materials without changing geometry or normalized skin weights."""
from pathlib import Path
import argparse,io,json,struct,math
from PIL import Image
import numpy as np
from functools import lru_cache
ap=argparse.ArgumentParser();ap.add_argument('rigs',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def n(f):return struct.unpack('<i',f.read(4))[0]
def s(f):return f.read(n(f)).decode()
def ws(f,t):b=t.encode();f.write(struct.pack('<i',len(b))+b)
audit=[]
@lru_cache(maxsize=160)
def texture(path,size):
 return Image.open(path).convert('RGB').convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
for c in json.loads((a.rigs/'configurations.json').read_text()):
 for level,size in [(0,2048),(1,1024),(2,512)]:
  f=io.BytesIO((a.rigs/c['key']/f'lod{level}.fas').read_bytes());assert f.read(4)==b'FAS1';bones=[s(f) for _ in range(n(f))];parts=[]
  for _ in range(n(f)):
   mat=s(f);nv=n(f);raw=f.read(nv*64);ni=n(f);ix=struct.unpack('<'+'i'*ni,f.read(ni*4));parts.append((mat,raw,ix))
  assert not f.read();grid=math.ceil(math.sqrt(len(parts)));cell=size//grid;pad=4;inner=cell-2*pad;name=f"pla2_{c['key']}_{level}.png"
  ranges=[]
  for mat,raw,_ in parts:
   uv=[struct.unpack_from('<2f',raw,i*64+24) for i in range(len(raw)//64)]
   ranges.append((min(0,min(u for u,v in uv)),max(1,max(u for u,v in uv)),min(0,min(v for u,v in uv)),max(1,max(v for u,v in uv))))
  for suffix,field,default in [('', 'base',(70,80,60,255)),('_n','normal',(128,128,255,255))]:
   atlas=Image.new('RGBA',(size,size),default)
   for j,(mat,_,_) in enumerate(parts):
    path=c['textures'][mat][field]
    im=texture(path,max(inner,512)) if path else Image.new('RGBA',(max(inner,512),max(inner,512)),default)
    u0,u1,v0,v1=ranges[j];w,h=im.size;pixels=np.asarray(im)
    xx=(((u0+(np.arange(inner)+.5)/inner*(u1-u0))%1)*w).astype(int)
    yy=(((1-(v1-(np.arange(inner)+.5)/inner*(v1-v0)))%1)*h).astype(int)
    im=Image.fromarray(pixels[yy[:,None],xx[None,:]])
    im=im.resize((inner,inner),Image.Resampling.LANCZOS);tile=Image.new('RGBA',(cell,cell),default);tile.paste(im,(pad,pad));tile.paste(im.crop((0,0,1,inner)).resize((pad,inner)),(0,pad));tile.paste(im.crop((inner-1,0,inner,inner)).resize((pad,inner)),(cell-pad,pad));tile.paste(tile.crop((0,pad,cell,pad+1)).resize((cell,pad)),(0,0));tile.paste(tile.crop((0,cell-pad-1,cell,cell-pad)).resize((cell,pad)),(0,cell-pad));atlas.paste(tile,((j%grid)*cell,(j//grid)*cell))
   atlas.save(a.out/(Path(name).stem+suffix+'.png'),compress_level=1)
  records=[];indices=[];unique={}
  for j,(mat,raw,ix) in enumerate(parts):
   mapping=[]
   for i in range(len(raw)//64):
    rec=bytearray(raw[i*64:(i+1)*64]);u,v=struct.unpack_from('<2f',rec,24)
    u0,u1,v0,v1=ranges[j];u=(u-u0)/(u1-u0);v=(v-v0)/(v1-v0)
    struct.pack_into('<2f',rec,24,((j%grid)*cell+pad+u*inner)/size,1-((j//grid)*cell+pad+(1-v)*inner)/size);rec=bytes(rec)
    if rec not in unique:unique[rec]=len(records);records.append(rec)
    mapping.append(unique[rec])
   indices.extend(mapping[i] for i in ix)
  out=a.out/f"pla2_{c['key']}_{level}.fas"
  with out.open('wb') as f:
   f.write(b'FAS1'+struct.pack('<i',40))
   for b in bones:ws(f,b)
   f.write(struct.pack('<i',1));ws(f,name);f.write(struct.pack('<i',len(records)));f.write(b''.join(records));f.write(struct.pack('<i',len(indices))+struct.pack('<'+'i'*len(indices),*indices))
  audit.append({'unit':c['unit'],'key':c['key'],'lod':level,'triangles':len(indices)//3,'gpu_vertices':len(records),'materials':1,'atlas_size':size,'file':out.name})
(a.out/'rig-budget.json').write_text(json.dumps(audit,indent=2)+'\n');print('Packed',len(audit),'skinned LODs')
