from pathlib import Path
import zipfile,json,hashlib,datetime
from zoneinfo import ZoneInfo
import sys
r=Path(sys.argv[1]).resolve();enc=lambda j:(json.dumps(j,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest();stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)');oldpath=r/'FreedomArrow-Assets-0.1.7.bamod';assert sha(oldpath.read_bytes())=='66a0957dabeab286bd3a226163a0b44620e4e71b776277d642e2f27956a43e86'
with zipfile.ZipFile(oldpath) as old:
 mapping=json.loads(old.read('UserData/FAModels/models.json'));assert 'F-14 Tomcat' in mapping and 'F-21 Super Tomcat' not in mapping
 mapping['F-21 Super Tomcat']=mapping['F-14 Tomcat'];replace={'UserData/FAModels/models.json':enc(mapping)}
 manifest=json.loads(old.read('UserData/FAAssets/manifest.json'));manifest['version']='0.1.8';manifest['files'].update({n:sha(b) for n,b in replace.items()});manifest['models']['F-21 Super Tomcat']=manifest['models']['F-14 Tomcat'];manifest['notes'].append('F-21 Super Tomcat aliases the existing F-14 model; F-14 mapping retained for older builds.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.8';replace['mod.json']=enc(mod)
 readme=old.read('README.md').decode().replace('0.1.7','0.1.8');readme=readme.rstrip()+'\n- '+stamp+' — Added the F-21 model-name alias for dev.17; all model, texture, loader and audio bytes retained.\n';replace['README.md']=readme.encode();output=r/'FreedomArrow-Assets-0.1.8.bamod'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():z.writestr(n,replace[n] if n in replace else old.read(n))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in replace)
 result={'version':'0.1.8','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_paths':list(replace),'verified_files':len(manifest['files']),'loader_version':'0.3.4','runtime_rendering_verified':False};(r/'assets018-package.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
