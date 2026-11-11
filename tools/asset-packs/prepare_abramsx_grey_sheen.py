"""Adjust only metallic/smoothness channels of grey-painted Abrams X hull texels.

The original green and approved silver colours identify the repainted grey regions.
Colour, normals, occlusion, detail channels, tracks, geometry and dimensions stay fixed.
"""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile
import numpy as np
from PIL import Image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ['green','silver','out']:ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);stage=a.out/'UserData/FAModels';stage.mkdir(parents=True,exist_ok=True)
 recipe={'label':'Abrams X grey-panel sheen trial1','metallic_target':.55,'smoothness_boost':.08,'smoothness_cap':.76,'files':{},'base_files':{},'source_files':{},'required_files':{},'mesh_sha256':{n:sha(a.green/n) for n in ['m_abramsx_cg.fam','m_abramsx_lo.fam']},'pixel_checks':{},'native_verified':False}
 for prefix,limit in [('m_abramsx_cg',2048),('m_abramsx_lo',1024)]:
  name=prefix+'_tex0.png';oldmask=a.silver/(prefix+'_tex0_mask.png');colour=np.asarray(Image.open(a.silver/name).convert('RGB'),np.float32)/255;green=np.asarray(Image.open(a.green/name).convert('RGB'),np.float32)/255
  original=np.asarray(Image.open(oldmask).convert('RGBA'));assert original.shape==(limit,limit,4)
  value=colour.max(-1);saturation=(value-colour.min(-1))/np.maximum(value,.001);difference=np.mean(np.abs(colour-green),-1)
  grey=(saturation<.18)&(value>.25)&(value<.9)&(difference>.02)
  weight=np.clip((.18-saturation)/.12,0,1)*np.clip((difference-.02)/.07,0,1)*np.clip((value-.25)/.08,0,1)*grey
  result=original.copy();metal=original[...,0].astype(np.float32)/255;smooth=original[...,3].astype(np.float32)/255
  result[...,0]=np.rint((metal+weight*np.maximum(.55-metal,0))*255).astype(np.uint8)
  result[...,3]=np.rint((smooth+weight*np.clip(.76-smooth,0,.08))*255).astype(np.uint8)
  outside=~grey;changed=np.any(result!=original,axis=-1)
  assert np.array_equal(result[outside],original[outside]) and np.array_equal(result[...,1:3],original[...,1:3])
  assert changed.any() and not np.any(changed&outside)
  n='UserData/FAModels/'+oldmask.name;p=a.out/n;Image.fromarray(result,'RGBA').save(p)
  recipe['files'][n]=sha(p);recipe['base_files'][n]=sha(oldmask);recipe['required_files']['UserData/FAModels/'+name]=sha(a.silver/name);recipe['source_files'].update({str(a.silver/name):sha(a.silver/name),str(a.green/name):sha(a.green/name)})
  recipe['pixel_checks'][prefix]={'dimensions':[limit,limit],'changed_fraction':float(changed.mean()),'non_grey_pixels_identical':True,'occlusion_and_detail_channels_identical':True,'original_grey_metallic_median':float(np.median(metal[grey])),'new_grey_metallic_median':float(np.median(result[...,0][grey])/255),'original_grey_smoothness_median':float(np.median(smooth[grey])),'new_grey_smoothness_median':float(np.median(result[...,3][grey])/255)}
  Image.fromarray(np.rint(weight*255).astype(np.uint8)).save(a.out/(prefix+'-grey-selector.png'))
 (a.out/'sheen-trial.json').write_text(json.dumps(recipe,indent=2)+'\n')
 with zipfile.ZipFile(a.out/'abramsx-grey-sheen-trial1.zip','w',zipfile.ZIP_STORED) as z:
  for n in recipe['files']:z.write(a.out/n,n)
  z.write(a.out/'sheen-trial.json','sheen-trial.json')
 print(json.dumps(recipe,indent=2))
if __name__=='__main__':main()
