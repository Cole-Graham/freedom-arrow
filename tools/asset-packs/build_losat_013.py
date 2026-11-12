"""Add only LOSAT files/mapping to pinned assets0.1.12; retain all other payload bytes."""
from pathlib import Path
import zipfile,json,hashlib,datetime,argparse
from zoneinfo import ZoneInfo
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('base',type=Path);ap.add_argument('models',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
enc=lambda x:(json.dumps(x,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.base.read_bytes())=='8e6d6bf09e1e40985dc360ebe99bfdee02d9b55961bce022268f9fde50492e90','base pin must be measured before use'
with zipfile.ZipFile(a.base) as z:
 replace={};new={}
 for f in sorted(a.models.glob('m_losat*')):
  assert f.suffix in ('.fam','.png','.json'),f
  new['UserData/FAModels/'+f.name]=f.read_bytes()
 assert len(new)==40,len(new)
 model={'file':'m_losat.fam','battle':'m_losat_lo.fam','scale':1,'align':True}
 mapping=json.loads(z.read('UserData/FAModels/models.json'));assert 'MGM-166 LOSAT' not in mapping;mapping['MGM-166 LOSAT']=model;replace['UserData/FAModels/models.json']=enc(mapping)
 manifest=json.loads(z.read('UserData/FAAssets/manifest.json'));assert manifest['version']=='0.1.12';manifest['version']='0.1.13';manifest['models']['MGM-166 LOSAT']=model
 manifest['files'].update({n:sha(b) for n,b in {**new,**replace}.items()});manifest['notes'].append('LOSAT supplied model:separate turret group,armory2K/battle1K maps. Native rendering and turret alignment untested.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(z.read('mod.json'));mod['version']='0.1.13';replace['mod.json']=enc(mod)
 stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)')
 readme=z.read('README.md').decode().replace('0.1.12','0.1.13');heading='## Document change log';assert readme.count(heading)==1;body,log=readme.split(heading);body='**Adds the supplied tracked MGM-166 LOSAT model for the live LOSAT card; all prior model/music/voice bytes retained.** Native rendering,launcher movement and combat remain untested.\n\n'+body;replace['README.md']=(body+heading+log.rstrip()+'\n- '+stamp+' — Added LOSAT armory/battle geometry andPBR textures; other assets unchanged.\n').encode()
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for n in z.namelist():out.writestr(n,replace.get(n,z.read(n)))
  for n,b in new.items():assert n not in z.namelist();out.writestr(n,b)
 with zipfile.ZipFile(a.output) as out:
  assert out.testzip() is None
  for n,h in manifest['files'].items():assert sha(out.read(n))==h,n
  unchanged=[n for n in z.namelist() if n not in replace];assert all(out.read(n)==z.read(n) for n in unchanged)
 result={'version':'0.1.13','path':str(a.output),'sha256':sha(a.output.read_bytes()),'bytes':a.output.stat().st_size,'base_sha256':sha(a.base.read_bytes()),'new_files':len(new),'retained_byte_identical_files':len(unchanged),'verified_manifest_files':len(manifest['files']),'runtime_verified':False}
 a.output.with_suffix('.verification.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
