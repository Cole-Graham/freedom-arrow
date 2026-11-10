"""Rebuild angle-limited, area-weighted normals without changing rendered geometry or UVs."""
from pathlib import Path
import struct,io,json,argparse
import numpy as np
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('models',nargs='+');args=parser.parse_args();src=args.source;r=args.output;r.mkdir(parents=True,exist_ok=True);stats=[]
def run(name):
 data=(src/(name+'.fam')).read_bytes();f=io.BytesIO(data);out=io.BytesIO()
 def n():return struct.unpack('<i',f.read(4))[0]
 def s():return f.read(n()).decode()
 def wn(x):out.write(struct.pack('<i',x))
 def ws(x):b=x.encode();wn(len(b));out.write(b)
 assert f.read(4)==b'FAM1';out.write(b'FAM1');parts=n();wn(parts);before=[];after=[];nv0=nv1=0;nf=0
 for _ in range(parts):
  ws(s());draws=n();wn(draws)
  for _ in range(draws):
   ws(s());out.write(f.read(16));nv=n();p=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();old=np.frombuffer(f.read(nv*12),'<f4').reshape(-1,3).copy();uv=np.frombuffer(f.read(nv*8),'<f4').reshape(-1,2).copy();ni=n();tri=np.frombuffer(f.read(ni*4),'<i4').reshape(-1,3).copy();cross=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);area=np.linalg.norm(cross,axis=1);normal=cross/np.maximum(area[:,None],1e-20)
   # Group coincident vertices to keep normal direction continuous across UV seams.
   key=np.round(p,5);_,group=np.unique(key,axis=0,return_inverse=True);adj=[set() for _ in range(int(group.max())+1)]
   for fi,inds in enumerate(tri):
    for vi in inds:adj[group[vi]].add(fi)
   newp=[];newn=[];newuv=[];newtri=[];cache={};cos=np.cos(np.deg2rad(30));big=area>=np.quantile(area[area>1e-10],.95) if np.any(area>1e-10) else area>0
   for fi,inds in enumerate(tri):
    idx=[]
    for vi in inds:
     faces=np.array(sorted(adj[group[vi]]),dtype=int);keep=faces[(normal[faces]@normal[fi])>=cos];weighted=cross[keep].sum(axis=0);ln=np.linalg.norm(weighted);nn=weighted/ln if ln>1e-12 else (old[vi] if np.linalg.norm(old[vi])>0 else normal[fi]);k=(int(vi),*np.round(nn,6))
     if k not in cache:cache[k]=len(newp);newp.append(p[vi]);newn.append(nn);newuv.append(uv[vi])
     idx.append(cache[k])
     if big[fi]:
      oldn=old[vi]/max(np.linalg.norm(old[vi]),1e-20);before.append(float(np.degrees(np.arccos(np.clip(oldn@normal[fi],-1,1)))));after.append(float(np.degrees(np.arccos(np.clip(nn@normal[fi],-1,1)))))
    newtri.append(idx)
   pp=np.asarray(newp,dtype='<f4');nn=np.asarray(newn,dtype='<f4');uu=np.asarray(newuv,dtype='<f4');ii=np.asarray(newtri,dtype='<i4');assert np.isfinite(nn).all()
   assert np.array_equal(pp[ii],p[tri]) and np.array_equal(uu[ii],uv[tri]),'surface geometry or UVs changed'
   wn(len(pp));out.write(pp.tobytes());out.write(nn.tobytes());out.write(uu.tobytes());wn(ni);out.write(ii.tobytes());nv0+=nv;nv1+=len(pp);nf+=len(tri)
 assert not f.read();dest=r/(name+'.fam');dest.write_bytes(out.getvalue());stats.append({'model':name,'parts_preserved':parts,'vertices_before':nv0,'vertices_after':nv1,'triangles':nf,'position_and_uv_per_corner_identical':True,'large_face_normal_error_mean_before':float(np.mean(before)),'large_face_normal_error_mean_after':float(np.mean(after)),'large_face_normal_error_p95_before':float(np.percentile(before,95)),'large_face_normal_error_p95_after':float(np.percentile(after,95))})
for name in args.models:run(name)
(r/'normal-validation.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))
