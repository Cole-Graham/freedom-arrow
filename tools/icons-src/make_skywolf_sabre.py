# Run from work/skywolf-icon-1127 on the deck: python make_skywolf_sabre.py blade 0.55 0.61 -> out_blade_55.png (shipped as FA_PLA_INF_TIANLANG[_OUTLINE].png). Wolf source = the pre-27-Nov approved icon (git show bde3246f:mod/source/runtime-qa/icons/FA_PLA_INF_TIANLANG.png).
# Sky Wolves (天狼) unit icon with a sabre behind the wolf (Osama 27 Nov 2026 22:3x: "make their unit icon smaller and have a sabre in the
# background, its similar to their irl patch and the sabre we use for the spec icon"). Sabre = the sword (and lightning) of the Light CAB spec icon,
# cut from the same PLA SOF sleeve badge as tools/icons-src/make_china_light.py. Wolf = the approved FA_PLA_INF_TIANLANG art, scaled down.
# Same 256x160 canvas and white (240) as the other FA_PLA_INF_* icons; sabre a shade darker with a transparent gap around the wolf.
import sys,numpy as np
from PIL import Image
from PIL import ImageFilter
class ndimage:   # scipy is not available here: binary dilation/erosion with PIL Max/Min filters (square kernel, close enough for masks)
    @staticmethod
    def _f(m,it,f):
        im=Image.fromarray((np.asarray(m)*255).astype('uint8'))
        for _ in range(int(it)):im=im.filter(f(3))
        return np.asarray(im)>127
    @staticmethod
    def binary_dilation(m,iterations=1):return ndimage._f(m,iterations,ImageFilter.MaxFilter)
    @staticmethod
    def binary_erosion(m,iterations=1):return ndimage._f(m,iterations,ImageFilter.MinFilter)
    @staticmethod
    def binary_closing(m,iterations=1):return ndimage.binary_erosion(ndimage.binary_dilation(m,iterations),iterations)
BOLT=sys.argv[1]=='bolt' if len(sys.argv)>1 else True
WS=float(sys.argv[2]) if len(sys.argv)>2 else 0.70
ICON='/home/sam/tars/work/ba-dev/replicas/codex/work/dev3-wt/mod/source/runtime-qa/icons/'
b=np.asarray(Image.open('/home/sam/tars/work/ba-dev/replicas/codex/work/sof-spec-icon-1126/in/badge.png').convert('RGB')).astype(int)
x0,x1,y0,y1=500,790,488,1312;c=b[y0:y1,x0:x1];R,G,B=c[...,0],c[...,1],c[...,2]
yy,xx=np.mgrid[y0:y1,x0:x1]
white=(R>215)&(G>215)&(B>215);yellow=(R>200)&(G>200)&(B<140);pale=(R>190)&(G>200)&(B>=140)&~white
dark=(R<120)&(G<150)&(B<120)&~((R>180)&(G<80))
keep=~(yy>1180)|((xx>598)&(xx<684))
sword=(white|pale)&keep;bolt=yellow&keep
sword|=dark&(yy<630)&(xx>595)&(xx<700)&ndimage.binary_dilation(pale,iterations=4)
sword=ndimage.binary_closing(sword,iterations=2);bolt=ndimage.binary_closing(bolt,iterations=2)
if BOLT:
    gap=ndimage.binary_dilation(bolt,iterations=8)&~bolt;sword&=~gap;shape=sword|bolt
else:
    # blade only: the bolt crosses the blade below the crossguard; fill the blade column there and drop the bolt arms
    Hh=sword.shape[0];rows=np.nonzero(sword.any(1))[0];top=rows.min();tipr=top+int(0.85*(rows.max()-top))
    cols=np.nonzero(sword[tipr])[0];cx=(cols.min()+cols.max())/2
    # blade half-width grows linearly from the tip up to the widest blade row just under the crossguard
    gr=top+int(0.30*(rows.max()-top));gc=np.nonzero(sword[gr])[0]
    shape=sword.copy();ry=np.arange(Hh)
    for y in range(gr,rows.max()+1):
        rc=np.nonzero(sword[y]|bolt[y])[0]
        inner=rc[np.abs(rc-cx)<=max(3,0.5*(cols.max()-cols.min())*(1+(tipr-y)/(tipr-gr)*0.6) if y<tipr else 0.5*(cols.max()-cols.min())+1)] if len(rc) else rc
        if len(inner):shape[y,inner.min():inner.max()+1]=True
    shape[:,:]=shape&~(bolt&~ndimage.binary_dilation(sword,1))|(shape&sword)
ys,xs=np.nonzero(shape);shape=shape[ys.min():ys.max()+1,xs.min():xs.max()+1]
K=4;W,H=256*K,160*K
sh=int(150*K);sw=max(1,round(shape.shape[1]*sh/shape.shape[0]))
sm=np.asarray(Image.fromarray((shape*255).astype('uint8')).resize((sw,sh),Image.LANCZOS)).astype(float)/255
canvas_s=np.zeros((H,W));ox=(W-sw)//2;oy=(H-sh)//2;canvas_s[oy:oy+sh,ox:ox+sw]=sm
wolf=Image.open('wolf_original.png').convert('RGBA');bb=wolf.getbbox();wolf=wolf.crop(bb)
ww,wh=round(wolf.width*K*WS),round(wolf.height*K*WS);wolf=np.asarray(wolf.resize((ww,wh),Image.LANCZOS)).astype(float)/255
canvas_w=np.zeros((H,W));wx=(W-ww)//2;wy=round(H*float(sys.argv[3] if len(sys.argv)>3 else 0.58)-wh/2);canvas_w[wy:wy+wh,wx:wx+ww]=wolf[...,3]
cut=ndimage.binary_dilation(canvas_w>0.25,iterations=3*K)
s=canvas_s*(~cut)
SW=240*0.80
col=(canvas_w*240+s*(1-canvas_w)*SW)/np.maximum(canvas_w+s*(1-canvas_w),1e-6)
al=np.clip(canvas_w+s*(1-canvas_w),0,1)
rgba=np.dstack([col,col,col,al*255]).clip(0,255).astype('uint8')
im=Image.fromarray(rgba,'RGBA').resize((256,160),Image.LANCZOS)
name=f"out_{'bolt' if BOLT else 'blade'}_{int(WS*100)}.png";im.save(name);print(name,im.getbbox())
