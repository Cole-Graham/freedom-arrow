"""J-10A livery: repaint the J-10C blue-grey panels as neutral light grey on a separate texture.

Builds 31-36 tinted J-10A with a material colorScale (2.0, 1.5, 1.3) on the shared J-10C
texture. That multiplies red most, so the paint turned salmon/tan, and it also warmed parts
that were already neutral. Here only blue-grey pixels change, on J-10A's own copy of tex1;
J-10C files are not touched. The .fam references are renamed in place (same length).
"""
import argparse,io,json,zipfile
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'releases/0.6/source/UserData/FAModels'
PAIRS=[('m_j10c_cg','m_j10a_grey','m_j10c_cg_tex1','m_j10a_gr_tex1'),('m_j10c_lo2','m_j10a_grey_lo','m_j10c_lo2_tex1','m_j10a_lo2_tex1')]
LIFT,OFFSET,CAP=1.12,8,225

def repaint(im):
    im=im.convert('RGBA');rgb=im.convert('RGB');h,s,_=rgb.convert('HSV').split()
    # Blue-grey paint: hue about 190-255 degrees, low but non-zero saturation.
    hue=h.point(lambda x:255 if 132<=x<=180 else 0)
    sat=s.point(lambda x:0 if x<10 else 255 if 25<=x<=110 else (x-10)*17 if x<25 else max(0,255-(x-110)*8))
    mask=ImageChops.multiply(hue,sat)
    grey=rgb.convert('L').point(lambda x:min(CAP,int(x*LIFT+OFFSET))).convert('RGB')
    out=Image.composite(grey,rgb,mask).convert('RGBA');out.putalpha(im.getchannel('A'))
    return out,mask

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--preview',type=Path);a=p.parse_args()
z=zipfile.ZipFile(a.base);M='UserData/FAModels/';report={}
for src_model,alias,src_tex,new_tex in PAIRS:
    assert len(src_tex)==len(new_tex)
    fam=z.read(M+src_model+'.fam');old=(src_tex+'.png').encode();new=(new_tex+'.png').encode()
    assert fam.count(old)>0 and new not in fam
    (OUT/(alias+'.fam')).write_bytes(fam.replace(old,new))
    im=Image.open(io.BytesIO(z.read(M+src_tex+'.png')));out,mask=repaint(im)
    out.save(OUT/(new_tex+'.png'),optimize=True)
    for suffix in ['_n.png','_mask.png']:
        if M+src_tex+suffix in z.namelist():(OUT/(new_tex+suffix)).write_bytes(z.read(M+src_tex+suffix))
    mat=json.loads(z.read(M+src_model+'.mat.json'));fixed={}
    for key,value in mat.items():
        value.pop('colorScale',None)
        fixed[key.replace(src_tex+'.png|',new_tex+'.png|')]=value
    (OUT/(alias+'.mat.json')).write_text(json.dumps(fixed,indent=2)+'\n')
    hist=mask.histogram();changed=sum(hist[128:])/sum(hist)
    report[alias]={'texture':new_tex+'.png','references_renamed':fam.count(old),'pixels_repainted':round(changed,3)}
    if a.preview and alias=='m_j10a_grey':
        w=512;pv=Image.new('RGB',(w*2+20,w),(255,255,255));pv.paste(im.convert('RGB').resize((w,w)),(0,0));pv.paste(out.convert('RGB').resize((w,w)),(w+20,0));pv.save(a.preview)
print(json.dumps(report,indent=2))
