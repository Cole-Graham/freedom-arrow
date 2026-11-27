"""F-16V Arsenal landing gear (Shawn 27 Nov 15:0x: "No landing gear, transplant the one from F-16A to it"). The F-16V file came without gear
(it lay on its belly at y 0). Takes the F-16A Arsenal model's gear pieces (sub-meshes entirely below 1.3 m, at the main-gear bay
z -2.1..-1.0 m or the nose gear z 1.8..2.95 m; both airframes are scaled to the same 15.06 m length), lifts the F-16V so its belly at the
main-gear bay matches the F-16A's, and adds the pieces with the F-16A textures and materials. Arsenal file only: in battle the aircraft
flies gear-up. Original in veh/x/f16v/pre-gear/. usage: python f16v_gear.py"""
import sys,os,json,struct,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';B=D+'/../x/f16v/pre-gear';os.makedirs(B,exist_ok=True)
st='m_roc_f16v_static'
for ext in ('.fam','.mat.json'):
    if not os.path.exists(f'{B}/{st}{ext}'):shutil.copy(f'{D}/{st}{ext}',f'{B}/{st}{ext}')
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
A=[x for b,q in read_fam(f'{D}/m_roc_f16a_static.fam') for x in q];V=read_fam(f'{B}/{st}.fam')
PA=np.concatenate([np.array(x['pos']).reshape(-1,3) for x in A]);PV=np.concatenate([np.array(x['pos']).reshape(-1,3) for b,q in V for x in q])
def belly(P,z0,z1):m=(P[:,2]>z0)&(P[:,2]<z1)&(np.abs(P[:,0])<0.4);return float(np.percentile(P[m,1],2))
gear=[];
for x in A:
    P=np.array(x['pos']).reshape(-1,3)
    if P[:,1].max()<1.3 and ((P[:,2].min()>-2.1 and P[:,2].max()<-1.0) or (P[:,2].min()>1.8 and P[:,2].max()<2.95)):gear.append(x)
body=[x for x in A if x not in gear];PB=np.concatenate([np.array(x['pos']).reshape(-1,3) for x in body])
dy=belly(PB,-1.0,0.5)-belly(PV,-1.0,0.5)
print('gear pieces',len(gear),'triangles',sum(len(x['idx'])//3 for x in gear),'lift F-16V by %.3f m'%dy)
for b,q in V:
    for x in q:P=np.array(x['pos'],np.float32).reshape(-1,3);P[:,1]+=dy;x['pos']=P.ravel().tolist()
V[0][1].extend(gear)
o=[b'FAM1',struct.pack('<i',len(V))]
for bone,ss in V:
    o+=[S(bone),struct.pack('<i',len(ss))]
    for x in ss:
        nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
open(f'{D}/{st}.fam','wb').write(b''.join(o))
mj=json.load(open(f'{B}/{st}.mat.json'));ma=json.load(open(f'{D}/m_roc_f16a_static.mat.json'))
for x in gear:
    k=x['tex']+'|'+','.join('%.4f'%c for c in x['col']);mj[k]=ma[k]
json.dump(mj,open(f'{D}/{st}.mat.json','w'),indent=1)
P=np.concatenate([np.array(x['pos']).reshape(-1,3) for b,q in V for x in q]);print('new F-16V Arsenal model y %.2f..%.2f'%(P[:,1].min(),P[:,1].max()))
