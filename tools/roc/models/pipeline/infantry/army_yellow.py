"""ROC Army digital camo with grass yellow (Shawn 27 Nov 20:5x, photo of the ROC Army uniform: "adding some more grass yellow ... more relevant to
the ROC Army, and do not change anything for all the Marine Uniforms"). Our army textures carry green, dark green and light speckle tones;
the real ROC Army pattern also has an olive/grass-yellow tone. The lighter mid-green camo blocks (green-dominant pixels whose block-averaged
brightness sits in the upper middle of the green tones) are shifted to grass yellow (hue ~55 deg, like the photo's olive khaki), keeping
their brightness detail; dark green, the light speckles and non-camo parts (skin, metal, black) stay. Writes <name>_army.png beside the
source. usage: python army_yellow.py IN.png [IN.png ...]"""
import sys,os,numpy as np
from PIL import Image,ImageFilter
Image.MAX_IMAGE_PIXELS=None
for f in sys.argv[1:]:
    im=Image.open(f);mode=im.mode;a=np.asarray(im.convert('RGBA')).astype(np.float32)
    c=a[...,:3];r,g,b=c[...,0],c[...,1],c[...,2];mx=c.max(2);mn=c.min(2);sat=(mx-mn)/np.maximum(mx,1)
    L=0.299*r+0.587*g+0.114*b
    green=(g>=r+4)&(g>=b+2)&(sat>0.12)
    Lb=np.asarray(Image.fromarray(L.clip(0,255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2))).astype(np.float32)
    # digital blocks: two coarse random grids (12 and 24 px cells, nearest-upscaled) make pixel-camo clusters, as in the real pattern
    H,W=L.shape;rng=np.random.default_rng(1127)
    def cells(n):return np.asarray(Image.fromarray((rng.random(((H+n-1)//n,(W+n-1)//n))*255).astype(np.uint8)).resize((W,H),Image.NEAREST)).astype(np.float32)/255
    blocks=(0.6*cells(24*max(1,W//2048))+0.4*cells(12*max(1,W//2048)))>0.58
    q=np.percentile(Lb[green],35) if green.sum()>1000 else 255
    w=(green&blocks&(Lb>q)).astype(np.float32)
    tgt=np.stack([L*1.20,L*1.12,L*0.62],-1)   # grass yellow / olive khaki at the same brightness (~ (120,112,62) at L 100)
    a[...,:3]=c*(1-w[...,None])+tgt*w[...,None]
    out=os.path.splitext(f)[0]+'_army.png';Image.fromarray(a.clip(0,255).round().astype(np.uint8),'RGBA').convert('RGBA' if mode=='RGBA' else 'RGB').save(out)
    print(os.path.basename(f),'green %.0f%% -> yellow %.1f%% of texture'%(100*green.mean(),100*(w>0.5).mean()),'->',os.path.basename(out))
