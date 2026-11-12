"""Package the exact PLA30-based roster revision, retaining all approved assets."""
from pathlib import Path
import argparse, hashlib, json, subprocess, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
BASE='809660cb5ec20c47bc24dff240badf23fa70fcb8f95160805193378ebdc5459a'
enc=lambda x:(json.dumps(x,indent=2)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',default='zip');a=p.parse_args()
assert digest(a.base)==BASE
with zipfile.ZipFile(a.base) as z:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==30
    oldpins=whole['sha256'].copy();core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assets=json.loads(z.read('UserData/FAAssets/manifest.json'))
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes(),'Mods/FAModels.dll':(REL/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes()}
    for folder in ['UserData/FreedomArrow/constants']:
        for f in (SRC/folder).glob('*.json'):
            key=f.relative_to(SRC).as_posix();data=f.read_bytes()
            if data!=z.read(key):override[key]=data
    for name in ['channel.json','pla-build.json','pla-spec-assignments.json','pla-specializations.json','pla-model-catalogue.json','pla-vehicle-armament.json','pla-infantry-designer.json','pla-roster-revision.json']:
        key='UserData/FreedomArrow/'+name;override[key]=(SRC/key).read_bytes()
    for name in ['models.json','m_j10a_grey.fam','m_j10a_grey.mat.json','m_j10a_grey_lo.fam','m_j10a_grey_lo.mat.json']:
        key='UserData/FAModels/'+name;override[key]=(SRC/key).read_bytes()
    for f in (SRC/'UserData/FreedomArrow/audio').glob('df31-nuclear-warning.*'):
        override[f.relative_to(SRC).as_posix()]=f.read_bytes()
    assets['version']='PLA TEST Build 31'
    for n,b in override.items():
        if n in assets['files'] or n.startswith('UserData/FAModels/'):assets['files'][n]=sha(b)
    override['UserData/FAAssets/manifest.json']=enc(assets)
    core['version']='31'
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=31,label='PLA TEST Build 31')
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z,zipfile.ZipFile(a.base) as base:
    assert len(z.namelist())==len(set(z.namelist()))
    for n,pin in whole['sha256'].items():
        with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pin,n
    for n,pin in core['sha256'].items():assert sha(z.read(n))==pin,n
    for n,pin in assets['files'].items():
        if n in z.namelist():assert sha(z.read(n))==pin,n
    unchanged=[]
    for n in base.namelist():
        if n not in override:
            assert z.getinfo(n).CRC==base.getinfo(n).CRC and z.getinfo(n).file_size==base.getinfo(n).file_size,n
            unchanged.append(n)
    for n in ['UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json','Mods/FAMusic.dll']:
        assert z.read(n)==base.read(n),n
    for source,alias in [('m_j10c_cg','m_j10a_grey'),('m_j10c_lo2','m_j10a_grey_lo')]:
        assert z.read('UserData/FAModels/'+alias+'.fam')==base.read('UserData/FAModels/'+source+'.fam')
    assert json.loads(z.read('mod.json'))['version']=='31'
receipt={'build':31,'label':'PLA TEST Build 31','base_build':30,'base_sha256':BASE,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'verified_core_hashes':len(core['sha256']),'unchanged_archive_entries':len(unchanged),'changed_paths':sorted(override),'new_paths':sorted(set(z.namelist())-set(base.namelist())),'approved_infantry_alignment_models_music_preserved':True,'native_verified':False,'installed':False}
a.out.with_suffix('.json').write_bytes(enc(receipt));(ROOT/'tools/pla-specs/build31-package-checks.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))
