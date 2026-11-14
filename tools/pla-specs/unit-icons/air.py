"""Aircraft unit icon (Osama 14 Nov): 3/4 view like the card picture, gear left out (SKIP), canopy cut out, a nose-cone line
and only the main contour lines. usage: air.py KEY fam AZ EL NOSEZ [MINLINE]
env SKIP (gear sub-meshes), CANOPY=blue|glass|none."""
import sys,os,subprocess
from PIL import Image,ImageFilter,ImageChops,ImageDraw
from collections import deque
KEY,FAM,AZ,EL,NZ=sys.argv[1:6];MINLINE=int(sys.argv[6]) if len(sys.argv)>6 else 400
D=os.path.dirname(os.path.abspath(__file__));B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender'
o=lambda n:f'{D}/out/FA_PLA_{KEY}_{n}.png'
passes={'sil':{'MODE':'sil'},'alb':{'MODE':'albedo'},'nose':{'MODE':'nose','NOSEZ':NZ},'lines':{'MODE':'sil','LINES':'1','LINE':os.environ.get('LINE','8'),'SKIP':os.environ.get('LSKIP',os.environ.get('SKIP',''))},'glass':{'MODE':'glass'}}
import time
def blenders():   # Blender processes on the whole deck (Sam 14 Nov 13:53: at most 4 at once)
    r=subprocess.run(['pgrep','-c','-f','bin/blender'],capture_output=True,text=True);return int(r.stdout.strip() or 0)
def render(names):   # at most 4 Blender at once, counting other jobs too
    todo=list(names);run=[]
    while todo or run:
        for n,p in [r_ for r_ in run if r_[1].poll() is not None]:
            assert p.returncode==0,f'render {n} failed';run.remove((n,p))
        if todo and len(run)<4 and blenders()<4:
            n=todo.pop(0);run.append((n,subprocess.Popen([B,'-b','-P',f'{D}/sil.py','--',FAM,o(n),AZ,EL],env=dict(os.environ,**passes[n]),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)))
        time.sleep(1)
render(['sil','glass','nose','lines'])
_g=Image.open(o('glass')).convert('RGBA')
if os.environ.get('CANOPY','auto') in ('auto','blue') and not ImageChops.multiply(_g.convert('L').point(lambda v:255 if v>127 else 0),_g.getchannel('A')).getbbox():render(['alb'])
sil=Image.open(o('sil')).getchannel('A').point(lambda v:255 if v>127 else 0)
def comps(m):
    W,H=m.size;px=m.load();seen=bytearray(W*H);out=[]
    for y in range(H):
        for x in range(W):
            if px[x,y] and not seen[y*W+x]:
                q=deque([(x,y)]);seen[y*W+x]=1;pts=[]
                while q:
                    cx,cy=q.popleft();pts.append((cx,cy))
                    for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                        nx,ny=cx+dx,cy+dy
                        if 0<=nx<W and 0<=ny<H and not seen[ny*W+nx] and px[nx,ny]:seen[ny*W+nx]=1;q.append((nx,ny))
                out.append(pts)
    return out
inner=sil.filter(ImageFilter.MinFilter(int(os.environ.get('INNER','41'))))   # lines hugging the outline are dropped
# contour lines: black Freestyle pixels well inside the body, short pieces dropped
li=Image.open(o('lines')).convert('RGBA');L=ImageChops.multiply(li.convert('L').point(lambda v:255 if v<100 else 0),inner)
keep=Image.new('L',L.size,0);kp=keep.load()
import math
nose0=Image.open(o('nose')).convert('L').point(lambda v:255 if v>127 else 0)
def centroid(m):
    pts=[(x,y) for y in range(0,m.height,4) for x in range(0,m.width,4) if m.getpixel((x,y))]
    return sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts)
DROPAXIS=float(os.environ.get('DROPAXIS','0'))   # drop lines within this many degrees of the fuselage axis (Flanker spine, Osama 14 Nov)
if DROPAXIS:
    (cx,cy),(nx_,ny_)=centroid(sil),centroid(nose0);axis=math.atan2(ny_-cy,nx_-cx)
for pts in comps(L):
    xs=[p[0] for p in pts];ys=[p[1] for p in pts]
    if DROPAXIS and len(pts)>50:
        mx,my=sum(xs)/len(xs),sum(ys)/len(ys);sxx=sum((x-mx)**2 for x in xs);syy=sum((y-my)**2 for y in ys);sxy=sum((x-mx)*(y-my) for x,y in pts)
        ang=0.5*math.atan2(2*sxy,sxx-syy);d=abs((ang-axis+math.pi/2)%math.pi-math.pi/2)
        if math.degrees(d)<DROPAXIS:continue
    if max(max(xs)-min(xs),max(ys)-min(ys))>=MINLINE:
        for p in pts:kp[p]=255
LM=os.environ.get('LINEMASK')   # keep only the contour lines at these sub-meshes (J-10: the canards, Osama 14 Nov)
if LM:
    passes['lmask']={'MODE':'glass','GLASSSUBS':LM,'ONLYSUBS':'1','GLASSONLY':''};render(['lmask'])
    lm=Image.open(o('lmask')).convert('RGBA');lm=ImageChops.multiply(lm.convert('L').point(lambda v:255 if v>127 else 0),lm.getchannel('A').point(lambda v:255 if v>127 else 0))
    keep=ImageChops.multiply(keep,lm.filter(ImageFilter.MaxFilter(41)))
# nose cone line: edge of the front section
nose=Image.open(o('nose')).convert('L').point(lambda v:255 if v>127 else 0)
nl=ImageChops.subtract(nose.filter(ImageFilter.MaxFilter(11)),nose);keep=ImageChops.lighter(keep,ImageChops.multiply(nl,sil.filter(ImageFilter.MinFilter(13))))
# canopy: largest blue area of the texture render (or glass parts), holes filled
mode=os.environ.get('CANOPY','auto');cut=None
if mode=='auto':   # flagged glass parts if the model has them, else the blue canopy paint
    _g=Image.open(o('glass')).convert('RGBA');mode='glass' if ImageChops.multiply(_g.convert('L').point(lambda v:255 if v>127 else 0),_g.getchannel('A')).getbbox() else 'blue'
if mode!='none':
    if mode=='blue':
        r,g,b,a=Image.open(o('alb')).convert('RGBA').split()
        m=ImageChops.multiply(ImageChops.subtract(b,r).point(lambda v:255 if v>45 else 0),a.point(lambda v:255 if v>127 else 0))
    else:
        gl=Image.open(o('glass')).convert('RGBA');m=ImageChops.multiply(gl.convert('L').point(lambda v:255 if v>127 else 0),gl.getchannel('A').point(lambda v:255 if v>127 else 0))
    m=m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5));cs=comps(m)
    if cs:
        cut=Image.new('L',m.size,0);cp=cut.load()
        big=max(len(c_) for c_ in cs);cs=[c_ for c_ in cs if len(c_)>=0.2*big]
        pick=[q for c_ in cs for q in c_] if mode=='glass' else max(cs,key=len) if os.environ.get('CANPICK')=='largest' else min(cs,key=lambda c_:sum(q[1] for q in c_)/len(c_))   # canopy on top; FH-97A: the EOTS (largest)
        for p in pick:cp[p]=255
        pad=Image.new('L',(cut.width+2,cut.height+2),0);pad.paste(cut,(1,1));ImageDraw.floodfill(pad,(0,0),128)
        cut=pad.crop((1,1,cut.width+1,cut.height+1)).point(lambda v:0 if v==128 else 255).filter(ImageFilter.MaxFilter(int(os.environ.get('CANGROW','9'))))
        cut=ImageChops.multiply(cut,sil.filter(ImageFilter.MinFilter(int(os.environ.get('CANRIM','35'))))) if os.environ.get('CANRIM')!='0' else cut;cut.save(o('cutf'))   # keep a body rim so the canopy is a window, not a notch
raw=Image.new('RGBA',sil.size,(0,0,0,0));raw.paste((255,255,255,255),mask=sil);raw.paste((0,0,0,255),mask=keep);raw.save(o('raw'))
args=[sys.executable,f'{D}/style.py',o('raw'),f'FA_PLA_{KEY}','380','180','0.6']+([o('cutf')] if cut else [])
subprocess.run(args,cwd=D,check=True,env=dict(os.environ,GAPFILL='0'))
I='/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/source/runtime-qa/icons'
for a_,b_ in ((f'{D}/out/FA_PLA_{KEY}-Label.png',f'{I}/FA_PLA_VEH_{KEY}.png'),(f'{D}/out/outline_FA_PLA_{KEY}-Label.png',f'{I}/FA_PLA_VEH_{KEY}_OUTLINE.png')):open(b_,'wb').write(open(a_,'rb').read())
open(f'{D}/list.txt','a').write(f'FA_PLA_{KEY} {os.path.basename(FAM)[:-4]} {AZ} {EL} air nose={NZ}\n');print('ok',KEY)
