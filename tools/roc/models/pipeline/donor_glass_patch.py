"""Truck glass from a vanilla donor whose glass reads the donor's own texture sheet (Shawn 28 Nov 03:0x, list 7: HF-IIE "The glass is still
wrong, use the material on HEMTT to replace it"; Kung Feng VI "Replace the glass material by the material on M142 HIMARS' window glass").
US_HeavyOshkosh3_glass (HEMTT) and Himars GLASS (M142) are the vehicle layered shader with the truck's whole 2048 base map (Layer_A97CDC25);
the vanilla windows sit on plain tinted glass patches of that sheet (read from the units bundle 28 Nov, /tmp/l8prev/pm2.py):
  HEMTT  px x 1050-1184 y 566-725  (rgb 64/86/85, alpha 171)      HIMARS px x 1606-1697 y 1290-1532 (rgb 99/99/99, alpha 189)
Every donor-glass sub-mesh (mat.json entry with a cockpitDonor) of the model's four .fam files gets its UVs squeezed into that patch (6 px
inset, Unity v = 1 - y/2048), and the entries name the new donor. Originals go to veh/x/<slug>/pre-donorpatch/.
usage: python donor_glass_patch.py SLUG hemtt|himars"""
import sys,os,json,struct,shutil
import numpy as np
T=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,T);from famread import read_fam
PATCH={'hemtt':('US_HeavyOshkosh3_glass',1050,1184,566,725),'himars':('Himars GLASS',1606,1697,1290,1532)}
slug,which=sys.argv[1],sys.argv[2];donor,x0,x1,y0,y1=PATCH[which];I=6
U0,U1,V0,V1=(x0+I)/2048,(x1-I)/2048,1-(y1-I)/2048,1-(y0+I)/2048
M=T+'/../veh/models';BK=f'{T}/../veh/x/{slug}/pre-donorpatch';os.makedirs(BK,exist_ok=True)
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for st in (f'm_roc_{slug}_static',f'm_roc_{slug}_lo_static',f'm_roc_{slug}_lo_static_l1',f'm_roc_{slug}_lo_static_l2'):
    if not os.path.exists(f'{M}/{st}.fam'):continue
    for ext in ('.fam','.mat.json'):
        if not os.path.exists(f'{BK}/{st}{ext}'):shutil.copy(f'{M}/{st}{ext}',f'{BK}/{st}{ext}')
    mj=json.load(open(f'{BK}/{st}.mat.json'));keys={k for k,v in mj.items() if v.get('cockpitDonor')}
    for k in keys:mj[k]['cockpitDonor']=donor
    V=read_fam(f'{BK}/{st}.fam');n=0
    for b,q in V:
        for x in q:
            if x['tex']+'|'+','.join('%.4f'%c for c in x['col']) not in keys:continue
            uv=np.array(x['uv'],np.float64).reshape(-1,2);lo,hi=uv.min(0),uv.max(0)
            uv=(uv-lo)/np.maximum(hi-lo,1e-6);uv[:,0]=U0+uv[:,0]*(U1-U0);uv[:,1]=V0+uv[:,1]*(V1-V0);x['uv']=uv.ravel().tolist();n+=1
    o=[b'FAM1',struct.pack('<i',len(V))]
    for bone,ss in V:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{M}/{st}.fam','wb').write(b''.join(o));json.dump(mj,open(f'{M}/{st}.mat.json','w'),indent=1)
    print(st,'glass sub-meshes',n,'->',donor,'u %.4f-%.4f v %.4f-%.4f'%(U0,U1,V0,V1))
