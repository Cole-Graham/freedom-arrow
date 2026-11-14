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
g=Graph(t,patches,native);A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];U=t['Units']
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
