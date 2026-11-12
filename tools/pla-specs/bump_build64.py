"""Version files for Build64 (main dev 0.7.0-dev.58 under the PLA pack)."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';FA=REL/'source/UserData/FreedomArrow'
B=64;merge=json.loads(Path(sys.argv[1]).read_text())
m=json.loads((REL/'mod.json').read_text());m.update(name=f'PLA TEST Build {B}',version=str(B),description='Latest PLA pack on top of main dev 0.7.0-dev.58: dev.58 runtime, maps, Russian and US units, with all China work kept.');(REL/'mod.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
c=json.loads((FA/'channel.json').read_text());c.update(package_version=str(B),verification=f'PLA Build{B-1} on main dev 0.7.0-dev.58. Data checks only; in-game check pending.');(FA/'channel.json').write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
p=json.loads((FA/'pla-build.json').read_text());p.update(build=B,label=f'PLA TEST Build {B}');(FA/'pla-build.json').write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n')
(FA/f'pla-build{B}.json').write_text(json.dumps({'build':B,'request':'Osama 12 Nov: "update the latest build into our PLA test build, we\'re getting close to launching"','merge':merge,'native_verified':False},indent=2,ensure_ascii=False)+'\n')
