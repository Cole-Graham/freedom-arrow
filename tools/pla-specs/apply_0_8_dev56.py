"""Freedom Arrow {V} over exact {PREV} (Osama 13 Nov 15:28 PST, thread 1570945828829405345):
"Please add or replace these unit cards. PLAGF Motorized units use "SF Jungle". "Airborne" use Airborne. "Marines" go to
Marines. "Motorized" goes to Motorized. "SF High Tech" goes to Blood Wolves, Godswords, Whistling Arrows and Mountain
Leopards. "SF CQC" to the rest of the SF".
Osama's six supplied images, cropped to 816x549 with the vanilla bottom fade; PortraitFileName only.
- PLAGF Ground Force/Armored (spec 18) -> SF_JUNGLE (the first line; Motorized gets its own image).
- PLAAF (17) -> AIRBORNE; PLA Motorized (21) -> MOTORIZED; Marines, Marine HJ-8, Marine QW-2 -> MARINES.
- Blood Wolves, Godswords, Whistling Arrows, Mountain Leopards -> SF_HIGH_TECH; every other SF card (vanilla SSO portrait,
  and Sea Dragons) -> SF_CQC. Snipers and PLARF conscripts keep their dev.41 cards. Test cards unchanged.
- The AIRBORNE_ASSAULT, AIR_ASSAULT and SEA_DRAGON portraits lose every user and leave the DLL.
"""
import argparse,hashlib,json,re,shutil,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
p=argparse.ArgumentParser();p.add_argument('--prev',required=True);p.add_argument('--version',required=True)
p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--images',type=Path,required=True);a=p.parse_args()
V,PREV=a.version,a.prev
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
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
P=lambda c:f'FA_CN_INF_{c}-Portrait'
NEW=['SF_HIGH_TECH','SF_JUNGLE','AIRBORNE','MARINES','SF_CQC','MOTORIZED'];GONE=['AIRBORNE_ASSAULT','AIR_ASSAULT','SEA_DRAGON']
SPEC={17:'AIRBORNE',18:'SF_JUNGLE',20:'MARINES',21:'MOTORIZED'}
HIGH=('Blood Wolves','Godswords','Whistling Arrows','Mountain Leopards')
MARINE=('Marines','Marine HJ-8 Team','Marine QW-2 Team')
changes={};kept={}
for k,r in sorted(U.items()):
    if r.get('CountryId')!=4 or r.get('Type')!=2 or not r.get('DisplayInArmory'):continue
    sp=member.get(k,set())&{17,18,19,20,21};old=r['PortraitFileName'];n=r['HUDName']
    if not sp:kept[k]=(n,old,'test or no specialization');continue
    assert len(sp)==1,(k,sp);s=next(iter(sp))
    if n.startswith(('Snipers','Armored Sniper Pair')):kept[k]=(n,old,'sniper pair');continue
    if n.startswith(HIGH):card='SF_HIGH_TECH'
    elif old=='RU\\SSO\\SSO' or n.startswith('Sea Dragons'):card='SF_CQC'
    elif s==20:
        assert n.split(' 陆')[0] in MARINE,(k,n);card='MARINES'
    elif s==19:kept[k]=(n,old,'PLARF conscripts');continue
    else:card=SPEC[s]
    new=P(card)
    if new==old:continue
    patches['Units'].setdefault(str(k),{})['PortraitFileName']=new;U[k]['PortraitFileName']=new
    changes[k]={'name':n,'spec':spec[s],'before':old,'after':new}
by={c:sorted(v['name'] for v in changes.values() if v['after']==P(c)) for c in NEW}
assert len(by['SF_HIGH_TECH'])==4 and all(any(x.startswith(h) for x in by['SF_HIGH_TECH']) for h in HIGH),by['SF_HIGH_TECH']
assert len(by['MARINES'])==3 and all(by[c] for c in NEW),by
users=[(k,r['PortraitFileName']) for k,r in U.items() if r.get('PortraitFileName') in {P(c) for c in GONE}]
assert not users,users
icons=REL/'source/runtime-qa/icons'
for c in NEW:shutil.copyfile(a.images/(P(c)+'.png'),icons/(P(c)+'.png'))
for c in GONE:(icons/(P(c)+'.png')).unlink()
cs=(REL/'source/runtime-qa/CardIcons.cs').read_text()
alias=lambda c:''.join(f'        ("{P(c)}{x}","{P(c)}.png"),\n' for x in ('','_BASIC','_HOVER'))
for c in GONE:
    assert alias(c) in cs,c;cs=cs.replace(alias(c),'')
anchor='        ("outline\\\\FA_BLACK_EAGLE-Label","FA_BLACK_EAGLE-Label.png"),\n'
assert cs.count(anchor)==1;cs=cs.replace(anchor,''.join(alias(c) for c in NEW)+anchor)
cs=cs.replace('PLA infantry portraits (Osama, 13 Nov 2026): original generated art, one card shared by each specialization group.',
 'PLA infantry portraits (Osama, 13 Nov 2026): conscripts and sniper pair are original generated art; the other six are Osama\'s supplied images.')
assert cs.count('15 portraits')==1 and cs.count('5 PLA infantry portraits')==1
cs=cs.replace('15 portraits','18 portraits').replace('5 PLA infantry portraits','8 PLA infantry portraits')
(REL/'source/runtime-qa/CardIcons.cs').write_text(cs)
inf=sorted({r['PortraitFileName'] for r in U.values() if r.get('CountryId')==4 and str(r.get('PortraitFileName','')).startswith('FA_CN_INF_')})
assert inf==sorted(P(c) for c in NEW+['CONSCRIPTS','SNIPER_PAIR']),inf
for c in inf:
    assert (icons/(c+'.png')).exists(),c
    for x in ('','_BASIC','_HOVER'):assert f'("{c}{x}","{c}.png")' in cs,(c,x)
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':__doc__.split('\n')[1:4],'changed':len(changes),'kept':len(kept),
 'by_card':{P(c):v for c,v in by.items()},'changes':{str(k):v for k,v in changes.items()},'kept_units':{str(k):v for k,v in kept.items()},
 'removed_images':[P(c) for c in GONE],'images':{c:hashlib.sha256((icons/(c+'.png')).read_bytes()).hexdigest() for c in inf}}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes(z.read('UserData/FAModels/models.json'))
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('changed',len(changes),'kept',len(kept));print(json.dumps(receipt['by_card'],ensure_ascii=False,indent=1))
