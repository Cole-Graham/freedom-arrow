"""CM-11 dark patches shining (Shawn 27 Nov 18:3x: "Check these dark patches, it is shining when rotate the camera"): in the hull mask
(tex1, R metal, A smoothness) the dark rust/grime patches have smoothness ~90/255 against ~43 on the rest, so they flash when the camera
turns. Smoothness is scaled down where the colour map is dark: factor 1 - 0.8 * clip((70 - luma) / 35, 0, 1); metal unchanged.
Arsenal (2048) and battle (1024) masks; originals in veh/x/cm11/pre-shine/. usage: python cm11_shine.py"""
import os,shutil
import numpy as np
from PIL import Image
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';BK=V+'/x/cm11/pre-shine';os.makedirs(BK,exist_ok=True)
col=np.asarray(Image.open(V+'/models/tex_full/m_roc_cm11_static_tex1.png').convert('RGB')).astype(np.float32)
for f in ('m_roc_cm11_static_tex1_mask.png','m_roc_cm11_lo_static_tex1_mask.png'):
    b=f'{BK}/{f}'
    if not os.path.exists(b):shutil.copy(f'{V}/models/{f}',b)
    m=np.asarray(Image.open(b).convert('RGBA')).astype(np.float32);H,W=m.shape[:2]
    c=np.asarray(Image.fromarray(col.astype(np.uint8)).resize((W,H),Image.LANCZOS)).astype(np.float32)
    L=0.299*c[...,0]+0.587*c[...,1]+0.114*c[...,2];k=1-0.8*np.clip((70-L)/35,0,1)
    before=m[...,3][L<45].mean();m[...,3]*=k
    Image.fromarray(m.clip(0,255).round().astype(np.uint8),'RGBA').save(f'{V}/models/{f}')
    print(f,'smoothness in dark patches %.0f -> %.0f, rest %.0f'%(before,m[...,3][L<45].mean(),m[...,3][L>=70].mean()))
