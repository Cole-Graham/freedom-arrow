"""recamo_sf1.py (Shawn 25 Nov 10:5x: SF Scout = ROC SF1 body with the ROC Infantry camo on the uniform).
Mask = large bright camo blocks of SF1's Camo body texture (512 px flood fill, blocks > 2 %); fill = generated ROC digital camo at
the ROC coat's palette and block size (scaled 1617/1256 px/m), with fold shading taken from SF1's Black variant."""
import sys,numpy as np
from PIL import Image,ImageFilter,ImageDraw
from collections import deque
T,coat,out=sys.argv[1:4]
C=Image.open(f'{T}/Camo/Body_Base_color.png').convert('RGB');Bk=Image.open(f'{T}/Black/Body_Base_color.png').convert('L');N=C.size[0]
s=np.asarray(C.resize((512,512),Image.BOX)).astype(float);lum=s.mean(2);sat=s.max(2)-s.min(2)
cand=(lum>48)&(sat>12)
lab=np.zeros((512,512),int);keep=np.zeros((512,512),bool);n=0
for y in range(512):
    for x in range(512):
        if cand[y,x] and not lab[y,x]:
            n+=1;q=deque([(y,x)]);lab[y,x]=n;pts=[]
            while q:
                a,b=q.popleft();pts.append((a,b))
                for c,d in ((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
                    if 0<=c<512 and 0<=d<512 and cand[c,d] and not lab[c,d]:lab[c,d]=n;q.append((c,d))
            if len(pts)>0.02*512*512:
                for a,b in pts:keep[a,b]=True
if len(sys.argv)>4:   # keep boots: UV polygons of faces below ankle height (uv_zmask.py)
    import json;bm=Image.new('L',(512,512));dr=ImageDraw.Draw(bm)
    for poly in json.load(open(sys.argv[4])):dr.polygon([(u*512,v*512) for u,v in poly],fill=255)
    keep&=~(np.asarray(bm.filter(ImageFilter.MaxFilter(5)))>0)
m=Image.fromarray((keep*255).astype('uint8')).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # close small holes
m=m.resize((N,N),Image.BILINEAR).filter(ImageFilter.GaussianBlur(2));M=np.asarray(m).astype(float)[...,None]/255
# ROC digital camo, generated (tiling one patch showed mirror seams). Palette and shares from a clean T_TWCoat patch (k-means):
PAL=np.array([[22,33,31],[49,73,52],[75,90,65],[132,136,125]],float);SHARE=(.117,.423,.362,.098)
blk=1617/1256*4                                  # 4 px blocks on the coat at 1256 px/m -> SF1 px
G=int(np.ceil(N/blk));rng=np.random.default_rng(25)
def noise(cells,octs=3):
    t=np.zeros((G,G))
    for o in range(octs):
        c=max(2,int(G/cells*2**o));r=rng.random((c,c));t+=np.asarray(Image.fromarray((r*255).astype('uint8')).resize((G,G),Image.BICUBIC)).astype(float)/2**o
    return (t-t.mean())/t.std()                # unit scale, so the per-block noise below has weight
q=lambda a,f:a>=np.quantile(a,1-f)
blob=noise(G*blk/(1617*.05));cls=np.where(q(blob+.22*rng.standard_normal((G,G)),SHARE[1]/(SHARE[1]+SHARE[2])),1,2)    # ~9 cm dark-green / olive blobs
dark=noise(G*blk/(1617*.018))+.4*blob+.45*rng.standard_normal((G,G));cls[q(dark,SHARE[0])]=0                             # black blobs sit in the dark green
lite=noise(G*blk/(1617*.025),2)+1.1*rng.standard_normal((G,G));cls[q(lite,SHARE[3])]=3              # light speckle clouds
ref=np.asarray(Image.open(coat).convert('RGB').crop((1400,730,1760,1090))).reshape(-1,3).astype(float)   # real pixels per class
rc=((ref[:,None]-PAL[None])**2).sum(2).argmin(1);col=np.zeros((G,G,3))
for k in range(4):
    m_=cls==k;pool=ref[rc==k];col[m_]=pool[rng.integers(0,len(pool),m_.sum())]
tile=np.asarray(Image.fromarray(col.astype('uint8')).resize((int(G*blk),)*2,Image.NEAREST)).astype(float)[:N,:N]
print('shares',[round((cls==k).mean(),3) for k in range(4)])
b=np.asarray(Bk).astype(float);bb=np.asarray(Bk.filter(ImageFilter.GaussianBlur(24))).astype(float)
detail=np.clip(b/np.maximum(bb,1),.6,1.4)[...,None]
new=np.clip(tile*detail,0,255);Cv=np.asarray(C).astype(float)
res=(Cv*(1-M)+new*M).astype('uint8');Image.fromarray(res).save(out)
Image.fromarray((keep*255).astype('uint8')).save(out.replace('.png','_mask512.png'))
print('kept %.1f%% of texture'%(100*keep.mean()))
