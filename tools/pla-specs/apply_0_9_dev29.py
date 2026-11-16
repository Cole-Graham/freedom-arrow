"""Freedom Arrow 0.9.0-dev.29 data over exact 0.9.0-dev.28 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama: F-22 mirror finish).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.29';PREV='0.9.0-dev.28'
# dev.28 was built in out/local-dev28.
BASE=json.loads((REL/f'out/local-dev28/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev28/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- F-22 stealth coating: mirror finish (Osama 16 Nov 2026 12:4x PST, thread 1571014792016171120: "recreate the F-22 symbiote skin ...
# take the vanilla skin and give it a mirror like reflective finish ... keep rudders and nose cone the standard flat grey along with the edges ...
# the 'vanguard edition' skin, basically all the white areas, we turn into a mirror finish and leave the rest ... a +20 point stealth coating
# loadout option"; 12:5x: "the various bay edges are treated with a darker grey coating, we only want to change that much lighter white area").
# 13:0x PST: "the raptor should have 45% ecm base and a 10 point reduction. Stealth coating adds +30 points for 50% ecm and 2.2 stealth".
# A new F-22 slot "Stealth coating": Standard (+0, default) or Mirror finish (+30: ECM 50%, stealth 2.2). Base F-22: 315 -> 305, ECM 50% -> 45%.
# ECM as Lateralus's plane ECM pods (lateralus/ecm_pods.py): the default ECM ability 2001398 (0.5) is shared with YF-23 and J-50, so the F-22's
# default is relinked to a copy at 0.55, and the option carries a non-default copy at 0.5 linked to the unit. Stealth 2.2 on the card is raw
# 1/2.2 (StealthOverride; F-22 raw 0.5 = 2.0). The look is runtime-only (runtime-qa/MirrorSkin.cs, UserData/FreedomArrow/mirror-skins.json):
# an F-22 with the option gets the Vanguard Edition paint (vanilla skin 4) with its white paint as a mirror; bay edges, panel lines, nose and
# rudders keep the flat grey.
ok(U[297]['Name']=='F-22 Raptor' and U[297]['ModelFileName']=='US_F22' and U[297]['Cost']==315 and U[297]['Stealth']==0.5,'F-22 is unit 297, 315 points, raw stealth 0.5')
ok(not [m for m in M.values() if m.get('UnitId')==297 and m.get('Type')==6],'F-22 has no protection-type slot yet')
_ua=[r for r in UAB.values() if r['UnitId']==297];ok(len(_ua)==1 and _ua[0]['AbilityId']==2001398 and AB[2001398]['ECMAccuracyMultiplier']==0.5 and AB[2001398]['IsDefault'],'F-22: one ability, default ECM 2001398 at 0.5 (50%)')
ok(sorted(r['UnitId'] for r in UAB.values() if r['AbilityId']==2001398)==[297,944,982],'ECM 2001398 shared with J-50 and YF-23: copy, do not edit')
g.put('Units',297,{'Cost':305})
_e45=g.add('AbilitiesJson',AB[2001398],{'Name':'ECM Plane F-22 Default FA 0.55','ECMAccuracyMultiplier':0.55})
g.put('UnitAbilitiesJson',_ua[0]['Id'],{'AbilityId':_e45})
_e50=g.add('AbilitiesJson',AB[2001398],{'Name':'ECM Plane F-22 coating FA 0.5','ECMAccuracyMultiplier':0.5,'IsDefault':False})
g.add('UnitAbilitiesJson',_ua[0],{'UnitId':297,'AbilityId':_e50})
_mf22=g.add('ModificationsJson',M[2019383],{'UnitId':297,'Name':'F22 stealth coating','UIName':'Stealth coating','Order':0})
_z={'Ability1Id':0,'Ability2Id':0,'Ability3Id':0,'Turret0Id':0,'StealthOverride':0.0}
_std=g.add('OptionsJson',O[31101],dict(_z,ModificationId=_mf22,Name='F22 Standard coating',UIName='Custom_Option_None',Order=0,Cost=0,OptionPicture='EMPTY'))
_mir=g.add('OptionsJson',O[31102],dict(_z,ModificationId=_mf22,Name='F22 Mirror finish',UIName='Mirror finish',Order=1,Cost=30,OptionPicture='FA_PLA_OPT_MIRROR',Ability1Id=_e50,StealthOverride=round(1/2.2,4)))
ok(sorted((O[x]['Cost'],O[x]['Name']) for x in (_std,_mir))==[(0,'F22 Standard coating'),(30,'F22 Mirror finish')],'F-22 coating options +0 / +30')
ok(all(O[x][f'Turret{i}Id']==0 for x in (_std,_mir) for i in range(21)) and O[_std]['Ability1Id']==0 and O[_mir]['Ability1Id']==_e50,'coating options change no turret; the mirror option carries the 50% ECM')
ok(U[297]['Cost']==305 and AB[[r for r in UAB.values() if r['UnitId']==297 and AB[r['AbilityId']].get('IsDefault')][0]['AbilityId']]['ECMAccuracyMultiplier']==0.55,'F-22 base: 305 points, default ECM 45%')
ok(sum(1 for r in UAB.values() if r['UnitId']==297 and AB[r['AbilityId']].get('IsDefault'))==1 and AB[2001398]['ECMAccuracyMultiplier']==0.5,'F-22 has one default ability; shared 2001398 unchanged')
ok(abs(O[_mir]['StealthOverride']-0.4545)<1e-4,'mirror finish stealth 2.2 (raw 0.4545)')
_ms=json.loads((SRC/'UserData/FreedomArrow/mirror-skins.json').read_text())
ok([(s['unit'],s['options']) for s in _ms['skins']]==[('F-22 Raptor',['F22 Mirror finish'])] and not any(s.get('all') for s in _ms['skins']),'mirror-skins.json: F-22, by option name, not forced on')
ok(all((SRC/'UserData/FreedomArrow'/s[k]).exists() for s in _ms['skins'] for k in ('albedo','mask')) and (SRC/'runtime-qa/icons/FA_PLA_OPT_MIRROR.png').exists(),'mirror textures and option icon present')
rec['f22_mirror']={'modification':_mf22,'options':{'standard':_std,'mirror':_mir},'cost':{'f22':305,'mirror':30},'ecm':{'base':0.55,'mirror':0.5,'abilities':[_e45,_e50]},'stealth_raw':round(1/2.2,4)}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

