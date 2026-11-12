"""Package the exact PLA65-based Build66: Osama 13:03 batch plus the live model set.

Models: live assets 0.1.14 versions of the RU/US model files PLA carried older copies of, the LOSAT
model, the dev.51 Black Eagle model, and the live models.json entries for Object 640 Black Eagle,
MGM-166 LOSAT (scale 1.2) and F-21 Super Tomcat (scale 1.1). ZTQ-62-I gets normal and mask maps.
PLA's own models, music and FAMusic/FAModels DLLs are unchanged.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
B=66;BASE=json.loads((REL/f'out/PLA-TEST-Build-{B-1}.json').read_text())['sha256']
enc=lambda x:(json.dumps(x,indent=2)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',default='zip');p.add_argument('--assets',type=Path,required=True);p.add_argument('--live-models',type=Path,required=True);p.add_argument('--blackeagle',type=Path,required=True);p.add_argument('--ztq62i',type=Path,required=True);a=p.parse_args()
assert digest(a.base)==BASE
with zipfile.ZipFile(a.base) as z:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==B-1
    core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assets=json.loads(z.read('UserData/FAAssets/manifest.json'))
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
    dll=override['Mods/FreedomArrow.Runtime.dll'];compiled=[dll[m.end():m.end()+m.group(1)[0]].decode() for m in re.finditer(rb'\x08PLA TEST(.)',dll)]
    assert compiled==[str(B)],('runtime DLL must be rebuilt with MelonInfo version',B,compiled)
    assert b'PlayableBorders' in dll and b'ChinaUi' in dll,'runtime must stay 0.7 plus China'
    for f in (SRC/'UserData/FreedomArrow/constants').glob('*.json'):
        key=f.relative_to(SRC).as_posix();data=f.read_bytes()
        if data!=z.read(key):override[key]=data
    for name in ['channel.json','pla-build.json','pla-spec-assignments.json',f'pla-build{B}.json']:
        key='UserData/FreedomArrow/'+name;override[key]=(SRC/key).read_bytes()
    D='UserData/FAModels/';live=json.loads(a.live_models.read_text());pm=json.loads(z.read(D+'models.json'))
    with zipfile.ZipFile(a.assets) as az:
        assert json.loads(az.read('mod.json'))['version']=='0.1.14'
        for n in az.namelist():
            if n.startswith(D+'m_') and (n not in z.namelist() or az.read(n)!=z.read(n)):override[n]=az.read(n)
    for f in sorted(a.blackeagle.glob('m_blackeagle_*')):override[D+f.name]=f.read_bytes()
    for f in sorted(a.ztq62i.glob('m_ztq62i_*')):override[D+f.name]=f.read_bytes()
    for name in ['Object 640 Black Eagle','MGM-166 LOSAT','F-21 Super Tomcat']:pm[name]=live[name]
    override[D+'models.json']=(json.dumps(pm,indent=2)+'\n').encode()
    for name,e in pm.items():
        for k in ('file','battle'):
            if e.get(k):assert D+e[k] in override or D+e[k] in z.namelist(),(name,e[k])
    for n,b in override.items():
        if n.startswith(D):assets['files'][n]=sha(b)
    for name in ['Object 640 Black Eagle','MGM-166 LOSAT','F-21 Super Tomcat']:assets.setdefault('models',{})[name]=pm[name]
    assets['version']=f'PLA TEST Build {B}'
    override['UserData/FAAssets/manifest.json']=enc(assets)
    core['version']=str(B)
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=B,label=f'PLA TEST Build {B}')
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z,zipfile.ZipFile(a.base) as base:
    assert len(z.namelist())==len(set(z.namelist()))
    for n,pin in whole['sha256'].items():
        with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pin,n
    for n,pin in core['sha256'].items():assert sha(z.read(n))==pin,n
    unchanged=[]
    for n in base.namelist():
        if n not in override:assert z.getinfo(n).CRC==base.getinfo(n).CRC,n;unchanged.append(n)
    assert not any(n.startswith(('UserData/FAMusic/','Mods/FA')) for n in override),'music and model loader untouched'
    for n in override:
        if n.startswith('UserData/FAModels/m_'):assert any(k in n for k in ('m_blackeagle_','m_ztq62i_','m_losat','m_su57d','m_f14','m_su47','m_su75','m_yf23')),('unexpected model file',n)
    assert json.loads(z.read('mod.json'))['version']==str(B)
receipt={'build':B,'label':f'PLA TEST Build {B}','base_build':B-1,'base_sha256':BASE,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'verified_core_hashes':len(core['sha256']),'unchanged_archive_entries':len(unchanged),'changed_paths':sorted(override),'native_verified':False,'installed':False}
a.out.with_suffix('.json').write_bytes(enc(receipt));(ROOT/f'tools/pla-specs/build{B}-package-checks.json').write_bytes(enc(receipt));print(json.dumps({k:v for k,v in receipt.items() if k!='changed_paths'},indent=2))
