"""Freedom Arrow 0.8.0-dev.84 over exact 0.8.0-dev.83 (Osama 13 Nov 21:00-21:14 PST, thread 1571014792016171120).
- ZBD-20 (945): seller VN-17 model, woodland digital ("I just downloaded VN-17 this will be used for the ZBD-20").
- Recon cards in desert digital, non-recon green ("ZBD-04A recon should be desert camo, same with ZBD-20"):
  ZBD-20 Recon (1256) and ZBD-04A Recon (1255) get their own unit Names (the model loader keys by Name) and the
  seller Dust_Camo sets (m_vn17d, m_zbd04d). ZBD-20 and ZBD-04A stay woodland.
- Marine HJ-8 Team (1193, PLAN Navy/SOF) -> "Marine HJ-8H Team": its launcher becomes HJ-8H, a copy of the Kornet-M
  launcher (665) and 9M133M-2 missile (2000160) with the Kornet icons and the Kornet-M team cost (70). New rows, so the
  other squads that share the HJ-8E launcher are unchanged. The PLA soldiers and rifles stay.
- Display names: HQ-12 (was "HQ-12 / KS-1"), PCL-181 (was "PCL-181 / SH-15").
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.84';PREV='0.8.0-dev.83'
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
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];SW=t['SquadWeaponsJson'];SM=t['SquadMembersJson'];WA=t['WeaponAmmunitionsJson'];rows=g.rows
checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
names={u.get('Name') for u in U.values()}
# Recon cards get their own Names
ren={}
for uid,old,hud,new in ((1255,'PLA ZBD-04A','ZBD-04A Recon','PLA ZBD-04A Recon'),(1256,'PLA ZBD-20','ZBD-20 Recon','PLA ZBD-20 Recon')):
    ok(U[uid]['Name']==old and U[uid]['HUDName']==hud and new not in names and uid not in native['Units'],(uid,U[uid]['Name'],U[uid]['HUDName']))
    g.put('Units',uid,{'Name':new});ren[uid]=[old,new]
ok(U[902]['Name']=='PLA ZBD-04A' and U[945]['Name']=='PLA ZBD-20','parents keep their Names')
rec['renamed']=ren
# HUD names
for uid,old,new in ((1047,'HQ-12 / KS-1','HQ-12'),(1034,'PCL-181 / SH-15','PCL-181')):
    ok(U[uid]['HUDName']==old,(uid,U[uid]['HUDName']));g.put('Units',uid,{'HUDName':new})
rec['hud']={'1047':['HQ-12 / KS-1','HQ-12'],'1034':['PCL-181 / SH-15','PCL-181']}
# HJ-8H
T=1193;ok(U[T]['HUDName']=='Marine HJ-8 Team' and U[T]['Cost']==55,'marine hj-8 team')
sw=[r for r in SW.values() if r['UnitId']==T and r['WeaponId']==2012264];ok(len(sw)==1,'one HJ-8E squad weapon')
mem=[m for m in SM.values() if m['UnitId']==T and m.get('SpecialWeaponId')==2012264];ok(len(mem)==1,'one HJ-8E gunner')
wa=[r for r in WA.values() if r.get('UnitId')==T and r['WeaponId']==2012264];ok(len(wa)==1 and wa[0]['AmmunitionId']==2012265,'one HJ-8E ammo row')
ok(W[665]['HUDName']=='Kornet-M' and A[2000160]['HUDName']=='9M133M-2','kornet-m rows')
nw=g.add('WeaponsJson',W[665],{'Name':'PLA Marine HJ-8H','HUDName':'HJ-8H'})
na=g.add('AmmunitionsJson',A[2000160],{'Name':'PLA Marine HJ-8H missile','HUDName':'HJ-8H'})
g.put('SquadWeaponsJson',sw[0]['Id'],{'WeaponId':nw});g.put('SquadMembersJson',mem[0]['Id'],{'SpecialWeaponId':nw})
kq=[r for r in WA.values() if r.get('UnitId')==460 and r['WeaponId']==665][0]['Quantity']
g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':nw,'AmmunitionId':na,'Quantity':kq})
g.put('Units',T,{'HUDName':'Marine HJ-8H Team','ThumbnailFileName':U[460]['ThumbnailFileName'],'Cost':U[460]['Cost'],'OriginalCost':U[460].get('OriginalCost',U[460]['Cost'])})
for k in W[665]:
    if k not in ('Id','Name','HUDName'):ok(W[nw].get(k)==W[665].get(k),('weapon field',k))
for k in A[2000160]:
    if k not in ('Id','Name','HUDName'):ok(A[na].get(k)==A[2000160].get(k),('ammo field',k))
ok(sum(1 for r in SW.values() if r['WeaponId']==2012264)>=5,'other squads keep HJ-8E')
rec['hj8h']={'unit':T,'weapon':nw,'ammo':na,'icon':W[nw].get('HUDIcon'),'thumbnail':U[T]['ThumbnailFileName'],'cost':[55,U[T]['Cost']],'missiles':kq,'damage':A[na].get('Damage')}
# models.json
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
for k,f in (('PLA ZBD-20','m_vn17s'),('PLA ZBD-20 Recon','m_vn17d'),('PLA ZBD-04A Recon','m_zbd04d')):
    before[k]=models.get(k);models[k]={'file':f+'_static.fam','battle':f+'_lo_static.fam','align':False}
ok(models['PLA ZBD-04A']['file']=='m_zbd04_camo_static.fam','ZBD-04A stays woodland')
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_vn17s','m_vn17d','m_zbd04d')}
ok(len([k for k in files if k.endswith('.fam')])==6,('fams',sorted(files)))
ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    for key in json.loads(Path(files[k]).read_text()):
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:00-21:14 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['hj8h']))
