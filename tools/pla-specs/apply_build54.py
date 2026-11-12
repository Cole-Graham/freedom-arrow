"""Build54 over exact Build53: LD-8A and PL-16 for stealth jets; J-16 heavy bomb load (Osama 12 Nov 11:05).

- LD-8A: PL-15-based anti-radiation missile for internal bays (copies the game's AGM-88 HARM).
- PL-16: PL-15 clone (same statistics, AIM-260 analog) carried 6 in a bay that holds 4 PL-15.
- J-16: 32x 250 kg bombs + 2x PL-15 + 2x PL-10.
Loadout menus may now hold up to 10 options.

Original Build52 notes:

"I'd rather you add extra loadouts than be cautious and not add them."
Aircraft that CMO gives few loadouts get extra realistic ones (EXTRA), appended to their existing
loadout menu. Stealth jets still use internal bays only; recon helicopters stay rockets-only.
Uses the Build47 weapon catalogue, pylon layouts and pricing (apply_build47_air.py).
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-53.json').read_text())['sha256']
lib=(ROOT/'tools/pla-specs/apply_build47_air.py').read_text()
exec(lib[lib.index('# ---- weapon catalogue'):lib.index('# ---- unit plan')])          # C, CANON, DROP, SLOTS
C['PL-16']=dict(C['PL-15'],cost=22.5)
C['LD-8A']=dict(ammo=298,w=395,vis={1:'Weapon/R77/R77'},pic='AGM88_HARM',cost=40,cls='agm')
EXTRA={
 915:[{'PL-16':6,'PL-10':2},{'LD-8A':4,'PL-10':2},{'LD-8A':2,'PL-15':2,'PL-10':2}],
 966:[{'PL-16':6,'PL-10':2},{'LD-8A':4,'PL-10':2},{'LD-8A':2,'PL-15':2,'PL-10':2}],
 921:[{'PL-16':6},{'LD-8A':4},{'LD-8A':2,'PL-15':2}],
 971:[{'PL-16':6},{'LD-8A':4},{'LD-8A':2,'PL-15':2}],
 944:[{'PL-16':6,'PL-10':2},{'LD-8A':4,'PL-10':2}],
 929:[{'PL-16':8,'PL-10':2},{'LD-8A':6,'PL-15C':4}],
 916:[{'250 kg bomb':32,'PL-15':2,'PL-10':2}],
}
STRIKE={918,919,967,946}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];T=t['TurretsJson']
exec(lib[lib.index('ammo_rows={};'):lib.index('# ---- per aircraft')])            # ammo/weapon/turret/assign helpers
for x in A.values():                                                                  # reuse the Build47 ammunition library
    m=re.fullmatch(r'PLA air (.+?)( heli)?',x.get('Name') or '')
    if m and m.group(1) in C:ammo_rows[(m.group(1),bool(m.group(2)))]=x['Id']
cmo=json.loads((ROOT/'tools/pla-specs/cmo-air-loadouts.json').read_text())
air=json.loads(z.read('UserData/FreedomArrow/pla-air-loadouts.json'))
ORDER='bvr ir heliaa agm bomb atgm rocket'.split()
receipt={'build':54,'base_build':53,'base_sha256':BASE,'added':{}}
for uid,extras in EXTRA.items():
    u=U[uid];heli=u['Type']==8;stealth=cmo.get(str(uid),{}).get('stealth_internal_only',False)
    mods=[m for m in t['ModificationsJson'].values() if m['UnitId']==uid and m['Type']==3 and m['Name'].startswith('PLA loadout')]
    existing=[o for o in t['OptionsJson'].values() if mods and o['ModificationId']==mods[0]['Id']]
    if mods:mid=mods[0]['Id']
    else:
        for r in g.rows('TurretUnitsJson',uid):
            tr=T[r['TurretId']]
            if not(tr['ModelFileName'] is None and tr['IsDefault']):
                for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tr['Id']]:
                    for wa in [x for x in g.rows('WeaponAmmunitionsJson',uid) if x['WeaponId']==tw['WeaponId']]:g.remove('WeaponAmmunitionsJson',wa['Id'])
                g.remove('TurretUnitsJson',r['Id'])
        mid=g.add('ModificationsJson',MOD_T,{'UnitId':uid,'Name':'PLA loadout '+u['HUDName'],'Type':3,'UIName':'Custom_Slot_Weapon_package','ThumbnailFileName':None,'Order':0})
    labels={o['UIName'] for o in existing};order=len(existing);added=[];used_t=set();used_w=set()
    for load in extras:
        if order>=10:break
        label=', '.join(f'{n}x {k}' for k,n in sorted(load.items(),key=lambda x:ORDER.index(C[x[0]]['cls'])))
        if label in labels:continue
        plan=assign(uid,load,stealth,heli);opt={k:(None if k.startswith('Turret') else copy.deepcopy(v)) for k,v in OPT_T.items() if k!='Id'}
        for (s,kind),parts in plan.items():
            tid=turret(parts,heli,kind);opt[f'Turret{s}Id']=tid;used_t.add(tid)
            for n,q in parts:used_w.add((weapon(n,q,heli),ammo(n,heli),q))
        raw=sum(C[k]['cost']*n for k,n in load.items());raw=raw if raw<=150 else 150+(raw-150)/2;ocost=int(round(raw/5.0)*5)
        main=max(load,key=lambda k:C[k]['cost']*load[k])
        opt.update(ModificationId=mid,Name=f'PLA loadout {u["HUDName"]} x{order}',Order=order,UIName=label,Cost=ocost,OptionPicture=C[main]['pic'],IsDefault=not existing and order==0)
        g.add('OptionsJson',OPT_T,opt);labels.add(label);order+=1;added.append(f'{label} ({ocost})')
    for tid in sorted(used_t):
        if not any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':tid,'Order':0})
    for wid,aid,q in sorted(used_w):
        if not any(r['WeaponId']==wid for r in g.rows('WeaponAmmunitionsJson',uid)):g.add('WeaponAmmunitionsJson',WA_T,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
    receipt['added'][f"{u['HUDName']} ({uid})"]={'before':len(existing),'after':order,'added':added}
# checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in EXTRA:
    for m in [m for m in t['ModificationsJson'].values() if m['UnitId']==uid and m['Type']==3]:
        os_=[o for o in t['OptionsJson'].values() if o['ModificationId']==m['Id']]
        ok(sum(bool(o['IsDefault']) for o in os_)==1 and all(o['Id']<=32767 for o in os_),('options',uid))
        for o in os_:
            for i in range(21):
                tid=o.get(f'Turret{i}Id')
                if not tid:continue
                if cmo.get(str(uid),{}).get('stealth_internal_only'):ok(dict(SLOTS[U[uid]['ModelFileName']]).get(i) in('b','s'),('stealth external',uid,i))
                ok(any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)),('turret link',uid,tid))
                for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tid]:ok(any(r['WeaponId']==tw['WeaponId'] for r in g.rows('WeaponAmmunitionsJson',uid)),('ammo row',uid,tw['WeaponId']))
for uid,u in before['Units'].items():ok(t['Units'][uid]==u,('unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-build54.json',receipt)
(ROOT/'tools/pla-specs/build54-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
for k,v in receipt['added'].items():print(k,v['before'],'->',v['after'],'|',' / '.join(v['added']))
