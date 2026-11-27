"""ROC SF2 / Infantry 2 (Shawn 27 Nov 14:1x, in game: "Make them align with the shoulder"): on JGSF_soldier_01 the vest's shoulders
and its two shoulder flaps rise up to ~7 cm above the top of the sleeves, so in game they stick up like wings. Outside the collar
(|x| > 5.5 % of the height) everything that is not a sleeve, the head or the helmet and lies above the shoulder line is pressed down
toward that line: z' = S + (z - S) * K (K 0.35). The shoulder line S runs from 2.5 % of the height above the sleeve top at the collar edge down to the top of the
sleeve at |x| = 11 % of the height. Vertices below the line do not move, so the vest stays joined. Writes a new .blend that the rig
config uses. usage: blender -b IN.blend -P shoulder_flaps.py -- MESH OUT.blend [k=0.35] [--dry]"""
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:];name,out=a[0],a[1];dry='--dry' in a;K=float(next((x[2:] for x in a if x.startswith('k=')),'0.08'));DROP=float(next((x[5:] for x in a if x.startswith('drop=')),'0.012'))
o=bpy.data.objects[name];me=o.data;W=np.array(o.matrix_world);Wi=np.linalg.inv(W)
L=np.array([v.co[:] for v in me.vertices]);V=(np.c_[L,np.ones(len(L))]@W.T)[:,:3]
z0,z1=V[:,2].min(),V[:,2].max();H=z1-z0;cx=np.median(V[:,0]);ax=np.abs(V[:,0]-cx);zr=(V[:,2]-z0)/H
p=list(range(len(V)))
def f(i):
    while p[i]!=i:p[i]=p[p[i]];i=p[i]
    return i
for e in me.edges:
    x,y=f(e.vertices[0]),f(e.vertices[1]);p[y]=x
r=np.array([f(i) for i in range(len(V))]);sleeve=np.zeros(len(V),bool)
for k in np.unique(r):
    m=r==k
    if m.sum()>150 and np.median(ax[m])/H>0.15 and zr[m].min()>0.5:sleeve|=m   # the two sleeves (arms reach out past 15 % of the height)
x1,x2=0.055*H,0.11*H
band=lambda lo,hi:(ax>=lo)&(ax<hi)&~sleeve&(zr>0.75)&(zr<0.9)
za=V[sleeve&(ax>x2-0.01*H)&(ax<x2+0.02*H),2].max()-DROP*H;zc=za+0.02*H   # DROP: the rig lowers the sleeves a little more (ArmFit); the line slopes 2 % of the height up to the collar   # a natural shoulder slope: 2.5 % of the height higher at the collar edge
RISE=float(next((x[5:] for x in a if x.startswith('rise=')),'0.03'));X2=float(next((x[3:] for x in a if x.startswith('x2=')),'0.125'))
x2=X2*H;zc=za+RISE*H
# Shawn 27 Nov 14:4x (yellow curves): a smooth shoulder, flat at the collar and rounding down to the sleeve: S = za + (zc - za) * (1 - t^2)
S=lambda d:np.where(d<=x1,np.inf,np.where(d>=x2,za,za+(zc-za)*(1-((d-x1)/(x2-x1))**2)))
head=np.zeros(len(V),bool)
for k in np.unique(r):
    m=r==k
    if zr[m].max()>0.89:head|=m   # head, helmet, headset and the collar keep their shape
sel=~sleeve&~head&(zr>0.75)&(ax>x1);s=S(ax);mv=sel&(V[:,2]>s)
newV=V.copy();newV[mv,2]=s[mv]+(V[mv,2]-s[mv])*K
print('SHOULDER collar-edge z %.3f sleeve-top z %.3f; vertices pressed down %d; max drop %.3f (%.1f %% of height)'%(zc,za,mv.sum(),(V[:,2]-newV[:,2]).max(),100*(V[:,2]-newV[:,2]).max()/H))
if not dry:
    Lnew=(np.c_[newV,np.ones(len(newV))]@Wi.T)[:,:3]
    for v,c in zip(me.vertices,Lnew):v.co=c
    me.update();bpy.ops.wm.save_as_mainfile(filepath=out);print('SAVED',out)
