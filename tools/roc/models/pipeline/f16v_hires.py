"""F-16V texture upgrade (Shawn 28 Nov 12:2x: "Remap the texture of F-16V and upgrade to high resolution. Enhance the PBR textures by following
the Mirage 2000-5's"). The Arsenal sheet was the seller's 4096 F16_Body_8_diff_1 cut to 2048, with no normal map and a mask from the specular
map under Rafale remaps. Now, like the Mirage (its own metal/roughness maps used as painted, metallic 1 / smoothness 0, plus a normal map):
- colour: the full 4096 F16_Body_8_diff_1 (Arsenal), 1024 for the battle models;
- _n: the seller's f16_Body_Norm (4096 / 1024);
- _mask: R metal = f16_body_MREC red, G AO 1, A smoothness = F16_body_Glos x 0.85 (the Mirage averages 0.50);
- mat.json: metallic 1, smoothness 0, no remaps (the mask as painted), as the Mirage.
Originals in veh/x/f16v/pre-hires/. usage: python f16v_hires.py, then conv.py on the list it prints"""
import os,json,shutil
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
T=os.path.dirname(os.path.abspath(__file__));X=T+'/../veh/x/f16v';M=T+'/../veh/models';BK=X+'/pre-hires';os.makedirs(BK,exist_ok=True)
col=Image.open(X+'/F16_Body_8_diff_1.tga').convert('RGB');nrm=Image.open(X+'/f16_Body_Norm.tga').convert('RGB')
mr=np.asarray(Image.open(X+'/f16_body_MREC.tga').convert('RGB'));gl=np.asarray(Image.open(X+'/F16_body_Glos.tga').convert('L')).astype(np.float32)
mask=np.dstack([mr[...,0],np.full(gl.shape,255,np.uint8),np.zeros(gl.shape,np.uint8),(gl*0.85).clip(0,255).astype(np.uint8)])
mask=Image.fromarray(mask,'RGBA');out=[]
for st,size in (('m_roc_f16v_static',4096),('m_roc_f16v_lo_static',1024)):
    for sfx in ('','_n','_mask'):
        f=f'{M}/{st}_tex0{sfx}.png'
        if os.path.exists(f) and not os.path.exists(f'{BK}/{st}_tex0{sfx}.png'):shutil.copy(f,f'{BK}/{st}_tex0{sfx}.png')
    for sfx,im in (('',col),('_n',nrm),('_mask',mask)):
        (im if im.size[0]==size else im.resize((size,size),Image.LANCZOS)).save(f'{M}/{st}_tex0{sfx}.png');out.append(f'{st}_tex0{sfx}.png')
for st in ('m_roc_f16v_static','m_roc_f16v_lo_static','m_roc_f16v_lo_static_l1','m_roc_f16v_lo_static_l2'):
    f=f'{M}/{st}.mat.json'
    if not os.path.exists(f):continue
    if not os.path.exists(f'{BK}/{st}.mat.json'):shutil.copy(f,f'{BK}/{st}.mat.json')
    d=json.load(open(f))
    for k,v in d.items():
        if 'tex0.png' in k:v.pop('metallicRemap',None);v.pop('smoothnessRemap',None);v.update(metallic=1.0,smoothness=0.0)
    json.dump(d,open(f,'w'),indent=1)
open(T+'/../veh/fat/list_f16v_hires.txt','w').write('\n'.join(out)+'\n');print('\n'.join(out))
