"""Package the next Freedom Arrow 0.8 gameplay version over the exact previous complete 0.8 package.

Usage: package_0_8_next.py --prev VERSION --version VERSION --build N --base PREV_COMPLETE --outdir DIR.
Changed constants, identity files and the version receipt go in; models/music must be byte-identical, so
the launcher keeps the published assets package. Writes the complete package (Vengeance switcher) and the
launcher gameplay package.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
enc=lambda x:(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ASSET=('Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')
p=argparse.ArgumentParser(description=__doc__)
for x in('prev','version','base','outdir','zip'):p.add_argument('--'+x,required=x!='zip',default='zip' if x=='zip' else None)
p.add_argument('--build',type=int,required=True);a=p.parse_args()
base=Path(a.base);out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);V=a.version
prev=json.loads((REL/'out/0.8'/f'FreedomArrow-{a.prev}.json').read_text());assert digest(base)==prev['complete']['sha256']
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
    assert json.loads(override['mod.json'])['version']==V and json.loads(override['UserData/FreedomArrow/channel.json'])['package_version']==V
    assert not any(n.startswith(ASSET) for n in override),'models/music must not change'
    core['version']=V
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=a.build,label='Freedom Arrow '+V)
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    subprocess.run(['cp','--reflink=auto',str(base.resolve()),str(complete.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(complete.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(complete) as c:names=c.namelist()
asset_names=[n for n in names if n.startswith(ASSET)]
subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(gameplay.resolve())],check=True)
with tempfile.NamedTemporaryFile('w',delete=False) as lst:lst.write('\n'.join(asset_names)+'\n');lp=lst.name
subprocess.run(f'{a.zip} -q -nw -d {gameplay.resolve()} -@ < {lp}',shell=True,check=True)
with zipfile.ZipFile(complete) as c,zipfile.ZipFile(gameplay) as gz,zipfile.ZipFile(base) as bz:
    for n,pin in whole['sha256'].items():assert sha(c.read(n))==pin,n
    for n in asset_names:assert c.getinfo(n).CRC==bz.getinfo(n).CRC,n
    assert set(gz.namelist())==set(names)-set(asset_names)
    for n in gz.namelist():assert gz.getinfo(n).CRC==c.getinfo(n).CRC,n
    assert json.loads(gz.read('mod.json'))['version']==V
receipt={'version':V,'build':a.build,'previous':a.prev,'assets_version':prev['assets_version'],'assets':prev['assets'],
 'complete':{'file':complete.name,'sha256':digest(complete),'size':complete.stat().st_size,'files':len(names)},
 'gameplay':{'file':gameplay.name,'sha256':digest(gameplay),'size':gameplay.stat().st_size,'files':len(set(names)-set(asset_names))},
 'changed_paths':sorted(override),'native_verified':False}
(out/f'FreedomArrow-{V}.json').write_bytes(enc(receipt));(ROOT/f'tools/pla-specs/{V}-package-checks.json').write_bytes(enc(receipt))
print(json.dumps({k:v for k,v in receipt.items() if k!='changed_paths'},indent=2))
