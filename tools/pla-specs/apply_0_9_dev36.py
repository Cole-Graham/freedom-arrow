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
# ---------- Osama 17 Nov 2026 10:2x PST: "ZTQ-15 seems to not have all its weapons", "remove ztz-85-II"; 17 Nov 11:1x PST (thread 1571014792016171120):
# "no swap the kurganets stand in. I tested and it fucked up", "the ZTQ-15 does not fire its other weapons, we'll need to swap it for the bulat".
# ZTQ-15, Recon and Light sat on the M10 body with three mounts: the 105 mm on the M10 turret (works), Type 86 + QJC-88 on the BTR-82AT turret part
# (2019317) and LG3 on a mount with no model part (2018997). The M10 body has neither part, so those three guns had no point to fire from.
# Now on the Kurganets body with one mount on its 57 mm turret part (RU_Kurganets57mm, vanilla mount 470: 2A94, PKT, Kornet, Bulat = 4 weapon
# points): 105 mm, Type 86, QJC-88, LG3 at orders 0-3. The model is still the ZTQ-15 (FAModels, by name). VT-5 keeps the old M10 layout (not asked).
_TW,_TU,_TT=t['TurretWeaponsJson'],t['TurretUnitsJson'],t['TurretsJson'];_ZTQ=[906,1240,1268]
def _ztq(u):return [(r['TurretId'],[_W[w['WeaponId']]['HUDName'] for w in sorted((w for w in _TW.values() if w['TurretId']==r['TurretId']),key=lambda w:w['Order'])]) for r in sorted((r for r in _TU.values() if r['UnitId']==u),key=lambda r:r['Order'])]
_old=[(2009128,['105 mm high-pressure rifled gun']),(2019317,['Type 86 7.62 mm','QJC-88 12.7 mm']),(2018997,['LG3 40 mm AGL'])]
ok(all(U[u]['ModelFileName']=='US_M10' and _ztq(u)==_old for u in _ZTQ),'ZTQ-15 x3 on M10 with the three old mounts')
ok(all(sorted({r['UnitId'] for r in _TU.values() if r['TurretId']==k})==_ZTQ for k in (2019317,2018997)),'mounts 2019317/2018997 ZTQ-15 only')
_mt=g.add('TurretsJson',_TT[2009128],{'Name':'PLA ZTQ-15 mount 0 Kurganets 57','ModelFileName':'RU_Kurganets/RU_Kurganets57mm'})
for _i,_src in enumerate((2009130,2019318,2019319,2018998)):
    g.add('TurretWeaponsJson',_TW[_src],{'TurretId':_mt,'Order':_i,'WeaponChannel':0,'WeaponPriority':_i})
for _u in _ZTQ:
    g.put('Units',_u,{'ModelFileName':'RU_Kurganets'})
    for _r in [r for r in _TU.values() if r['UnitId']==_u]:
        if _r['TurretId']==2009128:g.put('TurretUnitsJson',_r['Id'],{'TurretId':_mt,'Order':0})
        else:g.remove('TurretUnitsJson',_r['Id'])
for _k in (2019317,2018997):
    for _r in [r for r in _TW.values() if r['TurretId']==_k]:g.remove('TurretWeaponsJson',_r['Id'])
    g.remove('TurretsJson',_k)
_new=[(_mt,['105 mm high-pressure rifled gun','Type 86 7.62 mm','QJC-88 12.7 mm','LG3 40 mm AGL'])]
ok(all(U[u]['ModelFileName']=='RU_Kurganets' and _ztq(u)==_new for u in _ZTQ),'ZTQ-15 x3 on Kurganets, one 57 mm mount, 4 weapons')
ok(sorted(w['Order'] for w in _TW.values() if w['TurretId']==_mt)==[0,1,2,3] and _TT[_mt]['ModelFileName']=='RU_Kurganets/RU_Kurganets57mm','mount numbered 0-3 on the Kurganets 57 mm part')
ok(all(U[u]['ModelFileName']=='US_M10' and _ztq(u)[0][0]==2009128 for u in (1261,1262)),'VT-5 unchanged')
rec['ztq15_kurganets']={'units':_ZTQ,'model':['US_M10','RU_Kurganets'],'mount':_mt,'part':'RU_Kurganets/RU_Kurganets57mm','removed_mounts':[2019317,2018997]}
# ZTZ-85-II (1264): its only deck card (row 2018800, PLARF Conscript, 6) goes; the unit row stays for old saves and decks.
_SA=t['SpecializationAvailabilitiesJson']
ok(U[1264]['HUDName']=='ZTZ-85-II' and [r['Id'] for r in _SA.values() if r.get('UnitId')==1264]==[2018800] and assign['assignments'].get('1264')==[19],'ZTZ-85-II one deck row, assignment 19')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r.get('UnitId')==1264 or r.get('SpecializationAvailabilityId')==2018800],'ZTZ-85-II: no transport links')
g.remove('SpecializationAvailabilitiesJson',2018800);assign['assignments'].pop('1264',None)   # as WZ-550 in dev.32
ok(not any(r.get('UnitId')==1264 for r in _SA.values()),'ZTZ-85-II in no deck')
rec['ztz85ii_removed']={'unit':1264,'deck_row':2018800}
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
# ---------- Brown explosion sheet test switch (Osama 17 Nov 2026 10:4x PST, thread 1567745029781454889, TARS handoff effects-brown-sheet-20261117):
# runtime only, off by default. runtime-qa/HideTextureTest.cs blanks loaded textures named in UserData/FreedomArrow/hide-textures.json
# ({"textures": ["Texture_Smoke_Brown_BaseMap"]}) on the GPU and restores them when the name or file goes; read every 3 s, so it switches in a match.
rec['hide_texture_test']={'runtime':'HideTextureTest.cs','switch':'UserData/FreedomArrow/hide-textures.json','default':'off'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
