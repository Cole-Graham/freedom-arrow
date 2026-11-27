"""CM-32 rebuild (Shawn 27 Nov 14:4x, in game): "Replace the hull and all wheels (lower body) by the body of CM-34", "Leave these 3 lines and
the box on top of hull tail and attach them to lower body of CM-34", "Replace the model of MK19 by the high quality model from Stryker ICV".
New m_roc_cm32 .fam files (Arsenal + battle + 2 LODs), all in game (Unity) space:
  - CM-34 hull (tex0) and wheels (tex1) sub-meshes, turned 180 deg about Y (the CM-34 .fam faces backwards; its card gets yaw 180 instead),
    still using the CM-34 textures, so the CM-34 Dust / Mosaic paint files apply to them;
  - from the old CM-32: the 3 rear antennas (untextured steel) and the box on the hull tail (its camo texture tex1, Dust/Mosaic files exist),
    lowered/raised so they sit on the CM-34 roof;
  - the vanilla Stryker ICV Mk19 remote weapon station (prefab US_STRYKER_ICV_MK19: the turret_0/weapon_0 part of mesh ICV, plus the Mk19
    gun mesh extracted_01), textures US_STRYKER_1 (green) and mk_19_mk20 (base, mask, normal), placed where the CM-32's own station was.
Old CM-32 files go to veh/x/cm32/v3-pre-kitbash/. usage: python cm32_kitbash.py   (rigging-prep venv: numpy + PIL)"""
import sys,os,json,struct,shutil
import numpy as np
from PIL import Image
T=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,T);from famread import read_fam
M=T+'/../veh/models';BK=T+'/../veh/x/cm32/v3-pre-kitbash';os.makedirs(BK,exist_ok=True)
VX='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_STRYKER_ICV_MK19'
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
def write(path,parts):
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(path,'wb').write(b''.join(o))
def arr(x):return np.array(x['pos'],np.float32).reshape(-1,3)
def sub_of(x,mask):   # the triangles of sub-mesh x whose 3 vertices pass mask (per vertex), re-indexed
    P=arr(x);Tr=np.array(x['idx']).reshape(-1,3);keep=mask[Tr].all(1)
    if not keep.any():return None
    used=np.unique(Tr[keep]);rm=-np.ones(len(P),int);rm[used]=np.arange(len(used))
    N=np.array(x['nrm'],np.float32).reshape(-1,3);U=np.array(x['uv'],np.float32).reshape(-1,2)
    return dict(tex=x['tex'],col=x['col'],pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U[used].ravel().tolist(),idx=rm[Tr[keep]].ravel().tolist())
def shift(x,d):P=arr(x)+np.array(d,np.float32);x['pos']=P.ravel().tolist();return x
def quat_mat(q):
    x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
# ---------- vanilla Stryker ICV Mk19 station (prefab space = game space, metres) ----------
sc=json.load(open(VX+'/scene.json'));nodes=sc['nodes']
def world(i):
    m=np.eye(4)
    while i>=0:
        n=nodes[i];L=np.eye(4);L[:3,:3]=quat_mat(n['rot'])*np.array(n['scale']);L[:3,3]=n['pos'];m=L@m;i=n['parent']
    return m
icv=np.load(VX+'/mesh/ICV_22933.npz');bones=nodes[4]['bones']   # bone slots -> node index: 8 body, 11 turret_0, 12 weapon_0
dom=icv['bi'][:,0];own=np.array([bones[b] in (11,12) for b in dom])&(icv['bw'][:,0]>0.5)
# the station's pedestal is weighted to the hull bone: hull vertices within 0.3 m (horizontal) of the turret_0 pivot, 2.26-2.50 m high
piv=(world(11)@np.array([0,0,0,1.0]))[:3];iv=icv['v']
own|=(np.hypot(iv[:,0]-piv[0],iv[:,2]-piv[2])<0.3)&(iv[:,1]>2.26)&(iv[:,1]<2.5)
gun=np.load(VX+'/mesh/extracted_01_20134.npz');W=world(14)
def vsub(v,n,uv,f,keep,tex):
    keepf=keep[f].all(1);used=np.unique(f[keepf]);rm=-np.ones(len(v),int);rm[used]=np.arange(len(used))
    return dict(tex=tex,col=(1.0,1.0,1.0,1.0),pos=v[used].ravel().tolist(),nrm=n[used].ravel().tolist(),uv=np.c_[uv[used,0],uv[used,1]-1].ravel().tolist(),idx=rm[f[keepf]].ravel().tolist())
gv=(np.c_[gun['v'],np.ones(len(gun['v']))]@W.T)[:,:3];gn=gun['n']@W[:3,:3].T
rws_parts=lambda st:[vsub(icv['v'],icv['n'],icv['uv'],icv['f0'],own,f'{st}_rws.png'),vsub(gv,gn,gun['uv'],gun['f0'],np.ones(len(gv),bool),f'{st}_mk19.png')]
RV=np.concatenate([np.array(p['pos']).reshape(-1,3) for p in rws_parts('x')]);rws_min=RV.min(0);rws_c=(RV.min(0)+RV.max(0))/2
# ---------- build each level ----------
LV=[('m_roc_cm32_static','m_roc_cm34_static'),('m_roc_cm32_lo_static','m_roc_cm34_lo_static'),('m_roc_cm32_lo_static_l1','m_roc_cm34_lo_static_l1'),('m_roc_cm32_lo_static_l2','m_roc_cm34_lo_static_l2')]
for st,src34 in LV:
    for ext in ('.fam','.mat.json'):
        if not os.path.exists(f'{BK}/{st}{ext}') and os.path.exists(f'{M}/{st}{ext}'):shutil.copy(f'{M}/{st}{ext}',f'{BK}/{st}{ext}')
    old=[x for b,ss in read_fam(f'{BK}/{st}.fam') for x in ss];c34=[x for b,ss in read_fam(f'{M}/{src34}.fam') for x in ss]
    out=[];mj={}
    mj34=json.load(open(f'{M}/{src34}.mat.json' if os.path.exists(f'{M}/{src34}.mat.json') else f'{M}/m_roc_cm34_lo_static.mat.json'));mjo=json.load(open(f'{BK}/{st}.mat.json' if os.path.exists(f'{BK}/{st}.mat.json') else f'{BK}/m_roc_cm32_lo_static.mat.json'))
    hull=[]
    for x in c34:
        if x['tex'].endswith(('_tex0.png','_tex1.png')):   # hull and wheels, not the turret (tex2)
            P=arr(x)*np.array([-1,1,-1],np.float32);N=np.array(x['nrm'],np.float32).reshape(-1,3)*np.array([-1,1,-1],np.float32)
            y=dict(x);y['pos']=P.ravel().tolist();y['nrm']=N.ravel().tolist();out.append(y);hull.append(P)
            k=x['tex']+'|'+','.join('%.4f'%c for c in x['col']);mj[k]=mj34[k]
    TRI=np.concatenate([arr(x)[np.array(x['idx']).reshape(-1,3)] for x in out])   # hull + wheel triangles, (n,3,3)
    def roof(xz,r=None):   # height of the highest CM-34 hull/wheel surface straight below the point (vertical ray against the triangles)
        p=np.array([xz[0],xz[1]]);a,b,c=TRI[:,0][:,[0,2]],TRI[:,1][:,[0,2]],TRI[:,2][:,[0,2]]
        d=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1]);ok=np.abs(d)>1e-12;d=np.where(ok,d,1)
        l0=((b[:,1]-c[:,1])*(p[0]-c[:,0])+(c[:,0]-b[:,0])*(p[1]-c[:,1]))/d;l1=((c[:,1]-a[:,1])*(p[0]-c[:,0])+(a[:,0]-c[:,0])*(p[1]-c[:,1]))/d;l2=1-l0-l1
        hit=ok&(l0>=0)&(l1>=0)&(l2>=0);y=l0*TRI[:,0,1]+l1*TRI[:,1,1]+l2*TRI[:,2,1]
        return float(y[hit].max())
    # old CM-32 antennas (untextured steel 0.154, above 2.2 m, rear half) and the tail box (camo tex1, above 2.12 m, behind z -2.8)
    for x in old:
        P=arr(x);col=tuple(round(c,3) for c in x['col'])
        if not x['tex'] and col in ((0.154,0.154,0.154,1.0),(0.03,0.03,0.03,1.0)):m=(P[:,1]>2.2)&(P[:,2]<-1.2)   # antenna masts (tyre material, 0.03 since v3)
        elif x['tex'].endswith('_tex1.png'):m=(P[:,1]>2.12)&(P[:,2]<-2.8)&(np.abs(P[:,0])<0.7)
        else:continue
        s=sub_of(x,m)
        if s and x['tex'] and arr(s)[:,1].max()<2.3:s=None   # keep only the box itself, not the old tail plates under it
        if s and len(s['idx'])//3<20:s=None   # stray caps
        if s:   # the CM-32 and CM-34 roofs are both at 2.22 m, so the antennas and the box keep their height
            out.append(s);k=x['tex']+'|'+','.join('%.4f'%c for c in x['col']);mj[k]=mjo.get(k,{'metallic':0.3,'smoothness':0.4,'alpha':'OPAQUE','cutoff':0.5,'emissive':[0,0,0],'unlit':False})
    # vanilla Mk19 station where the CM-32's own station stood (centre x 0.37, z -0.30), on the roof
    tgt=np.array([0.37,0,-0.30]);tgt[1]=roof((tgt[0],tgt[2]))-0.01   # pedestal foot 1 cm into the roof
    for p in rws_parts('m_roc_cm32_static' if st=='m_roc_cm32_static' else 'm_roc_cm32_lo_static'):
        Q=arr(p);Q=Q-np.array([rws_c[0],rws_min[1],rws_c[2]])+tgt;p['pos']=Q.ravel().tolist();out.append(p)
        mj[p['tex']+'|1.0000,1.0000,1.0000,1.0000']={'metallic':0.0 if 'rws' in p['tex'] else 1.0,'smoothness':0.35,'alpha':'OPAQUE','cutoff':0.5,'emissive':[0,0,0],'unlit':False}
    write(f'{M}/{st}.fam',[('root',out)]);json.dump(mj,open(f'{M}/{st}.mat.json','w'),indent=1)
    print(st,'sub-meshes',len(out),'triangles',sum(len(x['idx'])//3 for x in out),'station at',tgt.round(2))
# textures for the station (full size for the Arsenal, half for battle)
for st,size in (('m_roc_cm32_static',None),('m_roc_cm32_lo_static',2)):
    base=Image.open(VX+'/tex/US_STRYKER_1_BaseMap_10113.png').convert('RGBA');g=Image.open(VX+'/tex/mk_19_mk20_BaseMap_88621.png').convert('RGBA')
    mk=Image.open(VX+'/tex/mk_19_mk20_MaskMap_80490.png').convert('RGBA');nm=np.asarray(Image.open(VX+'/tex/mk_19_mk20_Normal_3812.png').convert('RGBA')).astype(np.float32)/255
    x_,y_=nm[...,3]*2-1,nm[...,1]*2-1;z_=np.sqrt(np.clip(1-x_*x_-y_*y_,0,1));nrgb=Image.fromarray((np.dstack([x_,y_,z_])*127.5+127.5).clip(0,255).astype(np.uint8),'RGB')   # packed normal (X in A, Y in G) -> RGB
    for im,name in ((base,'rws'),(g,'mk19'),(mk,'mk19_mask'),(nrgb,'mk19_n')):
        if size:im=im.resize((im.width//size,im.height//size),Image.LANCZOS)
        im.save(f'{M}/{st}_{name}.png')
print('textures written')
