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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from fa_version import key   # 0.9.1-dev.N and 0.9.1 too (Lateralus 19 Nov)
m=key(V)
def _ge(minor,dev):return m>=key(f'0.{minor}.0-dev.{dev}')
if not _ge(9,25):print('queued_checks: not required before 0.9.0-dev.25');sys.exit(0)
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
# by 50 points": 305 -> 355; 0.9.0-dev.43, Osama 18 Nov 11:5x PST: "J-36 increase price by 60": 355 -> 415). The latest stage reached applies.
LATER={929:(((9,32),355),((9,43),415)),921:(((9,35),255),),966:(((9,35),255),),1251:(((9,35),250),)}
# 0.9.0-dev.35 (Osama 16 Nov 20:5x PST: "All 5th gen fighters are 2x availability and shouldn't have been touched by any SEAD point buffs"): these
# 5th/6th-gen options are back at their pre-SEAD price and the four fighters back at 2 cards.
FIFTH_OPTIONS=(1888,1889,24653,24654,24656,24657,24659,24660,24664,20191,20198,20234);FIFTH_ROWS={2008203,2014507,2008260,2014513}
after35=_ge(9,35)
# 0.9.4-dev.4 (Osama 21 Nov 2026 18:2x PST, Doc "China changes 9.4"): "J-36 base price increased by +30pts" 415 -> 445; "J-31 Heavy SEAD +55" 155 -> 210 in dev.4 only; from dev.5 the option costs 55 ("I meant the overall price should be +55").
after094d4=m>=key('0.9.4-dev.4');LATER_094={929:445};LATER_094_OPT={24659:210 if m==key('0.9.4-dev.4') else 55}  # dev.5+: 'the overall price should be +55' (Osama 21 Nov 18:5x)
def _want(i,new):
    if after094d4 and i in LATER_094:return LATER_094[i]
    return ([p for s,p in LATER.get(i,()) if _ge(*s)] or [new])[-1]
def _wopt(i,old,new):
    if after094d4 and i in LATER_094_OPT:return LATER_094_OPT[i]
    return old if after35 and i in FIFTH_OPTIONS else new
bad+=[f'unit {i} {n} cost {Ut.get(i,{}).get("Cost")} (want {_want(i,new)})' for i,(n,old,new) in SP.UNITS.items() if Ut.get(i,{}).get('Cost')!=_want(i,new)]
bad+=[f'option {i} {n} cost {Ot.get(i,{}).get("Cost")} (want {_wopt(i,old,new)})' for i,(u,n,old,new) in SP.OPTIONS.items() if (Ot.get(i,{}).get('Cost') or 0)!=_wopt(i,old,new)]
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
# 0.9.4-dev.2 (build 249) only: the SRAT II / APS option (1934) cost 55 under Osama's 700-armour pricing (+25). From dev.3 it is Lateralus's 45 again
# (Osama 21 Nov 2026 17:27 PST: "yeah lets keep Lateralus's point distribution").
_msp={i:(55 if i==1934 and m==key('0.9.4-dev.2') else new) for i,(n,old,new) in MS.PRICES.items()}
bad+=[f'M-SHORAD option {i} cost {Ot.get(i,{}).get("Cost")} (want {new})' for i,new in _msp.items() if Ot.get(i,{}).get('Cost')!=new]
if not _ge(9,26):
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
if _ge(9,26):
    for s in ('altitude_intent_installed','sead_overkill_installed','sead_retarget_installed','FREEDOM_ARROW_LOBBY_TABS installed','online_room_status','overlay_hidden_for_menu','leaving_match','FREEDOM_ARROW_LOBBY_SLOTS installed','same name in two places','deployment_in_clock'):
        if s.encode('utf-16-le') not in dll and s.encode() not in dll:bad.append(f'runtime DLL lacks {s}')
    if 'UserData/FreedomArrow/sead-overkill.json' not in z.namelist():bad.append('sead-overkill.json missing')
# From dev.33: the SEAD availability change (lateralus/sead_availability.py).
if _ge(9,33):
    import sead_availability as SAV
    SAt=merged('SpecializationAvailabilitiesJson.json','specialization_availabilities.json')
    bad+=[f'{n} deck row {row}: {SAt.get(row,{}).get("MaxAvailabilityXp0")} cards (want {new})' for u,(n,row,old,new) in SAV.ROWS.items() if SAt.get(row,{}).get('MaxAvailabilityXp0')!=(old if after35 and row in FIFTH_ROWS else new)]
    # China SF smoke / HJ-12 / sprint / PF-89 and cheap recon lasers (lateralus/china_sf_recon.py, Lateralus 16 Nov 16:5x PST).
    import china_sf_recon as CSR
    _F={'AbilitiesJson':'abilities.json','UnitAbilitiesJson':'unit_abilities.json','SquadMembersJson':'squad_members.json','WeaponAmmunitionsJson':'weapon_ammunitions.json','Units':'units.json'}
    bad+=CSR.check(lambda tab:merged(tab+'.json',_F[tab]))
# From dev.36: the six [FA] [PvE] maps ship, and every China wave in them names units and options that exist in this package (Osama 17 Nov
# 13:2x PST: "do units update when we update the armory": the maps store only unit and option ids, so stats follow the armory, but a removed
# or renumbered unit/option would break a wave).
if _ge(9,36):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'releases/0.8/scenarios'))
    import common as SC,pve as PVE
    Mt=merged('ModificationsJson.json','modifications.json')
    for name in PVE.ALL_NAMES:
        f=f'UserData/FreedomArrow/scenarios/{name}/{name}.bascr'
        if f not in z.namelist():bad.append(f'PvE map missing: {name}');continue
        waves=[json.loads(next(q['v'] for q in b['props_v2'] if q['k']=='val').replace('\u00a8','"')) for b in SC.load(SC.dec(zipfile.ZipFile(z.open(f)).read('nodes.bam')))['b'] if b['nnKey']=='getSpMultUnData']
        want=next(len(PVE.WAVES[t]) for p_,_,_,t,_ in PVE.BASES if name in PVE.names(p_,t))
        if len(waves)<want:bad.append(f'{name}: {len(waves)} wave groups (want at least {want} waves)')
        for w in waves:
            for u in w['Units']:
                if u['unitId'] not in Ut:bad.append(f'{name}: wave unit {u["unitId"]} not in the package')
                for it in u['items']:
                    if Mt.get(it['mod'],{}).get('UnitId')!=u['unitId'] or Ot.get(it['opt'],{}).get('ModificationId')!=it['mod']:bad.append(f'{name}: unit {u["unitId"]} option {it} not in the package')
# From dev.36: stress recovery 0.33 (Lateralus 17 Nov 12:35 PST "queue it"), the lobby list of packaged maps only and the altitude arrow traces.
if _ge(9,36):
    gc=json.loads(z.read('UserData/FreedomArrow/game-config.json'))
    if gc.get('StressRecoveryMultiplier')!=0.33:bad.append(f"game-config StressRecoveryMultiplier {gc.get('StressRecoveryMultiplier')} (want 0.33)")
    for s in ('FREEDOM_ARROW_STRESS_RECOVERY','local [FA] maps not in this package','still_shown','icon_left_modified'):
        if s.encode('utf-16-le') not in dll and s.encode() not in dll:bad.append(f'runtime DLL lacks {s}')
# From 0.9.1-dev.4 (Lateralus 19 Nov 2026 13:2x PST: "only create new rows when we ask for a unique combination of abilities"; "that also goes for
# when we are making new units"): no FA ability row has the same values (all fields except Id and Name) as another row. Link the existing row instead.
if m>=key('0.9.1-dev.4'):
    _vab={r['Id'] for r in json.loads((van/'AbilitiesJson.json').read_text())}
    _sig={};[_sig.setdefault(json.dumps({k:v for k,v in r.items() if k not in ('Id','Name')},sort_keys=True),[]).append(i) for i,r in sorted(At.items())]
    bad+=[f'ability rows {ids} have the same values: link {ids[0]} instead of adding a row' for ids in _sig.values() if len(ids)>1 and any(i not in _vab for i in ids)]
# From 0.9.1-dev.5 (Lateralus 19 Nov 2026 13:5x PST: "we should never have OriginalCost anything except 0"): a non-zero Units.OriginalCost replaces
# Cost at load (LoadUnits.PrepareForMods), so the card shows the old price. Vanilla has 0 on every unit.
if m>=key('0.9.1-dev.5'):
    bad+=[f'unit {i} {u.get("HUDName")} OriginalCost {u["OriginalCost"]} (want 0; Cost {u.get("Cost")} is the price)' for i,u in sorted(Ut.items()) if u.get('OriginalCost')]
# From 0.9.2-dev.8 (Lateralus 20 Nov 2026, thread 1572962048705429598): the [3v3] Bay of Winds map ships, and the Create a lobby cards carry
# New / Updated tags: map-labels.json is the comparison with the current playtest release, and the runtime draws it (MapLabels.cs).
if m>=key('0.9.2-dev.8'):
    for f in ('[FA] [3v3] Bay of Winds 0.1','[FA] [3v3] Bay of Winds Skirmish 0.1'):
        if f'UserData/FreedomArrow/scenarios/{f}/{f}.bascr' not in z.namelist():bad.append(f'map missing: {f}')
    import map_labels as ML
    if 'UserData/FreedomArrow/map-labels.json' not in z.namelist():bad.append('map-labels.json missing')
    elif z.read('UserData/FreedomArrow/map-labels.json')!=ML.labels(V,z)[1]:bad.append('map-labels.json differs from the comparison with the current playtest release')
    dll=z.read('Mods/FreedomArrow.Runtime.dll')
    if 'FREEDOM_ARROW_MAP_LABELS'.encode('utf-16-le') not in dll:bad.append('runtime DLL lacks FREEDOM_ARROW_MAP_LABELS')
# From 0.9.4-dev.1 (Lateralus 21 Nov 2026: "queue up the fix for force firing through smoke for 0.9.4"): Fire at position does not shoot
# through smoke (SmokeGroundFire.cs, ActualArrow's SmokeGroundPatch).
if m>=key('0.9.4-dev.1'):
    if 'FREEDOM_ARROW_SMOKE_GROUND'.encode('utf-16-le') not in z.read('Mods/FreedomArrow.Runtime.dll'):bad.append('runtime DLL lacks FREEDOM_ARROW_SMOKE_GROUND')
# From 0.9.4-dev.1 (Lateralus 21 Nov 2026: "queue up the fix but at 5 seconds before the match ends"): online, the host sends the FA winner
# 5 s before time up (ModeControls.QueueScoreLimitEnding; it logs "online_early_end").
if m>=key('0.9.4-dev.1'):
    if 'online_early_end'.encode('utf-16-le') not in z.read('Mods/FreedomArrow.Runtime.dll'):bad.append('runtime DLL lacks the online early time-up end (online_early_end)')
# From 0.9.4-dev.1 (Lateralus 21 Nov 2026: "queue both"): every packaged FA map's native War Goals can never award a victory point (capture
# goals 1000000, destruction off, no sudden death; scenarios/common.py native_goals_out_of_reach), so a time-out without an FA winner is a
# server draw; and the result screen shows Major/Minor from the FA score (conquest/ResultLevel.cs, logs "result_level").
if m>=key('0.9.4-dev.1'):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'releases/0.8/scenarios'))
    import common as SC2
    _modes=0
    for f in [n for n in z.namelist() if n.startswith('UserData/FreedomArrow/scenarios/') and n.endswith('.bascr')]:
        for b in SC2.load(SC2.dec(zipfile.ZipFile(z.open(f)).read('nodes.bam')))['b']:
            if b['nnKey']!='setConquestMode':continue
            _modes+=1;q={x['k']:x['v'] for x in b['props_v2']}
            if (q.get('goal1'),q.get('goal2'),q.get('goal3'),q.get('isDestructionEnabled'),q.get('deathByScore'))!=('1000000','1000000','1000000','False','False'):
                bad.append(f'{f}: native War Goals can still award victory points {q.get("goal1")}/{q.get("goal2")}/{q.get("goal3")} destruction {q.get("isDestructionEnabled")}')
    if _modes==0:bad.append('no setConquestMode found in the packaged maps')
    if 'result_level'.encode('utf-16-le') not in z.read('Mods/FreedomArrow.Runtime.dll'):bad.append('runtime DLL lacks the result-screen level hook (result_level)')
# From 0.9.4-dev.5 (Osama 21 Nov 2026 19:08-19:51 PST, thread 1573561286803980289, "you can push this into the build"): infantry cover and damage.
# Buildings take 30 % (game-config BuildingDamageFloor 0.3); tank-gun, autocannon and HMG anti-infantry rounds x0.8, tank HEAT = HE, Ignore Cover 0
# (cover_damage_094.py); SPAAG main guns keep their values; the BMOP Toros fires a cut copy of 57x348mm HE (491 stays 4.3 for the Ural ZU-23).
if m>=key('0.9.4-dev.5'):
    import cover_damage_094 as CD
    gc=json.loads(z.read('UserData/FreedomArrow/game-config.json'))
    if (gc.get('BuildingDamageFloor'),gc.get('BuildingDamagePerSoldier'),gc.get('ForestDamageTaken'))!=(0.3,0,0.55):bad.append(f"game-config buildings/woods {gc.get('BuildingDamageFloor')}/{gc.get('BuildingDamagePerSoldier')}/{gc.get('ForestDamageTaken')} (want 0.3/0/0.55)")
    Am=merged('AmmunitionsJson.json','ammunitions.json');WAm=merged('WeaponAmmunitionsJson.json','weapon_ammunitions.json')
    for i,(c,n,b,a) in list(CD.DAMAGE.items())+list(CD.HEAT.items()):
        if i!=CD.SHARED and Am.get(i,{}).get('Damage')!=a:bad.append(f'ammo {i} {n} Damage {Am.get(i,{}).get("Damage")} (want {a})')
    bad+=[f'ammo {i} {n} IgnoreCover {Am.get(i,{}).get("IgnoreCover")} (want 0)' for i,(n,b) in CD.IGNORE_COVER.items() if i!=CD.SHARED and Am.get(i,{}).get('IgnoreCover')]
    _t=[r['AmmunitionId'] for r in WAm.values() if r and r.get('UnitId')==CD.SHARED_CUT and Am.get(r['AmmunitionId'],{}).get('HUDName')==Am[CD.SHARED].get('HUDName') and Am[r['AmmunitionId']].get('Damage')!=2.9]
    if (Am[CD.SHARED].get('Damage'),Am[CD.SHARED].get('IgnoreCover'))!=(4.3,0.25) or len(_t)!=1 or _t[0]==CD.SHARED or (Am[_t[0]].get('Damage'),Am[_t[0]].get('IgnoreCover'))!=(3.4,0):bad.append(f'57x348mm HE: Ural 491 must stay 4.3/0.25 and the Toros fire a 3.4/0 copy ({_t})')
# From 0.9.5-dev.6 (Osama 22 Nov 2026 00:05 PST, thread 1573561286803980289: "we need to clear the memory before and after every match"):
# GC + Resources.UnloadUnusedAssets on Void (between menu and map, both ways) and back in Hangar_Scene (MemoryCleanup.cs).
if m>=key('0.9.5-dev.6'):
    if 'FREEDOM_ARROW_MEMORY_CLEANUP'.encode('utf-16-le') not in z.read('Mods/FreedomArrow.Runtime.dll'):bad.append('runtime DLL lacks the match memory cleanup (FREEDOM_ARROW_MEMORY_CLEANUP)')
# From 0.9.5-dev.16 (Osama 22 Nov 2026 01:42 PST, thread 1573561286803980289: "in the main menu we need a button with our art that opens our
# website"): Home tab banner (WebsiteButton.cs) and its art.
if m>=key('0.9.5-dev.16'):
    if 'FREEDOM_ARROW_WEBSITE_BUTTON'.encode('utf-16-le') not in z.read('Mods/FreedomArrow.Runtime.dll'):bad.append('runtime DLL lacks the website button (FREEDOM_ARROW_WEBSITE_BUTTON)')
    if 'UserData/FreedomArrow/menu-art/website-button.png' not in z.namelist():bad.append('menu-art/website-button.png missing')
if bad:sys.exit('QUEUED LATERALUS CHANGES MISSING FROM THE PACKAGE ('+str(len(bad))+'):\n'+'\n'.join(bad[:30]))
print(f'queued_checks: {sum(len(f) for f in S.SPW.values())+len(S.SPA)} SPAAG/SAM values, {len(SP.UNITS)+len(SP.OPTIONS)} SEAD prices, {len(EP.EXPECT)} ECM pod options and the plane sale are in {Path(pkg).name}')
