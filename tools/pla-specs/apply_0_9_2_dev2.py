"""Freedom Arrow 0.9.2-dev.2 data over exact 0.9.2-dev.1 (build 232). Opened by BA Codex thread 1572407822849810463 (Osama, China helicopter rebalance).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.2-dev.2';PREV='0.9.2-dev.1'
# 0.9.2-dev.1 (build 232) was built in out/local-092dev1.
BASE=json.loads((REL/f'out/local-092dev1/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-092dev1/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- China helicopter rebalance against US/RU (Osama 19 Nov 2026 20:30 PST, thread 1572407822849810463: "Apply this whole rebalancing to the
# next dev build", after the line-by-line proposal sheet 1zRtOuP5XgN2DhuBMwaTY-8nbdPV5hf7oaCSSglrRkrw: "much more in line with what we want").
# Every China helicopter-tab card and option was priced from the closest US/RU card and what US/RU options charge for the same weapon
# (8 Hellfire K 90, 8 Verba 90, 8 Kokon 30, 8 Ataka 50, 4 LMUR 100, 2 AIM-9 50, 14 APKWS 15; mixed packages 5 below the sum).
# Option prices assume W1-W4 (China helicopter missiles 12 damage). W7 (rocket pods too weak) is open and not in this section.
_O=t['OptionsJson'];_M=t['ModificationsJson'];_A=t['AmmunitionsJson'];_AB=t['AbilitiesJson'];_UA=t['UnitAbilitiesJson']
_HU=[[1239, "Z-10", 195, 100], [913, "Z-10K", 195, 120], [1270, "Z-10U", 195, 120], [1237, "Z-19G Recon", 75, 90], [1104, "Z-21", 115, 110], [1135, "Z-21 Recon", 115, 90], [941, "Z-9WA", 65, 55], [1133, "Z-9WA Recon", 65, 55], [1107, "Z-9", 65, 55], [942, "Z-11WB", 60, 50]]  # unit, name, base before, base after (U lines that change)
for _u,_n,_c0,_c1 in _HU:
    ok(U[_u]['HUDName']==_n and U[_u]['Cost']==_c0 and not U[_u].get('OriginalCost'),(_u,_n,'base before'))
    ok(not any(o and o.get('ReplaceUnitId')==_u for o in _O.values()),(_u,'no swap row'))
    g.put('Units',_u,{'Cost':_c1});ok(U[_u]['Cost']==_c1,(_u,'base after'))
_HO=[[24508, "Z-10", "Multirole (HJ-8)", 65, 55], [24509, "Z-10", "Fire support", 70, 95], [24506, "Z-10", "Heavy anti-armor (AKD-9)", 80, 75], [24510, "Z-10", "Multirole (HJ-10)", 100, 115], [24505, "Z-10", "Heavy anti-armor (HJ-10)", 95, 115], [24495, "Z-10K", "Heavy anti-armor (HJ-8)", 70, 80], [24496, "Z-10K", "Fire support", 80, 110], [24494, "Z-10K", "Heavy anti-armor (AKD-9)", 80, 75], [24497, "Z-10K", "Multirole (8x HJ-10, 14x FS-70A)", 90, 105], [24498, "Z-10K", "Multirole (8x HJ-10, 14x FS-90)", 100, 115], [24493, "Z-10K", "Heavy anti-armor (HJ-10)", 95, 115], [31088, "Z-10U", "Multirole (HJ-8)", 65, 55], [31089, "Z-10U", "Fire support", 70, 95], [31086, "Z-10U", "Heavy anti-armor (AKD-9)", 80, 75], [31090, "Z-10U", "Multirole (HJ-10)", 100, 115], [31085, "Z-10U", "Heavy anti-armor (HJ-10)", 95, 115], [24524, "Z-19", "Multirole (AKD-9)", 75, 60], [24523, "Z-19", "Multirole (HJ-10)", 100, 105], [24525, "Z-19", "Heavy anti-armor", 110, 115], [31096, "Z-19", "Escort (8x TY-90, 14x FS-90)", 85, 110], [24528, "Z-19G", "Multirole (AKD-9)", 75, 60], [24527, "Z-19G", "Multirole (HJ-10)", 100, 105], [24529, "Z-19G", "Heavy anti-armor", 110, 115], [31097, "Z-19G", "Escort (8x TY-90, 14x FS-90)", 85, 110], [24583, "Z-19G Recon", "Fire support (FS-90)", 20, 40], [24582, "Z-19G Recon", "Fire support (FS-70A)", 20, 30], [24513, "Z-21", "Air escort", 75, 150], [24512, "Z-21", "Fire support", 30, 55], [24514, "Z-21", "Multirole (8x HJ-10, 14x FS-90)", 100, 115], [24645, "Z-21", "Multirole (4x CM-501GA, 14x FS-70A)", 95, 115], [24511, "Z-21", "Multirole (8x HJ-10, 14x FS-70A)", 100, 105], [24643, "Z-21", "Heavy anti-armor (8x HJ-10)", 110, 135], [24644, "Z-21", "Heavy anti-armor (16x HJ-10)", 155, 180], [24586, "Z-21 Recon", "Fire support (FS-70A)", 10, 30], [24587, "Z-21 Recon", "Fire support (FS-90)", 20, 40], [24544, "Z-9WA", "Air escort", 65, 90], [24545, "Z-9WA", "Fire support (72x 57 mm rocket)", 35, 50], [24648, "Z-9WA", "Multirole (AKD-9)", 40, 45], [24646, "Z-9WA", "Multirole (HJ-8)", 40, 45], [24647, "Z-9WA", "Fire support (36x 57 mm rocket)", 50, 70], [24543, "Z-9WA", "Heavy anti-armor", 50, 30], [24584, "Z-9WA Recon", "Fire support (57 mm rocket)", 35, 50]]  # option, unit, option name, before, after (L lines that change)
for _o,_n,_on,_c0,_c1 in _HO:
    _m=_M[_O[_o]['ModificationId']];ok(U[_m['UnitId']]['HUDName']==_n and U[_m['UnitId']]['CountryId']==4,(_o,_n,'option owner'))
    ok((_O[_o].get('Cost') or 0)==_c0 and not _O[_o].get('ReplaceUnitId'),(_o,_on,'option before'))
    g.put('OptionsJson',_o,{'Cost':_c1});ok(_O[_o]['Cost']==_c1,(_o,'option after'))
# W1-W4: China helicopter/drone missiles 10.5 -> 12, like Hellfire K (164), Vikhr (83), Ataka (123) and Kokon (80). Ground ATGMs stay 10.5.
# HJ-10 2017053 and AKD-9 2017071 are also on the Wing Loong.
for _i,_n,_ref in ((2017053,'HJ-10',164),(2017071,'AKD-9',123),(2017077,'HJ-8',80),(2019088,'AKD-11',164)):
    ok(_A[_i]['HUDName']==_n and _A[_i]['Damage']==10.5 and _A[_ref]['Damage']==12.0,(_i,_n,'10.5'))
    _users={U[r['UnitId']]['Type'] for r in t['WeaponAmmunitionsJson'].values() if r and r.get('AmmunitionId')==_i and r['UnitId'] in U}
    ok(_users<={8,16},(_i,'aircraft only',_users))
    g.put('AmmunitionsJson',_i,{'Damage':12.0})
# W5: TY-90 high-altitude range 775 -> 500 like Stinger (18), Verba (97) and Igla-S (127).
for _i in (2016167,2017083):
    ok(_A[_i]['HUDName']=='TY-90' and _A[_i]['HighAltRange']==775.0 and _A[18]['HighAltRange']==_A[97]['HighAltRange']==_A[127]['HighAltRange']==500.0,(_i,'TY-90 775'))
    g.put('AmmunitionsJson',_i,{'HighAltRange':500.0})
# W6: Z-9 flares 10 -> 15: link vanilla row 23 (Dauphin; identical apart from the flare count) and drop our row 2011621 (Z-9 its only user).
_k=lambda r:{f:v for f,v in r.items() if f not in ('Id','Name','DecoyQuantity')}
ok(_k(_AB[2011621])==_k(_AB[23]) and _AB[2011621]['DecoyQuantity']==10 and _AB[23]['DecoyQuantity']==15,'Z-9 row = row 23 but flares')
_z9=[r for r in _UA.values() if r and r.get('AbilityId')==2011621]
ok(len(_z9)==1 and _z9[0]['UnitId']==1107 and U[1107]['HUDName']=='Z-9','Z-9 only user of 2011621')
ok(not any(o and 2011621 in (o.get('Ability1Id'),o.get('Ability2Id'),o.get('Ability3Id')) for o in _O.values()),'2011621 not on options')
g.put('UnitAbilitiesJson',_z9[0]['Id'],{'AbilityId':23});g.remove('AbilitiesJson',2011621)
rec['china_helo_rebalance']={'sheet':'1zRtOuP5XgN2DhuBMwaTY-8nbdPV5hf7oaCSSglrRkrw','units':len(_HU),'options':len(_HO),
    'missiles_12':[2017053,2017071,2017077,2019088],'ty90_high_alt_500':[2016167,2017083],'z9_ability':[2011621,23]}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
