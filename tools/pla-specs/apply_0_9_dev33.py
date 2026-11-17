"""Freedom Arrow 0.9.0-dev.33 data over exact 0.9.0-dev.32 (16 Nov 2026). Opened by BA Codex thread 1571554273639006392 (Lateralus).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.33';PREV='0.9.0-dev.32'
# dev.32 was built in out/local-dev32.
BASE=json.loads((REL/f'out/local-dev32/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev32/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- SEAD plane availability (Lateralus 16 Nov 2026 15:27 PST "queue it"): 13 non-strike SEAD planes 2 -> 3 cards; strike planes and
# SEAD helicopters keep their count. See lateralus/sead_availability.py; lateralus/queued_checks.py checks the counts in the package.
import sead_availability
rec['sead_availability']=sead_availability.apply(t,lambda tab,i,f:g.put(tab,i,f),ok)
# ---------- Osama 16 Nov 2026 16:0x PST, thread 1567745029781454889: "qLU-11 damage set to 1.75 next time, F-35 side winders don't get removed when you swap
# to empty wing tips", "For the AKF loadouts please make sure the loadout icon uses the AKF". F-22 Symbiote stainless steel: mirror-skins.json and
# FA_F22_MIRROR_LITMASK.png (mirror-paint smoothness 0.96 -> 0.80; live on Osama's PC since 16:06).
# - QLU-11 round 2004003 (33 squads): damage 2.5 -> 1.75.
# - F-35A/B/C wingtip "Empty" options 20161/20163/20165 set no pylon, so the Sidewinder pylons (slots 5 and 6, mount 300) stayed after a swap. They
#   now set slots 5 and 6 to the game's blank mount 160, as vanilla Empty options do (AH-1Z 170, Ka-52 213), with the TurretUnits row 160 vanilla
#   helicopters carry.
# - Mixed strike 31081-31084 (J-10A, J-20S, J-31, J-35) showed the GBU-55 picture; now KH38ML, the AKF-98A weapon icon (as J-16 Light strike 24417).
_A=t['AmmunitionsJson'];_TU=t['TurretUnitsJson'];_TJ=t['TurretsJson']
ok(_A[2004003]['HUDName']=='QLU-11 ammo (test)' and _A[2004003]['Damage']==2.5,'QLU-11 round 2.5');g.put('AmmunitionsJson',2004003,{'Damage':1.75})
ok(_TJ[160]['ModelFileName'] is None and not [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==160],'mount 160 is the blank mount')
for u,e,s_ in ((294,20161,20162),(295,20163,20164),(741,20165,20166)):
    ok(O[e]['UIName']=='Custom_Option_Empty' and not any(O[e][f'Turret{i}Id'] for i in range(21)) and (O[s_]['Turret5Id'],O[s_]['Turret6Id'])==(300,300) and O[e]['ModificationId']==O[s_]['ModificationId'] and M[O[e]['ModificationId']]['UnitId']==u,(u,'Empty wingtips set nothing, Sidewinders on 5/6'))
    g.put('OptionsJson',e,{'Turret5Id':160,'Turret6Id':160})
    if not [r for r in _TU.values() if r['UnitId']==u and r['TurretId']==160]:g.add('TurretUnitsJson',{'UnitId':u,'TurretId':160,'Order':0})
_mx=[31081,31082,31083,31084]
ok(all('Mixed strike' in O[i]['UIName'] and 'AKF-98A' in O[i]['UIName'] and O[i]['OptionPicture']=='GBU55' for i in _mx) and O[24417]['OptionPicture']=='KH38ML','Mixed strike options show GBU55; J-16 AKF uses KH38ML')
for i in _mx:g.put('OptionsJson',i,{'OptionPicture':'KH38ML'})
ok(_A[2004003]['Damage']==1.75 and all((O[e]['Turret5Id'],O[e]['Turret6Id'])==(160,160) for e in (20161,20163,20165)) and all(O[i]['OptionPicture']=='KH38ML' for i in _mx),'QLU-11 1.75, F-35 empty wingtips clear, AKF icons')
rec['osama_1606']={'qlu11_damage':[2.5,1.75],'f35_empty_wingtips':[20161,20163,20165],'akf_icons':_mx,'f22_symbiote_smoothness':[0.96,0.80]}
# ---------- J-35 / J-31 AKF loadouts +160 (Osama 16 Nov 2026 16:1x PST, thread 1567745029781454889: "J-35/J-31 AKF loadouts are +160"): Mixed strike
# (4x AKF-98A) 31083 (J-31) and 31084 (J-35) 80 -> 160.
ok([(O[i]['UIName'],O[i]['Cost']) for i in (31083,31084)]==[('Mixed strike (4x AKF-98A)',80)]*2 and [M[O[i]['ModificationId']]['UnitId'] for i in (31083,31084)]==[1251,921],'J-31 / J-35 Mixed strike +80')
for i in (31083,31084):g.put('OptionsJson',i,{'Cost':160})
ok(O[31083]['Cost']==160 and O[31084]['Cost']==160,'J-31 / J-35 AKF loadouts +160')
rec['j31_j35_akf_cost']={'options':[31083,31084],'cost':[80,160]}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
