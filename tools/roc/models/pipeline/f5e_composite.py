"""F-5E (Shawn 27 Nov 19:4x, his F-5E_Land.blend): the hull material is a node mix that a GLB cannot carry - the colour map, the panel-line
map laid over it (overlay, 0.5) and the dirt map (black, its alpha = dirt). Bakes that mix into one colour map at 4096 (the Arsenal limit
is 2048), plus a normal map from the panel lines (the material's Bump on the lines). usage: python f5e_composite.py"""
import os,numpy as np
from PIL import Image,ImageFilter
Image.MAX_IMAGE_PIXELS=None
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/x/f5e';S=4096
hull=np.asarray(Image.open(D+'/src/F-5E-Main_Hull.png').convert('RGB').resize((S,S),Image.LANCZOS)).astype(np.float32)/255
lines=np.asarray(Image.open(D+'/src/F-5E-Lines.png').convert('L').resize((S,S),Image.LANCZOS)).astype(np.float32)/255
dirt=np.asarray(Image.open(D+'/src/F-5E-Dirty.png').convert('RGBA').resize((S,S),Image.LANCZOS)).astype(np.float32)[...,3]/255
L=lines[...,None];ov=np.where(hull<0.5,2*hull*L,1-2*(1-hull)*(1-L));out=hull*0.5+ov*0.5   # overlay at 0.5
out=out*(1-0.35*dirt[...,None])
Image.fromarray((out.clip(0,1)*255+0.5).astype(np.uint8)).save(D+'/tex/f5e_hull.png')
h=np.asarray(Image.fromarray((lines*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)/255
gx=np.roll(h,-1,1)-np.roll(h,1,1);gy=np.roll(h,-1,0)-np.roll(h,1,0);k=4.0
n=np.dstack([-gx*k,gy*k,np.ones_like(h)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
Image.fromarray(((n*0.5+0.5)*255+0.5).astype(np.uint8)).save(D+'/tex/f5e_hull_n.png')
print('dirt mean %.3f lines mean %.3f'%(dirt.mean(),lines.mean()),'->',D+'/tex')
