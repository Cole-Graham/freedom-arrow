"""Support tab armory textures near vanilla size (Osama 14 Nov 2026 22:5x PST "bring support textures down to near vanilla size too").
Vanilla support unit = one 2048x2048 colour map + 1024 mask + 1024 normal = 6.3 Mpx (work/texture-audit-20261114/vanilla.json).
Every support armory model (support-lod/jobs.json) goes to at or under BUDGET Mpx (colour+mask+normal) by halving its largest
texture first, never below MINPX. Source sizes: the PNGs in Assets 0.2.32. Output in the plan format of armory-opt/plan_tex.json.
usage: plan.py ASSETS.bamod OUT.json [BUDGET_MPX] [MINPX]"""
import sys,zipfile,struct,json,os
z=zipfile.ZipFile(sys.argv[1]);names=set(z.namelist());D='UserData/FAModels/'
B=float(sys.argv[3]) if len(sys.argv)>3 else 6.3;MIN=int(sys.argv[4]) if len(sys.argv)>4 else 256
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
J=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../support-lod/jobs.json')))
SL='/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.9/support-lod/'
def dims(p):
    with z.open(p) as f:h=f.read(24)
    return struct.unpack('>II',h[16:24])
use={}
for j in J:
    f=j['file'];src=SL+('out/' if j['cut'] else 'in/')+f
    if not os.path.exists(src):open('/tmp/_sup.fam','wb').write(z.read(D+f) if D+f in names else b'');src='/tmp/_sup.fam'
    try:parts=read_fam(src)
    except Exception as e:print('skip',f,e);continue
    t=set()
    for _,subs in parts:
        for s in subs:
            if s['tex']:st=s['tex'][:-4];t|={y for y in (s['tex'],st+'_n.png',st+'_mask.png') if D+y in names}
    use[f]=t
size={t:dims(D+t) for ts in use.values() for t in ts};new=dict(size)
px=lambda f:sum(new[t][0]*new[t][1] for t in use[f])/1e6
before={f:px(f) for f in use}
for f in sorted(use,key=lambda f:-before[f]):
    while px(f)>B:
        t=max((t for t in use[f] if min(new[t])>MIN),key=lambda t:new[t][0]*new[t][1],default=None)
        if t is None:break
        new[t]=(new[t][0]//2,new[t][1]//2)
changed={t:[size[t],new[t]] for t in new if new[t]!=size[t]}
json.dump({'budget_mpx':B,'min_px':MIN,'models':{f:[round(before[f],1),round(px(f),1),len(use[f])] for f in use},'textures':changed},open(sys.argv[2],'w'),indent=1)
for f in use:print(f'{f:24s} {len(use[f]):2d} tex {before[f]:5.1f} -> {px(f):4.1f} Mpx')
print('models',len(use),'textures to shrink',len(changed),'total Mpx',round(sum(before.values()),1),'->',round(sum(px(f) for f in use),1))
