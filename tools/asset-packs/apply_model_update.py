"""Apply a prototype asset delta only; never import a delta into BAModLauncher."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,zipfile
MANIFEST='UserData/FAAssets/manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(n):
    return n in ['Mods/FAModels.dll','Mods/FAMusic.dll','UserData/FAMusic/voice-presets.txt'] or n.startswith(('UserData/FAModels/','UserData/FAMusic/Packs/','UserData/FAMusic/Voice/'))
def apply(archive,game):
    game=game.resolve();z=zipfile.ZipFile(archive);names=z.namelist()
    if len(names)!=len(set(names)):raise ValueError('Duplicate paths')
    m=json.loads(z.read(MANIFEST));assert m['schema']==1 and m['kind']=='prototype-delta'
    def dest(n):
        p=(game/n).resolve()
        if Path(n).is_absolute() or '\\' in n or '..' in Path(n).parts or not p.is_relative_to(game):raise ValueError('Unsafe path '+n)
        return p
    for n,h in m['base_files'].items():
        assert allowed(n),n
        assert dest(n).is_file() and sha(dest(n))==h,'Previous assets differ: '+n
    payload={n:z.read(n) for n in names if n in m['files']}
    for n,data in payload.items():assert allowed(n) and hashlib.sha256(data).hexdigest()==m['files'][n],n
    permitted=set(m['files'])|{MANIFEST,'README.md','apply_model_update.py'}
    assert all(n in permitted for n in names),'Unexpected archive content'
    mapping='UserData/FAModels/models.json';oldmap=json.loads(dest(mapping).read_text()) if dest(mapping).exists() else {};oldmap.update(m['models'])
    writes={**payload,mapping:(json.dumps(oldmap,indent=2)+'\n').encode(),MANIFEST:(json.dumps(m,indent=2)+'\n').encode()}
    b=game/'UserData/FAAssetBackups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');b.mkdir(parents=True);exists=[]
    for n in writes:
        p=dest(n)
        if p.exists():q=b/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);exists.append(n)
    restore='from pathlib import Path\nimport shutil\ng=Path('+repr(str(game))+');b=Path('+repr(str(b))+')\nfor n in '+repr(list(writes))+':\n p=g/n\n if n in '+repr(exists)+':\n  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/n,p)\n else:p.unlink(missing_ok=True)\n'
    (b/'restore.py').write_text(restore)
    with (Path.home()/'.agent-changes.log').open('a') as log:log.write(datetime.datetime.now().astimezone().isoformat()+' | FA asset prototype delta | '+str(game)+' | asset files only | revert: python '+str(b/'restore.py')+'\n')
    try:
        for n,data in writes.items():p=dest(n);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.fa-assets-tmp');tmp.write_bytes(data);tmp.replace(p)
        assert all(dest(n).is_file() and sha(dest(n))==h for n,h in m['files'].items())
    except Exception:exec(compile(restore,str(b/'restore.py'),'exec'));raise
    return {'changed_asset_files':len(payload),'version':m['version'],'rollback':'python '+str(b/'restore.py'),'restart_required':True}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('game_root',type=Path);a=p.parse_args();print(json.dumps(apply(a.archive,a.game_root),indent=2))
