"""Patriot wheels on ROC trucks (Shawn 27 Nov 19:3x: "Apply the PBR property of patriot PAC-2 to models of Hsiung Feng IIE, Kung Feng VI,
Land Sword II and Tien Kung III, Thunderbolt-2000. Including the details of metallic reflection and the texture of wheels"; 20:0x: HF-IIE
preview first, then Thunderbolt-2000). The vanilla Patriot PAC-2 sheet (US_Patriot_1_1 BaseMap) has a whole tyre sidewall with its hub
(centre 1442,1217, radius 73 px) and a tread strip (x 0-468, y 1450-1520). A new 2048 wheel sheet: sidewall disc in the top-left 1024
square, tread band (2048 x 300) below. Every wheel of the given texture (connected pieces of those sub-meshes, axis = the thinnest box
side) gets new UVs per triangle: side faces (normal along the axis) a planar disc map, the rest the tread wrapped once round.
Mask: rubber metallic 0 / smoothness 0.15, hub metallic 0.1 / smoothness 0.35 (Patriot: metallic 0); flat normal map.
All four .fam files; the old sheet and .fam files go to veh/x/<slug>/pre-patriot-wheels/. usage: python patriot_wheels.py SLUG TEXINDEX[:split]
':split' (Thunderbolt-2000, whose wheels share a sheet with other parts): only wheel-shaped groups move, into a new sub-mesh on a new
<stem>_wheel.png sheet (round within 15 %, at least 0.5 m across, thinner than 0.6 of the diameter); a .mat.json entry is added."""
import sys,os,shutil,struct,glob,numpy as np
from PIL import Image
T=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,T);from famread import read_fam
slug,ti=sys.argv[1],int(sys.argv[2].split(':')[0]);SPLIT=sys.argv[2].endswith(':split');V=T+'/../veh';M=V+'/models';BK=f'{V}/x/{slug}/pre-patriot-wheels';os.makedirs(BK,exist_ok=True)
PAT='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_PATRIOT_PAC2/tex/US_Patriot_1_1_BaseMap_54991.png'
src=Image.open(PAT).convert('RGB');CX,CY,R=1442,1217,73
S=2048;sheet=Image.new('RGB',(S,S),(40,40,38))
disc=src.crop((CX-R,CY-R,CX+R,CY+R)).resize((1024,1024),Image.LANCZOS);sheet.paste(disc,(0,0))
tread=src.crop((0,1450,468,1520)).resize((S,300),Image.LANCZOS);sheet.paste(tread,(0,1100))
a=np.asarray(sheet).astype(np.float32);yy,xx=np.mgrid[0:S,0:S];rr=np.hypot(xx-512,yy-512)/512
rub=((rr>0.62)&(rr<=1)&(yy<1024))|((yy>=1100)&(yy<1400))
mask=np.zeros((S,S,4),np.uint8);mask[...,1]=255;mask[...,0]=np.where(rub,0,26);mask[...,3]=np.where(rub,38,90)
def S_(b):b=b.encode();return struct.pack('<i',len(b))+b
def write(path,parts):
    o=[b'FAM1',struct.pack('<i',len(parts))]
    for bone,ss in parts:
        o+=[S_(bone),struct.pack('<i',len(ss))]
        for x in ss:
            nv=len(x['pos'])//3;o+=[S_(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*x['pos']),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(path,'wb').write(b''.join(o))
def comps(P,Tr):
    _,w=np.unique(np.round(P,4),axis=0,return_inverse=True);w=w.ravel();par=np.arange(w.max()+1)
    def r(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    for t in w[Tr]:
        for u,v in ((t[0],t[1]),(t[1],t[2])):
            ru,rv=r(u),r(v)
            if ru!=rv:par[ru]=rv
    return np.array([r(t[0]) for t in w[Tr]])
nw=0
for f in sorted(glob.glob(f'{M}/m_roc_{slug}_*static*.fam')):
    b=f'{BK}/{os.path.basename(f)}'
    if not os.path.exists(b):shutil.copy(f,b)
    parts=read_fam(b);n=0
    for bone,ss in parts:
        extra=[]
        for x in ss:
            if not x['tex'].endswith(f'_tex{ti}.png'):continue
            P=np.array(x['pos'],np.float64).reshape(-1,3);Tr=np.array(x['idx']).reshape(-1,3);N=np.array(x['nrm']).reshape(-1,3)
            lab=comps(P,Tr);V_=[];U_=[];N_=[]
            # a wheel can be several pieces (tyre, rim, hub): group pieces by the biggest piece they sit inside; the wheel's box sets the map
            pcs=[]
            for L in np.unique(lab):
                q=P[np.unique(Tr[lab==L])];lo,hi=q.min(0),q.max(0);pcs.append([L,lo,hi,(hi-lo).max()])
            pcs.sort(key=lambda z:-z[3]);wheels=[]
            for L,lo,hi,sz in pcs:
                c=(lo+hi)/2;home=next((w for w in wheels if np.all(np.abs(c-(w[1]+w[2])/2)<=(w[2]-w[1])/2+1e-3)),None)
                if home:home[0].append(L)
                else:wheels.append([[L],lo,hi])
            if SPLIT:   # keep only wheel-shaped groups; the rest stays on the old sheet
                def round_(lo,hi):e=np.sort(hi-lo);return e[1]/e[2]>0.85 and e[2]>0.5 and e[0]<0.6*e[2]
                wheels=[w for w in wheels if round_(w[1],w[2])]
                keep=~np.isin(lab,[L for w in wheels for L in w[0]])
                if not wheels:continue
                rest=dict(x);used=np.unique(Tr[keep]);rm=-np.ones(len(P),int);rm[used]=np.arange(len(used))
                U0=np.array(x['uv']).reshape(-1,2);rest.update(pos=P[used].ravel().tolist(),nrm=N[used].ravel().tolist(),uv=U0[used].ravel().tolist(),idx=rm[Tr[keep]].ravel().tolist())
                if keep.any():extra.append(rest)
                x["tex"]=x['tex'].replace(f'_tex{ti}.png','_wheel.png')
            for Ls,lo,hi in wheels:
                t=Tr[np.isin(lab,Ls)];ext=hi-lo;ax=int(np.argmin(ext));o=[i for i in range(3) if i!=ax]
                c=(lo+hi)/2;Rw=max(ext[o[0]],ext[o[1]])/2
                tp=P[t];fn=np.cross(tp[:,1]-tp[:,0],tp[:,2]-tp[:,0]);fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-12
                side=np.abs(fn[:,ax])>0.6
                d=tp-c;uv=np.zeros(tp.shape[:2]+(2,))
                uv[side,:,0]=(0.5+0.5*d[side][...,o[0]]/Rw)*0.5;uv[side,:,1]=1-(0.5+0.5*d[side][...,o[1]]/Rw)*0.5   # top-left square (image y down)
                th=np.arctan2(d[~side][...,o[1]],d[~side][...,o[0]])/(2*np.pi)+0.5
                fix=th.max(1)-th.min(1)>0.5;th[fix]=np.where(th[fix]<0.5,th[fix]+1,th[fix])
                uv[~side,:,0]=th;w_=(d[~side][...,ax]-(lo[ax]-c[ax]))/max(ext[ax],1e-6);uv[~side,:,1]=1-(1100+20+w_*260)/S
                V_.append(tp.reshape(-1,3));U_.append(uv.reshape(-1,2));N_.append(N[t].reshape(-1,3));nw+=1
            V_,U_,N_=np.concatenate(V_),np.concatenate(U_),np.concatenate(N_)
            U_[:,1]-=1   # .fam v = image-from-bottom v - 1 (as cm32_kitbash vsub)
            x['pos']=V_.ravel().tolist();x['uv']=U_.ravel().tolist();x['nrm']=N_.ravel().tolist();x['idx']=list(range(len(V_)));n+=len(V_)//3
        ss.extend(extra)
    if SPLIT:   # material entry for the new sheet (same values as the wheel sheet in mode 1: the mask carries metal / smoothness)
        import json
        mp=f[:-4]+'.mat.json'
        if not os.path.exists(f'{BK}/'+os.path.basename(mp)):shutil.copy(mp,BK)
        mj=json.load(open(f'{BK}/'+os.path.basename(mp)));stem=os.path.basename(f)[:-4];stem=stem.replace('_l1','').replace('_l2','')
        old=next((v for k,v in mj.items() if k.startswith(f'{stem}_tex{ti}.png|')),{'alpha':'OPAQUE','cutoff':0.5,'emissive':[0,0,0],'unlit':False})
        mj[f'{stem}_wheel.png|1.0000,1.0000,1.0000,1.0000']={**old,'metallic':1.0,'smoothness':0.0,'alpha':'OPAQUE'};json.dump(mj,open(mp,'w'),indent=1)
    write(f,parts);print(os.path.basename(f),'wheel triangles',n)
for lvl,sz in (('static',2048),('lo_static',1024)):
    st=f'{M}/m_roc_{slug}_{lvl}_'+('wheel' if SPLIT else f'tex{ti}')
    for ext in ('.png','_n.png','_mask.png'):
        if os.path.exists(st+ext) and not os.path.exists(f'{BK}/{os.path.basename(st)}{ext}'):shutil.copy(st+ext,BK)
    sheet.resize((sz,sz),Image.LANCZOS).save(st+'.png');Image.new('RGB',(sz,sz),(128,128,255)).save(st+'_n.png');Image.fromarray(mask).resize((sz,sz),Image.NEAREST).save(st+'_mask.png')
print('wheels remapped (pieces over all files)',nw)
