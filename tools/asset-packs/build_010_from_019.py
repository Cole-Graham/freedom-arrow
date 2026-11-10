"""Add the source-rig swept-wing armory export to the verified0.1.9 pack."""
from pathlib import Path
import zipfile,json,hashlib,datetime,argparse
from zoneinfo import ZoneInfo
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);ap.add_argument('armory_mesh',type=Path);args=ap.parse_args();r=args.folder.resolve();enc=lambda j:(json.dumps(j,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest();stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)')
oldpath=r/'FreedomArrow-Assets-0.1.9.bamod';assert sha(oldpath.read_bytes())=='e5a90f1af63cfe394013daa23bad882ef11b246052be6bf18d1fb9eaaffa3ca9';mesh=args.armory_mesh.read_bytes();assert sha(mesh)=='f0d3e5ed35b95e7ad160ff92dcf2a7f70ddbfa4b392951e44176e9e54bd79a4c'
with zipfile.ZipFile(oldpath) as old:
 name='UserData/FAModels/m_f14_cg.fam';assert sha(old.read(name))=='5da8dde77a4c5f34c409c323eac836fb379a274a2b5573a9962fc3b2a8a49ab8';replace={name:mesh}
 manifest=json.loads(old.read('UserData/FAAssets/manifest.json'));manifest['version']='0.1.10';manifest['files'][name]=sha(mesh);manifest['notes'].append('F14/F21 armory: existing source wing pivots swept back; original gear-down body, UVs, textures and battle model retained. Native visual check pending.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.10';replace['mod.json']=enc(mod)
 readme=old.read('README.md').decode().replace('0.1.9','0.1.10');a,b=readme.split('## Document change log');a+='F14/F21 armory wing pose swept back using supplied source wing pivots. Landing gear and body are byte-identical; all UVs, textures and battle geometry retained. Preview checked; native visual review pending.\n\n';replace['README.md']=(a+'## Document change log'+b.rstrip()+'\n- '+stamp+' — Swept the F14/F21 armory wings back using the existing source rig; no new rigging.\n').encode()
 output=r/'FreedomArrow-Assets-0.1.10.bamod'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():z.writestr(n,replace[n] if n in replace else old.read(n))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in replace)
 result={'version':'0.1.10','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_paths':list(replace),'verified_files':len(manifest['files']),'loader_version':'0.3.4','runtime_rendering_verified':False};(r/'assets010-package.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
