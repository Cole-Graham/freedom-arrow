"""One unit icon end to end: model from the package's models.json (by card Name), render, style, install, list cards.
usage: do_icon.py KEY "models.json key" "HUD prefix" [AZ EL] [SKIP]"""
import json,zipfile,subprocess,sys,os
from pathlib import Path
KEY,MK,HUD=sys.argv[1:4];AZ=sys.argv[4] if len(sys.argv)>4 else '0';EL=sys.argv[5] if len(sys.argv)>5 else '0';SKIP=sys.argv[6] if len(sys.argv)>6 else ''
W=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree');D=Path(__file__).parent
z=zipfile.ZipFile(W/'mod/out/0.8/FreedomArrow-0.9.0-dev.1-complete.bamod');m=json.loads(z.read('UserData/FAModels/models.json'))
f=m[MK]['file'];(D/'fam'/f).write_bytes(z.read('UserData/FAModels/'+f))
mj='UserData/FAModels/'+f[:-4]+'.mat.json'
if mj in z.namelist():(D/'fam'/(f[:-4]+'.mat.json')).write_bytes(z.read(mj))
env=dict(os.environ,SKIP=SKIP)
subprocess.run(['/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender','-b','-P',str(D/'sil.py'),'--',str(D/'fam'/f),str(D/f'out/FA_PLA_{KEY}_raw.png'),AZ,EL],env=env,capture_output=True,check=True)
sargs=[]
if os.environ.get('GLASS'):   # cut the glass out: white glass render -> mask with the gaps between panes filled
    from PIL import Image,ImageDraw
    subprocess.run(['/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender','-b','-P',str(D/'sil.py'),'--',str(D/'fam'/f),str(D/f'out/FA_PLA_{KEY}_glass.png'),AZ,EL],env=dict(env,MODE='glass'),capture_output=True,check=True)
    g=Image.open(D/f'out/FA_PLA_{KEY}_glass.png').convert('RGBA');c=Image.eval(g.convert('L'),lambda v:255 if v>127 else 0)
    c=Image.composite(c,Image.new('L',c.size,0),g.getchannel('A').point(lambda v:255 if v>127 else 0))
    pad=Image.new('L',(c.width+2,c.height+2),0);pad.paste(c,(1,1));ImageDraw.floodfill(pad,(0,0),128)
    pad.crop((1,1,c.width+1,c.height+1)).point(lambda v:0 if v==128 else 255).save(D/f'out/FA_PLA_{KEY}_cutf.png')
    sargs=['380','180','1.2',str(D/f'out/FA_PLA_{KEY}_cutf.png')]
subprocess.run([sys.executable,str(D/'style.py'),str(D/f'out/FA_PLA_{KEY}_raw.png'),f'FA_PLA_{KEY}',*sargs],cwd=D,check=True)
I=W/'mod/source/runtime-qa/icons'
(I/f'FA_PLA_VEH_{KEY}.png').write_bytes((D/f'out/FA_PLA_{KEY}-Label.png').read_bytes());(I/f'FA_PLA_VEH_{KEY}_OUTLINE.png').write_bytes((D/f'out/outline_FA_PLA_{KEY}-Label.png').read_bytes())
with open(D/'list.txt','a') as l:l.write(f'FA_PLA_{KEY} {f[:-4]} {AZ} {EL}\n')
print('model',f)
