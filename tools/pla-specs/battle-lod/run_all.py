"""Rebuild every China battle mesh over LIMIT triangles (Osama 14 Nov 16:28 PST). 2 Blender at a time, nice 10."""
import json,zipfile,sys,os,subprocess,time
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender'
LIMIT=int(os.environ.get('LIMIT','60000'))
z=zipfile.ZipFile('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/0.8/FreedomArrow-0.9.0-dev.2-complete.bamod');m=json.loads(z.read('UserData/FAModels/models.json'));N=set(z.namelist())
tris=dict((k,t) for t,k in json.load(open('/tmp/d35/battle_tris.json')))
jobs={}
for k,v in m.items():
    f=v.get('battle')
    if f and tris.get(k,0)>LIMIT and f not in jobs:jobs[f]=k
print('jobs',len(jobs),flush=True)
def blenders():return int(subprocess.run(['pgrep','-c','-f','bin/blender'],capture_output=True,text=True).stdout.strip() or 0)
run=[];todo=list(jobs.items());res={}
while todo or run:
    for f,p in [x for x in run if x[1].poll() is not None]:
        run.remove((f,p));o=f'{D}/out/{f}'
        try:
            a=read_fam(f'{D}/src/{f}');b=read_fam(o)
            ta=sum(len(s['idx'])//3 for _,ss in a for s in ss);tb=sum(len(s['idx'])//3 for _,ss in b for s in ss)
            ext=lambda P:[(min(x[i::3]),max(x[i::3])) for x in [[c for _,ss in P for s in ss for c in s['pos']]] for i in range(3)]
            ea,eb=ext(a),ext(b);dev=max(abs(ea[i][j]-eb[i][j]) for i in range(3) for j in range(2))
            res[f]={'unit':jobs[f],'tris':[ta,tb],'parts_same':[x[0] for x in a]==[x[0] for x in b],'bbox_dev':round(dev,3),'bytes':[os.path.getsize(f'{D}/src/{f}'),os.path.getsize(o)],'rc':p.returncode}
        except Exception as e:res[f]={'unit':jobs[f],'error':str(e),'rc':p.returncode}
        print('done',f,res[f],flush=True)
    if todo and len(run)<2 and blenders()<4:
        f,k=todo.pop(0);stem=f[:-4]
        for n in N:
            if n.startswith('UserData/FAModels/'+stem+'.') or n.startswith('UserData/FAModels/'+stem+'_tex'):
                t=f'{D}/src/'+n.split('/')[-1]
                if not os.path.exists(t):open(t,'wb').write(z.read(n))
        run.append((f,subprocess.Popen(['nice','-n','10',B,'-b','-P',f'{D}/tools/lod.py','--',f'{D}/src/{f}',f'{D}/out/{f}',str(LIMIT)],stdout=open(f'{D}/out/{stem}.log','w'),stderr=subprocess.STDOUT)))
    time.sleep(1)
json.dump(res,open(f'{D}/out/results.json','w'),indent=1);print('ALLDONE',flush=True)
