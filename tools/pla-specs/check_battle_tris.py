"""Battle triangle limit (Osama 14 Nov 2026 16:28 PST: "in battle we want a triangle limit"). Every FAModels entry's battle model
(its 'battle' file, or 'file' when there is none) must be at most LIMIT triangles. usage: check_battle_tris.py PACKAGE.bamod [LIMIT]"""
import json,struct,sys,zipfile
LIMIT=int(sys.argv[2]) if len(sys.argv)>2 else 60000
def tris(d):
    o=4;i32=lambda:struct.unpack_from('<i',d,o)[0]
    assert d[:4]==b'FAM1';n=0
    np_=struct.unpack_from('<i',d,o)[0];o+=4
    for _ in range(np_):
        L=struct.unpack_from('<i',d,o)[0];o+=4+L;ns=struct.unpack_from('<i',d,o)[0];o+=4
        for _ in range(ns):
            L=struct.unpack_from('<i',d,o)[0];o+=4+L+16;nv=struct.unpack_from('<i',d,o)[0];o+=4+4*8*nv;ni=struct.unpack_from('<i',d,o)[0];o+=4+4*ni;n+=ni//3
    assert o==len(d);return n
# 0.9.0-dev.4 (Osama 14 Nov 18:25 PST): meshes still being redone, named in BA_BATTLE_TRIS_PENDING, are reported but allowed.
import os;PENDING=set(filter(None,os.environ.get('BA_BATTLE_TRIS_PENDING','').split(',')))
z=zipfile.ZipFile(sys.argv[1]);m=json.loads(z.read('UserData/FAModels/models.json'));N=set(z.namelist());seen={};bad=[]
for k,v in m.items():
    f=v.get('battle') or v.get('file')
    if not f:continue
    if f not in seen:seen[f]=tris(z.read('UserData/FAModels/'+f)) if 'UserData/FAModels/'+f in N else None
    if seen[f] is None or seen[f]>LIMIT and f not in PENDING:bad.append((k,f,seen[f]))
print(json.dumps({'limit':LIMIT,'battle_models':len(seen),'max':max(v for v in seen.values() if v is not None),'over':bad,'pending_allowed':sorted(f for f in set(seen) if f in PENDING and (seen[f] or 0)>LIMIT)},ensure_ascii=False))
sys.exit(1 if bad else 0)
