"""Freedom Arrow 0.9.2-dev.8 data over exact 0.9.2-dev.7 (build 239; 0.9.2 build 240 has the same data). Opened by BA Codex thread 1572407822849810463.
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.2-dev.8';PREV='0.9.2-dev.7'
# 0.9.2-dev.7 (build 239) was built in out/local-092dev7. 0.9.2 (build 240) has the same game data.
BASE=json.loads((REL/f'out/local-092dev7/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-092dev7/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- China infantry cards from community art (Osama 20 Nov 2026 00:4x PST, thread 1572407822849810463: "These are new art given by our community",
# "Let's remove the broken arrow logo and use them for unit cards and art"). 12 images, BROKEN ARROW mark removed (work/osama-art-20261120: delogo
# corners rebuilt and pasted back only over the logo), cropped to 816x549 with the vanilla bottom fade -> releases/0.6/source/runtime-qa/icons/
# FA_CN_INF_<CARD>-Portrait.png, registered in CardIcons.cs. Each card goes to the squads whose weapon or unit matches the picture. PortraitFileName only.
_CARDS={
 'AIRBORNE_HELO':['Airborne 空降兵','Assault Raiders 突击队','Pathfinders 先遣队','Recon 侦察组'],
 'AIRBORNE_SOF':['Thunder Gods 雷神'],
 'HJ12':['HJ-12 Team'],
 'HJ73':['HJ-73D Team','HJ-8E Team'],
 'MANPAD':['QW-2 Team','Marine QW-2 Team','FN-6 Team','QW-12 Patrol 防空巡逻','AA Troopers 防空班','Air Defense Scouts 防空侦察'],
 'MARINE_JUNGLE':['Marines 陆战队','Marine HJ-8H Team'],
 'JIAO_LONG':['Sea Dragons 蛟龙','Marine Recon'],
 'MECH_INF':['Mech. Rifles 机步班','Armored Scouts 装甲侦察','Moto. Riflemen 摩步班','Infantry 步兵'],
 'PF98':['PF-98 Team','Tank Hunters 坦克杀手','AT Troopers 反坦克组'],
 'QJZ171':['QJZ-89 Team','Weapons Squad 火力班','QJY-201'],
 'SCOUT_SNIPER':['Snipers 狙击组','Armored Sniper Pair 狙击组'],
 'PAP':['PAP Snow Leopards 雪豹','Counter-Raid Team 反袭击队'],
}
_inspec={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r}
_cn=[i for i,u in U.items() if u and u.get('CountryId')==4 and u.get('Type')==2 and i in _inspec]
_icons=REL/'source/runtime-qa/icons';_cs=(REL/'source/runtime-qa/CardIcons.cs').read_text()
_done={}
for _c,_names in _CARDS.items():
    _p=f'FA_CN_INF_{_c}-Portrait'
    ok((_icons/(_p+'.png')).is_file(),(_p,'icon file'))
    for _x in ('','_BASIC','_HOVER'):ok(f'("{_p}{_x}","{_p}.png")' in _cs,(_p,_x,'CardIcons alias'))
    for _n in _names:
        _ids=[i for i in _cn if U[i]['HUDName']==_n];ok(_ids,(_n,'card exists'))
        for _i in _ids:
            ok(_i not in _done,(_i,'one card per unit'));_done[_i]=(_n,U[_i].get('PortraitFileName'),_p)
            g.put('Units',_i,{'PortraitFileName':_p});ok(U[_i]['PortraitFileName']==_p,_i)
rec['community_cards']={str(i):{'name':n,'before':b,'after':a} for i,(n,b,a) in sorted(_done.items())}
ok(len(_done)==34,('34 cards (Snipers and QJZ-89 Team are two cards each)',len(_done)))
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
