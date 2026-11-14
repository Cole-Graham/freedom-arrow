"""Run air.py for a list of aircraft: extract model + textures from the package, find landing gear sub-meshes, set the nose line."""
import json,zipfile,sys,os,subprocess
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
D=os.path.dirname(os.path.abspath(__file__))
z=zipfile.ZipFile('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/0.8/FreedomArrow-0.9.0-dev.1-complete.bamod');m=json.loads(z.read('UserData/FAModels/models.json'))
jobs=json.loads(sys.argv[1])   # [[KEY, models.json key, AZ, EL, extra env], ...]
for KEY,MK,AZ,EL,env in jobs:
    f=m[MK]['file'];stem=f[:-4]
    for n in z.namelist():
        if n.startswith('UserData/FAModels/'+stem) and not n.endswith(('_n.png','_mask.png')):open(f'{D}/fam/'+n.split('/')[-1],'wb').write(z.read(n))
    subs=[sb for bone,ss in read_fam(f'{D}/fam/{f}') for sb in ss]
    box=lambda sb:[(min(sb['pos'][i::3]),max(sb['pos'][i::3])) for i in range(3)]
    B=[box(s) for s in subs];big=max(range(len(subs)),key=lambda i:len(subs[i]['pos']))
    ymin=min(b[1][0] for b in B);ymax=max(b[1][1] for b in B);zmin=min(b[2][0] for b in B);zmax=max(b[2][1] for b in B);L=zmax-zmin;H=ymax-ymin
    by=B[big][1][0]
    gear=[i for i,b in enumerate(B) if i!=big and b[1][1]<by+0.12*H+0.02*L and b[1][0]<by-0.01*L and max(b[0][1]-b[0][0],b[2][1]-b[2][0])<0.2*L]
    nz=zmax-float(env.pop('NOSEF','0.09'))*L
    print(KEY,f,'subs',len(subs),'gear',gear,'nose',round(nz,2),flush=True)
    e=dict(os.environ,GEARCUT='1',**env)
    r=subprocess.run([sys.executable,f'{D}/air.py',KEY,f'{D}/fam/{f}',str(AZ),str(EL),str(nz),env.get('MINLINE',os.environ.get('MINLINE','300'))],env=e,capture_output=True,text=True)
    print(' ',r.stdout.strip()[-80:],r.stderr.strip()[-300:],flush=True)
