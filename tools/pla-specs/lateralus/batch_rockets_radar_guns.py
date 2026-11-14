"""Lateralus 0.8 batch: rocket launcher Ignore Cover/damage changes and radar-gun projectile speed
(Lateralus 13 Nov 2026 23:02 PST, thread 1568104480459722894, message 1571057794273124364).

Applies over any 0.8 complete package (--base). Each change first checks the value it replaces, so a later dev build that
changed the same field stops this script instead of being overwritten. Writes the constants into releases/0.6/source and
tools/pla-specs/lateralus/batch-rockets-radar-guns-checks.json. A dev build then packages them as usual.

Radar guns: the mod's prediction (CramPrediction) and overkill gate (AaCooldown) select guns by data (weapon Type 115, or
114 with IsRadarDependent; ammo TrajectoryType 10, Seeker 0, a projectile target bit). All 27 Chinese units with such a gun
already qualify in 0.8.0-dev.92. The 0.7 rule also gives every projectile-defence gun round MuzzleVelocity 1610; four
Chinese rounds were still at the vanilla 805.
"""
import argparse,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
z=zipfile.ZipFile(a.base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];U=t['Units'];W_=t['WeaponsJson']
# (ammo id, HUD name now, launcher, {field: (from, to)})
ROCKETS=[(130,'66mm HE','M72A10',{'Damage':(6.5,6.0),'IgnoreCover':(0.5,0.25)}),
 (2001500,'66mm HEAT','M72A7',{'IgnoreCover':(0.35,0.0),'HUDName':('66mm HEAT','66mm HEDP')}),
 (121,'105mm HEAT Thermobaric','RMG',{'Damage':(4.0,4.5),'IgnoreCover':(1.0,0.75)}),
 (476,'OG-7V 40mm HE','RPG-7V',{'IgnoreCover':(0.2,0.25)}),
 (906,'TBG-7L Thermobaric','RPG-7V',{'IgnoreCover':(1.0,0.75)}),
 (107,'TBG-7V Thermobaric','RPG-7V2',{'IgnoreCover':(1.0,0.75)}),
 (396,'Thermobaric rocket','RPO-M',{'IgnoreCover':(1.0,0.75)}),
 (524,'RShG-1 Thermobaric','RShG-1',{'IgnoreCover':(1.0,0.75)}),
 (377,'73mm Thermobaric','RShG-2',{'IgnoreCover':(1.0,0.75)}),
 (41,'84mm Thermobaric','SMAW',{'IgnoreCover':(1.0,0.75)}),
 (937,'84mm Thermobaric','SMAW-D HIT',{'IgnoreCover':(1.0,0.75)}),
 # Lateralus wrote "100% -> 25%"; the 0.8 value is 20% (vanilla 20%). Target 25% as asked.
 (525,'OG-9V','SPG-9M',{'IgnoreCover':(0.2,0.25)}),
 (392,'140mm blast-frag','SRAW MPV',{'IgnoreCover':(0.5,0.25)})]
GUNS=[(2009559,932,'PGZ-04A'),(2010643,1050,'PGZ-04'),(2010663,1051,'PGZ-88'),(2010677,1052,'PGZ-95')]
checks=0;rec={'rockets':[],'radar_guns':[]}
def ok(c,l):
    global checks
    assert c,l;checks+=1
for aid,hud,launcher,ch in ROCKETS:
    r=A[aid];ok(r['HUDName']==hud,(aid,r['HUDName']))
    for f,(old,new) in ch.items():ok(r[f]==old,(launcher,aid,f,r[f],old))
    g.put('AmmunitionsJson',aid,{f:new for f,(old,new) in ch.items()})
    for f,(old,new) in ch.items():ok(A[aid][f]==new,(aid,f))
    rec['rockets'].append({'launcher':launcher,'ammo':aid,'hud':hud,'changes':{f:[o,n] for f,(o,n) in ch.items()},
        'units':sorted({U[w['UnitId']]['HUDName'] for w in WA.values() if w['AmmunitionId']==aid and w['UnitId'] in U})})
for aid,uid,name in GUNS:
    users={w['UnitId'] for w in WA.values() if w['AmmunitionId']==aid};ok(users=={uid} and U[uid]['HUDName']==name,(aid,users))
    ok(A[aid]['MuzzleVelocity']==805.0,(aid,A[aid]['MuzzleVelocity']));g.put('AmmunitionsJson',aid,{'MuzzleVelocity':1610.0});ok(A[aid]['MuzzleVelocity']==1610.0,aid)
    rec['radar_guns'].append({'unit':name,'unit_id':uid,'ammo':aid,'MuzzleVelocity':[805.0,1610.0]})
# Lateralus 14 Nov 2026: a disposable never has more than one round per launcher. The PF-97 copied the RPO-M/MRO-Z setup
# (4-round magazine, 4 rounds per carrier); it becomes one tube per soldier. The Russian weapons stay as they are.
PF97=(2004876,2012515);rec['pf97']=[]
for wid in PF97:
    ok(W_[wid]['HUDName']=='PF-97' and W_[wid]['Type']==63 and W_[wid]['MagazineSize']==4,(wid,W_[wid]['MagazineSize']))
    g.put('WeaponsJson',wid,{'MagazineSize':1});ok(W_[wid]['MagazineSize']==1,wid)
for r in [r for r in WA.values() if r['WeaponId'] in PF97]:
    ok(r['Quantity']==4,(r['Id'],r['Quantity']));g.put('WeaponAmmunitionsJson',r['Id'],{'Quantity':1});ok(WA[r['Id']]['Quantity']==1,r['Id'])
    rec['pf97'].append({'unit':U[r['UnitId']]['HUDName'],'unit_id':r['UnitId'],'stock_row':r['Id'],'rounds_per_launcher':[4,1]})
ok(len(rec['pf97'])>=4,rec['pf97'])
# Lateralus 14 Nov 2026: the PF-97 rounds were the MRO-Z napalm (10 s burn, M202 effect). Make them a thermobaric round
# like the RPO-M (also 93 mm): every combat field of RPO-M ammo 396, with damage 5 and Ignore Cover 75%.
SM=t['SquadMembersJson'];SW=t['SquadWeaponsJson']
RPOM=A[396];ok(RPOM['HUDName']=='Thermobaric rocket' and RPOM['DamageOverTimeDuration']==0,'RPO-M ammo')
COPY=('AudioPreset','FXPreset','StressDamage','DamageOverTimeDuration','TargetType','PenetrationAtMinRange','PenetrationAtGroundRange',
      'NoDamageFalloff','TopArmorAttack','IsTopArmorArmorAttack','HealthAOERadius','StressAOERadius','CriticMultiplier','LowAltRange','HighAltRange')
pf_ammo=sorted({r['AmmunitionId'] for r in WA.values() if r['WeaponId'] in PF97});rec['pf97_ammo']=[]
for aid in pf_ammo:
    x=A[aid];ok(x['Damage']==10.0 and x['DamageOverTimeDuration']==10.0 and x['FXPreset']=='AMMUNITION_VFX_PRESET_ROCKET_M202_Flash',(aid,x['Damage']))
    new={k:RPOM[k] for k in COPY};new.update(Damage=5.0,IgnoreCover=0.75);before={k:x[k] for k in new}
    g.put('AmmunitionsJson',aid,new);ok(all(A[aid][k]==v for k,v in new.items()),aid)
    rec['pf97_ammo'].append({'ammo':aid,'changes':{k:[before[k],v] for k,v in new.items() if before[k]!=v}})
ok(len(pf_ammo)>=2,pf_ammo)
# DZT-98 (PF-98A thermobaric): damage 5 -> 4.5, Ignore Cover 100% -> 75%.
DZT=sorted(i for i,x in A.items() if x.get('HUDName')=='DZT-98 thermobaric (analog)');ok(len(DZT)>=1,DZT);rec['dzt98']=[]
for aid in DZT:
    ok(A[aid]['Damage']==5.0 and A[aid]['IgnoreCover']==1.0 and A[aid]['DamageOverTimeDuration']==0,(aid,A[aid]['Damage']))
    g.put('AmmunitionsJson',aid,{'Damage':4.5,'IgnoreCover':0.75});rec['dzt98'].append({'ammo':aid,'Damage':[5.0,4.5],'IgnoreCover':[1.0,0.75]})
# Thunder Gods (1143): one FHJ-02 carrier becomes a plain QBZ-191 rifleman.
TG=1143;FHJ=2013057;QBZ191=2003998
car=sorted(m['Id'] for m in SM.values() if m['UnitId']==TG and m['SpecialWeaponId']==FHJ);ok(len(car)==2 and all(SM[i]['PrimaryWeaponId']==QBZ191 for i in car),car)
g.put('SquadMembersJson',car[-1],{'SpecialWeaponId':0});rec['thunder_gods']={'member':car[-1],'FHJ-02 launchers':[2,1]}
# Combat Engineers (1156): five PF-97 with 1 round each, like the US Combat Engineers' five SMAW-D HIT (2 shotgunners, 3 riflemen).
CE=1156;DZJ=2012024;QBS09=2012131;PFW=2012515
mem={m['Id']:m for m in SM.values() if m['UnitId']==CE};ok(U[CE]['HUDName'].startswith('Combat Engineers') and len(mem)==7,len(mem))
dzj=sorted(i for i,m in mem.items() if m['SpecialWeaponId']==DZJ);shot=sorted(i for i,m in mem.items() if m['PrimaryWeaponId']==QBS09 and not m['SpecialWeaponId'])
rifle=sorted(i for i,m in mem.items() if m['PrimaryWeaponId']==QBZ191 and not m['SpecialWeaponId'])
ok(len(dzj)==2 and len(shot)==2 and len(rifle)==2,(dzj,shot,rifle))
for i in dzj+shot+rifle[:1]:g.put('SquadMembersJson',i,{'SpecialWeaponId':PFW})
for r in [r for r in SW.values() if r['UnitId']==CE and r['WeaponId']==DZJ]:g.remove('SquadWeaponsJson',r['Id'])
for r in [r for r in WA.values() if r['UnitId']==CE and r['WeaponId']==DZJ]:g.remove('WeaponAmmunitionsJson',r['Id'])
sw_tpl=next(r for r in SW.values() if r['WeaponId']==PFW);wa_tpl=next(r for r in WA.values() if r['WeaponId']==PFW)
g.add('SquadWeaponsJson',sw_tpl,{'UnitId':CE,'WeaponId':PFW,'Order':1})
g.add('WeaponAmmunitionsJson',wa_tpl,{'UnitId':CE,'WeaponId':PFW,'AmmunitionId':wa_tpl['AmmunitionId'],'Order':0,'Quantity':1})
ok(sum(1 for m in SM.values() if m['UnitId']==CE and m['SpecialWeaponId']==PFW)==5 and not any(m['SpecialWeaponId']==DZJ for m in SM.values() if m['UnitId']==CE),'CE carriers')
ok([r['Quantity'] for r in WA.values() if r['UnitId']==CE and r['WeaponId']==PFW]==[1] and not [r for r in WA.values() if r['UnitId']==CE and r['WeaponId']==DZJ],'CE ammo')
rec['combat_engineers']={'PF-97 carriers':5,'rounds_per_launcher':1,'DZJ-08':[2,0],'ammo':wa_tpl['AmmunitionId']}
# Every projectile-defence gun round that the prediction and overkill gate select now flies at 1610.
P=128|256|512|1024;W=t['WeaponsJson'];left=[]
for w in WA.values():
    am,wp=A.get(w['AmmunitionId']),W.get(w['WeaponId'])
    if am and wp and w['UnitId'] in U and int(am.get('TargetType') or 0)&P and am.get('TrajectoryType')==10 and am.get('Seeker')==0 \
       and (wp['Type']==115 or (wp['Type']==114 and wp.get('IsRadarDependent'))) and am['MuzzleVelocity']!=1610.0:left.append((w['UnitId'],am['Id']))
ok(not left,left)
rec['checks']=checks;rec['base']=json.loads(z.read('mod.json'))['version']
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(Path(__file__).parent/'batch-rockets-radar-guns-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'base',rec['base'])
