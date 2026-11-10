"""Bake the supplied F14 wing pivots into the existing static armory export; preserve other draws exactly."""
from pathlib import Path
import struct,io,json,sys,importlib.util,math,hashlib,argparse
import numpy as np
from pygltflib import GLTF2
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',type=Path,required=True);parser.add_argument('--glb',type=Path,required=True);parser.add_argument('--converter',type=Path,required=True);parser.add_argument('--pivots',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();source=args.model;glb=args.glb;r=args.output;r.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()=='5da8dde77a4c5f34c409c323eac836fb379a274a2b5573a9962fc3b2a8a49ab8'
assert hashlib.sha256(glb.read_bytes()).hexdigest()=='e4317f8efc6e4c931f296bd23569a3c154027ca0ae2d6cb17643460cbbf558f5'
g=GLTF2().load(glb);blob=g.binary_blob()
spec=importlib.util.spec_from_file_location('fc',args.converter);fc=importlib.util.module_from_spec(spec);spec.loader.exec_module(fc)
expected=[]
def walk(index,parent):
 nd=g.nodes[index];M=parent@fc.node_matrix(nd)
 if nd.mesh is not None:
  for p in g.meshes[nd.mesh].primitives:
   assert p.mode in (None,4);raw=fc.acc(g,blob,p.attributes.POSITION);raw=(np.c_[raw,np.ones(len(raw))]@M.T)[:,:3];expected.append((nd.name,p,raw))
 for child in nd.children or []:walk(child,M)
for index in g.scenes[g.scene or 0].nodes:walk(index,np.eye(4))
data=source.read_bytes();f=io.BytesIO(data);num=lambda:struct.unpack('<i',f.read(4))[0];string=lambda:f.read(num()).decode();assert f.read(4)==b'FAM1' and num()==1;assert string()=='root';assert num()==len(expected);draws=[]
for name,prim,raw in expected:
 start=f.tell();tex=string();f.read(16);nv=num();posoff=f.tell();p=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();noff=f.tell();n=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();uv=f.read(nv*8);ni=num();ix=f.read(ni*4);assert nv==len(raw);draws.append({'name':name,'p':p,'n':n,'raw':raw,'posoff':posoff,'noff':noff,'start':start,'end':f.tell()})
assert not f.read()
raw=np.concatenate([x['raw'] for x in draws]);old=np.concatenate([x['p'] for x in draws]);coef=[];offset=[]
for axis in range(3):
 a,b=np.linalg.lstsq(np.c_[raw[:,axis],np.ones(len(raw))],old[:,axis],rcond=None)[0];coef.append(a);offset.append(b)
coef=np.array(coef);offset=np.array(offset);err=float(np.abs(raw*coef+offset-old).max());assert err<2e-6,(coef,offset,err)
# The glTF export maps Blender (x,y,z) to (x,z,-y). The FAM export additionally mirrors X.
probe=json.loads(args.pivots.read_text());basis=np.array([[1,0,0],[0,0,1],[0,-1,0]],float);bone={x['bone']:np.array(x['head']) for x in probe['bones']};out=bytearray(data);changed=[];nonwing=0
for d in draws:
 name=d['name']
 if not name.startswith('f14 wing'):nonwing+=1;continue
 suffix=0 if name=='f14 wing' else int(name.rsplit('.',1)[1]);left=suffix<=8;key='Bone' if left else 'Bone.001';angle=math.radians(52 if left else -52);rz=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
 # Compose the existing source bone rotation into the unchanged FAM coordinate transform.
 A=np.diag(coef)@basis;rotation=A@rz@np.linalg.inv(A);pivot=(basis@bone[key])*coef+offset
 pp=(d['p'].astype(float)-pivot)@rotation.T+pivot;nn=d['n'].astype(float)@rotation.T
 for k,arr in [('posoff',pp),('noff',nn)]:b=arr.astype('<f4').tobytes();out[d[k]:d[k]+len(b)]=b
 changed.append(name)
assert changed and all(bytes(out[d['start']:d['end']])==data[d['start']:d['end']] for d in draws if not d['name'].startswith('f14 wing'))
# Every header, UV, index and material segment is byte-identical, including landing gear.
allowed=np.zeros(len(data),dtype=bool)
for d in draws:
 if d['name'].startswith('f14 wing'):allowed[d['posoff']:d['noff']+d['n'].nbytes]=True
assert np.all(np.frombuffer(bytes(out),dtype=np.uint8)[~allowed]==np.frombuffer(data,dtype=np.uint8)[~allowed])
target=r/'m_f14_cg.fam';target.parent.mkdir(exist_ok=True);target.write_bytes(out)
validation={'source_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'source_alignment_max_error':err,'wing_draws_changed':len(changed),'wing_objects':sorted(set(changed)),'other_draws_byte_identical':nonwing,'source_bytes':len(data),'output_bytes':len(out),'uv_material_indices_byte_identical':True,'landing_gear_and_body_byte_identical':True,'source_rig_pivots':{k:list(v) for k,v in bone.items()},'wing_rotation_degrees_from_source':[52,-52],'native_render_verified':False};(r/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))
