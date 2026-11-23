"""Build52 over exact Build51: extra aircraft loadouts (Osama 12 Nov 05:41 PST).

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
BASE=json.loads((REL/'out/PLA-TEST-Build-51.json').read_text())['sha256']
lib=(ROOT/'tools/pla-specs/apply_build47_air.py').read_text()
exec(lib[lib.index('# ---- weapon catalogue'):lib.index('# ---- unit plan')])          # C, CANON, DROP, SLOTS
EXTRA={
 915:[{'PL-15':2,'PL-10':2,'LS-6':2},{'LT-2':4,'PL-10':2},{'YJ-91':2,'PL-15':2,'PL-10':2},{'PL-17':2,'PL-15':2,'PL-10':2}],
 966:[{'PL-15':2,'PL-10':2,'LS-6':2},{'LT-2':4,'PL-10':2},{'YJ-91':2,'PL-15':2,'PL-10':2},{'PL-17':2,'PL-15':2,'PL-10':2}],
 921:[{'PL-15':2,'LT-2':2},{'LS-6':4},{'YJ-91':2,'PL-15C':2},{'PL-15C':4,'PL-10':2}],
 971:[{'PL-15':2,'LT-2':2},{'LS-6':4},{'YJ-91':2,'PL-15C':2},{'PL-15C':4,'PL-10':2}],
 929:[{'PL-15C':4,'LS-6':4},{'YJ-91':4,'PL-15C':4},{'KD-88':4,'PL-15C':4},{'LT-2':6,'PL-15C':4},{'GB-6':4,'PL-15C':4}],
 944:[{'PL-15C':4,'LS-6':2,'PL-10':2},{'YJ-91':2,'PL-15C':4,'PL-10':2},{'LT-2':4,'PL-15C':2,'PL-10':2}],
 974:[{'YJ-91':4,'PL-15':2},{'PL-15':2,'PL-10':2,'YJ-91':2},{'PL-12':4,'PL-10':2},{'YJ-83K':2,'PL-12':2,'PL-10':2}],
 977:[{'YJ-91':4,'PL-15':2},{'PL-15':2,'PL-10':2,'YJ-91':2},{'PL-12':4,'PL-10':2},{'KD-88':2,'PL-12':2,'PL-10':2}],
 967:[{'LS-6':4},{'GB-6':2},{'KD-88':2},{'YJ-91':2}],
 946:[{'AKD-10':4,'LS-6':2},{'LS-6':4},{'AKD-9':8},{'LT-2':2}],
 1089:[{'PL-5E':2},{'57 mm rocket':32},{'250 kg bomb':2},{'90 mm rocket':14}],
 1091:[{'PL-5E':2},{'PL-5E':2,'57 mm rocket':16}],
 919:[{'CJ-10K':6},{'KD-88':4},{'YJ-83K':4}],
 1226:[{'PL-12':4,'PL-10':2},{'PL-12':2,'PL-10':2,'YJ-91':2}],
 975:[{'PL-12':2,'PL-9':2},{'PL-9':4}],
 1092:[{'PL-8':2,'250 kg bomb':2},{'PL-8':2,'57 mm rocket':36}],
 1104:[{'AKD-10':8,'TY-90':4},{'AKD-10':16},{'CM-501GA':8,'70 mm rocket':14}],
 941:[{'HJ-8':4,'57 mm rocket':36},{'TY-90':4,'57 mm rocket':36},{'AKD-9':4,'57 mm rocket':18}],
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
receipt={'build':52,'base_build':51,'base_sha256':BASE,'added':{}}
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
        if order>=8:break
        label=', '.join(f'{n}x {k}' for k,n in sorted(load.items(),key=lambda x:ORDER.index(C[x[0]]['cls'])))
        if label in labels:continue
        plan=assign(uid,load,stealth,heli);opt={k:(0 if k.startswith('Turret') else copy.deepcopy(v)) for k,v in OPT_T.items() if k!='Id'}
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
save('UserData/FreedomArrow/pla-build52.json',receipt)
(ROOT/'tools/pla-specs/build52-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
for k,v in receipt['added'].items():print(k,v['before'],'->',v['after'],'|',' / '.join(v['added']))
