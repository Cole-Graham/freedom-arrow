"""Freedom Arrow 0.8.0-dev.97 over exact 0.8.0-dev.96 (Osama 13 Nov 23:13-23:30 PST, thread 1571014792016171120).
- Frosted fighter canopies (J-5..J-16, Su-30 and others with the vanilla F-16 glass): FAModels 0.3.22 (dev.82) falls back to
  its own clear glass at a fixed 0.3 opacity when the F-16 glass is not loaded, and keeps that material for the session.
  FAModels 0.3.23: the fallback uses 0.025 and the fallback materials are turned into the vanilla F-16 glass in place as soon
  as it can be found (each scene load, and every 10 s by name). Log: FAMODELS_COCKPIT_UPGRADED.
- Z-9 (transport, PLAAF): seller model without the launcher and HJ-8s (m_z9t). Z-9WA gunship and Z-9WA Recon: seller model
  with the weapons (m_z9; were the old m_z9wa).
- PHL-191 Cruise: the opened tube door that stayed in the raised position (F0160176) removed; launcher back behind the cab with
  no rear overhang (m_phl191ch).
- CSK-131 (4x4): body material emissive 1 -> 0 (the seller emission map made it glow white).
- CSK-181 (6x6): flat body normal map (the seller grime/splatter normal made the camo look like scraped bare metal).
"""
import argparse,hashlib,json,sys,zipfile,io
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.97';PREV='0.8.0-dev.96'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
def setm(k,f):
    before[k]=dict(models[k]);e={kk:vv for kk,vv in models[k].items() if kk in ('hide','scale')};models[k]={'file':f+'_static.fam','battle':f+'_lo_static.fam','align':False,**e}
ok(models['PLA Catalogue Z-9']['file']=='m_z9_static.fam','z9');setm('PLA Catalogue Z-9','m_z9t')
for k in ('PLA Z-9WA','PLA Recon Z-9WA'):ok(models[k]['file']=='m_z9wa.fam',k);setm(k,'m_z9')
ok(models['PLA PHL-191 Cruise']['file']=='m_phl191cg_static.fam','cruise');setm('PLA PHL-191 Cruise','m_phl191ch')
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True);files={}
for n in ('m_csk4b_static','m_csk4b_lo_static'):
    k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));hit=0
    for v in mj.values():
        if v.get('emissive') and max(v['emissive'])>0:v['emissive']=[0.0,0.0,0.0];hit+=1
    ok(hit==1,(n,'one glowing material'));f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f)
for n in ('m_csk181_static_tex2_n.png','m_csk181_lo_static_tex2_n.png'):
    k='UserData/FAModels/'+n;ok(k in z.namelist(),n);sz=Image.open(io.BytesIO(z.read(k))).size
    f=gdir/n;Image.new('RGBA',(64,64),(128,128,255,255)).save(f);files[k]=str(f)
rec['csk131_emissive_off']=True;rec['csk181_flat_body_normal']=True
for f in sorted(a.stage.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_z9t','m_phl191ch'):files['UserData/FAModels/'+f.name]=str(f)
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files if ('m_z9t' in k or 'phl191ch' in k)),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json') and ('m_z9t' in k or 'phl191ch' in k)]:
    mj=json.loads(Path(files[k]).read_text());ok(not any(v.get('cockpitDonor') for v in mj.values()),('clear glass',k))
    for key in mj:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,famodels='0.3.23',request='Osama 13 Nov 23:13-23:30 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))
