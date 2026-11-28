"""ROC Marine green gear (Shawn 27 Nov: "Make this green color darker and more close to the uniform"): the belt, leg straps, thigh
pouch and knee pads are a saturated green (about 35,64,45) beside a dark tiger-stripe uniform. Pixels whose green channel stands
clear of red and blue (g - max(r,b) above 8, full at 20; the camo's own green stands about 7 clear, so it stays) are desaturated
by 55 % and darkened to 72 %. Writes a new file; the source stays. usage: python darken_green.py IN.png OUT.png"""
import sys
import numpy as np
from PIL import Image
im=Image.open(sys.argv[1]);mode=im.mode;a=np.asarray(im.convert('RGBA')).astype(np.float32)
c=a[...,:3];r,g,b=c[...,0],c[...,1],c[...,2]
w=np.clip((g-np.maximum(r,b)-8)/12,0,1)[...,None]
L=(0.299*r+0.587*g+0.114*b)[...,None]
new=(c+0.55*(L-c))*0.72
a[...,:3]=c*(1-w)+new*w
Image.fromarray(np.clip(a+0.5,0,255).astype(np.uint8),'RGBA').convert(mode).save(sys.argv[2])
print('changed px %.1f%%'%(100*(w>0.05).mean()),'->',sys.argv[2])
