"""Freedom Arrow 0.9.0-dev.32 data over exact 0.9.0-dev.31 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama: LY-1 radar, laser effect).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.32';PREV='0.9.0-dev.31'
# dev.31 was built in out/local-dev31.
BASE=json.loads((REL/f'out/local-dev31/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev31/FreedomArrow-{PREV}-complete.bamod'
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
# ---------- LY-1 radar (Osama 16 Nov 2026 14:3x PST: "LY-1 needs a radar I forgot"). The LY-1 is on the HQ-17A hull; the HQ-17A's radar is
# its default ability 2010621 (IsRadar, low-altitude optics and weapon range x1.25, high-altitude optics x2, 5 s radar switch). A unit has one
# default ability, and the LY-1's is its own laser APS copy, so the radar fields go onto that same row (vanilla combines flags in one row,
# e.g. T-14 smoke + APS). Radar + APS in one row has no vanilla example: check the HUD buttons in game.
_hq=AB[2010621];ok(_hq['IsRadar'] and _hq['RadarLowAltOpticsModifier']==1.25 and _hq['RadarHighAltOpticsModifier']==2.0 and _hq['RadarSwitchCooldown']==5.0,'HQ-17A radar ability 2010621')
_ly=[a_['Id'] for a_ in AB.values() if a_.get('Name')=='PLA LY-1 laser defense'];ok(len(_ly)==1 and AB[_ly[0]]['IsAPS'] and not AB[_ly[0]]['IsRadar'],'LY-1 laser APS, no radar yet');_ly=_ly[0]
_rad={k:v for k,v in _hq.items() if k.startswith('Radar') or k in ('IsRadar','IsRadarStatic')}
g.put('AbilitiesJson',_ly,_rad)
ok(all(AB[_ly][k]==v for k,v in _rad.items()) and AB[_ly]['IsAPS'] and AB[_ly]['APSCooldown']==10.0,'LY-1 ability: HQ-17A radar + laser APS 10 s')
rec['ly1_radar']={'ability':_ly,'from':2010621,'fields':sorted(_rad)}
# ---------- Lasers without the machine-gun look and sound (Osama 14:3x PST: "it also seems to have a machine gun effect, can we remove that?
# it looks like its firing a machine gun"). The LY-1 laser and the ZTZ-99A/99 LSDW laser were made from 7.62 mm MG rows (PKT sound, 7.62 tracer
# and MG impact burst). The game has no empty effect preset, so: weapon sound = the quiet subsonic sniper shot, impact sound = none (vanilla
# allows an empty ammunition sound), visual = the single sniper tracer. The red beam (dazzler.json) is unchanged.
W=t['WeaponsJson'];AM=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
_lw=[w['Id'] for w in W.values() if w.get('HUDName') in ('LSDW','LY-1 laser')];ok(len(_lw)==2,'two laser weapons: LSDW, LY-1 laser')
_la=sorted({r['AmmunitionId'] for r in WA.values() if r['WeaponId'] in _lw});ok(len(_la)==2,'two laser pulse ammunitions')
ok(all(W[w]['AudioPreset']=='WEAPON_SOUND_PRESET_VEH_MACHINEGUN_Medium_Caliber_PKT' for w in _lw) and all(AM[x]['FXPreset']=='AMMUNITION_VFX_PRESET_7.62_BULLET_Shooting_RADIOFUSE' for x in _la),'lasers still on the PKT / 7.62 presets')
for w in _lw:g.put('WeaponsJson',w,{'AudioPreset':'WEAPON_SOUND_PRESET_INF_SNIPER_Subsonic'})
for x in _la:g.put('AmmunitionsJson',x,{'AudioPreset':'','FXPreset':'AMMUNITION_VFX_PRESET_Sniper_BULLET_US'})
ok(all(AM[x]['AudioPreset']=='' and AM[x]['FXPreset']=='AMMUNITION_VFX_PRESET_Sniper_BULLET_US' for x in _la),'laser pulses: no impact sound, sniper tracer')
rec['laser_effects']={'weapons':_lw,'ammo':_la,'weapon_sound':'WEAPON_SOUND_PRESET_INF_SNIPER_Subsonic','fx':'AMMUNITION_VFX_PRESET_Sniper_BULLET_US'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

