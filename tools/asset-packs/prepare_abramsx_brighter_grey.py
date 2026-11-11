"""Lighten mid-grey material response by reducing only its metallic blend.

Colour textures and smoothness stay fixed. Black and very dark grey pixels are
excluded. This is a numeric material-mask trial at the current texture sizes.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile
import numpy as np
from PIL import Image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ['current','green','out']:ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);stage=a.out/'UserData/FAModels';stage.mkdir(parents=True,exist_ok=True)
 recipe={'label':'Abrams X brighter mid-grey material trial2','metallic_target':.32,'dark_value_excluded_at_or_below':.32,'full_adjustment_from_value':.40,'files':{},'base_files':{},'required_files':{},'mesh_sha256':{n:sha(a.current/n) for n in ['m_abramsx_cg.fam','m_abramsx_lo.fam']},'pixel_checks':{},'native_verified':False}
 for prefix,limit in [('m_abramsx_cg',2048),('m_abramsx_lo',1024)]:
  name=prefix+'_tex0.png';mask=a.current/(prefix+'_tex0_mask.png');colour=np.asarray(Image.open(a.current/name).convert('RGB'),np.float32)/255;green=np.asarray(Image.open(a.green/name).convert('RGB'),np.float32)/255;original=np.asarray(Image.open(mask).convert('RGBA'));assert original.shape==(limit,limit,4)
  value=colour.max(-1);saturation=(value-colour.min(-1))/np.maximum(value,.001);difference=np.mean(np.abs(colour-green),-1)
  selected=(saturation<.18)&(value>.32)&(value<.9)&(difference>.02)
  weight=np.clip((.18-saturation)/.12,0,1)*np.clip((difference-.02)/.07,0,1)*np.clip((value-.32)/.08,0,1)*selected
  metal=original[...,0].astype(np.float32)/255;result=original.copy();result[...,0]=np.rint((metal-weight*np.maximum(metal-.32,0))*255).astype(np.uint8)
  changed=np.any(result!=original,axis=-1);assert changed.any()
  assert np.array_equal(result[~selected],original[~selected]) and np.array_equal(result[...,1:],original[...,1:])
  assert np.array_equal(result[value<=.32],original[value<=.32])
  n='UserData/FAModels/'+mask.name;p=a.out/n;Image.fromarray(result,'RGBA').save(p);recipe['files'][n]=sha(p);recipe['base_files'][n]=sha(mask);recipe['required_files']['UserData/FAModels/'+name]=sha(a.current/name)
  recipe['pixel_checks'][prefix]={'dimensions':[limit,limit],'changed_fraction':float(changed.mean()),'black_and_very_dark_grey_pixels_identical':True,'non_selected_pixels_identical':True,'occlusion_detail_and_smoothness_channels_identical':True,'metallic_median_before':float(np.median(metal[selected])),'metallic_median_after':float(np.median(result[...,0][selected])/255)}
 (a.out/'brighter-grey-trial.json').write_text(json.dumps(recipe,indent=2)+'\n')
 with zipfile.ZipFile(a.out/'abramsx-brighter-grey-trial2.zip','w',zipfile.ZIP_STORED) as z:
  for n in recipe['files']:z.write(a.out/n,n)
  z.write(a.out/'brighter-grey-trial.json','brighter-grey-trial.json')
 print(json.dumps(recipe,indent=2))
if __name__=='__main__':main()
