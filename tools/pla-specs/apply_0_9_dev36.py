"""Freedom Arrow 0.9.0-dev.36 data over exact 0.9.0-dev.35 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.36';PREV='0.9.0-dev.35'
# dev.35 was built in out/local-dev35.
BASE=json.loads((REL/f'out/local-dev35/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev35/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- "a lot of models have this weird giant 2d splash, see it on the JRVG in skirmish" / "the weird giant bomb splash" (Osama 16 Nov 2026 22:2x-22:4x PST,
# thread 1571014792016171120). The JRVG-1 76 mm proximity round (ammo, JRVG-1 only) uses AMMUNITION_VFX_PRESET_SHELL_127mm_HE, an effect only ships use in
# vanilla (naval gun, sea impact). No other land unit uses a ship-only effect. It gets the 57 mm HE effect its other round uses. Not yet seen in game.
_A=t['AmmunitionsJson']
_jr=[x for x in t['WeaponAmmunitionsJson'].values() if x['UnitId']==952];_px=[x['AmmunitionId'] for x in _jr if _A[x['AmmunitionId']].get('HUDName')=='76 mm HE (proximity)']
ok(len(_px)==1 and _A[_px[0]]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_127mm_HE' and {x['UnitId'] for x in t['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==_px[0]}=={952},'JRVG-1 proximity round on the naval 127 mm effect, JRVG only')
g.put('AmmunitionsJson',_px[0],{'FXPreset':'AMMUNITION_VFX_PRESET_ROUND_57mm_HE'});ok(_A[_px[0]]['FXPreset']=='AMMUNITION_VFX_PRESET_ROUND_57mm_HE','JRVG-1 proximity round 57 mm HE effect')
rec['jrvg_proximity_fx']={'ammo':_px[0],'fx':['AMMUNITION_VFX_PRESET_SHELL_127mm_HE','AMMUNITION_VFX_PRESET_ROUND_57mm_HE']}
# ---------- "isnt the Z-21 CM-501GA an LMUR copy?" (Osama 16 Nov 2026 23:0x PST): yes, ammo 2017128 copies the vanilla LMUR (449): 1000 m, seeker 50, seeker
# reach 250 m, trajectory 110. It differed in TargetType: 35 = Ground + Infantry + Ship, no Vehicle bit (TargetType enum 1/2/4/8/16/32), so the Z-21 never fired
# it at vehicles. LMUR is 38 = Infantry + Vehicle + Ship. dev.35's seeker reach 1000 m (wrong cause) goes back to the LMUR's 250 m.
ok(_A[2017128]['TargetType']==35 and _A[2017128]['MaxSeekerDistance']==1000.0 and {x['UnitId'] for x in t['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==2017128}=={1104},'CM-501GA TargetType 35, seeker 1000 (dev.35), Z-21 only')
g.put('AmmunitionsJson',2017128,{'TargetType':38,'MaxSeekerDistance':250.0});ok(_A[2017128]['TargetType']==38 and _A[2017128]['MaxSeekerDistance']==250.0,'CM-501GA = LMUR targets and seeker')
rec['cm501ga']={'ammo':2017128,'TargetType':[35,38],'MaxSeekerDistance':[1000,250],'template':'vanilla LMUR 449'}
# ---------- Alarms (Osama 17 Nov 2026 10:1x PST, thread 1567745029781454889: "swap the air warning out and make that the missile warning and then remove
# the air warning in general because I think there already is one in vanilla"). Runtime only (runtime-qa/AlertSounds.cs): the ballistic missile alarm
# plays the Arleigh Burke sound (audio/aircraft-alarm-burke.ogg) instead of the C-RAM "incoming"; nothing plays on the aircraft warning any more.
# Nuclear launch announcements (Osama 17 Nov 10:2x PST: "these should start fading out after 3.5 seconds a bit earlier on the nuclear warnings"):
# audio/nuke-warning-{cn,us,ru}.mp3 fade out from 3.5 s to 5.0 s and end there (were 11.9 s).
rec['alarms']={'ballistic':'aircraft-alarm-burke.ogg','aircraft':'none','nuclear_fade':[3.5,5.0]}
# ---------- "The CM-501GA should be a LMUR clone" (Osama 16 Nov 2026 23:0x PST): the rest of the LMUR (vanilla ammo 449, weapon 603) is copied, except
# names and icon. Ammo IgnoreCover 1.0 -> 0.0. Weapon 2017902 (Z-21 only): Type 80 -> 81 (LMUR's launcher type), aim arc -30..+30 at 80 deg/s, tracks 2
# targets, 24-32 s between bursts, 1 s between the shots of a burst.
import json as _json
_VW={r['Id']:r for r in _json.loads((a.vanilla/'WeaponsJson.json').read_text())}
_W=t['WeaponsJson'];_L=_VW[603]
ok(_A[2017128]['IgnoreCover']==1.0 and {x['UnitId'] for x in t['WeaponAmmunitionsJson'].values() if x['WeaponId']==2017902}=={1104},'CM-501GA IgnoreCover 1, weapon Z-21 only')
g.put('AmmunitionsJson',2017128,{'IgnoreCover':0.0})
_keys=('Type','LowerVerticalAngle','UpperVerticalAngles','VerticalRotationSpeed','MultiTargetTracking','TimeBetweenBurstsMin','TimeBetweenBurstsMax','TimeBetweenShotsInBurst')
g.put('WeaponsJson',2017902,{k:_L.get(k) for k in _keys})
_VA={r['Id']:r for r in _json.loads((a.vanilla/'AmmunitionsJson.json').read_text())}
ok(all(_A[2017128].get(k)==_VA[449].get(k) for k in _VA[449] if k not in ('Id','Name','HUDName')) and all(_W[2017902].get(k)==_L.get(k) for k in _L if k not in ('Id','Name','HUDName','HUDIcon')),'CM-501GA = LMUR except names and icon')
rec['cm501ga_lmur_clone']={'ammo':2017128,'weapon':2017902,'template':{'ammo':449,'weapon':603}}
# ---------- Osama 17 Nov 2026 10:2x PST: "ZTQ-15 seems to not have all its weapons" and "remove ztz-85-II".
# ZTQ-15, Recon and Light share mount 1 (2019317: Type 86 at order 1, QJC-88 at order 2) and mount 2 (2018997: LG3 at order 2). The game builds each mount's
# weapon list by order and puts an empty slot for every skipped number, so mount 1 got one empty slot and mount 2 two. Vanilla numbers each mount from 0 without
# gaps (Kurganets 57 mm turret 0,1,2,3). Renumbered from 0. The Kurganets stand-in (Osama's idea) is kept for later if weapons are still missing.
_TW,_TU=t['TurretWeaponsJson'],t['TurretUnitsJson']
for _tur,_want in ((2019317,[(1,'Type 86 7.62 mm'),(2,'QJC-88 12.7 mm')]),(2018997,[(2,'LG3 40 mm AGL')])):
    _rows=sorted((r for r in _TW.values() if r['TurretId']==_tur),key=lambda r:r['Order'])
    ok([(r['Order'],t['WeaponsJson'][r['WeaponId']].get('HUDName')) for r in _rows]==_want and sorted({r['UnitId'] for r in _TU.values() if r['TurretId']==_tur})==[906,1240,1268],f'ZTQ-15 mount {_tur} orders {_want}')
    for _i,_r in enumerate(_rows):g.put('TurretWeaponsJson',_r['Id'],{'Order':_i})
    ok([r['Order'] for r in sorted((r for r in _TW.values() if r['TurretId']==_tur),key=lambda r:r['Order'])]==list(range(len(_rows))),f'ZTQ-15 mount {_tur} numbered from 0')
# ZTZ-85-II (1264): its only deck card (row 2018800, PLARF Conscript, 6) goes; the unit row stays for old saves and decks.
_SA=t['SpecializationAvailabilitiesJson']
ok(U[1264]['HUDName']=='ZTZ-85-II' and [r['Id'] for r in _SA.values() if r.get('UnitId')==1264]==[2018800] and assign['assignments'].get('1264')==[19],'ZTZ-85-II one deck row, assignment 19')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r.get('UnitId')==1264 or r.get('SpecializationAvailabilityId')==2018800],'ZTZ-85-II: no transport links')
g.remove('SpecializationAvailabilitiesJson',2018800);assign['assignments'].pop('1264',None)   # as WZ-550 in dev.32
ok(not any(r.get('UnitId')==1264 for r in _SA.values()),'ZTZ-85-II in no deck')
rec['ztq15_mount_orders']={'2019317':[[1,2],[0,1]],'2018997':[[2],[0]]};rec['ztz85ii_removed']={'unit':1264,'deck_row':2018800}
# ---------- ZTZ-59 and ZTZ-80 (Osama 17 Nov 2026 10:3x PST, thread 1567745029781454889: "ZTZ-59 to 10 HP, 45 forward speed, 45 ppoints", "ZTZ-80 shows 72
# forward move, this should be 60 forward, 65 points"). Forward = road speed (MaxSpeedRoad, what the card shows). ZTZ-59 (1060): HP 12 -> 10, road 50 -> 45,
# 55 -> 45 points. ZTZ-80 (1061, the renamed Type 59D card): road 72 -> 60, 60 -> 65 points. Own armour/mobility rows only; the ZTZ-59D1 recon copy
# (1260, own mobility 2018623 at 72) is not changed.
_AR=t['ArmorsJson'];_MB=t['MobilityJson']
def _one(tab,uid,key):
    r=[x for x in t[tab].values() if x['UnitId']==uid];ok(len(r)==1 and len([x for x in t[tab].values() if x[key]==r[0][key]])==1,(tab,uid,'own row'));return r[0][key]
_a59=_one('UnitArmorsJson',1060,'ArmorId');_m59=_one('UnitPropulsionsJson',1060,'MobilityId');_m80=_one('UnitPropulsionsJson',1061,'MobilityId')
ok((U[1060]['HUDName'],U[1060]['Cost'],_AR[_a59]['MaxHealthPoints'],_MB[_m59]['MaxSpeedRoad'])==('ZTZ-59',55,12,50.0),'ZTZ-59 55, 12 HP, road 50')
ok((U[1061]['HUDName'],U[1061]['Cost'],_MB[_m80]['MaxSpeedRoad'])==('ZTZ-80',60,72.0),'ZTZ-80 60, road 72')
g.put('Units',1060,{'Cost':45});g.put('ArmorsJson',_a59,{'MaxHealthPoints':10});g.put('MobilityJson',_m59,{'MaxSpeedRoad':45.0})
g.put('Units',1061,{'Cost':65});g.put('MobilityJson',_m80,{'MaxSpeedRoad':60.0})
ok((U[1060]['Cost'],_AR[_a59]['MaxHealthPoints'],_MB[_m59]['MaxSpeedRoad'],U[1061]['Cost'],_MB[_m80]['MaxSpeedRoad'])==(45,10,45.0,65,60.0),'ZTZ-59 45 pts 10 HP road 45; ZTZ-80 65 pts road 60')
rec['ztz59_ztz80']={'ztz59':{'cost':[55,45],'hp':[12,10],'road':[50,45]},'ztz80':{'cost':[60,65],'road':[72,60]}}
# ---------- WZ1224 130 (Osama 17 Nov 2026 10:3x PST, thread 1567745029781454889: "WZ 1224 130 points"): unit 1272 110 -> 130.
ok(U[1272]['HUDName']=='WZ1224' and U[1272]['Cost']==110,'WZ1224 110');g.put('Units',1272,{'Cost':130});ok(U[1272]['Cost']==130,'WZ1224 130')
rec['wz1224_cost']=[110,130]
# ---------- PTZ-89 off the deck (Osama 17 Nov 2026 10:3x PST, thread 1567745029781454889: "ptz-89 removed, model looks ugly"): its only card 2008238
# (PLARF, 6) is removed; no transport links; the unit row stays hidden, like earlier removals.
_SA=t['SpecializationAvailabilitiesJson']
ok(U[947]['HUDName']=='PTZ-89' and [(c['Id'],c['SpecializationId']) for c in _SA.values() if c['UnitId']==947]==[(2008238,19)] and not [r for r in t['TransportAvailabilitiesJson'].values() if r['UnitId']==947 or r['SpecializationAvailabilityId']==2008238],'PTZ-89: one PLARF card, no transport links')
g.remove('SpecializationAvailabilitiesJson',2008238);assign['assignments'].pop('947',None)
ok(not [c for c in _SA.values() if c['UnitId']==947],'PTZ-89 has no card')
rec['ptz89_removed']=2008238
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
