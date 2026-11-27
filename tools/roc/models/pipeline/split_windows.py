"""Cab windows that the seller painted into the body texture become real glass: textured faces whose centre lies in a window box and whose
face normal points out of that window move to one untextured sub-mesh with colour key GLASS, mapped in the .mat.json to the vanilla
9K51 Grad cab glass (FAModels cockpitDonor). Shawn 27 Nov 15:0x (Land Sword II: "Fix all the material of glass").
usage: python split_windows.py SLUG BOXES.json   BOXES = [{"x":[a,b],"y":[a,b],"z":[a,b],"n":"x"|"z"}, ...] (game metres; "n": the axis the
window faces, either sign). All four .fam files; originals in veh/x/<slug>/pre-windows/."""
import sys,os,json,struct,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
slug=sys.argv[1];BOX=json.load(open(sys.argv[2]))
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';B=D+f'/../x/{slug}/pre-windows';os.makedirs(B,exist_ok=True)
GLASS=(0.10,0.12,0.13,0.80);K='|'+','.join('%.4f'%c for c in GLASS)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for st in (f'm_roc_{slug}_static',f'm_roc_{slug}_lo_static',f'm_roc_{slug}_lo_static_l1',f'm_roc_{slug}_lo_static_l2'):
    for ext in ('.fam','.mat.json'):
        if os.path.exists(f'{D}/{st}{ext}') and not os.path.exists(f'{B}/{st}{ext}'):shutil.copy(f'{D}/{st}{ext}',f'{B}/{st}{ext}')
    parts=read_fam(f'{B}/{st}.fam');n=0
    for bone,ss in parts:
        add=[]
        for x in ss:
            if not x['tex']:continue
            P=np.array(x['pos'],np.float32).reshape(-1,3);T=np.array(x['idx']).reshape(-1,3);V=P[T];C=V.mean(1)
            fn=np.cross(V[:,1]-V[:,0],V[:,2]-V[:,0]);fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-12
            m=np.zeros(len(T),bool)
            for b in BOX:
                ax={'x':0,'z':2}[b['n']]
                m|=(C[:,0]>=b['x'][0])&(C[:,0]<=b['x'][1])&(C[:,1]>=b['y'][0])&(C[:,1]<=b['y'][1])&(C[:,2]>=b['z'][0])&(C[:,2]<=b['z'][1])&(np.abs(fn[:,ax])>0.7)
            if not m.any():continue
            used=np.unique(T[m]);rm=-np.ones(len(P),int);rm[used]=np.arange(len(used))
            N=np.array(x['nrm'],np.float32).reshape(-1,3);U=np.array(x['uv'],np.float32).reshape(-1,2)
            add.append(dict(tex='',col=GLASS,pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U[used].ravel().tolist(),idx=rm[T[m]].ravel().tolist()))
            x['idx']=T[~m].ravel().tolist();n+=int(m.sum())
        ss.extend(add)
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{D}/{st}.fam','wb').write(b''.join(o))
    mp=f'{B}/{st}.mat.json';mj=json.load(open(mp)) if os.path.exists(mp) else {}
    mj[K]={'cockpitDonor':'RU_BM_21_Grad_glass','fallback':{'metallic':0.3,'smoothness':0.95,'alpha':'BLEND','cutoff':0.5,'emissive':[0,0,0],'unlit':False}}
    json.dump(mj,open(f'{D}/{st}.mat.json','w'),indent=1);print(st,'window faces -> glass',n)
