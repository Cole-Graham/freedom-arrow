"""J-11 lighter livery (Osama 12 Nov 04:18): J-11BS and J-11BHG use the J-16 model, J-11D the J-16D model,
each on its own lighter copy of the colour texture. Only low-saturation mid/dark-grey paint is lifted; red
markings, roundels, cockpit and very dark parts keep their pixels. J-16/J-16D files are not touched.
.fam references are renamed in place (same length)."""
import argparse,io,json,zipfile
from pathlib import Path
from PIL import Image,ImageChops
OUT=Path(__file__).resolve().parents[2]/'releases/0.6/source/UserData/FAModels'
PAIRS=[('m_j16_cg','m_j11_cg','m_j16_cg_tex0','m_j11_cg_tex0'),('m_j16_lo2','m_j11_lo2','m_j16_lo2_tex0','m_j11_lo2_tex0'),
       ('m_j16d_cg','m_j11d_cg','m_j16d_cg_tex0','m_j11d_cg_tex0'),('m_j16d_lo','m_j11d_lo','m_j16d_lo_tex0','m_j11d_lo_tex0')]
GAIN,OFFSET,CAP=0.9,60,205
def lighten(im):
    im=im.convert('RGBA');rgb=im.convert('RGB');h,s,v=rgb.convert('HSV').split()
    grey=s.point(lambda x:255 if x<22 else max(0,255-(x-22)*20))          # neutral paint only
    mid=v.point(lambda x:0 if x<45 else 255 if x>=60 else (x-45)*17)        # skip very dark parts
    mask=ImageChops.multiply(grey,mid)
    lift=Image.merge('RGB',[c.point(lambda x:min(CAP,int(x*GAIN+OFFSET))) for c in rgb.split()])
    out=Image.composite(lift,rgb,mask).convert('RGBA');out.putalpha(im.getchannel('A'));return out
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);a=p.parse_args()
z=zipfile.ZipFile(a.base);M='UserData/FAModels/'
for model,alias,tex,new in PAIRS:
    assert len(tex)==len(new);fam=z.read(M+model+'.fam');old=(tex+'.png').encode();assert fam.count(old)>0 and (new+'.png').encode() not in fam
    (OUT/(alias+'.fam')).write_bytes(fam.replace(old,(new+'.png').encode()))
    lighten(Image.open(io.BytesIO(z.read(M+tex+'.png')))).save(OUT/(new+'.png'),optimize=True)
    for suf in ['_n.png','_mask.png']:(OUT/(new+suf)).write_bytes(z.read(M+tex+suf))
    mat=json.loads(z.read(M+model+'.mat.json'));(OUT/(alias+'.mat.json')).write_text(json.dumps({k.replace(tex+'.png|',new+'.png|'):v for k,v in mat.items()},indent=2)+'\n')
    print(alias,'refs',fam.count(old))
