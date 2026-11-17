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
# Later decisions that supersede a queued price, from the version that made them (0.9.0-dev.32, Osama 16 Nov 14:4x PST: "J-36 ... price increased
# by 50 points": 305 -> 355).
LATER={929:((9,32),355),921:((9,35),255),966:((9,35),255),1251:((9,35),250)}
# 0.9.0-dev.35 (Osama 16 Nov 20:5x PST: "All 5th gen fighters are 2x availability and shouldn't have been touched by any SEAD point buffs"): these
# 5th/6th-gen options are back at their pre-SEAD price and the four fighters back at 2 cards.
FIFTH_OPTIONS=(1888,1889,24653,24654,24656,24657,24659,24660,24664,20191,20198,20234);FIFTH_ROWS={2008203,2014507,2008260,2014513}
after35=(int(m.group(1)),int(m.group(2)))>=(9,35)
def _want(i,new):
    l=LATER.get(i);return l[1] if l and (int(m.group(1)),int(m.group(2)))>=l[0] else new
bad+=[f'unit {i} {n} cost {Ut.get(i,{}).get("Cost")} (want {_want(i,new)})' for i,(n,old,new) in SP.UNITS.items() if Ut.get(i,{}).get('Cost')!=_want(i,new)]
bad+=[f'option {i} {n} cost {Ot.get(i,{}).get("Cost")} (want {old if after35 and i in FIFTH_OPTIONS else new})' for i,(u,n,old,new) in SP.OPTIONS.items() if (Ot.get(i,{}).get('Cost') or 0)!=(old if after35 and i in FIFTH_OPTIONS else new)]
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
    for s in ('altitude_intent_installed','sead_overkill_installed','sead_retarget_installed','FREEDOM_ARROW_LOBBY_TABS installed','online_room_status','overlay_hidden_for_menu','leaving_match','FREEDOM_ARROW_LOBBY_SLOTS installed','same name in two places','deployment_in_clock'):
        if s.encode('utf-16-le') not in dll and s.encode() not in dll:bad.append(f'runtime DLL lacks {s}')
    if 'UserData/FreedomArrow/sead-overkill.json' not in z.namelist():bad.append('sead-overkill.json missing')
# From dev.33: the SEAD availability change (lateralus/sead_availability.py).
if (int(m.group(1)),int(m.group(2)))>=(9,33):
    import sead_availability as SAV
    SAt=merged('SpecializationAvailabilitiesJson.json','specialization_availabilities.json')
    bad+=[f'{n} deck row {row}: {SAt.get(row,{}).get("MaxAvailabilityXp0")} cards (want {new})' for u,(n,row,old,new) in SAV.ROWS.items() if SAt.get(row,{}).get('MaxAvailabilityXp0')!=(old if after35 and row in FIFTH_ROWS else new)]
    # China SF smoke / HJ-12 / sprint / PF-89 and cheap recon lasers (lateralus/china_sf_recon.py, Lateralus 16 Nov 16:5x PST).
    import china_sf_recon as CSR
    _F={'AbilitiesJson':'abilities.json','UnitAbilitiesJson':'unit_abilities.json','SquadMembersJson':'squad_members.json','WeaponAmmunitionsJson':'weapon_ammunitions.json','Units':'units.json'}
    bad+=CSR.check(lambda tab:merged(tab+'.json',_F[tab]))
if bad:sys.exit('QUEUED LATERALUS CHANGES MISSING FROM THE PACKAGE ('+str(len(bad))+'):\n'+'\n'.join(bad[:30]))
print(f'queued_checks: {sum(len(f) for f in S.SPW.values())+len(S.SPA)} SPAAG/SAM values, {len(SP.UNITS)+len(SP.OPTIONS)} SEAD prices, {len(EP.EXPECT)} ECM pod options and the plane sale are in {Path(pkg).name}')
