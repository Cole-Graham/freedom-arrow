"""Fit vanilla infantry squad cost from men and weapon classes; apply to PLA squads."""
import json,sys
import numpy as np
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-audit-20261112')
from load import *
from collections import defaultdict
t,z=load(sys.argv[1])
U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];SM=t['SquadMembersJson']
spec=defaultdict(list)
for r in t['SpecializationAvailabilitiesJson'].values():spec[r['UnitId']].append(r['SpecializationId'])
def cls(am,q):
    if am['LowAltRange']>0 and am['GroundRange']==0:return 'manpad'
    if am['Seeker'] in(50,100) and am['ArmorTargeted']==2 and am['PenetrationAtGroundRange']>=100:return 'atgm'
    if am['ArmorTargeted']==2 and am['Seeker']==0 and am['PenetrationAtGroundRange']>=600:return 'heavy_at'
    if am['ArmorTargeted']==2 and am['Seeker']==0 and am['PenetrationAtGroundRange']>=150:return 'light_at'
    if am['ArmorTargeted']==2 and am['HealthAOERadius']>=15 and am['GroundRange']<=300:return 'thermo'
    if am['ArmorTargeted']==2:return 'gl'
    if am['GroundRange']>=500:return 'sniper'
    if am['GroundRange']>=400 and am['Damage']>=1.0:return 'hmg'
    if am['Damage']>=1.8 and q>=300:return 'mg'
    if am['Damage']>=2.5:return 'marksman'
    return None
FEAT=['men','atgm','manpad','heavy_at','light_at','thermo','gl','sniper','hmg','mg','marksman','sf','recon']
def feats(uid):
    men=sum(1 for m in SM.values() if m['UnitId']==uid)
    # carriers per weapon = members holding it
    hold=defaultdict(int)
    for m in SM.values():
        if m['UnitId']!=uid:continue
        for k in ('PrimaryWeaponId','SpecialWeaponId'):
            if m.get(k):hold[m[k]]+=1
    f=defaultdict(float);f['men']=men
    for r in WA.values():
        if r['UnitId']!=uid:continue
        c=cls(A[r['AmmunitionId']],r['Quantity'])
        if c and c not in('mg','marksman') or (c in('mg','marksman') and hold[r['WeaponId']]<=4):
            if c:f[c]+=hold.get(r['WeaponId'],1)
    u=U[uid];f['sf']=1.0 if u['Stealth']<=0.45 else 0.0;f['recon']=1.0 if u['CategoryType']==0 else 0.0
    return [f[k] for k in FEAT],men
X=[];y=[];names=[]
for u in U.values():
    if u['Type']!=2 or u['Id']>=900 or u.get('CountryId') not in (1,2) or u.get('IsUnitModification') or u['Cost']<=0 or u.get('CategoryType') not in (0,1) or any(k in (u['HUDName'] or '') for k in ('Pilot','Crew','Zombie')):continue
    v,men=feats(u['Id'])
    if men<2:continue
    X.append([1]+v);y.append(u['Cost']);names.append(u['HUDName'])
X=np.array(X);y=np.array(y)
WGT=np.array([0,0.35,3,3,2,1,1.5,0.8,3,2,0.7,0.8,3,3])
def knn(v,exclude=None,k=3):
    dd=np.sqrt((((X-np.array([1]+v))*WGT)**2).sum(axis=1))
    if exclude is not None:dd[exclude]=1e9
    idx=np.argsort(dd)[:k];w=1/(dd[idx]+0.5)
    return float((y[idx]*w).sum()/w.sum()),[names[i] for i in idx]
pred=np.array([knn(list(X[i][1:]),exclude=i)[0] for i in range(len(y))]);err=np.abs(pred-y)
coef=np.zeros(X.shape[1])
print('vanilla squads',len(y),'mean abs error',round(err.mean(),1),'median',round(float(np.median(err)),1))
print(dict(zip(['base']+FEAT,[round(c,2) for c in coef])))
out={'coef':dict(zip(['base']+FEAT,[float(c) for c in coef])),'n':len(y),'mae':float(err.mean()),'pla':{}}
d=json.loads(z.read('UserData/FreedomArrow/pla-infantry-designer.json'))
for e in d['entries']:
    uid=e['unit'];u=U.get(uid)
    if not u or not u.get('DisplayInArmory') or not spec[uid] or 22 in spec[uid]:continue
    v,men=feats(uid);p,nb=knn(v);p=max(10,int(round(p/5)*5))
    out['pla'][str(uid)]={'name':u['HUDName'],'old':u['Cost'],'new':p,'features':dict(zip(FEAT,v)),'vanilla_neighbours':nb}
json.dump(out,open(sys.argv[2],'w'),indent=1,ensure_ascii=False)
for k,v in out['pla'].items():print(k,v['name'][:28],v['old'],'->',v['new'],'|',', '.join(x[:18] for x in v['vanilla_neighbours']))
