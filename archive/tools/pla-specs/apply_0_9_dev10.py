"""Freedom Arrow 0.9.0-dev.10 data batch over exact 0.9.0-dev.9 (Osama, 14-15 Nov 2026, thread 1567745029781454889).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.10';PREV='0.9.0-dev.9'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
UAB=t['UnitAbilitiesJson'];SAJ=t['SpecializationAvailabilitiesJson']
import copy
SM=t['SquadMembersJson'];SW=t['SquadWeaponsJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];TAJ=t['TransportAvailabilitiesJson']
def members(u):return sorted((m for m in SM.values() if m['UnitId']==u),key=lambda m:m['Id'])
# ---------- Godswords QTS-11 (Osama 15 Nov 2026 07:47 UTC / 23:47 PST: "QTS-11 (only on Godswords), pen to 40mm, rof 50%, damage 1.5
# squad size 12 (6 more QTS-11 too)"). The QTS-11 grenade launcher 2004006 / ammo 2004007 is shared by 31 China squads, so Godswords
# get their own copies: pen 15 -> 40 (both ranges), rate of fire halved (TimeBetweenBursts 1.0 -> 2.0 s), damage 2.5 -> 1.5.
# Squad 6 -> 12, every man with the QTS-11 rifle and grenade launcher.
GW,GA=2004006,2004007
ok(U[1181]['HUDName'].startswith('Godswords'),'Godswords 1181')
gm=members(1181);ok(len(gm)==6 and all(m['PrimaryWeaponId']==2004004 and m['SpecialWeaponId']==GW for m in gm),'Godswords 6 x QTS-11')
ok(W[GW]['TimeBetweenBurstsMin']==1.0==W[GW]['TimeBetweenBurstsMax'] and A[GA]['Damage']==2.5 and A[GA]['PenetrationAtMinRange']==15.0==A[GA]['PenetrationAtGroundRange'],'QTS-11 GL base stats')
nw=g.add('WeaponsJson',W[GW],{'Name':'PLA Godswords QTS-11 grenade launcher','TimeBetweenBurstsMin':2.0,'TimeBetweenBurstsMax':2.0})
na=g.add('AmmunitionsJson',A[GA],{'Name':'PLA Godswords QTS-11 grenade launcher ammunition','PenetrationAtMinRange':40.0,'PenetrationAtGroundRange':40.0,'Damage':1.5})
for m in gm:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':nw})
for i in range(6):g.add('SquadMembersJson',gm[0],{'SpecialWeaponId':nw})
_sw=[r for r in SW.values() if r['UnitId']==1181 and r['WeaponId']==GW];ok(len(_sw)==1,'Godswords GL squad weapon');g.put('SquadWeaponsJson',_sw[0]['Id'],{'WeaponId':nw})
_wa=[r for r in WA.values() if r['UnitId']==1181 and r['WeaponId']==GW];ok(len(_wa)==1 and _wa[0]['AmmunitionId']==GA,'Godswords GL ammo row');g.put('WeaponAmmunitionsJson',_wa[0]['Id'],{'WeaponId':nw,'AmmunitionId':na})
ok(len(members(1181))==12 and all(m['SpecialWeaponId']==nw for m in members(1181)),'Godswords 12 x QTS-11')
ok(sum(1 for m in SM.values() if m['SpecialWeaponId']==GW)>0,'other squads keep the shared launcher')
# A 12-man squad does not fit the ZBD-05 (8 seats): drop that one transport choice. Z-20J becomes 13 below; ZSD-89A and CSK-181 have 12.
_gc=[r for r in TAJ.values() if r['SpecializationAvailabilityId']==2013107];_tr={r['UnitId']:r['Id'] for r in _gc}
ok(sorted(_tr)==[1076,1230,1238,1250] and U[1076]['InfantrySlots']==8,'Godswords transports')
g.remove('TransportAvailabilitiesJson',_tr[1076])
rec['godswords_qts11']={'unit':1181,'squad':[6,12],'weapon':[GW,nw],'ammunition':[GA,na],'penetration':[15,40],'time_between_bursts':[1.0,2.0],'damage':[2.5,1.5],
    'transport_removed':'ZBD-05 1076 (8 seats)'}
# ---------- Z-20 transports 11 -> 13 seats (Osama: "Z-20 all passenger capacity to 13"). Z-20S and Z-20T carry no one.
for _u in (914,1238,1244):ok(str(U[_u]['HUDName']).startswith('Z-20') and U[_u]['InfantrySlots']==11,('Z-20 seats',_u));g.put('Units',_u,{'InfantrySlots':13})
ok(not [u for i,u in U.items() if str(u.get('HUDName','')).startswith('Z-20') and u.get('CountryId')==4 and u.get('InfantrySlots',0) not in (0,13)],'every Z-20 transport 13')
rec['z20_seats']={'units':[914,1238,1244],'seats':[11,13]}
# ---------- 4-man PLAAF teams (Osama: "PLAAF HJ-12 4 man, QLU-11 team 4 man, QW-12 Patrol 4 man, Tank Hunters 4 man (reduce rifle
# count, not special weapons)"). Only plain riflemen (QBZ-191 2003998, no special weapon) are removed, newest first.
_four={}
for _u,_n in ((1137,'HJ-12 Team'),(1140,'QLU-11 Team'),(1145,'QW-12 Patrol'),(1139,'Tank Hunters')):
    ok(U[_u]['HUDName'].startswith(_n),(_n,_u));ms=members(_u);rifle=[m for m in ms if m['PrimaryWeaponId']==2003998 and m['SpecialWeaponId']==0]
    cut=len(ms)-4;ok(0<cut<=len(rifle),(_n,'riflemen to cut',len(ms),len(rifle)))
    keep_weapons=sorted((m['PrimaryWeaponId'],m['SpecialWeaponId']) for m in ms if m not in rifle[len(rifle)-cut:])
    for m in rifle[len(rifle)-cut:]:g.remove('SquadMembersJson',m['Id'])
    ok(len(members(_u))==4 and sorted((m['PrimaryWeaponId'],m['SpecialWeaponId']) for m in members(_u))==keep_weapons,(_n,'4 men, special weapons kept'))
    ok(any(m['PrimaryWeaponId']==2003998 for m in members(_u)) or not rifle,(_n,'rifle row still used'))
    _four[f'{_u} {_n}']=[len(ms),4]
rec['four_man_teams']=_four
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
