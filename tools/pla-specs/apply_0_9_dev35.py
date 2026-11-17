"""Freedom Arrow 0.9.0-dev.35 data over exact 0.9.0-dev.34 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.35';PREV='0.9.0-dev.34'
# dev.34 was built in out/local-dev34.
BASE=json.loads((REL/f'out/local-dev34/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev34/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- Conscript Recon (unit 1213) to 4 men, 25 points (Osama 16 Nov 2026 20:39 PST, thread 1571014792016171120: "conscript recon to 4 man (lose
# the qcw and QBZ-191 and add 3 QBZ-95)", "and 20 points"; 20:4x: "conscript recon are 25 pts"). Was 6 men: 4 x QCW-05, 1 x QBU-88, 1 x QBZ-191, 40 points. Now 3 x QBZ-95 (weapon 2012205,
# ammo 2012206, 120 rounds per row as in the other China squads that carry it) and the QBU-88. Squad weapon orders stay 0, 1 (no gap).
SM,SW,WA=t['SquadMembersJson'],t['SquadWeaponsJson'],t['WeaponAmmunitionsJson']
_m=sorted((r['Id'],r['PrimaryWeaponId']) for r in SM.values() if r['UnitId']==1213)
ok(_m==[(2015657,2013349),(2015658,2013349),(2015659,2013349),(2015660,2013349),(2015661,2012821),(2015662,2003998)] and U[1213]['Cost']==40 and U[1213]['HUDName']=='Conscript Recon','Conscript Recon: 4 QCW-05, QBU-88, QBZ-191, 40 points')
ok(sorted((r['Id'],r['WeaponId'],r['Order']) for r in SW.values() if r.get('UnitId')==1213)==[(2015663,2003998,1),(2015665,2012821,2),(2015667,2013349,0)],'Conscript Recon squad weapons')
ok(sorted((r['Id'],r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('UnitId')==1213)==[(2015664,2003998,2003999,160),(2015666,2012821,2012822,60),(2015668,2013349,2013350,20)],'Conscript Recon ammo rows')
ok(t['WeaponsJson'][2012205].get('HUDName')=='QBZ-95' and sorted({(r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('WeaponId')==2012205})==[(2012206,120)],'QBZ-95 2012205 with ammo 2012206 x 120')
for _id in (2015657,2015658,2015659):g.put('SquadMembersJson',_id,{'PrimaryWeaponId':2012205})
for _id in (2015660,2015662):g.remove('SquadMembersJson',_id)
g.put('SquadWeaponsJson',2015667,{'WeaponId':2012205,'Order':0});g.put('SquadWeaponsJson',2015665,{'Order':1});g.remove('SquadWeaponsJson',2015663)
g.put('WeaponAmmunitionsJson',2015668,{'WeaponId':2012205,'AmmunitionId':2012206,'Quantity':120});g.remove('WeaponAmmunitionsJson',2015664)
g.put('Units',1213,{'Cost':25})
ok(sorted(r['PrimaryWeaponId'] for r in SM.values() if r['UnitId']==1213)==[2012205,2012205,2012205,2012821] and U[1213]['Cost']==25
   and sorted((r['WeaponId'],r['Order']) for r in SW.values() if r.get('UnitId')==1213)==[(2012205,0),(2012821,1)]
   and sorted((r['WeaponId'],r['Quantity']) for r in WA.values() if r.get('UnitId')==1213)==[(2012205,120),(2012821,60)],'Conscript Recon: 3 QBZ-95 + QBU-88, 25 points')
rec['conscript_recon']={'unit':1213,'men':[6,4],'cost':[40,25],'weapons':'3 x QBZ-95 2012205 + QBU-88 2012821','removed_members':[2015660,2015662]}
# ---------- Falcons (unit 1185): QLB-06 -> QLU-11, 75 points (Osama 16 Nov 2026 20:4x PST, thread 1571014792016171120: "falcons replace 2x ALB-06 with
# QLU-11 and 75 points"; "ALB-06" = the squad's two QLB-06 grenade launchers). QLU-11 2004002 with ammo 2004003 x 120, as the 33 other squads that carry it.
_f=sorted((r['Id'],r['PrimaryWeaponId']) for r in SM.values() if r['UnitId']==1185 and r['PrimaryWeaponId'] in (2016050,2004002))
ok(_f==[(2015349,2016050),(2015350,2016050)] and U[1185]['Cost']==65 and U[1185]['HUDName']=='Falcons 猎鹰','Falcons: 2 QLB-06, 65 points')
ok((SW[2018065]['UnitId'],SW[2018065]['WeaponId'])==(1185,2016050) and (WA[2018069]['UnitId'],WA[2018069]['WeaponId'],WA[2018069]['Quantity'])==(1185,2016050,120),'Falcons QLB-06 squad weapon and ammo rows')
ok(t['WeaponsJson'][2004002].get('HUDName')=='QLU-11' and sorted({(r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('WeaponId')==2004002})==[(2004003,120)],'QLU-11 2004002 with ammo 2004003 x 120')
for _id in (2015349,2015350):g.put('SquadMembersJson',_id,{'PrimaryWeaponId':2004002})
g.put('SquadWeaponsJson',2018065,{'WeaponId':2004002});g.put('WeaponAmmunitionsJson',2018069,{'WeaponId':2004002,'AmmunitionId':2004003,'Quantity':120})
g.put('Units',1185,{'Cost':75})
ok(not any(r['UnitId']==1185 and 2016050 in (r['PrimaryWeaponId'],r['SpecialWeaponId']) for r in SM.values()) and sum(r['PrimaryWeaponId']==2004002 for r in SM.values() if r['UnitId']==1185)==2
   and U[1185]['Cost']==75,'Falcons: 2 QLU-11, no QLB-06, 75 points')
rec['falcons']={'unit':1185,'QLB-06 -> QLU-11':[2015349,2015350],'cost':[65,75]}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
