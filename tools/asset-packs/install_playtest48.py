"""Install the pinned local gameplay test and scoped models, with one undo.

Does not change the public launcher feed or canonical live/PLA aliases.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import zipfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('recipe', type=Path)
    a = ap.parse_args()
    c = json.loads(a.recipe.read_text())
    h = Path.home()
    g = h / '.local/share/Steam/steamapps/common/broken_arrow'
    switch = runpy.run_path(str(h / 'Games/FreedomArrow-Profiles/switch.py'))
    sha, closed = switch['sha'], switch['closed']
    with (h / 'Games/FreedomArrow-Profiles/switch.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        closed()
        switch['install'](c['profile'], g, h, check=True)
        archive = h / 'Downloads' / c['asset_file']
        assert sha(archive) == c['asset_sha256']
        mapping_path = g / 'UserData/FAModels/models.json'
        assert sha(mapping_path) == c['base_mapping_sha256'], 'Model map changed: inspect before merging'
        mapping = json.loads(mapping_path.read_text())
        before_mapping = json.loads(mapping_path.read_text())
        for name, scale in [('F-21 Super Tomcat', 1.1), ('MGM-166 LOSAT', 1.2)]:
            mapping[name]['scale'] = scale
        assert 'Object 640 Black Eagle' not in mapping
        mapping['Object 640 Black Eagle'] = c['model_entry']
        assets = g / 'UserData/FAAssets/manifest.json'
        manifest = json.loads(assets.read_text())
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist()) == set(c['files'])
            data = {}
            for name, digest in c['files'].items():
                assert name.startswith('UserData/FAModels/m_blackeagle_')
                assert Path(name).name == name.split('/')[-1] and '..' not in Path(name).parts
                data[name] = z.read(name)
                assert hashlib.sha256(data[name]).hexdigest() == digest
        data['UserData/FAModels/models.json'] = (json.dumps(mapping, indent=2) + '\n').encode()
        for name, content in data.items():
            manifest['files'][name] = hashlib.sha256(content).hexdigest()
        for name in ['F-21 Super Tomcat', 'MGM-166 LOSAT', 'Object 640 Black Eagle']:
            manifest['models'][name] = mapping[name]
        manifest.setdefault('local_overrides', {})['dev48_models'] = {
            'gameplay_version': c['profile']['version'], 'files': c['files'],
            'scales': {'F-21 Super Tomcat': 1.1, 'MGM-166 LOSAT': 1.2},
            'native_verified': False,
        }
        data['UserData/FAAssets/manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
        manager_name = 'UserData/BAModManager/manifest.json'
        targets = sorted([*data, manager_name])
        protected = {}
        for folder in ['UserData/FAModels', 'UserData/FAMusic']:
            for p in (g / folder).rglob('*'):
                if p.is_file() and p.relative_to(g).as_posix() not in targets:
                    protected[p.relative_to(g).as_posix()] = sha(p)
        for name in ['Mods/FAModels.dll', 'Mods/FAMusic.dll']:
            protected[name] = sha(g / name)
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup = h / 'Games/BA-Backups' / ('pre-dev48-models-' + stamp)
        backup.mkdir(parents=True)
        existed = []
        for name in targets:
            p = g / name
            if p.is_file():
                dest = backup / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
                existed.append(name)
        restore = ('from pathlib import Path\nimport shutil\n'
                   'g=Path(' + repr(str(g)) + ');b=Path(' + repr(str(backup)) + ')\n'
                   'for n in ' + repr(targets) + ':\n'
                   ' p=g/n\n'
                   ' if n in ' + repr(existed) + ':\n'
                   '  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/n,p)\n'
                   ' else:p.unlink(missing_ok=True)\n')
        (backup / 'restore-assets.py').write_text(restore)
        core = None
        try:
            closed()
            core = switch['install'](c['profile'], g, h)
            closed()
            for name, content in data.items():
                p = g / name
                p.parent.mkdir(parents=True, exist_ok=True)
                temp = p.with_name(p.name + '.fatmp')
                temp.write_bytes(content)
                temp.replace(p)
            manager = g / manager_name
            current = json.loads(manager.read_text())
            package = next(p for p in current['packages'] if p.get('info', {}).get('id') == 'freedomarrow.gameplay')
            assert package['enabled'] and package['info']['version'] == c['profile']['version']
            package['files'] = sorted(set(package['files']) | set(data))
            temp = manager.with_suffix('.json.fatmp')
            temp.write_text(json.dumps(current, indent=2) + '\n')
            temp.replace(manager)
            for name, content in data.items():
                assert sha(g / name) == hashlib.sha256(content).hexdigest(), name
            for name, digest in protected.items():
                assert sha(g / name) == digest, name
            actual_mapping = json.loads(mapping_path.read_text())
            for name, entry in before_mapping.items():
                if name not in ['F-21 Super Tomcat', 'MGM-166 LOSAT']:
                    assert actual_mapping[name] == entry, name
        except Exception:
            exec(compile(restore, str(backup / 'restore-assets.py'), 'exec'))
            if core:
                subprocess.run(shlex.split(core['undo']), check=True)
            raise
        undo = backup / 'restore.py'
        undo.write_text('import subprocess\nsubprocess.run(' + repr(['python3', str(backup / 'restore-assets.py')]) + ',check=True)\nsubprocess.run(' + repr(shlex.split(core['undo'])) + ',check=True)\n')
        result = dict(core, model_files=len(c['files']), preserved_shared_files=len(protected),
                      scales={'F-21 Super Tomcat': 1.1, 'MGM-166 LOSAT': 1.2},
                      model_entry=actual_mapping['Object 640 Black Eagle'],
                      undo='python3 ' + str(undo), public_feed_changed=False)
        (a.recipe.parent / 'installed-result.json').write_text(json.dumps(result, indent=2) + '\n')
        with (h / '.agent-changes.log').open('a') as log:
            log.write(datetime.datetime.now().astimezone().isoformat() + ' | BA Codex | dev48 Black Eagle/model scales; all other shared assets verified | undo: python3 ' + str(undo) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
