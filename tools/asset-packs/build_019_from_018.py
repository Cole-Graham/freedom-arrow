"""Rebuild only Abrams X battle normals in the verified prior combined asset pack."""
from pathlib import Path
import zipfile,json,hashlib,datetime,argparse,tempfile,subprocess,sys
from zoneinfo import ZoneInfo
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path);args=parser.parse_args();r=args.folder.resolve()
enc=lambda j:(json.dumps(j,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest();stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)')
oldpath=r/'FreedomArrow-Assets-0.1.8.bamod';assert sha(oldpath.read_bytes())=='dd969d2b1c5d5ba48030feb31bc87655a8d0a86a4d4c2145875385ad366affe7'
with zipfile.ZipFile(oldpath) as old,tempfile.TemporaryDirectory() as td:
 t=Path(td);name='UserData/FAModels/m_abramsx_lo.fam';(t/'m_abramsx_lo.fam').write_bytes(old.read(name))
 subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'model-loader/fix_panel_normals.py'),'--source',str(t),'--output',str(t/'fixed'),'m_abramsx_lo'],check=True)
 validation=json.loads((t/'fixed/normal-validation.json').read_text());replace={name:(t/'fixed/m_abramsx_lo.fam').read_bytes()}
 manifest=json.loads(old.read('UserData/FAAssets/manifest.json'));manifest['version']='0.1.9';manifest['files'].update({n:sha(b) for n,b in replace.items()});manifest['notes'].append('Abrams X battle mesh: corrected smoothed normals; triangle positions, UVs, textures and armory mesh unchanged. Runtime appearance unverified.');replace['UserData/FAAssets/manifest.json']=enc(manifest)
 mod=json.loads(old.read('mod.json'));mod['version']='0.1.9';replace['mod.json']=enc(mod)
 readme=old.read('README.md').decode().replace('0.1.8','0.1.9');assert readme.count('## Document change log')==1
 heading='## Document change log';a,b=readme.split(heading);a+='Abrams X battle normals corrected: large-face mean error19.6°→1.8°. Surface positions, UVs, textures and other models/audio retained. Mesh/preview evidence only; native appearance pending.\n\n';readme=a+heading+b.rstrip()+'\n- '+stamp+' — Corrected Abrams X battle normals only; all unrelated payload bytes retained.\n';replace['README.md']=readme.encode()
 output=r/'FreedomArrow-Assets-0.1.9.bamod'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in old.namelist():z.writestr(n,replace[n] if n in replace else old.read(n))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
  assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in replace)
 result={'version':'0.1.9','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_paths':list(replace),'verified_files':len(manifest['files']),'loader_version':'0.3.4','runtime_rendering_verified':False,'normal_validation':validation};(r/'assets019-package.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
