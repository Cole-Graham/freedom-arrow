"""F-CK-1 windscreen, second pass (Shawn 27 Nov 18:3x, in game: "Change this to glass material"): fck1_windscreen.py only searched the small
sub-meshes, but most of the front windscreen sits in the big body sub-mesh (tex1, ~19k triangles), painted grey-green in the colour map.
Body triangles above the sill (|x| < 0.4 m, y > 1.8 m, z 2.95-4.0 m) whose colour-map sample is the green windscreen paint (G - R > 4)
move to the canopy glass key (0.85, 0.90, 0.95, 0.15) = vanilla F-16 glass. All four .fam files; originals in veh/x/fck1/pre-windscreen2/."""
import sys,os,struct,shutil
import numpy as np
from PIL import Image
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';B=D+'/../x/fck1/pre-windscreen2';os.makedirs(B,exist_ok=True)
GL=(0.85,0.9,0.95,0.15)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
def write(path,parts):
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(path,'wb').write(b''.join(o))
def split(x,m):
    P=np.array(x['pos']).reshape(-1,3);N=np.array(x['nrm']).reshape(-1,3);U=np.array(x['uv']).reshape(-1,2);T=np.array(x['idx']).reshape(-1,3);out=[]
    for keep in (~m,m):
        used=np.unique(T[keep]);rm=-np.ones(len(P),int);rm[used]=np.arange(len(used))
        out.append(dict(tex=x['tex'],col=x['col'],pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U[used].ravel().tolist(),idx=rm[T[keep]].ravel().tolist()))
    return out
for st in ('m_roc_fck1_static','m_roc_fck1_lo_static','m_roc_fck1_lo_static_l1','m_roc_fck1_lo_static_l2'):
    if not os.path.exists(f'{B}/{st}.fam'):shutil.copy(f'{D}/{st}.fam',f'{B}/{st}.fam')
    parts=read_fam(f'{B}/{st}.fam');n=0;new=[]
    for bone,ss in parts:
        keep=[]
        for x in ss:
            if not x['tex'].endswith('_tex1.png'):keep.append(x);continue
            P=np.array(x['pos']).reshape(-1,3);U=np.array(x['uv']).reshape(-1,2);T=np.array(x['idx']).reshape(-1,3);c=P[T].mean(1)
            m=(np.abs(c[:,0])<0.4)&(c[:,1]>1.8)&(c[:,2]>2.95)&(c[:,2]<4.0)
            if m.any():
                a=np.asarray(Image.open(f'{D}/{x["tex"]}').convert('RGB')).astype(int);H,W=a.shape[:2];uv=U[T].mean(1)
                px=a[np.clip(((-uv[:,1])%1*H).astype(int),0,H-1),np.clip((uv[:,0]%1*W).astype(int),0,W-1)]
                m&=(px[:,1]-px[:,0])>4
            if not m.any():keep.append(x);continue
            body,gl=split(x,m);gl['col']=GL;keep+=[body,gl];n+=int(m.sum())
        new.append((bone,keep))
    write(f'{D}/{st}.fam',new);print(st,'windscreen triangles moved to glass',n)
