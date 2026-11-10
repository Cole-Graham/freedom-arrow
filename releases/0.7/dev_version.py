"""Pick the dev version for the next 0.6 build.

builds.json is tracked in Git. It lists every version that build.py has packaged, with a hash of the
build inputs. A version is used once only:
- not in builds.json: never built, so keep it, whatever has changed;
- in builds.json with the same inputs: a rebuild of the same version, so keep it;
- in builds.json with other inputs: already built, so move to the next unused dev number.
build_constants.py runs this first. Run it alone to see the decision: python releases/0.7/dev_version.py"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, subprocess
from bump_version import bump, current
R=Path(__file__).resolve().parent
ROOT=R.parents[1]
LEDGER=R/'builds.json'
# Everything build_constants.py and build.py read from the repository.
INPUTS=['releases/0.7','releases/0.1/source','pipeline']
# Tracked, but not read by the build and not packaged.
SKIP=re.compile(r'^releases/0\.7/(builds\.json|dev_version\.py|bump_version\.py|verify\.py|EVIDENCE\.md|TESTING\.md|GAME-MODE\.md|(evidence|row-tests|economy-tests|fingerprint-tests|supply-stealth-tests|diagnostic-tests)/)|^pipeline/tests/')
def ledger():return json.loads(LEDGER.read_text(encoding='utf-8')) if LEDGER.is_file() else {}
def inputs_sha256(version):
    """Hash of the build inputs, with the version itself written as {VERSION} and Windows line ends as Unix ones."""
    files=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard','--',*INPUTS],cwd=ROOT,check=True,capture_output=True).stdout.decode().split('\0')
    pattern=re.compile(re.escape(version.encode())+rb'(?!\d)');h=hashlib.sha256()
    for name in sorted(f for f in set(files) if f and not SKIP.match(f) and (ROOT/f).is_file()):
        data=(ROOT/name).read_bytes()
        if b'\0' not in data:data=pattern.sub(b'{VERSION}',data.replace(b'\r\n',b'\n'))
        h.update(name.encode()+b'\0'+hashlib.sha256(data).digest())
    return h.hexdigest()
def dev_number(v):return int(re.fullmatch(r'0\.7\.0-dev\.(\d+)',v).group(1))
def ensure():
    """Bump the version only when the current one has been built from other inputs. Returns the version to build."""
    v=current();built=ledger().get(v)
    if built is None:print(f'{v}: not built yet, so this build keeps {v}.');return v
    if built['inputs']==inputs_sha256(v):print(f'{v}: inputs unchanged since its build, so this build keeps {v}.');return v
    test=re.fullmatch(r'(0\.7\.0-devtest\.lat\.)(\d+)',v)
    if test:
        prefix=test.group(1)
        used=[int(x[len(prefix):]) for x in [v,*ledger()] if x.startswith(prefix) and x[len(prefix):].isdigit()]
        new=prefix+str(max(used)+1)
    else:
        used=[x for x in [v,*ledger()] if re.fullmatch(r'0\.7\.0-dev\.\d+',x)]
        new=f'0.7.0-dev.{max(map(dev_number,used))+1}'
    print(f'{v}: already built and the inputs changed, so this build is {new}.');bump(new);return new
def check():
    """Called by build.py before it builds: stop if this version was already built from other inputs."""
    v=current();built=ledger().get(v);inputs=inputs_sha256(v)
    if built is not None and built['inputs']!=inputs:raise SystemExit(f'{v} was already built from other inputs. Run build_constants.py; it picks the next version.')
    return v,inputs
def record(archive):
    """Called by build.py after it packages. Keeps the first record of a version, so a rebuild changes nothing."""
    v,inputs=check();entries=ledger()
    if v in entries:print(f'{v} is already in builds.json with these inputs.');return
    commit=subprocess.run(['git','rev-parse','--short','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    entries[v]={'inputs':inputs,'bamod_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'parent_commit':commit,
     'built_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    LEDGER.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
    print(f'{v} recorded in builds.json. Commit it with this version.')
if __name__=='__main__':ensure()
