"""Patriot-like surface on ROC trucks (Shawn 27 Nov 19:3x, "the PBR property of patriot PAC-2 ... the details of metallic reflection"): the
vanilla Patriot reads as matte painted steel (its material: metallic 0, the shine comes only from the surface detail). Our enhanced masks
(R metal, G AO, A smoothness) made the trucks glossy (smoothness about 0.7) and half-metallic on some sheets. Each body mask is remapped:
metal x0.3 (bare-metal detail stays visible, painted panels stop mirroring), smoothness 0.22-0.50 following its old pattern (worn and dirty
spots stay rougher), AO kept. Wheels (patriot_wheels.py) are left alone. Originals go to veh/x/<slug>/pre-patriot-pbr/.
usage: python patriot_pbr.py SLUG WHEELTEX"""
import sys,os,glob,shutil,numpy as np
from PIL import Image
slug,wt=sys.argv[1],int(sys.argv[2]);V=os.path.dirname(os.path.abspath(__file__))+'/../veh';BK=f'{V}/x/{slug}/pre-patriot-pbr';os.makedirs(BK,exist_ok=True)
for f in sorted(glob.glob(f'{V}/models/m_roc_{slug}_*static_tex*_mask.png')):
    if f.endswith(f'_tex{wt}_mask.png'):continue
    b=f'{BK}/{os.path.basename(f)}'
    if not os.path.exists(b):shutil.copy(f,b)
    m=np.asarray(Image.open(b).convert('RGBA')).astype(np.float32)
    old=(m[...,0].mean(),m[...,3].mean())
    m[...,0]*=0.3;m[...,3]=255*(0.22+0.28*(m[...,3]/255))
    Image.fromarray(m.clip(0,255).round().astype(np.uint8),'RGBA').save(f)
    print(os.path.basename(f),'metal %.0f->%.0f smooth %.0f->%.0f'%(old[0],m[...,0].mean(),old[1],m[...,3].mean()))
