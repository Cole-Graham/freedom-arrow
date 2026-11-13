"""HJ-10 (Red Arrow 10B) weapon icon, side profile drawn to the proportions of Osama's reference photo
(Discord 1570919354122633287): blunt seeker dome, body length 13x diameter, 4 long-chord mid wings at 40-58% of length,
4 small tail fins at 80-88%, dark mid band. Nose left and PL-17/PL-21 icon style (fill 232,255,234 on 234x90, outline copy)."""
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage
S=8;Wc,Hc=234*S,90*S;L=212*S;x0=(Wc-L)//2;cy=Hc//2;r=int(L/13/2)
def X(f):return x0+int(f*L)
def draw(img):
    d=ImageDraw.Draw(img)
    d.ellipse([X(0),cy-r,X(0)+2*r,cy+r],fill=255)                      # seeker dome
    d.rectangle([X(0)+r,cy-r,X(0.985),cy+r],fill=255)                  # body
    d.rectangle([X(0.985),cy-int(r*0.8),X(1.0),cy+int(r*0.8)],fill=255) # nozzle
    for sgn in (-1,1):                                                 # mid wings: swept leading edge, straight trailing edge
        root0,root1,tip0,tip1,span=0.40,0.585,0.49,0.575,int(0.085*L)
        d.polygon([(X(root0),cy+sgn*r),(X(tip0),cy+sgn*(r+span)),(X(tip1),cy+sgn*(r+span)),(X(root1),cy+sgn*r)],fill=255)
        f0,f1,ft0,ft1,fs=0.80,0.885,0.84,0.885,int(span*0.55)         # tail control fins
        d.polygon([(X(f0),cy+sgn*r),(X(ft0),cy+sgn*(r+fs)),(X(ft1),cy+sgn*(r+fs)),(X(f1),cy+sgn*r)],fill=255)
    return img
m=np.asarray(draw(Image.new('L',(Wc,Hc),0)))>127
cut=np.zeros_like(m)                                                  # panel lines: dome joint and the dark mid band edges
for f in (0.075,0.385,0.60):cut[:,X(f)-S//2*2:X(f)+S//2*2]=True
cut&=ndimage.binary_erosion(m,iterations=2*S)
FILL=(232,255,234)
def save(alpha,name):
    rgba=np.zeros((Hc,Wc,4),np.uint8);rgba[...,:3]=FILL;rgba[...,3]=alpha*255
    Image.fromarray(rgba).resize((234,90),Image.LANCZOS).save(name)
save(m&~cut,'FA_PLA_HJ10.png')
save(m&~ndimage.binary_erosion(m,iterations=int(1.6*S)),'FA_PLA_HJ10_OUTLINE.png')
