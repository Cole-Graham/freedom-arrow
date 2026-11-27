"""F-CK-1 windscreen (Shawn 27 Nov 15:0x, in game: "Make it glass"): canopy_split.py moved only the canopy faces whose colour-map alpha is
below 0.5; the front windscreen panel stayed body (tex1). Body faces above the cockpit sill (|x| < 0.42 m, y > 1.76 m) from z 2.88 m forward
(the canopy glass ends at the windscreen frame) become a new sub-mesh with the canopy glass key (0.85, 0.90, 0.95, 0.15), which the
.mat.json already maps to the vanilla F-16 glass. All four .fam files; originals in veh/x/fck1/pre-windscreen/."""
import sys,os,struct,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';B=D+'/../x/fck1/pre-windscreen';os.makedirs(B,exist_ok=True)
GL=(0.85,0.9,0.95,0.15)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for st in ('m_roc_fck1_static','m_roc_fck1_lo_static','m_roc_fck1_lo_static_l1','m_roc_fck1_lo_static_l2'):
    if not os.path.exists(f'{B}/{st}.fam'):shutil.copy(f'{D}/{st}.fam',f'{B}/{st}.fam')
    parts=read_fam(f'{B}/{st}.fam');n=0
    for bone,ss in parts:
        add=[]
        for x in ss:
            if not x['tex'].endswith('_tex1.png') or len(x['idx'])//3>5000:continue   # the canopy frame piece only, never the fuselage skin
            P=np.array(x['pos'],np.float32).reshape(-1,3);T=np.array(x['idx']).reshape(-1,3);C=P[T].mean(1)
            m=(np.abs(C[:,0])<0.42)&(C[:,1]>1.76)&(C[:,2]>2.88)&(C[:,2]<3.1)
            if not m.any():continue
            used=np.unique(T[m]);rm=-np.ones(len(P),int);rm[used]=np.arange(len(used))
            N=np.array(x['nrm'],np.float32).reshape(-1,3);U=np.array(x['uv'],np.float32).reshape(-1,2)
            add.append(dict(tex='',col=GL,pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U[used].ravel().tolist(),idx=rm[T[m]].ravel().tolist()))
            x['idx']=T[~m].ravel().tolist();n+=int(m.sum())
        ss.extend(add)
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{D}/{st}.fam','wb').write(b''.join(o));print(st,'windscreen faces -> glass',n)
