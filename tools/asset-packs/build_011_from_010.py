"""Restore native4K F14/F21 armory body/cockpit maps; all other pack members stay byte-identical."""
from pathlib import Path
import zipfile,json,hashlib,datetime,argparse,struct
from zoneinfo import ZoneInfo
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);ap.add_argument('texture_dir',type=Path);args=ap.parse_args();r=args.folder.resolve();enc=lambda j:(json.dumps(j,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest();stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)');c=json.loads(Path(__file__).with_name('f14-armory-4k.json').read_text())
oldpath=r/'FreedomArrow-Assets-0.1.10.bamod';assert sha(oldpath.read_bytes())=='9d8cfbaead5f60c69d86389daa597d251df4bb26f5164e6232697dd00349331a';replace={};rows=[]
with zipfile.ZipFile(oldpath) as old:
 assert sha(old.read('UserData/FAModels/m_f14_cg.fam'))==c['armory_mesh_sha256']
 for idx,label in c['material_indices'].items():
  for suffix in ['.png','_n.png','_mask.png']:
   name=f'm_f14_cg_tex{idx}{suffix}';path='UserData/FAModels/'+name;b=(args.texture_dir/name).read_bytes();before=old.read(path)
   assert b.startswith(b'\x89PNG\r\n\x1a\n') and struct.unpack('>2i',b[16:24])==(4096,4096)
   assert struct.unpack('>2i',before[16:24])==(2048,2048)
   replace[path]=b;rows.append({'path':path,'material':label,'old_size':[2048,2048],'new_size':[4096,4096],'old_sha256':sha(before),'sha256':sha(b)})
 assert len(replace)==12
 manifest=json.loads(old.read('UserData/FAAssets/manifest.json'));manifest['version']='0.1.11';manifest['files'].update({n:sha(b) for n,b in replace.items()});manifest['notes'].append('F14/F21 armory body and cockpit: original4K colour, normal and mask maps restored from supplied source. Geometry, swept wings, gear and battle textures retained; native review pending.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.11';replace['mod.json']=enc(mod)
 readme=old.read('README.md').decode().replace('0.1.10','0.1.11');a,b=readme.split('## Document change log');a+='F14/F21 armory body/cockpit texture maps now use original4K pixels instead of2K imports. Swept wings, gear-down mesh, clear glass, other armory textures and battle1K assets retained. No generated/upscaled artwork. Native appearance pending.\n\n';replace['README.md']=(a+'## Document change log'+b.rstrip()+'\n- '+stamp+' — Restored twelve original4K armory maps for F14/F21 body and cockpit; all other payload retained.\n').encode()
 output=r/'FreedomArrow-Assets-0.1.11.bamod'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():z.writestr(n,replace[n] if n in replace else old.read(n))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in replace)
 result={'version':'0.1.11','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_paths':list(replace),'verified_files':len(manifest['files']),'loader_version':'0.3.4','runtime_rendering_verified':False,'texture_changes':rows};(r/'assets011-package.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
