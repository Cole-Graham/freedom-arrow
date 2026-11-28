"""EC225 roundel from the official emblem (Shawn 27 Nov 19:2x: "use it [QTBR] to replace EC225 roundel", link to Wikimedia Commons
National_Emblem_of_the_Republic_of_China.svg): the SVG's own geometry, drawn per texel on both sides (side-facing texels, centre y 5.25 m,
z 2.05 m, disc radius 0.30 m = 22.5 SVG units): blue disc #000095 (r 22.5); 12 rays = the horizontal and vertical rhombi
(15 x 4 units) and their 30 and 60 degree turns, white; white sun disc r 8 with a blue ring (stroke 1, r 7.5-8.5). One ray points up.
Replaces the roc7 roundel inside the disc; the texture's panel detail stays (brightness ratio to its local average).
Originals of this step go to veh/x/ec225/pre-qtbr/. usage: python ec225_qtbr.py"""
import os,glob,shutil,numpy as np
from PIL import Image,ImageFilter
V=os.path.dirname(os.path.abspath(__file__))+'/../veh';BK=V+'/x/ec225/pre-qtbr'
pos=np.load(f'{V}/x/ec225/pos/pos_H225.npy').astype(np.float32)[::-1];ok=~np.isnan(pos[...,0]);P=np.nan_to_num(pos)
y,z,nx=P[...,1],P[...,2],P[...,3];side=ok&(np.abs(nx)>0.55)
CY,CZ,RD=5.25,2.05,0.30;k=22.5/RD
ex,ey=(z-CZ)*k,-(y-CY)*k
def rhombi(x,y):return (np.abs(x)/15+np.abs(y)/4<=1)|(np.abs(x)/4+np.abs(y)/15<=1)
def emblem(ex,ey):   # 0 outside, 1 blue, 2 white
    r=np.hypot(ex,ey);ray=np.zeros_like(r,bool)
    for d in (0,30,60):
        c,s_=np.cos(np.radians(d)),np.sin(np.radians(d));ray|=rhombi(c*ex+s_*ey,-s_*ex+c*ey)
    return np.where(r>22.5,0,np.where((ray&(r>8.5))|(r<7.5),2,1))
# 4x4 supersampling: the texel position field is smooth on the side panels, so it is upsampled bilinearly
ys_,xs_=np.where(side&(np.hypot(ex,ey)<26));y0,y1,x0,x1=ys_.min()-2,ys_.max()+3,xs_.min()-2,xs_.max()+3
up=lambda f:np.asarray(Image.fromarray(f[y0:y1,x0:x1].astype(np.float32),'F').resize(((x1-x0)*4,(y1-y0)*4),Image.BILINEAR))
E=emblem(up(ex),up(ey));cov=lambda v:(E==v).reshape(y1-y0,4,x1-x0,4).mean((1,3))
cw,cb=np.zeros(ex.shape),np.zeros(ex.shape);cw[y0:y1,x0:x1]=cov(2);cb[y0:y1,x0:x1]=cov(1);cw*=side;cb*=side
BLUE,WHITE=np.array((0,0,149),float),np.array((232,232,228),float)
for f in sorted(glob.glob(f'{V}/models/m_roc_ec225*_tex0.png')+glob.glob(f'{V}/models/tex_full/m_roc_ec225*_tex0.png')):
    b=f'{BK}/{f.replace(V+"/models/","").replace("/","_")}'
    if not os.path.exists(b):shutil.copy(f,b)
    im=Image.open(b);mode=im.mode;a=np.asarray(im.convert('RGBA')).astype(float);H,W=a.shape[:2]
    rs=lambda m:np.asarray(Image.fromarray(m.astype(np.float32),'F').resize((W,H),Image.BILINEAR))[...,None]
    w_,b_=rs(cw),rs(cb)
    a[...,:3]=a[...,:3]*(1-w_-b_)+WHITE*w_+BLUE*b_   # flat decal paint (the roc7 roundel under it must not show through)
    Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA').convert(mode).save(f);print(os.path.basename(f),W,'white %.0f blue %.0f texels'%(w_.sum(),b_.sum()))
