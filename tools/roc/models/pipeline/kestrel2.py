"""Kestrel-2 launcher model (Shawn 27 Nov 18:0x: "Change the Kestrel-1 to Kestrel-2, Use the model of AT4-CS RS but make the tube dark grey").
The vanilla AT-4 mesh (prefab AT-4, extracted with work/vanilla-export-20261123/extract.py) in its prefab space (the mesh node's rotation and
x2.219 scale applied), so a FAModels weapon rule with offset 0 / scale 1 lies exactly where the vanilla launcher would; colour map turned to a dark
grey with the original shading (luminance kept, contrast kept, ~RGB 58,60,62 average); vanilla normal and mask maps.
Writes t91/models/w_roc_kestrel2(.fam, _lo.fam, .png, _n.png, _mask.png). usage: python kestrel2.py"""
import os,json,struct,glob
import numpy as np
from PIL import Image
X='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/AT-4';O=os.path.dirname(os.path.abspath(__file__))+'/../t91/models'
sc=json.load(open(X+'/scene.json'));n=[n for n in sc['nodes'] if n.get('mesh')][0];d=np.load(glob.glob(X+'/mesh/*.npz')[0])
x,y,z,w=n['rot'];R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
V=(d['v']*np.array(n['scale']))@R.T+np.array(n['pos']);N=d['n']@R.T;N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12
UV=np.c_[d['uv'][:,0],d['uv'][:,1]-1]
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for name in ('w_roc_kestrel2','w_roc_kestrel2_lo'):
    nv=len(V);idx=d['f0'].ravel().tolist()
    o=[b'FAM1',struct.pack('<i',1),S('root'),struct.pack('<i',1),S('w_roc_kestrel2.png'),struct.pack('<4f',1,1,1,1),struct.pack('<i',nv),
       struct.pack('<%df'%(3*nv),*V.astype(np.float32).ravel()),struct.pack('<%df'%(3*nv),*N.astype(np.float32).ravel()),struct.pack('<%df'%(2*nv),*UV.astype(np.float32).ravel()),
       struct.pack('<i',len(idx)),struct.pack('<%di'%len(idx),*idx)]
    open(f'{O}/{name}.fam','wb').write(b''.join(o))
    json.dump({'w_roc_kestrel2.png|1.0000,1.0000,1.0000,1.0000':{'metallic':0.0,'smoothness':0.35,'alpha':'OPAQUE','cutoff':0.5,'emissive':[0,0,0],'unlit':False}},open(f'{O}/{name}.mat.json','w'),indent=1)
t=lambda k:X+'/tex/'+[f for f in os.listdir(X+'/tex') if k in f][0]
a=np.asarray(Image.open(t('BaseMap')).convert('RGBA')).astype(float);L=a[...,:3]@[0.3,0.59,0.11]
g=(L-L.mean())*0.8+60;a[...,0],a[...,1],a[...,2]=g-2,g,g+2
Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA').save(O+'/w_roc_kestrel2.png')
Image.open(t('MaskMap')).save(O+'/w_roc_kestrel2_mask.png')
nm=np.asarray(Image.open(t('Normal')).convert('RGBA')).astype(np.float32)/255;xx,yy=nm[...,3]*2-1,nm[...,1]*2-1
if np.abs(nm[...,0]-nm[...,3]).mean()<0.02 or nm[...,0].std()<0.02:   # packed (X in A, Y in G)
    Image.fromarray((np.dstack([xx,yy,np.sqrt(np.clip(1-xx*xx-yy*yy,0,1))])*127.5+127.5).clip(0,255).astype(np.uint8),'RGB').save(O+'/w_roc_kestrel2_n.png')
else:Image.open(t('Normal')).convert('RGB').save(O+'/w_roc_kestrel2_n.png')
print('KESTREL2 verts',len(V),'tris',len(d['f0']),'bbox',V.min(0).round(3),V.max(0).round(3),'colour mean',np.asarray(Image.open(O+'/w_roc_kestrel2.png'))[...,:3].reshape(-1,3).mean(0).round(1))
