"""ROC Air Force SAR paint for the EC225 (Shawn 27 Nov 00:2x: "change the texture to fit ROC camo similar to the reference", 2 photos of 2251).
Laid out in 3D from uvpos.py (model: nose -Y, tail +Y, up +Z, sides +-X): sky-blue cabin, dark-blue engine deck and fin cap, white belly and tail boom,
yellow tail-boom band, black nose radome, and on both sides a red cross on a white disc and the ROC roundel (blue disc, white sun) behind it.
Only painted texels change (the seller's blue / white / red livery colours); glass, rotors, interior, metal and dark parts keep theirs. Panel detail
comes from the seller's AO and normal maps in game; a faint noise keeps the paint from looking flat. usage: python livery_ec225.py TEXDIR POSDIR OUTDIR"""
import sys,os,shutil,math,numpy as np
from PIL import Image
TD,PD,OD=sys.argv[1:4];os.makedirs(OD,exist_ok=True)
for f in os.listdir(TD):
    if not f.endswith('_BaseColor.png'):shutil.copy(os.path.join(TD,f),OD)
img=np.asarray(Image.open(f'{TD}/ec225_H225_BaseColor.png').convert('RGB'),float);H,W,_=img.shape
pos=np.load(f'{PD}/pos_H225.npy').astype(np.float32)[::-1];ok=~np.isnan(pos[...,0]);P=np.nan_to_num(pos)
x,y,z,nx=P[...,0],P[...,1],P[...,2],P[...,3]
r,g,b=img[...,0],img[...,1],img[...,2];L=img.mean(2);sat=img.max(2)-img.min(2)
paint=ok&(((b>r+25)&(b>g+10))|((L>140)&(sat<45))|((r>g+60)&(r>b+60)))     # seller's navy, white and red livery
SKY,DEEP,WHITE,YEL,BLK,RED=[np.array(c,float) for c in ((72,168,222),(28,78,150),(226,228,224),(232,184,30),(30,30,32),(196,30,36))]
col=np.empty_like(img);col[:]=WHITE
cabin=(y<5.0)&(z>1.0);col[cabin]=SKY
col[(y<6.6)&(z>2.75)]=DEEP                                 # engine deck and gearbox cowling
col[(y>10.3)&(z>3.9)]=DEEP                                 # fin cap
col[(y>8.9)&(y<9.35)&(z<3.6)]=YEL                         # tail-boom band
col[(y<-3.9)&(z<1.75)]=BLK                                # nose radome
# side markings: red cross on a white disc (y 4.45, behind the last window) and the ROC roundel (y 5.25), 0.30 m radius, centre height 2.05 m, on side-facing texels
side=np.abs(nx)>0.55
def disc(cy,cz,rad):return side&(((y-cy)**2+(z-cz)**2)<rad**2)
d1=disc(4.45,2.05,0.30);col[d1]=WHITE
arm=0.07;cr=d1&(((np.abs(y-4.45)<arm)&(np.abs(z-2.05)<0.22))|((np.abs(z-2.05)<arm)&(np.abs(y-4.45)<0.22)));col[cr]=RED
d2=disc(5.25,2.05,0.30);col[d2]=DEEP
ang=np.arctan2(z-2.05,y-5.25);rr=np.sqrt((y-5.25)**2+(z-2.05)**2)
sun=d2&((rr<0.11)|((rr<0.25)&(np.cos(12*ang)>0.35)))      # white sun with 12 rays
col[sun]=WHITE
rng=np.random.default_rng(5);nz=np.asarray(Image.fromarray(rng.normal(0,1,(H//32,W//32)).astype(np.float32),'F').resize((W,H),Image.BICUBIC))   # smooth, no blocks
col=col*(1+0.015*nz[...,None])
out=img.copy();out[paint]=col[paint]
Image.fromarray(np.clip(out,0,255).round().astype(np.uint8)).save(f'{OD}/ec225_H225_BaseColor.png')
print('LIVERY painted %.1f%% of the sheet; markings texels: cross disc %d, roundel %d'%(100*paint.mean(),d1.sum(),d2.sum()))
