"""CM-32 bare roof plate (Shawn 27 Nov 18:0x: "Add camo to this area similar to other place"): the CM-32 uses the CM-34 hull, and the
roof plate under the CM-34 turret (2.1 x 1.9 m, 2 triangles, UV u 0.198-0.427, v 0.281-0.483) is painted plain dark with the turret's
shadow, because the turret hides it. Fill that UV rectangle with camo from the long hull-side strip of the same texture (u 0.075-0.150,
image rows 34-57 % and 63-86 %, clear of the painted details above): both strip pieces turned 90 deg and stacked, resized to the rectangle, 6 px feathered edge.
Done on the colour texture and the Dust/Mosaic paint sets, Arsenal and battle sizes. The CM-34 shares these files; on the CM-34 the
plate stays under its turret. Originals go to veh/x/cm34/pre-panel-camo/. usage: python cm34_panel_camo.py"""
import os,shutil
import numpy as np
from PIL import Image
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';BK=V+'/x/cm34/pre-panel-camo';os.makedirs(BK,exist_ok=True)
FILES=[V+'/models/m_roc_cm34_static_tex0.png',V+'/models/m_roc_cm34_lo_static_tex0.png']+[f'{V}/x/cm34/schemes/m_roc_cm34{l}_static_tex0@{s}.png' for l in ('','_lo') for s in ('Dust','Mosaic')]
R=(0.198,1-0.483,0.427,1-0.281)   # rectangle in image fractions (x0,y0,x1,y1); image y = 1 - v
for f in FILES:
    b=f'{BK}/{os.path.basename(f)}'
    if not os.path.exists(b):shutil.copy(f,b)
    im=Image.open(b);mode=im.mode;a=np.asarray(im.convert('RGBA')).astype(np.float32);H,W=a.shape[:2]
    x0,y0,x1,y1=int(R[0]*W),int(R[1]*H),int(R[2]*W),int(R[3]*H);u0,u1=int(0.075*W),int(0.150*W)
    pieces=[np.rot90(a[int(r0*H):int(r1*H),u0:u1]) for r0,r1 in ((0.34,0.57),(0.63,0.86))]
    n=min(p.shape[1] for p in pieces);patch=np.concatenate([p[:,:n] for p in pieces],0);patch=np.asarray(Image.fromarray(patch.clip(0,255).astype(np.uint8),'RGBA').resize((x1-x0,y1-y0),Image.LANCZOS)).astype(np.float32)
    e=max(2,6*W//1536);yy,xx=np.mgrid[0:y1-y0,0:x1-x0];w=np.clip(np.minimum.reduce([xx,yy,x1-x0-1-xx,y1-y0-1-yy])/e,0,1)[...,None]
    a[y0:y1,x0:x1]=a[y0:y1,x0:x1]*(1-w)+patch*w
    Image.fromarray(a.clip(0,255).round().astype(np.uint8),'RGBA').convert(mode).save(f);print('patched',os.path.basename(f),(x0,y0,x1,y1))
