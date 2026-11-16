"""Fail a build whose finished package is missing queued Lateralus changes (16 Nov 2026, thread 1571554273639006392).
Why: the SPAAG/SAM data queued for 0.9.0-dev.13 was in the commit but never in any package dev.13-dev.24 (its data step ran without the
section), and nothing noticed. From 0.9.0-dev.25 on, package_0_8_next.py runs this on the complete package:
- every SPAAG/SAM value in spaag_sead_data.py is in the merged weapon and ammo tables;
- the plane sale ships: UserData/FreedomArrow/plane-refund.json and the plane_sale / server_money hooks in the runtime DLL;
- from 0.9.0-dev.26: the M-SHORAD APKWS laser is in ability slot 2, no unit has two modifications filling one ability slot, and the runtime has
  altitude intent, SEAD overkill (sead-overkill.json), SEAD re-target, lobby tabs and the deployment/menu overlay fixes.
Usage: queued_checks.py COMPLETE.bamod VERSION VANILLA_DIR"""
import json,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import spaag_sead_data as S,sead_prices as SP,ecm_pods as EP,mshorad as MS
pkg,V,van=sys.argv[1],sys.argv[2],Path(sys.argv[3])
m=re.match(r'0\.(\d+)\.0-dev\.(\d+)',V)
if not m or (int(m.group(1)),int(m.group(2)))<(9,25):print('queued_checks: not required before 0.9.0-dev.25');sys.exit(0)
z=zipfile.ZipFile(pkg);bad=[]
def merged(tab,fn):
    t={r['Id']:dict(r) for r in json.loads((van/tab).read_text())}
    for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
        if v is None:t.pop(int(k),None)
        else:t.setdefault(int(k),{'Id':int(k)}).update(v)
    return t
for tab,fn,spec in (('WeaponsJson.json','weapons.json',S.SPW),('AmmunitionsJson.json','ammunitions.json',S.SPA)):
    t=merged(tab,fn)
    bad+=[f'{tab} {i} {k}={t.get(int(i),{}).get(k)} (want {n})' for i,f in spec.items() for k,(o,n) in f.items() if t.get(int(i),{}).get(k)!=n]
Ut=merged('Units.json','units.json');Ot=merged('OptionsJson.json','options.json');At=merged('AbilitiesJson.json','abilities.json')
bad+=[f'unit {i} {n} cost {Ut.get(i,{}).get("Cost")} (want {new})' for i,(n,old,new) in SP.UNITS.items() if Ut.get(i,{}).get('Cost')!=new]
bad+=[f'option {i} {n} cost {Ot.get(i,{}).get("Cost")} (want {new})' for i,(u,n,old,new) in SP.OPTIONS.items() if (Ot.get(i,{}).get('Cost') or 0)!=new]
for i,want in EP.EXPECT.items():
    got=[At.get(Ot.get(i,{}).get(f'Ability{k}Id'),{}).get('ECMAccuracyMultiplier') for k in (1,2,3)]
    if not any(g is not None and abs(g-want)<1e-6 for g in got):bad.append(f'ECM option {i} multipliers {got} (want {want})')
for i,want in EP.EXPECT_NOPOD.items():
    got=[At.get(Ot.get(i,{}).get(f'Ability{k}Id'),{}).get('ECMAccuracyMultiplier') for k in (1,2,3)]
    if not any(g is not None and abs(g-want)<1e-6 for g in got):bad.append(f'no-pod ECM option {i} multipliers {got} (want {want})')
UAt=merged('UnitAbilitiesJson.json','unit_abilities.json')
for name,want in EP.EXPECT_DEFAULT.items():
    uid=[k for k,v in Ut.items() if v.get('Name')==name]
    got=[At.get(x.get('AbilityId'),{}) for x in UAt.values() if uid and x.get('UnitId')==uid[0]]
    if not any(a.get('IsDefault') and a.get('ECMAccuracyMultiplier') is not None and abs(a['ECMAccuracyMultiplier']-want)<1e-6 for a in got):bad.append(f'{name} default ECM is not {want}')
bad+=[f'M-SHORAD option {i} cost {Ot.get(i,{}).get("Cost")} (want {new})' for i,(n,old,new) in MS.PRICES.items() if Ot.get(i,{}).get('Cost')!=new]
if (int(m.group(1)),int(m.group(2)))<(9,26):
    if Ot.get(1937,{}).get('Ability1Id')!=MS.LASER:bad.append('M-SHORAD APKWS option has no laser')
else:   # dev.26+: laser in slot 2, and no unit loses an ability to a slot collision (mshorad_laser_slot.py)
    import mshorad_laser_slot as MLS
    if Ot.get(1937,{}).get('Ability2Id')!=MLS.LASER or Ot.get(1937,{}).get('Ability1Id'):bad.append('M-SHORAD APKWS laser is not in ability slot 2 only')
    Mt=merged('ModificationsJson.json','modifications.json');SAt=merged('SpecializationAvailabilitiesJson.json','specialization_availabilities.json')
    bad+=[f'ability slot {k} collision on unit {u} {n}' for u,n,k in MLS.slot_collisions(Ut,Mt,Ot,At,{r.get('UnitId') for r in SAt.values()})]
if 'UserData/FreedomArrow/plane-refund.json' not in z.namelist():bad.append('plane-refund.json missing')
dll=z.read('Mods/FreedomArrow.Runtime.dll')
for s in ('plane_sale_installed','server_money_set'):
    if s.encode('utf-16-le') not in dll and s.encode() not in dll:bad.append(f'runtime DLL lacks {s}')
# Lateralus 16 Nov 2026 ("These builds do not have the yellow altitude changing indicator ... Was there anything else you forgot to keep?"):
# altitude intent, SEAD overkill 0.33 and SEAD re-target were in the sead3-sead5 test builds only. From dev.26 the package must have them,
# and the other dev.26 runtime work.
if (int(m.group(1)),int(m.group(2)))>=(9,26):
    for s in ('altitude_intent_installed','sead_overkill_installed','sead_retarget_installed','FREEDOM_ARROW_LOBBY_TABS installed','online_room_status','overlay_hidden_for_menu','leaving_match','FREEDOM_ARROW_LOBBY_SLOTS installed','same name in two places'):
        if s.encode('utf-16-le') not in dll and s.encode() not in dll:bad.append(f'runtime DLL lacks {s}')
    if 'UserData/FreedomArrow/sead-overkill.json' not in z.namelist():bad.append('sead-overkill.json missing')
if bad:sys.exit('QUEUED LATERALUS CHANGES MISSING FROM THE PACKAGE ('+str(len(bad))+'):\n'+'\n'.join(bad[:30]))
print(f'queued_checks: {sum(len(f) for f in S.SPW.values())+len(S.SPA)} SPAAG/SAM values, {len(SP.UNITS)+len(SP.OPTIONS)} SEAD prices, {len(EP.EXPECT)} ECM pod options and the plane sale are in {Path(pkg).name}')
