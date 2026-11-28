"""Kung Feng VI wheels (Shawn 27 Nov 18:3x: "Wheel is too tidy, make it realistic like 9K51 Grad"): the wheel sheet (tex2: tyres and green
rims) is clean and near black. The Grad's tyres and rims are dusty grey-brown. A dust layer (118, 108, 92) is blended over the sheet with
a multi-scale noise mask: up to 50 % on the tyres (dark pixels), about half that on the rims, tread detail kept. Arsenal 2048 and battle 1024 .fat files are written
from the result; the original goes to veh/x/kf6/pre-wheeldust/. usage: python kf6_wheel_dust.py  (then conv.py on the list it prints)"""
import os,shutil
import numpy as np
from PIL import Image
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';BK=V+'/x/kf6/pre-wheeldust';os.makedirs(BK,exist_ok=True)
f='m_roc_kf6_static_tex2.png';b=f'{BK}/{f}'
if not os.path.exists(b):shutil.copy(f'{V}/models/{f}',b)
im=Image.open(b);a=np.asarray(im.convert('RGBA')).astype(np.float32);H,W=a.shape[:2];rng=np.random.default_rng(27)
def noise(cells):
    g=rng.random((cells,cells)).astype(np.float32);return np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize((W,H),Image.BICUBIC)).astype(np.float32)/255
N=0.25*noise(8)+0.35*noise(32)+0.25*noise(128)+0.15*noise(512)
L=(0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2])/255
tyre=np.clip((0.22-L)/0.12,0,1)
w=np.clip(0.18+0.30*(N-0.4)/0.25,0.0,0.5)*(0.45+0.55*tyre)
D=np.array([118,108,92],np.float32)
from PIL import ImageFilter
det=a[...,:3]-np.asarray(Image.fromarray(a[...,:3].clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)   # tread / bolt detail
a[...,:3]=a[...,:3]*(1-w[...,None])+D*w[...,None]+det*w[...,None]*0.8
out=Image.fromarray(a.clip(0,255).round().astype(np.uint8),'RGBA').convert(im.mode)
out.save(f'{V}/models/{f}');os.makedirs('/tmp/kf6wd',exist_ok=True);out.resize((W//2,H//2),Image.LANCZOS).save('/tmp/kf6wd/m_roc_kf6_lo_static_tex2.png')
print('dust mean weight tyres %.2f rims %.2f'%(w[tyre>0.5].mean(),w[tyre<0.1].mean()))
