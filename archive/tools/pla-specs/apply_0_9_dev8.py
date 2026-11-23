"""Freedom Arrow 0.9.0-dev.8 batch over exact 0.9.0-dev.7 (Osama, 14-15 Nov 2026, thread 1567745029781454889).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.8';PREV='0.9.0-dev.7'
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
# ---------- YJ-18 ship launcher moves from PLAN SF to PLAAF (Osama 22:15 PST: "YJ-18 moved to PLAAF"). Same card (2 availability, 225).
ok(U[1129]['HUDName']=='YJ-18' and SAJ[2008984]['UnitId']==1129 and SAJ[2008984]['SpecializationId']==20,'YJ-18 PLAN card')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==2008984],'no transports on it')
g.put('SpecializationAvailabilitiesJson',2008984,{'SpecializationId':17});assign['assignments']['1129']=[17]
rec['yj18_to_plaaf']={'card':2008984,'spec':[20,17]}
# ---------- VT-5 front KE 350, all variants (Osama 22:23 PST). Each has its own armour row.
AR=t['ArmorsJson'];UA=t['UnitArmorsJson']
for _u,_a,_ke in ((1261,2018635,500),(1262,2018651,500),(953,2009955,300)):
    ok(str(U[_u]['HUDName']).startswith('VT-5') and [r['ArmorId'] for r in UA.values() if r['UnitId']==_u]==[_a] and AR[_a]['KinArmorFront']==_ke,('VT-5 armour',_u))
    ok(sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==_a})==[_u],('armour row not shared',_a))
    g.put('ArmorsJson',_a,{'KinArmorFront':350})
rec['vt5_front_ke']={'1261 VT-5':[500,350],'1262 VT-5 Recon':[500,350],'953 VT-5 draft (no card)':[300,350]}
# ---------- Z-11WB moves to PLAGF Motorized (Osama 22:19 PST). Its PLAAF card becomes the Motorized card; the PLAN card goes.
TAJ=t['TransportAvailabilitiesJson']
ok(U[942]['HUDName']=='Z-11WB' and SAJ[2008231]['SpecializationId']==17 and SAJ[2018726]['SpecializationId']==20 and SAJ[2008231]['UnitId']==942==SAJ[2018726]['UnitId'],'Z-11WB cards')
ok(not [r for r in TAJ.values() if r['SpecializationAvailabilityId'] in (2008231,2018726)] and not [r for r in TAJ.values() if r['UnitId']==942],'Z-11WB no transport links')
g.put('SpecializationAvailabilitiesJson',2008231,{'SpecializationId':21});g.remove('SpecializationAvailabilitiesJson',2018726)
assign['assignments']['942']=[21];assign.get('shared_transports',{}).pop('942',None)
rec['z11wb_to_motorized']={'moved':2008231,'removed':2018726}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
