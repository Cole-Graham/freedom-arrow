"""Freedom Arrow 0.8.0-dev.41 over exact 0.8.0-dev.40 (Osama 13 Nov 13:14 PST, thread 1570897564474015785):
"conscripts card are used on all conscript units. All Motorized use airborne assault, airborne units use air assault,
PLAGF armored use airborne assault, snipers use sniper pair obviuosly, we need some for SF and I'll get more images,
marines use sea dragon, type 21 can be saved for later".
PortraitFileName only. Special forces (current SSO portrait) wait for more images, except Sea Dragons and snipers.
Test-spec units and units without a specialization keep their portraits. Images are embedded in FreedomArrow.Runtime.dll
(CardIcons, FA_CN_INF_*-Portrait with _BASIC/_HOVER aliases).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
V='0.8.0-dev.41';PREV='0.8.0-dev.40'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
U=t['Units'];S=t['SpecializationsJson']
spec={s:S[s]['Name'] for s in S if S[s].get('CountryId')==4}
assert spec[17]=='PLA PLAAF Air Force' and spec[18]=='PLA PLAGF Ground Force/Armored' and spec[19]=='PLA PLARF Rocket/Reservist' and spec[20]=='PLA PLAN Navy/SOF' and spec[21]=='PLA PLAGF Motorized',spec
member={}
for r in t['SpecializationAvailabilitiesJson'].values():member.setdefault(r['UnitId'],set()).add(r['SpecializationId'])
CARD={17:'AIR_ASSAULT',18:'AIRBORNE_ASSAULT',19:'CONSCRIPTS',20:'SEA_DRAGON',21:'AIRBORNE_ASSAULT'}
SF='RU\\SSO\\SSO'
changes={};kept={}
for k,r in sorted(U.items()):
    if r.get('CountryId')!=4 or r.get('Type')!=2 or not r.get('DisplayInArmory'):continue
    sp=member.get(k,set())&set(CARD)
    old=r['PortraitFileName']
    if not sp:kept[k]=(r['HUDName'],old,'test or no specialization');continue
    assert len(sp)==1,(k,sp)
    s=sp.pop()
    if r['HUDName'].startswith(('Snipers','Armored Sniper Pair')):card='SNIPER_PAIR'
    elif r['HUDName'].startswith('Sea Dragons'):card='SEA_DRAGON'
    elif old==SF:kept[k]=(r['HUDName'],old,'special forces: waiting for SF images');continue
    else:card=CARD[s]
    new=f'FA_CN_INF_{card}-Portrait'
    patches['Units'].setdefault(str(k),{})['PortraitFileName']=new
    changes[k]={'name':r['HUDName'],'spec':spec[s],'before':old,'after':new}
icons=REL/'source/runtime-qa/icons'
for c in {v['after'] for v in changes.values()}:assert (icons/(c+'.png')).exists(),c
cs=(REL/'source/runtime-qa/CardIcons.cs').read_text()
for c in {v['after'] for v in changes.values()}:
    for alias in ('','_BASIC','_HOVER'):assert f'("{c}{alias}","{c}.png")' in cs,(c,alias)
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':__doc__.split('\n')[1:4],'changed':len(changes),'kept':len(kept),
 'by_card':{c:sorted(v['name'] for v in changes.values() if v['after']==c) for c in sorted({v['after'] for v in changes.values()})},
 'changes':{str(k):v for k,v in changes.items()},'kept_units':{str(k):v for k,v in kept.items()},
 'images':{c:hashlib.sha256((icons/(c+'.png')).read_bytes()).hexdigest() for c in sorted({v['after'] for v in changes.values()})}}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
MJ='UserData/FAModels/models.json';(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes(z.read(MJ))
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('changed',len(changes),'kept',len(kept));print(json.dumps(receipt['by_card'],ensure_ascii=False,indent=1))
