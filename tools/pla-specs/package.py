"""Package the next Freedom Arrow 0.8/0.9 gameplay version over the exact previous complete package.

Usage: package.py --prev VERSION --version VERSION --build N --base PREV_GAMEPLAY_OR_COMPLETE --outdir DIR [--assets ASSETS.bamod].
Changed constants, identity files and the version receipt go in.
Lateralus 24 Nov 2026 21:4x ("I don't think we need the complete file anymore right?", "yes ok get rid of it"): a gameplay build
(no --famodels / --asset / --drop-assets) starts from the previous GAMEPLAY package and writes only the gameplay package; the models
and music stay in the previous assets package, and the checks read GAMEPLAY+ASSETS (pkgview.py). Only a model build still makes the
complete package (from the previous complete, or from previous gameplay + assets when no complete exists) and the next assets version. The gameplay package pairs with the assets package of the previous build's receipt (or --assets).
Lateralus 13 Nov 2026: gameplay and assets are ALWAYS available separately. When the complete package's model files differ
from that assets package, this script makes the next assets version (make_assets.py) and the receipt names it; publish it
with the gameplay package.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,zipfile
sys.path.insert(0,str(Path(__file__).parent));import make_assets
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'mod';SRC=REL/'source'
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
# Lateralus 24 Nov 2026 ("in the future don't let models be re-staged while another thread is building a dev build"): 0.9.7-dev.3's first run read
# work/model-rework-096/stage while another thread rebuilt it (FileNotFoundError on a .fas). The packager holds this lock (shared) until it exits;
# every model stage.py takes it exclusively and stops while it is held. A stage that is already running is waited for.
import fcntl
_STAGE_LOCK=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/.model-stage.lock')
if _STAGE_LOCK.parent.is_dir():
    _stage_lock=_STAGE_LOCK.open('a')
    try:fcntl.flock(_stage_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    except BlockingIOError:print('A model stage is running; waiting for it to finish before packaging.',flush=True);fcntl.flock(_stage_lock,fcntl.LOCK_SH)
if a.complete_only:raise SystemExit('--complete-only is retired (Lateralus 13 Nov 2026: gameplay and assets are always available separately). A new assets version is made automatically.')
base=Path(a.base);out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);V=a.version
# Repo cleanup step 1 (Lateralus 22 Nov 2026, docs/development/REPO-CLEANUP-PLAN.md): out/receipts is the one record of builds. It replaced
# out/0.8 plus the receipts left in out/local-* (which let eleven different models files be called Assets 0.2.52). Every build reads and
# writes its receipt only there.
RCPT=REL/'out/receipts'
prev=json.loads((RCPT/f'FreedomArrow-{a.prev}.json').read_text());_bd=digest(base)
MODEL_BUILD=bool(a.famodels or a.asset or a.drop_assets)
if prev.get('complete') and _bd==prev['complete']['sha256']:BASE_KIND='complete'
else:assert _bd==prev['gameplay']['sha256'],f'--base is neither the {a.prev} gameplay nor its complete package';BASE_KIND='gameplay'
PREV_ASSETS=Path(a.assets or prev['assets'].get('path') or sys.exit(f'{a.prev} receipt names no assets path; pass --assets'))
if MODEL_BUILD and BASE_KIND=='gameplay':
    # A model build needs every file: rebuild the previous complete from its gameplay + assets packages (made once, deleted after the build).
    merged=out/f'.base-{a.prev}-complete.bamod'
    subprocess.run(['cp','--reflink=auto',str(PREV_ASSETS.resolve()),str(merged.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(base) as gz0:
        names0=[n for n in gz0.namelist() if not n.endswith('/')];gz0.extractall(tmp,names0)
        subprocess.run([a.zip,'-q','-nw',str(merged.resolve()),*names0],cwd=tmp,check=True)
    base=merged;BASE_KIND='complete'
GAMEPLAY_ONLY=BASE_KIND=='gameplay'
print('package mode:','gameplay only (no complete package)' if GAMEPLAY_ONLY else 'complete + gameplay (model build)',flush=True)
# Osama 13 Nov 12:39 ("make sure the model fixes land with your other thread"): two threads build on this branch. Stack every
# build on the newest receipt, and refuse a package that drops the dev.35-38 model/camo/data fixes (check_model_carry.py).
# 0.9 (Osama 14 Nov 2026 11:05 PST, "launch this as 0.9"): 0.9.0-dev.N builds continue in out/0.8 after 0.8.0-dev.105.
# Lateralus 19 Nov 2026: playtests are 0.9.1, 0.9.2, ...; dev builds toward them 0.9.1-dev.N. fa_version orders all of them.
sys.path.insert(0,str(Path(__file__).resolve().parent));from fa_version import PATTERN as _VP,key as _vkey
_receipts=[(m[1],f) for f in RCPT.glob('FreedomArrow-0.*.json') if (m:=re.fullmatch(r'FreedomArrow-('+_VP+r')\.json',f.name))]
# The record holds every line (main development, hotfixes, the model rework batch), so the base must be the newest build OLDER than
# the one being made: 0.9.5b-dev.2 builds on 0.9.5b-dev.1 even when a 0.9.6-dev.95 test build exists.
_vV=_vkey(re.match(_VP,V)[0])   # a test build such as 0.9.4-dev.1-test1 sorts as 0.9.4-dev.1
newest=max(((_vkey(v),v) for v,f in _receipts if _vkey(v)<_vV))
# 0.9.6 release (24 Nov 2026): the old 0.9.6-dev.90-97 receipts are Osama's retired 23 Nov model-rework test line (redone tonight on
# codex/development); they sort above dev.20, so the release names the reason to build on a different base: BA_PREV_REASON=<why>.
if a.prev!=newest[1] and os.environ.get('BA_PREV_REASON'):print(f'--prev {a.prev} kept over newer receipt {newest[1]}: {os.environ["BA_PREV_REASON"]}')
else: assert a.prev==newest[1],f'--prev {a.prev} is not the newest build before {V} ({newest[1]}); build on it so other threads\' fixes are kept'
# Osama 14 Nov 2026 15:39 PST ("make sure dev builds we aren't skipping"): the #build-install dev-build post fell behind from 0.8.0-dev.82
# to 0.9.0-dev.2. The next build may start only after the previous one is on that post (work/build-install/devpost.py).
_st=json.loads(Path('/home/sam/tars/work/ba-dev/replicas/codex/work/build-install/state.json').read_text()).get('dev_build',{}).get('version')
if _st!=a.prev and not os.environ.get('BA_DEVPOST_SKIP'):raise SystemExit(f'The #build-install dev-build post shows {_st}, not {a.prev}. Upload {a.prev} (gameplay, assets, complete) and run work/build-install/devpost.py first, or set BA_DEVPOST_SKIP=<reason>.')
complete,gameplay=out/f'FreedomArrow-{V}-complete.bamod',out/f'FreedomArrow-{V}.bamod'
target=gameplay if GAMEPLAY_ONLY else complete   # the package the changes are written into
with zipfile.ZipFile(base) as z:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['label']=='Freedom Arrow '+a.prev
    core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
    # preview.png (Osama 23 Nov 2026: the launcher card showed an F-22 texture): BAModManager stores a root preview.* as the pack's picture
    # (ModService, PreviewNames) and installs nothing into the game for it, so it stays out of the payload lists below.
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),'preview.png':(REL/'preview.png').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
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
    for f in sorted([*(SRC/'UserData/FreedomArrow/loading').glob('*.png'),*(SRC/'UserData/FreedomArrow/menu-art').glob('*.png'),*(SRC/'UserData/FreedomArrow/ranked').rglob('*.png'),SRC/'UserData/FreedomArrow/menu-art/menu-art.json',SRC/'UserData/FreedomArrow/china-voices.json',*(SRC/'UserData/FreedomArrow/ChinaVoice').rglob('*.mp3'),*(SRC/'UserData/FreedomArrow/audio').glob('*.mp3'),*(SRC/'UserData/FreedomArrow/audio').glob('*.ogg')]):
        k=f.relative_to(SRC).as_posix()
        if f.is_file() and (k not in z.namelist() or f.read_bytes()!=z.read(k)):override[k]=f.read_bytes()
    # Lateralus 13 Nov 2026: maps live in maps/scenarios (moved from the frozen 0.7 branch) and their zone values in
    # maps/source/UserData/FAConquestPrototype/settings.json. Rebuild every scenario from source on each build.
    with tempfile.TemporaryDirectory() as built_dir:
        subprocess.run([sys.executable,str(ROOT/'maps/scenarios/make_scenario.py'),'--game-dir',a.game_dir,'--out',built_dir],check=True)
        built={'UserData/FreedomArrow/scenarios/'+f.relative_to(built_dir).as_posix():f.read_bytes() for f in Path(built_dir).rglob('*') if f.is_file()}
    # Lateralus 23 Nov 2026 (0.9.6): the map list (exact names, IDs, size, ranked pool) from maps/maps.json, checked by make_scenario.py.
    # The game (MapSizes.cs) and the ranked hub read it instead of the [NvN] tag in the name.
    k='UserData/FreedomArrow/maps.json';built_registry=built.pop('UserData/FreedomArrow/scenarios/_maps.json',None)
    if _vkey(V)>=_vkey('0.9.6-dev.1'):
        assert built_registry,'make_scenario.py wrote no map list'
        if k not in z.namelist() or z.read(k)!=built_registry:override[k]=built_registry
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
    conquest=ROOT/'maps/source/UserData/FAConquestPrototype'
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
    # Osama 22 Nov 2026 00:4x PST ("wait until next model asset update"): the grunt-only C&C voice clips leave with the next Assets
    # version, i.e. any build that changes models (--famodels / --asset). Gameplay-only hotfixes keep the current Assets untouched.
    _gd=Path(__file__).with_name('voice-grunt-drops.txt')
    if (a.famodels or a.asset) and _gd.exists():drops=sorted(set(drops)|{l.strip() for l in _gd.read_text().splitlines() if l.strip() and l.strip() in z.namelist()})
    # Osama 24 Nov 2026 22:1x ("keep this in our storage in case we want to readd them since they're game ready, pull them away"): 1,484 model
    # files no models.json entry uses (75 old models, 1.8 GB) leave with the next Assets version, i.e. any model build. The files are kept, with
    # their former units, in work/model-archive/leftovers-20261124 (index.json). To bring one back, copy it into the stage and remove its lines here.
    _bm=Path(__file__).with_name('banned-models.txt')
    _ban=tuple('UserData/FAModels/'+l.strip() for l in _bm.read_text().splitlines() if l.strip() and not l.startswith('#')) if _bm.exists() else ()
    if _ban:
        assert not [k for k in override if k.startswith(_ban)],('banned model files (banned-models.txt) in this build',[k for k in override if k.startswith(_ban)][:5])
        if a.famodels or a.asset:drops=sorted(set(drops)|{n for n in z.namelist() if n.startswith(_ban)})
    _ld=Path(__file__).with_name('leftover-model-drops.txt')
    if (a.famodels or a.asset) and _ld.exists():
        _left={l.strip() for l in _ld.read_text().splitlines() if l.strip()}
        # The model stage passes its whole set (--asset for every file), leftovers included: the list wins over the stage.
        _gone=_left&set(override)
        for k in sorted(_gone):del override[k]
        drops=sorted(set(drops)|{n for n in _left if n in z.namelist()})
        _gone|=set(drops)
        # Guard: no unit of the new models.json may use a dropped mesh (file, battle, LODs, variants).
        _mj=override.get('UserData/FAModels/models.json') or z.read('UserData/FAModels/models.json')
        _mj=json.loads(_mj.read_bytes() if isinstance(_mj,Path) else _mj);_use=set()
        for _e in _mj.values():
            for _x in [_e,*_e.get('variants',[])]:_use|={'UserData/FAModels/'+f for f in [_x.get('file'),_x.get('battle'),*_x.get('lods',[])] if f}
        # 25 Nov 2026 15:4x: the infantry weapon and body lists name model files too. The 24 Nov list dropped w_qbb95 (QBB-95), which only
        # infantry-weapons.json uses; FAModels then rejected the whole weapon list from Assets 0.2.100 on ("infantry rules rejected", every
        # China soldier on vanilla weapon models), found in Lateralus's dev.19 / dev.21 test logs.
        for _jn,_keys in (('infantry-weapons.json',('file','battle')),('infantry-bodies.json',('file',))):
            _j=override.get('UserData/FAModels/'+_jn) or (z.read('UserData/FAModels/'+_jn) if 'UserData/FAModels/'+_jn in z.namelist() else b'[]')
            for _r in json.loads(_j.read_bytes() if isinstance(_j,Path) else _j):
                _use|={'UserData/FAModels/'+f for f in [*(_r.get(k) for k in _keys),*_r.get('lods',[])] if f}
        assert not _use&_gone,('models.json or an infantry list uses a dropped leftover model',sorted(_use&_gone)[:5])
    # Osama 25 Nov 2026 00:2x ("lets not encrypt but lets rename at least"): model files named after a seller's model number or tag get our own
    # names in every model build (model-renames.txt). The renamed files go in, the old names leave, and the names inside the .fam files
    # (int32 length + UTF-8) and the FAModels .json files are rewritten. The launcher downloads the renamed files once.
    _rn=Path(__file__).with_name('model-renames.txt')
    if (a.famodels or a.asset) and _rn.exists():
        _map=dict(l.split() for l in _rn.read_text().splitlines() if l.strip() and not l.startswith('#'))
        _pat=re.compile(r'(?<![A-Za-z0-9_])('+'|'.join(map(re.escape,sorted(_map,key=len,reverse=True)))+r')(?=[_.])')
        _rb=re.compile(_pat.pattern.encode())
        def _fam(b):
            out,i=bytearray(),0
            for m in _rb.finditer(b):
                p0=m.start();n=int.from_bytes(b[p0-4:p0],'little');s0=b[p0:p0+n]
                assert 0<n<=512 and s0.startswith(m.group(1)) and s0.isascii(),('a model name in a .fam that is not a length-prefixed string',s0[:40])
                new=_pat.sub(lambda x:_map[x.group(1)],s0.decode()).encode()
                out+=b[i:p0-4]+len(new).to_bytes(4,'little')+new;i=p0+n
            return bytes(out+b[i:])
        _tmp=Path(tempfile.mkdtemp(prefix='renamed-models-',dir=out));import atexit,shutil;atexit.register(shutil.rmtree,_tmp,True)
        _names=set(z.namelist())|set(override);_done=0
        for n in sorted(_names):
            if not n.startswith('UserData/FAModels/') or n in drops:continue
            src=override.get(n)
            b=None
            if _pat.match(n.rsplit('/',1)[1]):
                d0,b0=n.rsplit('/',1);new=d0+'/'+_pat.sub(lambda x:_map[x.group(1)],b0,count=1)
                # 0.9.7-dev.18: a later model build stages the seller-named file again while the base Assets already holds the renamed one
                # (dev.11 renamed them): the newly staged file replaces the base copy. Two staged files that map to one name still stop the build.
                assert new not in override and not (new in _names and new not in z.namelist()),('renamed model file already exists',new)
                b=(src.read_bytes() if isinstance(src,Path) else src) if src is not None else z.read(n)
                if n.endswith('.fam'):b=_fam(b)
                elif n.endswith(('.json','.txt')):b=_pat.sub(lambda x:_map[x.group(1)],b.decode()).encode()
                f=_tmp/new;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);override[new]=f;_done+=1
                if n in override:del override[n]
                if n in z.namelist():drops.append(n)
            elif n.endswith(('.json','.txt')):
                t=(src.read_bytes() if isinstance(src,Path) else src) if src is not None else z.read(n)
                if _rb.search(t):override[n]=_pat.sub(lambda x:_map[x.group(1)],t.decode()).encode()
        drops=sorted(set(drops))
        # Guard: no old name is left in a file name or inside a model or .json file, and every file models.json names is in the package.
        _final={n for n in (set(z.namelist())|set(override))-set(drops) if n.startswith('UserData/FAModels/')}
        assert not [n for n in _final if _pat.match(n.rsplit('/',1)[1])],'an old model name is still a file name'
        for n in _final:
            if n.endswith(('.fam','.json','.txt')):
                v=override.get(n);v=(v.read_bytes() if isinstance(v,Path) else v) if v is not None else z.read(n)
                assert not _rb.search(v),('an old model name is still inside',n)
        _mj=override.get('UserData/FAModels/models.json') or z.read('UserData/FAModels/models.json')
        _mj=json.loads(_mj.read_bytes() if isinstance(_mj,Path) else _mj)
        for _e in _mj.values():
            for _x in [_e,*_e.get('variants',[])]:
                for f in [_x.get('file'),_x.get('battle'),*_x.get('lods',[])]:assert not f or 'UserData/FAModels/'+f in _final,('models.json names a missing file',f)
        # FAModels rejects the whole infantry weapon list if one rule names a missing file (25 Nov 2026: w_qbb95), so check both lists too.
        for _jn,_keys in (('infantry-weapons.json',('file','battle')),('infantry-bodies.json',('file',))):
            _j=override.get('UserData/FAModels/'+_jn) or (z.read('UserData/FAModels/'+_jn) if 'UserData/FAModels/'+_jn in z.namelist() else b'[]')
            for _r in json.loads(_j.read_bytes() if isinstance(_j,Path) else _j):
                for f in [*(_r.get(k) for k in _keys),*_r.get('lods',[])]:assert not f or 'UserData/FAModels/'+f in _final,(_jn+' names a missing file',f)
        print(f'Renamed {_done} model files of {len(_map)} models (model-renames.txt).',flush=True)
    assert all(n.startswith(('UserData/FAModels/','UserData/FAMusic/Voice/')) and n in z.namelist() and n not in override for n in drops),'--drop-assets: FAModels or FAMusic voice files of the base package only'
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
        if n not in ['mod.json','README.md','preview.png']:whole['sha256'][n]=H(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    # The runtime refuses the payload unless this set is exactly 257 files plus 0 or 58 battle copies (Runtime.cs;
    # 0.9.0-dev.13 first failed in game with 315). Keep this in step with that check.
    inf=[n for n in whole['sha256'] if n in ('Mods/FAModels.dll','UserData/FAModels/infantry-bodies.json') or n.startswith('UserData/FAModels/pla2_')]
    bc=sum(n.endswith(('_b.fat','_b_n.fat')) for n in inf)
    # 0.9.5-dev.30: or 266 + 0 or 60 with the recon frog-shirt body (Osama 22 Nov "Pla recon snipers use this model").
    # 0.9.7: or 287 + 0 or 66 with the SF NVG gear atlas too (woodland + desert, 3 LODs x diffuse + normal, 2 battle copies each).
    # 0.9.7: or 290 + 0 or 66 with the no-NVG goggles-up desert body for the Medium CAB (3 meshes, existing textures; Osama 25 Nov).
    # 0.9.7: or 275 + 0 or 62 with the Fictional 1 airborne body (Osama 25 Nov "Fictional 1 soldier body no?", "please apply this model to all the PLAAF").
    assert (len(inf)-bc,bc) in ((257,0),(257,58),(266,0),(266,60),(275,0),(275,62),(287,0),(287,66),(290,0),(290,66)),f'infantry files {len(inf)} with {bc} battle copies; the runtime expects 257 + 0 or 58, 266 + 0 or 60, 275 + 0 or 62, 287 + 0 or 66, or 290 + 0 or 66'
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    subprocess.run(['cp','--reflink=auto',str(base.resolve()),str(target.resolve())],check=True)
    if retired_scenarios:subprocess.run([a.zip,'-q','-nw','-d',str(target.resolve()),*retired_scenarios],check=True)
    if drops:
        with tempfile.NamedTemporaryFile('w',delete=False) as dl:dl.write('\n'.join(drops)+'\n')
        subprocess.run(f'{a.zip} -q -nw -d {target.resolve()} -@ < {dl.name}',shell=True,check=True)   # -nw: map names contain [ ], which zip reads as wildcards
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():
            f=stage/n;f.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(b,Path):os.link(b,f) if os.stat(b).st_dev==os.stat(stage).st_dev else f.write_bytes(b.read_bytes())
            else:f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(target.resolve()),*sorted(override)],cwd=stage,check=True)
override_assets={n for n in override if n.startswith(ASSET)}
if GAMEPLAY_ONLY:
    assert not override_assets,'a gameplay build changes no model or music file'
    with zipfile.ZipFile(gameplay) as g0,zipfile.ZipFile(PREV_ASSETS) as a0:
        assert not [n for n in g0.namelist() if n.startswith(ASSET)],'model/music files in the gameplay package'
        asset_names=[n for n in a0.namelist() if n.startswith(ASSET)];names=g0.namelist()+asset_names
    # Checks below read the data and the models together: GAMEPLAY+ASSETS (pkgview.py).
    view=f'{gameplay.resolve()}+{PREV_ASSETS.resolve()}'
    with zipfile.ZipFile(gameplay) as gz,zipfile.ZipFile(base) as bz,zipfile.ZipFile(PREV_ASSETS) as az:
        pinned=lambda n:az if n.startswith(ASSET) else gz
        # UserData/FAAssets/manifest.json: the assets package carries its own copy (its version line differs); differ() ignored it the same way.
        for n,pin in whole['sha256'].items():assert n=='UserData/FAAssets/manifest.json' or sha(pinned(n).read(n))==pin,n
        for n,pin in json.loads(gz.read('UserData/FreedomArrow/payload-manifest.json'))['sha256'].items():assert sha(pinned(n).read(n))==pin,('core pin',n)
        assert set(gz.namelist())==(set(bz.namelist())-set(retired_scenarios))|set(override),'gameplay package = previous gameplay - retired + changed'
        for n in gz.namelist():assert n in override or gz.getinfo(n).CRC==bz.getinfo(n).CRC,n
        assert json.loads(gz.read('mod.json'))['version']==V
        if _vkey(V)>=_vkey('0.9.1-dev.2'):assert not set(RENAMED_DLLS)&set(gz.namelist()) and set(RENAMED_DLLS.values())<=set(gz.namelist()),'old DLL names left or FA names missing'
else:
  view=str(complete)
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
AV,mismatch=(json.loads(zipfile.ZipFile(assets).read('mod.json'))['version'],[]) if GAMEPLAY_ONLY else differ(assets)   # gameplay only: asset pins checked above
assert vt(AV)>=vt(prev['assets_version']),f'--assets {AV} is older than {prev["assets_version"]} of {a.prev}'
made=None
if mismatch:
    # Lateralus 22 Nov 2026: "two different models files should never have the same version number". 0.9.5-dev.10 to dev.34 were built with
    # --prev 0.9.4 and their receipts stayed in their own out/local-* folders, so out/0.8 alone always gave 0.2.51 + 1 and eleven different
    # files were all named 0.2.52. The next number counts every build in the one record, out/receipts (repo cleanup step 1).
    known=[json.loads(f.read_text()).get('assets_version','0.0.0') for f in RCPT.glob('FreedomArrow-0.*.json')]
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
        for pkg in ((gameplay,) if GAMEPLAY_ONLY else (complete,gameplay)):subprocess.run([a.zip,'-q','-nw',str(pkg.resolve()),'mod.json'],cwd=tmp,check=True)
for pkg in ((gameplay,) if GAMEPLAY_ONLY else (complete,gameplay)):
    with zipfile.ZipFile(pkg) as c:assert c.read('mod.json')==enc(m),pkg.name
receipt={'version':V,'build':a.build,'previous':a.prev,'assets_version':AV,
 'assets':{'file':assets.name,'path':str(assets.resolve()),'sha256':digest(assets),'size':assets.stat().st_size,'files':len(zipfile.ZipFile(assets).namelist()),'new_in_this_build':made is not None},
 'assets_compatible':True,
 'complete':None if GAMEPLAY_ONLY else {'file':complete.name,'sha256':digest(complete),'size':complete.stat().st_size,'files':len(names)},
 'gameplay':{'file':gameplay.name,'sha256':digest(gameplay),'size':gameplay.stat().st_size,'files':len(set(names)-set(asset_names))},
 'changed_paths':sorted(override),'native_verified':False}
(RCPT/f'FreedomArrow-{V}.json').write_bytes(enc(receipt));(ROOT/f'tools/pla-specs/{V}-package-checks.json').write_bytes(enc(receipt))
print(json.dumps({k:v for k,v in receipt.items() if k!='changed_paths'},indent=2))
carry=ROOT.parent/'pla-audit-20261112/check_model_carry.py'
_pp={**os.environ,'PYTHONPATH':str(Path(__file__).parent)+os.pathsep+os.environ.get('PYTHONPATH','')}   # pkgview for GAMEPLAY+ASSETS
if carry.exists():subprocess.run([sys.executable,str(carry),view],check=True,env=_pp)   # dev.35-38 fixes still present
# dev.93 (Osama 13 Nov 22:58): no armory-vs-multiplayer equipment fault that vanilla does not have (lost default abilities,
# unlinked option abilities, child turrets without parents, weapons without ammo, option ids above 32767).
subprocess.run([sys.executable,str(Path(__file__).parent/'audit_mp_equipment.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.0-dev.3 (12the12 bug report, Osama 14 Nov 14:58): a loadout swap row costs base + option, or the Arsenal overview and editor disagree.
# 0.9.0-dev.4 (Osama 14 Nov 16:28): every battle model at most 60,000 triangles.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_battle_tris.py'),view],check=True)
# 0.9.0-dev.7: a mount may not carry more weapons than its body slot holds in vanilla (QN-506 stall, J-20 freeze).
subprocess.run([sys.executable,str(Path(__file__).parent/'check_slot_weapons.py'),str(gameplay),str(a.vanilla) if getattr(a,'vanilla',None) else '/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.0-dev.5 (Osama's PC 14 Nov 18:56 PST: dev.4 refused its constants, "Field type mismatch OriginalName"): the runtime's field-type
# rule runs at build time, so a package the game would refuse can't be built.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_field_types.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True,env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
subprocess.run([sys.executable,str(Path(__file__).parent/'audit_swap_prices.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
subprocess.run([sys.executable,str(Path(__file__).parent/'check_mount_weapons.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.2-dev.1 (Osama 19 Nov 2026, QQ bug FA-003): every infantry squad has 5 HP per soldier, like vanilla.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_squad_hp.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# 0.9.2-dev.2 (Osama 19 Nov 2026): China airborne/marine/engineer/SF cards keep at least their vanilla counterparts' armour.
subprocess.run([sys.executable,str(Path(__file__).parent/'check_infantry_armor.py'),str(gameplay),'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# Lateralus 16 Nov 2026: the dev.13 SPAAG/SAM data never reached a package; fail if queued changes are missing (lateralus/queued_checks.py).
subprocess.run([sys.executable,str(Path(__file__).parent/'lateralus/queued_checks.py'),view,V,'/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla'],check=True)
# The temporary complete base of a model build made from gameplay + assets (above) is this build's own scratch.
if (_m:=out/f'.base-{a.prev}-complete.bamod').exists():_m.unlink()
