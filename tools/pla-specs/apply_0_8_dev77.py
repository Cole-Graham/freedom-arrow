"""Freedom Arrow 0.8.0-dev.77 over exact 0.8.0-dev.76 (Osama 13 Nov 20:1x PST, thread 1567745029781454889):
- ZTQ-15, ZTQ-15 Recon, VT-5, VT-5 Recon (906, 1240, 1261, 1262): 105 mm gun 2009127 reload 4 s (was 4-5 s).
- ZSD-63C (960): removed (hidden, card and its transport links deleted), as the dev.49 roster removals.
- ZSD-89 (1064 PLAGF Armored, 1246 PLAN): 12 HP (was 10), as the ZSD-89A.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.77'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.76.json').read_text())['complete']['sha256']
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
g=Graph(t,patches,native);U,W,WA,AR,UA,SA,TA=(t[k] for k in ('Units','WeaponsJson','WeaponAmmunitionsJson','ArmorsJson','UnitArmorsJson','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson'))
def hud(i,n):assert U[i]['HUDName']==n,(i,U[i]['HUDName'])
rec={}
GUN=2009127;cards={906:'ZTQ-15',1240:'ZTQ-15 Recon',1261:'VT-5',1262:'VT-5 Recon'}
for i,n in cards.items():hud(i,n)
assert W[GUN]['HUDName']=='105 mm high-pressure rifled gun' and sorted({r['UnitId'] for r in WA.values() if r['WeaponId']==GUN})==sorted(cards)
rec['gun_reload']=[[W[GUN]['MagazineReloadTimeMin'],W[GUN]['MagazineReloadTimeMax']],[4.0,4.0]]
g.put('WeaponsJson',GUN,{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
Z63=960;hud(Z63,'ZSD-63C')
g.put('Units',Z63,{'DisplayInArmory':False});assign['assignments'].pop(str(Z63),None)
ids={r['Id'] for r in SA.values() if r['UnitId']==Z63};nta=0
for r in list(TA.values()):
    if r['SpecializationAvailabilityId'] in ids or r['UnitId']==Z63:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=Z63]
rec['zsd63c_removed']={'cards':len(ids),'transport_links':nta}
hp={}
for i in (1064,1246):
    hud(i,'ZSD-89');arm=[r['ArmorId'] for r in UA.values() if r['UnitId']==i];assert len(arm)==1 and [r['UnitId'] for r in UA.values() if r['ArmorId']==arm[0]]==[i]
    hp[i]=[AR[arm[0]]['MaxHealthPoints'],12];g.put('ArmorsJson',arm[0],{'MaxHealthPoints':12})
rec['zsd89_hp']=hp
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok((W[GUN]['MagazineReloadTimeMin'],W[GUN]['MagazineReloadTimeMax'])==(4.0,4.0),'ZTQ-15/VT-5 gun 4 s')
ok(not U[Z63]['DisplayInArmory'] and not [r for r in SA.values() if r['UnitId']==Z63] and not [r for r in TA.values() if r['UnitId']==Z63] and str(Z63) not in assign['assignments'],'ZSD-63C removed')
ok(all(AR[[r['ArmorId'] for r in UA.values() if r['UnitId']==i][0]]['MaxHealthPoints']==12 for i in (1064,1246)),'ZSD-89 12 HP')
receipt={'version':V,'base':'0.8.0-dev.76','base_sha256':BASE,'request':'Osama 13 Nov 20:1x PST: ZTQ-15 4 second reload and VT-5 not 4-5; ZSD-63C remove; ZSD-89 12 hp',**rec,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec))
