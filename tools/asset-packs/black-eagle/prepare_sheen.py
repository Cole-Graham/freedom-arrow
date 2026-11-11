"""Moderate Black Eagle body sheen trial; preserve source color and normals."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('current',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);results=[]
for stem in ['m_blackeagle_cg','m_blackeagle_lo']:
 mask=a.current/(stem+'_tex0_mask.png');original=np.asarray(Image.open(mask).convert('RGBA'));colour=np.asarray(Image.open(a.current/(stem+'_tex0.png')).convert('RGB'),dtype=np.float32)/255;value=colour.max(-1);weight=np.clip((value-.06)/.08,0,1)
 out=original.copy();metal=original[:,:,0].astype(np.float32)/255;smooth=original[:,:,3].astype(np.float32)/255
 out[:,:,0]=np.rint((metal+weight*np.maximum(.25-metal,0))*255).astype(np.uint8)
 out[:,:,3]=np.rint((smooth+weight*np.clip(.65-smooth,0,.16))*255).astype(np.uint8)
 assert np.array_equal(out[:,:,1:3],original[:,:,1:3]);assert np.array_equal(out[value<=.06],original[value<=.06])
 dest=a.output/mask.name;Image.fromarray(out).save(dest);sel=weight>.99
 results.append({'file':mask.name,'base_sha256':hashlib.sha256(mask.read_bytes()).hexdigest(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'selected_metal_median':float(np.median(out[:,:,0][sel])/255),'selected_smooth_median':float(np.median(out[:,:,3][sel])/255),'occlusion_detail_and_darkest_texels_preserved':True})
print(json.dumps(results,indent=2))
