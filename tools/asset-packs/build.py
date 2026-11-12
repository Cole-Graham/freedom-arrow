"""Build a separate optional models/music BAModLauncher package; export changed files for prototypes."""
import argparse,hashlib,json,struct,zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def safe(name):
    p=Path(name)
    if not name or p.name!=name or '\\' in name or name in ('.','..'):raise ValueError('Unsafe asset name: '+name)
    return name

def fam_textures(path):
    data=path.read_bytes();at=0
    def take(n):
        nonlocal at
        if n<0 or at+n>len(data):raise ValueError('Truncated FAM: '+str(path))
        b=data[at:at+n];at+=n;return b
    def integer():return struct.unpack('<i',take(4))[0]
    def string():return take(integer()).decode('utf-8')
    if take(4)!=b'FAM1':raise ValueError('Unsupported FAM: '+str(path))
    textures=set();parts=integer()
    if not 0<parts<100000:raise ValueError('Invalid FAM part count')
    for _ in range(parts):
        string();groups=integer()
        if not 0<groups<100000:raise ValueError('Invalid material count')
        for _ in range(groups):
            tex=string()
            if tex:textures.add(safe(tex))
            take(16);nv=integer();take(nv*32);ni=integer();take(ni*4)
    if at!=len(data):raise ValueError('Trailing FAM bytes: '+str(path))
    return textures

def collect(game,config):
    directory=game/'UserData/FAModels';all_models=json.loads((directory/'models.json').read_text());models={};files={}
    def add(name,required=True):
        name=safe(name);p=directory/name
        if not p.is_file():
            if required:raise FileNotFoundError(p)
            return
        files['UserData/FAModels/'+name]=p
    for unit in config['units']:
        entry=all_models[unit];models[unit]=entry
        for name in dict.fromkeys([entry['file'],entry.get('battle') or entry['file']]):
            safe(name);add(name)
            for tex in fam_textures(directory/name):
                add(tex)
                for suffix in ['_n.png','_mask.png']:add(Path(tex).stem+suffix,False)
            add(Path(name).stem+'.mat.json',False)
    for name in ['karatel-license.txt','xm30-source.txt']:add(name,False)
    for folder in config.get('music_roots',[]):
        root=game/folder
        if not root.is_dir():raise FileNotFoundError(root)
        for p in root.rglob('*'):
            if p.is_file():files[p.relative_to(game).as_posix()]=p
    for name in config.get('music_files',[]):
        p=game/name
        if p.is_file():files[name]=p
    for name in ['FAModels.dll','FAMusic.dll']:files['Mods/'+name]=game/'Mods'/name
    if not (game/'UserData/FAMusic/Packs/USA').is_dir():raise ValueError('USA default playlist is missing')
    # Do not ship playlist choice or playback history: the loader defaults to USA
    # when no choice exists, and asset updates preserve a player's saved choice.
    return models,files

def build(game,output,version,config_path=None,previous=None):
    cfg=json.loads((config_path or ROOT/'live.json').read_text());models,files=collect(game,cfg)
    hashes={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in sorted(files.items())}
    base=json.loads(previous.read_text()) if previous else None
    if base and (base['id']!=cfg['id'] or output.suffix.lower()!='.zip'):raise ValueError('Prototype deltas require matching pack ID and .zip output; do not import a delta into BAModLauncher')
    changed={n:h for n,h in hashes.items() if not base or base['files'].get(n)!=h}
    manifest={'schema':1,'id':cfg['id'],'version':version,'models':models,'files':hashes,'notes':cfg['notes'],'kind':'prototype-delta' if base else 'full-asset-pack'}
    if base:manifest['base_files']=base['files']
    text=lambda obj:(json.dumps(obj,indent=2)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True);tmp=output.with_name(output.name+'.tmp')
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for n,h in changed.items():
                data=files[n].read_bytes()
                if hashlib.sha256(data).hexdigest()!=h:raise RuntimeError('Asset changed while building: '+n)
                z.writestr(n,data)
            z.writestr('UserData/FAAssets/manifest.json',text(manifest))
            if base:
                z.writestr('apply_model_update.py',(ROOT/'apply_model_update.py').read_bytes())
                readme='Prototype changed-file update. Do NOT import into BAModLauncher. Close the game. Extract apply_model_update.py and run: python apply_model_update.py UPDATE.zip GAME_ROOT . It checks the previous model files, merges live mappings, backs up touched files, then verifies the new files. No gameplay constants are changed.\n'
            else:
                z.writestr('UserData/FAModels/models.json',text(models))
                z.writestr('mod.json',text({'id':cfg['id'],'name':cfg['name'],'version':version,'type':'mod','description':'Optional live models, music and voice assets. USA playlist by default. Install once; keep enabled while updating Freedom Arrow gameplay. No PLA test assets or gameplay data.'}))
                readme='Optional live-unit models, music and existing voice assets. USA is the default playlist for new installs. Existing playlist choices are retained. Close the game; import/apply this .bamod in BAModLauncher separately from Freedom Arrow gameplay. Keep this model package installed when updating gameplay. Includes models for seven live units plus the existing music/voice pack; no PLA preview roster or balance data. Gameplay updates do not require reinstalling this pack. Raw source archives are excluded. This private prototype package has not been cleared for public asset redistribution.\n'
            stamp=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')
            readme+='\n## Document change log\n\n- '+stamp+' (America/Los_Angeles) — Built this independent cosmetic asset package; no gameplay data.\n'
            z.writestr('README.md',readme)
        with zipfile.ZipFile(tmp) as z:
            assert z.testzip() is None
            for n,h in changed.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
        tmp.replace(output)
    finally:tmp.unlink(missing_ok=True)
    output.with_suffix('.manifest.json').write_bytes(text(manifest))
    return {'output':str(output),'version':version,'models':len(models),'total_asset_files':len(files),'changed_files':len(changed),'raw_asset_bytes':sum(p.stat().st_size for p in files.values()),'download_bytes':output.stat().st_size,'kind':manifest['kind']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game_root',type=Path);p.add_argument('output',type=Path);p.add_argument('--version',required=True);p.add_argument('--config',type=Path);p.add_argument('--previous-manifest',type=Path);a=p.parse_args();print(json.dumps(build(a.game_root,a.output,a.version,a.config,a.previous_manifest),indent=2))
