"""tex_budget.py FAM BUDGET_MPX [MINPX]: fit a model's textures (colour + _n normal PNGs beside the .fam) into BUDGET_MPX, keeping the most
detail where the most surface is: repeatedly shrink (3/4 steps) the texture with the most pixels per square metre of surface it covers. Rule (Osama 24 Nov):
Armory textures about 1.5x vanilla (2048 colour + 1024 mask + 1024 normal = 6.3 Mpx -> 9.4 Mpx). Originals are kept in <dir>/tex_full/."""
import sys,os,shutil,numpy as np
from PIL import Image
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
fam,B=sys.argv[1],float(sys.argv[2])*1e6;MIN=int(sys.argv[3]) if len(sys.argv)>3 else 128;d=os.path.dirname(fam)
area={}
for _,subs in read_fam(fam):
    for sb in subs:
        if not sb['tex']:continue
        P=np.array(sb['pos']).reshape(-1,3);I=np.array(sb['idx']).reshape(-1,3)
        a=0.5*np.linalg.norm(np.cross(P[I[:,1]]-P[I[:,0]],P[I[:,2]]-P[I[:,0]]),axis=1).sum();area[sb['tex']]=area.get(sb['tex'],0)+a
orig={t:Image.open(os.path.join(d,'tex_full',t) if os.path.exists(os.path.join(d,'tex_full',t)) else os.path.join(d,t)).size for t in area}
size={t:Image.open(os.path.join(d,t)).size[0] for t in area}   # width; height keeps the source aspect
def hgt(t,s):return max(4,round(s*orig[t][1]/orig[t][0]/4)*4)
def px(t,s):return s*hgt(t,s)*(2 if os.path.exists(os.path.join(d,t[:-4]+'_n.png')) else 1)
while sum(px(t,s) for t,s in size.items())>B:
    t=max((t for t in size if size[t]*3//4>=MIN),key=lambda t:px(t,size[t])/max(area[t],1e-6))
    size[t]=max(MIN,int(size[t]*0.75)//64*64)   # 3/4 steps (2048 -> 1536 -> 1152 ...), multiples of 64
os.makedirs(os.path.join(d,'tex_full'),exist_ok=True)
for t,s in size.items():
    for f in (t,t[:-4]+'_n.png'):
        p=os.path.join(d,f)
        if not os.path.exists(p):continue
        k=os.path.join(d,'tex_full',f)
        if not os.path.exists(k):shutil.copy(p,k)
        im=Image.open(k)
        if im.size[0]!=s:im.resize((s,hgt(t,s)),Image.LANCZOS).save(p)
        else:shutil.copy(k,p)
print('BUDGET',round(sum(px(t,s) for t,s in size.items())/1e6,2),'Mpx',{t.split('_tex')[1][:-4]:(s,round(area[t],1)) for t,s in sorted(size.items(),key=lambda x:-area[x[0]])})
