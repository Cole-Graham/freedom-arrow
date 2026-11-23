"""Freedom Arrow 0.8.0-dev.44 over exact 0.8.0-dev.43 (Osama 13 Nov 13:44 PST, thread 1569806740139282476):
"HQ-6 says he does ship with multiple textures. I redownloaded a few can you check?"
- HQ-6A: the seller's Camouflage set (Camouflage.rar, PBR Metalic Roughness), the coating on the listing preview cab,
  in place of the Base Green set. The re-downloaded DF-15 and ZSD-89A archives have the same contents as before.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.44';PREV='0.8.0-dev.43'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base);files=sorted(x.name for x in a.stage.iterdir());checks=0
for f in files:assert f.split('_static')[0].replace('_lo','') in ('m_hq6a',),f;checks+=1
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 13:44 PST: HQ-6 seller ships multiple textures; re-downloaded a few.',
 'files':files,'fixed':{'HQ-6A':'seller Camouflage set (forest camo) from Camouflage.rar'},'redownload_check':{'DF-15 zip':'same contents','ZSD-89A zip':'same contents','PCL-181 zip':'same size'},'checks':checks}
f=SRC/f'UserData/FreedomArrow/pla-{V}.json';f.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print('checks',checks)
