"""Seated crew pose from the vanilla MTV (Shawn 28 Nov, list 7: "Add 2x Drivers to ROC vehicles ... use the models of ROC Mech. Rifleman").
The vanilla US_MTV prefab (work/vanilla-export-20261123/out/US_MTV) has its driver as a 40-bone skinned mesh (lod_0) with the bones posed
seated in the cab. Bone world matrices (prefab space) x bind poses give the skinning matrices; any body rigged to the same 40-bone soldier
skeleton (our .fas files) can be posed with them. Writes seated.npz: bone names, skin matrices (40,4,4), and the posed vanilla driver for a check."""
import json,numpy as np
E='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_MTV'
d=json.load(open(E+'/scene.json'));N=d['nodes'];z=np.load(E+'/mesh/lod_0_67036.npz')
def q2m(q):
    x,y,zz,w=q;return np.array([[1-2*(y*y+zz*zz),2*(x*y-zz*w),2*(x*zz+y*w)],[2*(x*y+zz*w),1-2*(x*x+zz*zz),2*(y*zz-x*w)],[2*(x*zz-y*w),2*(y*zz+x*w),1-2*(x*x+y*y)]])
def local(n):
    M=np.eye(4);r=n['rot'];r=[r[k] for k in 'xyzw'] if isinstance(r,dict) else r;s=n['scale'];s=[s[k] for k in 'xyz'] if isinstance(s,dict) else s
    p=n['pos'];p=[p[k] for k in 'xyz'] if isinstance(p,dict) else p
    M[:3,:3]=q2m(r)*np.array(s);M[:3,3]=p;return M
W={}
def world(i):
    if i in W:return W[i]
    n=N[i];M=local(n);W[i]=M if n['parent'] in (None,-1) else world(n['parent'])@M;return W[i]
lod=[x for x in N if x['name']=='lod_0'][0];names=[N[i]['name'] for i in lod['bones']]
S=np.array([world(i)@z['bp'][k] for k,i in enumerate(lod['bones'])])
def pose(v,bi,bw):
    V=np.c_[v,np.ones(len(v))];out=np.zeros((len(v),3))
    for k in range(4):out+=bw[:,k:k+1]*np.einsum('nij,nj->ni',S[bi[:,k]],V)[:,:3]
    return out
P=pose(z['v'],z['bi'],z['bw'])
print('vanilla driver posed bbox',P.min(0).round(2),P.max(0).round(2))
print('head',(world(lod['bones'][names.index('Head')])[:3,3]).round(2),'hips',world(lod['bones'][names.index('Hips')])[:3,3].round(2))
np.savez('seated.npz',names=np.array(names),S=S,driver=P,f=z['f0'])
