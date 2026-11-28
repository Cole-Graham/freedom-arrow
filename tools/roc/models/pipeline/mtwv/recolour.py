"""MTWV base paint (Shawn 28 Nov 03:4x: "plain green camo similar to vanilla MTV as base paint"). The Navistar 7400 pack is a white civilian
cab (NI_Cabin) on a black frame. Paint = low-saturation pixels: white/light grey on the cab, mid grey on equipment; they become olive
drab (66, 72, 48) keeping their shading (luminance ratio). Black rubber, glass-black, rust/dirt (saturated) stay. The vanilla MTV sheet
(MTV_BaseColor1: grey panels + dirt, its paint colour comes from the game's layered shader) gets the same olive on its grey panels.
usage: python recolour.py   (writes tex/*_BaseColor.png)"""
import numpy as np
from PIL import Image
T='../../../dl12/files/Textures_UE';G=np.array([66,72,48],np.float32)
E='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_MTV/tex/MTV_BaseColor1_21092.png'
def paint(src,dst,lo,ref,keep_dark=25,size=None):
    im=Image.open(src).convert('RGBA');im=im.resize((size,size),Image.LANCZOS) if size else im
    a=np.asarray(im).astype(np.float32);rgb=a[...,:3];L=rgb.mean(2);mx,mn=rgb.max(2),rgb.min(2);sat=(mx-mn)/np.maximum(mx,1)
    w=np.clip((0.22-sat)/0.10,0,1)*np.clip((L-lo)/20,0,1)*np.clip((L-keep_dark)/15,0,1)
    out=G*np.clip(L/ref,0.25,1.35)[...,None]
    a[...,:3]=rgb*(1-w[...,None])+out*w[...,None]
    Image.fromarray(a.clip(0,255).round().astype(np.uint8),'RGBA').convert('RGB').save(dst);print(dst,'painted %.0f%%'%(100*(w>0.5).mean()))
paint(f'{T}/NI_Cabin_BaseColor.jpg','tex/NI_Cabin_BaseColor.png',120,215,size=2048)
paint(f'{T}/NI_Equipment_BaseColor.jpg','tex/NI_Equipment_BaseColor.png',18,70,keep_dark=10,size=2048)
paint(f'{T}/NI_Frame_BaseColor.jpg','tex/NI_Frame_BaseColor.png',14,70,keep_dark=8,size=2048)
paint(E,'tex/MTV_Bed_BaseColor.png',40,110)
