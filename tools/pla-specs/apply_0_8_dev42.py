"""Freedom Arrow 0.8.0-dev.42 over exact 0.8.0-dev.41 (Osama 13 Nov 13:19-13:21 PST, thread 1569806740139282476):
"I need you to use the seller's pattern on all of them please first ... let's start with the seller's version. QN-506
doesn't even have textures so it's fine"; "I'm talking all the models, we want to use what the seller already provided".
Every model whose paint we generated or recoloured goes back to the seller's own texture:
- Rebuilt from the seller's coating (the exact source the desert recolour started from): DF-15, DF-17, HQ-6A (also no
  brightening), ZTZ-59D/59D1 (seller colours), DF-21/21D, DF-31A, YJ-18, HQ-12, PGZ-88, PLZ-70, PLZ-83, PLZ-85, PLZ-89, PGZ-09.
- Type 89 (PLARF) uses the seller-painted ZSD-89 like PLAN ZSD-89 (no desert copy).
- Generated digital camo (dev.35-38) back to the seller files: ZTQ-15, ZTQ-15 Recon, VT-5, VT-5 Recon -> m_ztq15_green;
  ZTZ-99, ZTZ-99A, ZTZ-99A2, ZTZ-99G, VT-4 -> m_ztz99a_green; ZBD-04, ZBD-04A -> m_zbd04_green; ZTZ-100 -> m_ztz100_cg.
Kept: QN-506 camo (no seller texture), ZTZ-96/96A/96B model swap (seller files), missing-texture fixes and clear glass.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
V='0.8.0-dev.42';PREV='0.8.0-dev.41'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base);MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ))
SET={'PLA Catalogue Type 89':('m_zsd89_static.fam','m_zsd89_lo_static.fam','m_zsd89d_static.fam'),
 **{k:('m_ztq15_green_static.fam','m_ztq15_green_lo_static.fam',None) for k in ('PLA ZTQ-15','PLA ZTQ-15 Recon','PLA VT-5','PLA VT-5 Recon')},
 **{k:('m_ztz99a_green_static.fam','m_ztz99a_green_lo_static.fam','m_ztz99a_wdigi_static.fam') for k in ('PLA Catalogue ZTZ-99','PLA ZTZ-99A','PLA ZTZ-99A2','PLA ZTZ-99G','PLA Catalogue VT-4 / Al-Hyder')},
 **{k:('m_zbd04_green_static.fam','m_zbd04_green_lo_static.fam','m_zbd04_wdigi_static.fam') for k in ('PLA Catalogue ZBD-04','PLA ZBD-04A')},
 'PLA ZTZ-100':('m_ztz100_cg.fam','m_ztz100_lo.fam','m_ztz100_wd.fam')}
before={};checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
names=set(z.namelist())
for k,(f,b,was) in SET.items():
    before[k]=models.get(k);ok(k in models,('mapped',k))
    if was:ok(models[k]['file']==was,('expected current',k,models[k]['file']))
    else:ok('ztq15_' in models[k]['file'] and 'digi' in models[k]['file'],('ZTQ generated camo',k,models[k]['file']))
    ok(f'UserData/FAModels/{f}' in names and f'UserData/FAModels/{b}' in names,('seller files present',f,b))
    models[k]={**models[k],'file':f,'battle':b}
files=sorted(x.name for x in a.stage.iterdir())
for f in files:ok(f'UserData/FAModels/{f}' in names,('replaces an existing file',f))
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 13:19-13:21 PST: use the seller-provided textures on all models (QN-506 excepted, it has none).',
 'mappings':{k:{'before':before[k],'after':models[k]} for k in SET},'replaced_files':files,
 'rebuilt_from_seller_coating':['DF-15','DF-17','HQ-6A','ZTZ-59D','DF-21','DF-31A','YJ-18','HQ-12','PGZ-88','PLZ-70','PLZ-83','PLZ-85','PLZ-89','PGZ-09'],
 'kept':['QN-506 projected woodland (seller has no textures)','ZTZ-96/96A/96B model swap','missing-texture fixes (black tyres, dark windows, PCL-181 flag painted out)','clear glass'],'checks':0}
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))
