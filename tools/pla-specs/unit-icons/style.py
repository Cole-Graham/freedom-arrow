"""Vanilla-style unit label (416x216, filled + outline) from sil.py output (white body, black Freestyle lines, transparent bg).
Filled: white body with the lines cut through (background shows, as on vanilla labels). Outline: ~3 px contour plus the lines.
Thin parts (antennas, whips) under OPEN icon-pixels are removed at full resolution, then everything is scaled down smoothly."""
from PIL import Image,ImageFilter,ImageChops
import sys
src,name=sys.argv[1],sys.argv[2];maxw=int(sys.argv[3]) if len(sys.argv)>3 else 380;maxh=int(sys.argv[4]) if len(sys.argv)>4 else 180;OPEN=float(sys.argv[5]) if len(sys.argv)>5 else 1.2
im=Image.open(src).convert('RGBA');bb0=im.getbbox();im=im.crop(bb0)
cut=Image.open(sys.argv[6]).convert('L').crop(bb0) if len(sys.argv)>6 else None   # glass/intake areas to cut out of the body
A=im.getchannel('A').point(lambda v:255 if v>127 else 0);Lm=im.convert('L')
lines=ImageChops.multiply(A,Lm.point(lambda v:255 if v<100 else 0))           # black line pixels inside the body
s=min(maxw/im.width,maxh/im.height);k=max(3,int(round(OPEN/s))|1)
body=A.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))     # drop antennas, whips and other hair-thin parts
import os
GAP=int(os.environ.get('GAPFILL','0'))   # close see-through slits up to GAP source px tall (e.g. turret/hull seam), upper part only
if GAP:
    W_,H_=body.size;px=body.load();bb_=body.getbbox();top,bot=bb_[1],bb_[1]+int((bb_[3]-bb_[1])*0.65)
    for x in range(W_):
        y=top;inside=False;gap0=None
        while y<bot:
            v=px[x,y]>127
            if v and gap0 is not None and y-gap0<=GAP:
                for yy in range(gap0,y):px[x,yy]=255
            if v:inside=True;gap0=None
            elif inside and gap0 is None:gap0=y
            y+=1
    for y in range(top,bot):                       # and short horizontal slits (gun barrel segment seams)
        x=0;inside=False;gap0=None
        while x<W_:
            v=px[x,y]>127
            if v and gap0 is not None and x-gap0<=GAP:
                for xx in range(gap0,x):px[xx,y]=255
            if v:inside=True;gap0=None
            elif inside and gap0 is None:gap0=x
            x+=1
if os.environ.get('FILLHOLES'):                    # fill background fully enclosed by the body (e.g. under a gun crossing the hull)
    from PIL import ImageDraw
    pad=Image.new('L',(body.width+2,body.height+2),0);pad.paste(body,(1,1));ImageDraw.floodfill(pad,(0,0),128)
    body=pad.crop((1,1,body.width+1,body.height+1)).point(lambda v:0 if v==128 else 255)
lines=ImageChops.multiply(lines,body.filter(ImageFilter.MinFilter(k)))         # keep only lines well inside the body
if cut is not None:body=ImageChops.subtract(body,cut.point(lambda v:255 if v>127 else 0))
bb=body.getbbox();body=body.crop(bb);lines=lines.crop(bb)
s=min(maxw/body.width,maxh/body.height);w,h=round(body.width*s),round(body.height*s)
B=body.resize((w,h),Image.LANCZOS)
# drop small loose bits (e.g. a periscope that floats once its thin mount is trimmed): keep pieces >= 1.5% of the largest
from collections import deque
bm=B.point(lambda v:255 if v>100 else 0);bp=bm.load();seen=set();parts=[]
for yy in range(h):
    for xx in range(w):
        if bp[xx,yy] and (xx,yy) not in seen:
            q=deque([(xx,yy)]);seen.add((xx,yy));pts=[]
            while q:
                cx,cy=q.popleft();pts.append((cx,cy))
                for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                    nx,ny=cx+dx,cy+dy
                    if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and bp[nx,ny]:seen.add((nx,ny));q.append((nx,ny))
            parts.append(pts)
big_=max((len(p_) for p_ in parts),default=0);Bp=B.load()
for p_ in parts:
    if len(p_)<0.015*big_:
        for (xx,yy) in p_:
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    if 0<=xx+dx<w and 0<=yy+dy<h:Bp[xx+dx,yy+dy]=0
Li=lines.resize((w,h),Image.LANCZOS).point(lambda v:min(255,int(v*2.2)))
def place(m):c=Image.new('L',(416,216),0);c.paste(m,((416-w)//2,198-h));return c
B,Li=place(B),place(Li)
def shadowed(alpha):
    sh=alpha.filter(ImageFilter.GaussianBlur(1.5)).point(lambda v:int(v*0.55))
    out=Image.new('RGBA',(416,216),(0,0,0,0));s_=Image.new('RGBA',(416,216),(0,0,0,0));s_.putalpha(sh)
    out.alpha_composite(s_,(3,3));w_=Image.new('RGBA',(416,216),(255,255,255,0));w_.putalpha(alpha);out.alpha_composite(w_);return out
filled=shadowed(ImageChops.subtract(B,Li))
ring=ImageChops.subtract(B,B.point(lambda v:255 if v>127 else 0).filter(ImageFilter.MinFilter(7)))
outline=shadowed(ImageChops.lighter(ring,Li))
filled.save(f'out/{name}-Label.png');outline.save(f'out/outline_{name}-Label.png')
pv=Image.new('RGBA',(832,216),(60,60,60,255));pv.alpha_composite(filled,(0,0));pv.alpha_composite(outline,(416,0));pv.save(f'out/{name}_preview.png')
print(name,'size',w,h,'filter',k)
