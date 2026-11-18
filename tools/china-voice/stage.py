"""Stage the China voice lines into the gameplay payload (Osama 16 Nov 2026 19:56 PST: build dev.34 with them, thread 1571014792016171120).
Source: work/china-voices (ElevenLabs v4, Old Radio filter, -16 LUFS; every clip checked with speech-to-text for non-speech sounds).
- Mandarin sets v2/listen/<Category>/<Style>/<NN_Trigger>/<NN_voice>.mp3 -> ChinaVoice/<Category>/<Style>/<Trigger>/<NN>.mp3
- Unit selection lines v2/listen/Units/<Category>/<Unit>/Selection_NN_<voice>.mp3 -> ChinaVoice/Units/<Unit>/Selection/<NN>.mp3
- Blood Wolves and Godswords speak English (San Chi): wolves/listen-SanChi/Shared -> ChinaVoice/Infantry/English, and their own lines
  -> ChinaVoice/Units/<Unit>_EN/<Trigger>. Their Mandarin unit lines are not staged.
Writes china-voices.json: unit id -> voice set and unit folder, plus the fallback set by unit Type (and CategoryType) for unmapped China units.
usage: stage.py VOICES_DIR UNITS_JSON OUT_USERDATA_DIR"""
import json,shutil,sys,re
from pathlib import Path
V,UJ,OUT=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])
U={int(k):v for k,v in json.loads(UJ.read_text()).items() if v}
root=OUT/'ChinaVoice'
if root.exists():shutil.rmtree(root)
n=0
def put(src,dst):
    global n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);n+=1
trig=lambda d:re.sub(r'^\d\d_','',d)
for f in sorted((V/'v2/listen').glob('*/*/*/*.mp3')):
    cat,sty,t,name=f.relative_to(V/'v2/listen').parts
    if cat=='Units':continue
    put(f,root/cat/sty/trig(t)/(name[:2]+'.mp3'))
ENGLISH={'Blood_Wolves','Godswords'}
for f in sorted((V/'v2/listen/Units').glob('*/*/*.mp3')):
    cat,unit,name=f.relative_to(V/'v2/listen/Units').parts
    if unit in ENGLISH:continue
    put(f,root/'Units'/unit/'Selection'/(re.search(r'_(\d\d)_',name)[1]+'.mp3'))
W=V/'wolves/listen-SanChi'
for f in sorted((W/'Shared').glob('*/*.mp3')):put(f,root/'Infantry/English'/trig(f.parent.name)/(f.name[:2]+'.mp3'))
for u in ENGLISH:
    for f in sorted((W/u).glob('*/*.mp3')):put(f,root/'Units'/(u+'_EN')/trig(f.parent.name)/(f.name[:2]+'.mp3'))
# Additive US-military callouts for Blood Wolves and Godswords (Osama 17 Nov 2026 17:03 PST, thread 1572407822849810463: "All are approved", no "Hooah"):
# wolves/callouts/listen-SanChi, numbered after the lines above in the same trigger folders (ChinaVoice.cs plays every mp3 in a folder).
C=V/'wolves/callouts/listen-SanChi'
for sub,dst in [('Shared',root/'Infantry/English')]+[(u,root/'Units'/(u+'_EN')) for u in sorted(ENGLISH)]:
    for d in sorted(p for p in (C/sub).iterdir() if p.is_dir()):
        out=dst/trig(d.name);k=len(list(out.glob('*.mp3'))) if out.exists() else 0
        for i,f in enumerate(sorted(d.glob('*.mp3')),k+1):put(f,out/f'{i:02d}.mp3')
# DF-31A (Osama 16 Nov 22:2x: "a lot of unique voice lines for the DF-31 nuclear ... calm ... old chinese phrases"): its own full set, df31/listen.
for f in sorted((V/'df31/listen').glob('*/*.mp3')):put(f,root/'Special/DF31'/f.parent.name/f.name)
# unit -> set. Names in v2/unit_map.json are the card names (HUDName) when the map was written; Blood Wolves was renamed in dev.34.
M=json.loads((V/'v2/unit_map.json').read_text());byname={}
for i,u in U.items():
    if u.get('CountryId')==4:byname.setdefault(u.get('HUDName'),[]).append(i)
byname.setdefault('Blood Wolves 血狼',[]).extend(byname.get('Blood Wolves 朱日和之狼',[]))
folders={p.name for p in (root/'Units').iterdir()}
def unit_folder(cat,hud):
    key=hud.split(' ')[0] if cat!='Infantry' else '_'.join(w for w in hud.split(' ') if not any('一'<=c<='鿿' for c in w))
    key=key.replace('/','_')
    key={'PAP_Snow_Leopards':'Snow_Leopards','HQ-9B':'HQ-9','HQ-9C':'HQ-9'}.get(key,key)   # folder names in v2/air.py, tanks.py, vehicles.py, infantry.py
    for cand in (key,key.split('_')[0],hud.split('/')[0].split(' ')[0]):
        if cand in folders:return cand
    return None
units={}
for cat,sty,hud,_ in M:
    for i in byname[hud]:
        e={'set':f'{cat}/{sty}'};f=unit_folder(cat,hud)
        if hud.startswith(('Blood Wolves','Godswords')):e={'set':'Infantry/English','unit':('Blood_Wolves' if hud.startswith('Blood') else 'Godswords')+'_EN'}
        elif f:e['unit']=f
        units[str(i)]=e
for i,u in U.items():
    if u.get('CountryId')==4 and (u.get('HUDName') or '').startswith('DF-31'):units[str(i)]={'set':'Special/DF31'}
cfg={'note':'FreedomArrow ChinaVoice.cs (dev.34). set = ChinaVoice/<set>/<Trigger>; unit = extra ChinaVoice/Units/<unit>/<Trigger> lines. Unmapped China units use fallback by Type, or Type:CategoryType.',
     'units':units,'fallback':{'2':'Infantry/Regular','16':'Plane/Regular','8':'Helicopter/Regular','4:2':'Tank/Regular','4':'Vehicle/Regular'},
     'volume':0.234,
     # Drones say nothing (Osama 16 Nov 22:2x). Units with a Drone sound preset are found by the runtime; these drones use other presets.
     'silent':[1105,1253]}   # Z-6B UAV, FH-97A
(OUT/'china-voices.json').write_text(json.dumps(cfg,indent=1,ensure_ascii=False)+'\n')
used={e.get('unit') for e in units.values()}-{None}
print('clips',n,'units mapped',len(units),'unit folders',len(folders),'unused unit folders',sorted(folders-used))
