"""Freedom Arrow 0.9.2-dev.1 data over exact 0.9.1 (19 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama, QN-506 / Type 86 spawn failure).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.2-dev.1';PREV='0.9.1'
# 0.9.1 was built in out/local-091.
BASE=json.loads((REL/f'out/local-091/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Weapon positions on body hull slots (Osama 19 Nov 2026 16:3x PST, thread 1571014792016171120: "can we make sure they're fixed?",
# after End's 0.9.1 log: "CombatSystem initialization for unit=PLA QN-506 failed" and "...PLA Catalogue Type 86 — original turret failed",
# IndexOutOfRange in UnitBuilder.SetupWeaponComponents, then a TurretComponent error every frame). Game code 1.2.2.1:
#  - InitCombatSystem(UnitModelInfo, Units) 0x3470C0 gives the unit's turret i the BODY prefab's turret script MainTurrets[i].
#  - SetupWeaponComponents 0x351B20 walks the turret's weapon list (padded with nulls up to each row's Order, LoadUnits.LoadWeapons) and, for
#    each real weapon at index k, reads that script's weapon point k (bounds check 0x351EEE). Null pads are skipped.
#  So a weapon at Order k on a body slot that vanilla fills with a model-less hull mount needs that hull mount to have more than k points.
#  BMPT slots 1/2 (AGS-17), BMD-2 slot 1 and BMP-3F slot 1 (PKT) have 1 point; Pantsir slot 0 has 2 (2A38M, 57E6E).
#  The dev.7 fix (QN-201 off slot 2) cut the count only; Osama's own GameLogs show QN-506 failing on 15, 16 and 17 Nov after it.
# Fix: each weapon takes the lowest free position its vanilla body slot has. Its muzzle may move to the body's hull weapon point.
_FIX=[  # (turret, weapon, unit names, Order before, Order after)
    (2009642,2009641,'QN-506 mount 1 Type 86 7.62 mm',1,0),
    (2009648,2009647,'QN-506 mount 2 QN-502',2,0),
    (2010896,2010895,'ZBD-86 / ZBD-86 Recon x2 mount 1 Type 86 7.62 mm',1,0),
    (2011202,2011201,'ZBD-05 mount 1 Type 86 7.62 mm',1,0),
    (2009600,2009605,'FK-2000 mount 0 FK-2000 SAM',2,1)]
TW=t['TurretWeaponsJson'];rec['hull_slot_weapon_order']=[]
for tid,wid,name,o0,o1 in _FIX:
    rows=[r for r in TW.values() if r['TurretId']==tid]
    ok([(r['WeaponId'],r['Order']) for r in rows if r['WeaponId']==wid]==[(wid,o0)],(name,[(r['WeaponId'],r['Order']) for r in rows]))
    ok(all(r['Order']!=o1 for r in rows if r['WeaponId']!=wid),(name,'target position taken'))
    rid=next(r['Id'] for r in rows if r['WeaponId']==wid);g.put('TurretWeaponsJson',rid,{'Order':o1});ok(TW[rid]['Order']==o1,name)
    rec['hull_slot_weapon_order'].append({'turret':tid,'weapon':wid,'row':rid,'name':name,'Order':[o0,o1]})
ok(sorted(r['UnitId'] for r in t['TurretUnitsJson'].values() if r['TurretId']==2010896)==[1063,1258,1259],'Type 86 mount 1 is on the 3 ZBD-86 cards')
rec['hull_slot_weapon_order_verified']='data checks only'
# ---------- Squad health = 5 HP per soldier (Osama 19 Nov 2026 16:42 PST, thread 1567745029781454889: "Yeah can we fix these? and make sure other
# units have same health matching their man power", after QQ bug FA-003 "godswords东方神剑的血量应该为60而不是30"). Every vanilla squad has
# MaxHealthPoints = 5 x soldiers (4 men 20, 12 men 60). In 0.9.1 six China squads were off. Each was alone on its own FA armour row, identical to
# a vanilla row except for HP, so the unit's UnitArmors row now links that vanilla row (one row per combination, no new rows):
# 4 men -> vanilla 80 'Armor Infantry 4Men' (HP 20); 12 men -> vanilla 283 'Armor Infantry Elite 12Men' (HP 60). Every other infantry squad
# that a specialization offers (US, Russia, China) already matched. Build check: check_squad_hp.py (packager).
AR=t['ArmorsJson'];UA=t['UnitArmorsJson'];SM=t['SquadMembersJson']
_HP=[  # (unit, UnitArmors row, FA armour row, HP before, soldiers, vanilla row)
    (1137,2011858,2011857,25,4,80),(1139,2011913,2011912,30,4,80),(1140,2011943,2011942,25,4,80),
    (1145,2012075,2012074,25,4,80),(1181,2013081,2013080,30,12,283),(1213,2014053,2014052,30,4,80)]
rec['squad_hp_5_per_soldier']=[]
for uid,uar,old,hp0,n,van in _HP:
    ok(UA[uar]['UnitId']==uid and UA[uar]['ArmorId']==old and AR[old].get('MaxHealthPoints')==hp0,(uid,'0.9.1 armour'))
    ok(sum(1 for r in SM.values() if r['UnitId']==uid)==n,(uid,'soldiers',n))
    ok(sum(1 for r in UA.values() if r['ArmorId']==old)==1,(uid,'FA row shared'))
    ok(van in native['ArmorsJson'] and AR[van].get('MaxHealthPoints')==5*n,(uid,'vanilla row',van))
    ok(all(AR[van].get(k)==AR[old].get(k) for k in AR[old] if k not in('Id','Name','MaxHealthPoints')),(uid,'only HP differs',van))
    g.put('UnitArmorsJson',uar,{'ArmorId':van});ok(UA[uar]['ArmorId']==van,uid)
    rec['squad_hp_5_per_soldier'].append({'unit':uid,'name':U[uid]['HUDName'],'soldiers':n,'HP':[hp0,5*n],'UnitArmors':uar,'ArmorId':[old,van]})
import collections as _c
_men=_c.Counter(r['UnitId'] for r in SM.values());_live={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values()}
_bad=[(r['UnitId'],AR[r['ArmorId']].get('MaxHealthPoints')) for r in UA.values() if U.get(r['UnitId'],{}).get('Type')==2 and r['UnitId'] in _live and _men[r['UnitId']] and AR[r['ArmorId']].get('MaxHealthPoints')!=5*_men[r['UnitId']]]
ok(not _bad,('squads still off',_bad))
# ---------- Tank Hunters 8 men, ZTQ-15 prices (Osama 19 Nov 2026 16:4x PST, thread 1567745029781454889: "Tank hunters to 8 man (and HP) and 75 pts";
# "ZTQ-15 light 155 points, ZTQ-15 (base) 175 points, ZTQ-15 Recon 195"). Tank Hunters 坦克杀手 (1139): 4 -> 8 soldiers. The 4 new soldiers copy
# rifleman 2014882 (QBZ-191, no launcher), so the squad keeps one PF-98A launcher and its 6 PF-98A + 6 DZT-98 rounds (one launcher per team).
# Bodies and rifles come from FAModels' per-unit maps (soldierIndex -1), so no model rows change. Armour: vanilla 84 'Armor Infantry 8Men' (HP 40;
# same fields as 80 apart from HP). Every transport offered with it carries 8 or more (Z-20KA 13, Z-9 8, ZBD-251 9, Lynx ATV 9, ZSD-89A 12, CSK-131 12).
# Price 50 -> 75. ZTQ-15 Light (1268) 140 -> 155, ZTQ-15 (906) 130 -> 175, ZTQ-15 Recon (1240) 145 -> 195; none has a loadout or swap row.
_th=[r for r in SM.values() if r['UnitId']==1139];ok(len(_th)==4 and sum(1 for r in _th if r.get('SpecialWeaponId'))==1,'Tank Hunters 4 men, 1 launcher')
_rif=SM[2014882];ok(_rif['UnitId']==1139 and not _rif.get('SpecialWeaponId'),'rifleman template')
_new=[g.add('SquadMembersJson',_rif) for _ in range(4)]
ok(sum(1 for r in SM.values() if r['UnitId']==1139)==8 and all(set(SM[i])==set(_rif) for i in _new),'Tank Hunters 8 men, rows like the template')
ok(UA[2011913]['UnitId']==1139 and UA[2011913]['ArmorId']==80,'Tank Hunters armour 4Men');ok(AR[84].get('MaxHealthPoints')==40 and all(AR[84].get(k)==AR[80].get(k) for k in AR[80] if k not in('Id','Name','MaxHealthPoints')),'vanilla 84 = 80 but HP 40')
g.put('UnitArmorsJson',2011913,{'ArmorId':84})
_slots=[U[r['UnitId']].get('InfantrySlots') for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId'] in {x['Id'] for x in t['SpecializationAvailabilitiesJson'].values() if x['UnitId']==1139}]
ok(_slots and min(_slots)>=8,('transports carry 8',_slots))
_PR={1139:(50,75),1268:(140,155),906:(130,175),1240:(145,195)}
for uid,(c0,c1) in _PR.items():
    ok(U[uid]['Cost']==c0 and not U[uid].get('OriginalCost'),(uid,'price before'));g.put('Units',uid,{'Cost':c1})
    ok(not any(o.get('ReplaceUnitId')==uid for o in t['OptionsJson'].values()),(uid,'swap row'))
_bad=[(r['UnitId'],AR[r['ArmorId']].get('MaxHealthPoints')) for r in UA.values() if U.get(r['UnitId'],{}).get('Type')==2 and r['UnitId'] in _live and AR[r['ArmorId']].get('MaxHealthPoints')!=5*sum(1 for x in SM.values() if x['UnitId']==r['UnitId'])]
ok(not _bad,('squads off after Tank Hunters',_bad))
rec['tank_hunters_8_men']={'unit':1139,'soldiers':[4,8],'new_SquadMembers':_new,'template':2014882,'ArmorId':[80,84],'HP':[20,40],'Cost':[50,75],'launchers':1}
rec['ztq15_prices']={str(k):list(v) for k,v in _PR.items() if k!=1139}
# ---------- FS-70A / FS-90 = APKWS (Osama 19 Nov 2026 16:5x PST, thread 1567745029781454889: "FS-90 and 70 have way more penetration compared to
# apkws it should be the same"). Both China laser-guided 70 mm rockets were vanilla helicopter APKWS (ammo 45) copies with AT values: damage 8 / 9,
# penetration 400, no blast, stress 160 / AOE 16. They now take APKWS's damage 3.5, penetration 60/60, stress 140, health and stress AOE 14 m.
# Range, guidance, Ignore Cover 0.6, dispersion and supply cost were already the same.
_A=t['AmmunitionsJson'];_F=['Damage','StressDamage','PenetrationAtMinRange','PenetrationAtGroundRange','HealthAOERadius','StressAOERadius']
rec['fs_rockets_like_apkws']={}
for _i in (2017197,2018819):
    ok(_A[_i]['HUDName'] in ('FS-70A','FS-90') and _A[_i]['PenetrationAtGroundRange']==400.0,(_i,'FS rocket before'))
    _old={f:_A[_i].get(f) for f in _F};g.put('AmmunitionsJson',_i,{f:_A[45][f] for f in _F})
    ok(all(_A[_i].get(k)==_A[45].get(k) for k in _A[45] if k not in('Id','Name','HUDName')),(_i,'equal to APKWS 45'))
    rec['fs_rockets_like_apkws'][_A[_i]['HUDName']]={'ammo':_i,'from':_old,'to':{f:_A[45][f] for f in _F}}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
