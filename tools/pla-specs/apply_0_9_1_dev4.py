"""Freedom Arrow 0.9.1-dev.4 data over exact 0.9.1-dev.3 (19 Nov 2026). Opened by BA Codex thread 1572962048705429598 (Lateralus 12:2x PST batch:
MANPAD team prices, CSK-131 Recon, recon/scout vehicle optics). 0.9.1-dev.3 (build 228) was art only, so its data equals 0.9.1-dev.2.
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.1-dev.4';PREV='0.9.1-dev.3'
# 0.9.1-dev.3 was built in out/local-091dev3.
BASE=json.loads((REL/f'out/local-091dev3/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-091dev3/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];S=t['SensorsJson'];SU=t['SensorUnitsJson'];SA=t['SpecializationAvailabilitiesJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def r5(x):return int((Decimal(str(x))/5).quantize(Decimal(1),rounding=ROUND_HALF_UP))*5
# ---------- 1. Infantry MANPAD teams cheaper (Lateralus 19 Nov 2026 12:2x PST, thread 1572962048705429598: "Lower the price of infantry MANPAD teams which
# only carry 1 launcher by 15%, and ... 2 launchers by 10% (rounded to the nearest 5)"; 12:4x: "You also forgot some infantry, like QW-12 Patrol, STT,
# Spetsnaz GRU, and maybe some more"). The teams are every infantry card in the Arsenal (rows with squad members, Infantry and Recon tabs) whose members
# carry a guided air-target weapon; launchers = members carrying one (SquadMembers Primary/Special). Halves round up (67.5 -> 70). Test QW-2 Escort 1223 and
# the hidden HN-6 MANPADS Team 1024 are left out. Lateralus 12:4x sets five China prices directly ("Osama underpriced the Chinese MANPAD teams"):
# QW-2 Team 65, Marine QW-2 Team 70, AA Troopers 55 (like US Troopers AA), FN-6 Team 60; AT Troopers 70 -> 80 (not a MANPAD team).
# Loadout swap rows (OptionsJson.ReplaceUnitId) get their own new price and the swap option costs follow, so that swap row = base + option
# (audit_swap_prices rule). A swap row whose base card is not a MANPAD team cannot drop below that base: STT (Pararescue 60 + Stinger option) 65 -> 60,
# option +5 -> +0. Spetsnaz GRU AT 346 (no MANPAD) keeps 100, so its option on GRU Mix goes +15 -> +30.
_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson'];_SM=t['SquadMembersJson']
_inf={m['UnitId'] for m in _SM.values()}
_mp={r['WeaponId'] for r in _WA.values() if r['UnitId'] in _inf and (_A[r['AmmunitionId']].get('Seeker') or 0)>0 and (_A[r['AmmunitionId']].get('TargetType') or 0)&24}
_teams={i:n for i,u in U.items() if i in _inf and u.get('DisplayInArmory') and i!=1223
        for n in [sum(1 for m in _SM.values() if m['UnitId']==i and (m.get('PrimaryWeaponId') in _mp or m.get('SpecialWeaponId') in _mp))] if n}
_EXPECT={69:(2,75,70),73:(2,85,75),109:(1,60,50),120:(2,65,60),134:(1,60,50),356:(2,75,70),371:(1,50,45),404:(1,60,50),413:(1,65,55),440:(1,75,65),
 522:(1,60,50),523:(2,65,60),524:(1,60,50),613:(1,60,50),704:(1,60,50),705:(1,60,50),706:(1,65,55),
 125:(1,85,70),417:(2,85,75),342:(1,65,60),1145:(1,65,55),1191:(1,65,55),1206:(1,60,50),
 1153:(2,65,65),1194:(2,65,70),1197:(1,60,55),1169:(2,65,60)}
_SET={1153:65,1194:70,1197:55,1169:60}
ok(set(_teams)==set(_EXPECT),('MANPAD teams',sorted(set(_teams)^set(_EXPECT))))
_new={}
for i,n in _teams.items():
    ok(n in (1,2) and (n,U[i]['Cost'])==_EXPECT[i][:2],(i,U[i]['HUDName'],'launchers/cost',n,U[i]['Cost']))
    _new[i]=_SET.get(i) or r5(U[i]['Cost']*(Decimal('0.85') if n==1 else Decimal('0.9')))
_own={o['ReplaceUnitId']:M[o['ModificationId']]['UnitId'] for o in O.values() if o.get('ReplaceUnitId') and M[o['ModificationId']]['UnitId']!=o['ReplaceUnitId']}
for i in list(_new):
    b=_own.get(i)
    if b is not None and b not in _new:_new[i]=max(_new[i],U[b]['Cost'])
ok({i:_new[i] for i in _new}=={i:v[2] for i,v in _EXPECT.items()},('new prices',{i:_new[i] for i in _new if _new[i]!=_EXPECT[i][2]}))
_old={i:U[i]['Cost'] for i in _teams}
for i,c in _new.items():g.put('Units',i,{'Cost':c})
ok(U[1198]['HUDName']=='AT Troopers 反坦克组' and U[1198]['Cost']==70 and 1198 not in _own,'AT Troopers 1198 at 70, no swap rows')
g.put('Units',1198,{'Cost':80})
_opt={}
for o in list(O.values()):
    s=o.get('ReplaceUnitId');own=M[o['ModificationId']]['UnitId'] if o.get('ModificationId') in M else None
    if not s or s==own or (s not in _new and own not in _new):continue
    c=U[s]['Cost']-U[own]['Cost'];ok(c>=0,('swap option cost',o['Id'],c))
    if (o.get('Cost') or 0)!=c:_opt[o['Id']]=[o.get('Cost'),c];g.put('OptionsJson',o['Id'],{'Cost':c})
ok(_opt=={3332:[10,5],2151:[5,10],1857:[0,5],1497:[15,30],1489:[5,0]},('swap option costs that move',_opt))
# Smoke off on QW-2 Team, Marine QW-2 Team and AA Troopers (Lateralus 12:4x "Remove smoke from QW-2 and Marine QW-2 teams and AA Troopers"): each used its
# own ability row (sprint + smoke ammo 276); their link goes to the vanilla Sprint ability 90, the one US Troopers AA and Stinger teams use.
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
ok(AB[90]['Name']=='Sprint' and not AB[90].get('SmokeAmmunitionId'),'vanilla Sprint 90 has no smoke')
for u,ab in ((1153,2012285),(1194,2013498),(1197,2013587)):
    rr=[r for r in UAB.values() if r['UnitId']==u];ok(len(rr)==1 and rr[0]['AbilityId']==ab and AB[ab].get('SmokeAmmunitionId')==276,(u,'one sprint+smoke ability'))
    ok([r['UnitId'] for r in UAB.values() if r['AbilityId']==ab]==[u],(u,'ability used by this unit only'));g.put('UnitAbilitiesJson',rr[0]['Id'],{'AbilityId':90})
# MANPAD rounds per launcher 4 -> 3 on Marine QW-2 Team and FN-6 Team (two launchers each: 8 -> 6 in the Arsenal).
for u,row,w in ((1194,2015442,'QW-2'),(1169,2015171,'FN-6')):
    ok(_WA[row]['UnitId']==u and t['WeaponsJson'][_WA[row]['WeaponId']]['HUDName']==w and _WA[row]['Quantity']==4,(u,'MANPAD ammo row',row));g.put('WeaponAmmunitionsJson',row,{'Quantity':3})
rec['manpad_team_prices']={'cost':{str(i):[_old[i],_new[i],_teams[i]] for i in sorted(_new)},'set_by_lateralus':{str(k):v for k,v in _SET.items()},
    'at_troopers_1198':[70,80],'swap_option_cost':{str(k):v for k,v in _opt.items()},'smoke_removed':[1153,1194,1197],'ammo_per_launcher_4_to_3':[1194,1169],
    'left_out':{'1223':'test unit','1024':'hidden HN-6 MANPADS Team'},'verified':'data checks only'}
# ---------- 2. CSK-131 Recon (Lateralus, same message: "Price 5 -> 30, optics Very Good -> Good, and make it available in every other China specs (similar
# to how USMC Scouts are available in other specs)"). Unit 1265: Cost is already 30 in 0.9.0-dev.41..0.9.1-dev.3 (unchanged here; "5" is not in the data).
# Its one sensor link (Very Good, sensor 3) -> Good (sensor 1). USMC Scouts 726 have one row per US spec with the same cards; 1265 has 4 cards in PLAGF
# Motorized (21) and gets 4 in Air Force 17, Armored 18, Rocket Force 19 and Navy SF 20 (not the hidden Test spec 22). pla-spec-assignments.json follows.
ok(U[1265]['HUDName']=='CSK-131 Recon' and U[1265]['Cost']==30,'CSK-131 Recon 1265 at 30')
_su=[r for r in SU.values() if r['UnitId']==1265];ok(len(_su)==1 and _su[0]['SensorId']==3 and S[1]['Name']=='Good Optics','1265 Very Good optics, one link')
g.put('SensorUnitsJson',_su[0]['Id'],{'SensorId':1})
_sa=[r for r in SA.values() if r['UnitId']==1265];ok(len(_sa)==1 and _sa[0]['SpecializationId']==21 and _sa[0]['MaxAvailabilityXp0']==4,'1265 only in Motorized, 4 cards')
_cn=sorted(i for i,s in t['SpecializationsJson'].items() if s.get('CountryId')==4 and s.get('ShowInHangar'));ok(_cn==[17,18,19,20,21],('China specs',_cn))
for s in _cn:
    if s!=21:g.add('SpecializationAvailabilitiesJson',_sa[0],{'SpecializationId':s})
ok(sorted(r['SpecializationId'] for r in SA.values() if r['UnitId']==1265)==_cn and all(r['MaxAvailabilityXp0']==4 for r in SA.values() if r['UnitId']==1265),'1265 in every China spec')
ok(assign['assignments'].get('1265')==[21],'assignment metadata 1265');assign['assignments']['1265']=_cn
rec['csk131_recon']={'unit':1265,'optics':['Very Good 3','Good 1'],'specs':_cn,'cards':4,'cost':'30 (unchanged, already 30)'}
# ---------- 3-8. Optics (same message). A unit's optics are its SensorUnitsJson links; a loadout option picks one with MainSensorId. Each change re-points
# the link and the option to the shared tier row of the same kind (plain rows 2 Medium, 23 Medium Plus, 1 Good, 3 Very Good; NonDefault rows 28 Medium
# Plus ND, 13 Good ND, 14 Very Good ND). No sensor row is edited.
_tier={1:'Good Optics',2:'Medium Optics',3:'Very Good Optics',13:'Good Optics NonDefault',14:'Very Good Optics NonDefault',23:'Medium Plus Optics',28:'Medium Plus Optics NonDefault'}
ok(all(S[k]['Name']==v for k,v in _tier.items()),'tier sensor rows')
# (unit, HUDName, {SensorUnits id: (old, new)}, {option id: (old MainSensorId, new)}, cost change)
_OPT=[(29,'LAV-25',{711:(23,1),925:(13,14)},{18:(23,1),19:(13,14)},None),             # A1 Medium+ -> Good; A2 armour/optics/smoke Good -> Very Good
 (249,'Humvee RWS',{641:(1,3)},{},None),                                                # Good -> Very Good
 (467,'M-ATV',{935:(1,3)},{},(30,35)),                                                  # Good -> Very Good, 30 -> 35
 (714,'M-ATV Javelin',{2000246:(1,3)},{},None),                                         # Good -> Very Good
 (23,'Typhoon VDV',{331:(2,1),777:(28,14)},{270:(2,1),271:(28,14)},None),               # Medium -> Good; 2A42 Medium+ -> Very Good
 (383,'BTR-90',{764:(2,1),765:(23,3)},{1731:(2,1),1732:(2,1),1733:(23,3),1734:(23,3)},None), # Medium -> Good; Berezhok/Bakhcha-U Medium+ -> Very Good
 (195,'Tigr BRShM ',{648:(1,3)},{426:(1,3)},None)]                                      # Good -> Very Good (the optronic system option stays Exceptional)
_orec={}
for u,h,sus,opts,cost in _OPT:
    ok(U[u]['HUDName']==h,(u,'name',U[u]['HUDName']))
    ok({r['Id']:r['SensorId'] for r in SU.values() if r['UnitId']==u}.items()>={k:v[0] for k,v in sus.items()}.items(),(u,'sensor links'))
    _mo={o['Id']:o.get('MainSensorId') for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId')==u and o.get('MainSensorId')}
    ok({k:_mo.get(k) for k in opts}=={k:v[0] for k,v in opts.items()} and set(_mo)-set(opts)<={425},(u,'option sensors',_mo))
    for k,(_,n) in sus.items():g.put('SensorUnitsJson',k,{'SensorId':n})
    for k,(_,n) in opts.items():g.put('OptionsJson',k,{'MainSensorId':n})
    if cost:ok(U[u]['Cost']==cost[0],(u,'cost'));g.put('Units',u,{'Cost':cost[1]})
    _orec[str(u)]={'name':h.strip(),'sensor_links':{str(k):[_tier[v[0]],_tier[v[1]]] for k,v in sus.items()},'options':{str(k):[_tier[v[0]],_tier[v[1]]] for k,v in opts.items()},**({'cost':list(cost)} if cost else {})}
ok(not [o for o in O.values() if o.get('ReplaceUnitId')==467],'no swap rows on M-ATV')
rec['vehicle_optics']=_orec
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
