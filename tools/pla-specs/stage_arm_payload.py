"""Stage rebuilt infantry LODs and only atlases changed by new LOD UV bounds."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'releases/0.6'
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args()
c=json.loads((R/'pla-specializations-contract.json').read_text())
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==c['base_sha256']
pins={};changed=[];source=R/'source'
assert len(list(a.payload.glob('*.fas')))==75 and len(list(a.payload.glob('*.png')))==150
with zipfile.ZipFile(a.base) as z:
 for f in sorted([*a.payload.glob('*.fas'),*a.payload.glob('*.png')]):
  n='UserData/FAModels/'+f.name;h=hashlib.sha256(f.read_bytes()).hexdigest()
  if f.suffix=='.png' and h==hashlib.sha256(z.read(n)).hexdigest():continue
  if f.suffix=='.png':changed.append(f.name)
  out=source/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out);pins[n]=h
receipt={'method':'proper segment rotation with length-only scaling and rigid hand rotation; nearest native surface weights','variants':25,'lods':75,'approved_offsets_preserved':True,'unchanged_atlas_textures':150-len(changed),'repacked_atlases':changed,'source_texture_content_unchanged':True,'sha256':pins,'preview_user_accepted':True,'native_verified':False}
(source/'UserData/FreedomArrow/infantry-arm-repair.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Staged',len(pins),'files; 75 FAS LODs and',len(changed),'repacked LOD atlases')
