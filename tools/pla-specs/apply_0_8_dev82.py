"""Freedom Arrow 0.8.0-dev.82 over exact 0.8.0-dev.81 (Osama 13 Nov 20:4x PST, thread 1567745029781454889):
- PGL-625 (920): Stryker armour profile (vanilla Stryker ICV row 2000016: HEAT and KE 60 front / 40 sides / 30 rear / 20 top,
  12 HP). Was the ZBL-191 profile from dev.71 (HEAT 700/700/130/20, KE 80/60/30/20), which is the Stryker's add-on armour row.
- FAModels 0.3.22 (complete package and assets): a cockpit-glass donor that is not loaded (US_F16_Glass in the editor and in
  matches without an F-16) now gives clear glass instead of refusing the whole model. FK-2000, DF-15/17/21/31A, HQ-12, J-5..J-16
  showed their stand-ins in those scenes (dev.73 log: "Cockpit donor unavailable: US_F16_Glass").
- ZSL-92 (Osama 20:5x "Make ZSL-92 autocannon the main ZSL-92 and remove the non autocannon version"): the autocannon card
  (1079, 'ZSL-92 Autocannon') is now named 'ZSL-92'; the 12.7 mm MG card (1232) is removed (hidden, card and its 10 transport links
  deleted). Both carried the same 10 squads, so no squad loses its transport.
- CSK-181 windows: vanilla glass (cockpitDonor US_F16_Glass), as the other Chinese models (Osama: "make sure glass is transplanted").
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.82'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.81.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
g=Graph(t,patches,native);U,AR,UA,SA,TA=(t[k] for k in ('Units','ArmorsJson','UnitArmorsJson','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson'))
PGL,PARM,STRY=920,2009357,2000016
assert U[PGL]['HUDName']=='PGL-625' and U[22]['HUDName']=='Stryker ICV' and [r['ArmorId'] for r in UA.values() if r['UnitId']==PGL]==[PARM] and sorted({r['UnitId'] for r in UA.values() if r['ArmorId']==PARM})==[PGL]
F=[k for k in AR[STRY] if k not in ('Id','Name','ModelFileName','IsDefault')]
before={k:AR[PARM][k] for k in F};g.put('ArmorsJson',PARM,{k:AR[STRY][k] for k in F})
ZAC,ZMG=1079,1232;assert U[ZAC]['HUDName']=='ZSL-92 Autocannon' and U[ZMG]['HUDName']=='ZSL-92'
carried_ac={r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==ZAC};carried_mg={r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==ZMG}
assert carried_mg<=carried_ac
g.put('Units',ZAC,{'HUDName':'ZSL-92'})
g.put('Units',ZMG,{'DisplayInArmory':False});assign['assignments'].pop(str(ZMG),None)
ids={r['Id'] for r in SA.values() if r['UnitId']==ZMG};nta=0
for r in list(TA.values()):
    if r['SpecializationAvailabilityId'] in ids or r['UnitId']==ZMG:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=ZMG]
zsl={'renamed':ZAC,'removed':ZMG,'cards':len(ids),'transport_links':nta}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(all(AR[PARM][k]==AR[STRY][k] for k in F),'PGL-625 = Stryker ICV armour')
ok(U[ZAC]['HUDName']=='ZSL-92' and not U[ZMG]['DisplayInArmory'] and not [r for r in SA.values() if r['UnitId']==ZMG] and not [r for r in TA.values() if r['UnitId']==ZMG] and carried_mg<={r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==ZAC},'ZSL-92 autocannon is the only ZSL-92')
ok('2000016' not in patches['ArmorsJson'] or patches['ArmorsJson']['2000016'] is not None,'Stryker row not removed')
receipt={'version':V,'base':'0.8.0-dev.81','base_sha256':BASE,'request':'Osama 13 Nov 20:4x PST: PGL-625 armor profile should be like Stryker armor profile; make sure glass is transplanted; Make ZSL-92 autocannon the main ZSL-92 and remove the non autocannon version',
 'pgl625_armour':{'from':before,'to':{k:AR[PARM][k] for k in F},'donor':STRY},'famodels':'0.3.22 donor fallback','csk181_glass':'cockpitDonor US_F16_Glass','zsl92':zsl,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(receipt['pgl625_armour']))
