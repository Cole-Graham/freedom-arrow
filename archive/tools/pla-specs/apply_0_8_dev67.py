"""Freedom Arrow 0.8.0-dev.67 over exact 0.8.0-dev.66 (Osama 13 Nov 18:2x PST, thread 1567745029781454889):
Sea Dragons and Beijing Swords amphibious; Forward Observers get the VDV Razvedka unit icon.
- Sea Dragons and Beijing Swords (1187, mobility 2013282): amphibious. Their mobility rows (2013406 for the 1191 card, 2013377 for the hidden 1190 draft) take the vanilla
amphibious-infantry pattern of PDSS, Green Light Team and KNT: IsAmphibious true, water speed 9 -> 18.
- Forward Observers (1164): unit icon (ThumbnailFileName) US_CAVALRY_SCOUTS-Label -> RU_VDV_RAZVEDKA-Label (VDV Razvedka 114).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.67'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.66.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,UP,MOB=t['Units'],t['UnitPropulsionsJson'],t['MobilityJson']
pdss=[MOB[r['MobilityId']] for r in UP.values() if U.get(r['UnitId'],{}).get('HUDName','').strip()=='PDSS'];assert pdss and all(m['IsAmphibious'] and m['MaxSpeedWater']==18.0 for m in pdss)
rows={}
for uid in (1190,1191,1187):
    assert U[uid]['HUDName'].startswith(('Sea Dragons','Beijing Swords'))
    for r in UP.values():
        if r['UnitId']==uid:
            mid=r['MobilityId'];assert sorted({x['UnitId'] for x in UP.values() if x['MobilityId']==mid})==[uid]
            rows[mid]=(MOB[mid]['IsAmphibious'],MOB[mid]['MaxSpeedWater']);g.put('MobilityJson',mid,{'IsAmphibious':True,'MaxSpeedWater':18.0})
FO=1164;assert U[FO]['HUDName'].startswith('Forward Observers') and U[114]['ThumbnailFileName']=='RU_VDV_RAZVEDKA-Label'
fo_before=U[FO]['ThumbnailFileName'];g.put('Units',FO,{'ThumbnailFileName':U[114]['ThumbnailFileName']})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for mid in rows:ok(MOB[mid]['IsAmphibious'] is True and MOB[mid]['MaxSpeedWater']==18.0,('amphibious',mid))
ok(U[FO]['ThumbnailFileName']=='RU_VDV_RAZVEDKA-Label','Forward Observers icon')
receipt={'version':V,'forward_observers_icon':[fo_before,'RU_VDV_RAZVEDKA-Label'],'base':'0.8.0-dev.66','base_sha256':BASE,'request':'Osama 13 Nov 18:2x PST: Sea Dragons Amphibious; Beijing Swords amphibious; Forward observer give icon from VDV Razvedka','rows_before':{str(k):v for k,v in rows.items()},'pattern':'vanilla PDSS / Green Light Team / KNT: amphibious, water 18','checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,rows)
