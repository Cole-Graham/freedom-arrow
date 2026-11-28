"""MTWV woodland option: the canvas stays plain (Shawn's reference photo: woodland body, plain green canvas). camo3d.py repaints by colour,
and the MTV canvas shares the bed's sheet, so the canvas UV islands (vanilla TENT mesh) are copied back from the default sheet."""
import numpy as np
from PIL import Image,ImageDraw
z=np.load('/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_MTV/mesh/TENT_34027.npz');uv=z['uv'];f=z['f0']
for st in ('m_roc_mtwv_static_tex0','m_roc_mtwv_lo_static_tex0'):
    d=Image.open(f'models/{st}.png').convert('RGBA');w=Image.open(f'x/mtwv/schemes/{st}@Woodland.png').convert('RGBA');W,H=d.size
    m=Image.new('L',(W,H),0);dr=ImageDraw.Draw(m)
    for t in f:dr.polygon([(uv[j,0]*W,(1-uv[j,1])*H) for j in t],fill=255)
    from PIL import ImageFilter;m=m.filter(ImageFilter.MaxFilter(5))
    w.paste(d,(0,0),m);w.save(f'x/mtwv/schemes/{st}@Woodland.png');print(st,'canvas texels restored %.1f%%'%(100*np.asarray(m).mean()/255))
