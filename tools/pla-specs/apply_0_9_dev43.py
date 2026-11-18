"""Freedom Arrow 0.9.0-dev.43 data over exact 0.9.0-dev.42 (18 Nov 2026). Opened by BA Codex thread 1567745029781454889 (Osama, J-36 price).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.43';PREV='0.9.0-dev.42'
# dev.42 was built in out/local-dev42.
BASE=json.loads((REL/f'out/local-dev42/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev42/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- J-36 +60 points (Osama 18 Nov 2026 11:5x PST, thread 1567745029781454889: "J-36 increase price by 60"). Card price only.
ok(U[929]['Name']=='PLA J-36' and U[929]['Cost']==355,('J-36 base price',U[929].get('Cost')))
ok(not [k for k,o in O.items() if o and o.get('ReplaceUnitId')==929],'J-36 has no swap rows to keep in step')
g.put('Units',929,{'Cost':415});ok(U[929]['Cost']==415,'J-36 now 415')
rec['j36_price']={'unit':929,'from':355,'to':415}
# ---------- CTL-181 NLOS and Blood Wolves CH-901 cannot be shot down (Osama 18 Nov 2026 12:1x PST, thread 1567745029781454889: "The Blood Wolves
# missile and the CTL-181 NLOS shouldn't be interceptable but it looks like its happening in game"). dev.42 data: both CanBeTargeted True (air
# defence guns/SAMs may engage them as projectiles); CH-901 also CanBeIntercepted True (APS). Osama 12 Nov (0.8.0-dev.13) had set CH-901 APS off;
# it was True again by 0.8.0-dev.105. Both flags off on both rounds; each round is used by one unit only.
_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
_nl={2018321:(1054,'NLOS missile'),2018448:(1183,'CH-901')}
for _i,(_u,_n) in _nl.items():
    ok(_A[_i]['HUDName']==_n and sorted({r['UnitId'] for r in _WA.values() if r['AmmunitionId']==_i})==[_u],(_n,'own round on one unit'))
    ok(_A[_i]['CanBeTargeted'] is True,(_n,'was targetable'))
    g.put('AmmunitionsJson',_i,{'CanBeTargeted':False,'CanBeIntercepted':False})
    ok(_A[_i]['CanBeTargeted'] is False and _A[_i]['CanBeIntercepted'] is False,(_n,'not interceptable'))
rec['nlos_not_interceptable']={str(i):{'unit':u,'name':n,'CanBeTargeted':[True,False],'CanBeIntercepted':['CH-901 True' if i==2018448 else False,False]} for i,(u,n) in _nl.items()}
# ---------- Recon CSK-131 back in PLAGF Motorized (Osama 18 Nov 2026 12:3x PST, thread 1567745029781454889: "add a recon CSK-131 to moto").
# The recon CSK-131 already exists: unit 1265 'PLA Mengshi Recon' (CSK-131 recon model m_csk4r, QJZ-89 12.7 mm RWS, Very Good optics sensor 3,
# Recon tab, 30 pts). Osama removed all three of its cards (PLAAF, PLAN SF, Motorized) on 15 Nov (0.9.0-dev.4). It comes back in Motorized (21)
# only, with the 4 cards it had there, and its card name follows his wording: Mengshi Recon -> CSK-131 Recon (internal Name kept: models/voices).
_SAJ=t['SpecializationAvailabilitiesJson'];_TAJ=t['TransportAvailabilitiesJson']
_u=U[1265];ok(_u['Name']=='PLA Mengshi Recon' and _u['HUDName']=='Mengshi Recon' and _u['CategoryType']==0 and _u['Cost']==30,'Mengshi Recon unit row')
ok(not [r for r in _SAJ.values() if r['UnitId']==1265] and '1265' not in assign['assignments'],'no cards now')
ok(not [r for r in _TAJ.values() if r.get('UnitId')==1265],'carries nobody')
_tpl=_SAJ[2018744];ok(_tpl['UnitId']==1263 and _tpl['SpecializationId']==21,'template: ZTL-191 Recon Motorized card row')
_new=g.add('SpecializationAvailabilitiesJson',_tpl,{'UnitId':1265,'SpecializationId':21,'MaxAvailabilityXp0':4,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0})
g.put('Units',1265,{'HUDName':'CSK-131 Recon'})
assign['assignments']['1265']=[21]
ok([(r['SpecializationId'],r['MaxAvailabilityXp0']) for r in _SAJ.values() if r['UnitId']==1265]==[(21,4)] and U[1265]['HUDName']=='CSK-131 Recon','CSK-131 Recon: Motorized, 4 cards')
rec['csk131_recon']={'unit':1265,'card_row':_new,'spec':21,'cards':4,'cost':30,'name':['Mengshi Recon','CSK-131 Recon']}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
