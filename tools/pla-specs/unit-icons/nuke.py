"""Add the vanilla nuclear trefoil (from DLC3_MIG31_NUKE-Label) to a finished label pair, top right above the vehicle."""
from PIL import Image
from collections import deque
import sys
name=sys.argv[1]
D='/home/sam/tars/work/ba-dev/replicas/codex/work/assetripper-20261107/export-dlc3-primary/Assets/Resources_moved/Images/Labels/DLC3/'
def trefoil(path):
    im=Image.open(path).convert('RGBA');A=im.getchannel('A');px=A.load();W,H=im.size;seen=set();best=[]
    for y in range(H):
        for x in range(W):
            if px[x,y]>40 and (x,y) not in seen:
                q=deque([(x,y)]);seen.add((x,y));pts=[]
                while q:
                    cx,cy=q.popleft();pts.append((cx,cy))
                    for dx in(-1,0,1):
                        for dy in(-1,0,1):
                            n=(cx+dx,cy+dy)
                            if 0<=n[0]<W and 0<=n[1]<H and n not in seen and px[n]>40:seen.add(n);q.append(n)
                if sum(p[0] for p in pts)/len(pts)>W*0.7 and sum(p[1] for p in pts)/len(pts)<H*0.6:best+=pts
    xs=[p[0] for p in best];ys=[p[1] for p in best];return im.crop((min(xs)-4,min(ys)-4,max(xs)+6,max(ys)+6))
for kind,lab in (('',D+'DLC3_MIG31_NUKE-Label.png'),('outline_',D+'outline/DLC3_MIG31_NUKE-Label.png')):
    icon=Image.open(f'out/{kind}{name}-Label.png').convert('RGBA');top=icon.getchannel('A').point(lambda v:255 if v>60 else 0).getbbox()[1]
    th=72;t=trefoil(lab);t=t.resize((round(t.width*th/t.height),th),Image.LANCZOS)
    icon.alpha_composite(t,(416-t.width-6,max(4,top-th-4)));icon.save(f'out/{kind}{name}-Label.png')
a=Image.open(f'out/{name}-Label.png');b=Image.open(f'out/outline_{name}-Label.png')
s=Image.new('RGBA',(832,216),(60,60,60,255));s.alpha_composite(a,(0,0));s.alpha_composite(b,(416,0));s.save(f'out/{name}_preview.png')
