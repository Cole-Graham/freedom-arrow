"""Freedom Arrow 0.9.0-dev.32 data over exact 0.9.0-dev.31 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama: LY-1 radar, laser effect).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.32';PREV='0.9.0-dev.31'
# dev.31 was built in out/local-dev31.
BASE=json.loads((REL/f'out/local-dev31/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev31/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LY-1 radar (Osama 16 Nov 2026 14:3x PST: "LY-1 needs a radar I forgot"). The LY-1 is on the HQ-17A hull; the HQ-17A's radar is
# its default ability 2010621 (IsRadar, low-altitude optics and weapon range x1.25, high-altitude optics x2, 5 s radar switch). A unit has one
# default ability, and the LY-1's is its own laser APS copy, so the radar fields go onto that same row (vanilla combines flags in one row,
# e.g. T-14 smoke + APS). Radar + APS in one row has no vanilla example: check the HUD buttons in game.
_hq=AB[2010621];ok(_hq['IsRadar'] and _hq['RadarLowAltOpticsModifier']==1.25 and _hq['RadarHighAltOpticsModifier']==2.0 and _hq['RadarSwitchCooldown']==5.0,'HQ-17A radar ability 2010621')
_ly=[a_['Id'] for a_ in AB.values() if a_.get('Name')=='PLA LY-1 laser defense'];ok(len(_ly)==1 and AB[_ly[0]]['IsAPS'] and not AB[_ly[0]]['IsRadar'],'LY-1 laser APS, no radar yet');_ly=_ly[0]
_rad={k:v for k,v in _hq.items() if k.startswith('Radar') or k in ('IsRadar','IsRadarStatic')}
g.put('AbilitiesJson',_ly,_rad)
ok(all(AB[_ly][k]==v for k,v in _rad.items()) and AB[_ly]['IsAPS'] and AB[_ly]['APSCooldown']==10.0,'LY-1 ability: HQ-17A radar + laser APS 10 s')
rec['ly1_radar']={'ability':_ly,'from':2010621,'fields':sorted(_rad)}
# ---------- Lasers without the machine-gun look and sound (Osama 14:3x PST: "it also seems to have a machine gun effect, can we remove that?
# it looks like its firing a machine gun"). The LY-1 laser and the ZTZ-99A/99 LSDW laser were made from 7.62 mm MG rows (PKT sound, 7.62 tracer
# and MG impact burst). The game has no empty effect preset, so: weapon sound = the quiet subsonic sniper shot, impact sound = none (vanilla
# allows an empty ammunition sound), visual = the single sniper tracer. The red beam (dazzler.json) is unchanged.
W=t['WeaponsJson'];AM=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName') in ('LSDW','LY-1 laser')];ok(len(_lw)==2,'two laser weapons: LSDW, LY-1 laser')
_la=sorted({r['AmmunitionId'] for r in WA.values() if r['WeaponId'] in _lw});ok(len(_la)==2,'two laser pulse ammunitions')
ok(all(W[w]['AudioPreset']=='WEAPON_SOUND_PRESET_VEH_MACHINEGUN_Medium_Caliber_PKT' for w in _lw) and all(AM[x]['FXPreset']=='AMMUNITION_VFX_PRESET_7.62_BULLET_Shooting_RADIOFUSE' for x in _la),'lasers still on the PKT / 7.62 presets')
for w in _lw:g.put('WeaponsJson',w,{'AudioPreset':'WEAPON_SOUND_PRESET_INF_SNIPER_Subsonic'})
for x in _la:g.put('AmmunitionsJson',x,{'AudioPreset':'','FXPreset':'AMMUNITION_VFX_PRESET_Sniper_BULLET_US'})
ok(all(AM[x]['AudioPreset']=='' and AM[x]['FXPreset']=='AMMUNITION_VFX_PRESET_Sniper_BULLET_US' for x in _la),'laser pulses: no impact sound, sniper tracer')
rec['laser_effects']={'weapons':_lw,'ammo':_la,'weapon_sound':'WEAPON_SOUND_PRESET_INF_SNIPER_Subsonic','fx':'AMMUNITION_VFX_PRESET_Sniper_BULLET_US'}
# ---------- F-22 Symbiote (Osama 16 Nov 2026 14:2x PST, thread 1567745029781454889: "The F-22 mirror coat should be called symbiote coating and the
# name should change to F-22 Symbiote"). The mirror option keeps its internal Name (mirror-skins.json selects the skin by it); its button reads
# "Symbiote coating" and, like vanilla options such as Tor-M1/M2 or Dragoon (ReplaceUnitName), it renames the unit to "F-22 Symbiote".
_sym=[o['Id'] for o in t['OptionsJson'].values() if o.get('Name')=='F22 Mirror finish'];ok(len(_sym)==1 and t['OptionsJson'][_sym[0]]['UIName']=='Mirror finish' and t['OptionsJson'][_sym[0]]['Cost']==30,'one F-22 Mirror finish option (+30)')
g.put('OptionsJson',_sym[0],{'UIName':'Symbiote coating','ReplaceUnitName':'F-22 Symbiote'})
ok((t['OptionsJson'][_sym[0]]['UIName'],t['OptionsJson'][_sym[0]]['ReplaceUnitName'],t['OptionsJson'][_sym[0]]['Name'])==('Symbiote coating','F-22 Symbiote','F22 Mirror finish'),'Symbiote coating renames the unit F-22 Symbiote')
rec['f22_symbiote']={'option':_sym[0],'ui_name':'Symbiote coating','unit_name':'F-22 Symbiote'}
# ---------- J-20 / J-20S turn like the F-35 (Osama 16 Nov 2026 14:2x PST, thread 1567745029781454889: "J-20's should have the same turn radius as the
# F-35, in game displays 985", "both variants"). Card radius (fighter-turn-20261110: AircraftHelper.GetRotationRadius) = floor(round(2 x MaxSpeed x
# (1 + 1/tan MaxSpeedYaw))/5) x 5: F-35 preset 17 (225, 40 deg) = 985; J-20/J-20S mobility 31 "Plane Su57" with FA preset 2001429 (250, 82.5 deg)
# = 565. Mobility 31 is shared with the Su-57D and preset 2001429 with the F-22 and Su-35/47 rows, so both J-20s get their own copies. Their speeds,
# pitch and other values stay; the yaw rates give the F-35's turn radius at each speed (yaw x J-20 speed / F-35 speed), and MaxSpeedYaw 45.7 gives
# card 985 exactly (the speed-scaled 44.4 would show 1005). Calculated from data; flight not yet seen in a game.
import math
_FP=t['FlyPresetsJson'];_MB=t['MobilityJson'];_UP=t['UnitPropulsionsJson']
def _card(v,y):return math.floor(round(2*v*(1+1/math.tan(math.radians(y))))/5)*5
_jp=[r for r in _UP.values() if r['UnitId'] in (915,966)]
ok(U[915]['HUDName']=='J-20' and U[966]['HUDName']=='J-20S' and sorted(r['MobilityId'] for r in _jp)==[31,31] and _MB[31]['FlyPresetId']==2001429,'J-20 and J-20S on mobility 31, preset 2001429')
ok(not [o for o in t['OptionsJson'].values() if o.get('MobilityId') and M.get(o['ModificationId'],{}).get('UnitId') in (915,966)],'no J-20 option overrides mobility')
ok(_card(_FP[17]['MaxSpeed'],_FP[17]['MaxSpeedYaw'])==985 and _card(_FP[2001429]['MaxSpeed'],_FP[2001429]['MaxSpeedYaw'])==565,'card radius: F-35 985, J-20 565')
_f,_j=_FP[17],_FP[2001429]
_y={k:round(_f[k]*_j[v]/_f[v],2) for k,v in (('MinSpeedYaw','MinSpeed'),('CornerSpeedYaw','CornerSpeed'),('AfterburnYaw','AfterburnSpeed'),('CornerAfterburnSpeedYaw','AfterburnCornerSpeed'))}
_y['MaxSpeedYaw']=45.7
_np=g.add('FlyPresetsJson',_j,{'Name':'FA Fighter J-20 F-35 turn',**_y})
_nm=g.add('MobilityJson',_MB[31],{'Name':'Plane J-20 F-35 turn','FlyPresetId':_np})
for r in _jp:g.put('UnitPropulsionsJson',r['Id'],{'MobilityId':_nm})
ok(_card(_FP[_np]['MaxSpeed'],_FP[_np]['MaxSpeedYaw'])==985 and all(_UP[r['Id']]['MobilityId']==_nm for r in _jp),'J-20 and J-20S card radius 985')
ok(_MB[31]['FlyPresetId']==2001429 and _FP[2001429]['MaxSpeedYaw']==82.5,'Su-57D, F-22 and Su-35/47 rows unchanged')
rec['j20_turn']={'units':[915,966],'preset':_np,'mobility':_nm,'yaw':_y,'card_radius':[565,985]}
# ---------- YF-23 Black Widow II: 45% ECM, 295 base (Osama 16 Nov 2026 14:3x PST: "YF-23 should be 45% ecm and dropped to 295 base (so 365
# after 2 sets of 2x AMRAAMS) points"). Its default ECM 2001398 (0.5 = 50%) is shared with the J-50, so the YF-23 is relinked to a copy at 0.55,
# as the F-22 in dev.29. Base 315 -> 295; with 2x AIM-120 in both bays (+35 each) = 365.
_yf=[u_ for u_ in U.values() if u_.get('Name')=='YF-23 Black Widow II'];ok(len(_yf)==1 and _yf[0]['Cost']==315,'YF-23 unit, 315');_yf=_yf[0]['Id']
_ua=[r for r in UAB.values() if r['UnitId']==_yf];ok(len(_ua)==1 and _ua[0]['AbilityId']==2001398 and AB[2001398]['ECMAccuracyMultiplier']==0.5,'YF-23: one ability, shared ECM 2001398 at 50%')
g.put('Units',_yf,{'Cost':295})
_e=g.add('AbilitiesJson',AB[2001398],{'Name':'ECM Plane YF-23 Default FA 0.55','ECMAccuracyMultiplier':0.55})
g.put('UnitAbilitiesJson',_ua[0]['Id'],{'AbilityId':_e})
_bays=sorted(o['Cost'] for o in t['OptionsJson'].values() if 'AIM120' in str(o.get('Name','')).replace('-','').upper() and M.get(o.get('ModificationId'),{}).get('UnitId')==_yf)
ok(U[_yf]['Cost']==295 and AB[_e]['ECMAccuracyMultiplier']==0.55 and AB[2001398]['ECMAccuracyMultiplier']==0.5,'YF-23 295 points, ECM 45%; shared 2001398 unchanged')
rec['yf23']={'unit':_yf,'cost':295,'ecm_ability':_e,'ecm':0.55,'aim120_bay_costs':_bays}
# ---------- J-36: stealth 2.2, +50 points (Osama 16 Nov 2026 14:4x PST: "J-36 to 2.2 stealth and price increased by 50 points"). Card stealth
# 2.2 = raw 1/2.2 (J-36 raw 0.5 = 2.0); 305 -> 355. No J-36 option overrides stealth, and no option swaps to another J-36 unit.
_j=[u_ for u_ in U.values() if u_.get('Name')=='PLA J-36'];ok(len(_j)==1 and _j[0]['Cost']==305 and _j[0]['Stealth']==0.5,'J-36 unit, 305, raw stealth 0.5');_j=_j[0]['Id']
ok(not [o for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId')==_j and o.get('StealthOverride')],'no J-36 option overrides stealth')
g.put('Units',_j,{'Cost':355,'Stealth':round(1/2.2,4)})
ok(U[_j]['Cost']==355 and abs(U[_j]['Stealth']-0.4545)<1e-4,'J-36 355 points, stealth 2.2 (raw 0.4545)')
rec['j36_stealth']={'unit':_j,'cost':355,'stealth_raw':round(1/2.2,4)}
# Maps 0.2 (Lateralus 16 Nov 2026 14:4x PST): Highway of Death, Baltiisk, Dam, Chkalovsk Airbase, Dead Center 2v2 and 1v1 with his zone and spawn
# edits (scenarios/*/layout.bascr; merge script and report in work/maps-02-20261116); Baltiisk zones J and K worth 1; the 0.1 versions are
# retired by GUID in runtime-qa/Runtime.cs. Scenarios and runtime only, no table changes.
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

