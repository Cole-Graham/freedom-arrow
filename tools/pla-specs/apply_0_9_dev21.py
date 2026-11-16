"""Freedom Arrow 0.9.0-dev.21 data over exact 0.9.0-dev.20 (BA 1.2.2.1 port, local build 193, 16 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.21';PREV='0.9.0-dev.20'
# dev.20 was built in out/local-dev20 (local test for Osama's PC).
BASE=json.loads((REL/f'out/local-dev20/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev20/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];AM=t['AmmunitionsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson']
# ---------- Tank KE rounds: 50 mm between close and max range (Osama 16 Nov 2026 03:1x PST: "all tanks should have a 50mm penetration range,
# can you find all the ones that aren't 50mm? Keep their top end penetration but lower the lower side"). Scope: the main-gun KE rounds
# (ArmorTargeted 1, close penetration >= 200) on every carded tank (Role 11). 30 of the 53 tank KE rounds were already 50; these 10 China
# rounds were 25 and the PT-76 57 mm (221, vanilla, PT-76 only) was 240/120. Close (top) penetration kept, max-range = top - 50.
# Not changed: autocannon rounds on tanks (Abrams X 30 mm, M10 Booker 50 mm, Scimitar 30 mm, PT-76 57 mm) and rounds on tanks with
# no card (ZTD-05, ZTZ-96, ZTZ-20, VT-1A, ZTZ-80/Type 80 catalogue, WZ-1224 catalogue, VT-4, ZTZ-99A2, ZTZ-99G).
SA=t['SpecializationAvailabilitiesJson'];_carded={r['UnitId'] for r in SA.values()}
_ke={221:(230,240,120),2010793:(1059,225),2010821:(1060,250),2010849:(1061,400),2009669:(938,350),2019344:(1272,450),2009855:(947,425),2009103:(905,525),2011357:(1082,425),2010195:(968,550),2011385:(1083,475)}
for _a,(_u,_top,*_lo) in _ke.items():
    _x=AM[_a];ok(_x['ArmorTargeted']==1 and _x['PenetrationAtMinRange']==_top and _x['PenetrationAtGroundRange']==(_lo[0] if _lo else _top-25) and U[_u]['Role']==11 and _u in _carded,(_a,'KE round at top/top-25 on a carded tank'))
    ok(all(U[r['UnitId']]['Role']==11 and r['UnitId'] in _carded for r in WA.values() if r['AmmunitionId']==_a),(_a,'used by carded tanks only'))
    g.put('AmmunitionsJson',_a,{'PenetrationAtGroundRange':float(_top-50)})
_tanks={i for i,u in U.items() if u.get('Role')==11 and u.get('Type')==4 and i in _carded}
_bad=sorted({r['AmmunitionId'] for r in WA.values() if r['UnitId'] in _tanks and AM[r['AmmunitionId']]['ArmorTargeted']==1 and AM[r['AmmunitionId']]['PenetrationAtMinRange']>=200 and AM[r['AmmunitionId']]['PenetrationAtMinRange']-AM[r['AmmunitionId']]['PenetrationAtGroundRange']!=50})
ok(not _bad,('carded tank main-gun KE rounds not at 50 mm spread',_bad))
rec['tank_ke_spread_50']={str(a):[v[0],v[1],(v[2] if len(v)>2 else v[1]-25),v[1]-50] for a,v in _ke.items()}
# ---------- WZ1224 95 -> 110 points (Osama 16 Nov 2026 03:19 PST: "wz1224 should be 110 pts"). Unit 'PLA WZ1224' (new in dev.14).
_wz=[u for u,x in U.items() if x.get('Name')=='PLA WZ1224'];ok(len(_wz)==1 and U[_wz[0]]['Cost']==95,'WZ1224 at 95')
g.put('Units',_wz[0],{'Cost':110});rec['wz1224_cost']=[95,110]
# ---------- ZTZ-99A / ZTZ-99 rework and the LSDW protection option (Osama 16 Nov 2026 03:5x PST, thread 1571014792016171120: "ZTZ-99A front armor
# to 800 and does not have any APS or lasers. base price is 230. Protection system should have the laser as the option for +100 ... LSDW (laser
# self defense weapon). This is what adds the laser APS and the Laser weapon. For the ZTZ-99 penetration should be 450-500mm, 1000mm HEAT front
# protection and 200 pts. Protection system: +100pts for the same laser option"; 03:5x: "60 second cool down but infinite ammo", card shows the
# laser icon instead of APS without ammo count). Like the vanilla Bradley Iron Fist slot (options 37/38): every protection option sets Turret0Id;
# LSDW puts a copy of the tank's main mount with the LSDW laser in place of the 7.62 coax, plus a non-default LSDW APS ability. Laser pulse:
# 0.2 damage (Osama 03:47 "minimal damage"), 200 stress, crit 0, 1400 m ground / 1200 m low altitude, 1 pulse / 2-3 s. APS: 999 charges ("infinite"), 60 s
# cooldown, no supply cost; Dazzler.cs (dazzler.json) stretches its reach to guided missiles only, lets RPGs through, draws the beam and swaps
# the card icon (FA_PLA_ABILITY_LSDW, no count). Replaces the dev.18 always-on APS on 2009067 and the earlier in-place coax change.
_d=AB[2009067];ok(_d['IsDefault'] and _d.get('IsSmoke') and _d.get('IsAPS'),'ZTZ-99A default ability 2009067: smoke + dev.18 APS')
g.put('AbilitiesJson',2009067,{'IsAPS':False,'APSHitboxProportion':0.0,'APSQuantity':0,'APSCooldown':0.0,'APSSupplyCost':0.0,'APSResupplyTime':0.0})
ok(not AB[82].get('IsDefault') and AB[82].get('IsAPS') and not AB[82].get('ModelFileName'),'vanilla 82 APS IronFist NoModel: non-default, no model')
_lap=g.add('AbilitiesJson',AB[82],{'Name':'PLA LSDW laser defense','APSHitboxProportion':1.0,'APSQuantity':999,'APSCooldown':60.0,'APSSupplyCost':0.0,'APSResupplyTime':0.0})
_wa=[r for r in WA.values() if r['WeaponId']==2009081];ok(len(_wa)==1 and _wa[0]['AmmunitionId']==2009083 and W[2009081]['HUDName']=='Type 86 7.62 mm','ZTZ-99A coax 7.62 mm rows unchanged')
_la=g.add('AmmunitionsJson',AM[2009083],{'Name':'PLA LSDW laser pulse','HUDName':'LSDW laser pulse','HUDMultiplier':1,'Damage':0.2,'StressDamage':200.0,'StressAOERadius':3.0,
  'CriticMultiplier':0.0,'GroundRange':700.0,'LowAltRange':600.0,'MuzzleVelocity':3000.0,'DispersionHorizontalRadius':0.5,'DispersionVerticalRadius':0.5})
# Range (Osama 03:56 "drop the range to the same range as its main gun, for low altitude only 1200"): ground = the 125 mm shells (data 700 =
# 1400 m on the card, both tanks), low altitude data 600 = 1200 m.
ok(all(AM[i]['GroundRange']==700.0 for i in (2009075,2009077,2009079,2011385,2011387,2011389)),'ZTZ-99A/99 125 mm shells: data range 700 (1400 m)')
_lw=g.add('WeaponsJson',W[2009081],{'Name':'PLA LSDW laser self-defense weapon','HUDName':'LSDW','HUDIcon':'FA_PLA_WP_LSDW_DAZZLER','AimTimeMin':0.5,'AimTimeMax':0.5,
  'MagazineSize':100,'ShotsPerBurstMin':1,'ShotsPerBurstMax':1,'TimeBetweenBurstsMin':2.0,'TimeBetweenBurstsMax':3.0,'NormalGroundAttackBurst':1})
# Ammunition rows are per unit (WeaponAmmunitionsJson.UnitId): one LSDW row per tank, in _lsdw_turret (dev.21 build 1 failed audit_mp_equipment on the ZTZ-99).
TJ=t['TurretsJson']
def _lsdw_turret(u,mount,coax,label):
    ok([r['TurretId'] for r in TU.values() if r['UnitId']==u and r.get('Order',0)==0]==[mount] and TJ[mount]['IsDefault'] and any(x['WeaponId']==coax for x in TW.values() if x['TurretId']==mount),label+': one main mount with the 7.62 coax')
    nt=g.add('TurretsJson',TJ[mount],{'Name':TJ[mount]['Name']+' LSDW','IsDefault':False})
    for x in [x for x in TW.values() if x['TurretId']==mount]:g.add('TurretWeaponsJson',x,{'TurretId':nt,'WeaponId':_lw if x['WeaponId']==coax else x['WeaponId']})
    g.add('WeaponAmmunitionsJson',_wa[0],{'UnitId':u,'WeaponId':_lw,'AmmunitionId':_la})
    g.add('TurretUnitsJson',{'UnitId':u,'TurretId':nt,'Order':0});g.add('UnitAbilitiesJson',{'UnitId':u,'AbilityId':_lap});return nt
# ZTZ-99A (904)
ok(U[904]['HUDName']=='ZTZ-99A' and [r['ArmorId'] for r in t['UnitArmorsJson'].values() if r['UnitId']==904]==[2009063] and t['ArmorsJson'][2009063]['KinArmorFront']==850,'ZTZ-99A: armour 2009063, KE front 850')
g.put('Units',904,{'Cost':230});g.put('ArmorsJson',2009063,{'KinArmorFront':800})
_t99a=_lsdw_turret(904,2009072,2009081,'ZTZ-99A')
ok(sorted(o['Id'] for o in O.values() if o['ModificationId']==2019383)==[31098,31099],'ZTZ-99A protection slot: None + JD-3')
for _o in (31098,31099):g.put('OptionsJson',_o,{'Turret0Id':2009072})
_o99a=g.add('OptionsJson',O[31099],{'Name':'PLA ZTZ-99A LSDW','UIName':'LSDW','Order':2,'Cost':100,'OptionPicture':'FA_PLA_ABILITY_LSDW','Ability1Id':2009067,'Ability2Id':_lap,'Turret0Id':_t99a})
# ZTZ-99 (1083)
ok(U[1083]['HUDName']=='ZTZ-99' and [r['ArmorId'] for r in t['UnitArmorsJson'].values() if r['UnitId']==1083]==[2011373] and not [m for m in M.values() if m['UnitId']==1083],'ZTZ-99: armour 2011373, no options yet')
ok([x['WeaponId'] for x in WA.values() if x['AmmunitionId']==2011385]==[2011381],'ZTZ-99 APFSDS 2011385 own row')
g.put('Units',1083,{'Cost':200});g.put('ArmorsJson',2011373,{'HeatArmorFront':1000});g.put('AmmunitionsJson',2011385,{'PenetrationAtMinRange':500.0,'PenetrationAtGroundRange':450.0})
_t99=_lsdw_turret(1083,2011382,2011391,'ZTZ-99')
_m99=g.add('ModificationsJson',M[2019383],{'UnitId':1083,'Name':'PLA ZTZ-99 protection'})
g.add('UnitAbilitiesJson',{'UnitId':1083,'AbilityId':4})
_n99=g.add('OptionsJson',O[31098],{'ModificationId':_m99,'Name':'PLA ZTZ-99 No protection','Ability1Id':2011377,'Ability2Id':4,'Turret0Id':2011382})
_o99=g.add('OptionsJson',O[31099],{'ModificationId':_m99,'Name':'PLA ZTZ-99 LSDW','UIName':'LSDW','Order':1,'Cost':100,'OptionPicture':'FA_PLA_ABILITY_LSDW','Ability1Id':2011377,'Ability2Id':_lap,'Turret0Id':_t99})
_dz=json.loads((SRC/'UserData/FreedomArrow/dazzler.json').read_text())
ok(_dz['units']==[904,1083] and _dz.get('laserWeaponNames')==['LSDW'] and _dz.get('cardIcon')=='FA_PLA_ABILITY_LSDW' and not _dz.get('laserAmmo'),'dazzler.json: ZTZ-99A + ZTZ-99, LSDW weapon, card icon')
ok(all((SRC/f'runtime-qa/icons/{n}.png').exists() for n in ('FA_PLA_WP_LSDW_DAZZLER','FA_PLA_WP_LSDW_DAZZLER_OUTLINE','FA_PLA_ABILITY_LSDW')),'LSDW icons embedded')
rec['lsdw']={'ability':_lap,'weapon':_lw,'ammo':_la,'turrets':{'904':_t99a,'1083':_t99},'options':{'904':_o99a,'1083':[_n99,_o99]},'modification_1083':_m99,
  'ztz99a':{'cost':230,'ke_front':800},'ztz99':{'cost':200,'heat_front':1000,'apfsds':[500,450]},'aps':{'charges':999,'cooldown':60},'laser':{'damage':0.2,'stress':200,'card_range_m':{'ground':1400,'low_alt':1200}}}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
