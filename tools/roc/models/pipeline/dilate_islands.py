"""Fill the empty texels between UV islands with the nearest island colour (12 px), so mip levels show no grey seams (CM-32's new hull UVs have
thousands of small islands). usage: python dilate_islands.py POS.npy IMG.png [IMG.png ...]   (in place)"""
import sys,numpy as np
from PIL import Image
P=np.load(sys.argv[1]).astype(np.float32)[::-1];ok0=~np.isnan(P[...,0])
for f in sys.argv[2:]:
    im=Image.open(f).convert('RGBA');W,H=im.size;a=np.asarray(im).astype(np.float32)
    ok=ok0[np.arange(H)*ok0.shape[0]//H][:,np.arange(W)*ok0.shape[1]//W].copy()
    for it in range(12):
        acc=np.zeros_like(a);cnt=np.zeros((H,W),np.float32)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            s=np.roll(a,(dy,dx),axis=(0,1));so=np.roll(ok,(dy,dx),axis=(0,1));acc+=s*so[...,None];cnt+=so
        new=(~ok)&(cnt>0);a[new]=acc[new]/cnt[new][:,None];ok=ok|new
    Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA').save(f);print('DILATE',f,'filled %.0f%%'%(100*ok.mean()))
