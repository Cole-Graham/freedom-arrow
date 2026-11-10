"""Pose original J50 landing-gear geometry for the armory; retain all topology, UVs and texture bindings."""
from pathlib import Path
import sys,io,struct,re,json,hashlib,numpy as np,argparse,importlib.util
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--glb',type=Path,required=True);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--converter',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
sp=importlib.util.spec_from_file_location('famconv',args.converter);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);acc,node_matrix=mod.acc,mod.node_matrix
from pygltflib import GLTF2
r=args.out;r.mkdir(parents=True,exist_ok=True);g=GLTF2().load(str(args.glb));blob=g.binary_blob();draws=[];world={}
def walk(i,m):
 n=g.nodes[i];m=m@node_matrix(n);world[n.name]=m
 if n.mesh is not None:
  for p in g.meshes[n.mesh].primitives:
   if p.mode not in (None,4):continue
   points=(np.c_[acc(g,blob,p.attributes.POSITION),np.ones(g.accessors[p.attributes.POSITION].count)]@m.T)[:,:3];draws.append((n.name,points))
 for j in n.children or []:walk(j,m)
for i in g.scenes[g.scene or 0].nodes:walk(i,np.eye(4))
allp=np.concatenate([p for n,p in draws]);lo,hi=allp.min(0),allp.max(0);scale=22.604/(hi[2]-lo[2]);center=np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2]);xf={};gear=[]
def rx(deg):
 a=np.deg2rad(deg);c,s=np.cos(a),np.sin(a);return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rz(deg):
 a=np.deg2rad(deg);c,s=np.cos(a),np.sin(a);return np.array([[c,-s,0],[s,c,0],[0,0,1]])
front=np.array([0,1.997,5.3516564]);xf['F']=(rx(90),front)
for side,sign in [('L',1),('R',-1)]:
 wheel=next(p for n,p in draws if n=='J50_Wheel_'+side);pivot=np.array([sign*2.2259,2.10,-4.32534]);span=wheel.mean(0)-pivot;a=world['J50_Wheel_'+side][:3,1];a=a/np.linalg.norm(a)
 if a[1]<0:a=-a
 b=span-a*np.dot(a,span);b=b/np.linalg.norm(b);old=np.stack([a,b,np.cross(a,b)],axis=1);ta=np.array([sign,0,0]);tb=np.array([0,-1,0]);target=np.stack([ta,tb,np.cross(ta,tb)],axis=1);R=target@old.T;assert np.allclose(R.T@R,np.eye(3)) and np.linalg.det(R)>.999;xf[side]=(R,pivot)
posed=[]
for name,P in draws:
 hit=re.match(r'J50_(?:LandGear|Wheel)_([FLR])(?:_|$)',name)
 door=re.match(r'J50_landgearGate_(F_[LR]|[LR]_[BF])(?:_|$)',name)
 R=np.eye(3);pivot=np.zeros(3)
 if hit:R,pivot=xf[hit[1]]
 elif door:
  tag=door[1];root='J50_landgearGate_'+tag;pivot=world[root][:3,3];sign=1 if tag.endswith('_L') or tag.startswith('L_') else -1;R=rz(sign*(85 if tag.startswith('F_') else 75))
 if hit or door:gear.append(name)
 posed.append((name,(P-pivot)@R.T+pivot,R))
newmin=np.concatenate([P for n,P,R in posed]).min(0)[1];newcenter=center.copy();newcenter[1]=newmin
oldbytes=args.model.read_bytes();assert hashlib.sha256(oldbytes).hexdigest()=='e0731c8d53e6a46c62b6c73119c210187b4a46cbf75d6e58c2aa2fdcc1e4e462'
(r/'before.fam').write_bytes(oldbytes);f=io.BytesIO(oldbytes);out=io.BytesIO()
def num():return struct.unpack('<i',f.read(4))[0]
def rawstr():
 n=num();b=f.read(n);return struct.pack('<i',n)+b,b.decode()
assert f.read(4)==b'FAM1';out.write(b'FAM1');np_=num();out.write(struct.pack('<i',np_));index=0;maxerr=0;mirror=np.diag([-1,1,1]);metrics=[]
for _ in range(np_):
 b,s=rawstr();out.write(b);ns=num();out.write(struct.pack('<i',ns))
 for _ in range(ns):
  b,s=rawstr();out.write(b);out.write(f.read(16));nv=num();out.write(struct.pack('<i',nv));P=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();N=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();uv=f.read(nv*8);ni=num();inds=f.read(ni*4);name,src=draws[index];name2,new,R=posed[index];assert name==name2 and len(src)==nv
  # Converter mirrors X before its bounds normalization.
  mirrored=src@mirror;c=center@mirror;expected=(mirrored-c)*scale;maxerr=max(maxerr,float(np.max(abs(expected-P))));assert np.max(abs(expected-P))<4e-5,(name,float(np.max(abs(expected-P))))
  final=(new@mirror-newcenter@mirror)*scale;nr=N@(mirror@R@mirror).T
  out.write(np.asarray(final,dtype='<f4').tobytes());out.write(np.asarray(nr,dtype='<f4').tobytes());out.write(uv);out.write(struct.pack('<i',ni));out.write(inds)
  if 'Wheel_' in name:metrics.append({'part':name,'before_min_y':float(P[:,1].min()),'after_min_y':float(final[:,1].min())})
  index+=1
assert not f.read() and index==len(draws)
(r/'m_j50_cg.fam').write_bytes(out.getvalue());result={'source_glb_sha256':hashlib.sha256(args.glb.read_bytes()).hexdigest(),'before_sha256':hashlib.sha256(oldbytes).hexdigest(),'after_sha256':hashlib.sha256(out.getvalue()).hexdigest(),'draws':index,'gear_draws':len(gear),'unchanged_topology_uv_materials':True,'source_to_original_max_error':maxerr,'body_lift':float((center[1]-newcenter[1])*scale),'wheels':metrics,'battle_unchanged':True,'native_verified':False};(r/'pose-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
