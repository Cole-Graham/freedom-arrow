"""JRVG-1 look (Osama 12 Nov: "can we remove the camo netting? and then add metallic textures on top of what we have?").

- Camo net: the net is its own material (tex2, alpha BLEND). Its texture becomes fully transparent and the
  material uses an alpha cutout, so the net is not drawn. The mesh is unchanged.
- Metal: the existing mask maps had metallic 0 and smoothness 0.05 (mean R 0, A 14). R (metallic) and A
  (smoothness) are rebuilt at the Black Eagle (vanilla-matched) levels, about R 93 / A 98, varying with the
  colour map's brightness; the existing occlusion (G) is kept. Normal maps are unchanged.
"""
import argparse,io,json,zipfile
from pathlib import Path
from PIL import Image,ImageFilter
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
z=zipfile.ZipFile(a.base);D='UserData/FAModels/';a.out.mkdir(parents=True,exist_ok=True);done=[]
rd=lambda n:Image.open(io.BytesIO(z.read(D+n)))
for lo in ('','lo_'):
    net=rd(f'm_jrvg1_{lo}tex2.png').convert('RGBA');r,g,b,_=net.split()
    Image.merge('RGBA',(r,g,b,Image.new('L',net.size,0))).save(a.out/f'm_jrvg1_{lo}tex2.png');done.append(f'm_jrvg1_{lo}tex2.png')
    for i in (0,1):
        col=rd(f'm_jrvg1_{lo}tex{i}.png').convert('L');old=rd(f'm_jrvg1_{lo}tex{i}_mask.png').convert('RGBA').resize(col.size)
        edge=Image.eval(Image.eval(col.filter(ImageFilter.GaussianBlur(1.2)),lambda v:min(255,v*2)),lambda v:v//6)
        m=Image.merge('RGBA',(Image.eval(edge,lambda v:min(255,85+v)),old.split()[1],Image.new('L',col.size,0),Image.eval(edge,lambda v:min(255,90+v))))
        m.save(a.out/f'm_jrvg1_{lo}tex{i}_mask.png');done.append(f'm_jrvg1_{lo}tex{i}_mask.png')
    n=f'm_jrvg1_{lo}static.mat.json';d=json.loads(z.read(D+n))
    for k,v in d.items():
        v.update(metallic=0.4,smoothness=0.46)
        if '_tex2.png' in k:v.update(alpha='MASK',cutoff=0.5)
    (a.out/n).write_text(json.dumps(d,indent=2)+'\n');done.append(n)
print(done)
