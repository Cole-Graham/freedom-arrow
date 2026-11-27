"""Antelope cab door windows (Shawn 27 Nov 14:4x in game: "Materials of glass on both side are incorrect"): the seller's cab has no door-window
glass; the side windows are body faces painted with camo. Body (tex1) faces on the cab sides whose centre lies in the window opening
(belt line 1.35 m to roof line 1.75 m, from the door frame at z 1.17 m forward to 4 cm behind the windscreen pillar) move to their own
untextured sub-mesh in the same dark tinted glass as the TK-III cab (0.10, 0.12, 0.13, opacity 0.80). All four .fam files; originals in
veh/x/antelope/pre-windows/. usage: python antelope_windows.py   (pla-division venv)"""
import sys,os,json,struct,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';B=D+'/../x/antelope/pre-windows';os.makedirs(B,exist_ok=True)
GLASS=(0.10,0.12,0.13,0.80);K='|'+','.join('%.4f'%x for x in GLASS)
zf=lambda y:2.12-(y-1.33)*(2.12-1.83)/(1.75-1.33)
inwin=lambda Q:(Q[...,1]>1.35)&(Q[...,1]<1.75)&(Q[...,2]>1.17)&(Q[...,2]<zf(Q[...,1])-0.04)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for st in ('m_roc_antelope_static','m_roc_antelope_lo_static','m_roc_antelope_lo_static_l1','m_roc_antelope_lo_static_l2'):
    for ext in ('.fam','.mat.json'):
        if not os.path.exists(f'{B}/{st}{ext}'):shutil.copy(f'{D}/{st}{ext}',f'{B}/{st}{ext}')
    parts=read_fam(f'{B}/{st}.fam');n=0
    for bone,ss in parts:
        add=[]
        for x in ss:
            if not x['tex'].endswith('_tex1.png'):continue
            P=np.array(x['pos'],np.float32).reshape(-1,3);T=np.array(x['idx']).reshape(-1,3);V=P[T]
            fn=np.cross(V[:,1]-V[:,0],V[:,2]-V[:,0]);fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-12
            m=inwin(V.mean(1))&(np.abs(fn[:,0])>0.8)
            if not m.any():continue
            used=np.unique(T[m]);remap={int(v):i for i,v in enumerate(used)}
            N=np.array(x['nrm'],np.float32).reshape(-1,3);U=np.array(x['uv'],np.float32).reshape(-1,2)
            add.append(dict(tex='',col=GLASS,pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U[used].ravel().tolist(),idx=[remap[int(v)] for v in T[m].ravel()]))
            x['idx']=T[~m].ravel().tolist();n+=int(m.sum())
        ss.extend(add)
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{D}/{st}.fam','wb').write(b''.join(o))
    mj=json.load(open(f'{B}/{st}.mat.json'));mj[K]={'metallic':0.3,'smoothness':0.95,'alpha':'BLEND','cutoff':0.5,'emissive':[0,0,0],'unlit':False}
    json.dump(mj,open(f'{D}/{st}.mat.json','w'),indent=1);print(st,'window faces moved to glass',n)
