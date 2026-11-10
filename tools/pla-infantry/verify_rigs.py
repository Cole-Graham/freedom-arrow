"""Offline validation of FAS1 layouts, weights, indices and configuration coverage."""
from pathlib import Path
import argparse,io,json,struct,math
ap=argparse.ArgumentParser();ap.add_argument('rigs',type=Path);ap.add_argument('payload',type=Path);a=ap.parse_args();configs=json.loads((a.rigs/'configurations.json').read_text());checks=0;triangles=0
for c in configs:
 assert c['unit'] in range(985,1010)
 for level in range(3):
  p=a.payload/f"pla2_{c['key']}_{level}.fas";f=io.BytesIO(p.read_bytes())
  def n():return struct.unpack('<i',f.read(4))[0]
  def s():return f.read(n()).decode()
  assert f.read(4)==b'FAS1' and n()==40;bones=[s() for _ in range(40)];assert len(set(bones))==40;assert n()==1
  tex=s();assert (a.payload/tex).is_file();assert (a.payload/(Path(tex).stem+'_n.png')).is_file();nv=n();assert 0<nv<200000
  for _ in range(nv):
   rec=struct.unpack('<8f4i4f',f.read(64));assert all(math.isfinite(x) for x in rec);assert all(0<=x<40 for x in rec[8:12]);assert all(x>=0 for x in rec[12:]);assert abs(sum(rec[12:])-1)<.001;assert all(-.001<=x<=1.001 for x in rec[6:8]);checks+=1
  ni=n();assert ni%3==0 and ni>0;indices=struct.unpack('<'+'i'*ni,f.read(ni*4));assert all(0<=i<nv for i in indices);assert not f.read();triangles+=ni//3;checks+=1
print(json.dumps({'configurations':len(configs),'skinned_lods':len(configs)*3,'vertex_and_index_checks':checks,'all_lod_triangles':triangles,'positive_weights_normalized':True,'textures_present':True,'native_animation_tested':False}))
