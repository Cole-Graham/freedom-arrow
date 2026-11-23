"""Freedom Arrow 0.8.0-dev.43 over exact 0.8.0-dev.42 (Osama 13 Nov 13:33-13:36 PST, thread 1569806740139282476):
"Are you sure DF-15 looks right? because the image preview when I bought it was not that"; "ALL models we bought should be
using the seller's texture unless it doesn't have it and when it doesn't, TELL ME first".
Each cart model was compared with its CGTrader listing preview. Seller textures that the FBX export had dropped are
reconnected (seller files and seller UVs only):
- DF-15: seller 3-colour camo (w f.jpg) on the cab, body and launcher (blinn1*, mi cai, lv) in place of plain green.
- PCL-181: seller digital camo (F015(2021).7z maps/F0150017.jpg) on the body in place of plain tan; the seller's own
  flag/badge textures are no longer painted over.
- ZSD-89A: seller "Textures_02_main" set, the coating in the listing preview (was the plain-green 01 set).
Models.json is unchanged (same file names).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.43';PREV='0.8.0-dev.42'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base);files=sorted(x.name for x in a.stage.iterdir());checks=0
for f in files:assert f.split('_static')[0].replace('_lo','') in ('m_df15','m_pcl181','m_zsd89a'),f;checks+=1
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 13:33-13:36 PST: DF-15 does not match the seller preview; all purchased models use the seller texture, and report missing textures before making any.',
 'files':files,'fixed':{'DF-15':'seller w f.jpg camo reconnected','PCL-181':'seller F0150017.jpg digital camo reconnected; seller flag/badge restored','ZSD-89A':'seller Textures_02_main (listing preview set)'},
 'reported_missing':['HQ-6A Forest Camo set not in the download (only Base Green)','QN-506 and ZTZ-59D paint only in SketchUp/Lumion files','DF-15 and PHL-03 decal placement lost in the FBX (decal images present)','PHL-03 tyre map (Map #29) not in the download'],'checks':checks}
f=SRC/f'UserData/FreedomArrow/pla-{V}.json';f.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print('checks',checks)
