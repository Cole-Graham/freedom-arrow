"""Armory textures, colour first (Osama 14 Nov 2026 23:2x PST: "we over did some of the optimization for tanks", "VT-5 looks
really bad", "I think its really important for units to look good in the armory", "we can increase the load a bit").
Every non-support armory model (models.json 'file') at or under BUDGET Mpx (colour+mask+normal). Shrink order: mask maps, then
normal maps (largest first, never below 1024 while colour is untouched), then colour maps. Colour maps are capped at 2048
(the vanilla colour size). Support models keep support-tex/plan_tex.json. Source sizes: PNGs of Assets 0.2.32.
usage: plan.py ASSETS.bamod COMPLETE.bamod OUT.json [BUDGET_MPX]"""
import sys,zipfile,struct,json,os
A=zipfile.ZipFile(sys.argv[1]);C=zipfile.ZipFile(sys.argv[2]);names=set(A.namelist());D='UserData/FAModels/';B=float(sys.argv[4]) if len(sys.argv)>4 else 25.0
SUP=set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../support-tex/plan_tex.json')))['models'])
def dims(p):
    with A.open(p) as f:h=f.read(24)
    return struct.unpack('>II',h[16:24])
def texs(fam):
    b=C.read(D+fam);o=4;np_=struct.unpack_from('<i',b,o)[0];o+=4;out=set()
    def s():
        nonlocal o;n=struct.unpack_from('<i',b,o)[0];o+=4;r=b[o:o+n].decode('utf8','replace');o+=n;return r
    for _ in range(np_):
        s();ns=struct.unpack_from('<i',b,o)[0];o+=4
        for _ in range(ns):
            t=s();o+=16;nv=struct.unpack_from('<i',b,o)[0];o+=4+nv*32;ni=struct.unpack_from('<i',b,o)[0];o+=4+ni*4
            if t:st=t[:-4];out|={y for y in (t,st+'_n.png',st+'_mask.png') if D+y in names}
    return out
m=json.loads(C.read(D+'models.json'));N=set(C.namelist())
files=sorted({v['file'] for v in m.values() if v.get('file') and D+v['file'] in N and v['file'] not in SUP})
use={f:texs(f) for f in files};size={t:dims(D+t) for ts in use.values() for t in ts}
kind=lambda t:'mask' if t.endswith('_mask.png') else 'n' if t.endswith('_n.png') else 'col'
new={t:(w,h) for t,(w,h) in size.items()}
for t,(w,h) in size.items():   # colour cap 2048
    if kind(t)=='col':
        while max(new[t])>2048:new[t]=(new[t][0]//2,new[t][1]//2)
px=lambda f:sum(new[t][0]*new[t][1] for t in use[f])/1e6
before={f:sum(size[t][0]*size[t][1] for t in use[f])/1e6 for f in files}
for f in sorted(files,key=lambda f:-px(f)):
    for k,floor in (('mask',1024),('n',1024),('mask',512),('n',512),('col',512)):
        while px(f)>B:
            t=max((t for t in use[f] if kind(t)==k and min(new[t])>floor),key=lambda t:new[t][0]*new[t][1],default=None)
            if t is None:break
            new[t]=(new[t][0]//2,new[t][1]//2)
changed={t:[size[t],new[t]] for t in new if new[t]!=size[t]}
json.dump({'budget_mpx':B,'models':{f:[round(before[f],1),round(px(f),1)] for f in files},'textures':changed},open(sys.argv[3],'w'),indent=1)
col_cut=[t for t in changed if kind(t)=='col' and max(changed[t][1])<min(2048,max(changed[t][0]))]
print('armory files',len(files),'textures shrunk',len(changed),'colour maps below min(source,2048):',len(col_cut),'still over',[f for f in files if px(f)>B+0.01][:8])
print('total Mpx',round(sum(before.values())),'->',round(sum(px(f) for f in files)))
