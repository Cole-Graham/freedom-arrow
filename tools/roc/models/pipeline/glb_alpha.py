"""glb_alpha.py IN.glb OUT.glb MAT=MODE[:CUTOFF] ...: set a GLB material's alphaMode (OPAQUE / MASK / BLEND). 26 Nov: AH-64E and F-CK-1 hulls
came out BLEND only because their colour maps carry an alpha channel; a solid hull must be OPAQUE (or MASK for small cut-outs)."""
import sys,json,struct
src,dst,*specs=sys.argv[1:];d=open(src,'rb').read()
n=struct.unpack_from('<I',d,12)[0];j=json.loads(d[20:20+n]);rest=d[20+n:]
for s in specs:
    name,mode=s.split('=');cut=None
    if ':' in mode:mode,cut=mode.split(':')
    hit=[m for m in j['materials'] if m.get('name')==name];assert hit,name
    for m in hit:
        m['alphaMode']=mode
        if mode=='MASK':m['alphaCutoff']=float(cut or .5)
        else:m.pop('alphaCutoff',None)
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
out=b'glTF'+struct.pack('<II',2,12+8+len(js)+len(rest))+struct.pack('<I',len(js))+b'JSON'+js+rest
open(dst,'wb').write(out);print('ALPHA',[(m.get('name'),m.get('alphaMode')) for m in j['materials']])
