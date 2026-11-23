"""Freedom Arrow 0.9.1-dev.5 data over exact 0.9.1-dev.4 (19 Nov 2026). Opened by BA Codex thread 1572962048705429598 (Lateralus, CSK-131 Recon price).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.1-dev.5';PREV='0.9.1-dev.4'
# 0.9.1-dev.4 was built in out/local-091dev4.
BASE=json.loads((REL/f'out/local-091dev4/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091dev4/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- OriginalCost -> 0 on every unit (Lateralus 19 Nov 2026 13:4x PST, thread 1572962048705429598: "CSK-131 Recon is still 5 points...";
# 13:5x: "set them all to 0", after checking the intended prices against Osama's requests). At load the game does: if OriginalCost != 0 then
# Cost = OriginalCost, else OriginalCost = Cost (LoadUnits.PrepareForMods, 1.2.2.1 0x289A40); the card, deck and shop price is then
# OriginalCost + chosen options (UnitsInfoService.ApplyCurrentMods 0x72B4B0). Every vanilla unit has OriginalCost 0. Eighteen China rows had a
# non-zero OriginalCost (old 0.8 scripts set Cost and OriginalCost together; later price changes set Cost only), so the game used the old price.
# After this, Cost is the price. Cost values checked against the latest request for each card:
#  PGZ-88 1051 90       Osama 14 Nov 11:55 PST "PGZ-88 1200 ground range and 90 pts" (OriginalCost 80 from 0.8.0-dev.57)
#  ZSD-89A x4 40        Osama 16 Nov 00:06 PST "ZSD-89A to 40 pts" (OriginalCost 25 from 0.8.0-dev.72)
#  ZBD-86 Recon 1258 40 Osama 16 Nov 12:51 PST "ztb-86 recon should be 40 pts" (OriginalCost 15 from 0.8.0-dev.90)
#  VT-5 1261 160        Osama 16 Nov 00:29 PST "VT-5 base to 160" (+60 APS option; OriginalCost 140)
#  VT-5 Recon 1262 220  Osama 14 Nov 11:55 PST "VT-5 Recon to 220" (hidden card; OriginalCost 145)
#  ZTL-191 Recon 1263 180 Osama 18 Nov 11:55 PST "ZTL-191 recon should be 180 points" (OriginalCost 120 from 0.8.0-dev.60)
#  CSK-131 Recon 1265 30 Osama 14 Nov "Mengshi Recon, 30 pts"; Lateralus 19 Nov 12:2x "Price 5 -> 30" (OriginalCost 5 from 0.8.0-dev.87)
#  The other 11 (PLZ-05, PHL-16, PHL-191 Ballistic/Cruise, WZ-8, ZTZ-59D1, ZTZ-85-II, SX2190) have OriginalCost = Cost: no price change.
_EXP={907:(260,260),1035:(350,350),1036:(225,225),1051:(80,90),1065:(25,40),1248:(25,40),1249:(25,40),1250:(25,40),1252:(300,300),1258:(15,40),
      1260:(65,65),1261:(140,160),1262:(145,220),1263:(120,180),1264:(85,85),1265:(5,30),1267:(225,225),1269:(50,50)}
_nz={i:(u['OriginalCost'],u['Cost']) for i,u in U.items() if u.get('OriginalCost')}
ok(_nz==_EXP,('units with a non-zero OriginalCost',{i:v for i,v in _nz.items() if _EXP.get(i)!=v},sorted(set(_nz)^set(_EXP))))
ok(all(not u.get('OriginalCost') for i,u in U.items() if i in native['Units']),'vanilla units all have OriginalCost 0')
_sw=sorted({o['ReplaceUnitId'] for o in t['OptionsJson'].values() if o.get('ReplaceUnitId') in _EXP});ok(not _sw,('swap rows onto these units',_sw))
for i in _EXP:g.put('Units',i,{'OriginalCost':0})
ok(not [i for i,u in U.items() if u.get('OriginalCost')] and all(U[i]['Cost']==c for i,(o,c) in _EXP.items()),'every OriginalCost 0, Cost unchanged')
rec['original_cost_zero']={str(i):{'name':U[i]['HUDName'],'OriginalCost':[o,0],'Cost':c,'price_change':[o,c] if o!=c else None} for i,(o,c) in _EXP.items()}
rec['original_cost_zero_verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
