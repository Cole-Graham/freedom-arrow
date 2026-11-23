"""Freedom Arrow 0.9.0-dev.37 data over exact 0.9.0-dev.36 (17 Nov 2026). Opened by BA Codex thread 1572407822849810463 (Osama, China cosmetic work).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.37';PREV='0.9.0-dev.36'
# dev.36 was built in out/local-dev36.
BASE=json.loads((REL/f'out/local-dev36/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev36/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- "all of our spec names need their Chinese names displayed. It should be after the English" (Osama 17 Nov 2026 16:4x PST, thread
# 1572407822849810463). UIName only; internal Name, slots and points unchanged. 22 (Test) is not a player spec and is left alone.
# Chinese = the PLA's own service names: 空军 Air Force, 陆军装甲兵 Army armored troops, 火箭军 Rocket Force, 海军特种部队 Navy special forces,
# 陆军摩托化部队 Army motorized force. Untested in game: the spec name font must draw CJK (unit names with Chinese already do in the armory).
_S=t['SpecializationsJson']
_cn={17:('PLAAF Air Force','空军'),18:('PLAGF Armored Force','陆军装甲兵'),19:('PLARF Rocket Conscript Force','火箭军'),20:('PLAN Special Forces','海军特种部队'),21:('PLAGF Motorized','陆军摩托化部队')}
for _k,(_en,_zh) in _cn.items():
    ok(_S[_k].get('CountryId')==4 and _S[_k]['UIName']==_en,f'spec {_k} UIName {_en}')
    g.put('SpecializationsJson',_k,{'UIName':f'{_en} {_zh}'});ok(_S[_k]['UIName']==f'{_en} {_zh}',f'spec {_k} Chinese name')
rec['spec_chinese_names']={str(k):f'{e} {z}' for k,(e,z) in _cn.items()}
# ---------- Not table data, but in this batch (Osama 17 Nov 2026 17:0x PST, thread 1572407822849810463):
# - SF night card portraits (v2, red light): runtime-qa/icons/FA_CN_INF_SF_CQC-Portrait.png and FA_CN_INF_SF_HIGH_TECH-Portrait.png. Embedded in
#   FreedomArrow.Runtime.dll (CardIcons.cs): REBUILD THE RUNTIME DLL for dev.37.
# - 110 Blood Wolves / Godswords US-callout clips, staged by tools/china-voice/stage.py into ChinaVoice/Infantry/English and Units/*_EN.
# ---------- Performance batch (Osama 17 Nov 2026 13:2x-17:5x PST, thread 1567745029781454889: "figure out which hooks are the heaviest or what's causing
# that discrepancy", "Get detailed logging and tracking and then run it again", "we should preload all the models before the game loads", "Let's put all of
# this in the next build"). Code only, no data rows. Measured on Osama's PC, 5v5 Local AI Skirmish Airbase, China Armored SF, Hard, 30 min (work/perf-skirmish-
# 20261117, summ.py): dev.36 with the tracking on 76.8 fps / 554 frames over 50 ms -> with the fixes 85.5 fps / 201 (hooks3), vanilla 101 fps / 22.
# - runtime f7188eb2: NLOS fire hook on FogOfWarWorker update (once per worker per frame, was FogOfWarUnit.Update ~7,500 calls/s); one merged
#   IsTargetOverkilled postfix (OverkillHooks.cs) for AaCooldown, SameUnitClaim, SeadOverkill; FREEDOM_ARROW_HOOK_HEALTH every 60 s (HookHealth.cs).
#   Seen in game: HJ-10 fired at a target added without its own line of sight (hooks1 run, 14:41:47); merged hook 6-8k calls/s, 0 errors.
# - runtime 89d7067d: PerfProbe detail mode (UserData/FreedomArrow/perf-detail.txt, off by default): every mod's Melon callbacks and patch bodies,
#   FREEDOM_ARROW_SLOW_FRAME per frame over 50 ms, FREEDOM_ARROW_MODS per-mod totals; live unit count in the health line.
# - runtime bc321cf1: the settings-screen check (conquest/NativeUi.cs MenuOpen) no longer runs FindObjectOfType once a second in battle (7-11 ms each);
#   FA Music 1.5.3: the menu-button search (FindObjectsOfTypeAll, 5x a second all match) only in the menu scene.
# - ae66e785 / 7d5cc977 / c1155743: FAModels 0.3.34: preload burst (the match's whole deck queue built in one pause, 97 items in 3.2 s on Osama's PC,
#   reset per match); timed update sections (FAMODELS slow update lines); infantry body swaps 6 ms per frame budget; cockpit glass fallback search at
#   most 3 tries per scene; visibility-sync renderer refresh at most 8 per check; pilot rescue spawn list cached per scene; FA Music voice-preset
#   rescans at most once per 2 min per unknown set. The body budget, cockpit cap and visibility stagger are not yet seen in a game.
# BUILD: the complete package needs the new DLLs: --famodels releases/0.6/experimental-model-loader/bin/Release/net6.0/FAModels.dll (0.3.34) and
# --asset Mods/FAMusic.dll=tools/music-player/bin/Release/net6.0/FAMusic.dll (1.5.3); rebuild both from source first. FAMusic.dll is an asset, so this
# also makes a new Assets version. pla-audit-20261112/check_model_carry.py accepts FA Music 1.5.3 by hash (APPROVED_FAMUSIC there).
# The runtime DLL is rebuilt anyway for the night cards above.
# Leave UserData/FreedomArrow/perf-probe.txt, perf-hooks.txt and perf-detail.txt out of packages (switches for tests only).
rec['performance_batch']={'runtime':['f7188eb2','89d7067d','bc321cf1'],'famodels':'0.3.34 (ae66e785, 7d5cc977, c1155743)','famusic':'1.5.3',
    'measured':{'dev36_tracking_on':{'fps':76.8,'frames_over_50ms':554},'with_fixes_hooks3':{'fps':85.5,'frames_over_50ms':201},'vanilla':{'fps':101.1,'frames_over_50ms':22}},
    'evidence':'work/perf-skirmish-20261117'}
# ---------- MD-22 afterburners (Osama 17 Nov 2026 22:4x PST, thread 1567745029781454889: "Fix the md22"; 16 Nov 22:2x: "MD-22 afterburners don't seem
# to work? I think you might need to model it off an F-35 for its stand in"). The MD-22 (976) sat on the S-70 Okhotnik drone, which has no afterburner;
# FAModels draws the MD-22 over it, but the engine effects come from the stand-in. dev.35 could not switch it because the 7 loadouts mount on slots 0 and 1,
# and slot 0 of the F-35A body is its gun. Now the F-35A (US_F35A) is the stand-in and every MD-22 loadout moves slot 0 -> 1 and slot 1 -> 2, the F-35A's
# left and right weapon bay slots (vanilla F-35A loadouts use 1-6). Pylons, weapons, prices and the drone voice preset are unchanged.
_O,_M=t['OptionsJson'],t['ModificationsJson']
_md=[o for o in _O.values() if o['ModificationId']==2018225]
ok(U[976]['HUDName']=='MD-22' and U[976]['ModelFileName']=='DLC3_S70_Okhotnik' and [m['UnitId'] for m in _M.values() if m['Id']==2018225]==[976],'MD-22 on the Okhotnik, loadout mod 2018225')
ok(len(_md)==7 and all(o['Turret0Id'] and o['Turret1Id'] and not any(o.get(f'Turret{i}Id') for i in range(2,21)) for o in _md),'7 MD-22 loadouts on slots 0 and 1 only')
_before={o['Id']:(o['Turret0Id'],o['Turret1Id']) for o in _md}
g.put('Units',976,{'ModelFileName':'US_F35A'})
for _o in _md:g.put('OptionsJson',_o['Id'],{'Turret0Id':0,'Turret1Id':_before[_o['Id']][0],'Turret2Id':_before[_o['Id']][1]})
ok(U[976]['ModelFileName']=='US_F35A' and all((_O[i]['Turret0Id'],_O[i]['Turret1Id'],_O[i]['Turret2Id'])==(0,a,b) for i,(a,b) in _before.items()),'MD-22 on the F-35A, loadouts on slots 1 and 2')
rec['md22_f35a_stand_in']={'unit':976,'model':['DLC3_S70_Okhotnik','US_F35A'],'loadouts':{str(i):{'slot1':a,'slot2':b} for i,(a,b) in _before.items()}}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
