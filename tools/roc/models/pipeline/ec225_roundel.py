"""EC225 roundel (Shawn 27 Nov 15:0x: "Replace this emblem on both side by the real ROC Blue sky with a White Sun emblem"). The livery's first
roundel drew the 12 rays as cosine petals (it read as a gear). Repaints, on the finished textures, the real emblem: a blue disc and the white
sun of the national emblem: 12 straight-sided triangular rays (each 30 deg wide at its base), a blue ring, then the white sun disc
(radii 30 : 17 : 15 of the ray length, as in the flag specification), on both sides (side-facing texels, centre y 5.25 m, z 2.05 m).
The texture's own panel detail stays (brightness ratio to its local average). usage: python ec225_roundel.py"""
import os,glob,numpy as np
from PIL import Image,ImageFilter
V=os.path.dirname(os.path.abspath(__file__))+'/../veh'
pos=np.load(f'{V}/x/ec225/pos/pos_H225.npy').astype(np.float32)[::-1];ok=~np.isnan(pos[...,0]);P=np.nan_to_num(pos)
y,z,nx=P[...,1],P[...,2],P[...,3];side=ok&(np.abs(nx)>0.55)
CY,CZ,RD,RT=5.25,2.05,0.30,0.27          # blue disc radius, ray tip radius (m)
rr=np.hypot(y-CY,z-CZ);ang=np.degrees(np.arctan2(z-CZ,y-CY))%30-15  # angle from the nearest ray axis (rays every 30 deg)
r_sun,r_ring=RT*15/30,RT*17/30
ray=(rr>=r_ring)&(rr<=RT)&(np.abs(ang)<=15*(RT-rr)/(RT-r_ring))
white=side&((rr<r_sun)|ray);blue=side&(rr<RD)&~white
DEEP,WHITE=np.array((28,78,150),float),np.array((226,228,224),float)
for f in sorted(glob.glob(f'{V}/models/m_roc_ec225*_tex0.png')+glob.glob(f'{V}/models/tex_full/m_roc_ec225*_tex0.png')):
    im=Image.open(f);mode=im.mode;a=np.asarray(im.convert('RGBA')).astype(float);H,W=a.shape[:2]
    pick=lambda m:np.asarray(Image.fromarray(m.astype(np.uint8)*255).resize((W,H),Image.NEAREST))>127
    wb,bb=pick(white),pick(blue)
    L=a[...,:3].mean(2);Lb=np.asarray(Image.fromarray(np.clip(L,0,255).astype(np.uint8),'L').filter(ImageFilter.BoxBlur(max(2,W//256)))).astype(float);ratio=np.clip(L/np.maximum(Lb,1),0.7,1.3)[...,None]
    a[...,:3]=np.where(wb[...,None],WHITE*ratio,np.where(bb[...,None],DEEP*ratio,a[...,:3]))
    Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA').convert(mode).save(f);print(os.path.basename(f),W,'white',int(wb.sum()),'blue',int(bb.sum()))
