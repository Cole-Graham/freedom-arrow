"""Create editable side-profile vectors from existing weapon meshes, without editing pixels."""
import argparse,hashlib,io,json,struct
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('models',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);receipt=[]
def num(f):return struct.unpack('<i',f.read(4))[0]
def string(f):return f.read(num(f)).decode()
for entry in json.loads((a.models/'plan.json').read_text()):
    name=entry['name'];raw=(a.models/entry['file']).read_bytes();f=io.BytesIO(raw);assert f.read(4)==b'FAM1';verts=[];faces=[]
    for _ in range(num(f)):
        string(f)
        for _ in range(num(f)):
            string(f);f.read(16);nv=num(f);ps=struct.unpack('<'+'f'*nv*3,f.read(nv*12));f.seek(nv*20,1);ni=num(f);indices=struct.unpack('<'+'i'*ni,f.read(ni*4));base=len(verts);verts.extend((ps[i+2],-ps[i+1]) for i in range(0,len(ps),3));faces.extend(tuple(base+j for j in indices[i:i+3]) for i in range(0,ni,3))
    lo=[min(v[i] for v in verts) for i in (0,1)];hi=[max(v[i] for v in verts) for i in (0,1)];scale=min(228/(hi[0]-lo[0]),132/(hi[1]-lo[1]));ox=(256-(hi[0]-lo[0])*scale)/2;oy=(160-(hi[1]-lo[1])*scale)/2
    points=[((x-lo[0])*scale+ox,(y-lo[1])*scale+oy) for x,y in verts];paths=[]
    for tri in faces:
        v=[points[i] for i in tri];area=(v[1][0]-v[0][0])*(v[2][1]-v[0][1])-(v[2][0]-v[0][0])*(v[1][1]-v[0][1])
        if abs(area)<.002:continue
        if area<0:v.reverse()
        paths.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in v)+'Z')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="160" viewBox="0 0 256 160"><path fill="#fff" fill-rule="nonzero" d="'+''.join(paths)+'"/></svg>\n';target=a.output/('FA_PLA_WP_'+name+'.svg');target.write_text(svg)
    receipt.append({'profile':name,'source_file':entry['file'],'source_sha256':hashlib.sha256(raw).hexdigest(),'projection':'Unity +Z right, +Y up; all projected triangles have consistent winding','triangles':len(paths),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest()})
(a.output/'model-projection.json').write_text(json.dumps(receipt,indent=2)+'\n');print([(x['profile'],x['triangles']) for x in receipt])
