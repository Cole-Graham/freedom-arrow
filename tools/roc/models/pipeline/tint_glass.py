"""Dark tinted cab glass (Shawn 26 Nov 21:5x "adjust the glass material to dark tinted glass ... rather than a solid black one"). FAModels takes a
glass part's opacity from its colour key, so the cut-out window parts (canopy_split.py colour 0.85,0.9,0.95,0.15) get a new colour in the .fam
files themselves, and the .mat.json entry follows. usage: python tint_glass.py SLUG R G B A   (pla-division venv; edits models/ in place)"""
import sys,os,json,struct
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
s=sys.argv[1];NEW=tuple(float(x) for x in sys.argv[2:6]);OLD=(0.85,0.9,0.95,0.15);D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models'
K=lambda c:'|'+','.join('%.4f'%x for x in c)
for st in (f'm_roc_{s}_static',f'm_roc_{s}_lo_static',f'm_roc_{s}_lo_static_l1',f'm_roc_{s}_lo_static_l2'):
    parts=read_fam(f'{D}/{st}.fam');n=0
    for b,ss in parts:
        for x in ss:
            if not x['tex'] and all(abs(a-c)<1e-3 for a,c in zip(x['col'],OLD)):x['col']=NEW;n+=1
    def S(b):b=b.encode();return struct.pack('<i',len(b))+b
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{D}/{st}.fam','wb').write(b''.join(o))
    mp=f'{D}/{st}.mat.json'
    if os.path.exists(mp):
        mj=json.load(open(mp));mj.pop(K(OLD),None);mj[K(NEW)]={'metallic':0.3,'smoothness':0.95,'alpha':'BLEND','cutoff':0.5,'emissive':[0,0,0],'unlit':False};json.dump(mj,open(mp,'w'),indent=1)
    print(st,'glass parts',n)
