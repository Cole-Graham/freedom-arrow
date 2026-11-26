"""antelope_own_tex.py (Shawn 26 Nov 02:3x: "Replace the 3 small textures customized by you for Antelope"): BA Codex's own replacements for
the 3 War Thunder-named textures in the Antelope pack. Same size and layout so the model's UVs still land on lamps, glass and grille:
headlight sheet 256 (only the lamp positions are read from the old sheet), side glass 512, round wire grille 1024 (alpha = wires)."""
import sys,numpy as np
from PIL import Image,ImageDraw,ImageFilter
from collections import deque
src,out=sys.argv[1],sys.argv[2];rng=np.random.default_rng(26)
def noise(n,cell,amp):
    r=rng.random((max(2,n//cell),)*2);return (np.asarray(Image.fromarray((r*255).astype('uint8')).resize((n,n),Image.BICUBIC)).astype(float)/255-.5)*amp
# 1. headlights: lamp discs where the old sheet has them, new lens drawing inside each
old=np.asarray(Image.open(f'{src}/headlight_glass_c.jpg').convert('RGB')).astype(float);N=old.shape[0]
yy,xx=np.mgrid[0:N,0:N].astype(float)
big=[(N/4,N/4),(3*N/4,N/4),(N/4,3*N/4),(3*N/4,3*N/4)]                    # 2x2 headlight sheet, one lamp per quadrant
rb=min(np.max(np.where(old[N//4,:N//2].mean(1)>14))-N/4, N/4-1)          # lamp radius read along the first row
mask=old.mean(2)>14
for cx,cy in big: mask&=np.hypot(xx-cx,yy-cy)>rb+2
lab=np.zeros(mask.shape,int);blobs=[(cx,cy,rb,None) for cx,cy in big]
for y in range(N):
    for x in range(N):
        if mask[y,x] and not lab[y,x]:
            q=deque([(y,x)]);lab[y,x]=len(blobs)+1;pts=[]
            while q:
                a,b=q.popleft();pts.append((a,b))
                for c,d in ((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
                    if 0<=c<N and 0<=d<N and mask[c,d] and not lab[c,d]:lab[c,d]=len(blobs)+1;q.append((c,d))
            if len(pts)>12 and len(pts)<3000:
                P=np.array(pts);cy,cx=P.mean(0);r=np.sqrt(len(pts)/np.pi);col=old[P[:,0],P[:,1]].mean(0);blobs.append((cx,cy,r,col))
img=np.zeros((N,N,3))
for cx,cy,r,col in blobs:
    d=np.hypot(xx-cx,yy-cy)/r;m=d<=1.0
    if r<20:img[m]=col;continue           # small indicator lamps keep their colour
    lens=170-60*d**1.5+10*np.sin(xx/2.2)+6*np.sin(yy/3.1)    # domed lens, fine flutes
    rim=(d>.9)*-50;refl=np.clip(1-np.hypot(xx-cx+.35*r,yy-cy+.35*r)/(.25*r),0,1)*60
    for c in range(3):img[...,c]=np.where(m,np.clip(lens+rim+refl,0,255),img[...,c])
Image.fromarray(img.astype('uint8')).convert('RGBA').save(f'{out}/headlight.png')
# 2. side glass: dark blue-grey, faint smudges
n=512;base=np.array([43,44,54],float)
g=base[None,None,:]+noise(n,64,14)[...,None]+noise(n,8,4)[...,None]+np.linspace(-6,6,n)[:,None,None]
Image.fromarray(np.clip(g,0,255).astype('uint8')).convert('RGBA').save(f'{out}/side_glass.png')
# 3. round wire grille: rim, 18 rings, 12 spokes; colour = painted metal, alpha = wires only
n=1024;W_=Image.new('L',(n,n),0);d=ImageDraw.Draw(W_);c=n/2;R=.47*n
for k in range(1,19):rr=R*k/18;d.ellipse((c-rr,c-rr,c+rr,c+rr),outline=255,width=5 if k<18 else 12)
for k in range(12):
    a=k*np.pi/6;d.line((c,c,c+R*np.cos(a),c+R*np.sin(a)),fill=255,width=8)
d.ellipse((c-14,c-14,c+14,c+14),fill=255)
A=np.asarray(W_.filter(ImageFilter.GaussianBlur(.8))).astype(float)
col=np.array([95,96,100],float)[None,None,:]+noise(n,32,18)[...,None]
rgba=np.dstack([np.clip(col,0,255),A*228/255]).astype('uint8');Image.fromarray(rgba,'RGBA').save(f'{out}/grille.png')
print('lamps',len(blobs),[(round(cx),round(cy),round(r)) for cx,cy,r,_ in blobs])
