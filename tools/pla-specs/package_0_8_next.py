"""Package the next Freedom Arrow 0.8 gameplay version over the exact previous complete 0.8 package.

Usage: package_0_8_next.py --prev VERSION --version VERSION --build N --base PREV_COMPLETE --outdir DIR [--assets ASSETS.bamod].
Changed constants, identity files and the version receipt go in. Writes the complete package (Vengeance switcher) and the
launcher gameplay package. The gameplay package pairs with the assets package of the previous build's receipt (or --assets).
Lateralus 13 Nov 2026: gameplay and assets are ALWAYS available separately. When the complete package's model files differ
from that assets package, this script makes the next assets version (make_assets.py) and the receipt names it; publish it
with the gameplay package.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,tempfile,zipfile
sys.path.insert(0,str(Path(__file__).parent));import make_assets
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
enc=lambda x:(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ASSET=('Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')
p=argparse.ArgumentParser(description=__doc__)
for x in('prev','version','base','outdir','zip'):p.add_argument('--'+x,required=x!='zip',default='zip' if x=='zip' else None)
p.add_argument('--assets',help='assets .bamod that the gameplay package pairs with (default: the one in the previous receipt)');p.add_argument('--complete-only',action='store_true',help=argparse.SUPPRESS);p.add_argument('--game-dir',default='/home/sam/tars/work/ba-dev/replicas/codex/work/ba-tool-verification-20261102/baseline-vengeance',help='Broken Arrow folder with the pinned native missions the scenario builder reads');p.add_argument('--build',type=int,required=True);p.add_argument('--famodels',help='new Mods/FAModels.dll for the complete package only (launcher assets package unchanged)');p.add_argument('--asset',action='append',default=[],help='PKGPATH=LOCALFILE model/texture file for the complete package only');a=p.parse_args()
if a.complete_only:raise SystemExit('--complete-only is retired (Lateralus 13 Nov 2026: gameplay and assets are always available separately). A new assets version is made automatically.')
base=Path(a.base);out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);V=a.version
prev=json.loads((REL/'out/0.8'/f'FreedomArrow-{a.prev}.json').read_text());assert digest(base)==prev['complete']['sha256']
# Osama 13 Nov 12:39 ("make sure the model fixes land with your other thread"): two threads build on this branch. Stack every
# build on the newest receipt, and refuse a package that drops the dev.35-38 model/camo/data fixes (check_model_carry.py).
newest=max((int(re.search(r'dev\.(\d+)\.json$',f.name).group(1)),f.name) for f in (REL/'out/0.8').glob('FreedomArrow-0.8.0-dev.*.json') if re.search(r'dev\.\d+\.json$',f.name))
assert a.prev==f'0.8.0-dev.{newest[0]}',f'--prev {a.prev} is not the newest build 0.8.0-dev.{newest[0]}; build on it so other threads\' fixes are kept'
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
    k='UserData/FreedomArrow/nlos.json'   # NLOS trait list (0.8.0-dev.7)
    if (SRC/k).exists() and (k not in z.namelist() or (SRC/k).read_bytes()!=z.read(k)):override[k]=(SRC/k).read_bytes()
    # Lateralus 13 Nov 2026: maps live in releases/0.8/scenarios (moved from the frozen 0.7 branch) and their zone values in
    # releases/0.8/source/UserData/FAConquestPrototype/settings.json. Rebuild every scenario from source on each build.
    with tempfile.TemporaryDirectory() as built_dir:
        subprocess.run([sys.executable,str(ROOT/'releases/0.8/scenarios/make_scenario.py'),'--game-dir',a.game_dir,'--out',built_dir],check=True)
        built={'UserData/FreedomArrow/scenarios/'+f.relative_to(built_dir).as_posix():f.read_bytes() for f in Path(built_dir).rglob('*') if f.is_file()}
    for k,b in built.items():
        if k not in z.namelist() or z.read(k)!=b:override[k]=b
    retired_scenarios=[n for n in z.namelist() if n.startswith('UserData/FreedomArrow/scenarios/') and not n.endswith('/') and n not in built]
    conquest=ROOT/'releases/0.8/source/UserData/FAConquestPrototype'
    settings=(conquest/'settings.json').read_bytes();compat=json.loads((conquest/'compatibility.json').read_text())
    compat['UserData/FAConquestPrototype/settings.json']=sha(settings);compat=enc(compat)
    for k,b in (('UserData/FAConquestPrototype/settings.json',settings),('UserData/FAConquestPrototype/compatibility.json',compat)):
        if z.read(k)!=b:override[k]=b
    assert json.loads(override['mod.json'])['version']==V and json.loads(override['UserData/FreedomArrow/channel.json'])['package_version']==V
    assert not any(n.startswith(ASSET) for n in override),'models/music must not change'
    if a.famodels:override['Mods/FAModels.dll']=Path(a.famodels).read_bytes()   # complete package only; gameplay package drops asset paths
    for spec in a.asset:
        k,f=spec.split('=',1);assert k.startswith(('UserData/FAModels/','UserData/FAMusic/','Mods/FAMusic.dll')),k;override[k]=Path(f).read_bytes()
    if a.famodels or a.asset:
        fa=json.loads(z.read('UserData/FAAssets/manifest.json'))
        for k in override:
            if k.startswith(ASSET) and k!='UserData/FAAssets/manifest.json':fa['files'][k]=sha(override[k])
        override['UserData/FAAssets/manifest.json']=enc(fa)
    core['version']=V
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    for n in retired_scenarios:core['sha256'].pop(n,None);whole['sha256'].pop(n,None)
    whole.update(build=a.build,label='Freedom Arrow '+V)
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    subprocess.run(['cp','--reflink=auto',str(base.resolve()),str(complete.resolve())],check=True)
    if retired_scenarios:subprocess.run([a.zip,'-q','-d',str(complete.resolve()),*retired_scenarios],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(complete.resolve()),*sorted(override)],cwd=stage,check=True)
override_assets={n for n in override if n.startswith(ASSET)}
with zipfile.ZipFile(complete) as c:names=c.namelist()
asset_names=[n for n in names if n.startswith(ASSET)]
subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(gameplay.resolve())],check=True)
with tempfile.NamedTemporaryFile('w',delete=False) as lst:lst.write('\n'.join(asset_names)+'\n');lp=lst.name
subprocess.run(f'{a.zip} -q -nw -d {gameplay.resolve()} -@ < {lp}',shell=True,check=True)
with zipfile.ZipFile(complete) as c,zipfile.ZipFile(gameplay) as gz,zipfile.ZipFile(base) as bz:
    for n,pin in whole['sha256'].items():assert sha(c.read(n))==pin,n
    for n in [x for x in asset_names if x in bz.namelist()]:assert c.getinfo(n).CRC==bz.getinfo(n).CRC or n in override_assets,n
    assert set(gz.namelist())==set(names)-set(asset_names)
    for n in gz.namelist():assert gz.getinfo(n).CRC==c.getinfo(n).CRC,n
    assert json.loads(gz.read('mod.json'))['version']==V
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
    known=[json.loads(f.read_text()).get('assets_version','0.0.0') for f in (REL/'out/0.8').glob('FreedomArrow-0.8.0-dev.*.json')]
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
