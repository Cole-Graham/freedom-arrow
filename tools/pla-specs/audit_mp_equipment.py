"""Armory vs multiplayer equipment audit (Osama 13 Nov 22:58 PST, thread 1567745029781454889).
Runs the 0.7 SP/MP guards (memory sp-mp-build-guards; releases/0.7/build_constants.py) on a 0.8 package and reports faults that
vanilla does not already have; exits 1 if there are any. package_0_8_next.py runs it on every build.
usage: audit_mp_equipment.py PACKAGE.bamod VANILLA_DIR"""
import json,sys,zipfile,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
pkg,van=sys.argv[1],Path(sys.argv[2])
def load(patched):
    t={}
    z=zipfile.ZipFile(pkg) if patched else None
    for tab,fn in FIELD_TO_FILE.items():
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        if z:
            for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
                if v is None:t[tab].pop(int(k),None)
                else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    return t
FL=('IsRadar','IsSmoke','IsAPS','IsDecoy','IsLaserDesignator','IsResupplyAbility','IsSneakAbility','IsInfantrySprint','ECMAccuracyMultiplier')
def kind(a):return '+'.join(k[2:] if k.startswith('Is') else 'ECM' for k in FL if (a.get(k) and (k!='ECMAccuracyMultiplier' or a[k] not in (0,1,1.0)))) or 'none'
def faults(t):
    U,AB,UA,O,M,T,TU,TW,WA=(t[k] for k in ('Units','AbilitiesJson','UnitAbilitiesJson','OptionsJson','ModificationsJson','TurretsJson','TurretUnitsJson','TurretWeaponsJson','WeaponAmmunitionsJson'))
    shown={u for u,r in U.items() if r.get('DisplayInArmory')}
    f=set();mods={m['Id']:m['UnitId'] for m in M.values()}
    # 1. only the first default ability row loads (LoadAbility RVA 0x285E50)
    d=collections.defaultdict(list)
    for r in sorted(UA.values(),key=lambda r:r['Id']):
        if r['AbilityId'] in AB and AB[r['AbilityId']].get('IsDefault'):d[r['UnitId']].append(r)
    for u,rs in d.items():
        if len(rs)>1:
            first=kind(AB[rs[0]['AbilityId']]);lost=[kind(AB[r['AbilityId']]) for r in rs[1:]]
            f.add(('ability lost: only the first default ability loads',u,f'loads {first}; drops {"/".join(lost)}'))
    # 2. option abilities need a (unit, ability) UnitAbilities link
    ua={(r['UnitId'],r['AbilityId']) for r in UA.values()}
    for o in O.values():
        u=mods.get(o['ModificationId'])
        for k in ('Ability1Id','Ability2Id','Ability3Id'):
            a=o[k]
            if a and u is not None and (u,a) not in ua and AB.get(a,{}).get('Name')!='Empty ability':f.add(('option ability without unit link',u,f'option {o["Id"]} {o.get("UIName")}: {AB.get(a,{}).get("Name",a)}'))
            if a and a not in AB:f.add(('option ability row missing',u,f'option {o["Id"]} ability {a}'))
    # 3. turrets/weapons/ammo
    linked=collections.defaultdict(set);ammo=collections.defaultdict(set);weps=collections.defaultdict(set);chosen=collections.defaultdict(set)
    for r in TU.values():linked[r['UnitId']].add(r['TurretId'])
    for r in WA.values():ammo[r['UnitId']].add(r['WeaponId'])
    for r in TW.values():weps[r['TurretId']].add(r['WeaponId'])
    for o in O.values():
        for i in range(21):
            x=o.get(f'Turret{i}Id')
            if x and o['ModificationId'] in mods:chosen[mods[o['ModificationId']]].add(x)
    for u in set(linked)|set(chosen):
        ts=linked[u]
        for x in ts|chosen[u]:
            if x not in T:f.add(('missing turret row',u,x));continue
            sel=T[x]['IsDefault'] or x in chosen[u]
            p=T[x].get('ParentTurretId')
            if sel and p and p not in ts|chosen[u]:f.add(('selectable child turret without its parent on the unit',u,f'turret {x} {T[x]["Name"]} parent {p}'))
            if x in chosen[u] and x not in ts and x!=160:f.add(('option turret not linked to the unit (TurretUnits)',u,f'turret {x} {T[x]["Name"]}'))
            if sel:
                for w in weps[x]:
                    if w not in ammo[u]:f.add(('selectable weapon without an ammunition row',u,f'turret {x} weapon {w} {t["WeaponsJson"].get(w,{}).get("HUDName")}'))
    # 4. option ids travel as a signed short
    per=collections.defaultdict(list)
    for o in O.values():
        if o['Id']>32767:f.add(('option id above 32767 (network short)',mods.get(o['ModificationId']),o['Id']))
        per[o['ModificationId']].append(o)
    # (Zero default options per modification is normal: vanilla has 438 such modifications.)
    for o in O.values():
        if o['ModificationId'] not in M:f.add(('option of a missing modification',None,o['Id']))
    return {x for x in f if x[1] is None or x[1] in shown},U
new,U=faults(load(True));old,_=faults(load(False))
out=sorted(new-old,key=lambda x:(x[0],str(x[1])));pre=sorted(new&old,key=lambda x:(x[0],str(x[1])))
rep={'package':Path(pkg).name,'new_faults':[[a,b,U.get(b,{}).get('HUDName') if b else None,str(c)] for a,b,c in out],'vanilla_faults_also_present':len(pre),'by_kind':collections.Counter(x[0] for x in out)}
print(json.dumps(rep,indent=1,ensure_ascii=False))
sys.exit(1 if out else 0)
