"""ROC SF2 / Infantry 2 (Shawn 27 Nov 14:1x, in game: "Make them align with the shoulder"): on the rigged JGSF_soldier_01 body the
vest's shoulders and shoulder flaps stand several cm above the sleeves (the sleeves were lowered onto the game's arms), so they stick
up like wings. Works on the rigged bind-pose .fas (y up, metres): outside the collar (|x| > 5.5 % of the height) every vertex that is
not on a sleeve and not on the head/helmet/collar and lies above the shoulder line is pressed toward it: y' = S + (y - S) * K.
S runs from 2.5 % of the height above the sleeve top at the collar edge down to the sleeve top at |x| = 11 %. Vertices below the line
do not move. Parts = position-welded connected pieces. usage: python fas_shoulders.py IN.fas OUT.fas [K=0.35]"""
import io,struct,sys
import numpy as np
src,dst=sys.argv[1],sys.argv[2];K=float(sys.argv[3]) if len(sys.argv)>3 else 0.1
d=open(src,'rb').read();f=io.BytesIO(d);assert f.read(4)==b'FAS1'
n=lambda:struct.unpack('<i',f.read(4))[0];s=lambda:f.read(n()).decode()
bones=[s() for _ in range(n())];parts=[]
for _ in range(n()):
    mat=s();nv=n();P=np.frombuffer(f.read(nv*64),np.float32).reshape(-1,16).copy();ni=n();ix=f.read(ni*4);parts.append([mat,P,ni,ix])
V=np.concatenate([p[1][:,:3] for p in parts]);T=np.concatenate([np.frombuffer(p[3],np.int32).reshape(-1,3)+o for p,o in zip(parts,np.cumsum([0]+[len(p[1]) for p in parts[:-1]]))])
_,weld=np.unique(np.round(V,4),axis=0,return_inverse=True);weld=weld.ravel()
par=np.arange(weld.max()+1)
def root(i):
    while par[i]!=i:par[i]=par[par[i]];i=par[i]
    return i
for t in weld[T]:
    a,b,c=root(t[0]),root(t[1]),root(t[2]);par[b]=a;par[root(c)]=a
r=np.array([root(w) for w in weld])
y0,y1=V[:,1].min(),V[:,1].max();H=y1-y0;yr=(V[:,1]-y0)/H;ax=np.abs(V[:,0]-np.median(V[:,0]))
# 27 Nov 14:4x (Shawn's yellow curves): after rigging, one sleeve cap still bulged. Same smooth shoulder on both sides, pressing EVERY
# vertex (sleeves too) between the collar edge and the upper arm that lies above it; head, helmet and headset (above 88 % of the height) keep.
x1,x2,x3=0.075*H,0.14*H,0.19*H   # x1 outside the collar (0.055 pulled the collar sides into flat sheets)
top=lambda lo,hi,side:V[(ax>=lo)&(ax<hi)&(np.sign(V[:,0])==side)&(yr>0.7)&(yr<0.88),1].max()
RISE=float(sys.argv[4]) if len(sys.argv)>4 else 0.045   # Infantry 2 (Shawn 27 Nov 15:0x 'needs further fix'): 0.02, flatter
za=min(top(x3-0.005*H,x3+0.005*H,1),top(x3-0.005*H,x3+0.005*H,-1));yc=za+RISE*H
t=np.clip((ax-x1)/(x3-x1),0,1);S=np.where(ax<=x1,np.inf,za+(yc-za)*(1-t**2))
mv=(yr>0.72)&(yr<0.88)&(ax>x1)&(ax<x3+0.02*H)&(V[:,1]>S)
newy=V[:,1].copy();newy[mv]=S[mv]+(V[mv,1]-S[mv])*K
print('FASSHOULDERS arm top %.3f; collar-edge %.3f; moved %d vertices; max drop %.3f m'%(za,yc,mv.sum(),(V[:,1]-newy).max()))
o=0
for p in parts:
    p[1][:,1]=newy[o:o+len(p[1])];o+=len(p[1])
out=[b'FAS1',struct.pack('<i',len(bones))]+[struct.pack('<i',len(b.encode()))+b.encode() for b in bones]+[struct.pack('<i',len(parts))]
for mat,P,ni,ix in parts:out+=[struct.pack('<i',len(mat.encode()))+mat.encode(),struct.pack('<i',len(P)),P.astype(np.float32).tobytes(),struct.pack('<i',ni),ix]
open(dst,'wb').write(b''.join(out))
