"""Union the real FAM mesh triangles into tight, right-facing side-profile vectors."""
import argparse,hashlib,io,json,struct,math
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
p=argparse.ArgumentParser(description=__doc__);p.add_argument('models',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);receipt=[]
def num(f):return struct.unpack('<i',f.read(4))[0]
def string(f):return f.read(num(f)).decode()
for entry in json.loads((a.models/'plan.json').read_text()):
 name=entry['name'];raw=(a.models/entry['file']).read_bytes();f=io.BytesIO(raw);assert f.read(4)==b'FAM1';verts=[];faces=[]
 for _ in range(num(f)):
  string(f)
  for _ in range(num(f)):
   string(f);f.read(16);nv=num(f);ps=struct.unpack('<'+'f'*nv*3,f.read(nv*12));f.seek(nv*20,1);ni=num(f);indices=struct.unpack('<'+'i'*ni,f.read(ni*4));base=len(verts);verts.extend((ps[i+2],-ps[i+1]) for i in range(0,len(ps),3));faces.extend(tuple(base+j for j in indices[i:i+3]) for i in range(0,ni,3))
 lo=[min(v[i] for v in verts) for i in (0,1)];hi=[max(v[i] for v in verts) for i in (0,1)];scale=228/(hi[0]-lo[0]);height=math.ceil((hi[1]-lo[1])*scale+4);points=[((x-lo[0])*scale+2,(y-lo[1])*scale+2) for x,y in verts]
 triangles=[Polygon([points[i] for i in face]) for face in faces];triangles=[t for t in triangles if t.area>.0001]
 shape=unary_union(triangles).simplify(.035,preserve_topology=True);polys=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape];paths=[]
 for poly in polys:
  for ring in [poly.exterior,*poly.interiors]:paths.append('M'+'L'.join(f'{x:.3f},{y:.3f}' for x,y in ring.coords)+'Z')
 d=''.join(paths);hashes={}
 for outline in (False,True):
  suffix='_OUTLINE' if outline else '';fill='#e7f7e4';stroke=' stroke="#26332d" stroke-width="1.15" stroke-linejoin="round" paint-order="stroke fill"' if outline else ''
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="232" height="{height}" viewBox="0 0 232 {height}"><path fill="{fill}" fill-rule="evenodd"{stroke} d="{d}"/></svg>\n'
  target=a.output/('FA_PLA_WP_'+name+suffix+'.svg');target.write_text(svg);hashes[suffix or 'plain']=hashlib.sha256(svg.encode()).hexdigest()
 receipt.append({'profile':name,'source_file':entry['file'],'source_sha256':hashlib.sha256(raw).hexdigest(),'projection':'Unity +Z faces right; +Y up; union of all side-projected mesh triangles, holes retained','triangles':len(triangles),'svg_sha256':hashes,'width':232,'height':height})
(a.output/'model-projection.json').write_text(json.dumps(receipt,indent=2)+'\n');print([(x['profile'],x['triangles'],x['height']) for x in receipt])
