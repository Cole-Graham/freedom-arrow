"""ROC Marine grey arm flap (Shawn 27 Nov, in game: "This is still a bug"): the weight transfer left a few vertices on the upper arm,
just past the shoulder joint, weighted to the spine. In the rifle stance the arm turns down and those vertices stay with the chest,
so the triangles between them and the arm stretch into a sheet from the shoulder to the elbow. Works on the rigged bind-pose .fas:
for each side, the shoulder joint is the mean of the vertices shared between <Side>Arm and the bones above it; every vertex within
20 cm of the joint height whose |x| is past (joint |x| - 2 cm) gives its torso weight (Hips, Spine, Spine1, Spine2) to <Side>Arm,
ramping from 0 % there to 100 % at joint |x| + 2 cm. Other weights do not change. usage: python fas_armweights.py IN.fas OUT.fas"""
import io,struct,sys
import numpy as np
src,dst=sys.argv[1],sys.argv[2]
d=open(src,'rb').read();f=io.BytesIO(d);assert f.read(4)==b'FAS1'
n=lambda:struct.unpack('<i',f.read(4))[0];s=lambda:f.read(n()).decode()
bones=[s() for _ in range(n())];parts=[]
for _ in range(n()):
    mat=s();nv=n();off=f.tell();P=np.frombuffer(f.read(nv*64),np.float32).reshape(-1,16).copy();ni=n();f.read(ni*4);parts.append([mat,P,off])
A=np.concatenate([p[1] for p in parts]);AI=A.view(np.int32)
TORSO=[bones.index(b) for b in ('Hips','Spine','Spine1','Spine2') if b in bones]
def wsum(P,bi):return np.where(P.view(np.int32)[:,8:12]==bi,P[:,12:16],0).sum(1)
moved=0
for side,sg in (('Left',-1),('Right',1)):
    arm=bones.index(side+'Arm');w=wsum(A,arm);j=A[(w>0.3)&(w<0.7),:3].mean(0);jx=abs(j[0])
    for p in parts:
        P=p[1];PI=P.view(np.int32);x,y=P[:,0]*sg,P[:,1]
        fr=np.clip((x-(jx-0.02))/0.04,0,1)*(np.abs(y-j[1])<0.2)
        tor=np.isin(PI[:,8:12],TORSO)&(P[:,12:16]>0)
        tw=(P[:,12:16]*tor).sum(1)*fr
        for i in np.where(tw>1e-4)[0]:
            W=P[i,12:16].copy();t=tor[i];W[t]*=1-fr[i]
            k=np.where(PI[i,8:12]==arm)[0]
            if len(k):k=k[0]
            else:k=int(np.argmin(np.where(t,W,9)));W[k]=0;PI[i,8+k]=arm   # take the emptiest torso slot (its rest is renormalised away)
            W[k]+=tw[i];P[i,12:16]=W/W.sum();moved+=1
    print(side,'joint',j.round(3))
out=bytearray(d)
for mat,P,off in parts:out[off:off+P.nbytes]=P.tobytes()
open(dst,'wb').write(bytes(out));print('vertices reweighted',moved,'->',dst)
