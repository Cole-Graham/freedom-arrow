"""VEH / Helo / Air armory textures at source size, each capped at 2048 (Osama 14 Nov 2026 23:4x PST: "VEH, Helo and Air tab units
need to look good, thats the priority, as long as they don't take me more than 0.3 seconds to load"). dev.7 shipped source-size
textures and measured <= 0.29 s first load on his PC for every VEH/Helo/Air model except CTL-181 (0.37 s), which keeps the
colour-first 30 Mpx plan (armory-tex2). Other tabs keep their dev.9 textures. Tab = units.json CategoryType (2 VEH, 5 Helo, 6 Air).
usage: plan.py ASSETS-0.2.32.bamod DEV9-COMPLETE.bamod DEV7-COMPLETE.bamod OUT.json"""
import sys,zipfile,struct,json,collections
A,C,S7=(zipfile.ZipFile(p) for p in sys.argv[1:4]);D='UserData/FAModels/';NA=set(A.namelist());N9=set(C.namelist());N7=set(S7.namelist())
u=json.loads(C.read('UserData/FreedomArrow/constants/units.json'));m=json.loads(C.read(D+'models.json'))
cat=collections.defaultdict(set)
for v in u.values():
    if isinstance(v,dict) and v.get('Name'):cat[v['Name']].add(v.get('CategoryType'))
P30=json.load(open('../armory-tex2/plan_30.json'))['textures'];SLOW={'m_ctl181_static.fam'}
def pdims(p):
    with A.open(p) as f:h=f.read(24)
    return list(struct.unpack('>II',h[16:24]))
def fdims(z,p):
    with z.open(p) as f:h=f.read(28)
    return list(struct.unpack_from('<2i',h,4))
def texs(fam):
    b=C.read(D+fam);o=4;np_=struct.unpack_from('<i',b,o)[0];o+=4;out=set()
    def s():
        nonlocal o;n=struct.unpack_from('<i',b,o)[0];o+=4;r=b[o:o+n].decode('utf8','replace');o+=n;return r
    for _ in range(np_):
        s();ns=struct.unpack_from('<i',b,o)[0];o+=4
        for _ in range(ns):
            t=s();o+=16;nv=struct.unpack_from('<i',b,o)[0];o+=4+nv*32;ni=struct.unpack_from('<i',b,o)[0];o+=4+ni*4
            if t:st=t[:-4];out|={y for y in (t,st+'_n.png',st+'_mask.png') if D+y in NA}
    return out
fams=collections.defaultdict(set)
for k,v in m.items():
    if v.get('file') and D+v['file'] in N9:fams[v['file']]|=cat.get(k,set())
sel=sorted(f for f,c in fams.items() if c&{2,5,6})
plan={};src7=0;regen=0;mpx9=mpx_new=0
for f in sel:
    for t in texs(f):
        s=pdims(D+t)
        if f in SLOW:new=list(P30[t][1]) if t in P30 else s
        else:
            new=list(s)
            while max(new)>2048:new=[new[0]//2,new[1]//2]
        new=[max(4,(x+3)//4*4) for x in new]
        fat=D+t[:-4]+'.fat';cur=fdims(C,fat) if fat in N9 else None
        if cur==new:continue
        use7=fat in N7 and fdims(S7,fat)==new
        plan[t]=[s,new,'dev7' if use7 else 'regen'];src7+=use7;regen+=not use7
json.dump({'models':sel,'textures':plan},open(sys.argv[4],'w'),indent=1)
print('VEH/Helo/Air armory models',len(sel),'textures to change',len(plan),'from dev.7',src7,'regenerate',regen)
