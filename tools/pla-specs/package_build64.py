"""Package PLA TEST Build64: the latest PLA pack on top of main dev 0.7.0-dev.58.

Starts from the exact latest PLA package (all models, music and China files) and replaces the
gameplay layer: merged constants and option migration (merge_dev58.py), the 0.7 runtime with the
China UI (built from releases/0.6/source/runtime-qa), FAModels with the moved Type21 fixture ID,
and main dev's skirmish mod, conquest settings, game config, squad reload and scenarios.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
BUILD=64
enc=lambda x:(json.dumps(x,indent=2)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=argparse.ArgumentParser(description=__doc__)
for x in ('base','dev','out'):p.add_argument('--'+x,type=Path,required=True)
p.add_argument('--zip',default='zip');a=p.parse_args()
FROM_DEV=['Mods/BALocalSkirmish.dll','UserData/FreedomArrow/game-config.json','UserData/FreedomArrow/squad-reload.json','UserData/FAConquestPrototype/settings.json','UserData/FAConquestPrototype/compatibility.json']
with zipfile.ZipFile(a.base) as z,zipfile.ZipFile(a.dev) as dz:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));base_build=whole['build'];assert base_build<BUILD
    core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assets=json.loads(z.read('UserData/FAAssets/manifest.json'))
    assert json.loads(dz.read('mod.json'))['version']=='0.7.0-dev.58'
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),
              'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes(),
              'Mods/FAModels.dll':(REL/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes()}
    dll=override['Mods/FreedomArrow.Runtime.dll'];compiled=[dll[m.end():m.end()+m.group(1)[0]].decode() for m in re.finditer(rb'\x08PLA TEST(.)',dll)]
    assert compiled==[str(BUILD)],('runtime DLL must be rebuilt with MelonInfo version',BUILD,compiled)
    assert b'PlayableBorders' in dll and b'ChinaUi' in dll and b'NuclearLaunchWarning' in dll,'runtime must be 0.7 plus China'
    for f in (SRC/'UserData/FreedomArrow/constants').glob('*.json'):override[f.relative_to(SRC).as_posix()]=f.read_bytes()
    for n in ['UserData/FreedomArrow/option-id-migration.json','UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json',
              'UserData/FreedomArrow/pla-spec-assignments.json','UserData/FreedomArrow/channel.json','UserData/FreedomArrow/pla-build.json',
              f'UserData/FreedomArrow/pla-build{BUILD}.json']:override[n]=(SRC/n).read_bytes()
    for n in FROM_DEV:override[n]=dz.read(n)
    dev_scen=[n for n in dz.namelist() if n.startswith('UserData/FreedomArrow/scenarios/')]
    for n in dev_scen:override[n]=dz.read(n)
    removed=[n for n in z.namelist() if n.startswith('UserData/FreedomArrow/scenarios/') and n not in dev_scen]
    # manifests
    for n in removed:
        for m in (core['sha256'],whole['sha256'],assets['files']):m.pop(n,None)
    assets['version']=f'PLA TEST Build {BUILD}'
    for n,b in override.items():
        if n in assets['files'] or n.startswith('UserData/FAModels/'):assets['files'][n]=sha(b)
    override['UserData/FAAssets/manifest.json']=enc(assets)
    core['version']=str(BUILD)
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/') or n in FROM_DEV:core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=BUILD,label=f'PLA TEST Build {BUILD}')
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted((set(whole['core_paths'])-set(removed))|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
    if removed:subprocess.run([a.zip,'-q','-nw','-d',str(a.out.resolve()),*removed],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z,zipfile.ZipFile(a.base) as base,zipfile.ZipFile(a.dev) as dz:
    names=z.namelist();assert len(names)==len(set(names))
    assert not any(n in names for n in removed)
    for n,pin in whole['sha256'].items():
        with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pin,n
    for n,pin in core['sha256'].items():assert sha(z.read(n))==pin,n
    for n,pin in assets['files'].items():
        if n in names:assert sha(z.read(n))==pin,n
    unchanged=[]
    for n in base.namelist():
        if n not in override and n not in removed:
            assert z.getinfo(n).CRC==base.getinfo(n).CRC,n;unchanged.append(n)
    for n in ['Mods/ArrowQueue.dll','Mods/FlatIncomeMod.dll','Mods/HudQuick.dll','Mods/TeamVoice.dll']:assert z.read(n)==dz.read(n),n
    assert z.read('Mods/FAMusic.dll')==base.read('Mods/FAMusic.dll')
    for n in FROM_DEV+dev_scen:assert z.read(n)==dz.read(n),n
    assert json.loads(z.read('mod.json'))['version']==str(BUILD)
receipt={'build':BUILD,'label':f'PLA TEST Build {BUILD}','base_build':base_build,'base_sha256':digest(a.base),'dev':'0.7.0-dev.58','dev_sha256':digest(a.dev),
         'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'verified_core_hashes':len(core['sha256']),
         'unchanged_archive_entries':len(unchanged),'changed_paths':sorted(override),'removed_paths':removed,'native_verified':False,'installed':False}
a.out.with_suffix('.json').write_bytes(enc(receipt));(ROOT/f'tools/pla-specs/build{BUILD}-package-checks.json').write_bytes(enc(receipt))
print(json.dumps({k:v for k,v in receipt.items() if k!='changed_paths'},indent=2))
