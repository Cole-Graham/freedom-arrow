"""Freedom Arrow 0.8.0-dev.22 over exact 0.8.0-dev.21 (Osama 13 Nov 01:24-01:31 PST, thread 1567745029781454889):
- Conscript rifles QBZ-95, QBB-95 and QBU-88: another 30% slower (time between shots / 0.7), on top of Build 61's -30%.
- WZ-8: an RQ-170 Sentinel (its armour, laser/plane ability, sensor, stealth 0.5, size, weight and engine sound) with the
  MiG-31 flight model (mobility row 169: 1260 speed, afterburner, MiG-31 fly preset), 260 points. Name, model and specs kept.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.22'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.21.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U,W,WA,TU,T=t['Units'],t['WeaponsJson'],t['WeaponAmmunitionsJson'],t['TurretUnitsJson'],t['TurretsJson']
name=lambda u:U[u]['HUDName']
for wid,n in ((2012205,'QBZ-95'),(2012207,'QBB-95'),(2012821,'QBU-88')):
    assert W[wid]['HUDName']==n
    g.put('WeaponsJson',wid,{k:round(W[wid][k]/0.7,2) for k in ('TimeBetweenBurstsMin','TimeBetweenBurstsMax')})
WZ8,RQ,MIG=1252,395,315;assert name(WZ8)=='WZ-8' and name(RQ)=='RQ-170 Sentinel' and name(MIG)=='MiG-31BM'
def link(tab,uid,field):
    r=[x for x in t[tab].values() if x['UnitId']==uid];assert len(r)==1,(tab,uid,len(r));return r[0]
for tab,field in (('UnitArmorsJson','ArmorId'),('UnitAbilitiesJson','AbilityId'),('SensorUnitsJson','SensorId')):
    g.put(tab,link(tab,WZ8,field)['Id'],{field:link(tab,RQ,field)[field]})
mob=link('UnitPropulsionsJson',MIG,'MobilityId')['MobilityId'];assert t['MobilityJson'][mob]['IsAfterburner']
g.put('UnitPropulsionsJson',link('UnitPropulsionsJson',WZ8,'MobilityId')['Id'],{'MobilityId':mob})
g.put('Units',WZ8,{k:U[RQ][k] for k in ('Stealth','CurrentStealth','Width','Length','Height','Weight','AudioPreset','TimeModifierResurrect')}|{'Cost':260})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for wid in (2012205,2012207,2012821):ok(abs(W[wid]['TimeBetweenBurstsMin']*0.7-before['WeaponsJson'][wid]['TimeBetweenBurstsMin'])<0.01,('rof',wid))
ok(U[WZ8]['Cost']==260 and U[WZ8]['Stealth']==0.5,'WZ-8 unit')
ok(link('UnitPropulsionsJson',WZ8,'MobilityId')['MobilityId']==mob and t['MobilityJson'][mob]['MaxSpeedRoad']==1260.0,'WZ-8 MiG-31 flight')
for tab,field in (('UnitArmorsJson','ArmorId'),('UnitAbilitiesJson','AbilityId'),('SensorUnitsJson','SensorId')):ok(link(tab,WZ8,field)[field]==link(tab,RQ,field)[field],('WZ-8',tab))
ok(U[WZ8]['ModelFileName']==before['Units'][WZ8]['ModelFileName'] and U[WZ8]['HUDName']=='WZ-8','identity kept')
for tab in t:
    if tab not in ('WeaponsJson','Units','UnitArmorsJson','UnitAbilitiesJson','SensorUnitsJson','UnitPropulsionsJson'):ok(t[tab]==before[tab],('no drift',tab))
receipt={'version':V,'base':'0.8.0-dev.21','base_sha256':BASE,'request':'Osama 13 Nov 01:24-01:31 PST: conscript rifles another -30% RoF; WZ-8 = RQ-170 with MiG-31 flight and afterburner, 260 pts',
 'conscript_rof':{W[w]['HUDName']:[before['WeaponsJson'][w]['TimeBetweenBurstsMin'],W[w]['TimeBetweenBurstsMin']] for w in (2012205,2012207,2012821)},
 'wz8':{'copies':'RQ-170 Sentinel 395 armour/ability/sensor/stealth/size','mobility':mob,'cost':[before['Units'][WZ8]['Cost'],260]},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
