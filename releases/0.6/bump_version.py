"""Set the 0.6 development version in every file that states it.

You do not usually need this: build_constants.py picks the version (see dev_version.py)."""
from pathlib import Path
import argparse, json, re
R=Path(__file__).resolve().parent
FILES=['verify.py','mod.json','vehicle-contract.json','us-baltic-contract.json','README.md',
 'source/runtime-qa/Runtime.cs','source/runtime-qa/FreedomArrow.Runtime.csproj',
 'source/UserData/FreedomArrow/channel.json','source/UserData/FreedomArrow/release-notes.md']
# These files also name old versions in their history. Change only the title and the verify command there.
CURRENT_LINES={'README.md':lambda l:l.startswith('# ') or 'verify.py' in l,
 'source/UserData/FreedomArrow/release-notes.md':lambda l:l.startswith('# ')}
def current():return json.loads((R/'mod.json').read_text(encoding='utf-8'))['version']
def bump(new):
    old=current();pattern=re.compile(re.escape(old)+r'(?!\d)')
    for name in FILES:
        p=R/name;s=p.read_bytes().decode('utf-8');keep=CURRENT_LINES.get(name,lambda l:True)
        t=''.join(pattern.sub(new,l) if keep(l) else l for l in s.splitlines(keepends=True))
        assert t!=s,(name,old)
        p.write_bytes(t.encode('utf-8'))
    print(old,'->',new)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('version',help='for example 0.6.0-dev.1');bump(ap.parse_args().version)
if __name__=='__main__':main()
