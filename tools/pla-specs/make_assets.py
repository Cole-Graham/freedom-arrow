"""Make the Freedom Arrow assets package (models, music, voices) from a complete 0.8 package.

Usage: make_assets.py --complete COMPLETE.bamod --prev PREV_ASSETS.bamod --version 0.2.N --gameplay 0.8.0-dev.N --out OUT.bamod
Lateralus 13 Nov 2026: gameplay and assets are ALWAYS published separately. The assets package holds exactly the asset
paths of the complete package, so "gameplay + assets" installs the same files as the complete package. Only mod.json,
README.md and the version in UserData/FAAssets/manifest.json differ; the runtime does not pin those three."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile
ASSET=('Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')
MAN='UserData/FAAssets/manifest.json'
enc=lambda x:(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def build(complete,prev,V,GV,out,zip='zip'):
    complete,prev,out=Path(complete),Path(prev),Path(out)
    with zipfile.ZipFile(complete) as c,zipfile.ZipFile(prev) as p:
        names=c.namelist();crc={i.filename:i.CRC for i in c.infolist()};man=json.loads(c.read(MAN))
        mod=json.loads(p.read('mod.json'));old={i.filename:i.CRC for i in p.infolist()}
    assets=[n for n in names if n.startswith(ASSET)]
    new=[n for n in assets if n not in old and not n.endswith('/')]
    changed=[n for n in assets if n in old and n!=MAN and old[n]!=crc[n]]
    PV=mod['version']
    mod.update(version=V,description=f'Freedom Arrow 0.8 models (China/PLA and live RU/US), music and voices. Made from gameplay {GV}; '
               f'a gameplay build names the assets version it needs. Assets {PV} plus {len(new)} new and {len(changed)} changed files.')
    readme=(f'# Freedom Arrow — Models and Music {V}\n\nThe models, music and voices of Freedom Arrow {GV}. Install it with the gameplay '
            f'package of the same build. Assets {PV} plus {len(new)} new and {len(changed)} changed files.\n')
    man.update(version=V,notes=[f'Freedom Arrow 0.8 models, music and voices {V}, made from gameplay {GV}.'])
    subprocess.run(['cp','--reflink=auto',str(complete.resolve()),str(out.resolve())],check=True)
    with tempfile.TemporaryDirectory() as tmp:
        lst=Path(tmp)/'drop.txt';lst.write_text('\n'.join(n for n in names if not n.startswith(ASSET))+'\n')
        with lst.open() as f:subprocess.run([zip,'-q','-nw','-d',str(out.resolve()),'-@'],stdin=f,check=True)
        stage=Path(tmp)/'stage'
        for n,b in (('mod.json',enc(mod)),('README.md',readme.encode()),(MAN,enc(man))):
            f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        subprocess.run([zip,'-q','-nw',str(out.resolve()),'mod.json','README.md',MAN],cwd=stage,check=True)
    with zipfile.ZipFile(out) as o:
        got={i.filename:i.CRC for i in o.infolist()}
        assert set(got)==set(assets)|{'mod.json','README.md'},'assets package paths differ from the complete package'
        assert all(got[n]==crc[n] for n in assets if n!=MAN),'an asset file differs from the complete package'
        assert json.loads(o.read(MAN))['files']==json.loads(zipfile.ZipFile(complete).read(MAN))['files']
        assert json.loads(o.read('mod.json'))['version']==V
    return {'file':out.name,'sha256':digest(out),'size':out.stat().st_size,'files':len(got),'previous':PV,'new':len(new),'changed':len(changed)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for x in ('complete','prev','version','gameplay','out'):p.add_argument('--'+x,required=True)
    p.add_argument('--zip',default='zip');a=p.parse_args()
    print(json.dumps(build(a.complete,a.prev,a.version,a.gameplay,a.out,a.zip),indent=2))
