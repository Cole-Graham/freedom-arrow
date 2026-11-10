"""Limit F14 armory detail to three3K colour maps; supporting maps2K, battle1K."""
from pathlib import Path
import zipfile,json,hashlib,datetime,argparse,struct
from zoneinfo import ZoneInfo
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);ap.add_argument('texture_dir',type=Path);args=ap.parse_args();r=args.folder.resolve();enc=lambda j:(json.dumps(j,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest();stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)');c=json.loads(Path(__file__).with_name('f14-armory-4k.json').read_text())
oldpath=r/'FreedomArrow-Assets-0.1.11.bamod';assert sha(oldpath.read_bytes())=='9db8af05b17e14326a93f80a221b77f634d6187520751ffe666f194ed0f6d582';replace={};rows=[]
assert sha((r/'FreedomArrow-Assets-0.1.10.bamod').read_bytes())=='9d8cfbaead5f60c69d86389daa597d251df4bb26f5164e6232697dd00349331a'
with zipfile.ZipFile(oldpath) as old:
 assert sha(old.read('UserData/FAModels/m_f14_cg.fam'))==c['armory_mesh_sha256']
 for idx,label in c['material_indices'].items():
  for suffix in ['.png','_n.png','_mask.png']:
   name=f'm_f14_cg_tex{idx}{suffix}';path='UserData/FAModels/'+name;before=old.read(path)
   if idx in ('3','4','5') and suffix=='.png':b=(args.texture_dir/name).read_bytes();size=3072
   else:
    with zipfile.ZipFile(r/'FreedomArrow-Assets-0.1.10.bamod') as base:b=base.read(path)
    size=2048
   assert b.startswith(b'\x89PNG\r\n\x1a\n') and struct.unpack('>2i',b[16:24])==(size,size)
   assert struct.unpack('>2i',before[16:24])==(4096,4096)
   replace[path]=b;rows.append({'path':path,'material':label,'old_size':[4096,4096],'new_size':[size,size],'old_sha256':sha(before),'sha256':sha(b)})
 assert len(replace)==12
 manifest=json.loads(old.read('UserData/FAAssets/manifest.json'));manifest['version']='0.1.12';manifest['files'].update({n:sha(b) for n,b in replace.items()});manifest['notes'].append('F14/F21 budget: three body colour maps3K; normal/mask/cockpit2K; battle1K. Existing appearance and glass retained. Calculated texture memory +80MiB over old2K, not measured runtime usage.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.12';replace['mod.json']=enc(mod)
 readme=old.read('README.md').decode().replace('0.1.11','0.1.12');a,b=readme.split('## Document change log');a+='Current F14/F21 texture budget supersedes the preceding4K recipe: three3K body colour maps, all supporting/cockpit maps2K, battle1K. Existing model appearance and clear glass retained. Memory/performance unmeasured.\n\n';replace['README.md']=(a+'## Document change log'+b.rstrip()+'\n- '+stamp+' — Reduced F14 texture memory: three3K colour maps; supporting maps2K; battle1K. Calculated +80MiB over2K instead of prior +768MiB; runtime untested.\n').encode()
 output=r/'FreedomArrow-Assets-0.1.12.bamod'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():z.writestr(n,replace[n] if n in replace else old.read(n))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in replace)
 result={'version':'0.1.12','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_paths':list(replace),'verified_files':len(manifest['files']),'loader_version':'0.3.4','runtime_rendering_verified':False,'texture_changes':rows};(r/'assets012-package.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
