"""Freedom Arrow 0.9.0-dev.5 over exact 0.9.0-dev.4. dev.4 loaded but its constants were refused at start (Osama's PC, 18:56 PST
14 Nov 2026): "Field type mismatch OriginalName". The new SX2190 row (1269) had OriginalName 'PLA SX2190'; vanilla has null in every
Units row. check_field_types.py now gates every package, so this can't ship again. Also the ZBL-191 jammer (+20), which landed after dev.4 was built.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.5';PREV='0.9.0-dev.4'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
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
# ---------- ZBL-191 ECM option +20 (Osama 14 Nov 18:33 PST, thread 1571338089186599002: "ZBL-191 also ecm upgrade for +20"), the same
# Hardhat jammer slot as the ZTL-191 (vanilla M1A1 FEP mod 397, ability 80, ECM 0.7). The ZBL-191 keeps its smoke/supply and
# Iron Fist APS abilities in both options; the jammer is the third. (Moved here from the dev.4 batch by that thread: dev.4 was built
# before it landed.)
ok(U[979]['HUDName']=='ZBL-191' and sorted(x['AbilityId'] for x in UAB.values() if x['UnitId']==979)==[82,2010319],'ZBL-191 abilities smoke + APS')
ok(not [x for x in M.values() if x['UnitId']==979 and x.get('Type')==6],'no ZBL-191 protection slot yet')
_ba=next(x for x in UAB.values() if x['UnitId']==979)
for _ab in (4,80):g.add('UnitAbilitiesJson',_ba,{'AbilityId':_ab})
_bm=g.add('ModificationsJson',M[397],{'UnitId':979,'Name':'PLA ZBL-191 Jammer'})
_b1=g.add('OptionsJson',O[1468],{'ModificationId':_bm,'Name':'ECM ZBL191 Base','Ability1Id':2010319,'Ability2Id':82,'Ability3Id':4,'Cost':0,'IsDefault':True})
_b2=g.add('OptionsJson',O[1469],{'ModificationId':_bm,'Name':'ECM ZBL191 Jammer','Ability1Id':2010319,'Ability2Id':82,'Ability3Id':80,'Cost':20,'IsDefault':False})
ok(_b1<=32767 and _b2<=32767,'short option ids')
rec['zbl191_jammer']={'option':_b2,'cost':20,'ability':'ECM Hardhat (0.7 accuracy, the M1A1 FEP jammer)','in_a_deck':bool([x for x in SAJ.values() if x['UnitId']==979])}
# ---------- SX2190 OriginalName back to null, as in every vanilla Units row ----------
ok(U[1269]['HUDName']=='SX2190' and U[1269].get('OriginalName')=='PLA SX2190','SX2190 row as in dev.4')
g.put('Units',1269,{'OriginalName':None});ok(U[1269]['OriginalName'] is None,'OriginalName null')
rec['sx2190_original_name']=['PLA SX2190',None]
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
