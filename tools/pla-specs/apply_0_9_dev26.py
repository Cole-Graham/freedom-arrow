"""Freedom Arrow 0.9.0-dev.26 data over exact 0.9.0-dev.25 (16 Nov 2026). Opened by BA Codex thread 1571554273639006392 (Lateralus).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.26';PREV='0.9.0-dev.25'
# dev.25 was built in out/local-dev25.
BASE=json.loads((REL/f'out/local-dev25/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev25/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Stryker M-SHORAD laser on the unit card (Lateralus 16 Nov 2026, "queue up a fix to add the laser icon to unit card when the APKSW
# loadout is selected on the stryker shorad"): the game merges only the first chosen option's Ability1, and every armour option also fills
# Ability1, so the dev.25 laser was dropped. The laser moves to Ability2 of option 1937. See lateralus/mshorad_laser_slot.py.
import mshorad_laser_slot as MLS
rec['mshorad_laser_slot']=MLS.apply(t,g,ok)
avail={r.get('UnitId') for r in t['SpecializationAvailabilitiesJson'].values()}
coll=MLS.slot_collisions(U,M,O,AB,avail);ok(not coll,f'no unit has two modifications filling one ability slot with a real ability: {coll}')
# Maps (Lateralus 16 Nov 2026): Klaipeda, Kadaga and Jelgava 1v1 zones A B C 2, D E 4 (scenarios/common.py END_VALUES and
# FAConquestPrototype/settings.json); Central Village 1v1 removed from make_scenario.py and settings, and the installed copies retired
# by GUID in runtime-qa/Runtime.cs. [1v1] Chernyakhovsky 0.1 is replaced by Lateralus's new design (same name and GUID; A B 2, D E 3, C F 4). No table changes; the packager rebuilds the scenarios and drops the removed ones.
# Create a lobby tabs 1v1 / 2v2 / 3v3 / 5v5 (Lateralus 16 Nov 2026): runtime only, runtime-qa/LobbyMapTabs.cs (patches ArrowQueue's map window).
# Deployment (Lateralus 16 Nov 2026): the online conquest mode starts with the deployment pause, so the top bar and zone values show during
# deployment (scenarios/common.py conquest_during_deployment); the DEPLOYMENT banner waits for RoomStatus.InProcess, not the map preview
# screen; zone values and banners hide while the Escape menu or settings are open (conquest/NativeUi.cs). Runtime and scenarios only.
# Lateralus 16 Nov 2026 (11:4x): altitude intent, SEAD overkill 0.33 and SEAD re-target ported from codex/batch/lateralus/intercept-sead
# (test builds sead3-sead5 only until now); overlay hidden once a leave is confirmed; lobby map list prefers the Mods/Scenarios copy on a
# name clash; End's 1v1 maps no longer lock slots 2-5 (build check: no locked slots); new [FA] [NvN] lobbies open N slots per team.
# ---------- LSDW laser: one pulse a second (Osama 16 Nov 2026 12:1x PST, thread 1571014792016171120: "the effect is perfect, but I just want it
# to have a rof of 1 second and increase the salvo size. But halve or third the effect since we shoot twice/thrice as fast"). dev.21-25: one
# pulse every 2-3 s (2.5 s mean), 100-pulse magazine, 400 pulses, 0.2 damage and 200 stress a pulse. Now one pulse every 1.0 s (2.5x as often);
# per-pulse damage, stress and supply cost divided by 2.5 and magazine and pulses carried multiplied by 2.5, so stress per second, time between
# reloads, firing time per load and resupply cost stay as before.
W=t['WeaponsJson'];AM=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName')=='LSDW'];ok(len(_lw)==1,'one LSDW weapon');_lw=_lw[0]
_was=[r for r in WA.values() if r['WeaponId']==_lw];_la={r['AmmunitionId'] for r in _was};ok(len(_la)==1 and len(_was)==2,'LSDW: one ammo, rows for ZTZ-99A and ZTZ-99');_la=_la.pop()
ok((W[_lw]['TimeBetweenBurstsMin'],W[_lw]['TimeBetweenBurstsMax'],W[_lw]['ShotsPerBurstMax'],W[_lw]['MagazineSize'])==(2.0,3.0,1,100),'LSDW dev.25 rate: 1 pulse / 2-3 s, magazine 100')
ok((AM[_la]['Damage'],AM[_la]['StressDamage'],AM[_la]['SupplyCost'])==(0.2,200.0,0.1) and all(r['Quantity']==400 for r in _was),'LSDW dev.25 pulse: 0.2 damage, 200 stress, 0.1 supply, 400 pulses')
g.put('WeaponsJson',_lw,{'TimeBetweenBurstsMin':1.0,'TimeBetweenBurstsMax':1.0,'MagazineSize':250})
g.put('AmmunitionsJson',_la,{'Damage':0.08,'StressDamage':80.0,'SupplyCost':0.04})
for r in _was:g.put('WeaponAmmunitionsJson',r['Id'],{'Quantity':1000})
ok(W[_lw]['TimeBetweenBurstsMax']==1.0 and AM[_la]['StressDamage']==80.0 and all(WA[r['Id']]['Quantity']==1000 for r in _was),'LSDW: 1 pulse / s, 80 stress, 1000 pulses')
rec['lsdw_rof']={'weapon':_lw,'ammo':_la,'pulse_s':1.0,'magazine':250,'pulses':1000,'damage':0.08,'stress':80.0,'supply':0.04}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
