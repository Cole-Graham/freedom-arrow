"""Freedom Arrow 0.8.0-dev.21 over exact 0.8.0-dev.20 (Osama 13 Nov 00:58-01:09 PST, thread 1567745029781454889,
after the infantry DPS-per-point sheet):
- Prices: PAP Snow Leopards 60 -> 90, Weapons Squad 35 -> 45, AA Troopers 55 -> 60, Beijing Swords 55 -> 70,
  Marine HJ-8 Team 70 -> 55, Godswords 50 -> 90, Taishan Eagles 55 -> 65 (Osama 01:16, after the QTS-11 XM25 change).
- PAP Snow Leopards: 4 DZJ-08 (two more QCW-05 gunners carry one). Falcons: PF-98 instead of PF-89 (in-squad PF-98
  ammunition 6, as Airborne). Mountain Leopards: 3 HJ-12 (every man carries one).
- Blood Wolves CH-901: 12 rounds, 1800 m (900 world), damage 8, penetration 30, interceptable; the squad's default
  ability becomes a laser designator (1800 range, not on the move, like vanilla infantry designators) so it lases its
  own targets.
- PLAAF Tank Hunters: DZT-98 thermobaric rounds 6 -> 10.
- QLU-11 = XM25 Punisher rate of fire and round, out to 1000 m (500 world), 10% slower fire (time between shots and
  reload / 0.9); spread scaled by 500/300 so it is as accurate as the XM25 at the same distance.
- QTS-11 grenade launcher = XM25 Punisher rate of fire and round (300 world). QTS-11 rifle and QLZ-04 unchanged.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.21'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.20.json').read_text())['complete']['sha256']
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
AB,SM,SW=t['AbilitiesJson'],t['SquadMembersJson'],t['SquadWeaponsJson']
name=lambda u:U[u]['HUDName'];wn=lambda w:W[w]['HUDName']
def members(u):return sorted([m for m in SM.values() if m['UnitId']==u],key=lambda m:m['Id'])
def rows(tab,u):return [r for r in t[tab].values() if r.get('UnitId')==u]
PRICE={1182:('PAP Snow Leopards 雪豹',60,90),1199:('Weapons Squad',35,45),1197:('AA Troopers 防空班',55,60),1187:('Beijing Swords 蓝剑',55,70),1193:('Marine HJ-8 Team',70,55),1181:('Godswords 东方神剑',50,90),1203:('Taishan Eagles 泰山雄鹰',55,65)}
for u,(n,old,new) in PRICE.items():assert name(u)==n and U[u]['Cost']==old,(u,U[u]['Cost']);g.put('Units',u,{'Cost':new})
QCW,DZJ,PF89,PF98,HJ12,QBU10,QBZ192=2013349,2012024,2011887,2011832,2011864,2012054,2013087
assert (wn(QCW),wn(DZJ),wn(PF89),wn(PF98),wn(HJ12))==('QCW-05','DZJ-08','PF-89','PF-98','HJ-12')
# Snow Leopards: two more DZJ-08 carriers
plain=[m for m in members(1182) if m['PrimaryWeaponId']==QCW and not m['SpecialWeaponId']];assert len(plain)==3
for m in plain[:2]:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':DZJ})
# Falcons: PF-89 -> PF-98
for m in members(1185):
    if m['SpecialWeaponId']==PF89:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':PF98})
sw=[s for s in rows('SquadWeaponsJson',1185) if s['WeaponId']==PF89];assert len(sw)==1;g.put('SquadWeaponsJson',sw[0]['Id'],{'WeaponId':PF98})
old=[r for r in rows('WeaponAmmunitionsJson',1185) if r['WeaponId']==PF89];assert len(old)==1
g.put('WeaponAmmunitionsJson',old[0]['Id'],{'WeaponId':PF98,'AmmunitionId':WA[2014870]['AmmunitionId'],'Quantity':WA[2014870]['Quantity']})
# Mountain Leopards: everyone carries an HJ-12
for m in members(1186):
    if not m['SpecialWeaponId']:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':HJ12})
# Blood Wolves CH-901 and laser
CHW,CHA=2018447,2018448;assert wn(CHW)=='CH-901' and t['AmmunitionsJson'][CHA]['HUDName']=='CH-901'
r=[r for r in rows('WeaponAmmunitionsJson',1183) if r['WeaponId']==CHW];assert len(r)==1 and r[0]['Quantity']==2;g.put('WeaponAmmunitionsJson',r[0]['Id'],{'Quantity':12})
g.put('AmmunitionsJson',CHA,{'GroundRange':900.0,'Damage':8.0,'PenetrationAtMinRange':30.0,'PenetrationAtGroundRange':30.0,'CanBeIntercepted':True})
bwab=[r['AbilityId'] for r in t['UnitAbilitiesJson'].values() if r['UnitId']==1183];assert bwab==[2013154] and AB[2013154]['IsDefault']
assert {x['UnitId'] for x in t['UnitAbilitiesJson'].values() if x['AbilityId']==2013154}=={1183}
g.put('AbilitiesJson',2013154,{'IsLaserDesignator':True,'LaserMaxRange':1800.0,'LaserUsableInMove':False})
# Tank Hunters DZT-98
assert WA[2014892]['UnitId']==1139 and WA[2014892]['Quantity']==6 and 'DZT-98' in t['AmmunitionsJson'][WA[2014892]['AmmunitionId']]['Name'];g.put('WeaponAmmunitionsJson',2014892,{'Quantity':10})
# XM25 tuning
A=t['AmmunitionsJson'];XW,XA=W[365],A[273];assert XW['HUDName']=='XM25 Punisher' and XA['GroundRange']==300.0
WKEEP={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','Type'};AKEEP={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','FXPreset'}
def as_xm25(wid,aid,rng=300.0,rof=1.0):
    wf={k:copy.deepcopy(v) for k,v in XW.items() if k not in WKEEP}
    for k in ('TimeBetweenBurstsMin','TimeBetweenBurstsMax','MagazineReloadTimeMin','MagazineReloadTimeMax'):wf[k]=round(XW[k]/rof,3)
    g.put('WeaponsJson',wid,wf)
    af={k:copy.deepcopy(v) for k,v in XA.items() if k not in AKEEP};f=rng/XA['GroundRange'];af['GroundRange']=rng
    for k in ('DispersionHorizontalRadius','DispersionVerticalRadius'):af[k]=round(XA[k]*f,3)
    g.put('AmmunitionsJson',aid,af)
assert (wn(2004002),wn(2004006))==('QLU-11','QTS-11 grenade launcher')
as_xm25(2004002,2004003,500.0,0.9);as_xm25(2004006,2004007)
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for u,(n,o,new) in PRICE.items():ok(U[u]['Cost']==new,('price',u))
ok(sum(m['SpecialWeaponId']==DZJ for m in members(1182))==4,'4 DZJ-08')
ok(sum(m['SpecialWeaponId']==HJ12 for m in members(1186))==3,'3 HJ-12')
ok(not any(PF89 in (m['SpecialWeaponId'],m['PrimaryWeaponId']) for m in members(1185)) and any(m['SpecialWeaponId']==PF98 for m in members(1185)),'Falcons PF-98')
for u in (1182,1185,1186,1183,1139):
    carried={m[f] for m in members(u) for f in ('PrimaryWeaponId','SpecialWeaponId') if m[f]}
    ok(carried=={s['WeaponId'] for s in rows('SquadWeaponsJson',u)}=={r['WeaponId'] for r in rows('WeaponAmmunitionsJson',u)},('kit consistent',u))
c=A[CHA];ok((c['GroundRange'],c['Damage'],c['PenetrationAtGroundRange'],c['CanBeIntercepted'],c['LaserGuided'])==(900.0,8.0,30.0,True,True),'CH-901')
ok(AB[2013154]['IsLaserDesignator'] and AB[2013154]['LaserMaxRange']==1800.0,'BW laser')
ok(WA[2014892]['Quantity']==10,'DZT-98 10')
ok(A[2004003]['Damage']==XA['Damage'] and A[2004003]['GroundRange']==500.0 and abs(W[2004002]['TimeBetweenBurstsMin']-XW['TimeBetweenBurstsMin']/0.9)<1e-3,'QLU-11 XM25')
ok(A[2004007]['Damage']==XA['Damage'] and A[2004007]['GroundRange']==300.0 and W[2004006]['MagazineSize']==XW['MagazineSize'],'QTS-11 GL XM25')
ok(W[2004002]['Type']==before['WeaponsJson'][2004002]['Type'] and W[2004006]['Type']==before['WeaponsJson'][2004006]['Type'],'types kept')
changed_tabs={'Units','SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson','AmmunitionsJson','AbilitiesJson','WeaponsJson'}
for tab in t:
    if tab not in changed_tabs:ok(t[tab]==before[tab],('no drift',tab))
receipt={'version':V,'base':'0.8.0-dev.20','base_sha256':BASE,'request':'Osama 13 Nov 00:58-01:09 PST (DPS-per-point follow-up)',
 'prices':{n:[o,new] for u,(n,o,new) in PRICE.items()},'kits':{'PAP Snow Leopards':'4x DZJ-08','Falcons':'PF-98 instead of PF-89','Mountain Leopards':'3x HJ-12'},
 'ch901':{'rounds':12,'range_world':900,'damage':8,'penetration':30,'interceptable':True,'blood_wolves_laser':1800},'dzt98_rounds':[6,10],
 'qlu11':'XM25 round and fire rate, 500 world range, 10% slower, spread x500/300','qts11_gl':'XM25 round and fire rate','checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
