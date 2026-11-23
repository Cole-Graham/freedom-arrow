"""Set the 0.3 development version in every file that states it."""
from pathlib import Path
import argparse, json
R=Path(__file__).resolve().parent
FILES=['verify.py','mod.json','vehicle-contract.json','us-baltic-contract.json','README.md',
 'source/runtime-qa/Runtime.cs','source/runtime-qa/FreedomArrow.Runtime.csproj',
 'source/conquest/FreedomArrow.ConquestPrototype.csproj','source/conquest/Mod.cs',
 'source/UserData/FreedomArrow/channel.json','source/UserData/FreedomArrow/release-notes.md']
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('version',help='for example 0.2.0-dev.15');new=ap.parse_args().version
    old=json.loads((R/'mod.json').read_text(encoding='utf-8'))['version']
    for name in FILES:
        p=R/name;s=p.read_bytes().decode('utf-8');assert old in s,(name,old)
        p.write_bytes(s.replace(old,new).encode('utf-8'))
    p=R.parents[1]/'README.md';s=p.read_bytes().decode('utf-8');a='The '+old.split('-')[-1]+' data candidate';assert a in s,a
    p.write_bytes(s.replace(a,'The '+new.split('-')[-1]+' data candidate').encode('utf-8'))
    print(old,'->',new)
if __name__=='__main__':main()
