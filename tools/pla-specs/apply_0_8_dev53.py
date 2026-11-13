"""Freedom Arrow 0.8.0-dev.53 over exact 0.8.0-dev.52: batch 3 of Osama's 13 Nov 14:36 PST list (thread 1569806740139282476).
Seller-texture reworks (work/pla-0.8/cart-20261113 runall.sh, build_cart.py, fix_glass.py, fix_metal.py):
- DF-15: seller w f.jpg camo on the cab/body's tiled UV set (UVChannel_2 x0.4), matching the listing; paint no longer bare metal.
- PHL-03: seller camo (phl0306) on the two door panels that had lost it; paint no longer bare metal (3ds Max metallic 1.0).
- CSK-181: camo body kept at full detail (only wheels/parts decimated); PCL-181: body decimated, tyres intact, window glass vanilla.
- QN-506: tracks/wheels dark, gun and missile pods olive (seller files have flat colours only).
- ZBD-04 / ZBD-04A / ZBD-04A Recon: seller Hull_Camo (digital) set, unrigged (m_zbd04_camo).
- PGL-625: seller Green_mix (digital) set. KQ-200: prop discs use the seller KQ200_Prop.tga alpha (translucent).
- SR-5: keeps the vanilla HIMARS model and hides its driver (FAModels 0.3.18 'hide').
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.53';PREV='0.8.0-dev.52'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with (REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod');MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));mb={};checks=0
for k in ('PLA Catalogue ZBD-04','PLA ZBD-04A'):
    assert models[k]['file']=='m_zbd04_green_static.fam',models[k];mb[k]=dict(models[k]);models[k]={**models[k],'file':'m_zbd04_camo_static.fam','battle':'m_zbd04_camo_lo_static.fam'};checks+=1
assert 'PLA SR-5' not in models;models['PLA SR-5']={'file':'','battle':'','align':False,'hide':'(?i)driver|crew|soldier|pilot|human|_char|body_'};mb['PLA SR-5']=None;checks+=1
files=sorted(x.name for x in a.stage.iterdir())
for k in ('PLA Catalogue ZBD-04','PLA ZBD-04A'):assert models[k]['file'] in files and models[k]['battle'] in files;checks+=1
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 14:36 PST list, batch 3 (reworks)','models_json':{k:{'before':mb[k],'after':models[k]} for k in mb},'files':files,'checks':checks,
 'not_done':{'DF-15/PHL-03 decals':'placement only in the seller .max (V-Ray blend)','Z-8L glass':'no seller map marks the windows','HQ-7':'no purchased model yet (old rip)','ZTZ-59D':'loads (500k vertices) but reported invisible; needs an armory look'}}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
(SRC/f'UserData/FreedomArrow/pla-{V}.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print('checks',checks,len(files))
