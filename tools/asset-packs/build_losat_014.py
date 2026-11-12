"""Replace only LOSAT attachments with static root meshes in pinned assets0.1.13."""
from pathlib import Path
import argparse,json,hashlib,zipfile,datetime
from zoneinfo import ZoneInfo
from losat_static import groups
p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);p.add_argument('static_dir',type=Path);p.add_argument('output',type=Path);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda j:(json.dumps(j,indent=2)+'\n').encode()
assert sha(a.base.read_bytes())=='46c71ab28402a66e38daaea663857c2265bb0e2597fcc29d36beb20ccdf8ec27'
with zipfile.ZipFile(a.base) as old:
 removed={'UserData/FAModels/'+stem+ext for stem in ['m_losat','m_losat_lo'] for ext in ['.fam','.mat.json']};added={}
 for stem in ['m_losat','m_losat_lo']:
  for ext in ['.fam','.mat.json']:
   n='UserData/FAModels/'+stem+'_static'+ext;b=(a.static_dir/(stem+'_static'+ext)).read_bytes();added[n]=b
   if ext=='.fam':assert [x[0] for x in groups(b)]==['root']
   else:assert b==old.read('UserData/FAModels/'+stem+ext)
 mapping=json.loads(old.read('UserData/FAModels/models.json'));assert mapping['MGM-166 LOSAT']['file']=='m_losat.fam';mapping['MGM-166 LOSAT']={'file':'m_losat_static.fam','battle':'m_losat_lo_static.fam','scale':1,'align':False};replace={'UserData/FAModels/models.json':enc(mapping)}
 meta=json.loads(old.read('UserData/FAAssets/manifest.json'));assert meta['version']=='0.1.13';meta['version']='0.1.14';meta['models']['MGM-166 LOSAT']=mapping['MGM-166 LOSAT']
 for n in removed:del meta['files'][n]
 meta['files'].update({n:sha(b) for n,b in {**added,**replace}.items()});meta['notes'].append('LOSAT correction:static root only, no turret attachment or automatic alignment. Every mesh segment and texture retained byte for byte.');replace['UserData/FAAssets/manifest.json']=enc(meta)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.14';replace['mod.json']=enc(mod)
 stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)');body,log=old.read('README.md').decode().split('## Document change log');body=body.replace('0.1.13','0.1.14',1);replace['README.md']=('**LOSAT is one static root model in both armory and battle. No turret-bone attachment or automatic alignment remains.** Existing mesh, normals, UVs, indices and textures are retained; native placement needs review.\n\n## Earlier pack details\n\n'+body+'## Document change log'+log.rstrip()+'\n- '+stamp+' — Removed LOSAT turret attachment; static root-only variants preserve every mesh segment and texture.\n').encode()
 with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():
   if n not in removed:z.writestr(n,replace.get(n,old.read(n)))
  for n,b in added.items():z.writestr(n,b)
 with zipfile.ZipFile(a.output) as z:
  assert z.testzip() is None
  for n,s in meta['files'].items():assert sha(z.read(n))==s,n
  unchanged=[n for n in old.namelist() if n not in removed|set(replace)];assert all(z.read(n)==old.read(n) for n in unchanged)
 result={'version':'0.1.14','sha256':sha(a.output.read_bytes()),'bytes':a.output.stat().st_size,'removed_paths':sorted(removed),'added_paths':sorted(added),'retained_byte_identical_files':len(unchanged),'verified_manifest_files':len(meta['files']),'static_root_only':True,'runtime_verified':False};a.output.with_suffix('.verification.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
