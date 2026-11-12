"""Package Freedom Arrow 0.8.0-dev.1 from the exact PLA TEST Build 68 package (Osama 12 Nov 13:27 PST).

Game content is Build 68 unchanged; only the identity changes (runtime MelonInfo, mod.json, channel,
pla-build, package manifests). Three outputs:
- FreedomArrow-0.8.0-dev.1-complete.bamod: one package for the Vengeance switcher (gameplay + models + music).
- FreedomArrow-0.8.0-dev.1.bamod: launcher gameplay package (id freedomarrow.gameplay).
- FreedomArrow-Assets-0.2.0.bamod: launcher models/music/voices package (id freedomarrow.assets.live):
  Mods/FAModels.dll, Mods/FAMusic.dll, UserData/FAModels, UserData/FAMusic, UserData/FAAssets.
Every file of the complete package is in exactly one of the two launcher packages, byte for byte.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.1';AV='0.2.0';B=69
BASE=json.loads((REL/'out/PLA-TEST-Build-68.json').read_text())['sha256']
enc=lambda x:(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ASSET=('Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')
is_asset=lambda n:n.startswith(ASSET)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--outdir',type=Path,required=True);p.add_argument('--zip',default='zip');a=p.parse_args()
assert digest(a.base)==BASE
out=a.outdir;out.mkdir(parents=True,exist_ok=True)
complete,gameplay,assetpkg=out/f'FreedomArrow-{V}-complete.bamod',out/f'FreedomArrow-{V}.bamod',out/f'FreedomArrow-Assets-{AV}.bamod'
with zipfile.ZipFile(a.base) as z:
    whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==68
    core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assets=json.loads(z.read('UserData/FAAssets/manifest.json'))
    override={'mod.json':(REL/'mod.json').read_bytes(),'README.md':(ROOT/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(SRC/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
    dll=override['Mods/FreedomArrow.Runtime.dll'];compiled=[dll[m.end():m.end()+m.group(1)[0]].decode() for m in re.finditer(rb'\x0dFreedom Arrow(.)',dll)]
    assert compiled==[V],compiled
    for f in (SRC/'UserData/FreedomArrow/constants').glob('*.json'):
        k=f.relative_to(SRC).as_posix();assert f.read_bytes()==z.read(k),('constants must equal Build68',k)
    for name in ['channel.json','pla-build.json','pla-build69.json']:k='UserData/FreedomArrow/'+name;override[k]=(SRC/k).read_bytes()
    assert json.loads(override['mod.json'])['version']==V and json.loads(override['UserData/FreedomArrow/channel.json'])['package_version']==V
    assets.update(version=AV,id='freedomarrow.assets.live');assets['notes']=[f'Freedom Arrow 0.8 models, music and voices for gameplay {V}: China (PLA) models and infantry, live RU/US models (Abrams X, B-21, X-47B, Su-57D, Su-75, Karatel, XM30, Su-47, F-14/F-21, YF-23, LOSAT, Black Eagle), FA music player and packs.']
    override['UserData/FAAssets/manifest.json']=enc(assets)
    core['version']=V
    for n,b in override.items():
        if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
    override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
    whole.update(build=B,label='Freedom Arrow '+V)
    for n,b in override.items():
        if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
    whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
    override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
    names=z.namelist()
    subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(complete.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)
        for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([a.zip,'-q','-nw',str(complete.resolve()),*sorted(override)],cwd=stage,check=True)
    # launcher split: gameplay = complete minus asset paths; assets = asset paths + its own mod.json/README
    with zipfile.ZipFile(complete) as cz:names=cz.namelist()   # includes files new in 0.8 (pla-build69.json)
    asset_names=[n for n in names if is_asset(n)]
    subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(gameplay.resolve())],check=True)
    with tempfile.NamedTemporaryFile('w',delete=False) as lst:lst.write('\n'.join(asset_names)+'\n');lp=lst.name
    subprocess.run(f'{a.zip} -q -nw -d {gameplay.resolve()} -@ < {lp}',shell=True,check=True)
    subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(assetpkg.resolve())],check=True)
    drop=[n for n in names if not is_asset(n) and n not in('mod.json','README.md')]
    with open(lp,'w') as f:f.write('\n'.join(drop)+'\n')
    subprocess.run(f'{a.zip} -q -nw -d {assetpkg.resolve()} -@ < {lp}',shell=True,check=True)
    amod={'id':'freedomarrow.assets.live','name':'Freedom Arrow — Models and Music','version':AV,'type':'mod','description':f'Freedom Arrow 0.8 models (China/PLA and live RU/US), music and voices. Needs gameplay {V}.'}
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp);(stage/'mod.json').write_bytes(enc(amod))
        (stage/'README.md').write_text(f'# Freedom Arrow — Models and Music {AV}\n\nModels, music and voices for Freedom Arrow {V}: China (PLA) vehicles, aircraft, helicopters and infantry; the live RU/US custom models; the FA music player and its packs. Install with the gameplay package through the launcher.\n')
        subprocess.run([a.zip,'-q','-nw',str(assetpkg.resolve()),'mod.json','README.md'],cwd=stage,check=True)
# verification
with zipfile.ZipFile(complete) as c,zipfile.ZipFile(gameplay) as gz,zipfile.ZipFile(assetpkg) as az:
    cn,gn,an=set(c.namelist()),set(gz.namelist()),set(az.namelist())
    assert len(cn)==len(c.namelist()) and len(gn)==len(gz.namelist()) and len(an)==len(az.namelist())
    for n,pin in whole['sha256'].items():assert sha(c.read(n))==pin,n
    for n,pin in core['sha256'].items():assert sha(c.read(n))==pin,n
    assert gn==cn-set(asset_names) and an==set(asset_names)|{'mod.json','README.md'}
    for n in gn:assert gz.getinfo(n).CRC==c.getinfo(n).CRC,n
    for n in asset_names:assert az.getinfo(n).CRC==c.getinfo(n).CRC,n
    assert json.loads(gz.read('mod.json'))['id']=='freedomarrow.gameplay' and json.loads(gz.read('mod.json'))['version']==V
    assert json.loads(az.read('mod.json'))=={'id':'freedomarrow.assets.live','name':'Freedom Arrow — Models and Music','version':AV,'type':'mod','description':amod['description']}
    infantry=[n for n in whole['sha256'] if n=='Mods/FAModels.dll' or n=='UserData/FAModels/infantry-bodies.json' or n.startswith('UserData/FAModels/pla2_')]
    assert len(infantry)==227 and all(n in an for n in infantry),'runtime infantry check needs these in the assets package'
receipt={'version':V,'assets_version':AV,'build':B,'content_build':68,'base_sha256':BASE,
 'complete':{'file':complete.name,'sha256':digest(complete),'size':complete.stat().st_size,'files':len(cn)},
 'gameplay':{'file':gameplay.name,'sha256':digest(gameplay),'size':gameplay.stat().st_size,'files':len(gn)},
 'assets':{'file':assetpkg.name,'sha256':digest(assetpkg),'size':assetpkg.stat().st_size,'files':len(an)},
 'verified_payloads':len(whole['sha256']),'core_hashes':len(core['sha256']),'native_verified':False}
(out/f'FreedomArrow-{V}.json').write_bytes(enc(receipt));(ROOT/'tools/pla-specs/0.8.0-dev.1-package-checks.json').write_bytes(enc(receipt))
print(json.dumps(receipt,indent=2))
