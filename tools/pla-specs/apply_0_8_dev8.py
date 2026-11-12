"""Freedom Arrow 0.8.0-dev.8 over exact 0.8.0-dev.7 (Osama 12 Nov 14:41 PST aircraft batch; 14:44 "give the infantry the CH-901").

1. Stray weapons. (a) Gun slot: on models with a native default gun turret, a unit with no default turret got the first
   mount of its turret list in that slot (J-7 PL-8, J-8D 4x 250 kg, J-20S PL-12). These units get an empty default turret
   in their first turret row; no gun is added. (b) Unset pylons: every loadout now sets every pylon of its model (vanilla
   option slots + Build47 slots); the J-16 left slots 10/11 open and showed a PL-12 and PL-17 there. (c) Turret and ammo
   rows that no loadout uses are deleted.
2. Pictures: a loadout shows its role weapon (bomb on strike, missile on CAP), not the costliest store. R73 (no such icon)
   is R73_MISSILE. PL-17 and PL-21 use new icons drawn from Osama's reference (FA_PLA_PL17 / FA_PLA_PL21).
3. Order: air-to-air, then strike (with CAS, anti-armor and mixed), then SEAD, then standoff and anti-ship; cheapest first.
4. Names: YJ-15 loads are Standoff strike. GB-6 strike loads are Anti-armor. BBC-5 loads removed (GB-6 twin kept) or
   rebuilt on GB-6.
5. Removed: Su-30MKK, J-11BS, J-11BHG and J-15 SEAD.
6. H-6K: Standoff strike KD-63 is 6x KD-63 only; new Heavy SEAD with 6x YJ-91.
7. LS-6 1000kg (GBU-56 analog, laser guided): 2x on J-20S, J-31, J-35 and MD-22 (J-31 loads); J-36 Heavy strike 4x.
8. FH-97A: J-31 menu, J-31 price; its fixed AMRAAM mount is removed.
9. ECM: J-16 40%, J-16D 50% (jammer pods), F-15EX 40% and 165 points (= J-16), Su-35S 30% in every loadout and 135 points.
10. J-36: in-flight top speed 900 km/h (J-16 speed values on its F-35 turn preset).
11. Blood Wolves NLOS launcher and missile named CH-901.
"""
import argparse,copy,hashlib,json,re,sys,zipfile
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.8'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.7.json').read_text())['complete']['sha256']
lib=(ROOT/'tools/pla-specs/apply_build47_air.py').read_text()
exec(lib[lib.index('# ---- weapon catalogue'):lib.index('# ---- unit plan')])          # C, CANON, DROP, SLOTS
C['PL-16']=dict(C['PL-15'],cost=22.5)
C['LD-8A']=dict(ammo=298,w=395,vis={1:'Weapon/R77/R77'},pic='AGM88_HARM',cost=40,cls='agm')
C['LS-6 250kg']=dict(C['250 kg bomb'],cost=7.5)
C['LS-6 1000kg']=dict(ammo=291,w=377,vis={1:'Weapon/GBU56/GBU56_single'},pic='GBU56',cost=30,cls='bomb',over={'HUDName':'LS-6 1000kg'})
C['PL-17']['pic']='FA_PLA_PL17';C['PL-21']['pic']='FA_PLA_PL21';C['LT-2']['pic']='GBU55'   # LT-2 rows show as LS-6 500kg
EMPTY=160
J20,J20S,J16,J16D,MD22,J31,J35,J36,H6K,FH97,J15,SU30,J11BS,J11BHG,BW=915,966,916,977,976,1251,921,929,919,1253,943,924,923,1241,1183
SU35S,F15EX=169,289
STEALTH={915,921,929,944,966,967,1251,976,1253}
ARM={'LD-8A','YJ-91','Kh-31P'};SHIP={'YJ-83K','YJ-12','YJ-21','Kh-31A'};STANDOFF={'CJ-10K','KD-63','KD-88','Kh-59M','YJ-15'}
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
U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];T=t['TurretsJson'];O=t['OptionsJson'];M=t['ModificationsJson'];TU=t['TurretUnitsJson'];WA=t['WeaponAmmunitionsJson'];UA=t['UnitAbilitiesJson'];AB=t['AbilitiesJson']
exec(lib[lib.index('ammo_rows={};'):lib.index('# ---- per aircraft')])            # ammo/weapon/turret/assign helpers
for x in A.values():
    m=re.fullmatch(r'PLA air (.+?)( heli)?',x.get('Name') or '')
    if m and m.group(1) in C:ammo_rows[(m.group(1),bool(m.group(2)))]=x['Id']
receipt={'version':V,'base':'0.8.0-dev.7','base_sha256':BASE,'request':'Osama 12 Nov 14:41 PST aircraft batch; 14:44 CH-901','removed_options':[],'added_options':[],
         'gun_slot_defaults':[],'pylons_filled':0,'rows_deleted':{'TurretUnitsJson':0,'WeaponAmmunitionsJson':0},'names':{}}
# ---- helpers (Build65)
twmap=defaultdict(list)
for r in t['TurretWeaponsJson'].values():twmap[r['TurretId']].append(r)
HUD={}
SHOW={'LT-2':'LS-6 500kg','LS-6':'LS-6 500kg'}
def load_of(o):
    ld=Counter()
    for i in range(21):
        for r in twmap.get(o.get(f'Turret{i}Id'),[]):
            m=re.fullmatch(r'PLA air (.+) x(\d+)',W[r['WeaponId']]['Name'] or '')
            if m:ld[m.group(1)]+=int(m.group(2));HUD.setdefault(m.group(1),W[r['WeaponId']]['HUDName'])
    return ld
def disp(k):return SHOW.get(k,HUD.get(k,k))
def menus():
    for m in list(M.values()):
        if m['Type']==3 and m['Name'].startswith('PLA loadout') and U.get(m['UnitId'],{}).get('CountryId')==4:yield m
def opts(mid):return sorted([o for o in O.values() if o['ModificationId']==mid],key=lambda o:o['Order'])
def drop(o,why):
    receipt['removed_options'].append({'unit':U[M[o['ModificationId']]['UnitId']]['HUDName'],'option':o['UIName'],'load':dict(load_of(o)),'why':why});g.remove('OptionsJson',o['Id'])
def add_option(uid,mid,load,stealth):
    heli=U[uid]['Type']==8;plan=assign(uid,load,stealth,heli);opt={k:(0 if k.startswith('Turret') else copy.deepcopy(v)) for k,v in OPT_T.items() if k!='Id'}
    for (s,kind),parts in plan.items():
        tid=turret(parts,heli,kind);opt[f'Turret{s}Id']=tid;twmap.setdefault(tid,[r for r in t['TurretWeaponsJson'].values() if r['TurretId']==tid])
        if not any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':tid,'Order':0})
        for n,q in parts:
            wid,aid=weapon(n,q,heli),ammo(n,heli)
            if not any(r['WeaponId']==wid for r in g.rows('WeaponAmmunitionsJson',uid)):g.add('WeaponAmmunitionsJson',WA_T,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
    raw=sum(C[k]['cost']*n for k,n in load.items());raw=raw if raw<=150 else 150+(raw-150)/2
    order=len(opts(mid))
    opt.update(ModificationId=mid,Name=f'PLA loadout {U[uid]["HUDName"]} d8 {order}',Order=order,UIName='',Cost=int(round(raw/5.0)*5),OptionPicture='EMPTY',IsDefault=False)
    oid=g.add('OptionsJson',OPT_T,opt);receipt['added_options'].append({'unit':U[uid]['HUDName'],'load':dict(load),'cost':O[oid]['Cost']});return oid
def rebuild(uid,o,load,why):
    """Replace option o by a new one with load, keeping its place and default flag."""
    keep=(o['Order'],o['IsDefault']);drop(o,why);oid=add_option(uid,mod_of[uid],load,uid in STEALTH);g.put('OptionsJson',oid,{'Order':keep[0],'IsDefault':keep[1]});return oid
mod_of={m['UnitId']:m['Id'] for m in menus()}
def find(uid,pred):return [o for o in opts(mod_of[uid]) if pred(load_of(o),o)]
# ---- 11. CH-901
nl=json.loads(z.read('UserData/FreedomArrow/nlos.json'));bww=max(nl['weapons']);bwa=max(nl['ammunition'])
assert W[bww]['Name']=='PLA Blood Wolves NLOS launcher' and A[bwa]['Name']=='PLA Blood Wolves NLOS missile'
g.put('WeaponsJson',bww,{'HUDName':'CH-901'});g.put('AmmunitionsJson',bwa,{'HUDName':'CH-901'})
# ---- 5. SEAD removals; 4. BBC-5
for uid in (SU30,J11BS,J11BHG,J15):
    for o in find(uid,lambda ld,o:any(k in ARM for k in ld)):drop(o,'SEAD removed (Osama)')
for uid in sorted(mod_of):
    for o in find(uid,lambda ld,o:'BBC-5' in ld):
        ld=load_of(o);twin={**{k:v for k,v in ld.items() if k!='BBC-5'},'GB-6':ld['BBC-5']}
        if any(load_of(x)==Counter(twin) for x in opts(mod_of[uid]) if x['Id']!=o['Id']):drop(o,'BBC-5 removed; GB-6 load kept')
        else:rebuild(uid,o,twin,'BBC-5 replaced by GB-6')
# ---- 6. H-6K
for o in find(H6K,lambda ld,o:'KD-63' in ld):rebuild(H6K,o,{'KD-63':6},'KD-63 standoff carries KD-63 only')
add_option(H6K,mod_of[H6K],{'YJ-91':6},False)
# ---- 7. LS-6 1000kg
for uid,load in ((J20S,{'LS-6 1000kg':2,'PL-10':2}),(J31,{'LS-6 1000kg':2,'PL-15':2}),(J35,{'LS-6 1000kg':2,'PL-15':2}),(MD22,{'LS-6 1000kg':2,'PL-15':2})):add_option(uid,mod_of[uid],load,True)
heavy=find(J36,lambda ld,o:o['UIName']=='Heavy strike');assert len(heavy)==1
rebuild(J36,heavy[0],{'PL-15C':4,'LS-6 1000kg':4},'J-36 Heavy strike is 4x LS-6 1000kg')
# ---- 8. FH-97A = J-31
for r in list(g.rows('TurretUnitsJson',FH97)):
    if T[r['TurretId']].get('IsDefault'):
        for tw in twmap.get(r['TurretId'],[]):
            for x in [x for x in g.rows('WeaponAmmunitionsJson',FH97) if x['WeaponId']==tw['WeaponId']]:g.remove('WeaponAmmunitionsJson',x['Id'])
        g.remove('TurretUnitsJson',r['Id'])
assert FH97 not in mod_of
mod_of[FH97]=g.add('ModificationsJson',MOD_T,{'UnitId':FH97,'Name':'PLA loadout FH-97A','Type':3,'UIName':'Custom_Slot_Weapon_package','ThumbnailFileName':None,'Order':0})
for o in opts(mod_of[J31]):
    oid=add_option(FH97,mod_of[FH97],dict(load_of(o)),True);g.put('OptionsJson',oid,{'IsDefault':o['IsDefault']})
g.put('Units',FH97,{'Cost':U[J31]['Cost']})
# ---- 1a. empty default turret in the gun slot
GUNSLOT=g.add('TurretsJson',T[EMPTY],{'Name':'PLA empty default mount','IsDefault':True})
vunits={u['Id'] for u in before['Units'].values() if u['Id'] in native['Units']}
model_default={}
for u in U.values():
    if u['Id'] in vunits and u.get('Type') in(8,16):
        model_default.setdefault(u.get('ModelFileName'),any(T[r['TurretId']].get('IsDefault') for r in TU.values() if r['UnitId']==u['Id']))
for uid in sorted(mod_of):
    rows=sorted(g.rows('TurretUnitsJson',uid),key=lambda r:r['Id'])
    if not model_default.get(U[uid].get('ModelFileName')) or any(T[r['TurretId']].get('IsDefault') for r in rows):continue
    first=rows[0];moved=first['TurretId']
    g.put('TurretUnitsJson',first['Id'],{'TurretId':GUNSLOT,'Order':0})
    g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':moved,'Order':0})
    receipt['gun_slot_defaults'].append({'unit':U[uid]['HUDName'],'was_first':[W[x['WeaponId']]['HUDName'] for x in twmap.get(moved,[])]})
# ---- 9. ECM
def ability(src,name):return g.add('AbilitiesJson',AB[src],{'Name':name})
ecm40=ability(2001969,'PLA ECM 40 percent Default');ecm50=ability(2001398,'PLA J-16D ECM 50 percent Default')
assert AB[ecm40]['ECMAccuracyMultiplier']==0.6 and AB[ecm50]['ECMAccuracyMultiplier']==0.5 and AB[ecm40]['IsDefault'] and AB[ecm50]['IsDefault']
for uid,new in ((J16,ecm40),(J16D,ecm50)):
    dflt=[r for r in g.rows('UnitAbilitiesJson',uid) if AB[r['AbilityId']].get('IsDefault') and AB[r['AbilityId']].get('ECMAccuracyMultiplier') not in(None,0,1)]
    assert len(dflt)==1,(uid,dflt);g.put('UnitAbilitiesJson',dflt[0]['Id'],{'AbilityId':new})
su35=[o for m in M.values() if m['UnitId']==SU35S for o in O.values() if o['ModificationId']==m['Id'] and o.get('Ability1Id')==2001406]
assert len(su35)==3
for o in su35:g.put('OptionsJson',o['Id'],{'Ability1Id':0})
g.put('Units',SU35S,{'Cost':U[SU35S]['Cost']-30})
f15=[o for m in M.values() if m['UnitId']==F15EX for o in O.values() if o['ModificationId']==m['Id'] and o.get('Ability1Id')==2001402]
assert len(f15)==2 and AB[2001404]['ECMAccuracyMultiplier']==0.6 and not AB[2001404]['IsDefault']
for o in f15:g.put('OptionsJson',o['Id'],{'Ability1Id':2001404})
g.put('Units',F15EX,{'Cost':U[J16]['Cost']})
# ---- 10. J-36 speed
mob=[t['MobilityJson'][r['MobilityId']] for r in t['UnitPropulsionsJson'].values() if r['UnitId']==J36];assert len(mob)==1
fp=t['FlyPresetsJson'];j16fp=fp[next(t['MobilityJson'][r['MobilityId']]['FlyPresetId'] for r in t['UnitPropulsionsJson'].values() if r['UnitId']==J16)]
new_fp=g.add('FlyPresetsJson',fp[mob[0]['FlyPresetId']],{'Name':'PLA J-36 F-35 turn, 900 km/h','MaxSpeed':j16fp['MaxSpeed'],'AfterburnSpeed':j16fp['AfterburnSpeed']})
g.put('MobilityJson',mob[0]['Id'],{'FlyPresetId':new_fp,'MaxSpeedRoad':900.0})
# ---- 2. icons on PL-17 / PL-21 weapons
for w in W.values():
    m=re.fullmatch(r'PLA air (PL-17|PL-21) x\d+',w.get('Name') or '')
    if m:g.put('WeaponsJson',w['Id'],{'HUDIcon':C[m.group(1)]['pic']})
# ---- 1b/1c, 2-4. per menu: delete unused rows, fill every pylon, names, pictures, order
vopt=native['OptionsJson'];vslots=defaultdict(set)
for o in before['OptionsJson'].values():
    if o['Id'] in vopt and o['ModificationId'] in M and M[o['ModificationId']]['UnitId'] in vunits:
        vslots[U[M[o['ModificationId']]['UnitId']].get('ModelFileName')]|={i for i in range(21) if o.get(f'Turret{i}Id')}
def role(uid,ld):
    cls=Counter();[cls.update({C[k]['cls']:n}) for k,n in ld.items()]
    names=set(ld);aa=cls['bvr']+cls['ir']
    if U[uid]['Type']==8:
        if cls['atgm'] and cls['rocket']:return 'Multirole'
        if cls['atgm']:return ('Light' if cls['atgm']<=4 else 'Heavy')+' anti-armor'
        if cls['rocket'] or cls['bomb']:return 'Fire support'
        return 'Air escort'
    arm=sum(n for k,n in ld.items() if k in ARM)
    if arm:return ('Light' if arm<=2 else 'Heavy')+' SEAD'
    if names&SHIP:return 'Anti-ship'
    if names&STANDOFF:return 'Standoff strike'
    if 'GB-6' in names:return 'Anti-armor'
    gnd=sum(n*(2 if k=='LS-6 1000kg' else 1) for k,n in ld.items() if C[k]['cls'] in('bomb','agm'))   # a 1000 kg bomb counts as two
    if gnd:return ('Light' if gnd<=4 else 'Heavy')+' strike'
    if cls['rocket']:return 'CAS'
    return ('Light' if aa<=4 else 'Heavy')+' CAP'
RANK=lambda nm:0 if nm.endswith('CAP') or nm=='Air escort' else 2 if nm.endswith('SEAD') else 3 if nm in('Standoff strike','Anti-ship') else 1
def role_weapon(nm,ld):
    if RANK(nm)==0:pool=[k for k in ld if C[k]['cls'] in('bvr','ir','heliaa')]
    elif nm.endswith('SEAD'):pool=[k for k in ld if k in ARM]
    elif RANK(nm)==3:pool=[k for k in ld if k in SHIP|STANDOFF]
    else:pool=[k for k in ld if C[k]['cls'] not in('bvr','ir','heliaa')]
    return max(pool or list(ld),key=lambda k:(C[k]['cost']*ld[k],k))
PIC={'R73':'R73_MISSILE'}
for uid,mid in sorted(mod_of.items()):
    os_=opts(mid);assert os_,('menu left empty',uid)
    used_t={o[f'Turret{i}Id'] for o in os_ for i in range(21) if o.get(f'Turret{i}Id')}
    for r in list(g.rows('TurretUnitsJson',uid)):
        if r['TurretId'] not in used_t and r['TurretId']!=EMPTY and not T[r['TurretId']].get('IsDefault'):g.remove('TurretUnitsJson',r['Id']);receipt['rows_deleted']['TurretUnitsJson']+=1
    live_w={tw['WeaponId'] for r in g.rows('TurretUnitsJson',uid) for tw in twmap.get(r['TurretId'],[])}
    for x in list(g.rows('WeaponAmmunitionsJson',uid)):
        if x['WeaponId'] not in live_w:g.remove('WeaponAmmunitionsJson',x['Id']);receipt['rows_deleted']['WeaponAmmunitionsJson']+=1
    if not any(r['TurretId']==EMPTY for r in g.rows('TurretUnitsJson',uid)):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':EMPTY,'Order':0})
    slots=sorted(vslots.get(U[uid].get('ModelFileName'),set())|{s for s,_ in SLOTS.get(U[uid].get('ModelFileName'),[])}|{i for o in os_ for i in range(21) if o.get(f'Turret{i}Id')})
    base=[role(uid,load_of(o)) for o in os_];names=list(base)
    def tag(nm,ld,level):
        main=role_weapon(nm,ld)
        if level==1:return f'{nm} ({disp(main)})'
        if level==2:return f'{nm} ({ld[main]}x {disp(main)})'
        return f"{nm} ({', '.join(f'{n}x {disp(k)}' for k,n in sorted(ld.items(),key=lambda x:(-C[x[0]]['cost']*x[1],x[0])))})"
    for level in(1,2,3):
        dup=Counter(names)
        names=[tag(b0,load_of(o),level) if dup[nm]>1 else nm for o,b0,nm in zip(os_,base,names)]
    order=sorted(zip(os_,base,names),key=lambda x:(RANK(x[1]),x[0]['Cost'],x[2]))
    if not any(o['IsDefault'] for o in os_):g.put('OptionsJson',order[0][0]['Id'],{'IsDefault':True})
    for i,(o,b0,nm) in enumerate(order):
        ld=load_of(o);pic=C[role_weapon(b0,ld)]['pic'];pic=PIC.get(pic,pic)
        fill={f'Turret{s}Id':EMPTY for s in slots if not o.get(f'Turret{s}Id')};receipt['pylons_filled']+=len(fill)
        g.put('OptionsJson',o['Id'],{**fill,'UIName':nm,'Order':i,'OptionPicture':pic})
    receipt['names'][U[uid]['HUDName']]=[(O[o['Id']]['UIName'],', '.join(f"{n}x {disp(k)}" for k,n in load_of(O[o['Id']]).items()),O[o['Id']]['Cost'],O[o['Id']]['OptionPicture'],O[o['Id']]['IsDefault']) for o in opts(mid)]
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
vpics={o['OptionPicture'] for o in before['OptionsJson'].values() if o['Id'] in vopt}|{'FA_PLA_PL17','FA_PLA_PL21'}
for uid,mid in mod_of.items():
    os_=opts(mid);slots=sorted(vslots.get(U[uid].get('ModelFileName'),set())|{i for o in os_ for i in range(21) if o.get(f'Turret{i}Id')})
    ok(sum(bool(o['IsDefault']) for o in os_)==1,('one default',uid))
    ranks=[RANK(re.sub(r' \(.*','',o['UIName'])) for o in os_];ok(ranks==sorted(ranks),('category order',uid,ranks))
    for a_,b_ in zip(os_,os_[1:]):
        if RANK(re.sub(r' \(.*','',a_['UIName']))==RANK(re.sub(r' \(.*','',b_['UIName'])):ok(a_['Cost']<=b_['Cost'],('price order',uid))
    ok(len({o['UIName'] for o in os_})==len(os_),('unique names',uid))
    used_t={o[f'Turret{i}Id'] for o in os_ for i in range(21) if o.get(f'Turret{i}Id')}
    for r in g.rows('TurretUnitsJson',uid):ok(r['TurretId'] in used_t|{EMPTY} or T[r['TurretId']].get('IsDefault'),('unused turret row',uid,r['TurretId']))
    if model_default.get(U[uid].get('ModelFileName')):ok(any(T[r['TurretId']].get('IsDefault') for r in g.rows('TurretUnitsJson',uid)),('gun slot default',uid))
    for o in os_:
        ok(all(o.get(f'Turret{s}Id') for s in slots),('pylon left open',uid,o['Id']));ok(o['Id']<=32767,('option id',o['Id']))
        ok(o['OptionPicture'] in vpics,('picture',uid,o['OptionPicture']))
        ld=load_of(o)
        ok('BBC-5' not in ld,('BBC-5',uid))
        if uid in(SU30,J11BS,J11BHG,J15):ok(not any(k in ARM for k in ld),('SEAD left',uid))
        if uid in STEALTH:ok('YJ-91' not in ld,('stealth YJ-91',uid))
        if uid in(J20,J20S):ok('PL-17' not in ld and ld['PL-15']+ld['PL-15C']<=4,('J-20 bay',uid))
        if uid==J20:ok(all(C[k]['cls'] in('bvr','ir') for k in ld),'J-20 AA only')
        if 'YJ-15' in ld:ok(o['UIName'].startswith('Standoff strike'),('YJ-15 name',o['UIName']))
        if 'GB-6' in ld and not any(k in ARM|SHIP|STANDOFF for k in ld):ok(o['UIName'].startswith('Anti-armor'),('GB-6 name',o['UIName']))
        for tid in [o[f'Turret{i}Id'] for i in range(21) if o.get(f'Turret{i}Id')]:
            ok(any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)),('turret link',uid,tid))
            for tw in twmap.get(tid,[]):ok(any(r['WeaponId']==tw['WeaponId'] for r in g.rows('WeaponAmmunitionsJson',uid)),('ammo row',uid,tw['WeaponId']))
for uid in (J20S,J31,J35,MD22,FH97):ok(any(load_of(o)['LS-6 1000kg']==2 for o in opts(mod_of[uid])),('LS-6 1000kg x2',uid))
ok(any(load_of(o)['LS-6 1000kg']==4 and o['UIName'].startswith('Heavy strike') for o in opts(mod_of[J36])),'J-36 Heavy strike 4x LS-6 1000kg')
ok(sorted(tuple(sorted(load_of(o).items())) for o in opts(mod_of[FH97]))==sorted(tuple(sorted(load_of(o).items())) for o in opts(mod_of[J31])),'FH-97A has the J-31 menu')
ok(not any(T[r['TurretId']].get('IsDefault') for r in g.rows('TurretUnitsJson',FH97)),'FH-97A fixed mount removed')
ok(any(load_of(o)==Counter({'YJ-91':6}) for o in opts(mod_of[H6K])) and all(set(load_of(o))=={'KD-63'} for o in opts(mod_of[H6K]) if 'KD-63' in load_of(o)),'H-6K')
ok(fp[t['MobilityJson'][mob[0]['Id']]['FlyPresetId']]['MaxSpeed']==250,'J-36 900 km/h')
for uid,want in ((J16,0.6),(J16D,0.5)):ok([AB[r['AbilityId']]['ECMAccuracyMultiplier'] for r in g.rows('UnitAbilitiesJson',uid) if AB[r['AbilityId']].get('IsDefault') and AB[r['AbilityId']].get('ECMAccuracyMultiplier') not in(None,0,1)]==[want],('ECM',uid))
CHANGED_NATIVE={('Units',SU35S),('Units',F15EX)}|{('OptionsJson',o['Id']) for o in su35+f15}
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4 and uid not in(SU35S,F15EX):ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab] and (tab,key) not in CHANGED_NATIVE:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
receipt['ecm']={'J-16':0.6,'J-16D':0.5,'F-15EX':'0.6 via its loadouts','Su-35S':'0.7 in every loadout'}
receipt['prices']={'Su-35S':U[SU35S]['Cost'],'F-15EX':U[F15EX]['Cost'],'FH-97A':U[FH97]['Cost'],'J-35':U[J35]['Cost']}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'pylons filled',receipt['pylons_filled'],'removed',len(receipt['removed_options']),'added',len(receipt['added_options']),'deleted',receipt['rows_deleted'],'gun slot',len(receipt['gun_slot_defaults']))
