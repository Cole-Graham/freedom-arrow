"""Package the next Freedom Arrow 0.8/0.9 gameplay version over the exact previous complete package.

Usage: package_0_8_next.py --prev VERSION --version VERSION --build N --base PREV_COMPLETE --outdir DIR [--assets ASSETS.bamod].
Changed constants, identity files and the version receipt go in. Writes the complete package (Vengeance switcher) and the
launcher gameplay package. The gameplay package pairs with the assets package of the previous build's receipt (or --assets).
Lateralus 13 Nov 2026: gameplay and assets are ALWAYS available separately. When the complete package's model files differ
from that assets package, this script makes the next assets version (make_assets.py) and the receipt names it; publish it
with the gameplay package.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,zipfile
sys.path.insert(0,str(Path(__file__).parent));import make_assets
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
enc=lambda x:(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
# 0.9.0-dev.4 (FAModels 0.3.26 textures, ~3,700 files): --asset files stay on disk until staged, not all in memory.
H=lambda x:digest(x) if isinstance(x,Path) else sha(x)
RENAMED_DLLS={f'Mods/{n}.dll':f'Mods/FA{n}.dll' for n in ('ArrowQueue','BALocalSkirmish','FlatIncomeMod','HudQuick','TeamVoice')}
ASSET=('Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')
p=argparse.ArgumentParser(description=__doc__)
for x in('prev','version','base','outdir','zip'):p.add_argument('--'+x,required=x!='zip',default='zip' if x=='zip' else None)
p.add_argument('--drop-assets',help='file listing asset paths to remove from the package (0.9.0-dev.4: PNGs replaced by FAModels 0.3.26 .fat textures)');p.add_argument('--assets',help='assets .bamod that the gameplay package pairs with (default: the one in the previous receipt)');p.add_argument('--complete-only',action='store_true',help=argparse.SUPPRESS);p.add_argument('--game-dir',default='/home/sam/tars/work/ba-dev/replicas/codex/work/ba-tool-verification-20261102/baseline-vengeance',help='Broken Arrow folder with the pinned native missions the scenario builder reads');p.add_argument('--build',type=int,required=True);p.add_argument('--famodels',help='new Mods/FAModels.dll for the complete package only (launcher assets package unchanged)');p.add_argument('--asset',action='append',default=[],help='PKGPATH=LOCALFILE model/texture file for the complete package only');a=p.parse_args()
if a.complete_only:raise SystemExit('--complete-only is retired (Lateralus 13 Nov 2026: gameplay and assets are always available separately). A new assets version is made automatically.')
base=Path(a.base);out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);V=a.version
prev=json.loads((REL/'out/0.8'/f'FreedomArrow-{a.prev}.json').read_text());assert digest(base)==prev['complete']['sha256']
# Osama 13 Nov 12:39 ("make sure the model fixes land with your other thread"): two threads build on this branch. Stack every
# build on the newest receipt, and refuse a package that drops the dev.35-38 model/camo/data fixes (check_model_carry.py).
# 0.9 (Osama 14 Nov 2026 11:05 PST, "launch this as 0.9"): 0.9.0-dev.N builds continue in out/0.8 after 0.8.0-dev.105.
# Lateralus 19 Nov 2026: playtests are 0.9.1, 0.9.2, ...; dev builds toward them 0.9.1-dev.N. fa_version orders all of them.
sys.path.insert(0,str(Path(__file__).resolve().parent));from fa_version import PATTERN as _VP,key as _vkey
_receipts=[(m[1],f) for f in (REL/'out/0.8').glob('FreedomArrow-0.*.json') if (m:=re.fullmatch(r'FreedomArrow-('+_VP+r')\.json',f.name))]
newest=max(((_vkey(v),v) for v,f in _receipts))
assert a.prev==newest[1],f'--prev {a.prev} is not the newest build {newest[1]}; build on it so other threads\' fixes are kept'
# Osama 14 Nov 2026 15:39 PST ("make sure dev builds we aren't skipping"): the #build-install dev-build post fell behind from 0.8.0-dev.82
# to 0.9.0-dev.2. The next build may start only after the previous one is on that post (work/build-install/devpost.py).
_st=json.loads(Path('/home/sam/tars/work/ba-dev/replicas/codex/work/build-install/state.json').read_text()).get('dev_build',{}).get('version')
if _st!=a.prev and not os.environ.get('BA_DEVPOST_SKIP'):raise SystemExit(f'The #build-install dev-build post shows {_st}, not {a.prev}. Upload {a.prev} (gameplay, assets, complete) and run work/build-install/devpost.py first, or set BA_DEVPOST_SKIP=<reason>.')
complete,gameplay=out/f'FreedomArrow-{V}-complete.bamod',out/f'FreedomArrow-{V}.bamod'
with zipfile.ZipFile(base) as z:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['label']=='Freedom Arrow '+a.prev
    core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
    dll=override['Mods/FreedomArrow.Runtime.dll'];assert [dll[m.end():m.end()+m.group(1)[0]].decode() for m in re.finditer(rb'\x0dFreedom Arrow(.)',dll)]==[V]
    for f in (SRC/'UserData/FreedomArrow/constants').glob('*.json'):
        k=f.relative_to(SRC).as_posix()
        if f.read_bytes()!=z.read(k):override[k]=f.read_bytes()
    for name in ['channel.json','pla-build.json','pla-spec-assignments.json',f'pla-{V}.json']:k='UserData/FreedomArrow/'+name;override[k]=(SRC/k).read_bytes()
    # nlos.json: NLOS trait list (0.8.0-dev.7). projectile-health.json: interceptable missile HP; spaag-weapons.json: SPAAG card DPS and burst refill (Lateralus missile-hp tests, 15 Nov 2026). dazzler.json: ZTZ-99A laser dazzler (Osama 16 Nov 2026). mirror-skins.json + FA_F22_MIRROR_*.png: F-22 mirror-finish option (Osama 16 Nov 2026, MirrorSkin.cs).
    # compatibility.json: game build pins (BA 1.2.2.1 port, 16 Nov 2026: dev.19 shipped the old GameAssembly pin because this file was carried from the base).
    # game-config.json: from 0.9.0-dev.36 it carries StressRecoveryMultiplier (Lateralus 17 Nov 2026); before, it was taken from the base package.
    for k in ('UserData/FreedomArrow/game-config.json','UserData/FreedomArrow/nlos.json','UserData/FreedomArrow/projectile-health.json','UserData/FreedomArrow/spaag-weapons.json','UserData/FreedomArrow/dazzler.json','UserData/FreedomArrow/compatibility.json','UserData/FreedomArrow/plane-refund.json','UserData/FreedomArrow/sead-overkill.json','UserData/FreedomArrow/helicopter-range.json','UserData/FreedomArrow/mirror-skins.json','UserData/FreedomArrow/FA_F22_MIRROR_ALBEDO.png','UserData/FreedomArrow/FA_F22_MIRROR_MASK.png','UserData/FreedomArrow/FA_F22_MIRROR_LITMASK.png'):
        if (SRC/k).exists() and (k not in z.namelist() or (SRC/k).read_bytes()!=z.read(k)):override[k]=(SRC/k).read_bytes()
    # China voice lines (Osama 16 Nov 2026 19:56 PST, dev.34): tools/china-voice/stage.py writes ChinaVoice/ and china-voices.json; ChinaVoice.cs plays them.
    # dev.35 warning sounds (AlertSounds.cs): nuclear announcements by faction, C-RAM ballistic alarm, Burke aircraft alarm.
    # Loading screens (Osama 18 Nov 2026, LoadingScreens.cs): UserData/FreedomArrow/loading/*.png replace every vanilla loading picture.
    for f in sorted([*(SRC/'UserData/FreedomArrow/loading').glob('*.png'),*(SRC/'UserData/FreedomArrow/menu-art').glob('*.png'),SRC/'UserData/FreedomArrow/menu-art/menu-art.json',SRC/'UserData/FreedomArrow/china-voices.json',*(SRC/'UserData/FreedomArrow/ChinaVoice').rglob('*.mp3'),*(SRC/'UserData/FreedomArrow/audio').glob('*.mp3'),*(SRC/'UserData/FreedomArrow/audio').glob('*.ogg')]):
        k=f.relative_to(SRC).as_posix()
        if f.is_file() and (k not in z.namelist() or f.read_bytes()!=z.read(k)):override[k]=f.read_bytes()
    # Lateralus 13 Nov 2026: maps live in releases/0.8/scenarios (moved from the frozen 0.7 branch) and their zone values in
    # releases/0.8/source/UserData/FAConquestPrototype/settings.json. Rebuild every scenario from source on each build.
    with tempfile.TemporaryDirectory() as built_dir:
        subprocess.run([sys.executable,str(ROOT/'releases/0.8/scenarios/make_scenario.py'),'--game-dir',a.game_dir,'--out',built_dir],check=True)
        built={'UserData/FreedomArrow/scenarios/'+f.relative_to(built_dir).as_posix():f.read_bytes() for f in Path(built_dir).rglob('*') if f.is_file()}
    for k,b in built.items():
        if k not in z.namelist() or z.read(k)!=b:override[k]=b
    # Lateralus 20 Nov 2026: New / Updated tags on the Create a lobby map cards, against the current playtest release (map_labels.py, MapLabels.cs).
    if _vkey(V)>=_vkey('0.9.2-dev.8'):
        import map_labels;_since,_labels=map_labels.labels(V,built);k='UserData/FreedomArrow/map-labels.json'
        if k not in z.namelist() or z.read(k)!=_labels:override[k]=_labels
        print(f'map labels against {_since}:',json.loads(_labels)['maps'])
    retired_scenarios=[n for n in z.namelist() if n.startswith('UserData/FreedomArrow/scenarios/') and not n.endswith('/') and n not in built]
    # 0.9.0-dev.43 (Osama 18 Nov: Delta loading screen 'third hand'): the loading folder is exact, so a replaced picture leaves the package.
    retired_scenarios+=[n for n in z.namelist() if n.startswith('UserData/FreedomArrow/loading/') and not n.endswith('/') and not (SRC/n).is_file()]
    conquest=ROOT/'releases/0.8/source/UserData/FAConquestPrototype'
    settings=(conquest/'settings.json').read_bytes();compat=json.loads((conquest/'compatibility.json').read_text())
    compat['UserData/FAConquestPrototype/settings.json']=sha(settings);compat=enc(compat)
    for k,b in (('UserData/FAConquestPrototype/settings.json',settings),('UserData/FAConquestPrototype/compatibility.json',compat)):
        if z.read(k)!=b:override[k]=b
    # Lateralus 19 Nov 2026 (thread 1572724406642286692, "queue it"; asked 18 Nov: "rename any .dll our mod uses to include FA, e.g.
    # FAArrowQueue.dll"): from 0.9.1-dev.2 the five third-party DLLs ship as FA + their old name. MelonLoader loads a mod whatever its file
    # name; assembly names, MelonPreferences and UserData/ArrowQueue.cfg do not change. The launcher's update removes files the new package
    # no longer has (BAModManager ModService.RemovePackageFiles), so the old copies go. ThirdPartyGuard keeps FATeamVoice/FAHudQuick cosmetic.
    if _vkey(V)>=_vkey('0.9.1-dev.2'):
        for old,new in RENAMED_DLLS.items():
            if old in z.namelist():
                assert new not in z.namelist() and new not in override,new
                override[new]=z.read(old);retired_scenarios.append(old)
                if old in core['sha256']:core['sha256'][new]=H(override[new])
                whole['core_paths']=[new if x==old else x for x in whole['core_paths']]
            else:assert new in z.namelist(),('neither name in the base package',old)
    assert json.loads(override['mod.json'])['version']==V and json.loads(override['UserData/FreedomArrow/channel.json'])['package_version']==V
    assert not any(n.startswith(ASSET) for n in override),'models/music must not change'
    if a.famodels:override['Mods/FAModels.dll']=Path(a.famodels).read_bytes()   # complete package only; gameplay package drops asset paths
    for spec in a.asset:
        k,f=spec.split('=',1);assert k.startswith(('UserData/FAModels/','UserData/FAMusic/','Mods/FAMusic.dll')),k;override[k]=Path(f)
    drops=sorted({l.strip() for l in Path(a.drop_assets).read_text().splitlines() if l.strip()}) if a.drop_assets else []
    assert all(n.startswith('UserData/FAModels/') and n in z.namelist() and n not in override for n in drops),'--drop-assets: FAModels files of the base package only'
    if a.famodels or a.asset or drops:
        fa=json.loads(z.read('UserData/FAAssets/manifest.json'))
        for k in override:
            if k.startswith(ASSET) and k!='UserData/FAAssets/manifest.json':fa['files'][k]=H(override[k])
        for n in drops:fa['files'].pop(n,None)
        override['UserData/FAAssets/manifest.json']=enc(fa)
    core['version']=V
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=H(b)
    # Drop retired maps before the manifest is written: 0.8.0-dev.98-lat.1 pinned the deleted 0.1 map files, so the
    # runtime's payload check failed ("verification failed") on every install.
    for n in retired_scenarios+drops:core['sha256'].pop(n,None);whole['sha256'].pop(n,None)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=a.build,label='Freedom Arrow '+V)
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=H(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    # The runtime refuses the payload unless this set is exactly 257 files plus 0 or 58 battle copies (Runtime.cs;
    # 0.9.0-dev.13 first failed in game with 315). Keep this in step with that check.
    inf=[n for n in whole['sha256'] if n in ('Mods/FAModels.dll','UserData/FAModels/infantry-bodies.json') or n.startswith('UserData/FAModels/pla2_')]
    bc=sum(n.endswith(('_b.fat','_b_n.fat')) for n in inf)
    assert bc in (0,58) and len(inf)-bc==257,f'infantry files {len(inf)} with {bc} battle copies; the runtime expects 257 + 0 or 58'
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    subprocess.run(['cp','--reflink=auto',str(base.resolve()),str(complete.resolve())],check=True)
    if retired_scenarios:subprocess.run([a.zip,'-q','-nw','-d',str(complete.resolve()),*retired_scenarios],check=True)
    if drops:
        with tempfile.NamedTemporaryFile('w',delete=False) as dl:dl.write('\n'.join(drops)+'\n')
        subprocess.run(f'{a.zip} -q -nw -d {complete.resolve()} -@ < {dl.name}',shell=True,check=True)   # -nw: map names contain [ ], which zip reads as wildcards
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():
            f=stage/n;f.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(b,Path):os.link(b,f) if os.stat(b).st_dev==os.stat(stage).st_dev else f.write_bytes(b.read_bytes())
            else:f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(complete.resolve()),*sorted(override)],cwd=stage,check=True)
override_assets={n for n in override if n.startswith(ASSET)}
with zipfile.ZipFile(complete) as c:names=c.namelist()
asset_names=[n for n in names if n.startswith(ASSET)]
subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(gameplay.resolve())],check=True)
with tempfile.NamedTemporaryFile('w',delete=False) as lst:lst.write('\n'.join(asset_names)+'\n');lp=lst.name
subprocess.run(f'{a.zip} -q -nw -d {gameplay.resolve()} -@ < {lp}',shell=True,check=True)
with zipfile.ZipFile(complete) as c,zipfile.ZipFile(gameplay) as gz,zipfile.ZipFile(base) as bz:
    for n,pin in whole['sha256'].items():assert sha(c.read(n))==pin,n
    # The runtime checks these core pins at start; every one must be in the package with its hash.
    for n,pin in json.loads(c.read('UserData/FreedomArrow/payload-manifest.json'))['sha256'].items():assert n in names and sha(c.read(n))==pin,('core pin',n)
    for n in [x for x in asset_names if x in bz.namelist()]:assert c.getinfo(n).CRC==bz.getinfo(n).CRC or n in override_assets,n
    assert set(gz.namelist())==set(names)-set(asset_names)
    for n in gz.namelist():assert gz.getinfo(n).CRC==c.getinfo(n).CRC,n
    assert not [n for n in drops if n in names],'a dropped asset is still in the package'
    assert json.loads(gz.read('mod.json'))['version']==V
    if _vkey(V)>=_vkey('0.9.1-dev.2'):assert not set(RENAMED_DLLS)&set(names) and set(RENAMED_DLLS.values())<=set(gz.namelist()),'old DLL names left or FA names missing'
# Lateralus 13 Nov 2026: dev.18-20 changed FAModels.dll and ZSL-92 textures in the complete package only, but the receipt
# kept saying assets 0.2.0, so "gameplay + assets 0.2.0" failed the runtime's hash check. Check the real assets package.
vt=lambda v:tuple(int(x) for x in v.split('.'))
paired=Path(a.assets or prev['assets'].get('path') or sys.exit(f'{a.prev} receipt names no assets path; pass --assets'));assets=paired
def differ(assets):
    with zipfile.ZipFile(complete) as c,zipfile.ZipFile(assets) as az:
        amod=json.loads(az.read('mod.json'));an={i.filename:i for i in az.infolist()}
        mismatch=[n for n in asset_names if n not in an or an[n].CRC!=c.getinfo(n).CRC or an[n].file_size!=c.getinfo(n).file_size]
        mismatch+=[n for n,pin in whole['sha256'].items() if n.startswith(ASSET) and n not in mismatch and (n not in an or sha(az.read(n))!=pin)]
        mismatch=[n for n in mismatch if n!='UserData/FAAssets/manifest.json' or json.loads(az.read(n))['files']!=json.loads(c.read(n))['files']]
    return amod['version'],mismatch
AV,mismatch=differ(assets)
assert vt(AV)>=vt(prev['assets_version']),f'--assets {AV} is older than {prev["assets_version"]} of {a.prev}'
made=None
if mismatch:
    known=[json.loads(f.read_text()).get('assets_version','0.0.0') for v,f in _receipts]
    x=max([AV,*known],key=vt).split('.');NV='.'.join(x[:-1]+[str(int(x[-1])+1)])
    print(f'Model files differ from assets {AV} ({len(mismatch)}: {mismatch[:5]}). Making assets {NV}.',flush=True)
    assets=out/f'FreedomArrow-Assets-{NV}.bamod';made=make_assets.build(complete,paired,NV,V,assets,a.zip)
    AV,left=differ(assets);assert AV==NV and not left,left[:10]
# The gameplay description names the assets version it needs (Mod Manager shows it). Keep it true.
m=json.loads(override['mod.json']);need=f'Needs Freedom Arrow — Models and Music {AV}.'
d=re.sub(r'Needs Freedom Arrow — Models and Music [0-9.]+\.',need,m['description']);d=d if need in d else d+' '+need
if d!=m['description']:
    m['description']=d;(REL/'mod.json').write_bytes(enc(m))
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp)/'mod.json').write_bytes(enc(m))
        for pkg in (complete,gameplay):subprocess.run([a.zip,'-q','-nw',str(pkg.resolve()),'mod.json'],cwd=tmp,check=True)
with zipfile.ZipFile(complete) as c,zipfile.ZipFile(gameplay) as gz:assert c.read('mod.json')==gz.read('mod.json')==enc(m)
receipt={'version':V,'build':a.build,'previous':a.prev,'assets_version':AV,
 'assets':{'file':assets.name,'path':str(assets.resolve()),'sha256':digest(assets),'size':assets.stat().st_size,'files':len(zipfile.ZipFile(assets).namelist()),'new_in_this_build':made is not None},
 'assets_compatible':True,
 'complete':{'file':complete.name,'sha256':digest(complete),'size':complete.stat().st_size,'files':len(names)},
 'gameplay':{'file':gameplay.name,'sha256':digest(gameplay),'size':gameplay.stat().st_size,'files':len(set(names)-set(asset_names))},
 'changed_paths':sorted(override),'native_verified':False}
(out/f'FreedomArrow-{V}.json').write_bytes(enc(receipt));(ROOT/f'tools/pla-specs/{V}-package-checks.json').write_bytes(enc(receipt))
print(json.dumps({k:v for k,v in receipt.items() if k!='changed_paths'},indent=2))
carry=ROOT.parent/'pla-audit-20261112/check_model_carry.py'
if carry.exists():subprocess.run([sys.executable,str(carry),str(complete)],check=True)   # dev.35-38 fixes still present
# dev.93 (Osama 13 Nov 22:58): no armory-vs-multiplayer equipment fault that vanilla does not have (lost default abilities,
# unlinked option abilities, child turrets without parents, weapons without ammo, option ids above 32767).
subprocess.run([sys.executable,str(Path(__file__).parent/'audit_mp_equipment.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.0-dev.3 (12the12 bug report, Osama 14 Nov 14:58): a loadout swap row costs base + option, or the Arsenal overview and editor disagree.
# 0.9.0-dev.4 (Osama 14 Nov 16:28): every battle model at most 60,000 triangles.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_battle_tris.py'),str(complete)],check=True)
# 0.9.0-dev.7: a mount may not carry more weapons than its body slot holds in vanilla (QN-506 stall, J-20 freeze).
subprocess.run([sys.executable,str(Path(__file__).parent/'check_slot_weapons.py'),str(complete),str(a.vanilla) if getattr(a,'vanilla',None) else '/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.0-dev.5 (Osama's PC 14 Nov 18:56 PST: dev.4 refused its constants, "Field type mismatch OriginalName"): the runtime's field-type
# rule runs at build time, so a package the game would refuse can't be built.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_field_types.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True,env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
subprocess.run([sys.executable,str(Path(__file__).parent/'audit_swap_prices.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
subprocess.run([sys.executable,str(Path(__file__).parent/'check_mount_weapons.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.2-dev.1 (Osama 19 Nov 2026, QQ bug FA-003): every infantry squad has 5 HP per soldier, like vanilla.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_squad_hp.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.2-dev.2 (Osama 19 Nov 2026): China airborne/marine/engineer/SF cards keep at least their vanilla counterparts' armour.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_infantry_armor.py'),str(complete),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# Lateralus 16 Nov 2026: the dev.13 SPAAG/SAM data never reached a package; fail if queued changes are missing (lateralus/queued_checks.py).
subprocess.run([sys.executable,str(Path(__file__).parent/'lateralus/queued_checks.py'),str(complete),V,'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
