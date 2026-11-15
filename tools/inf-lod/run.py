"""Cut every dev.11 infantry body over budget (LOD0 28k, LOD1 7k, LOD2 3k triangles; files within 5% are kept), at most 4 Blender at once."""
import json,subprocess,sys,os,re
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'.');import fas
B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender';BUD={0:28000,1:7000,2:3000}
rules=json.load(open('rules-dev11.json'));lvl={}
for r in rules:
    for i,f in enumerate(r['lods']):lvl[f]=i
os.makedirs('out',exist_ok=True);jobs=[];plan={}
for f,l in sorted(lvl.items()):
    t=fas.tris(fas.read('orig/'+f)[1]);cut=t>BUD[l]*1.05;plan[f]={'lod':l,'before':t,'target':BUD[l] if cut else None}
    if cut:jobs.append((f,BUD[l]))
def go(j):
    f,tg=j;r=subprocess.run([B,'-b','-P','decimate_fas.py','--','orig/'+f,'out/'+f,str(tg)],capture_output=True,text=True)
    m=re.search(r'FASCUT .*',r.stdout);return f,(m.group(0) if m else 'FAILED '+r.stdout[-500:]+r.stderr[-500:])
with ThreadPoolExecutor(4) as ex:
    for f,msg in ex.map(go,jobs):
        print(msg,flush=True)
        if os.path.exists('out/'+f):plan[f]['after']=fas.tris(fas.read('out/'+f)[1])
json.dump(plan,open('plan.json','w'),indent=1)
print('cut',len(jobs),'of',len(plan))
