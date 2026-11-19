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
# ---------- CSK-131 Recon shows 5 points (Lateralus 19 Nov 2026 13:4x PST, thread 1572962048705429598: "CSK-131 Recon is still 5 points...", Arsenal
# screenshot). Units.Cost is 30, but the row also has OriginalCost 5. The game sets the card price to OriginalCost + the chosen options' costs
# (UnitsInfoService.ApplyCurrentMods, 1.2.2.1 0x72B4B0); every vanilla unit has OriginalCost 0 (543 of 545 rows, the other 2 also 0), and unit 1265 has
# no options, so the card showed 5. OriginalCost -> 0 as in vanilla, so the card shows Cost 30.
ok(U[1265]['HUDName']=='CSK-131 Recon' and U[1265]['Cost']==30 and U[1265]['OriginalCost']==5,'CSK-131 Recon 1265: Cost 30, OriginalCost 5')
ok(not [m for m in t['ModificationsJson'].values() if m.get('UnitId')==1265] and not [o for o in t['OptionsJson'].values() if o.get('ReplaceUnitId')==1265],'1265 has no options or swap rows')
ok(all(not u.get('OriginalCost') for i,u in U.items() if i in native['Units']),'vanilla units all have OriginalCost 0')
g.put('Units',1265,{'OriginalCost':0});ok(U[1265]['OriginalCost']==0 and U[1265]['Cost']==30,'CSK-131 Recon OriginalCost 0, Cost 30')
rec['csk131_recon_price']={'unit':1265,'OriginalCost':[5,0],'Cost':30,'shown':[5,30],'verified':'data checks only'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
