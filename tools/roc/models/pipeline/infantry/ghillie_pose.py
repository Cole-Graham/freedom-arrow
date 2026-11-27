"""ROC SF 4 (Shawn 27 Nov 01:5x "make sure the arm and the hand in ROC SF 4 are align with the Ghillie suit's"): the ghillie (JiLiFu) was modelled
in a T-pose (sleeves level at z 1.45 m out to |x| 0.80 m) while the soldier's arms hang in an A-pose (hand at |x| 0.62 m, z 0.95 m). This bends each
ghillie sleeve onto the arm: a sleeve point at distance d from the shoulder (|x| = 0.28 m) goes to the point at arc length d on the arm's centre line
(centroids of coat + arm in 2 cm slices), keeping its offset across the sleeve; a smooth ramp over |x| 0.24-0.36 m joins it to the body.
Writes a new .blend; the source is not changed. usage: blender -b SRC.blend -P ghillie_pose.py -- OUT.blend"""
import bpy,sys,numpy as np,mathutils as mu
out=sys.argv[sys.argv.index('--')+1]
def W(n):
    o=bpy.data.objects[n];M=np.array(o.matrix_world);return o,M,np.array([v.co[:] for v in o.data.vertices])
def world(M,P):return P@M[:3,:3].T+M[:3,3]
_,Ma,A=W('SM_CC_Arm');_,Mc,C=W('SM_TWCoat');g,Mg,G=W('JiLiFu')
A,C,GW=world(Ma,A),world(Mc,C),world(Mg,G)
# source units are cm

XS=28.0
new=GW.copy()
for side in (1,-1):
    R=np.vstack([A,C]);R=R[side*R[:,0]>XS-2]
    xs=np.arange(XS,(side*R[:,0]).max(),2.0)
    cl=np.array([R[np.abs(side*R[:,0]-x)<1.0].mean(0) for x in xs if (np.abs(side*R[:,0]-x)<1.0).any()])   # arm centre line (x,y,z)
    seg=np.linalg.norm(np.diff(cl,axis=0),axis=1);arc=np.concatenate([[0],np.cumsum(seg)])
    S=GW[side*GW[:,0]>XS-6]
    sx=np.arange(XS-6,(side*GW[:,0]).max()+2,2.0)
    sc={round(x):S[np.abs(side*S[:,0]-x)<1.0][:,1:].mean(0) for x in sx if (np.abs(side*S[:,0]-x)<1.0).any()}   # sleeve centre (y,z) per slice
    keys=np.array(sorted(sc));vals=np.array([sc[k] for k in keys])
    idx=np.where(side*GW[:,0]>XS-4)[0]
    for i in idx:
        x=side*GW[i,0];d=max(0.0,x-XS)
        yc=np.interp(x,keys,vals[:,0]);zc=np.interp(x,keys,vals[:,1]);oy,oz=GW[i,1]-yc,GW[i,2]-zc
        s=min(d,arc[-1]);j=min(np.searchsorted(arc,s,side='right')-1,len(cl)-2);f=(s-arc[j])/max(seg[j],1e-6)
        p=cl[j]+(cl[j+1]-cl[j])*f+(cl[j+1]-cl[j])/max(seg[j],1e-6)*max(0,d-arc[-1])   # past the hand: continue straight
        t=(cl[j+1]-cl[j])/max(seg[j],1e-6);up=np.array([-t[2]*side,0,t[0]*side]);up/=np.linalg.norm(up)+1e-9
        m=p+np.array([0,oy,0])+up*oz
        w=np.clip((x-24)/12,0,1);w=w*w*(3-2*w)
        new[i]=GW[i]*(1-w)+m*w
inv=np.linalg.inv(Mg);loc=new@inv[:3,:3].T+inv[:3,3]
for v,c in zip(g.data.vertices,loc):v.co=mu.Vector(c)
bpy.ops.wm.save_as_mainfile(filepath=out,copy=True)
print('GHILLIE posed; sleeve vertices moved',int((np.linalg.norm(new-GW,axis=1)>0.5).sum()))
