"""Freedom Arrow 0.9.2-dev.8 data over exact 0.9.2-dev.7 (build 239). Data opened by BA Codex thread 1572962048705429598 (Lateralus, plane return time and ground missile resupply).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.2-dev.8';PREV='0.9.2-dev.7'
# 0.9.2-dev.7 (build 239) was built in out/local-092dev7.
BASE=json.loads((REL/f'out/local-092dev7/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-092dev7/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
A=t['AmmunitionsJson'];O=t['OptionsJson'];M=t['ModificationsJson'];WA=t['WeaponAmmunitionsJson']
# ---------- 1. Plane return time: power 5 -> 1.6 curve, nukes and heavy hitters compensated (Lateralus 20 Nov 2026 10:2x PST, thread
# 1572962048705429598: "Yes go with option 1 and compensate the nukes, and add base times for the other heavy hitters with no base time").
# The game (RefundSystem.GetPurchaseDelay, 1.2.2.1) sets a plane's return delay to PlanesRefundFloor 60 + base + K x (sum of shots x
# ResupplyTime^P)^(1/P), base = Units.TimeModifierRefund + chosen options' TimeModifierRefund. Option 1 = K 0.3, P 1.6 (vanilla K 1, P 5); the
# runtime sets them from game-config.json (PlaneReturnCurve.cs). Below: base times so that using the whole load of a nuke or heavy hitter
# (ResupplyTime >= 700 s) takes as long as before: base += t*n^0.2 - 0.3*t*n^(1/1.6). Where two slots can both carry the weapon (B-52H bay +
# pylons, F-22 left + right bay) each option gets half of the full-load compensation, so the full load is exact.
def _comp(t,n):return t*n**0.2-0.3*t*n**(1/1.6)
_NUKE_CARD={702:('MiG-31K (S)',1400.0,1300.0,1)}
_OPT={1740:('Tu-160','Custom_Option_Kh102_nuke',1400.0,1300.0,1,1),1026:('B-1B Lancer','Custom_Option_B61_Nuke',2000.0,700.0,1,1),
      1083:('B-2 Spirit','Custom_Option_B61_Nuke',2000.0,700.0,1,1),20177:('B-21 Raider','Custom_Option_B61_Nuke',2000.0,700.0,1,1),
      1746:('MiG-31K','Custom_Option_HE_warhead',0.0,760.0,1,1),1747:('MiG-31K','Custom_Option_Cluster_warhead',0.0,760.0,1,1),
      20203:('B-21 Raider','2x AGM-183A ARRW',0.0,760.0,2,1),24478:('H-6K','Anti-ship (YJ-21)',0.0,760.0,2,1),
      20157:('B-52H Stratofortress','2x AGM-183A ARRW',0.0,760.0,4,2),20158:('B-52H Stratofortress','2x AGM-183A ARRW',0.0,760.0,4,2),
      31000:('F-22 Raptor','1x MAKO',0.0,760.0,2,2),31001:('F-22 Raptor','1x MAKO',0.0,760.0,2,2)}
rec['plane_return_base']={}
for uid,(h,b0,tt,n) in _NUKE_CARD.items():
    ok(U[uid]['HUDName'].strip()==h and U[uid]['TimeModifierRefund']==b0,(uid,h,U[uid].get('TimeModifierRefund')))
    nb=round(b0+_comp(tt,n));g.put('Units',uid,{'TimeModifierRefund':float(nb)});rec['plane_return_base'][f'unit {uid}']={'name':h,'base':[b0,nb]}
for oid,(h,on,b0,tt,n,share) in _OPT.items():
    o=O[oid];ok(U[M[o['ModificationId']]['UnitId']]['HUDName'].strip()==h and (o.get('UIName') or o['Name']).strip()==on and (o.get('TimeModifierRefund') or 0.0)==b0,(oid,h,on,o.get('TimeModifierRefund')))
    nb=round(b0+_comp(tt,n)/share);g.put('OptionsJson',oid,{'TimeModifierRefund':float(nb)});rec['plane_return_base'][f'option {oid}']={'card':h,'loadout':on,'base':[b0,nb],'missiles':n,'shared_by_slots':share}
ok(U[702]['TimeModifierRefund']==2310.0 and O[1740]['TimeModifierRefund']==2310.0 and O[1083]['TimeModifierRefund']==2490.0 and O[1746]['TimeModifierRefund']==532.0,'nuke and Kinzhal base times')
rec['plane_return_curve']={'PlanesRefundAmmoCoeff_K':[1,0.3],'PlanesRefundAmmoCoeff_P':[5,1.6],'where':'game-config.json + runtime PlaneReturnCurve.cs'}
# ---------- 2. Ground-launched cruise and ballistic missiles: ResupplyTime -50 %, SupplyCost -25 % (Lateralus, same message: "for ground launched
# cruise and ballistic missiles I want to reduce the resupply time per missile by 50% and supply costs by 25%, with the following exceptions (leave at
# current values): DF-17/ZF, DF-31A Nuclear, CTL-181 NLOS, CH-901"). Ammunition with TrajectoryType 200/300 on ground cards in a deck; each row is
# used only by ground launchers (checked), so planes, ships and the exceptions keep their values.
_GROUND={34:'ATACMS',218:'9M723-1F',219:'9M728',427:'400mm HE PrSM',439:'9M79-1F',440:'9M79-1K',566:'9M723-1K5',752:'9M728',903:'400mm HE PrSM',
         2010363:'DF-15 conventional test missile ammunition',2010375:'DF-21 conventional test missile ammunition',2011649:'YJ-18',2017443:'Fire Dragon 480',
         2017462:'Fire Dragon 300',2017463:'Fire Dragon 480',2018727:'Fire Dragon 280A'}
_KEEP={2010351:'DF-17/ZF',2010399:'DF-31A Nuclear',2018321:'CTL-181 NLOS',2018448:'Blood Wolves 朱日和之狼'}
rec['ground_missiles']={}
for aid,h in _GROUND.items():
    a_=A[aid];ok(a_['HUDName'].strip()==h and a_['TrajectoryType'] in (200,300),(aid,h,a_.get('HUDName')))
    users={U[r['UnitId']]['HUDName'].strip() for r in WA.values() if r['AmmunitionId']==aid and r['UnitId'] in U}
    ok(all(U[r['UnitId']].get('Type')==4 for r in WA.values() if r['AmmunitionId']==aid and r['UnitId'] in U) and not users&set(_KEEP.values()),(aid,'ground only, no exception',users))
    old=(a_['ResupplyTime'],a_['SupplyCost']);g.put('AmmunitionsJson',aid,{'ResupplyTime':old[0]*0.5,'SupplyCost':old[1]*0.75})
    rec['ground_missiles'][str(aid)]={'name':h,'users':sorted(users),'ResupplyTime':[old[0],A[aid]['ResupplyTime']],'SupplyCost':[old[1],A[aid]['SupplyCost']]}
for aid,h in _KEEP.items():ok(h in {U[r['UnitId']]['HUDName'].strip() for r in WA.values() if r['AmmunitionId']==aid and r['UnitId'] in U},(aid,h,'exception user'))
rec['ground_missiles_unchanged']={str(k):v for k,v in _KEEP.items()}
# ---------- 3. Blue Dragon: Type 10 and Type 90 (Osama 20 Nov 2026 12:18 PST, thread 1573418243715113213: "Type 10 and 90 we give them 4 second
# reload. Can you start building these units? I'm wondering if we can sneak this into live build so we don't need to worry about merging builds").
# Stats = War Thunder values converted to FA scale (work/blue-dragon-wt-20261120/REPORT.md): KE pen = WT 10 m x FA/WT of the same-calibre FA round
# (M829A3 633 -> 550), far = close - 50; HEAT shell x1.25; front KE ~ WT turret-cheek KE; front HEAT ~ 0.9 x WT CE.
# Parent: M1A2 SEP v2 TUA (2): base game (Leopard 2A8 is Baltic DLC), no loadout options, M256 + M2 and M240 cupolas, Laser Smoke x2 (LWS + smoke),
# Very Good optics, 70/55 tracks. Each card gets its own main turret (cupolas re-parented) so its gun can have its own reload.
# No model yet (C5 models not bought): the TUA model shows as a stand-in. HIDDEN until Osama picks the spec: DisplayInArmory False, no deck card.
# Costs are placeholders (not given); set BD_SPECS to place the cards.
TJ=t['TurretsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];W=t['WeaponsJson'];AR=t['ArmorsJson'];MOB=t['MobilityJson']
def _rows(tab,**kw):return sorted([r for r in t[tab].values() if all(r.get(k)==v for k,v in kw.items())],key=lambda r:r['Id'])
BD_SPECS=[]  # e.g. [(4,2)] = US Armored Brigade, 2 cards; empty = hidden
ok(U[2]['HUDName']=='M1A2 SEP v2 TUA' and U[2]['CountryId']==2 and U[2]['ContentMembership']==-1 and not _rows('ModificationsJson',UnitId=2),'TUA: base-game US card, no options')
ok([(r['TurretId'],r['Order']) for r in _rows('TurretUnitsJson',UnitId=2)]==[(436,0),(440,0),(441,0)] and TJ[440]['ParentTurretId']==436 and TJ[441]['ParentTurretId']==436,'TUA turrets 436 + cupolas 440/441')
ok([(r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in _rows('WeaponAmmunitionsJson',UnitId=2)]==[(266,254,16),(266,251,24),(18,19,200),(27,27,1140)],'TUA ammunition rows')
ok((W[266]['MagazineSize'],W[266]['MagazineReloadTimeMin'],W[266]['MagazineReloadTimeMax'])==(1,6.0,7.0),'M256 one round, 6-7 s')
ok((A[254]['HUDName'].strip(),A[254]['PenetrationAtMinRange'],A[254]['PenetrationAtGroundRange'])==('M829A3 APFSDS',550.0,500.0) and (A[253]['HUDName'].strip(),A[253]['PenetrationAtMinRange'])==('M830 HEAT',600.0),'FA M829A3 550/500, M830 600')
_jm12=g.add('AmmunitionsJson',A[253],{'Name':'Round 120 JM12A1 HEAT BlueDragon','HUDName':'JM12A1 HEAT','GroundRange':700.0})
rec['blue_dragon']={'parent':'M1A2 SEP v2 TUA (2)','visible':bool(BD_SPECS),'specs':BD_SPECS,'model':'stand-in (TUA); C5 model not bought','cards':{}}
for nm,gun,ap,pen,armour,cost in (('Type 10','MainGun 120 Type 10 TKG autoloader','Type 10 APFSDS',(525.0,475.0),((600,100,100,60),(800,200,100,100)),190),
                                  ('Type 90','MainGun 120 Type 90 L44 autoloader','JM33 APFSDS',(425.0,375.0),((500,120,100,60),(600,200,100,100)),140)):
    ok(not any(u.get('Name')==nm or u.get('HUDName')==nm for u in U.values()),nm+' name free')
    d=dict(U[2]);d.pop('Id');d.update({'Name':nm,'HUDName':nm,'Cost':cost,'OriginalCost':0,'Description':None,'OriginalName':None,'DisplayInArmory':bool(BD_SPECS)})
    uid=g.put('Units',max(U)+1,d)
    for r in _rows('SensorUnitsJson',UnitId=2):g.add('SensorUnitsJson',r,{'UnitId':uid})
    for r in _rows('UnitAbilitiesJson',UnitId=2):g.add('UnitAbilitiesJson',r,{'UnitId':uid})
    _ua=_rows('UnitArmorsJson',UnitId=2);ok(len(_ua)==1 and _ua[0]['ArmorId']==2000397,'TUA one armour row')
    (kf,ks,kr,kt),(hf,hs,hr,ht)=armour
    arm=g.add('ArmorsJson',AR[2000397],{'Name':f'Armor {nm} BlueDragon','KinArmorFront':kf,'KinArmorSides':ks,'KinArmorRear':kr,'KinArmorTop':kt,
        'HeatArmorFront':hf,'HeatArmorSides':hs,'HeatArmorRear':hr,'HeatArmorTop':ht,'MaxHealthPoints':14})
    g.add('UnitArmorsJson',_ua[0],{'UnitId':uid,'ArmorId':arm})
    _up=_rows('UnitPropulsionsJson',UnitId=2);ok(len(_up)==1 and (MOB[_up[0]['MobilityId']]['MaxSpeedRoad'],MOB[_up[0]['MobilityId']]['MaxCrossCountrySpeed'])==(70.0,55.0),'TUA one mobility 70/55')
    g.add('UnitPropulsionsJson',_up[0],{'UnitId':uid,'MobilityId':g.add('MobilityJson',MOB[_up[0]['MobilityId']],{'Name':f'Tracks {nm} BlueDragon 70kph'})})
    w=g.add('WeaponsJson',W[266],{'Name':gun,'HUDName':'120mm '+nm,'AutoLoaded':True,'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
    apr=g.add('AmmunitionsJson',A[254],{'Name':f'Round 120 {ap} BlueDragon','HUDName':ap,'PenetrationAtMinRange':pen[0],'PenetrationAtGroundRange':pen[1]})
    main=g.add('TurretsJson',TJ[436]);tmap={436:main}
    for c in (440,441):tmap[c]=g.add('TurretsJson',TJ[c],{'ParentTurretId':main})
    for old,new in tmap.items():
        for r in _rows('TurretWeaponsJson',TurretId=old):g.add('TurretWeaponsJson',r,{'TurretId':new,'WeaponId':w if r['WeaponId']==266 else r['WeaponId']})
    for r in _rows('TurretUnitsJson',UnitId=2):g.add('TurretUnitsJson',r,{'UnitId':uid,'TurretId':tmap[r['TurretId']]})
    for r in _rows('WeaponAmmunitionsJson',UnitId=2):
        if r['WeaponId']==266:g.add('WeaponAmmunitionsJson',r,{'UnitId':uid,'WeaponId':w,'AmmunitionId':apr if r['AmmunitionId']==254 else _jm12,'Quantity':16})
        else:g.add('WeaponAmmunitionsJson',r,{'UnitId':uid})
    for sp,n in BD_SPECS:
        src=_rows('SpecializationAvailabilitiesJson',UnitId=2)[0];g.add('SpecializationAvailabilitiesJson',src,{'UnitId':uid,'SpecializationId':sp,'MaxAvailabilityXp0':n})
    # checks on the finished card
    ok([(TJ[r['TurretId']]['Name'],r['Order']) for r in _rows('TurretUnitsJson',UnitId=uid)]==[(TJ[x]['Name'],o) for x,o in ((436,0),(440,0),(441,0))],nm+' turret links mirror the TUA')
    ok(all(TJ[tmap[c]]['ParentTurretId']==main for c in (440,441)) and [x['WeaponId'] for x in _rows('TurretWeaponsJson',TurretId=main)]==[w if x['WeaponId']==266 else x['WeaponId'] for x in _rows('TurretWeaponsJson',TurretId=436)],nm+' main turret: new gun, same order')
    ok((W[w]['MagazineReloadTimeMin'],W[w]['MagazineReloadTimeMax'],W[w]['MagazineSize'])==(4.0,4.0,1),nm+' 4 s reload')
    ok(sorted((r['WeaponId'],A[r['AmmunitionId']]['HUDName'],A[r['AmmunitionId']]['PenetrationAtMinRange'],A[r['AmmunitionId']]['PenetrationAtGroundRange'],r['Quantity']) for r in _rows('WeaponAmmunitionsJson',UnitId=uid) if r['WeaponId']==w)
       ==sorted([(w,ap,pen[0],pen[1],16),(w,'JM12A1 HEAT',600.0,600.0,16)]),nm+' rounds')
    _a=AR[[r['ArmorId'] for r in _rows('UnitArmorsJson',UnitId=uid)][0]]
    ok(tuple(_a[k] for k in ('KinArmorFront','KinArmorSides','KinArmorRear','KinArmorTop','HeatArmorFront','HeatArmorSides','HeatArmorRear','HeatArmorTop','MaxHealthPoints'))==(*armour[0],*armour[1],14),nm+' armour')
    ok([r['SpecializationId'] for r in _rows('SpecializationAvailabilitiesJson',UnitId=uid)]==[s for s,_ in BD_SPECS] and U[uid]['DisplayInArmory']==bool(BD_SPECS),nm+' visibility')
    rec['blue_dragon']['cards'][nm]={'unit':uid,'cost':cost,'gun':w,'reload_s':4.0,'ap':[ap,apr,*pen],'heat':['JM12A1 HEAT',_jm12,600.0],'turret':main,'armour_row':arm,
        'KE':list(armour[0]),'HEAT':list(armour[1]),'HP':14,'road_xc':[70,55]}
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
