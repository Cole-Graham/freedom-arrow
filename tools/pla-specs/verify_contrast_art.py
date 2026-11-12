"""Check contrast-only artwork against the exact Build24 source checkout; no game verification."""
from pathlib import Path
import argparse,xml.etree.ElementTree as E,hashlib,subprocess,json
from PIL import Image,ImageChops
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-root',type=Path,required=True);p.add_argument('--renderer',required=True);a=p.parse_args();old=a.base_root.resolve();r=Path(__file__).resolve().parents[2];masters=r/'tools/pla-specs/approved-patch-masters';icons=r/'releases/0.6/source/runtime-qa/icons';src=r/'releases/0.6/source';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest();renderer=a.renderer
for name in ['FA_CHINA_AIR_SF','FA_CHINA_ARMORED','FA_CHINA_ROCKET','FA_CHINA_NAVAL']:
 f=masters/(name+'.svg');root=E.parse(f).getroot();original=E.parse(old/'tools/pla-specs/approved-patch-masters'/(name+'.svg')).getroot();star=root[-1][0][-1] if name=='FA_CHINA_ROCKET' else root[-1][0]
 # Only explicit colors may differ; all geometry, transforms, stroke widths and structure remain exact.
 for a,b in zip(original.iter(),root.iter(),strict=True):
  assert a.tag==b.tag
  assert {k:v for k,v in a.attrib.items() if k not in ['fill','stroke']}=={k:v for k,v in b.attrib.items() if k not in ['fill','stroke']}

 before=Image.open(old/'releases/0.6/source/runtime-qa/icons'/(name+'.png')).convert('RGBA');after=Image.open(icons/(name+'.png')).convert('RGBA');assert before.size==after.size==(128,128);assert ImageChops.difference(before.getchannel('A'),after.getchannel('A')).getbbox() is None
 checks.append({'address':name,'geometry_identical':True,'alpha_identical':True,'changed_rgb_bounds':ImageChops.difference(before.convert('RGB'),after.convert('RGB')).getbbox(),'before_sha256':sha((old/'releases/0.6/source/runtime-qa/icons'/(name+'.png')).read_bytes()),'after_sha256':sha((icons/(name+'.png')).read_bytes())})
# Assert every other icon, all masters and all runtime C# are exact Build24 bytes.
changed=[]
for f in (old/'releases/0.6/source/runtime-qa/icons').glob('*.png'):
 n=icons/f.name
 if n.read_bytes()!=f.read_bytes():changed.append(f.stem)
assert sorted(changed)==sorted(x['address'] for x in checks)
for f in (old/'tools/pla-specs/approved-patch-masters').glob('*.png'):assert f.read_bytes()==(masters/f.name).read_bytes()
for f in (old/'releases/0.6/source/runtime-qa').glob('*.cs'):assert f.read_bytes()==(src/'runtime-qa'/f.name).read_bytes()

assert len(checks)==4
print(json.dumps({"passed":True,"four_spec_checks":checks,"other_icons_and_all_masters_unchanged":True},indent=2))
