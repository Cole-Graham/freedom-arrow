# Light CAB spec icon from the PLA Special Operations Forces sleeve badge (Osama 26 Nov 2026 15:5x "See the sword with the lightening? I want to
# copy that as our spec icon"): the sword (with its pommel) and the lightning bolt cut from the badge's red band (in/badge.png, 1280x1567),
# drawn in the China spec icon style: one mint colour (228,244,226) like FA_CHINA_NAVAL, sword a shade darker, a cut gap around the bolt,
# transparent elsewhere, 128 px. Source: the Wikimedia Commons PNG of the PLA SOF sleeve badge Osama posted (usage: make_china_light.py BADGE.png);
# with the same top/bottom margin (~8 px) as the other China spec icons.
import sys,numpy as np
from PIL import Image
from scipy import ndimage
b=np.asarray(Image.open(sys.argv[1] if len(sys.argv)>1 else 'in/badge.png').convert('RGB')).astype(int)
x0,x1,y0,y1=500,790,488,1312;c=b[y0:y1,x0:x1];R,G,B=c[...,0],c[...,1],c[...,2]
yy,xx=np.mgrid[y0:y1,x0:x1]
white=(R>215)&(G>215)&(B>215)
yellow=(R>200)&(G>200)&(B<140)
pale=(R>190)&(G>200)&(B>=140)&~white
dark=(R<120)&(G<150)&(B<120)&~((R>180)&(G<80))
leaf_zone=yy>1180;narrow=(xx>598)&(xx<684)
keep=~leaf_zone|narrow
sword=(white|pale)&keep
bolt=yellow&keep
pommel_box=(yy<630)&(xx>595)&(xx<700)
sword|=dark&pommel_box&ndimage.binary_dilation(pale,iterations=4)   # the D pommel's inner lines stay part of the pommel
sword=ndimage.binary_closing(sword,iterations=2);bolt=ndimage.binary_closing(bolt,iterations=2)
gap=ndimage.binary_dilation(bolt,iterations=8)&~bolt
sword&=~gap
lab,n=ndimage.label(sword|bolt);sizes=ndimage.sum(sword|bolt,lab,range(1,n+1));big=np.isin(lab,1+np.flatnonzero(sizes>400))
sword&=big;bolt&=big
BASE=np.array([228,244,226]);SW=BASE*0.80
H,W=c.shape[:2];rgba=np.zeros((H,W,4),float)
rgba[sword,:3]=SW;rgba[sword,3]=1
rgba[bolt,:3]=BASE;rgba[bolt,3]=1
ys,xs=np.nonzero(rgba[...,3]>0);rgba=rgba[ys.min():ys.max()+1,xs.min():xs.max()+1]
h,w=rgba.shape[:2];S=112/h;nw,nh=max(1,round(w*S)),112
pm=rgba.copy();pm[...,:3]*=pm[...,3:4]
im=Image.fromarray((pm*np.array([1,1,1,255])).clip(0,255).astype('uint8'),'RGBA').resize((nw,nh),Image.LANCZOS)
a=np.asarray(im).astype(float);al=a[...,3:4]/255;a[...,:3]=np.where(al>0,a[...,:3]/np.maximum(al,1e-6),0)
im=Image.fromarray(a.clip(0,255).astype('uint8'),'RGBA')
out=Image.new('RGBA',(128,128),(0,0,0,0));out.alpha_composite(im,((128-nw)//2,8));out.save('FA_CHINA_LIGHT.png')   # -> mod/source/runtime-qa/icons/
print('icon',nw,'x',nh,'sword px',int(sword.sum()),'bolt px',int(bolt.sum()))
