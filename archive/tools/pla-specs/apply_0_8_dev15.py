"""Freedom Arrow 0.8.0-dev.15 over exact 0.8.0-dev.14 (Osama 12 Nov 15:24 PST, transports):
"The Shaanxi should not be listed as a transprot ... Same with Z-8L and Mi-8 Cargo. CSK-131 mengshi and CSK-131 transport should
be the same id basically. Z-20T is a gunship and shouild be in the Helo tab. Lynx ATV still have their US weapon loadouts,
replace with Chinese weapons please! Please add CSK-181 to Airborne and Marine SOF and Motorized please!"
- Shaanxi HMV3 (1235), Z-8L (1106), Mi-8 Cargo (1227), Z-20T (1245): no longer offered as squad transports (their
  TransportAvailabilities rows are deleted); they stay as their own cards.
- Z-20T: gunship role 73 (as Z-10/Z-19), so it sits in the Helo tab.
- CSK-131: the Transport copy (1229) is merged into CSK-131 Mengshi (900): its squad links are dropped where the Mengshi is
  already offered (or moved to it), and 1229 leaves the roster.
- CSK-181 Transport (1230): also in Air Force/Airborne (17) and Navy/SOF (20); offered to every squad in 17, 20 and 21 that
  already has a ground transport.
- Lynx ATV (1228): Type 86 7.62 mm, QJC-88 12.7 mm and QLZ-87 35 mm AGL in place of the M240, M2 and Mk19 (same mounts and
  mechanics; Chinese MG/HMG ammunition rows, Mk19 grenade copy renamed).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.15'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.14.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native)
U,SA,TA,W,A,WA,T,TU,TW,O=(t[k] for k in ('Units','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson','WeaponsJson','AmmunitionsJson','WeaponAmmunitionsJson','TurretsJson','TurretUnitsJson','TurretWeaponsJson','OptionsJson'))
HMV,Z8L,MI8,Z20T,MENG,CSK131T,CSK181,LYNX=1235,1106,1227,1245,900,1229,1230,1228
assert [U[i]['HUDName'] for i in (HMV,Z8L,MI8,Z20T,MENG,CSK131T,CSK181,LYNX)]==['Shaanxi HMV3','Z-8L','Mi-8 Cargo','Z-20T','CSK-131 Mengshi','CSK-131 Transport','CSK-181 Transport','Lynx ATV']
spec_of=lambda r:SA[r['SpecializationAvailabilityId']]['SpecializationId']
receipt={'version':V,'base':'0.8.0-dev.14','base_sha256':BASE,'request':'Osama 12 Nov 15:24 PST transports','removed_transport_links':{},'csk131_merge':{},'csk181_added':{}}
# 1. not transports
for uid in (HMV,Z8L,MI8,Z20T):
    rows=[r for r in list(TA.values()) if r['UnitId']==uid];receipt['removed_transport_links'][U[uid]['HUDName']]=len(rows)
    for r in rows:g.remove('TransportAvailabilitiesJson',r['Id'])
g.put('Units',Z20T,{'Role':U[1239]['Role']})
# 2. CSK-131 merge
moved=dropped=0
for r in [r for r in list(TA.values()) if r['UnitId']==CSK131T]:
    if any(x['SpecializationAvailabilityId']==r['SpecializationAvailabilityId'] and x['UnitId']==MENG for x in TA.values()):g.remove('TransportAvailabilitiesJson',r['Id']);dropped+=1
    else:g.put('TransportAvailabilitiesJson',r['Id'],{'UnitId':MENG});moved+=1
for r in [r for r in list(SA.values()) if r['UnitId']==CSK131T]:g.remove('SpecializationAvailabilitiesJson',r['Id'])
g.put('Units',CSK131T,{'DisplayInArmory':False})
receipt['csk131_merge']={'links_dropped_duplicate':dropped,'links_moved_to_mengshi':moved}
# 3. CSK-181 in 17, 20, 21
src=next(r for r in SA.values() if r['UnitId']==CSK181 and r['SpecializationId']==21)
for sp in (17,20):
    if not any(r['UnitId']==CSK181 and r['SpecializationId']==sp for r in SA.values()):g.add('SpecializationAvailabilitiesJson',src,{'SpecializationId':sp})
ground={MENG,CSK181,1231,LYNX}
for sp in (17,20,21):
    n=0
    for s in [s for s in SA.values() if s['SpecializationId']==sp and U.get(s['UnitId'],{}).get('Type')==2]:
        links=[r for r in TA.values() if r['SpecializationAvailabilityId']==s['Id']]
        if any(r['UnitId'] in ground or U[r['UnitId']].get('Type')==4 for r in links) and not any(r['UnitId']==CSK181 for r in links):
            g.add('TransportAvailabilitiesJson',links[0],{'SpecializationAvailabilityId':s['Id'],'UnitId':CSK181});n+=1
    receipt['csk181_added'][sp]=n
# 4. Lynx weapons
CN={27:('Type 86 7.62 mm',2009835,'PKT','Type 86 machine gun'),18:('QJC-88 12.7 mm',2009869,'Kord','QJC-88 heavy machine gun'),21:('QLZ-87 35 mm AGL',None,'AGS30_VEH','QLZ-87 grenade launcher')}
agl=g.add('AmmunitionsJson',A[50],{'Name':'PLA Lynx QLZ-87 35 mm','HUDName':'35 mm HE-fragmentation'})
lynx_w={}
for wid,(name,aid,pic,ui) in CN.items():
    nw=g.add('WeaponsJson',W[wid],{'Name':'PLA Lynx '+name,'HUDName':name,'HUDIcon':pic});lynx_w[wid]=(nw,aid or agl,pic,ui)
for r in [r for r in list(WA.values()) if r['UnitId']==LYNX]:
    nw,aid,_,_=lynx_w[r['WeaponId']];g.put('WeaponAmmunitionsJson',r['Id'],{'WeaponId':nw,'AmmunitionId':aid})
for r in [r for r in list(TU.values()) if r['UnitId']==LYNX]:
    old=r['TurretId'];wid=next(x['WeaponId'] for x in TW.values() if x['TurretId']==old);nw,_,pic,ui=lynx_w[wid]
    nt=g.add('TurretsJson',T[old],{'Name':'PLA Lynx '+T[old]['Name'].replace('M1297 GMV ','')});tw=next(x for x in TW.values() if x['TurretId']==old)
    g.add('TurretWeaponsJson',tw,{'TurretId':nt,'WeaponId':nw});g.put('TurretUnitsJson',r['Id'],{'TurretId':nt})
    for o in [o for o in O.values() if any(o.get(f'Turret{i}Id')==old for i in range(21)) and t['ModificationsJson'][o['ModificationId']]['UnitId']==LYNX]:
        g.put('OptionsJson',o['Id'],{**{f'Turret{i}Id':nt for i in range(21) if o.get(f'Turret{i}Id')==old},'UIName':ui,'OptionPicture':pic})
# assignment metadata
n='UserData/FreedomArrow/pla-spec-assignments.json';spec=json.loads(z.read(n))
spec['assignments'][str(CSK131T)]=[];spec['assignments'][str(CSK181)]=[17,19,20,21];spec['shared_transports'][str(CSK181)]=[17,19,20,21]
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in (HMV,Z8L,MI8,Z20T,CSK131T):ok(not any(r['UnitId']==uid for r in TA.values()),('still a transport',uid))
ok(U[Z20T]['Role']==73,'Z-20T gunship role')
ok(not any(r['UnitId']==CSK131T for r in SA.values()),'CSK-131 Transport merged')
ok(sorted(r['SpecializationId'] for r in SA.values() if r['UnitId']==CSK181)==[17,19,20,21],'CSK-181 specs')
for sp in (17,20,21):ok(any(r['UnitId']==CSK181 and spec_of(r)==sp for r in TA.values()),('CSK-181 transport in',sp))
lw=[W[x['WeaponId']]['HUDName'] for x in WA.values() if x['UnitId']==LYNX];ok(sorted(lw)==sorted(v[0] for v in CN.values()),('Lynx weapons',lw))
for r in TU.values():
    if r['UnitId']==LYNX:ok(all(W[x['WeaponId']]['HUDName'] in lw for x in TW.values() if x['TurretId']==r['TurretId']),'Lynx turret weapons')
for r in TA.values():
    sp=spec_of(r)
    if sp>=17:ok(any(s['UnitId']==r['UnitId'] and s['SpecializationId']==sp for s in SA.values()),('carrier crosses spec',r['Id']))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['lynx']={U[LYNX]['HUDName']:lw,'options':[(o['UIName'],o['OptionPicture']) for o in O.values() if t['ModificationsJson'][o['ModificationId']]['UnitId']==LYNX]};receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(n,spec);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))
