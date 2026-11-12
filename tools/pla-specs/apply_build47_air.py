"""Build47 aircraft pass over exact Build46 (Osama 12 Nov 05:00 PST).

Every armed PLA jet and helicopter gets a loadout menu built from Command: Modern Operations
DB3K_519 (tools/pla-specs/cmo-air-loadouts.json, extracted by work/pla-cmo-20261112/extract.py):
up to 8 distinct loadouts per aircraft, no fuel tanks or pods, internal bays only for stealth
fighters. Chinese weapons are mapped to the closest weapon already in the game; ATGMs use the
10.5 damage standard. Each aircraft also takes speed, armour, sensors, stealth and default ECM
from one vanilla counterpart of the same generation, and a new base price.
"""
import argparse,copy,hashlib,json,math,re,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-46.json').read_text())['sha256']

# ---- weapon catalogue: canonical name -> analog ammo (plane, heli), launcher template, visuals by pack size, picture, cost per round
C={
 'PL-5E':dict(ammo=165,w=435,vis={1:'Weapon/R60/R60_1'},pic='R60',cost=8,cls='ir'),
 'PL-7':dict(ammo=165,w=435,vis={1:'Weapon/R60/R60_1'},pic='R60',cost=8,cls='ir'),
 'PL-8':dict(ammo=158,w=243,vis={1:'Weapon/R73/R73'},tip='Weapon/R73/R73_Wingtip',pic='R73',cost=10,cls='ir'),
 'PL-9':dict(ammo=158,w=243,vis={1:'Weapon/R73/R73'},tip='Weapon/R73/R73_Wingtip',pic='R73',cost=10,cls='ir'),
 'PL-10':dict(ammo=59,w=113,vis={1:'Weapon/R73/R73'},tip='Weapon/R73/R73_Wingtip',pic='AIM9_PYLON',cost=12.5,cls='ir'),
 'PL-11':dict(ammo=285,w=371,vis={1:'Weapon/R27/R27ER'},pic='AIM7_MISSILE',cost=12.5,cls='bvr'),
 'PL-12':dict(ammo=159,w=244,vis={1:'Weapon/R77/R77',2:'Weapon/R77/R77_2'},pic='R77_MISSILE',cost=17.5,cls='bvr'),
 'PL-15':dict(ammo=531,w=675,vis={1:'Weapon/R77/R77',2:'Weapon/R77/R77_2'},pic='JATM',cost=22.5,cls='bvr'),
 'PL-15C':dict(ammo=89,w=118,vis={1:'Weapon/R77/R77',2:'Weapon/R77/R77_2'},pic='AMRAAM_MISSILE',cost=20,cls='bvr'),
 'PL-17':dict(ammo=312,w=437,vis={1:'Weapon/R37'},pic='R37',cost=30,cls='bvr'),
 'PL-21':dict(ammo=533,w=679,vis={1:'Weapon/R37'},pic='AIM174',cost=30,cls='bvr'),
 'TY-90':dict(ammo=2016167,w=2016170,vis={1:'Weapon/ATAS',2:'Weapon/ATAS',4:'Weapon/ATAS'},pic='STINGER_x2_WINGTIP',cost=8,cls='heliaa'),
 'AKD-10':dict(ammo=164,w=12,vis={1:'Weapon/Hellfire/Hellfire_1',2:'Weapon/Hellfire/Hellfire_2',4:'Weapon/Hellfire/Hellfire_4'},pic='HELLFIRE_X4',cost=10,cls='atgm',over={'Damage':10.5}),
 'AKD-9':dict(ammo=164,w=12,vis={1:'Weapon/Hellfire/Hellfire_1',2:'Weapon/Hellfire/Hellfire_2',4:'Weapon/Hellfire/Hellfire_4'},pic='HELLFIRE_X4',cost=8,cls='atgm',over={'Damage':10.5,'GroundRange':800.0,'PenetrationAtGroundRange':800.0,'PenetrationAtMinRange':800.0}),
 'HJ-8':dict(ammo=80,w=195,vis={2:'Weapon/shturm_b_2',4:'Weapon/shturm_b_4',8:'Weapon/shturm_b_8'},pic='KOKON_x4_PYLON',cost=6,cls='atgm',over={'Damage':10.5}),
 'CM-501GA':dict(ammo=2016169,w=2016176,vis={1:'Weapon/Hellfire/Hellfire_1',2:'Weapon/Hellfire/Hellfire_2',4:'Weapon/Hellfire/Hellfire_4'},pic='HELLFIRE_X2',cost=11,cls='atgm'),
 'FS-70A':dict(ammo=726,w=937,vis={0:'Weapon/Hydra'},pic='S8L',cost=1.5,cls='rocket'),
 '57 mm rocket':dict(ammo=294,heli=17,w=604,hw=15,vis={0:'Weapon/Hydra'},pic='HYDRA_x19_PYLON',cost=0.5,cls='rocket',over={'Damage':3.0}),
 '70 mm rocket':dict(ammo=294,heli=17,w=604,hw=15,vis={0:'Weapon/Hydra'},pic='HYDRA_x19_PYLON',cost=0.6,cls='rocket'),
 '90 mm rocket':dict(ammo=313,heli=81,w=441,hw=103,vis={0:'Weapon/B8M1/B8M1'},hvis={0:'Weapon/B8V20'},pic='S8_POD',cost=0.7,cls='rocket'),
 'S-8KO':dict(ammo=313,heli=81,w=441,hw=103,vis={0:'Weapon/B8M1/B8M1'},hvis={0:'Weapon/B8V20'},pic='S8_POD',cost=0.7,cls='rocket'),
 'S-13B':dict(ammo=148,heli=85,w=232,hw=114,vis={0:'Weapon/B13L5/B13L5'},hvis={0:'Weapon/B13L1'},pic='S13_PLANE',cost=2,cls='rocket'),
 'KD-88':dict(ammo=477,w=633,vis={1:'Weapon/KH_Missiles/KH59MK2'},pic='KH_59MK2_SQUARED',cost=35,cls='agm'),
 'AKF-98A':dict(ammo=318,w=448,vis={1:'Weapon/KH_Missiles/KH38ML'},pic='KH38ML',cost=30,cls='agm'),
 'Kh-29T':dict(ammo=539,w=446,vis={1:'Weapon/KH_Missiles/KH29ML'},pic='KH29_T_MISSILE',cost=25,cls='agm'),
 'Kh-31A':dict(ammo=460,w=614,vis={1:'Weapon/Kh35U_Fold'},pic='KH_35U',cost=45,cls='agm'),
 'Kh-31P':dict(ammo=271,w=358,vis={1:'Weapon/KH_Missiles/KH31P'},pic='KH31P',cost=40,cls='agm'),
 'YJ-91':dict(ammo=271,w=358,vis={1:'Weapon/KH_Missiles/KH31P'},pic='KH31P',cost=40,cls='agm'),
 'Kh-59M':dict(ammo=316,w=450,vis={1:'Weapon/KH_Missiles/KH59MK'},pic='KH_59MK2',cost=35,cls='agm'),
 'KD-63':dict(ammo=316,w=450,vis={1:'Weapon/KH_Missiles/KH59MK'},pic='KH_59MK2',cost=35,cls='agm'),
 'YJ-83K':dict(ammo=478,w=634,vis={1:'Weapon/Kh35U_Fold'},pic='KH_35U',cost=45,cls='agm'),
 'YJ-12':dict(ammo=334,w=485,vis={1:'Weapon/Kh22_Kh32'},pic='KH32',cost=60,cls='agm'),
 'YJ-15':dict(ammo=334,w=485,vis={1:'Weapon/Kh22_Kh32'},pic='KH32',cost=60,cls='agm'),
 'YJ-21':dict(ammo=455,w=610,vis={1:'Weapon/Kh47_Kinzhal'},pic='MOD_KINZHAL_HE',cost=75,cls='agm'),
 'CJ-10K':dict(ammo=337,w=943,vis={1:'Weapon/KH101'},pic='Kh_101',cost=50,cls='agm'),
 'GB-6':dict(ammo=296,w=391,vis={1:'Weapon/JSOW/JSOW_LOD'},pic='JSOW',cost=25,cls='bomb'),
 'BBC-5':dict(ammo=296,w=391,vis={1:'Weapon/JSOW/JSOW_LOD'},pic='JSOW',cost=25,cls='bomb'),
 'LS-6':dict(ammo=290,w=376,vis={1:'Weapon/AB500/KAB500'},pic='GBU55',cost=15,cls='bomb'),
 'LT-2':dict(ammo=325,w=456,vis={1:'Weapon/AB500/KAB500'},pic='KAB500',cost=15,cls='bomb'),
 'KAB-500Kr':dict(ammo=325,w=456,vis={1:'Weapon/AB500/KAB500'},pic='KAB500',cost=15,cls='bomb'),
 'KAB-1500Kr':dict(ammo=326,w=457,vis={1:'Weapon/KAB1500'},pic='KAB1500LG',cost=40,cls='bomb'),
 '250 kg bomb':dict(ammo=160,w=459,vis={2:'Weapon/AB250/FAB250_2_Long',3:'Weapon/AB250/FAB250_3_Long',6:'Weapon/AB250/FAB250_6',9:'Weapon/AB250/FAB250_9'},pic='FAB_250',cost=5,cls='bomb'),
 '500 kg bomb':dict(ammo=157,w=475,vis={1:'Weapon/AB500/FAB500_1',2:'Weapon/AB500/FAB500_2_SU'},pic='FAB_500',cost=7.5,cls='bomb'),
 'BL-755':dict(ammo=321,w=472,vis={1:'Weapon/AB500/PBK500_1'},pic='PBK_500U',cost=12.5,cls='bomb'),
}
CANON=[('[PL-10]','PL-10'),('[PL-15C]','PL-15C'),('[PL-15]','PL-15'),('[PL-17]','PL-17'),('[PL-12','PL-12'),('PL-11','PL-11'),('PL-21','PL-21'),('PL-5E','PL-5E'),
 ('PL-7','PL-7'),('PL-8','PL-8'),('PL-9','PL-9'),('TY-90','TY-90'),('AKD-10','AKD-10'),('LJ-7','AKD-10'),('KD-10','AKD-10'),('AKD-9','AKD-9'),('LJ-9','AKD-9'),
 ('HJ-8','HJ-8'),('CM-501GA','CM-501GA'),('FS-70A','FS-70A'),('57mm','57 mm rocket'),('70mm Rocket','70 mm rocket'),('90mm','90 mm rocket'),('S-8KO','S-8KO'),
 ('S-13B','S-13B'),('AKD-88','KD-88'),('AKF-88C','KD-88'),('AKF-98A','AKF-98A'),('Kh-29T','Kh-29T'),('Kh-31A','Kh-31A'),('YJ-91','YJ-91'),('Kh-31P','Kh-31P'),
 ('Kh-59M','Kh-59M'),('YJ-83K','YJ-83K'),('YJ-12','YJ-12'),('YJ-15','YJ-15'),('YJ-21','YJ-21'),('YJ-63','KD-63'),('CJ-10K','CJ-10K'),('GB-6','GB-6'),
 ('YJ-6, 240','BBC-5'),('LS-6-500','LS-6'),('LT-2','LT-2'),('KAB-500Kr','KAB-500Kr'),('KAB-1500Kr','KAB-1500Kr'),('250kg GPB','250 kg bomb'),
 ('FAB-250M','250 kg bomb'),('500kg GPB','500 kg bomb'),('FAB-500M','500 kg bomb'),('BL.755','BL-755')]
DROP=['Durandal','YJ-1000']
# ---- donor airframe pylon slots: (slot, kind)
SLOTS={'RU_MIG29SMT':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(5,'a'),(6,'a')],
 'RU_SU-57':[(1,'b'),(2,'b'),(4,'b'),(5,'b'),(3,'s'),(6,'s'),(7,'t'),(8,'t')],
 'RU_SU27SM':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(9,'h'),(10,'h'),(11,'a'),(12,'a'),(5,'a'),(6,'a'),(7,'t'),(8,'t')],
 'RU_SU30SM':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(9,'h'),(10,'h'),(11,'h'),(12,'a'),(5,'a'),(6,'a'),(7,'t'),(8,'t')],
 'RU_SU34':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(9,'h'),(10,'h'),(11,'h'),(12,'h'),(5,'a'),(6,'a'),(7,'t'),(8,'t')],
 'RU_TU22M3':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(5,'h'),(6,'h')],
 'DLC3_S70_Okhotnik':[(0,'b'),(1,'b')],'RU_Orion':[(0,'h'),(1,'h'),(2,'h'),(3,'h')],
 'US_AH-1Z Viper':[(1,'h'),(2,'h'),(3,'h'),(4,'h'),(5,'t'),(6,'t')],'US_AH64L':[(1,'h'),(2,'h'),(3,'h'),(4,'h')],
 'DLC2_AS365_Dauphin':[(0,'h'),(1,'h')],'US_MH60M_IDAP':[(2,'h'),(3,'h'),(4,'h'),(5,'h')]}
# ---- unit plan: analog chassis (vanilla id), base cost, generation class; None analog keeps chassis
PLAN={915:(44,250,'5th'),966:(44,255,'5th'),921:(294,255,'5th'),971:(294,250,'5th'),929:(297,315,'5th+ (6th-gen prototype)'),944:(297,300,'5th+ (6th-gen prototype)'),
 917:(284,140,'4.5'),955:(284,140,'4.5'),916:(169,165,'4.5'),1242:(169,160,'4.5'),1241:(169,150,'4.5'),974:(169,190,'4.5 EW'),977:(169,190,'4.5 EW'),
 1226:(285,115,'4th'),923:(465,125,'4th'),924:(465,140,'4th'),943:(312,135,'4th'),918:(306,140,'4th'),919:(280,190,'4th (bomber)'),
 975:(744,80,'3rd'),1092:(744,60,'3rd'),1091:(512,40,'2nd (UAV conversion)'),1089:(512,35,'1st'),
 967:(633,180,'UCAV'),946:(None,75,'UCAV'),
 913:(86,105,'attack helicopter'),978:(86,105,'attack helicopter'),1239:(86,105,'attack helicopter'),1104:(8,115,'attack helicopter'),1135:(8,115,'attack helicopter (recon)'),
 940:(532,75,'light attack helicopter'),1103:(532,75,'light attack helicopter'),1236:(532,75,'light attack helicopter'),1132:(532,75,'light attack helicopter (recon)'),
 1134:(532,75,'light attack helicopter (recon)'),1237:(532,75,'light attack helicopter (recon)'),941:(532,65,'light attack helicopter'),1133:(532,65,'light attack helicopter (recon)')}

STRIKE={918,919,967,946}
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--cmo',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];W=t['WeaponsJson'];T=t['TurretsJson']
cmo=json.loads(a.cmo.read_text());receipt={'build':47,'base_build':46,'base_sha256':BASE,'source':'CMO DB3K_519 (sha256 aea7489e3dc4ccd972c7f0153fce1e0ddbf9197d1840f6ee79ea64d5b49e6995)','aircraft':{}}

def canon(name):
    if any(d in name for d in DROP):return None
    for pat,c in CANON:
        if pat in name:return c
    raise KeyError(name)
# ---- pick loadouts
def pick(uid):
    groups={}
    for lo in cmo[str(uid)]['loadouts']:
        tot=defaultdict(int);bad=False
        for w in lo['weapons']:
            c=canon(w['weapon'])
            if c is None:bad=True;break
            tot[c]+=w['count']
        if bad or not tot:continue
        key=tuple(sorted(tot))
        std=not re.search(r'Short-Range|Long-Range|Heavy Short',lo['loadout'])
        cur=groups.get(key)
        if cur is None or (std and not cur[0]):groups[key]=(std,dict(tot),lo['loadout'])
    chosen=[];covered=set()
    cands=sorted(groups.values(),key=lambda x:(-len(x[1]),x[2]))
    while cands and len(chosen)<8:
        best=max(cands,key=lambda x:(len(set(x[1])-covered),min(1,sum(C[k]['cost']*n for k,n in x[1].items())//60),any(C[k]['cls'] in('bvr','ir') for k in x[1]),sum(x[1].values())))
        if chosen and not set(best[1])-covered and len(chosen)>=4:break
        pure_aa=all(C[k]['cls'] in('bvr','ir') for k in best[1])
        if pure_aa and sum(all(C[k]['cls'] in('bvr','ir') for k in c[1]) for c in chosen)>=(1 if uid in STRIKE else 3):
            cands.remove(best);continue
        cands.remove(best);chosen.append(best);covered|=set(best[1])
    # fighters open on an air-to-air loadout; strike types on their first pick
    if not chosen:return chosen
    if U[uid]['Type']==8:
        first=max(chosen,key=lambda c:sum(n for k,n in c[1].items() if C[k]['cls']=='atgm'))
    elif uid in STRIKE:
        first=max(chosen,key=lambda c:sum(C[k]['cost']*n for k,n in c[1].items() if C[k]['cls'] not in('bvr','ir')))
    else:
        aa=[c for c in chosen if all(C[k]['cls'] in('bvr','ir') for k in c[1])];first=aa[0] if aa else max(chosen,key=lambda c:sum(n for k,n in c[1].items() if C[k]['cls'] in('bvr','ir')))
    chosen.remove(first);chosen.insert(0,first)
    return chosen
# ---- shared library rows
ammo_rows={};weapon_rows={};turret_rows={}
OPT_T=t['OptionsJson'][854]  # vanilla F-16 pylon option: clean None pattern
MOD_T=next(m for m in t['ModificationsJson'].values() if m['Type']==3)
TURRET_T=T[166];TW_T=next(iter(t['TurretWeaponsJson'].values()));WA_T=next(iter(t['WeaponAmmunitionsJson'].values()));TU_T=next(iter(t['TurretUnitsJson'].values()))
def ammo(name,heli):
    key=(name,heli and 'heli' in C[name])
    if key not in ammo_rows:
        cat=C[name];src=A[cat['heli'] if key[1] else cat['ammo']]
        fields={'Name':'PLA air '+name+(' heli' if key[1] else ''),'HUDName':name,**cat.get('over',{})}
        ammo_rows[key]=g.add('AmmunitionsJson',src,fields)
    return ammo_rows[key]
def weapon(name,q,heli):
    key=(name,q,heli and 'hw' in C[name])
    if key not in weapon_rows:
        cat=C[name];src=W[cat['hw'] if key[2] else cat['w']]
        ms=q if cat['cls']=='rocket' else min(max(1,src['MagazineSize']),q)
        weapon_rows[key]=g.add('WeaponsJson',src,{'Name':'PLA air '+name+' x'+str(q),'HUDName':name,'MagazineSize':ms})
    return weapon_rows[key]
def visual(name,q,heli,kind):
    cat=C[name];v=(cat.get('hvis') if heli and cat.get('hvis') else cat['vis'])
    if kind=='t' and cat.get('tip'):return cat['tip']
    if 0 in v:return v[0]
    return v[max([k for k in v if k<=q] or [min(v)])]
def turret(parts,heli,kind):
    key=(tuple(parts),heli,kind)
    if key not in turret_rows:
        tid=g.add('TurretsJson',TURRET_T,{'Name':'PLA air pylon '+' + '.join(f'{n} x{q}' for n,q in parts),'ModelFileName':visual(parts[0][0],parts[0][1],heli,kind),'IsDefault':False})
        for i,(n,q) in enumerate(parts):g.add('TurretWeaponsJson',TW_T,{'TurretId':tid,'WeaponId':weapon(n,q,heli),'Order':i})
        turret_rows[key]=tid
    return turret_rows[key]
PREF={'ir':'tasbh','bvr':'asbht','heliaa':'th','atgm':'hb','rocket':'hb','agm':'hb','bomb':'hb'}
def assign(uid,load,stealth,heli):
    slots=[s for s in SLOTS[U[uid]['ModelFileName']] if not stealth or s[1] in 'bs']
    free=list(slots);plan=defaultdict(list)
    order=sorted(load.items(),key=lambda x:'bvr ir heliaa agm bomb atgm rocket'.split().index(C[x[0]]['cls']))
    for name,n in order:
        pref=[s for k in PREF[C[name]['cls']] for s in free if s[1]==k]
        # rockets and bombs fill pods; missiles take one slot each where room allows
        cls=C[name]['cls'];k=max(1,min(len(pref),n if cls in('bvr','ir','agm','heliaa') else max(1,min(len(pref),2 if n<=12 else 4))))
        if not pref:k=0
        use=pref[:k]
        if not use:  # out of slots: ride on the emptiest used pylon
            tgt=min(plan,key=lambda s:len(plan[s]));base,extra=n,0;plan[tgt].append((name,n));continue
        base,extra=divmod(n,len(use))
        for i,s in enumerate(use):
            q=base+(1 if i<extra else 0)
            if q:plan[s].append((name,q));free.remove(s)
    return plan
# ---- per aircraft
CHANGED=set()
for uid,(analog,cost,gen) in PLAN.items():
    u=U[uid];heli=u['Type']==8;model=u['ModelFileName'];rec={'name':u['HUDName'],'class':gen,'analog':analog and U[analog]['HUDName'],'cost':[u['Cost'],cost]}
    stealth=cmo[str(uid)]['stealth_internal_only'] if str(uid) in cmo else False
    chosen=pick(uid) if str(uid) in cmo and model in SLOTS else []
    if chosen:
        # remove old pylon mounts and the weapon-package modification; keep the gun
        for r in g.rows('TurretUnitsJson',uid):
            tr=T[r['TurretId']]
            if not(tr['ModelFileName'] is None and tr['IsDefault']):
                for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tr['Id']]:
                    for wa in [x for x in g.rows('WeaponAmmunitionsJson',uid) if x['WeaponId']==tw['WeaponId']]:g.remove('WeaponAmmunitionsJson',wa['Id'])
                g.remove('TurretUnitsJson',r['Id'])
        for m in g.rows('ModificationsJson',uid):
            if m['Type']==3:
                for o in [o for o in t['OptionsJson'].values() if o['ModificationId']==m['Id']]:g.remove('OptionsJson',o['Id'])
                g.remove('ModificationsJson',m['Id'])
        mid=g.add('ModificationsJson',MOD_T,{'UnitId':uid,'Name':'PLA loadout '+u['HUDName'],'Type':3,'UIName':'Custom_Slot_Weapon_package','ThumbnailFileName':None,'Order':0})
        used_t=set();used_w=set();rec['loadouts']=[]
        for i,(std,load,src) in enumerate(chosen):
            plan=assign(uid,load,stealth,heli);opt={k:(0 if k.startswith('Turret') else copy.deepcopy(v)) for k,v in OPT_T.items() if k!='Id'}
            for (s,kind),parts in plan.items():
                tid=turret(parts,heli,kind);opt[f'Turret{s}Id']=tid;used_t.add(tid)
                for n,q in parts:used_w.add((weapon(n,q,heli),ammo(n,heli),q))
            label=', '.join(f'{n}x {k}' for k,n in sorted(load.items(),key=lambda x:'bvr ir heliaa agm bomb atgm rocket'.split().index(C[x[0]]['cls'])))
            main=max(load,key=lambda k:C[k]['cost']*load[k])
            raw=sum(C[k]['cost']*n for k,n in load.items());raw=raw if raw<=150 else 150+(raw-150)/2  # heavy loads: half price above 150
            ocost=int(round(raw/5.0)*5)
            opt.update(ModificationId=mid,Name=f'PLA loadout {u["HUDName"]} {i}',Order=i,UIName=label,Cost=ocost,OptionPicture=C[main]['pic'],IsDefault=i==0)
            g.add('OptionsJson',OPT_T,opt)
            rec['loadouts'].append({'label':label,'cost':ocost,'cmo_source':src,'slots':{str(s[0]):p for s,p in plan.items()}})
        for tid in sorted(used_t):g.add('TurretUnitsJson',TU_T,{'UnitId':uid,'TurretId':tid,'Order':0})
        for wid,aid,q in sorted(used_w):g.add('WeaponAmmunitionsJson',WA_T,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
        CHANGED.add(uid)
    if analog:
        v=U[analog];g.put('Units',uid,{'Stealth':v['Stealth'],'CurrentStealth':v['CurrentStealth']})
        for tab,field in [('UnitArmorsJson','ArmorId'),('UnitPropulsionsJson','MobilityId'),('SensorUnitsJson','SensorId')]:
            src=[r for r in t[tab].values() if r['UnitId']==analog]
            if not src:continue
            for r in g.rows(tab,uid):g.remove(tab,r['Id'])
            for r in src:g.add(tab,r,{'UnitId':uid})
        for r in g.rows('UnitAbilitiesJson',uid):
            if t['AbilitiesJson'][r['AbilityId']].get('IsDefault'):g.remove('UnitAbilitiesJson',r['Id'])
        for r in [r for r in t['UnitAbilitiesJson'].values() if r['UnitId']==analog and t['AbilitiesJson'][r['AbilityId']].get('IsDefault')]:g.add('UnitAbilitiesJson',r,{'UnitId':uid})
        CHANGED.add(uid)
    g.put('Units',uid,{'Cost':cost});receipt['aircraft'][str(uid)]=rec
# ---- checks
checks=0
def ok(v,label):
    global checks
    assert v,label;checks+=1
for uid in CHANGED:
    mods=[m for m in t['ModificationsJson'].values() if m['UnitId']==uid and m['Type']==3]
    for m in mods:
        opts=[o for o in t['OptionsJson'].values() if o['ModificationId']==m['Id']]
        ok(1<=len(opts)<=8 and sum(bool(o['IsDefault']) for o in opts)==1,('options',uid))
        for o in opts:
            ok(o['Id']<=32767,('option id',o['Id']))
            for i in range(21):
                tid=o.get(f'Turret{i}Id')
                if not tid:continue
                ok(any(r['TurretId']==tid for r in g.rows('TurretUnitsJson',uid)),('turret not linked',uid,tid))
                for tw in [x for x in t['TurretWeaponsJson'].values() if x['TurretId']==tid]:
                    ok(any(r['WeaponId']==tw['WeaponId'] for r in g.rows('WeaponAmmunitionsJson',uid)),('weapon without ammo row',uid,tw['WeaponId']))
    ok(sum(1 for r in g.rows('UnitAbilitiesJson',uid) if t['AbilitiesJson'][r['AbilityId']].get('IsDefault'))<=1,('default abilities',uid))
    if receipt['aircraft'][str(uid)].get('loadouts') and cmo.get(str(uid),{}).get('stealth_internal_only'):
        for lo in receipt['aircraft'][str(uid)]['loadouts']:
            ok(all(dict(SLOTS[U[uid]['ModelFileName']])[int(s)] in 'bs' for s in lo['slots']),('stealth external',uid))
# non-air rows untouched
air=set(PLAN)
for tab in FIELD_TO_FILE:
    for key,row in before[tab].items():
        if tab=='Units' and key not in air:ok(t[tab].get(key)==row,('unit drift',key))
receipt['checks']=checks;receipt['new_rows']={'ammunition':len(ammo_rows),'weapons':len(weapon_rows),'turrets':len(turret_rows)}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-air-loadouts.json',receipt)
(ROOT/'tools/pla-specs/build47-air-checks.json').write_bytes(enc({k:v for k,v in receipt.items() if k!='aircraft'}))
print(json.dumps({k:v for k,v in receipt.items() if k!='aircraft'},indent=2))
for uid,r in receipt['aircraft'].items():print(uid,r['name'],r['class'],r['cost'],len(r.get('loadouts',[])),'|',' / '.join(l['label']+f" ({l['cost']})" for l in r.get('loadouts',[]))[:400])
