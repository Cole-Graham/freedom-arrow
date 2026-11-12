"""ZTQ-62-I PBR layers (Osama 12 Nov: "needs metallic normals, right now it's pastel like because it's from
wargame, look at vanilla to see similar metallic texture layers").

The Wargame rip had only colour maps, metallic 0 and smoothness 0.18. FAModels reads X_n.png (tangent
normal) and X_mask.png (HDRP mask: R metallic, G occlusion, B detail, A smoothness) beside each texture.
Levels follow the Black Eagle conversion that was matched to vanilla tank paint: mask mean R 97, G 248,
A 99 and material factors metallic 0.4 / smoothness 0.46. Normals come from the colour map's luminance
(Sobel), at a mild strength; worn/bright paint edges get slightly more metal and gloss.
"""
import argparse,io,json,zipfile
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
z=zipfile.ZipFile(a.base);D='UserData/FAModels/'
SOBEL_X=ImageFilter.Kernel((3,3),[-1,0,1,-2,0,2,-1,0,1],scale=1,offset=128)
SOBEL_Y=ImageFilter.Kernel((3,3),[-1,-2,-1,0,0,0,1,2,1],scale=1,offset=128)
written=[]
for stem in ['m_ztq62i_tex0','m_ztq62i_tex1','m_ztq62i_lo_tex0','m_ztq62i_lo_tex1']:
    im=Image.open(io.BytesIO(z.read(D+stem+'.png'))).convert('RGBA')
    lum=im.convert('L').filter(ImageFilter.GaussianBlur(1.2))
    lum=Image.eval(lum,lambda v:min(255,v*2))        # dark paint: stretch so relief reads
    gx=lum.filter(SOBEL_X);gy=lum.filter(SOBEL_Y)
    gx=Image.eval(gx,lambda v:max(0,min(255,128+(128-v)//2)));gy=Image.eval(gy,lambda v:max(0,min(255,128+(v-128)//2)))
    nb=Image.new('L',im.size,250)
    n=Image.merge('RGB',(gx,gy,nb));out=a.out/(stem+'_n.png');out.parent.mkdir(parents=True,exist_ok=True);n.save(out);written.append(out.name)
    edge=Image.eval(lum,lambda v:v//6)
    r=Image.eval(edge,lambda v:min(255,85+v));g=Image.new('L',im.size,248);b=Image.new('L',im.size,0);al=Image.eval(edge,lambda v:min(255,90+v))
    m=Image.merge('RGBA',(r,g,b,al));out=a.out/(stem+'_mask.png');m.save(out);written.append(out.name)
for mat in ['m_ztq62i_static.mat.json','m_ztq62i_lo_static.mat.json']:
    d=json.loads(z.read(D+mat))
    for v in d.values():v.update(metallic=0.4,smoothness=0.46)
    (a.out/mat).write_text(json.dumps(d,indent=2)+'\n');written.append(mat)
print(written)
