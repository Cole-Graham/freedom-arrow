"""Freedom Arrow 0.9.0-dev.13 data batch over exact 0.9.0-dev.12 (Osama/Lateralus, 15 Nov 2026).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.13';PREV='0.9.0-dev.12'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
UAB=t['UnitAbilitiesJson'];SAJ=t['SpecializationAvailabilitiesJson']
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
IW=SRC/'UserData/FAModels/infantry-weapons.json';iw=json.loads(IW.read_text())
_A=t['AmmunitionsJson']
# ---------- QTS-11 rifle damage 1.2 -> 1.5 (Lateralus 15 Nov 2026 06:53 PST: "Does the QTS-11 have 1.2 damage? If so, increase the damage from
# the QTS-11 from 1.2 to 1.5"). Its own round 2004005, used only by the QTS-11 rifle 2004004; every squad that carries it changes. The QTS-11
# grenade launcher (2019270 / 2019271) is a separate weapon and is not changed. 1.5 is the T2 rifle damage (M4A1 Mod. II, QMK).
ok(W[2004004]['HUDName']=='QTS-11' and _A[2004005]['Name']=='PLA Test Rifle QTS11 ammunition' and _A[2004005]['Damage']==1.2,'QTS-11 rifle round')
ok({r['WeaponId'] for r in WA.values() if r['AmmunitionId']==2004005}=={2004004},'QTS-11 round only on the QTS-11 rifle')
g.put('AmmunitionsJson',2004005,{'Damage':1.5});rec['qts11_rifle_damage']={'weapon':2004004,'ammunition':2004005,'damage':[1.2,1.5],'squads':len({r['UnitId'] for r in WA.values() if r['WeaponId']==2004004})}
# ---------- Godswords 100 -> 90 points (Lateralus 15 Nov 2026 06:59 PST: "Lower their price to 90", after the QTS-11 rifle went to 1.5).
# One card, no loadout that swaps to or from another squad row.
ok(U[1181]['HUDName'].startswith('Godswords') and U[1181]['Cost']==100,'Godswords 1181 at 100')
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==1181] and not [m for m in M.values() if m['UnitId']==1181],'Godswords: no swap rows or loadouts')
g.put('Units',1181,{'Cost':90});rec['godswords_cost']={'unit':1181,'cost':[100,90]}
# ---------- Conscripts carry the QBZ-03 at 30% damage (first asked as 30% of the rate of fire) (Osama 15 Nov 2026 12:04 PST: "give Conscropts QBZ-03, the ak
# copy, and make it only 30% of basic rifle rof"). New rifle QBZ-03 = the vanilla AK-74 (T0) rifle 156 and its round 364 (5.45x39, damage 1.2),
# renamed; vanilla AK-74 model and icon until a QBZ-03 model/icon exists. Osama 12:1x: "it's an AK-74 clone", "30% of the QBZ-95 speed, not 30%
# slower"; 12:2x: "instead of changing rof, we change damage so it's 30% damage". So the QBZ-03 keeps the AK-74's 4.0 s between shots (the
# QBZ-95's rate) and its own round does 30% of the AK-74's 1.2: 0.36. Same damage per minute as the 30%-rate version (about 5.4 per man). Conscripts 1166 only: its 9 QBZ-95 riflemen move to the QBZ-03, 120 rounds as before. The QBZ-95 stays on the
# other 9 squads; QBB-95 and QBU-88 unchanged.
_SM=t['SquadMembersJson'];_SW=t['SquadWeaponsJson']
ok(W[2012205]['TimeBetweenBurstsMax']==4.0 and U[1166]['HUDName'].startswith('Conscripts') and W[156]['HUDName']=='AK-74' and W[156]['TimeBetweenBurstsMax']==4.0 and _A[364]['Damage']==1.2,'Conscripts, vanilla AK-74 T0')
ok(not [w for w in W.values() if 'QBZ-03' in str(w.get('HUDName'))],'no QBZ-03 yet')
_cm=[m for m in _SM.values() if m['UnitId']==1166 and m['PrimaryWeaponId']==2012205];_cw=[r for r in WA.values() if r['UnitId']==1166 and r['WeaponId']==2012205];_cs=[r for r in _SW.values() if r['UnitId']==1166 and r['WeaponId']==2012205]
ok(len(_cm)==9 and len(_cw)==1 and _cw[0]['Quantity']==120 and len(_cs)==1,'Conscripts: 9 QBZ-95 riflemen, 120 rounds')
_q3=g.add('WeaponsJson',W[156],{'Name':'PLA infantry QBZ-03','HUDName':'QBZ-03'})
_q3a=g.add('AmmunitionsJson',_A[364],{'Name':'PLA infantry QBZ-03 ammunition','Damage':round(_A[364]['Damage']*0.3,2)})
for m in _cm:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':_q3})
g.put('SquadWeaponsJson',_cs[0]['Id'],{'WeaponId':_q3});g.put('WeaponAmmunitionsJson',_cw[0]['Id'],{'WeaponId':_q3,'AmmunitionId':_q3a})
ok(not [m for m in _SM.values() if m['UnitId']==1166 and 2012205 in (m['PrimaryWeaponId'],m['SpecialWeaponId'])] and len({r['UnitId'] for r in WA.values() if r['WeaponId']==2012205})==9,'QBZ-95 off Conscripts, still on 9 squads')
rec['conscripts_qbz03']={'unit':1166,'weapon':_q3,'ammunition':_q3a,'clone_of':[156,364],'time_between_shots':4.0,'damage':[1.2,0.36],'men':9,'rounds':120,'dpm_per_man':[13.5,round(0.36*60/4.0,1)]}
# ---------- ZTZ-59 40 -> 55 points (Osama 15 Nov 2026 12:2x PST: "ZTZ-59 to 55 points"). Unit 1060 only (ZTZ-59D 60 and ZTZ-59D1 65 unchanged);
# no loadouts, no swap rows.
ok(U[1060]['HUDName']=='ZTZ-59' and U[1060]['Cost']==40 and not [o for o in O.values() if o.get('ReplaceUnitId')==1060] and not [m for m in M.values() if m.get('UnitId')==1060],'ZTZ-59 1060 at 40')
g.put('Units',1060,{'Cost':55});rec['ztz59_cost']={'unit':1060,'cost':[40,55]}
# ---------- Howitzer and gun-mortar shell effects by calibre (Osama 15 Nov 2026 12:3x PST: "did we fix the plz-07 splash effect being really
# ugly?", "some of the howitzers had wrong effects"). Vanilla gives each calibre one impact effect and its smoke and guided rounds the same one:
# 120 mm mortar/gun-mortar MORTAR_OBUS_120mm (HE, smoke); 122 mm howitzer SHELL_120mm_HE (2S1); 152/155 mm SHELL_152-155mm_HE (HE, smoke,
# Krasnopol). Five China rounds had another calibre's effect: the PLL-09 120 mm gun-mortar HE showed the 122 mm howitzer blast and its smoke the
# 152 mm one; the PLZ-70 and PLZ-07B 122 mm smoke and the PLZ-07B GP6 122 mm guided round showed the 152/155 mm blast. Effect only: damage,
# radius, smoke and flight unchanged. The PLZ-07/07B 122 mm HE already uses the vanilla 2S1 effect and is not changed.
_FX={2010465:'AMMUNITION_VFX_PRESET_MORTAR_OBUS_120mm',2018959:'AMMUNITION_VFX_PRESET_MORTAR_OBUS_120mm',
     2018961:'AMMUNITION_VFX_PRESET_SHELL_120mm_HE',2018963:'AMMUNITION_VFX_PRESET_SHELL_120mm_HE',2018965:'AMMUNITION_VFX_PRESET_SHELL_120mm_HE'}
ok(_A[2010465]['HUDName']=='120 mm gun-mortar ammunition' and _A[2010465]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_120mm_HE','PLL-09 120 mm HE effect')
ok(_A[2018959]['HUDName']=='120 mm smoke' and _A[2018959]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_152-155mm_HE','PLL-09 120 mm smoke effect')
ok(all(_A[i]['HUDName']=='122 mm smoke' and _A[i]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_152-155mm_HE' for i in (2018961,2018963)),'122 mm smoke effects')
ok(_A[2018965]['HUDName']=='GP6 122 mm laser-guided' and _A[2018965]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_152-155mm_HE','GP6 effect')
ok(_A[6]['FXPreset']==_A[87]['FXPreset']=='AMMUNITION_VFX_PRESET_MORTAR_OBUS_120mm' and _A[174]['FXPreset']=='AMMUNITION_VFX_PRESET_SHELL_120mm_HE','vanilla 120 mm mortar and 122 mm 2S1 effects')
_fxu={i:sorted(U[r['UnitId']]['HUDName'] for r in WA.values() if r['AmmunitionId']==i and r['UnitId'] in U) for i in _FX}
ok(_fxu=={2010465:['PLL-09'],2018959:['PLL-09'],2018961:['PLZ-70'],2018963:['PLZ-07B'],2018965:['PLZ-07B']},f'effect rounds used only by their own gun {_fxu}')
for i,fx in _FX.items():g.put('AmmunitionsJson',i,{'FXPreset':fx})
rec['artillery_effects']={str(i):{'round':_A[i]['HUDName'],'units':_fxu[i],'effect':fx} for i,fx in _FX.items()}
# ---------- SPAAG guns and SAMs against SEAD missiles (Lateralus 15 Nov 2026, thread 1571554273639006392; tested in the 0.9.0-dev.12-hp5 test
# builds on codex/batch/lateralus/missile-hp, final 0.9.0-dev.12-hp5-burst-tier3-sam-claim6-gunsam, 13:58 PST "Ok its working well now ... make
# sure everything is queued for the next build"). Values = that test build's tables against dev.12 (58 weapons, 12 rounds):
# - 12 SPAAG gun rounds: damage between 2.5 and 4.9, a 2-hit kill on a 5 HP missile, dev.12 DPS kept (heavy -27%).
# - Bursts: light guns 3 rounds (2-3 s pause), middle 7 (2-3 s), heavy 11 (1.5-2 s), to set how many missiles each tier stops.
# - 46 SEAD-capable multi-target SAMs launch faster: short range 0.8-1.2 s, medium 1.5-2.0 s, long 2.5-3.0 s between missiles; Pantsir 57E6E,
#   FK-2000 SAM and PGL-625 FB-10 (units that also have an intercepting gun) 2.0-2.5 s so SAM, gun and SAM take turns.
# Runtime parts (projectile-health.json 5 HP, spaag-weapons.json, ProjectileHealth/SpaagWeapons/SameUnitClaim.cs, CramPrediction fixes) ship with it.
_SPW={"2010639":{"ShotsPerBurstMin":[7,3],"ShotsPerBurstMax":[10,3]},"628":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"261":{"ShotsPerBurstMin":[7,3],"ShotsPerBurstMax":[10,3]},"2010625":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"320":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"784":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"347":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"323":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"315":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"327":{"TimeBetweenBurstsMin":[1.5,2.0],"TimeBetweenBurstsMax":[2.0,3.0],"ShotsPerBurstMax":[10,7]},"2014549":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"620":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"324":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"238":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"2009181":{"TimeBetweenBurstsMin":[1.5,2.0],"TimeBetweenBurstsMax":[2.0,3.0],"ShotsPerBurstMax":[10,7]},"236":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"650":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"651":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"691":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"2014555":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"599":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"2010569":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"705":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"366":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"2009371":{"TimeBetweenBurstsMax":[3.0,2.5]},"704":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"2010597":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"732":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"772":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"2009599":{"ShotsPerBurstMin":[7,11],"ShotsPerBurstMax":[10,11]},"307":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"619":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"2010583":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"2014534":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"2010673":{"ShotsPerBurstMax":[10,7]},"2009555":{"ShotsPerBurstMin":[7,3],"ShotsPerBurstMax":[10,3]},"625":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"329":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"685":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"773":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"28":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"690":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"220":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"319":{"TimeBetweenBurstsMin":[4.0,2.5],"TimeBetweenBurstsMax":[5.0,3.0]},"2009605":{"TimeBetweenBurstsMax":[3.0,2.5]},"774":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"2010659":{"ShotsPerBurstMin":[7,3],"ShotsPerBurstMax":[10,3]},"20":{"TimeBetweenBurstsMax":[3.0,2.5]},"2009195":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"345":{"TimeBetweenBurstsMin":[1.5,2.0],"TimeBetweenBurstsMax":[2.0,3.0],"ShotsPerBurstMax":[10,7]},"99":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"346":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"2009365":{"ShotsPerBurstMin":[7,11],"ShotsPerBurstMax":[10,11]},"309":{"ShotsPerBurstMin":[7,3],"ShotsPerBurstMax":[10,3]},"783":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]},"19":{"TimeBetweenBurstsMin":[1.5,2.0],"TimeBetweenBurstsMax":[2.0,3.0],"ShotsPerBurstMax":[10,7]},"605":{"TimeBetweenBurstsMin":[2.0,0.8],"TimeBetweenBurstsMax":[3.0,1.2]},"2010611":{"TimeBetweenBurstsMin":[3.0,1.5],"TimeBetweenBurstsMax":[4.0,2.0]}}
_SPA={"62":{"Damage":[2.0,4.0]},"2009185":{"Damage":[3.0,4.0]},"213":{"Damage":[2.3,4.6]},"2009603":{"Damage":[7.8,4.9]},"2010677":{"Damage":[2.3,2.6]},"231":{"Damage":[3.0,4.0]},"2009369":{"Damage":[7.8,4.9]},"60":{"Damage":[3.0,4.0]},"262":{"Damage":[2.0,2.7]},"2010643":{"Damage":[2.3,4.6]},"2010663":{"Damage":[2.3,4.6]},"2009559":{"Damage":[2.3,4.6]}}
for _tab,_d in (('WeaponsJson',_SPW),('AmmunitionsJson',_SPA)):
    for _k,_f in _d.items():
        ok(all(t[_tab][int(_k)].get(f)==ov[0] for f,ov in _f.items()),f'{_tab} {_k} has the dev.12 values {_f}')
        g.put(_tab,int(_k),{f:ov[1] for f,ov in _f.items()})
rec['spaag_sead']={'source':'0.9.0-dev.12-hp5-burst-tier3-sam-claim6-gunsam','weapons':_SPW,'ammunition':_SPA}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);IW.write_text(json.dumps(iw,indent=2,ensure_ascii=False)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
