"""Freedom Arrow 0.9.1-dev.2 data over exact 0.9.1-dev.1 (19 Nov 2026). Opened by BA Codex thread 1572962048705429598 (Lateralus, Infantry 步兵 price).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.1-dev.2';PREV='0.9.1-dev.1'
# 0.9.1-dev.1 was built in out/local-091dev1.
BASE=json.loads((REL/f'out/local-091dev1/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091dev1/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Infantry 步兵 50 -> 35 (Lateralus 19 Nov 2026 08:1x PST, thread 1572962048705429598: "lower Infantry 步兵 price from 50 -> 35").
# Unit 1175: 7 men, 4 QBZ-95, 2 QBB-95, 1 QBU-88, 6 single-shot PF-89 (its internal Name "PLA Designer 47 Missile-Site Security — HJ-73D" is a
# stale squad-designer label; it carries no HJ-73D). No loadout options and no swap rows (OptionsJson.ReplaceUnitId) point at it.
ok(U[1175]['HUDName']=='Infantry 步兵' and U[1175]['Cost']==50,'Infantry 步兵 1175 at 50')
_mods={i for i,m in t['ModificationsJson'].items() if m['UnitId']==1175}
ok(not [o for o in t['OptionsJson'].values() if o.get('ModificationId') in _mods or o.get('ReplaceUnitId')==1175],'no options or swap rows on 1175')
g.put('Units',1175,{'Cost':35});ok(U[1175]['Cost']==35,'Infantry 步兵 35')
rec['infantry_1175_price']={'unit':1175,'cost':[50,35],'verified':'data checks only'}
# ---------- China card cleanup: stale squad-designer Names and design-note Descriptions (Lateralus 19 Nov 2026 08:39 PST, thread 1572962048705429598:
# "yeah queue up that cleanup"). The internal Name of 63 China cards in the Arsenal is still the squad-designer label ("PLA Designer 47 Missile-Site
# Security — HJ-73D" on a squad with no HJ-73D). It becomes "PLA " + the card name (HUDName), with the unit id added where two cards share a card
# name. 230 China cards in the Arsenal carry design notes in Description ("Fixed PLA armament draft", "Named model-list stand-in. Donor ...",
# "Sheet row 47", ...). Vanilla has no unit Description (535 None, 10 empty), so these become None. Card names (HUDName), stats and hidden rows are
# unchanged. Nothing in the repo looks units up by these Names (git grep "PLA Designer": only the old pla_designer_infantry.py generator).
_cn=[i for i,u in U.items() if u.get('CountryId')==4 and u.get('DisplayInArmory')]
_ren=sorted(i for i in _cn if (U[i].get('Name') or '').startswith('PLA Designer '))
ok(len(_cn)==236 and len(_ren)==63,('China Arsenal cards / designer names',len(_cn),len(_ren)))
_hn={};[_hn.setdefault(U[i]['HUDName'].strip(),[]).append(i) for i in _ren]
_names={}
for i in _ren:
    _h=U[i]['HUDName'].strip();_names[i]=f'PLA {_h}'+(f' ({i})' if len(_hn[_h])>1 else '')
ok(len(set(_names.values()))==63 and not set(_names.values())&{u.get('Name') for j,u in U.items() if j not in _names},'new names unique')
_old={i:U[i]['Name'] for i in _ren}
for i,n in _names.items():g.put('Units',i,{'Name':n})
_desc=sorted(i for i in _cn if U[i].get('Description'))
ok(len(_desc)==230,('China Arsenal cards with a Description',len(_desc)))
for i in _desc:g.put('Units',i,{'Description':None})
ok(all(U[i]['Name']==_names[i] for i in _ren) and not any(U[i].get('Description') for i in _cn),'names and descriptions set')
ok(U[1175]['Name']=='PLA Infantry 步兵','1175 renamed')
rec['china_card_cleanup']={'renamed':{str(i):[_old[i],_names[i]] for i in _ren},'description_cleared':_desc,'verified':'data checks only'}
# ---------- Long-range SAMs: low-altitude optics = high-altitude optics (Lateralus 19 Nov 2026 10:5x PST, thread 1572724406642286692: "increase the
# low-altitude optics of all Long-range SAMs, to match their high altitdue optics. e.g. the PAC-2 has 4000 low and 5300 high, and it needs to go to 5300
# low and 5300 high"). Long-range SAM = a unit whose radar ability is static with RadarLowAltOpticsModifier 1.0 (radar on: low x1.0, high x2.0;
# FogOfWarUnit.CalculateVisionRangeForTarget): Patriot PAC-2/3/MSE, Buk M2/M3, IRIS-T SLM, S-300PM/V4, S-350, S-400, HQ-9/9A/9B, HQ-16, HQ-11,
# HQ-12, HQ-6A (17). Cards show raw x 2 m, so PAC-2 2000/2650 raw = 4000/5300. Every sensor these units use is raised to its own high value; each
# such sensor must be used only by long-range SAMs (sensor 8 "Optics SAM HA + Bad" is shared by 9 of them and nothing else). No loadout option on
# these units swaps a sensor. Units already equal (HQ-6A/11/12/16/9A/9B, 2000/2000) are unchanged.
_lr={r['UnitId'] for r in t['UnitAbilitiesJson'].values() if (_a:=t['AbilitiesJson'].get(r['AbilityId'])) and _a.get('IsRadar') and _a.get('IsRadarStatic')
     and _a.get('RadarLowAltOpticsModifier')==1.0 and r['UnitId'] in U}
ok(len(_lr)==17 and {163,251,448,192,231,545,227,156,466,225,911,1233,1234,1045,1046,1047,1048}==_lr,('long-range SAMs',sorted(_lr)))
_mods={i for i,m in t['ModificationsJson'].items() if m.get('UnitId') in _lr}
ok(not [o for o in t['OptionsJson'].values() if o.get('ModificationId') in _mods and (o.get('MainSensorId') or o.get('ExtraSensorId'))],'no sensor options on long-range SAMs')
_sens={r['SensorId'] for r in t['SensorUnitsJson'].values() if r.get('UnitId') in _lr}
_users={sid:{r['UnitId'] for r in t['SensorUnitsJson'].values() if r.get('SensorId')==sid} for sid in _sens}
ok(all(u<=_lr for u in _users.values()),('long-range SAM sensors shared with other units',{k:sorted(v-_lr) for k,v in _users.items() if v-_lr}))
_sold={sid:(t['SensorsJson'][sid]['OpticsLowAltitude'],t['SensorsJson'][sid]['OpticsHighAltitude']) for sid in _sens}
ok(_sold[8]==(2000.0,2650.0),('sensor 8 low/high',_sold[8]))
for sid,(lo,hi) in _sold.items():
    if lo<hi:g.put('SensorsJson',sid,{'OpticsLowAltitude':hi})
ok(all(t['SensorsJson'][sid]['OpticsLowAltitude']==t['SensorsJson'][sid]['OpticsHighAltitude'] for sid in _sens),'low = high on every long-range SAM sensor')
ok(t['SensorsJson'][8]['OpticsLowAltitude']==2650.0,'PAC-2 low 2650 raw (5300 m)')
rec['long_range_sam_low_optics']={'units':sorted(_lr),'sensors':{str(k):{'users':sorted(_users[k]),'low':[v[0],t['SensorsJson'][k]['OpticsLowAltitude']],'high':v[1]} for k,v in _sold.items()},'verified':'data checks only'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
