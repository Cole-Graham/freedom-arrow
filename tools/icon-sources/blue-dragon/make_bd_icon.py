"""Blue Dragon spec icon from Osama's dragon silhouette (23 Nov 17:0x "use this to make the Blue dragons icon and make sure the icon matches the
vanilla icon colors", then "actually lets use this one" = dl/src2.png). Vanilla spec icons (SPEC_US_Cavalry / SPEC_RU_Mechanized, bars-icon/x) are a
flat pale-mint fill RGB ~(228,244,226) with a soft dark drop shadow (alpha ~110, offset down/right). Same here, 128x128 like the other FA spec icons."""
from PIL import Image,ImageFilter;import numpy as np,sys
src=Image.open('dl/src2.png').convert('L');a=np.asarray(src)
m=a<110
H,W=m.shape;m[:4,:]=m[-4:,:]=False;m[:,:4]=m[:,-4:]=False   # screenshot border lines
ys,xs=np.nonzero(m);m=m[ys.min():ys.max()+1,xs.min():xs.max()+1]
S=128;pad=6;h,w=m.shape;sc=(S-2*pad)/max(h,w)
big=Image.fromarray((m*255).astype(np.uint8)).resize((max(1,round(w*sc*4)),max(1,round(h*sc*4))),Image.LANCZOS)
mask=big.resize((round(w*sc),round(h*sc)),Image.LANCZOS)
canvas=Image.new('L',(S,S),0);canvas.paste(mask,((S-mask.width)//2,(S-mask.height)//2))
sh=Image.new('L',(S,S),0);sh.paste(canvas,(2,3));sh=sh.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v:int(v*0.45))
out=Image.new('RGBA',(S,S),(0,0,0,0))
out.alpha_composite(Image.merge('RGBA',[Image.new('L',(S,S),18),Image.new('L',(S,S),20),Image.new('L',(S,S),18),sh]))
fill=Image.new('RGBA',(S,S),(228,244,226,255));fill.putalpha(canvas);out.alpha_composite(fill)
out.save('FA_US_BLUE_DRAGON.png')
prev=Image.new('RGBA',(96*3*3+128*3+40,300),(40,46,52,255))
for i,f in enumerate(['../bars-icon/x/SPEC_US_Cavalry_2835.png','../bars-icon/x/SPEC_RU_Mechanized_3886.png']):prev.alpha_composite(Image.open(f).convert('RGBA').resize((288,288)),(i*300,6))
prev.alpha_composite(out.resize((288,288),Image.LANCZOS),(620,6));prev.alpha_composite(out,(930,80));prev.save('preview.png')
o=np.asarray(out,np.float32);op=o[...,3]>200;print('opaque',op.mean().round(3),'rgb',o[op][:,:3].mean(0).round(0))
