"""Truck cab glass (Shawn 27 Nov 18:3x, HF-IIE and Land Sword II: "The glass is still not good, use the one of Kung Feng VI"): all three already
borrow the 9K51 Grad glass (cockpitDonor RU_BM_21_Grad_glass). That material has no colour map, only the soap-film iridescence map
(Soap_T), so the window UVs decide what shows: the seller UVs (scattered atlas islands over 0.8 x 0.9 of the sheet) drew swirling bands
like a picture on the glass. The Grad's own windscreen is a plain projection (u 0.09-0.68, v 0.82-0.95 for ~2.2 m, about 0.27 UV per metre).
Here every donor-glass triangle gets a planar projection on its main axis (front/back windows x-y, side windows z-y, roof x-z) at
0.27 UV per metre from (0.09, 0.82). All four .fam files of the model; originals go to veh/x/<slug>/pre-glassuv/.
usage: python glass_planar_uv.py SLUG"""
import sys,os,json,struct,shutil,glob
import numpy as np
T=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,T);from famread import read_fam
slug=sys.argv[1];M=T+'/../veh/models';BK=f'{T}/../veh/x/{slug}/pre-glassuv';os.makedirs(BK,exist_ok=True)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
def write(path,parts):
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(path,'wb').write(b''.join(o))
K=float(os.environ.get("GLASS_K","0.27"));U0=np.array([float(x) for x in os.environ.get("GLASS_U0","0.09,-0.18").split(",")])   # .fam v = Unity v - 1 (as cm32_kitbash vsub); AH-64 glass: GLASS_K=0.38 GLASS_U0=0.0,-0.86
for f in sorted(glob.glob(f'{M}/m_roc_{slug}_*static*.fam')):
    b=f'{BK}/{os.path.basename(f)}'
    if not os.path.exists(b):shutil.copy(f,b)
    mj=json.load(open(f[:-4]+'.mat.json'));parts=read_fam(b);n=0
    for bone,ss in parts:
        for x in ss:
            if 'cockpitDonor' not in mj.get(x['tex']+'|'+','.join('%.4f'%c for c in x['col']),{}):continue
            P=np.array(x['pos'],np.float64).reshape(-1,3);Tr=np.array(x['idx']).reshape(-1,3);N=np.cross(P[Tr[:,1]]-P[Tr[:,0]],P[Tr[:,2]]-P[Tr[:,0]])
            # split shared vertices so each triangle can take its own projection
            V=P[Tr.ravel()];ax=np.repeat(np.argmax(np.abs(N),1),3);lo=V.min(0)
            uv=np.where(ax[:,None]==2,V[:,[0,1]]-lo[[0,1]],np.where(ax[:,None]==0,V[:,[2,1]]-lo[[2,1]],V[:,[0,2]]-lo[[0,2]]))*K+U0
            nrm=np.array(x['nrm']).reshape(-1,3)[Tr.ravel()]
            x['pos']=V.ravel().tolist();x['nrm']=nrm.ravel().tolist();x['uv']=uv.ravel().tolist();x['idx']=list(range(len(V)));n+=len(Tr)
    write(f,parts);print(os.path.basename(f),'glass triangles re-projected',n)
