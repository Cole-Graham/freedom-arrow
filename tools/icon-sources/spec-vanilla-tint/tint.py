"""Recolour FA spec icons to the vanilla spec-icon look (Osama 23 Nov 17:2x "can you recolor ALL spec icons so they match vanilla color").
Vanilla (SPEC_US_Cavalry / SPEC_RU_Mechanized): flat pale-mint fill RGB ~(228,244,226) + soft dark drop shadow (alpha ~110, down/right).
Each icon keeps its own shape and inner detail: colour = mint x (luminance / the icon's 95th-percentile luminance), then the same drop shadow as
FA_US_BLUE_DRAGON (offset 2,3 px, blur 1.6, 45%). Nation flags (FA_CHINA_FLAG, FA_EUROCORP_FLAG) are not spec icons and stay as flags.
usage: python tint.py ICON_DIR NAME..."""
import sys,numpy as np
from PIL import Image,ImageFilter
D=sys.argv[1];MINT=np.array([228,244,226],np.float32)
for n in sys.argv[2:]:
    p=f'{D}/{n}.png';im=Image.open(p).convert('RGBA');a=np.asarray(im,np.float32)
    A=a[...,3];L=a[...,:3]@np.array([0.299,0.587,0.114],np.float32);op=A>128
    lp=np.percentile(L[op],95);t=np.clip(L/max(lp,1),0,1)[...,None]
    rgb=MINT*t;S=im.size
    fill=Image.fromarray(np.dstack([rgb,A]).round().astype(np.uint8),'RGBA')
    sh=Image.new('L',S,0);sh.paste(Image.fromarray(A.astype(np.uint8)),(2,3));sh=sh.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v:int(v*0.45))
    out=Image.new('RGBA',S,(0,0,0,0));out.alpha_composite(Image.merge('RGBA',[Image.new('L',S,18),Image.new('L',S,20),Image.new('L',S,18),sh]));out.alpha_composite(fill)
    out.save(p);o=np.asarray(out,np.float32);m=o[...,3]>200;print(n,'fill rgb',o[m][:,:3].mean(0).round(0))
