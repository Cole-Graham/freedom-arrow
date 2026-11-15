"""Run lod2.py on the support jobs, 2 at a time (never more than 4 Blender on the deck), nice 10. Target = vanilla triangles,
but never below a third of the current count in this pass (Osama found 60k battle meshes too coarse)."""
import json,zipfile,subprocess,time,os
J=json.load(open('jobs.json'));B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender';L='/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.9/battle-lod/tools/lod2.py'
z=zipfile.ZipFile('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/0.8/FreedomArrow-0.9.0-dev.8-complete.bamod')
todo=[j for j in J if j['cut']];run=[]
for j in todo:
    open('in/'+j['file'],'wb').write(z.read('UserData/FAModels/'+j['file']))
    j['goal']=max(j['target'],j['now']//3)
def blenders():return int(subprocess.run(['pgrep','-c','-f','bin/blender'],capture_output=True,text=True).stdout.strip() or 0)
while todo or run:
    for j,p in [r for r in run if r[1].poll() is not None]:
        run.remove((j,p));print('done',j['file'],'goal',j['goal'],'rc',p.returncode,flush=True)
    if todo and len(run)<2 and blenders()<4:
        j=todo.pop(0);run.append((j,subprocess.Popen(['nice','-n','10',B,'-b','-P',L,'--','in/'+j['file'],'out/'+j['file'],str(j['goal'])],stdout=open('logs/'+j['file']+'.log','w'),stderr=subprocess.STDOUT)))
    time.sleep(3)
json.dump(J,open('jobs.json','w'),indent=1);print('ALLDONE',flush=True)
