"""Freedom Arrow 0.9.4-dev.1 batch data over exact 0.9.3 (build 242). Opened by BA Codex thread 1567745029781454889 (Osama, Spetsnaz Alpha stand-off RPG-30).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.4-dev.1';PREV='0.9.3'
# 0.9.3 (build 242, the playtest released 20 Nov 2026) was built in out/local-093r242.
BASE=json.loads((REL/f'out/local-093r242/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-093r242/FreedomArrow-{PREV}-complete.bamod'
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
O=t['OptionsJson'];SM=t['SquadMembersJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson']
# ---------- 1. Spetsnaz Alpha, stand-off loadout: 6 RPG-30 (Osama 20 Nov 2026 13:2x PST, thread 1567745029781454889: "Next patch, we need to give 6 rpg
# -30 to spets alpha stand off loadout"). The stand-off option (1511, Custom_Option_Standoff) swaps in unit 354. Disposable launchers are one round per
# carrier (SquadMembers.SpecialWeaponId x WeaponAmmunitions.Quantity 1, the vanilla pattern), so 6 RPG-30 = 6 carriers: the 4 existing (583, 584, 592,
# 593) plus riflemen 587 and 589 (AK-107, no special weapon). Squad size (14), primaries, cost and the close-quarters loadout (unit 131) stay as they are.
_RPG30=169;_NEW=(587,589)
ok(O[1511]['UIName']=='Custom_Option_Standoff' and O[1511]['ReplaceUnitId']==354 and U[354]['HUDName'].strip()=='Spetsnaz Alpha','stand-off option -> unit 354')
ok(W[_RPG30]['HUDName']=='RPG-30' and W[_RPG30]['Type']==63,'weapon 169 is the disposable RPG-30')
_carr=lambda:sorted(m['Id'] for m in SM.values() if m.get('UnitId')==354 and m.get('SpecialWeaponId')==_RPG30)
ok(_carr()==[583,584,592,593],('RPG-30 carriers before',_carr()))
_wa=[r for r in WA.values() if r.get('UnitId')==354 and r.get('WeaponId')==_RPG30]
ok(len(_wa)==1 and _wa[0]['Quantity']==1,('RPG-30 ammo row',_wa))
_men=sum(1 for m in SM.values() if m.get('UnitId')==354);ok(_men==14,('squad size',_men))
for mid in _NEW:
    ok(SM[mid]['UnitId']==354 and SM[mid]['PrimaryWeaponId']==911 and not SM[mid].get('SpecialWeaponId'),(mid,'AK-107 rifleman without a special weapon'))
    g.put('SquadMembersJson',mid,{'SpecialWeaponId':_RPG30})
ok(_carr()==[583,584,587,589,592,593] and sum(1 for m in SM.values() if m.get('UnitId')==354)==_men,('6 RPG-30 carriers, squad size unchanged',_carr()))
rec['spetsnaz_alpha_standoff_rpg30']={'unit':354,'option':1511,'carriers':[4,6],'new_carriers':list(_NEW),'rounds_per_carrier':1,'cost_unchanged':O[1511].get('Cost')}
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
