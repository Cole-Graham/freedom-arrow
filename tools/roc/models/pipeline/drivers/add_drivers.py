"""Two seated ROC Mech. Riflemen in the cab (Shawn 28 Nov 03:0x, list 7: "Add 2x Drivers to ROC vehicles as shown below: Antelope, Hsiung Feng
IIE-K, Kung Feng VI, Land Sword II, Tien Kung III, Thunderbolt-2000, use the models of ROC Mech. Rifleman"). The stand-ins' own crews are
hidden with the rest of the stand-in, so the cabs were empty. The ROC Infantry body (inf/lod/roc_infantry_N.fas, the vanilla 40-bone soldier
rig) is posed with the vanilla MTV driver's seated pose (seated.npz, seated_pose.py) and baked into the vehicle .fam as two static sub-meshes:
the driver and the co-driver (same pose, other seat). Arsenal model: body LOD1 (7k triangles each); battle model and LOD1: body LOD2 (3k);
far LOD2: none. Seat = hips position in the .fam (from the cab glass and side views, 28 Nov); yaw 180 for the TB2000, whose cab is at -z.
Originals go to veh/x/<slug>/pre-drivers/. usage: python add_drivers.py [SLUG ...]"""
import sys,os,io,json,struct,shutil
import numpy as np
D=os.path.dirname(os.path.abspath(__file__));R=D+'/..';sys.path.insert(0,R+'/tools');from famread import read_fam
M=R+'/veh/models'
# slug: (hips x of the driver (the co-driver mirrors it), hips y, hips z, yaw)
SEATS={'antelope':(0.42,1.00,1.45,0),'hf2e':(0.36,0.66,3.62,0),'kf6':(0.45,1.76,1.07,0),'lsw2':(0.55,2.51,3.85,0),
       'tk3':(0.55,1.81,6.10,0),'tb2000':(0.55,2.31,-4.07,180),
       'mtwv':(0.50,1.71,1.75,0)}   # 28 Nov: MTWV (Navistar cab: windscreen z 2.3-2.7, side windows y 1.9-2.6, half width 1.05)
Z=np.load(D+'/seated.npz');S=Z['S'];NAMES=list(Z['names'])
HIPS=S[NAMES.index('Hips')]   # not a position; the posed hips joint comes from the bind pose below
def read_fas(path):
    f=io.BytesIO(open(path,'rb').read());assert f.read(4)==b'FAS1'
    n=lambda:struct.unpack('<i',f.read(4))[0];s=lambda:f.read(n()).decode()
    bones=[s() for _ in range(n())];parts=[]
    for _ in range(n()):
        mat=s();nv=n();P=np.frombuffer(f.read(nv*64),np.float32).reshape(-1,16).copy();ni=n();I=np.frombuffer(f.read(ni*4),np.int32).copy();parts.append((mat,P,I))
    return bones,parts
def posed(level):
    bones,parts=read_fas(f'{R}/inf/lod/roc_infantry_{level}.fas');remap=np.array([NAMES.index(b) for b in bones])
    out=[]
    for mat,P,I in parts:
        bi=remap[P.view(np.int32)[:,8:12]];bw=P[:,12:16];bw=bw/np.maximum(bw.sum(1,keepdims=True),1e-6)
        V=np.c_[P[:,:3],np.ones(len(P))];Nn=P[:,3:6];pos=np.zeros((len(P),3));nrm=np.zeros((len(P),3))
        for k in range(4):
            Mk=S[bi[:,k]];pos+=bw[:,k:k+1]*np.einsum('nij,nj->ni',Mk,V)[:,:3];nrm+=bw[:,k:k+1]*np.einsum('nij,nj->ni',Mk[:,:3,:3],Nn)
        nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-9;out.append((mat,pos,nrm,P[:,6:8].copy(),I))
    return out
# hips joint in the posed (MTV) space: the vanilla driver's hips bone position
E='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_MTV';HJ=np.array([-0.53,1.83,2.25])
def S_(b):b=b.encode();return struct.pack('<i',len(b))+b
def write(path,V):
    o=[b'FAM1',struct.pack('<i',len(V))]
    for bone,ss in V:
        o+=[S_(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S_(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(path,'wb').write(b''.join(o))
BODY={1:posed(1),2:posed(2)}
MAT={'metallic':1.0,'smoothness':0.0,'alpha':'OPAQUE','cutoff':0.5,'emissive':[0.0,0.0,0.0],'unlit':False}
for slug in (sys.argv[1:] or SEATS):
    x0,y0,z0,yaw=SEATS[slug];BK=f'{R}/veh/x/{slug}/pre-drivers';os.makedirs(BK,exist_ok=True)
    for st,level in ((f'm_roc_{slug}_static',1),(f'm_roc_{slug}_lo_static',2),(f'm_roc_{slug}_lo_static_l1',2),(f'm_roc_{slug}_lo_static_l2',None)):
        if not os.path.exists(f'{M}/{st}.fam'):continue
        for ext in ('.fam','.mat.json'):
            if os.path.exists(f'{M}/{st}{ext}') and not os.path.exists(f'{BK}/{st}{ext}'):shutil.copy(f'{M}/{st}{ext}',f'{BK}/{st}{ext}')
        V=read_fam(f'{BK}/{st}.fam')
        if level:
            c,s_=np.cos(np.radians(yaw)),np.sin(np.radians(yaw));Ry=np.array([[c,0,s_],[0,1,0],[-s_,0,c]])
            for side in (-1,1):          # driver on the vanilla driver's side (x < 0 in the MTV), co-driver mirrored across the cab
                for mat,pos,nrm,uv,I in BODY[level]:
                    p=(pos-HJ)@Ry.T+np.array([side*x0,y0,z0]);n=nrm@Ry.T
                    V[0][1].append({'tex':mat,'col':(1.0,1.0,1.0,1.0),'pos':p.astype(np.float32).ravel().tolist(),'nrm':n.astype(np.float32).ravel().tolist(),'uv':uv.ravel().tolist(),'idx':I.tolist()})
        write(f'{M}/{st}.fam',V)
        mj=f'{M}/{st}.mat.json'
        if level and os.path.exists(mj):
            d=json.load(open(f'{BK}/{st}.mat.json'));d[f'roc_infantry_{level}.png|1.0000,1.0000,1.0000,1.0000']=dict(MAT);json.dump(d,open(mj,'w'),indent=1)
        P=np.concatenate([np.array(x['pos']).reshape(-1,3) for b,q in V for x in q]);print(slug,st,'body LOD',level,'bbox',P.min(0).round(2),P.max(0).round(2))
