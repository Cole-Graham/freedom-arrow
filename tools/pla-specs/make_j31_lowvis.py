"""J-31 low-vis model (Osama 12 Nov 03:57): the J-35 model (m_j35n_fixed) with the source pack's default
texture, which has no Chinese writing, star bars or wing art. The navy paint was applied on top of that
default texture on 9 Nov; the saved pre-navy textures are that default. Only the colour texture differs;
normal and mask maps, canopy and cockpit textures are shared. .fam references are renamed in place (same length)."""
import argparse,io,json,zipfile,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/'releases/0.6/source/UserData/FAModels'
PAIRS=[('m_j35n_fixed','m_j31_lowvis','m_j35n_fixed_tex0','m_j31_lowvis_tex0'),('m_j35n_fixed_lo','m_j31_lowvis_lo','m_j35n_fixed_lo_tex0','m_j31_lowvis_lo_tex0')]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--pre-navy',type=Path,required=True);a=p.parse_args()
z=zipfile.ZipFile(a.base);M='UserData/FAModels/';rec=[]
for model,alias,tex,new in PAIRS:
    assert len(tex)==len(new)
    fam=z.read(M+model+'.fam');old=(tex+'.png').encode();assert fam.count(old)>0 and (new+'.png').encode() not in fam
    (OUT/(alias+'.fam')).write_bytes(fam.replace(old,(new+'.png').encode()))
    src=(a.pre_navy/(tex+'.png')).read_bytes();(OUT/(new+'.png')).write_bytes(src)
    for suf in ['_n.png','_mask.png']:(OUT/(new+suf)).write_bytes(z.read(M+tex+suf))
    mat=json.loads(z.read(M+model+'.mat.json'));(OUT/(alias+'.mat.json')).write_text(json.dumps({k.replace(tex+'.png|',new+'.png|'):v for k,v in mat.items()},indent=2)+'\n')
    rec.append({'alias':alias,'from':model,'colour_texture_sha256':hashlib.sha256(src).hexdigest(),'fam_refs_renamed':fam.count(old)})
print(json.dumps(rec,indent=1))
