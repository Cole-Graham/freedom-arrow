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
# v2 (Shawn 27 Nov 02:4x "EC225 ... looks like a toy, try your best to enhance the texture quality"): keep the seller's own surface detail
# (panel lines, rivets, grime) as a brightness ratio to its local average, measured inside each old livery colour separately, so the old
# navy / white boundaries leave no halo; plus a cavity darkening from the normal map and exhaust soot behind the engines.
from PIL import ImageFilter
cls=np.where((b>r+25)&(b>g+10),0,np.where((r>g+60)&(r>b+60),1,2))
Lc=0.3*r+0.59*g+0.11*b
def nblur(v,m,rad):
    def k(x):
        x=x.astype(np.float32)
        for ax in (0,1):
            c=np.cumsum(np.pad(x,[(rad+1,rad) if i==ax else (0,0) for i in range(2)],mode='edge'),axis=ax);x=(np.take(c,range(2*rad+1,c.shape[ax]),axis=ax)-np.take(c,range(0,c.shape[ax]-2*rad-1),axis=ax))/(2*rad+1)
        return x
    return k(v*m)/np.maximum(k(m.astype(np.float32)),1e-3)
det=np.ones_like(Lc)
for k_ in range(3):
    mk=(cls==k_)&paint;loc=nblur(Lc,mk,6);det=np.where(mk,np.clip(Lc/np.maximum(loc,1),0.72,1.25),det)
nm=np.asarray(Image.open(f'{TD}/ec225_H225_Normal.png').convert('RGB'),float)/255;tilt=np.sqrt((nm[...,0]-0.5)**2+(nm[...,1]-0.5)**2)*2
cav=np.clip(np.asarray(Image.fromarray((tilt*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)),float)/255*1.6,0,0.45)
col=col*det[...,None]*(1-cav[...,None])
soot=np.clip(1-(y-2.6)/4.0,0,1)*(y>2.6)*(z>2.85)*(z<3.7)*(np.abs(x)>0.45)*0.55*np.clip((np.abs(nx)-0.2)/0.4,0,1)
col=col*(1-soot[...,None])+np.array([28,26,24.0])*soot[...,None]
out=img.copy();out[paint]=col[paint]
Image.fromarray(np.clip(out,0,255).round().astype(np.uint8)).save(f'{OD}/ec225_H225_BaseColor.png')
print('LIVERY painted %.1f%% of the sheet; markings texels: cross disc %d, roundel %d'%(100*paint.mean(),d1.sum(),d2.sum()))
