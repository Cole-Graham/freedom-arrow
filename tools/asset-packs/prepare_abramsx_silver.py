"""Restore purchased silver textures at bounded resolution; do not modify either mesh.

Run with the paid source GLB, the extracted AbramsX texture directory, the existing
famconv.py converter, its Python environment, and a staging output directory.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zipfile
from PIL import Image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ['glb','textures','converter','python','out']:ap.add_argument('--'+name,type=Path,required=True)
 a=ap.parse_args();recipe=json.loads(Path(__file__).with_name('abramsx-silver-source.json').read_text())
 assert sha(a.glb)==recipe['glb_sha256'],'Source GLB differs from the audited export'
 source=a.textures/recipe['silver_basecolor']['file'];assert sha(source)==recipe['silver_basecolor']['sha256']
 assert sha(a.converter)==recipe['converter_sha256'],'Inspect converter changes before preparing textures'
 a.out.mkdir(parents=True,exist_ok=True);stage=a.out/'UserData/FAModels';stage.mkdir(parents=True,exist_ok=True)
 for prefix,limit in [('m_abramsx_cg',2048),('m_abramsx_lo',1024)]:
  subprocess.run([str(a.python.absolute()),str(a.converter.resolve()),str(a.glb.resolve()),str(stage.resolve()),prefix,'--maps-only','--tex-max',str(limit)],check=True)
  with Image.open(source) as im:
   im=im.convert('RGBA');im.thumbnail((limit,limit),Image.Resampling.LANCZOS);im.save(stage/(prefix+'_tex0.png'))
 files={}
 for p in sorted(stage.glob('*.png')):
  w,h=struct.unpack('>II',p.read_bytes()[16:24]);expected=2048 if p.name.startswith('m_abramsx_cg') else 1024
  assert (w,h)==(expected,expected),(p.name,w,h)
  files[str(p.relative_to(a.out))]={'sha256':sha(p),'size':p.stat().st_size,'width':w,'height':h}
 assert len(files)==12
 receipt={'name':'Abrams X silver trial: armory2K, battle1K','mesh_changes':False,'mapping_changes':False,'files':files,'source':recipe,'native_visual_verified':False}
 (a.out/'silver-textures.json').write_text(json.dumps(receipt,indent=2)+'\n')
 zpath=a.out/'abramsx-silver-2k-armory-1k-battle.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_STORED) as z:
  for n in files:z.write(a.out/n,n)
  z.write(a.out/'silver-textures.json','silver-textures.json')
 print(json.dumps({'archive':str(zpath),'sha256':sha(zpath),'bytes':zpath.stat().st_size,'textures':len(files),'armory_resolution':2048,'battle_resolution':1024}))
if __name__=='__main__':main()
