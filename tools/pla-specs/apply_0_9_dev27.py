"""Freedom Arrow 0.9.0-dev.27 data over exact 0.9.0-dev.26 (16 Nov 2026). Opened by BA Codex thread 1567745029781454889 (Osama: LY-1).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.27';PREV='0.9.0-dev.26'
# dev.26 was built in out/local-dev26.
BASE=json.loads((REL/f'out/local-dev26/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev26/FreedomArrow-{PREV}-complete.bamod'
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
sys.path.insert(0,str(Path(__file__).parent/'lateralus'))
# ---------- LY-1 (Osama 16 Nov 2026 12:28 PST, thread 1567745029781454889): "make it a unit for PLAN SOF, we use the same effect as the laser
# defense system on the ZTZ-99A and the same icon. It fires one pulse every burst. 1200m ground range, 1500 low, 1200 high. can engage munitions.
# it has 0 dispersion, 5 damage and 20mm of penetration, it also causes significant panic just like the ZTZ-99 version. call it LY-1. It also
# comes with the laser APS trait, it fires once every 3 seconds. 120 points."; 12:3x: "when I talk about my numbers, I'm talking unit card numbers".
# Model: work/pla-0.9/ly1 (HQ-17A hull + the purchased LY-1 laser turret), models.json "PLA LY-1" in the next Assets.
# Unit: the HQ-17A (1049) hull, armour, mobility and sensors; no missiles, no radar profile. Weapon: a copy of the dev.26 LSDW (1 pulse per
# burst, 1.0 s between pulses, magazine 250, 1000 pulses, aim 0.5 s, 80 stress over 3 m a pulse = the ZTZ-99A panic) as an anti-air gun
# (type 115 like the C-RAM M61, so Intercept Lead treats it as a missile-defence gun), elevation 85 deg like the M61. Pulse: card range is
# 2 x data, so ground 600 / low 750 / high 600; targets 1983 = the C-RAM 20 mm set (ground, air, ships and every munition: projectiles, SEAD,
# cruise, ballistic); dispersion 0; damage 5 (missiles have 5 HP since dev.13: one pulse kills); penetration 20 mm at every range.
# Laser APS: a copy of the LSDW APS (999 charges, no supply) with a 3 s cooldown, the unit's one built-in ability. dazzler.json lists the unit
# (APS reach and beam) and the weapon name (beam per pulse, card icon). Card: PLAN SF (20), 2 cards (count not given; as the HHQ-10).
W=t['WeaponsJson'];AM=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];TJ=t['TurretsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson']
AR=t['ArmorsJson'];MOB=t['MobilityJson'];SAJ=t['SpecializationAvailabilitiesJson']
def _rows(tab,**kw):return [r for r in t[tab].values() if all(r.get(k)==v for k,v in kw.items())]
_lw=[w['Id'] for w in W.values() if w.get('HUDName')=='LSDW'];ok(len(_lw)==1,'one LSDW weapon');_lw=_lw[0]
_la={r['AmmunitionId'] for r in WA.values() if r['WeaponId']==_lw};ok(len(_la)==1,'one LSDW pulse');_la=_la.pop()
ok((W[_lw]['ShotsPerBurstMax'],W[_lw]['TimeBetweenBurstsMin'],W[_lw]['TimeBetweenBurstsMax'],W[_lw]['MagazineSize'],W[_lw]['HUDIcon'])==(1,1.0,1.0,250,'FA_PLA_WP_LSDW_DAZZLER'),'LSDW dev.26: 1 pulse / 1.0 s, magazine 250, LSDW icon')
ok((AM[_la]['StressDamage'],AM[_la]['StressAOERadius'],AM[_la]['TrajectoryType'],AM[_la]['Seeker'])==(80.0,3.0,10,0),'LSDW pulse dev.26: 80 stress over 3 m, direct, unguided')
_lap=[a_['Id'] for a_ in AB.values() if a_.get('Name')=='PLA LSDW laser defense'];ok(len(_lap)==1 and AB[_lap[0]]['IsAPS'] and AB[_lap[0]]['APSQuantity']==999,'LSDW laser APS');_lap=_lap[0]
ok(U[1049]['HUDName']=='HQ-17A' and not _rows('ModificationsJson',UnitId=1049) and [r['TurretId'] for r in _rows('TurretUnitsJson',UnitId=1049)]==[2010626],'HQ-17A: no options, one mount 2010626')
ok(not any(u.get('Name')=='PLA LY-1' for u in U.values()),'PLA LY-1 name free')
_d=dict(U[1049]);_d.pop('Id');_d.update({'Name':'PLA LY-1','HUDName':'LY-1','Cost':120,'Description':None,'OriginalName':None})
ly=g.put('Units',max(U)+1,_d)
for r in _rows('SensorUnitsJson',UnitId=1049):g.add('SensorUnitsJson',r,{'UnitId':ly})
_ua=[r for r in _rows('UnitArmorsJson',UnitId=1049) if AR[r['ArmorId']].get('IsDefault')];ok(len(_ua)==1,'HQ-17A one default armour')
g.add('UnitArmorsJson',_ua[0],{'UnitId':ly,'ArmorId':g.add('ArmorsJson',AR[_ua[0]['ArmorId']],{'Name':'PLA LY-1 ArmorsJson'})})
_up=_rows('UnitPropulsionsJson',UnitId=1049);ok(len(_up)==1,'HQ-17A one mobility')
g.add('UnitPropulsionsJson',_up[0],{'UnitId':ly,'MobilityId':g.add('MobilityJson',MOB[_up[0]['MobilityId']],{'Name':'PLA LY-1 MobilityJson'})})
_ab=g.add('AbilitiesJson',AB[_lap],{'Name':'PLA LY-1 laser defense','APSCooldown':3.0,'IsDefault':True})
g.add('UnitAbilitiesJson',{'UnitId':ly,'AbilityId':_ab})
lyw=g.add('WeaponsJson',W[_lw],{'Name':'PLA LY-1 laser weapon','HUDName':'LY-1 laser','Type':115,'UpperVerticalAngles':85,'VerticalRotationSpeed':115})
lya=g.add('AmmunitionsJson',AM[_la],{'Name':'PLA LY-1 laser pulse','HUDName':'LY-1 laser pulse','Damage':5.0,'PenetrationAtMinRange':20.0,'PenetrationAtGroundRange':20.0,
  'GroundRange':600.0,'LowAltRange':750.0,'HighAltRange':600.0,'TargetType':1983,'DispersionHorizontalRadius':0.0,'DispersionVerticalRadius':0.0,'DispersionMinimal':0.0})
_lt=g.add('TurretsJson',TJ[2010626],{'Name':'PLA LY-1 laser mount','IsDefault':True})
g.add('TurretWeaponsJson',next(x for x in TW.values() if x['TurretId']==2010626),{'TurretId':_lt,'WeaponId':lyw,'Order':0,'WeaponChannel':0,'WeaponPriority':0})
g.add('TurretUnitsJson',{'UnitId':ly,'TurretId':_lt,'Order':0})
g.add('WeaponAmmunitionsJson',{'UnitId':ly,'WeaponId':lyw,'AmmunitionId':lya,'Quantity':1000,'Order':0})
g.add('SpecializationAvailabilitiesJson',{'SpecializationId':20,'UnitId':ly,'MaxAvailabilityXp0':2,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0});assign['assignments'][str(ly)]=[20]
ok([(W[x['WeaponId']]['HUDName'],AM[r['AmmunitionId']]['HUDName'],r['Quantity']) for r in _rows('WeaponAmmunitionsJson',UnitId=ly) for x in TW.values() if x['TurretId']==_lt]==[('LY-1 laser','LY-1 laser pulse',1000)],'LY-1: laser only')
_p=AM[lya];ok((_p['Damage'],_p['PenetrationAtMinRange'],_p['PenetrationAtGroundRange'],_p['GroundRange']*2,_p['LowAltRange']*2,_p['HighAltRange']*2,_p['TargetType']&1920,_p['DispersionHorizontalRadius'])==(5.0,20.0,20.0,1200.0,1500.0,1200.0,1920,0.0),'LY-1 pulse: 5 dmg, 20 mm, card 1200/1500/1200 m, munitions, no dispersion')
ok([AB[r['AbilityId']]['APSCooldown'] for r in _rows('UnitAbilitiesJson',UnitId=ly) if AB[r['AbilityId']]['IsDefault']]==[3.0] and len(_rows('UnitAbilitiesJson',UnitId=ly))==1,'LY-1: one built-in laser APS, 3 s')
ok(U[ly]['Cost']==120 and [(c['SpecializationId'],c['MaxAvailabilityXp0']) for c in _rows('SpecializationAvailabilitiesJson',UnitId=ly)]==[(20,2)],'LY-1: 120 points, PLAN SF, 2 cards')
DZ=SRC/'UserData/FreedomArrow/dazzler.json';_dz=json.loads(DZ.read_text())
ok(_dz['units'][:2]==[904,1083] and _dz['laserWeaponNames'][0]=='LSDW' and _dz['cardIcon']=='FA_PLA_ABILITY_LSDW','dazzler.json ZTZ-99A/99 LSDW')
_dz['units']=[x for x in _dz['units'] if x!=ly]+[ly];_dz['laserWeaponNames']=[x for x in _dz['laserWeaponNames'] if x!='LY-1 laser']+['LY-1 laser']
rec['ly1']={'unit':ly,'cost':120,'spec':20,'cards':2,'weapon':lyw,'ammo':lya,'mount':_lt,'ability':_ab,'aps_cooldown_s':3.0,
  'card_range_m':{'ground':1200,'low':1500,'high':1200},'damage':5.0,'penetration_mm':20,'stress':80.0,'pulse_s':1.0,'targets':1983,'model':'PLA LY-1 (work/pla-0.9/ly1)'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);DZ.write_text(json.dumps(_dz,indent=2,ensure_ascii=False)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

