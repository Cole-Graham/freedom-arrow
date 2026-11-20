"""New / Updated map tags for the Create a lobby window (Lateralus 20 Nov 2026, MapLabels.cs).
Each lobby map in the new package is compared with the current playtest release on the live manifest
(work/build-install/live-manifest.json "current"; the release before it when the package is that release).
A name the release did not have is "new", or "updated" when the release had the same name without the version number."""
import hashlib, json, re, sys, urllib.request, zipfile
from pathlib import Path
WORK=Path('/home/sam/tars/work/ba-dev/replicas/codex/work');MANIFEST=WORK/'build-install/live-manifest.json';CACHE=WORK/'build-install/release-cache'
sys.path.insert(0,str(Path(__file__).resolve().parent));from fa_version import key
PREFIX='UserData/FreedomArrow/scenarios/'
def base(name):return re.sub(r'\s+\d+(?:\.\d+)+$','',name.strip())
def lobby_maps(files):
    """files: package path -> bytes (or a zip). The map names the lobby lists: meta.json "scenario", Skirmish flavors left out."""
    names=set()
    for k in (files if isinstance(files,dict) else files.namelist()):
        if k.startswith(PREFIX) and k.endswith('/meta.json') and k.count('/')==4:
            raw=files[k] if isinstance(files,dict) else files.read(k)
            n=(json.loads(raw).get('scenario') or k.split('/')[3]).strip()
            if n.startswith('[FA]') and 'Skirmish' not in n:names.add(n)
    return names
def release(version):
    """(version, gameplay zip) of the playtest release to compare with."""
    m=json.loads(MANIFEST.read_text());rel={r['version']:r['gameplay'] for r in m['releases']}
    v=m['current']
    if v==version:v=max((r for r in rel if key(r)<key(version)),key=key)
    g=rel[v]
    for f in [CACHE/g['filename'],*WORK.glob('*/releases/0.6/out/*/'+g['filename'])]:
        if f.is_file() and f.stat().st_size==g['size'] and hashlib.sha256(f.read_bytes()).hexdigest()==g['sha256']:return v,zipfile.ZipFile(f)
    CACHE.mkdir(parents=True,exist_ok=True);f=CACHE/g['filename'];tmp=f.with_suffix('.part')
    with urllib.request.urlopen(g['url'],timeout=600) as r,open(tmp,'wb') as w:
        while b:=r.read(1<<20):w.write(b)
    assert hashlib.sha256(tmp.read_bytes()).hexdigest()==g['sha256'],f'{g["url"]} does not match the manifest'
    tmp.rename(f);return v,zipfile.ZipFile(f)
def labels(version,built):
    since,z=release(version);old=lobby_maps(z);old_base={base(n) for n in old}
    maps={n:('updated' if base(n) in old_base else 'new') for n in sorted(lobby_maps(built)-old)}
    return since,(json.dumps({'since':since,'maps':maps},indent=1,ensure_ascii=False)+'\n').encode()
if __name__=='__main__':
    # map_labels.py VERSION SCENARIO_DIR: preview against a make_scenario.py output folder
    d=Path(sys.argv[2]);built={PREFIX+f.relative_to(d).as_posix():f.read_bytes() for f in d.rglob('meta.json')}
    print(labels(sys.argv[1],built)[1].decode())
