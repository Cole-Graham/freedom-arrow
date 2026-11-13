"""Freedom Arrow 0.8.0-dev.51 over exact 0.8.0-dev.50: batch 2 of Osama's 13 Nov 14:36 PST list (thread 1569806740139282476).
Vanilla glass: FAModels cockpitDonor US_F16_Glass (the game's own F-16 canopy material) on the glass of J-5, J-6, J-7, J-8,
Z-10, Z-11WB, HQ-12, PCL-09, PHL-16, DF-17 (DF-ZF), DF-21, DF-31A and PHL-191. Where the seller painted the glass into the hull
atlas, the see-through faces were split out by the seller's own opacity map (DF-17: its refraction map) with
work/pla-0.8/batch-20261113b/glass_split.py and the model rebuilt with its original famconv arguments.
More metal: HQ-6A hull/turret and Z-11WB mask maps lifted (metallic >= 0.45 / 0.5, smoothness +0.12 / +0.15).
Z-8L glass is not split: its seller texture has no opacity, refraction or other map that marks the windows.
Models.json is unchanged.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.51';PREV='0.8.0-dev.50'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--log',type=Path,required=True);a=p.parse_args()
with (REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod');names=set(z.namelist())
files=sorted(x.name for x in a.stage.iterdir());checks=0
for f in files:
    if f.endswith('.mat.json'):
        d=json.loads((a.stage/f).read_text());assert f'UserData/FAModels/{f}' in names,f;checks+=1
donors=sorted(f for f in files if f.endswith('.mat.json') and 'US_F16_Glass' in (a.stage/f).read_text());assert len(donors)>=24,donors;checks+=1
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 14:36 PST: vanilla glass transplants and transparent windows; Z-11WB and HQ-6 more metallic.',
 'glass_donor_files':donors,'build_log':json.loads(a.log.read_text()),'files':files,'not_done':{'Z-8L glass':'no map marks the windows in the seller texture'},'checks':checks}
(SRC/f'UserData/FreedomArrow/pla-{V}.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print('checks',checks,len(donors))
