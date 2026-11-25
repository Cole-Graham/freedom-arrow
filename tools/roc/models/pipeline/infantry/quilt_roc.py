"""quilt_roc.py (Shawn 25 Nov 11:3x: "make the details better following the ROC infantry's"): fill an N x N image with real ROC
Infantry camo by image quilting (Efros & Freeman 2001). Pieces come from clean areas of the ROC trousers and coat back, scaled
by texel density (pants 1412, coat 1256 px/m -> target px/m), with the baked fold shading flattened, so the pattern prints at the ROC Infantry size. Seams follow a minimum-error cut.
usage: python quilt_roc.py PANTS.png N TARGET_PX_PER_M OUT.png"""
import sys,numpy as np
from PIL import Image
src,N,tpx,out=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]),sys.argv[4]
from PIL import ImageFilter
from pathlib import Path
D=Path(src).parent
SRC=[('T_TWPants_Color.png',1412,(130,1260,790,1940)),('T_TWPants_Color.png',1412,(1230,1260,1920,1940)),   # lower trouser legs
     ('T_TWCoat_Color.png',1256,(1270,330,1700,1100))]                                                       # coat back
S=[]
for f,px,c in SRC:
    im=Image.open(D/f).convert('RGB').crop(c);k=tpx/px;im=im.resize((round(im.width*k),round(im.height*k)),Image.LANCZOS)
    a=np.asarray(im).astype(np.float32);L=a.mean(2);bl=np.asarray(Image.fromarray(np.clip(L,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(150))).astype(np.float32)
    a*=((L.mean()/np.maximum(bl,1))**.5)[...,None]   # flatten the fabric folds baked into the source, keep the camo
    S.append(np.clip(a,0,255))
B,OV=320,56;ST=B-OV;n=int(np.ceil((N-OV)/ST));W=n*ST+OV
O=np.zeros((W,W,3),np.float32);rng=np.random.default_rng(1125)
def cands(K=300):
    out=[]
    for _ in range(K):
        s=S[rng.integers(len(S))];y=rng.integers(0,s.shape[0]-B);x=rng.integers(0,s.shape[1]-B);out.append(s[y:y+B,x:x+B])
    return np.stack(out)
def cut(err):   # err: (B, OV) vertical overlap -> mask True where the NEW piece is used
    E=err.copy()
    for i in range(1,E.shape[0]):
        a=E[i-1];l=np.r_[np.inf,a[:-1]];r=np.r_[a[1:],np.inf];E[i]+=np.minimum(np.minimum(l,a),r)
    m=np.zeros(err.shape,bool);j=int(E[-1].argmin())
    for i in range(E.shape[0]-1,-1,-1):
        m[i,j:]=True
        if i:lo=max(j-1,0);j=lo+int(E[i-1,lo:j+2].argmin())
    return m
for by in range(n):
    for bx in range(n):
        y,x=by*ST,bx*ST;C=cands();e=np.zeros(len(C),np.float32);cur=O[y:y+B,x:x+B]
        if bx:e+=((C[:,:,:OV]-cur[None,:,:OV])**2).sum((1,2,3))
        if by:e+=((C[:,:OV,:]-cur[None,:OV,:])**2).sum((1,2,3))
        p=C[rng.choice(np.argsort(e)[:15])];m=np.ones((B,B),bool)   # random among the 15 best: the single best repeats one piece
        if bx:m[:,:OV]&=cut(((p[:,:OV]-cur[:,:OV])**2).sum(2))
        if by:m[:OV,:]&=cut(((p[:OV,:]-cur[:OV,:])**2).sum(2).T).T
        O[y:y+B,x:x+B]=np.where(m[...,None],p,cur)
Image.fromarray(np.clip(O[:N,:N],0,255).astype('uint8')).save(out);print('QUILT',n*n,'pieces',N)
