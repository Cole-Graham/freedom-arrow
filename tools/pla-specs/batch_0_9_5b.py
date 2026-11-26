"""Freedom Arrow 0.9.4-dev.1 batch data over exact 0.9.3 (build 242). Opened by BA Codex thread 1567745029781454889 (Osama, Spetsnaz Alpha stand-off RPG-30).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'mod';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent),str(Path(__file__).parent/'lateralus')]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.7-dev.22';PREV='0.9.3'
# 0.9.3 (build 242, the playtest released 20 Nov 2026) was built in out/local-093r242.
BASE=json.loads((REL/f'out/receipts/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']   # the one record of builds (repo cleanup step 1)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-093r242/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
O=t['OptionsJson'];SM=t['SquadMembersJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson']
# ---------- 1. Spetsnaz Alpha, stand-off loadout: 6 RPG-30 (Osama 20 Nov 2026 13:2x PST, thread 1567745029781454889: "Next patch, we need to give 6 rpg
# -30 to spets alpha stand off loadout"). The stand-off option (1511, Custom_Option_Standoff) swaps in unit 354. Disposable launchers are one round per
# carrier (SquadMembers.SpecialWeaponId x WeaponAmmunitions.Quantity 1, the vanilla pattern), so 6 RPG-30 = 6 carriers: the 4 existing (583, 584, 592,
# 593) plus riflemen 587 and 589 (AK-107, no special weapon). Squad size (14), primaries, cost and the close-quarters loadout (unit 131) stay as they are.
_RPG30=169;_NEW=(587,589)
ok(O[1511]['UIName']=='Custom_Option_Standoff' and O[1511]['ReplaceUnitId']==354 and U[354]['HUDName'].strip()=='Spetsnaz Alpha','stand-off option -> unit 354')
ok(W[_RPG30]['HUDName']=='RPG-30' and W[_RPG30]['Type']==63,'weapon 169 is the disposable RPG-30')
_carr=lambda:sorted(m['Id'] for m in SM.values() if m.get('UnitId')==354 and m.get('SpecialWeaponId')==_RPG30)
ok(_carr()==[583,584,592,593],('RPG-30 carriers before',_carr()))
_wa=[r for r in WA.values() if r.get('UnitId')==354 and r.get('WeaponId')==_RPG30]
ok(len(_wa)==1 and _wa[0]['Quantity']==1,('RPG-30 ammo row',_wa))
_men=sum(1 for m in SM.values() if m.get('UnitId')==354);ok(_men==14,('squad size',_men))
for mid in _NEW:
    ok(SM[mid]['UnitId']==354 and SM[mid]['PrimaryWeaponId']==911 and not SM[mid].get('SpecialWeaponId'),(mid,'AK-107 rifleman without a special weapon'))
    g.put('SquadMembersJson',mid,{'SpecialWeaponId':_RPG30})
ok(_carr()==[583,584,587,589,592,593] and sum(1 for m in SM.values() if m.get('UnitId')==354)==_men,('6 RPG-30 carriers, squad size unchanged',_carr()))
rec['spetsnaz_alpha_standoff_rpg30']={'unit':354,'option':1511,'carriers':[4,6],'new_carriers':list(_NEW),'rounds_per_carrier':1,'cost_unchanged':O[1511].get('Cost')}
# ---------- 2. Tank guns and autocannons hurt infantry less: anti-infantry rounds x0.55 (Osama 20 Nov 2026 14:1x PST, thread 1567745029781454889: "I liked
# how Tanks and IFV damage was before we removed the cover ... Maybe we should just do a % damage reduction for IFVs and etc across the board to match
# that?", "no no hook I'm just saying we go across the db and change all the values", "like tank cannon and autocannons"). Before 0.9.0-dev.44 calm infantry
# in the open took 0.36 + 0.02 x soldiers of a hit (8 men: 52 %; tank HE with IgnoreCover 0.25: about 64 %); 0.55 sits between. Scope: rounds of main guns
# (Weapons.Type 110) and autocannons (114) on deck ground vehicles (Units.Type 4, not artillery/MLRS/mortar/loitering roles 130-133) that can target infantry
# (TargetType bit 2) with PenetrationAtMinRange < 150, i.e. HE/frag/MP; AP, APFSDS and HEAT keep their damage, and so do rounds that can target planes (AA autocannons:
# ZU-23, 57 mm Derivatsiya, JRVG-1 76 mm). Damage is one value for every target, so these
# rounds also do 45 % less to light vehicles and (autocannons) helicopters: accepted by Osama. A round also fired by anything else (infantry, helicopters,
# planes, MG/AGL/AA weapons, artillery) gets a vehicle copy so the other users keep their damage.
# PARKED, not in the batch (Osama 20 Nov 2026 17:24 PST: "we are not pushing the tank and autocannon HE nerfs right? that's just a proposal?").
# Set _HE_NERF=True only when Osama or Lateralus approve it for a build.
# Superseded 21 Nov 2026 19:51 PST by section 22 (cover_damage_094.py, x0.8 with Ignore Cover 0): leave _HE_NERF False.
_HE_NERF=False
A=t['AmmunitionsJson']
if _HE_NERF:
    _F=0.55;_WT={110,114};_ART={130,131,132,133}
    _deck={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values()}|{t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r.get('SpecializationAvailabilityId') in t['SpecializationAvailabilitiesJson']}
    _veh=lambda u:u is not None and u.get('Type')==4 and u.get('Role') not in _ART
    _q=lambda wa:_veh(U.get(wa.get('UnitId'))) and W.get(wa.get('WeaponId'),{}).get('Type') in _WT
    _sel=lambda a:a is not None and (a.get('TargetType') or 0)&2 and not (a.get('TargetType') or 0)&16 and (a.get('PenetrationAtMinRange') or 0)<150   # plane-capable (AA gun) rounds keep their damage
    _rows=[wa for wa in WA.values() if wa.get('UnitId') in _deck and _q(wa) and _sel(A.get(wa.get('AmmunitionId')))]
    _ids=sorted({wa['AmmunitionId'] for wa in _rows})
    _users={}
    for wa in WA.values():_users.setdefault(wa.get('AmmunitionId'),[]).append(wa)
    _before={i:A[i].get('Damage') for i in _ids};_copies={};_inplace=[]
    for i in _ids:
        other=[wa for wa in _users[i] if not _q(wa)]
        nd=round((A[i].get('Damage') or 0)*_F,3)
        if other:
            c=g.add('AmmunitionsJson',A[i],{'Name':(A[i].get('Name') or '')+' FA vehicle','Damage':nd});_copies[i]=c
            for wa in _users[i]:
                if _q(wa):g.put('WeaponAmmunitionsJson',wa['Id'],{'AmmunitionId':c})
        else:
            g.put('AmmunitionsJson',i,{'Damage':nd});_inplace.append(i)
    ok((len(_ids),len(_rows),len(_copies))==(47,84,0),('scope: 47 rounds on 84 vehicle weapon rows, no copies',len(_ids),len(_rows),len(_copies)))
    ok(all(abs((A[_copies.get(i,i)].get('Damage') or 0)-round((_before[i] or 0)*_F,3))<1e-9 for i in _ids),'every selected round x0.55')
    ok(all(A[i].get('Damage')==_before[i] for i in _copies),'shared originals keep their damage for the other users')
    ok(all(A[wa['AmmunitionId']].get('Damage')==_before.get(wa['AmmunitionId'],A[wa['AmmunitionId']].get('Damage')) for wa in WA.values() if not _q(wa)),'no non-vehicle weapon row changed')
    ok(all((A[_copies.get(i,i)].get('PenetrationAtMinRange') or 0)<150 and not (A[_copies.get(i,i)].get('TargetType') or 0)&16 for i in _ids),'no AP/HEAT or AA round touched')
    ok(not any(_q(wa) and wa['AmmunitionId'] in _copies for wa in WA.values()),'vehicle rows now point at the copies')
    rec['vehicle_anti_infantry_x055']={'factor':_F,'rounds':len(_ids),'in_place':len(_inplace),'vehicle_copies':{str(k):v for k,v in _copies.items()},'weapon_rows':len(_rows),
      'examples':{A[i]['HUDName']:[_before[i],A[_copies.get(i,i)]['Damage']] for i in _ids[:12]}}
# ---------- 3. China special forces and line infantry armour (Osama 20 Nov 2026 15:xx PST, thread 1567745029781454889: "PLAAF Snipers have SF cqc kit,
# they need 8 armor and only 1 smoke like other sniper teams. Godswords, BloodWolvse, Falcons, Sea dragons 8 armor 1 smoke. Troopers and light riflement and
# moto riflemen need 8 armor."). ArmorValue 10 -> 8 (SF) and 6 -> 8 (spec 21 line infantry: Moto. Riflemen, Light Riflemen, AA and AT Troopers); HP stays.
# Own armour rows change in place. Godswords use vanilla row 283 (Elite 12Men, shared with units 113 and 150), so they link the existing vanilla row 314
# (Shock 12Men: the same row with ArmorValue 8). Snipers and Godswords use ability 81 (Sprint30 Smoke x4); they link the existing row 103 (Sprint30 Smoke:
# the same row with 1 smoke). Blood Wolves, Falcons and Sea Dragons already have 1 smoke.
AR=t['ArmorsJson'];UA=t['UnitArmorsJson'];AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
_arm=lambda u:[r for r in UA.values() if r.get('UnitId')==u]
_abl=lambda u:[r for r in UAB.values() if r.get('UnitId')==u]
_same=lambda x,y,skip:all(x.get(k)==y.get(k) for k in set(x)|set(y) if k not in skip)
_OWN={1144:(2012047,10),1183:(2013150,10),1185:(2013216,10),1191:(2013404,10),1196:(2013556,6),1205:(2013818,6),1197:(2013583,6),1198:(2013610,6)}
_names={1144:'Snipers',1181:'Godswords',1183:'Blood Wolves',1185:'Falcons',1191:'Sea Dragons',1196:'Moto. Riflemen',1205:'Light Riflemen',1197:'AA Troopers',1198:'AT Troopers'}
for u,n in _names.items():ok(U[u]['HUDName'].startswith(n) and U[u].get('CountryId')==4 and len(_arm(u))==1,(u,n,'China infantry with one armour row'))
_hp={u:AR[_arm(u)[0]['ArmorId']].get('MaxHealthPoints') for u in _names}
for u,(aid,av) in _OWN.items():
    ok(_arm(u)[0]['ArmorId']==aid and AR[aid].get('ArmorValue')==av and sum(1 for r in UA.values() if r.get('ArmorId')==aid)==1,(u,'own armour row',aid,av))
    g.put('ArmorsJson',aid,{'ArmorValue':8})
ok(_arm(1181)[0]['ArmorId']==283 and _same(AR[283],AR[314],{'Id','Name','ArmorValue','IsDefault'}) and AR[314].get('ArmorValue')==8,'Godswords: row 314 = row 283 with ArmorValue 8')
g.put('UnitArmorsJson',_arm(1181)[0]['Id'],{'ArmorId':314})
ok(_same(AB[81],AB[103],{'Id','Name','SmokeAmmunitionQuantity'}) and (AB[81]['SmokeAmmunitionQuantity'],AB[103]['SmokeAmmunitionQuantity'])==(4,1),'ability 103 = ability 81 with 1 smoke')
for u in (1144,1181):
    r=[x for x in _abl(u) if x.get('AbilityId')==81];ok(len(r)==1,(u,'one Sprint30 Smoke x4 row'));g.put('UnitAbilitiesJson',r[0]['Id'],{'AbilityId':103})
ok(all(AR[_arm(u)[0]['ArmorId']].get('ArmorValue')==8 for u in _names),'all nine units ArmorValue 8')
ok(all(AR[_arm(u)[0]['ArmorId']].get('MaxHealthPoints')==_hp[u] for u in _names),'health points unchanged')
_smk=lambda u:sum(AB[x['AbilityId']].get('SmokeAmmunitionQuantity') or 0 for x in _abl(u))
ok(all(_smk(u)==1 for u in (1144,1181,1183,1185,1191)),'SF and Snipers: 1 smoke')
ok(AR[283].get('ArmorValue')==10 and sorted(r['UnitId'] for r in UA.values() if r.get('ArmorId')==283)==[113,150],'vanilla row 283 unchanged for units 113 and 150')
rec['china_infantry_armor_8']={'units':{str(u):_names[u] for u in _names},'armor_value':8,'godswords_armor_row':[283,314],'smoke_1_ability_row':[81,103],'linked_ability_units':[1144,1181]}
# ---------- 4. Infantry AT launchers aim their anti-tank round in 0.2 s (Osama 20 Nov 2026 16:3x PST, thread 1567745029781454889: "all AT launchers not atgms
# should get 0.2 second aim time only on their AT munition"; list approved 16:49 "Yes add it to the next build"). Launchers = Weapons.Type 62 (reloadable) and 63
# (disposable) carried by deck infantry; AT munition = TargetType 45 (vehicles only, no infantry bit), all HEAT/tandem. Ammunitions.AimTimeMin/MaxOverride 0 -> 0.2
# (the per-round fields vanilla uses for gun-launched ATGMs and direct-fire HEAT; the weapon's 1-2 s stays for HE, thermobaric, incendiary and smoke rounds).
# Kept at vanilla aim (Osama 17:2x: "dual purpose rounds no, leave them at normal vanilal aim time"): SMAW-D HEDP, C90-CR-AM, M72A7 HEDP, DZJ-08, SPG-9M PG-9V. Every user of a changed round must be a launcher on an
# infantry card (Carl Gustaf M3/M4 and RPG-7V2 rows on other cards share three rounds and get 0.2 s too), else the build stops.
_AIM=0.2;_LT={62,63}
_dinf={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if U.get(r['UnitId'],{}).get('Type')==2}
_lw={m[k] for m in SM.values() if m.get('UnitId') in _dinf for k in ('PrimaryWeaponId','SpecialWeaponId') if m.get(k) and W.get(m[k],{}).get('Type') in _LT}
_at=sorted({wa['AmmunitionId'] for wa in WA.values() if wa.get('WeaponId') in _lw and wa.get('UnitId') in _dinf and A[wa['AmmunitionId']].get('TargetType')==45})
ok(len(_at)==20 and len(_lw)==37,('scope: 20 AT rounds on 37 launcher rows',len(_at),len(_lw)))
ok(all(not A[i].get('AimTimeMinOverride') and not A[i].get('AimTimeMaxOverride') for i in _at),'no override set before')
for i in _at:
    users=[wa for wa in WA.values() if wa.get('AmmunitionId')==i]
    ok(all(W.get(wa.get('WeaponId'),{}).get('Type') in _LT and U.get(wa.get('UnitId'),{}).get('Type')==2 for wa in users),(i,A[i].get('HUDName'),'only infantry launchers fire it'))
    g.put('AmmunitionsJson',i,{'AimTimeMinOverride':_AIM,'AimTimeMaxOverride':_AIM})
ok(all((A[i]['AimTimeMinOverride'],A[i]['AimTimeMaxOverride'])==(_AIM,_AIM) for i in _at),'20 AT rounds aim 0.2 s')
_lr=[a for a in {wa['AmmunitionId'] for wa in WA.values() if wa.get('WeaponId') in _lw} if a not in _at]
ok(all(not A[a].get('AimTimeMinOverride') for a in _lr),'other launcher rounds keep the weapon aim time')
_DP={128:'84mm HEDP',593:'90mm dual purpose',2001500:'66mm HEDP',2012025:'DZJ-08 ammunition',105:'PG-9V'}
ok(all(A[i]['HUDName']==n and i not in _at and not A[i].get('AimTimeMinOverride') and not A[i].get('AimTimeMaxOverride') for i,n in _DP.items()),'dual-purpose rounds and PG-9V keep vanilla aim')
rec['launcher_at_aim_0_2']={'aim_s':_AIM,'rounds':{str(i):A[i]['HUDName'] for i in _at},'launchers':len(_lw)}
# ---------- 5. China infantry cards from community art (Osama 20 Nov 2026 00:4x PST, thread 1572407822849810463: "Let's remove the broken arrow logo and use them
# for unit cards and art"; held 00:5x "Don't replace the unit cards yet"; released 16:50 "yes add them" to the earlier name-match mapping of 357c2e52).
# 12 images, BROKEN ARROW mark removed (work/osama-art-20261120; PAP support-hand finger fixed), 816x549 with the vanilla bottom fade -> mod/source/
# runtime-qa/icons/FA_CN_INF_<CARD>-Portrait.png, registered in CardIcons.cs (needs the runtime DLL rebuild). PortraitFileName only.
_CARDS={
 # Airborne and Assault Raiders keep their old portrait (Osama 21 Nov 2026 14:2x PST: "Chinese airborne unit icon should use the old one on the Airborne
 # and Assault Raiders units").
 'AIRBORNE_HELO':['Pathfinders 先遣队','Recon 侦察组'],
 'AIRBORNE_SOF':['Thunder Gods 雷神'],
 'HJ12':['HJ-12 Team'],
 'HJ73':['HJ-73D Team','HJ-8E Team'],
 'MANPAD':['QW-2 Team','Marine QW-2 Team','FN-6 Team','QW-12 Patrol 防空巡逻','AA Troopers 防空班','Air Defense Scouts 防空侦察'],
 'MARINE_JUNGLE':['Marines 陆战队','Marine HJ-8H Team'],
 'JIAO_LONG':['Sea Dragons 蛟龙','Marine Recon'],
 'MECH_INF':['Mech. Rifles 机步班','Armored Scouts 装甲侦察','Moto. Riflemen 摩步班','Infantry 步兵'],
 'PF98':['PF-98 Team','Tank Hunters 坦克杀手','AT Troopers 反坦克组'],
 'QJZ171':['QJZ-89 Team','Weapons Squad 火力班','QJY-201'],
 'SCOUT_SNIPER':['Snipers 狙击组','Armored Sniper Pair 狙击组'],
 'PAP':['PAP Snow Leopards 雪豹','Counter-Raid Team 反袭击队'],
}
_inspec={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r}
_cn=[i for i,u in U.items() if u and u.get('CountryId')==4 and u.get('Type')==2 and i in _inspec]
_icons=SRC/'runtime-qa/icons';_cs=(SRC/'runtime-qa/CardIcons.cs').read_text()
_done={}
for _c,_names in _CARDS.items():
    _p=f'FA_CN_INF_{_c}-Portrait'
    ok((_icons/(_p+'.png')).is_file(),(_p,'icon file'))
    for _x in ('','_BASIC','_HOVER'):ok(f'("{_p}{_x}","{_p}.png")' in _cs,(_p,_x,'CardIcons alias'))
    for _n in _names:
        _ids=[i for i in _cn if U[i]['HUDName']==_n];ok(_ids,(_n,'card exists'))
        for _i in _ids:
            ok(_i not in _done,(_i,'one card per unit'));_done[_i]=(_n,U[_i].get('PortraitFileName'),_p)
            g.put('Units',_i,{'PortraitFileName':_p});ok(U[_i]['PortraitFileName']==_p,_i)
_keep=[i for i in _cn if U[i]['HUDName'] in ('Airborne 空降兵','Assault Raiders 突击队')]
ok(_keep and all(i not in _done and U[i]['PortraitFileName']=='FA_CN_INF_AIRBORNE-Portrait' for i in _keep),('Airborne and Assault Raiders keep the old airborne portrait',[(i,U[i]['PortraitFileName']) for i in _keep]))
ok(len(_done)==34-len(_keep),('community cards (Snipers and QJZ-89 Team are two cards each)',len(_done),len(_keep)))
rec['community_cards']={str(i):{'name':n,'before':b,'after':a} for i,(n,b,a) in sorted(_done.items())}
# ---------- 6. Chinese community bug sheet (QQ "Freedom Arrow Bug反馈及意见收集表", Osama 20 Nov 2026 20:5x PST, thread 1573561286803980289: "bug fixes",
# "this is the Chinese community's ongoing bug fix"). Only clear data errors; balance and content requests wait for Osama.
# 6a. FA-005/FA-009 ZBD-05 shows two 30 mm cannons: turret 2018991 (mount 0 "no ATGM", only used by option 31062) is IsDefault True beside the real
# mount 0 turret 2011194, so the unit gets both. Vanilla option turrets are IsDefault False (3,032 of 3,180 option turrets). 2018991 -> False.
TT=t['TurretsJson'];TUn=t['TurretUnitsJson']
ok(TT[2018991]['Name']=='PLA ZBD-05 mount 0 no ATGM' and TT[2018991]['IsDefault'] is True and TT[2011194]['IsDefault'] is True,'ZBD-05 two default mount-0 turrets')
ok(sorted(r['TurretId'] for r in TUn.values() if r and r.get('UnitId')==1076)==[2011194,2011202,2018991],'ZBD-05 turret links')
ok([o['Id'] for o in O.values() if o and any(o.get(f'Turret{i}Id')==2018991 for i in range(21))]==[31062],'only the No ATGM option uses 2018991')
g.put('TurretsJson',2018991,{'IsDefault':False});ok(TT[2018991]['IsDefault'] is False,'no ATGM turret is option-only')
_def=sorted(r['TurretId'] for r in TUn.values() if r and r.get('UnitId')==1076 and TT[r['TurretId']].get('IsDefault'));ok(_def==[2011194,2011202],('ZBD-05 defaults',_def))
# 6b. FA-023 the guided 90 mm rocket is FS-90A, not FS-90 (display names only: 11 weapons, 1 round, 12 loadout names; stats unchanged).
import re as _re
_fs=_re.compile(r'FS-90(?!A)');_ren={}
for _tab,_f in (('WeaponsJson',('HUDName',)),('AmmunitionsJson',('HUDName',)),('OptionsJson',('UIName',))):
    for _i,_r in list(t[_tab].items()):
        if not _r:continue
        _d={k:_fs.sub('FS-90A',_r[k]) for k in _f if isinstance(_r.get(k),str) and _fs.search(_r[k])}
        if _d:g.put(_tab,_i,_d);_ren[f'{_tab}:{_i}']=_d
ok(len(_ren)==24,('FS-90 renames',len(_ren)))
ok(not any(isinstance(r.get(k),str) and _fs.search(r[k]) for tb,k in (('WeaponsJson','HUDName'),('AmmunitionsJson','HUDName'),('OptionsJson','UIName')) for r in t[tb].values() if r),'no FS-90 left')
rec['qq_bug_sheet']={'zbd05_option_turret_not_default':2018991,'fs90a_renames':_ren}
# ---------- Blue Dragon Japanese tanks: 4-5 s reload (Osama 21 Nov 2026 01:12 PST, thread 1573418243715113213: "lets do 4-5 seconds not flat 4";
# Japan's tank specialty). The hidden 0.9.3 Type 10 / Type 90 guns (flat 4.0 s since 0.9.3-dev.1) become 4.0-5.0 s. Found by name, not id.
_bd={}
for _gn in ('MainGun 120 Type 10 TKG autoloader','MainGun 120 Type 90 L44 autoloader'):
    _w=[i for i,r in W.items() if r and r.get('Name')==_gn];ok(len(_w)==1 and (W[_w[0]]['MagazineReloadTimeMin'],W[_w[0]]['MagazineReloadTimeMax'])==(4.0,4.0),(_gn,'one gun, flat 4 s'))
    g.put('WeaponsJson',_w[0],{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':5.0});ok((W[_w[0]]['MagazineReloadTimeMin'],W[_w[0]]['MagazineReloadTimeMax'])==(4.0,5.0),_gn+' 4-5 s')
    _bd[_gn]={'weapon':_w[0],'reload_s':[[4.0,4.0],[4.0,5.0]]}
rec['blue_dragon_japan_reload']=_bd
# ---------- Blue Dragon tank tab, hidden (Osama 21 Nov 2026 01:1x PST, thread 1573418243715113213: "lets build it all make sure their optics values
# are similar to the US values. I think KSTAM needs to be SA"): K2 (+KSTAM), K1A1, K1, Type 74 STB-2, T-80U (ROK), Type 16 MCV; Type 10/90 optics to US level.
import blue_dragon_tanks;blue_dragon_tanks.apply(t,g,ok,rec)
# Blue Dragon spec 23 'Blue Dragon (Testing Preview)' with those 9 cards (Osama 21 Nov 14:0x: "we can add the blue dragons spec in the next build").
blue_dragon_tanks.add_spec(t,g,ok,rec)
# Blue Dragon 0.9.4-dev.2 items (Osama 21 Nov 2026 14:5x PST, thread 1573418243715113213): K2 front HEAT 1100 -> 1075 and the Type 74 (G) hand-loaded card.
# They were written as a separate apply_0_9_4_dev2.py over the dev.1 package, which no build ran (not in build 249). Folded in here for 0.9.4-dev.3
# (Osama 21 Nov 18:08 "combine all the threads today and build the final build"); apply_0_9_4_dev2.py is retired.
import blue_dragon_dev2;blue_dragon_dev2.apply(t,g,ok,rec)
# ---------- 7. 105 mm tank guns: reload 5-6 s, ZTZ-100 4-5 s (Osama 21 Nov 2026 01:12 PST, thread 1567745029781454889: "I need this to start with all the
# 105 guns going to 5-6 second reload. Except ZTZ-100, that becomes 4-5 seconds"; the flat 4 s is now reserved for Japan's Type 10/90/74). Weapons.
# MagazineReloadTime Min/Max on the 105 mm main guns (Type 110, one round per load). Already 5-6 s: M68E1 (M60A1, M728), M35 (M8 AGS/Thunderbolt, M10
# Booker), ZTZ-80/59D1 gun. The AC-130's M102 is an aircraft howitzer and is left out.
# Stryker MGS (M68A2, 6-7 s) excluded (Osama 21 Nov 01:19 PST: "Stryker is not part of this change").
_R105={2009127:('105 mm high-pressure rifled gun',(4.0,4.0),(5.0,6.0)),2009665:('105 mm rifled gun',(6.0,7.0),(5.0,6.0)),
       2011297:('105 mm high-pressure rifled gun',(4.0,5.0),(5.0,6.0)),2010191:('Prototype 105 mm gun',(4.0,4.0),(4.0,5.0))}
_r=lambda w:(W[w].get('MagazineReloadTimeMin'),W[w].get('MagazineReloadTimeMax'))
for w,(n,old,new) in _R105.items():
    ok(W[w]['HUDName'].strip()==n and W[w].get('Type')==110 and W[w].get('MagazineSize')==1 and _r(w)==old,(w,n,'old reload',_r(w),old))
    g.put('WeaponsJson',w,{'MagazineReloadTimeMin':new[0],'MagazineReloadTimeMax':new[1]})
    ok(_r(w)==new,(w,'new reload',_r(w)))
ok(all(_r(w)==(5.0,6.0) for w in (11,258,657,2010845)),'other 105 mm tank guns already 5-6 s')
ok(_r(81)==(6.0,8.0),'AC-130 M102 unchanged')
ok(_r(24)==(6.0,7.0),'Stryker MGS M68A2 stays 6-7 s (Osama 01:19: "Stryker is not part of this change")')
_zw={wa['WeaponId'] for wa in WA.values() if wa.get('UnitId')==968}
ok(2010191 in _zw and U[968]['HUDName'].strip()=='ZTZ-100','ZTZ-100 (968) fires the prototype 105 mm gun')
rec['reload_105mm']={str(w):{'name':n,'old':list(o),'new':list(nw)} for w,(n,o,nw) in _R105.items()}
# ---------- 8. ZTZ-100 front KE armour 750 -> 700 (Osama 21 Nov 2026 01:18 PST, thread 1567745029781454889: "ZTZ-100 to 700 front armor KE").
# Its own armour row 2010183 (only unit 968); HEAT front 1050 and the other faces unchanged.
_ZA=t['ArmorsJson'];_ZUA=[r for r in t['UnitArmorsJson'].values() if r.get('UnitId')==968]
ok(len(_ZUA)==1 and _ZUA[0]['ArmorId']==2010183 and _ZA[2010183].get('KinArmorFront')==750,'ZTZ-100 armour row 2010183, KE front 750')
ok([r['UnitId'] for r in t['UnitArmorsJson'].values() if r.get('ArmorId')==2010183]==[968],'row used only by the ZTZ-100')
_zb={k:v for k,v in _ZA[2010183].items() if k!='KinArmorFront'}
g.put('ArmorsJson',2010183,{'KinArmorFront':700})
ok(_ZA[2010183]['KinArmorFront']==700 and {k:v for k,v in _ZA[2010183].items() if k!='KinArmorFront'}==_zb,'KE front 700, nothing else changed')
rec['ztz100_ke_front']=[750,700]
# ---------- 9. CTL-181 NLOS has no smoke (Osama 21 Nov 2026 01:38 PST, thread 1573561286803980289: "CTL NLOS remove its smoke"). Its only ability link
# (UnitAbilities 2010702) points at row 2000197 "Smoke x1 NoModel Default", shared by 57 units, so the row stays and the link moves to vanilla row 4
# "Empty ability" (93 vanilla users, no flags), per the ability-row-reuse rule. No option of the CTL-181 sets an ability.
UAb=t['UnitAbilitiesJson'];AB=t['AbilitiesJson']
ok(U[1054]['HUDName'].strip()=='CTL-181 NLOS','unit 1054 is the CTL-181 NLOS')
ok(sorted((r['Id'],r['AbilityId']) for r in UAb.values() if r and r.get('UnitId')==1054)==[(2010702,2000197)] and AB[2000197]['IsSmoke'] is True,'CTL-181 smoke link')
ok(AB[4]['Name']=='Empty ability' and not any(v for k,v in AB[4].items() if k.startswith('Is')),'row 4 has no ability')
_mods={m['Id'] for m in t['ModificationsJson'].values() if m and m.get('UnitId')==1054}
ok(not any(o.get(f'Ability{i}Id') for o in O.values() if o and o.get('ModificationId') in _mods for i in (1,2,3)),'no CTL-181 option sets an ability')
g.put('UnitAbilitiesJson',2010702,{'AbilityId':4})
ok([r['AbilityId'] for r in UAb.values() if r and r.get('UnitId')==1054]==[4] and AB[2000197]['IsSmoke'] is True,'CTL-181 links the empty row; shared smoke row unchanged')
rec['ctl181_no_smoke']={'unit':1054,'unit_ability':2010702,'ability':[2000197,4]}
# ---------- 10. China vehicle ammunition gets vanilla icons (Osama 21 Nov 2026 12:4x PST, thread 1572407822849810463: "can you make sure all Chinese vehicles
# have ammunition icons here? I'm sure all of them can use some icon from Vanilla"). China non-infantry rounds used our placeholder addresses FA_PLA_AMMO_*
# (CANNON/MG/AUTOCANNON draw three plain bullets in the unit panel). Each round now points at the vanilla HUDIcon of the matching vanilla round: tank guns by
# calibre and kind, artillery by calibre, missiles/rockets by their closest vanilla type, MGs/autocannons/AA and aircraft guns AMMO_BULLET_SHORT (as vanilla).
# HUDIcon only; every round touched is used by China units only (HJ-12 is also the HJ-12 Team's round and gets the Javelin icon there too).
import re
# HUDIcon for a China non-infantry round, from what the round is. Vanilla convention: MGs, autocannons, AA guns and aircraft guns all use AMMO_BULLET_SHORT.
NAMED=[ # (regex on HUDName, icon); first match wins
 (r'gun-launched missile','AMMO_RU_TANK_125_ATGM'),(r'^76 mm','AMMO_RU_TANK_125_HE'),(r'^73 mm','AMMO_SMAW_HEAA'),
 (r'^HJ-8','AMMO_TOW_2A'),(r'^HJ-9','AMMO_KORNET'),(r'^HJ-10','AMMO_HELLFIRE_2'),(r'^HJ-12','AMMO_JAVELIN'),(r'^HJ-16','AMMO_JAVELIN'),(r'^HJ-73','AMMO_KONKURS_M'),
 (r'^ABZ-13','AMMO_KORNET'),(r'^NLOS missile','AMMO_JAGM'),(r'^QN-502','AMMO_HERMES_A'),(r'^QN-201','AMMO_GRIFFIN'),(r'^UAV guided missile','AMMO_GRIFFIN'),
 (r'^HQ-7','AMMO_OSA_AKM'),(r'^FK-2000','AMMO_PANCIR_S1'),(r'^(FB-10|QW-)','AMMO_STINGER'),(r'^HQ-6','AMMO_BUK_M2'),(r'^HQ-11','AMMO_TOR_M2'),
 (r'^HQ-1[26]','AMMO_BUK_M3'),(r'^HQ-9','AMMO_S300'),(r'^PL-(2|8|10)\b','AMMO_AIM9M'),(r'^PL-1[25]\b','AMMO_AMRAAM'),
 (r'^DF-','AMMO_ISKANDER_M'),(r'^SY-400','AMMO_ATCAMS'),(r'^BRE','AMMO_SMERCH'),(r'^PHL-(11|81) 122','AMMO_GRAD'),(r'^90 mm unguided rockets','AMMO_S8'),
 (r'^LG3','AMMO_GRENADES'),(r'^120 mm gun-mortar','AMMO_RU_MORTAR_120'),
]
GUN={('125','AP'):'AMMO_RU_TANK_125_AP',('125','HE'):'AMMO_RU_TANK_125_HE',('125','HEAT'):'AMMO_RU_TANK_125_HEAT',
     ('120','AP'):'AMMO_US_TANK_120_AP',('120','HE'):'AMMO_US_TANK_120_HE',('120','HEAT'):'AMMO_US_TANK_120_HEAT',
     ('105','AP'):'AMMO_US_TANK_120_AP',('105','HE'):'AMMO_US_TANK_105_HE',('105','HEAT'):'AMMO_US_TANK_120_HEAT',
     ('100','AP'):'AMMO_RU_TANK_115_AP',('100','HE'):'AMMO_RU_TANK_115_HE',
     ('85','HE'):'AMMO_RU_TANK_115_HE',('85','HEAT'):'AMMO_RU_TANK_115_HEAT'}
ART={'122':'AMMO_RU_ARTILLERY_122','152':'AMMO_RU_ARTILLERY_152mm','155':'AMMO_US_ARTILLERY_155'}
def icon(a):
    k,n=a['HUDIcon'],(a.get('HUDName') or '').strip()
    if n.startswith('100 mm gun / HJ-9'):return 'AMMO_RU_BMP_100_ATGM' if (a.get('PenetrationAtMinRange') or 0)>=300 else 'AMMO_RU_BMP_100_HE'
    for p,ic in NAMED:
        if re.search(p,n):return ic
    if k in('FA_PLA_AMMO_MG','FA_PLA_AMMO_AUTOCANNON'):return 'AMMO_BULLET_SHORT'
    if k in('FA_PLA_AMMO_HOWITZER','FA_PLA_AMMO_MORTAR'):return ART[re.search(r'(\d{3}) mm',n).group(1)]
    if k=='FA_PLA_AMMO_CANNON':
        cal=re.search(r'(\d{2,3}) mm',n).group(1);kind='AP' if re.search(r'APFSDS|\bAP\b',n) else 'HEAT' if 'HEAT' in n else 'HE' if re.search(r'\bHE\b',n) else None
        return GUN[(cal,kind)]
    raise KeyError((a['Id'],k,n))
_vic={A[i].get('HUDIcon') for i in native['AmmunitionsJson'] if i in A}
_cnv={i for i,u in U.items() if u and u.get('CountryId')==4 and u.get('Type')!=2}
_ar={wa['AmmunitionId'] for wa in WA.values() if wa and wa.get('UnitId') in _cnv and wa.get('AmmunitionId') in A and A[wa['AmmunitionId']].get('HUDIcon') not in _vic}
ok(len(_ar)==279 and all(A[i]['HUDIcon'].startswith('FA_PLA_AMMO_') for i in _ar),('279 China non-infantry rounds on placeholder icons',len(_ar)))
ok(all(U.get(wa.get('UnitId'),{}).get('CountryId')==4 for wa in WA.values() if wa and wa.get('AmmunitionId') in _ar),'only China units fire these rounds')
_ic={}
for i in sorted(_ar):
    _ic[i]=(A[i]['HUDIcon'],icon(A[i]));ok(_ic[i][1] in _vic,(i,_ic[i]))
    g.put('AmmunitionsJson',i,{'HUDIcon':_ic[i][1]})
ok(not any(A[wa['AmmunitionId']].get('HUDIcon') not in _vic for wa in WA.values() if wa and wa.get('UnitId') in _cnv and wa.get('AmmunitionId') in A),'every China vehicle round has a vanilla icon')
ok(A[2010195]['HUDIcon']=='AMMO_US_TANK_120_AP' and A[2010197]['HUDIcon']=='AMMO_US_TANK_105_HE' and A[2010199]['HUDIcon']=='AMMO_US_TANK_120_HEAT','ZTZ-100 gun rows')
rec['china_vehicle_ammo_icons']={str(i):{'name':A[i].get('HUDName'),'before':b,'after':n} for i,(b,n) in _ic.items()}
# ---------- 11. Tank Hunters 6 men (Osama 21 Nov 2026 13:16 PST, thread 1567745029781454889: "Tank hunters (which by the way should be 6 man)").
# The 15-per-minute launcher reload of this section is REVERTED (Osama 21 Nov 2026 15:4x PST, same thread: "revert all the RPG 15 rof changes like SMAW and
# Tank hunters and others"; 15:50 "we revert the MAAWS rof, all launcher ROF changes reverted"). Rangers RAWS (74), Rangers MAAWS (410), RPG-29 Vampyr (127)
# and Tank Hunters (1139) had 4 s in 0.9.4-dev.1 (build 248); all go back to the 0.9.3 reload of 6 s (10/min) and their weapon copies are gone.
SW=t['SquadWeaponsJson'];AR=t['ArmorsJson'];UA=t['UnitArmorsJson']
for _w in (202,787,505,788,172,2011919,2016259,61):
    ok(W[_w]['Type']==62 and (W[_w]['MagazineReloadTimeMin'],W[_w]['MagazineReloadTimeMax'])==(6.0,6.0),(_w,W[_w]['HUDName'],'launcher reload stays 6 s (15/min reverted)'))
ok(not any(w.get('MagazineReloadTimeMin')==4.0 and w.get('Type') in (62,63) and 'FA tank hunter' in (w.get('Name') or '') for w in W.values()),'no tank-hunter launcher copies')
# Tank Hunters 1139: 8 -> 6 men. Two plain QBZ-191 riflemen out (newest first); the PF-98A gunner stays; armour 8Men (84) -> vanilla 6Men (82), same AV 6.
_ms=[m for m in SM.values() if m.get('UnitId')==1139];_rf=[m for m in _ms if m.get('PrimaryWeaponId')==2003998 and not m.get('SpecialWeaponId')]
ok(len(_ms)==8 and len(_rf)==7,('Tank Hunters 8 men, 7 riflemen',len(_ms),len(_rf)))
for m in sorted(_rf,key=lambda m:m['Id'])[-2:]:g.remove('SquadMembersJson',m['Id'])
_ua=[r for r in UA.values() if r.get('UnitId')==1139];ok(len(_ua)==1 and _ua[0]['ArmorId']==84 and AR[82]['Name']=='Armor Infantry 6Men' and AR[82]['ArmorValue']==AR[84]['ArmorValue']==6,('Tank Hunters armour row',_ua))
g.put('UnitArmorsJson',_ua[0]['Id'],{'ArmorId':82})
_ms=[m for m in SM.values() if m.get('UnitId')==1139]
ok(len(_ms)==6 and sum(1 for m in _ms if m.get('SpecialWeaponId'))==1 and AR[82]['MaxHealthPoints']==30,'Tank Hunters 6 men, 1 PF-98A, 30 HP')
rec['tank_hunters_6_men']={'men':[8,6],'armor':[84,82]}
# ---------- 12. Helicopter range and optics (Lateralus 21 Nov 2026, thread 1568104480459722894; proposal in the Lateralus 0.9 Changelog, "Helicopter range"
# tab; tested in 0.9.4-dev.1-test1..test4 from codex/batch/lateralus/heli-range; 13:2x PST "queue up all of the proposal for the next 0.9.4 dev build").
# lateralus/heli_range.py: radar row 59 low-altitude optics 1.0 -> 2.0; long-range SAM sensor low optics 2650 -> 2000; long-range radar helicopter range x1.25;
# helicopter-range.json for runtime-qa/HeliRange.cs and HeliRangeCard.cs.
import heli_range as _HR
_HR.apply(t,g,ok);_heli=_HR.contract(t)
ok(len(_heli['radar'])>0 and not _HR.check(lambda tab:t[tab]),'helicopter range contract and radar row 59')
rec['heli_range']={'radar_low_optics':{str(k):list(v) for k,v in _HR.FIX.items()},'radar_groups':len(_heli['radar']),'ammo':len(_heli['ammo'])}
# ---------- 11b. Assaultmen SMAW 4 s reload, thermobaric 2.667 damage and 9 rounds: REVERTED 21 Nov 2026 15:4x PST (all launcher ROF changes reverted) (Osama: "revert all the RPG 15 rof
# changes like SMAW and Tank hunters and others"). The 9 rounds and lower damage only kept the total and per-second damage the same with the faster reload, so
# all three go back to 0.9.3: reload 6 s, thermobaric 4.0 damage, 6 rounds (shipped changed in 0.9.4-dev.1, build 248).
_tbwa=[r for r in WA.values() if r.get('AmmunitionId')==41]
ok(t['AmmunitionsJson'][41]['Damage']==4.0 and len(_tbwa)==1 and _tbwa[0]['Quantity']==6 and _tbwa[0]['UnitId']==63,'Assaultmen SMAW thermobaric: 4.0 damage, 6 rounds (0.9.3)')
# ---------- 13. Z-10K ground optics 3200 -> 2800 (Lateralus 21 Nov 2026 13:4x PST, thread 1568104480459722894: "lower the Z-10K to 2800"). 3200 (dev.44, Osama)
# is not a key in spotting-caps.json, so SpottingCap left the Z-10K uncapped: it saw ground targets at 3200 raw and the Optics tooltip showed 6400 m. 2800 is the
# Exceptional tier: capped at 1200 raw (2400 m). Its own sensor copy (2019482, used only by the Z-10K) changes in place; low/high stay 1250/1000 (card 2500 m).
SN,SUt=t['SensorsJson'],t['SensorUnitsJson']
_caps={float(k):v for k,v in json.loads(z.read('UserData/FreedomArrow/spotting-caps.json'))['OpticsGroundCaps'].items()}
_z10=[r['UnitId'] for r in SUt.values() if r.get('SensorId')==2019482]
ok(SN[2019482]['Name']=='Optics Z-10K 3200' and SN[2019482]['OpticsGround']==3200.0 and len(_z10)==1 and U[_z10[0]]['HUDName'].strip()=='Z-10K',('Z-10K sensor',_z10))
g.put('SensorsJson',2019482,{'Name':'Optics Z-10K 2800','OpticsGround':2800.0})
ok(_caps.get(2800.0)==1200.0 and (SN[2019482]['OpticsLowAltitude'],SN[2019482]['OpticsHighAltitude'])==(1250.0,1000.0),'Z-10K 2800 has a spotting cap (1200 raw)')
rec['z10k_optics']={'sensor':2019482,'ground':[3200.0,2800.0],'cap_raw':_caps[2800.0]}
# ---------- 14. China optics in line with the US and Russia (Lateralus 21 Nov 2026 13:43 PST, thread 1568104480459722894: "Chinese tank optics are way too strong,
# compare them to US and Russian tank optics and come up with a proposed fix. Also look at other chinese vehicles"; 14:1x "ok queue up all the fixes").
# US/RU: older tanks 1300, modernised 1450, top end 1650; recon tanks one each (240+ pts); armed recon IFVs 1650-2300. Ground optics only, raw.
# - Old/cheap line tanks 1450 -> 1300 (T-72A, T-62M, Sprut-SD level), own rows edited in place: ZTZ-59, ZTZ-80, PTL-02, ZTZ-96A. WZ1224 left at 1450 (open question).
# - Recon tanks 2300 -> 1650 (T-90M Razvedchik level): ZTZ-59D1, VT-5 Recon, ZTQ-15 Recon, ZTL-191 Recon -> vanilla row 1 "Good Optics" (1650/1100/1000).
# - ZBD-04A Recon 2800 -> 2300 (M3A3 CFV level) -> vanilla row 3 "Very Good Optics"; ZBD-03 Recon, ZBD-86 Recon 2300 -> 1650 -> row 1.
# - Z-9 1650 -> 1300 (AS-365 Dauphin); Z-20S recon 2800 -> 2300 (US/RU recon utility helicopters) -> row 3.
# Shared vanilla rows 3 and 5 are not edited: the China units are relinked (SensorUnits) to the existing vanilla row of the target tier.
SN,SUt=t['SensorsJson'],t['SensorUnitsJson']
_su=lambda u:[r for r in SUt.values() if r and r.get('UnitId')==u]
_cn={}
for _u,_n,_sid in ((1060,'ZTZ-59',2010815),(1061,'ZTZ-80',2010843),(1059,'PTL-02',2010787),(1082,'ZTZ-96A',2011351),(1107,'Z-9',2011637)):
    _r=_su(_u);_to=1300.0
    ok(U[_u]['HUDName'].strip()==_n and U[_u]['CountryId']==4 and len(_r)==1 and _r[0]['SensorId']==_sid and SN[_sid]['OpticsGround']==(1650.0 if _n=='Z-9' else 1450.0),(_n,'own sensor row'))
    ok({r['UnitId'] for r in SUt.values() if r and r.get('SensorId')==_sid}=={_u},(_n,'sensor row used only by this unit'))
    _cn[_n]={'sensor':_sid,'ground':[SN[_sid]['OpticsGround'],_to]};g.put('SensorsJson',_sid,{'OpticsGround':_to})
for _u,_n,_old,_new in ((1260,'ZTZ-59D1',3,1),(1262,'VT-5 Recon',3,1),(1240,'ZTQ-15 Recon',3,1),(1263,'ZTL-191 Recon',3,1),(1255,'ZBD-04A Recon',5,3),
                        (1257,'ZBD-03 Recon',3,1),(1258,'ZBD-86 Recon',3,1),(1243,'Z-20S',5,3)):
    _r=_su(_u)
    ok(U[_u]['HUDName'].strip()==_n and U[_u]['CountryId']==4 and len(_r)==1 and _r[0]['SensorId']==_old,(_n,'on vanilla sensor',_old))
    g.put('SensorUnitsJson',_r[0]['Id'],{'SensorId':_new});_cn[_n]={'sensor':[_old,_new],'ground':[SN[_old]['OpticsGround'],SN[_new]['OpticsGround']]}
ok((SN[1]['Name'],SN[1]['OpticsGround'],SN[3]['Name'],SN[3]['OpticsGround'],SN[5]['OpticsGround'])==('Good Optics',1650.0,'Very Good Optics',2300.0,2800.0),'vanilla tier rows unchanged')
_caps=_caps if '_caps' in dir() else {float(k):v for k,v in json.loads(z.read('UserData/FreedomArrow/spotting-caps.json'))['OpticsGroundCaps'].items()}
_SAv=t['SpecializationAvailabilitiesJson'];_av={r['UnitId'] for r in _SAv.values() if r}|{r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r and r.get('SpecializationAvailabilityId') in _SAv}
ok(all(SN[r['SensorId']]['OpticsGround'] in _caps for r in SUt.values() if r and r.get('UnitId') in _av and U.get(r['UnitId'],{}).get('CountryId')==4),'every China sensor in a deck has a spotting cap')
rec['china_optics']=_cn
_heli=_HR.contract(t)  # sensor groups after sections 13-14
# ---------- 13. QN-506 to the Vehicles tab with BMPT optics (Osama 21 Nov 2026 14:2x PST, thread 1567745029781454889: "Move QN-506 to Vehicle tab and give
# it the same optics as BMPT"). Units.CategoryType 0 (Recon tab) -> 2 (Vehicles, BMPT's tab). Its own sensor row 2009631 already had the BMPT values
# (1450 / 900 / 1000); the unit now links BMPT's vanilla row 23 "Medium Plus Optics", so both always match.
_QN,_BMPT=937,240;SUJ=t['SensorUnitsJson'];SJ=t['SensorsJson']
ok(U[_QN]['HUDName'].strip()=='QN-506' and U[_QN]['CategoryType']==0 and U[_BMPT]['CategoryType']==2,('QN-506 in Recon, BMPT in Vehicles',U[_QN]['CategoryType']))
g.put('Units',_QN,{'CategoryType':U[_BMPT]['CategoryType']})
_qs=[r for r in SUJ.values() if r.get('UnitId')==_QN];_bs=[r for r in SUJ.values() if r.get('UnitId')==_BMPT]
ok(len(_qs)==1 and len(_bs)==1 and _bs[0]['SensorId']==23,('one sensor each, BMPT on row 23',_qs,_bs))
_old=_qs[0]['SensorId'];g.put('SensorUnitsJson',_qs[0]['Id'],{'SensorId':_bs[0]['SensorId']})
_k=('OpticsGround','OpticsLowAltitude','OpticsHighAltitude')
ok([SJ[[r for r in SUJ.values() if r.get('UnitId')==_QN][0]['SensorId']][k] for k in _k]==[SJ[23][k] for k in _k],'QN-506 optics = BMPT optics')
ok(not any(o.get('MainSensorId') or o.get('ExtraSensorId') for o in O.values() if o and t['ModificationsJson'].get(o.get('ModificationId'),{}).get('UnitId')==_QN),'no QN-506 loadout swaps its sensor')
rec['qn506_vehicle_tab']={'unit':_QN,'category':[0,2],'sensor':[_old,23],'optics':[SJ[23][k] for k in _k]}
# ---------- 14. QN-506 missile = CH-901 clone; HJ-10 laser-guided cruise missile with its own designator (Osama 21 Nov 2026 14:2x PST, thread
# 1567745029781454889: "QN-506 should just be a clone of the CH-901. Reworked. HJ-10 should also be reworked. HJ-10 is a cruise missile (NOT interceptable)
# like the CH-901. But it retains its current ATGM stats in terms of penetration and damage. HJ-10 gets its own laser designator. That way for the NLOS feature
# to work, it needs to be lazed"; earlier "QN-502 should be 30mm penetration", "QN-506 should not be able to hit aircraft").
# (a) QN-506's QN-502 launcher (2009647) and round (2009651) take every field of the Blood Wolves' CH-901 launcher (2018447) and round (2018448) except
#     Id/Name/HUDName: loitering, laser-guided, cruise path (TrajectoryType 200), not interceptable, 15 damage, 30 penetration, ground targets only (so no
#     helicopters). QN-506 keeps its 4 rounds and its own laser (ability "Laser Smoke x2").
# (b) HJ-10 (936) round 2009623: CH-901 flight (cruise path, not interceptable, laser-guided, speed/burn/turn/seeker of the CH-901) with its own ATGM numbers
#     kept: 13 damage, 90 penetration, 800 range, vehicle/ship targets, 25 m splash, top attack, stress 360, supply 75. Seeker distance = its 800 range.
# (c) HJ-10 gets a laser designator: a new ability row = its shared radar+smoke row 2009175 (PGZ-09, AFT-10 keep it) + vanilla "Laser Veh Default" laser
#     (1500, usable on the move). No existing row has radar + smoke + laser (ability-row-reuse rule: new row only for a unique combination).
# (d) nlos.json unchanged (Osama 14:35 "keep the hooks so we don't break anything"): HJ-10 keeps the NLOS fire hook and the keep-lock.
SKIP_F={'Id','Name','HUDName'}
_CHW,_CHA,_QW,_QA,_HJ,_HJA=2018447,2018448,2009647,2009651,936,2009623
ok(W[_CHW]['HUDName']=='CH-901' and A[_CHA]['HUDName']=='CH-901' and W[_QW]['HUDName'].startswith('QN-502') and A[_QA]['HUDName'].startswith('QN-502'),'CH-901 and QN-502 rows')
ok({r['UnitId'] for r in WA.values() if r.get('AmmunitionId')==_QA}=={937} and {r['UnitId'] for r in WA.values() if r.get('WeaponId')==_QW}=={937},'QN-502 rows only on QN-506')
_qnq=[r['Quantity'] for r in WA.values() if r.get('AmmunitionId')==_QA]
g.put('WeaponsJson',_QW,{k:v for k,v in W[_CHW].items() if k not in SKIP_F})
_qicon=A[_QA]['HUDIcon'];g.put('AmmunitionsJson',_QA,{k:v for k,v in A[_CHA].items() if k not in SKIP_F|{'HUDIcon'}})
ok(A[_QA]['HUDIcon']==_qicon and _qicon in _vic,('QN-502 round keeps its vanilla icon from section 10',_qicon))
ok(all(W[_QW].get(k)==W[_CHW].get(k) for k in W[_CHW] if k not in SKIP_F) and all(A[_QA].get(k)==A[_CHA].get(k) for k in A[_CHA] if k not in SKIP_F|{'HUDIcon'}),'QN-502 = CH-901 clone')
ok(A[_QA]['PenetrationAtMinRange']==30 and A[_QA]['CanBeIntercepted'] is False and not (int(A[_QA]['TargetType'])&(8|16)),'QN-502: 30 penetration, not interceptable, no helicopters or planes')
ok([r['Quantity'] for r in WA.values() if r.get('AmmunitionId')==_QA]==_qnq==[4],'QN-506 keeps 4 rounds')
ok(any(AB_.get('IsLaserDesignator') for AB_ in [t['AbilitiesJson'][r['AbilityId']] for r in t['UnitAbilitiesJson'].values() if r.get('UnitId')==937]),'QN-506 has its own laser')
ok({r['UnitId'] for r in WA.values() if r.get('AmmunitionId')==_HJA}=={_HJ} and A[_HJA]['HUDName']=='HJ-10 guided missile','HJ-10 round only on HJ-10 (936)')
_keep={k:A[_HJA][k] for k in ('Damage','PenetrationAtMinRange','PenetrationAtGroundRange','GroundRange','MinimalRange','TargetType','HealthAOERadius','IsTopArmorArmorAttack','TopArmorAttack','StressDamage','SupplyCost','ResupplyTime','ArmorTargeted')}
_fly=('TrajectoryType','CanBeIntercepted','CanBeTargeted','LaserGuided','Seeker','MaxSpeed','Acceleration','MuzzleVelocity','BurnTime','RotationSpeed','PreEgnitionRotationSpeed','SeekerAngle','CanReaquire','MainEngineIgnitionDelay','AimStartDelay','LoftAngle','LoftHeight','OverflyHeight')
g.put('AmmunitionsJson',_HJA,{**{k:A[_CHA][k] for k in _fly},'MaxSeekerDistance':_keep['GroundRange']})
ok(all(A[_HJA][k]==v for k,v in _keep.items()),'HJ-10 keeps its ATGM damage, penetration, range and targets')
ok(A[_HJA]['CanBeIntercepted'] is False and A[_HJA]['TrajectoryType']==200 and A[_HJA]['LaserGuided'] is True,'HJ-10: cruise path, not interceptable, laser-guided')
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
_hjab=[r for r in UAB.values() if r.get('UnitId')==_HJ]
ok(len(_hjab)==1 and _hjab[0]['AbilityId']==2009175 and AB[10]['Name']=='Laser Veh Default' and AB[10]['IsLaserDesignator'],('HJ-10 ability row',_hjab))
_las={k:AB[10][k] for k in ('IsLaserDesignator','LaserMaxRange','LaserUsableInMove')}
_nab=g.add('AbilitiesJson',AB[2009175],{'Name':'PLA HJ-10 radar smoke laser',**_las})
g.put('UnitAbilitiesJson',_hjab[0]['Id'],{'AbilityId':_nab})
ok(AB[_nab]['IsRadar'] and AB[_nab]['IsSmoke'] and AB[_nab]['IsLaserDesignator'] and AB[_nab]['LaserMaxRange']==1500,'HJ-10 ability: radar + smoke + laser')
ok(sorted(U[r['UnitId']]['HUDName'] for r in UAB.values() if r.get('AbilityId')==2009175 and U.get(r['UnitId']))==['AFT-10','PGZ-09'],'PGZ-09 and AFT-10 keep the shared row')
_nlos=json.loads(z.read('UserData/FreedomArrow/nlos.json'))
# (Superseded 24 Nov 2026 by nlos_cruise_1124.py: nlos.json lists no rounds; the two nlos.json checks here were removed.)
# Osama 21 Nov 14:35: "lets just keep the hooks so we don't break anything": nlos.json stays as it is (HJ-10 keeps both the fire hook and the keep-lock).
rec['qn506_ch901_hj10_laser']={'qn502_weapon':_QW,'qn502_round':_QA,'clone_of':[_CHW,_CHA],'hj10_round':_HJA,'hj10_ability':[2009175,_nab],'nlos_keep_lock':_nlos['ammunition']}
# ---------- 15. Tank front HEAT tiers (Osama 21 Nov 2026, thread 1567745029781454889: "top end tanks should die in 4 shots" (PF-98 and Kornet-M);
# "There needs to be step between the mid-high and mid tanks. 950 ... SEPV2, SEP, and BVM"; "SEPV2 TUA same as others. ZTZ-100 top end, BMPT and M1150 keep them
# in the mid-high tier HEAT armor. FEP will be mid-high tier"; 15:00 "I didn't see these tank armor changes on the patch you just pushed?"). Only HeatArmorFront
# changes; KE, sides, rear, top and HP stay. Tiers: top end 1075 (PF-98 4 frontal hits, Kornet-M 4), mid-high 950 (PF-98 4, Kornet-M 3); modern/mid/old unchanged.
# T-80BVM: its obr. 2018+ option is already 950; its base (800) stays until Osama decides. T-15 / VN20 (heavy IFV class) are not in this section.
_TOP={964:'Abrams X',503:'Leopard 2A8',191:'M1A2 SEP v3',13:'T-14 Armata',238:'T-90M',237:'T-90M Razvedchik',985:'Object 640',904:'ZTZ-99A',968:'ZTZ-100'}
_MH={243:'M1A2 SEP v2',2:'M1A2 SEP v2 TUA',244:'M1A2 SEP',54:'M1A1 FEP',240:'BMPT Terminator',457:'M1150 Assault Breacher'}
UAJ=t['UnitArmorsJson'];ARJ=t['ArmorsJson']
_users={}
for r in UAJ.values():_users.setdefault(r['ArmorId'],set()).add(r['UnitId'])
_tiers={};_before={}
for tier,units,val,allowed in (('top',_TOP,1075,(1100,1200,1050)),('mid-high',_MH,950,(1100,1200,1050))):
    for uid,name in units.items():
        ok(U[uid]['HUDName'].strip().startswith(name.split()[0]),(name,uid,U[uid]['HUDName']))
        for r in [r for r in UAJ.values() if r.get('UnitId')==uid]:
            aid=r['ArmorId'];ok(ARJ[aid]['HeatArmorFront'] in allowed,(name,aid,ARJ[aid]['HeatArmorFront']))
            ok(_users[aid]<=set(units),(name,aid,'row shared outside its tier',sorted(_users[aid]-set(units))))
            _before.setdefault(aid,ARJ[aid]['HeatArmorFront']);_tiers[aid]=(tier,val)
_snap={i:dict(r) for i,r in ARJ.items() if r and i not in _tiers}
for aid,(tier,val) in sorted(_tiers.items()):g.put('ArmorsJson',aid,{'HeatArmorFront':val})
ok(len(_tiers)==34,('34 armour rows (Abrams X shares the SEP v3 rows, Razvedchik shares T-90M base)',len(_tiers)))
ok(all(ARJ[a]['HeatArmorFront']==v for a,(tr,v) in _tiers.items()),'every tier row at its value')
ok(all(ARJ[i]==r for i,r in _snap.items()),'no other armour row changed')
ok(ARJ[2010183]['HeatArmorFront']==1075 and ARJ[2010183]['KinArmorFront']==700,'ZTZ-100: HEAT 1075, KE 700 (section 8)')
import math
_hits=lambda B,P,A,hp=14:math.ceil(hp/(B*P*P/(P*P+A*A))-1e-9)
ok((_hits(10,800,1075),_hits(10.5,950,1075),_hits(10,800,950),_hits(10.5,950,950))==(4,4,4,3),'PF-98 / Kornet-M: top 4 / 4, mid-high 4 / 3')
rec['tank_heat_tiers']={'top_1075':{str(a):_before[a] for a,(tr,v) in _tiers.items() if tr=='top'},'mid_high_950':{str(a):_before[a] for a,(tr,v) in _tiers.items() if tr=='mid-high'}}
# ---------- 16. High-end IFV class (Osama 21 Nov 2026, thread 1567745029781454889: "700mm will be the high end IFV armor then, reserved for AMPV Reactive armor,
# Bradley variants with BUSK 3 and the XM 30 (it should have 200 KE). T15 barbaris should be adjust to the (current) T-80U armor profile ... Stryker SRAT II armor
# also gets 700mm (but they keep lower KE). For China, only ZBD -20 gets it and the VN-20 get's the same T-80U armor profile as the T-15"; "the 700mm upgrades are
# +25 points and knock out 5 move speed for tracked vehicles and 10 move speed for wheeled vehicles"; "leave the bradley for now its slow anyways"; 15:04 "No just
# apply them"). Defaults taken where he had not answered: the +25 / speed rule applies to the 700 upgrades only (XM30 and ZBD-20 have 700 as base armour, no
# penalty); speed means road and cross-country, reverse unchanged. Bradley BUSK 3 keeps its speed. Stryker row 2000018 ("SRAT Trophy", HEAT 200) is used by no option.
_SRAT=(2000235,2000236,2000237,2000238,2000239,2000240,2000380,2000381,2000382,2000383,2000384,2000385,2000386,2000387)
_700=(2000015,2000026,2000027,2001818,2009807)+_SRAT
for a_ in _700:ok(ARJ[a_]['HeatArmorFront']==600,(a_,ARJ[a_]['Name'],'front HEAT 600'))
for a_ in _700:g.put('ArmorsJson',a_,{'HeatArmorFront':700})
ok(ARJ[2001818]['KinArmorFront']==300 and U[983]['HUDName'].strip()=='XM30','XM30 KE front 300');g.put('ArmorsJson',2001818,{'KinArmorFront':200})
_us={}
for r in UAJ.values():_us.setdefault(r['ArmorId'],set()).add(r['UnitId'])
ok(_us[2000015]=={16,26,37,28} and _us[2000026]==_us[2000027]=={41} and _us[2001818]=={983} and _us[2009807]=={945} and all(len(_us[x])==1 for x in _SRAT),'700 rows used only by their vehicles')
_T80=[r['ArmorId'] for r in UAJ.values() if r.get('UnitId')==239 and ARJ[r['ArmorId']].get('IsDefault')]
ok(_T80==[2000475],('T-80U base armour row',_T80))
_prof={k:ARJ[2000475][k] for k in ('KinArmorFront','KinArmorSides','KinArmorRear','KinArmorTop','HeatArmorFront','HeatArmorSides','HeatArmorRear','HeatArmorTop','MaxHealthPoints')}
for a_,uid in ((2000437,255),(2019365,1274)):
    ok(_us[a_]=={uid} and ARJ[a_]['HeatArmorFront']==1100,(a_,uid,'T-15 / VN20 own row'));g.put('ArmorsJson',a_,_prof)
    ok(all(ARJ[a_][k]==v for k,v in _prof.items()),(uid,'= T-80U profile'))
# costs: every 700 upgrade costs 25; armour+APS options keep their APS share. Exception, Stryker M-SHORAD only: its armour options keep
# Lateralus's point distribution, SRAT II 15 (70) and SRAT II / APS 45 (1934) (Osama 21 Nov 2026 17:27 PST, thread 1567745029781454889: "yeah lets keep
# Lateralus's point distribution", "for this unit only"; they were 25 and 55 in 0.9.4-dev.2, build 249). Its 700 armour and -10 speed stay.
_COST={1764:(20,25),1773:(20,25),1753:(25,25),1759:(25,25),60:(15,25),2082:(55,65),44:(10,25),50:(20,25),70:(15,15),1943:(10,25),1946:(10,25),8:(25,25),25:(25,25),42:(25,25),1934:(45,45),1944:(50,65),1947:(50,65),1894:(65,65)}
for o,(b,n) in _COST.items():
    ok(O[o]['Cost']==b and O[o]['ArmorId'] in _700,(o,O[o].get('UIName'),O[o]['Cost'],O[o]['ArmorId']))
    if b!=n:g.put('OptionsJson',o,{'Cost':n})
ok((O[70]['Cost'],O[1934]['Cost'])==(15,45) and O[70]['ArmorId'] in _700 and O[1934]['ArmorId'] in _700,'Stryker M-SHORAD keeps Lateralus prices 15/45 with 700 armour')
_unp=sorted((o['Id'],o.get('UIName'),o['ArmorId']) for o in O.values() if o and o.get('ArmorId') in _700 and o['Id'] not in _COST)
ok(all(x[2] in (2001818,2009807) for x in _unp),('every 700 upgrade option is priced; only XM30/ZBD-20 base-armour options left',_unp))
# speed: wheeled Strykers -10 (their SRAT rows 189/238 are used only by Stryker armour options); tracked AMPV -5 on a new row (206 is shared with the M1287 MCV)
MBJ=t['MobilityJson']
ok({o['MobilityId'] for o in O.values() if o and o.get('MobilityId') in (189,238)}=={189,238} and not [r for r in t['UnitPropulsionsJson'].values() if r.get('MobilityId') in (189,238) and r.get('UnitId') not in (5,20,21,22,24,25,33,452)],'Stryker armour speed rows only on Strykers')
for m in (189,238):
    ok((MBJ[m]['MaxSpeedRoad'],MBJ[m]['MaxCrossCountrySpeed'])==(100.0,50.0),(m,'100 / 50'));g.put('MobilityJson',m,{'MaxSpeedRoad':90.0,'MaxCrossCountrySpeed':40.0})
ok((MBJ[206]['MaxSpeedRoad'],MBJ[206]['MaxCrossCountrySpeed'])==(70.0,50.0) and O[60]['MobilityId']==0 and O[2082]['MobilityId']==0,'AMPV 70 / 50, armour options keep the base speed')
_am=g.add('MobilityJson',MBJ[206],{'Name':'Tracks AMPV armoured','MaxSpeedRoad':65.0,'MaxCrossCountrySpeed':45.0})
_amp=[r for r in t['UnitPropulsionsJson'].values() if r.get('UnitId')==41]
if not any(r.get('MobilityId')==_am for r in _amp):g.add('UnitPropulsionsJson',_amp[0],{'MobilityId':_am})
for o in (60,2082):g.put('OptionsJson',o,{'MobilityId':_am})
ok((MBJ[_am]['MaxSpeedRoad'],MBJ[_am]['MaxCrossCountrySpeed'],MBJ[_am]['MaxSpeedReverse'])==(65.0,45.0,MBJ[206]['MaxSpeedReverse']),'AMPV armoured 65 / 45')
ok(all(O[o]['MobilityId']==0 for o in (1753,1759,1764,1773)),'Bradley BUSK 3 keeps its speed')
rec['ifv_700_class']={'rows_700':list(_700),'xm30_ke':[300,200],'t80u_profile_to':{'2000437':255,'2019365':1274},'costs':{str(o):list(v) for o,v in _COST.items()},'stryker_speed':[[100,50],[90,40]],'ampv_mobility':_am}
# ---------- 17. Top-attack ATGMs kill top-end tanks in 2 hits; long-range AAMs give the shooter away (Osama 21 Nov 2026 15:1x PST, thread
# 1567745029781454889: "Top attack yes to 2 hit"; "All long range missiles R-37, JATM, PL-17, AIM-260, P-21 all need more flash so that a J-36 gets detected always
# and isn't invisible anymore"; "BVM base stays modern, QN-506 autocannon keeps helo range ... Other parked, hold for now").
# (a) The 140-penetration top-attack ATGMs (Javelin, Spike LR, TOW-2B, HJ-16, HJ-16 IIR, HJ-12E, GAM-102LR, Blue Dragon KSTAM) 10.5 -> 11 damage, and HJ-12 also 130 -> 140 penetration:
#     11 x 140^2 / (140^2 + 100^2) = 7.28 per hit, 2 hits = 14.6 > 14 HP on top armour 100. RBS 56 and Sokol-V already kill in 2 and keep 10.5.
# (b) FlashPerShot 1.0 -> 3.5 on every long-range AAM launcher (R-37, JATM / AIM-260, PL-17, PL-21): one shot takes the shooter's WeaponFlash from 1 to the
#     FogOfWarConfig cap 4.5 (it decays 0.15 per second). Whether and how far air detection uses WeaponFlash is not verified in code: check in game.
_TA=[i for i,a_ in A.items() if a_ and a_.get('IsTopArmorArmorAttack') and a_.get('Seeker') and a_.get('ArmorTargeted')==2 and a_.get('Damage')==10.5
     and a_.get('PenetrationAtMinRange') in (130.0,140.0) and any(r.get('AmmunitionId')==i and U.get(r.get('UnitId'),{}).get('DisplayInArmory') for r in WA.values())]
_tan=sorted({(A[i].get('HUDName') or '').strip() for i in _TA})
ok(_tan==['GAM-102LR ammunition','HJ-12 ammunition','HJ-12E ammunition','HJ-16','HJ-16 IIR','Javelin','KSTAM','Spike LR','TOW-2B'],('top-attack ATGM rounds (KSTAM = Blue Dragon K2 gun missile)',_tan))
for i in _TA:
    f={'Damage':11.0}
    if A[i]['PenetrationAtMinRange']==130.0:f.update(PenetrationAtMinRange=140.0,PenetrationAtGroundRange=140.0)
    g.put('AmmunitionsJson',i,f)
ok(all(A[i]['Damage']==11.0 and A[i]['PenetrationAtMinRange']==A[i]['PenetrationAtGroundRange']==140.0 for i in _TA),'top-attack ATGMs 11 damage, 140 penetration')
ok(all(math.ceil(14/(11*140**2/(140**2+a_**2))-1e-9)==2 for a_ in (60,80,100)),'2 hits on every tank top')
ok(A[572]['Damage']==10.5 and A[2000161]['Damage']==10.5,'RBS 56 and Sokol-V unchanged')
_LR={437:'R-37',675:'JATM',2001659:'JATM',2016472:'PL-17',2016476:'PL-21',2016482:'PL-17',2016509:'PL-17',2017635:'PL-17'}
for w_,n_ in _LR.items():ok(W[w_]['HUDName']==n_ and W[w_]['FlashPerShot']==1.0,(w_,n_,W[w_].get('FlashPerShot')));g.put('WeaponsJson',w_,{'FlashPerShot':3.5})
ok(not [w_ for w_,x in W.items() if x and (x.get('HUDName') or '') in ('R-37','JATM','PL-17','PL-21','AIM-260') and w_ not in _LR],'every long-range AAM launcher covered')
rec['top_attack_and_aam_flash']={'top_attack_rounds':_TA,'damage':[10.5,11.0],'hj12_pen':[130,140],'aam_flash':{str(k):[1.0,3.5] for k in _LR}}
# ---------- 18. Split-loadout cards show in the Arsenal again (Osama 21 Nov 2026 15:3x PST: "we lost our American Airborne, not the NGSW. We need both in US
# air"). 0.9.0-dev.11 turned the Rangers / Airborne / Mech. Riflemen squad-loadout swaps into separate cards (new specialization rows), but the variant units kept
# Units.IsUnitModification = True, the flag for "reached only through a loadout option". With the options gone, those cards were hidden. Clear the flag on every
# unit that has its own card and is no longer the target of any option: Airborne (64), Rangers CQC (409), Mech. Riflemen MAAWS (707).
SAJ_=t['SpecializationAvailabilitiesJson']
_rep={o['ReplaceUnitId'] for o in O.values() if o and o.get('ReplaceUnitId')}
_lost=sorted({a_['UnitId'] for a_ in SAJ_.values() if a_ and U.get(a_.get('UnitId'),{}).get('IsUnitModification') and a_['UnitId'] not in _rep})
ok(_lost==[64,409,707],('hidden split cards',_lost,[U[x]['HUDName'] for x in _lost]))
for x in _lost:g.put('Units',x,{'IsUnitModification':False})
ok(not [a_ for a_ in SAJ_.values() if a_ and U.get(a_.get('UnitId'),{}).get('IsUnitModification') and a_['UnitId'] not in _rep],'no card left on a loadout-only unit')
ok(len([a_ for a_ in SAJ_.values() if a_ and a_.get('UnitId') in (64,351) and a_.get('SpecializationId')==5])==2,'US Airborne infantry has both Airborne and Airborne NGSW')
rec['split_cards_visible']={str(x):U[x]['HUDName'].strip() for x in _lost}
# ---------- 19. China balance patch (Osama 21 Nov 2026 18:2x PST, thread 1567745029781454889: Doc "China changes 9.4" 1uhNb7jt, "I have a list of new
# changes for you", "Balance patch"). All 37 lines; HJ-10 = 140 points (18:3x). Readings and rows: china_balance_094.py.
import china_balance_094;china_balance_094.apply(t,g,ok,rec)
# ---------- 20. Helicopter launcher layouts (Osama 21 Nov 2026 19:1x PST, thread 1567745029781454889: "Z-10 Fire support TY-90's should only have 2
# launchers (but 8 missiles) ... see if there are any launcher oddities"). Z-10 family Fire support and Z-21 Heavy anti-armor: same missiles, fewer and even
# launchers. Z-19 / Z-9WA (2-pylon Dauphin body) not changed: asked. See heli_launchers_094.py.
import heli_launchers_094;heli_launchers_094.apply(t,g,ok,rec)
# ---------- 21. Z-19 family and armed Z-9WAs on the AH-1W SuperCobra stand-in (Osama 21 Nov 2026 19:3x PST, thread 1567745029781454889: "Z-19 should
# just use the Cobra as its standin", "Z-9 and Z-19 that way we have more pylons, but just don't change the stats"). See donor_cobra_094.py.
import donor_cobra_094;donor_cobra_094.apply(t,g,ok,rec)
# ---------- 22. Infantry cover and damage (Osama 21 Nov 2026 19:08-19:43 PST, thread 1573561286803980289, "you can push this into the build" 19:51): tank
# guns, autocannons and HMGs x0.8 on anti-infantry rounds (0.5 / 0.2 / 0.1 steps), Ignore Cover 0, tank HEAT = HE, SPAAG main guns kept except JRVG-1.
# Buildings 30 % = game-config.json BuildingDamageFloor 0.3. See cover_damage_094.py and the Balance notes Doc 1if0iWzQ.
import cover_damage_094;cover_damage_094.apply(t,g,ok,rec,_heli)
# ---------- 23. China truck names (Osama 21 Nov 2026 20:57 PST, thread 1572407822849810463: "Let's make these recommended changes to the names of the cargo
# trucks"): Shaanxi SX2121 4x4 / SX2220 6x6 / SX2306 8x8 by the model each card shows; shown name only. See truck_names_094.py.
import truck_names_094;truck_names_094.apply(t,g,ok,rec)
# ---------- 24. Reservists (Osama 21 Nov 2026 21:2x PST, thread 1572407822849810463, a Chinese player: "这个义务兵我们称之为预备役"; "yeah we should
# update it"): 1166 Conscripts 义务兵 -> Reservists 预备役, 1213 Conscript Recon -> Reservist Recon; shown name only. See reserve_names_094.py.
import reserve_names_094;reserve_names_094.apply(t,g,ok,rec)
# ---------- 25. ZBD-251 air-droppable (Osama 21 Nov 2026 21:3x PST, thread 1572407822849810463: "ZBD-251 next patch should be air droppable"): its own
# mobility row IsAirDroppable True, as the BMD-4M / ZBD-03. See zbd251_airdrop_094.py.
import zbd251_airdrop_094;zbd251_airdrop_094.apply(t,g,ok,rec)
# ---------- 26. NLOS cruise missiles (Osama 21 Nov 2026 23:3x PST, thread 1567745029781454889, testing 0.9.5-dev.1: "The HJ-10 still doesn't fire",
# "the blood wolves NLOS still goes haywire after lazing"): HJ-10, QN-502, CTL-181 and CH-901 rounds LaserGuided False on the cruise path (the
# 13 Nov 0.8.0-dev.25 CTL-181 fix); HJ-10 launcher Type 81 -> 82 cruise launcher, vertical. See nlos_cruise_fix_095.py.
import nlos_cruise_fix_095;nlos_cruise_fix_095.apply(t,g,ok,rec)
# ---------- 27. Blue Dragon Japanese vehicles (Osama 21 Nov 2026 23:4x PST, thread 1573418243715113213: "I just installed a bunch of Japanese units,
# can you please add them to the units in our armory"): Type 89 FV, Type 87 AW, Type 93 Kin-SAM cards in spec 23 (Arsenal only). Their models and the
# Type 10 / Type 90 models + paint schemes are ASSETS (work/blue-dragon-models-20261122). See blue_dragon_jp.py.
import blue_dragon_jp;blue_dragon_jp.apply(t,g,ok,rec)
# ---------- 28. Blue Dragon: the rest of Shawn's folder as units (Osama 22 Nov 2026 00:3x PST, thread 1573418243715113213: "all of these models should
# be made into units"): F-2A, KF-21 Boramae, F-35B (JASDF), F-35B (ROKN), Type 19 in spec 23 (Arsenal only), copies of F-16C / F-16V / F-35B /
# PCL-181 with their loadout options. See blue_dragon_jp2.py.
import blue_dragon_jp2;blue_dragon_jp2.apply(t,g,ok,rec)
# ---------- ZTZ-99B (next patch, batch codex/batch/osama/ztz99b; Osama 22 Nov 2026 01:0x PST, thread 1572407822849810463): ZTZ-99A protection
# slot gets GL-6 APS +70 and LSDW + GL-6 APS +120 (APS row 82 overrides the LSDW defence, LSDW weapon kept); the two APS options show the ZTZ-99B
# model (FAModels models.json variants). See ztz99b_095.py.
import ztz99b_095;ztz99b_095.apply(t,g,ok,rec)
# ---------- ZBD-100 (Osama 22 Nov 2026, thread 1572407822849810463): new China unit, Type 100 model on a Bradley stand-in, ZBD-20 armour and
# drive (ZBD-20 no longer amphibious), 35 mm gun, 80 pts, APS +40, 8x CH-901 loadout. Merged for 0.9.5-dev.19 (Osama 22 Nov 02:50 "please add it"). See zbd100.py.
import zbd100;zbd100.apply(t,g,ok,rec)
# ---------- Turret weapon Order <= weapon count (Osama 22 Nov 2026 03:2x PST, thread 1567745029781454889: "Fix and test all of these issues"):
# the ZTZ-99A / ZTZ-99 Arsenal cards threw in RefundSystem.GetAmmoResupplyTime because the 12.7 mm 'mount 1' had its only weapon at Order 2.
# 30 turrets on 35 China units, Order 2 -> 1. See turret_order_0941.py.
import turret_order_0941;turret_order_0941.apply(t,g,ok,rec)
# ---------- New cards for new models (Osama 22 Nov 2026 11:xx PST, thread 1572407822849810463): ZTZ-59D in the Rocket Force Vehicles tab; Korea:
# K263 Vulcan (M163) and K200 KIFV (M113). See new_cards_1122.py.
import new_cards_1122;new_cards_1122.apply(t,g,ok,rec)
# ---------- Card names (Osama 22 Nov 2026 12:1x PST): ZBD-100 -> Type 100 CSV, ZBD-20 -> VN-17 (HUDName only). See rename_1122.py.
import rename_1122;rename_1122.apply(t,g,ok,rec)
# ---------- AR-2000 on a helicopter stand-in (Osama 22 Nov 2026 13:2x PST, thread 1573561286803980289; QQ sheet FA-041): Kiowa body, AKD-11 on the
# left and right pylons through a default loadout option, stats kept (launch refused and retried every frame on the Termit pylon). See ar2000_heli_095.py.
import ar2000_heli_095;ar2000_heli_095.apply(t,g,ok,rec)
# ---------- HQ-9 rework (Osama 22 Nov 2026 15:2x PST): HQ-9C card -> HQ-9B with a 4x HQ-9B / 8x HQ-9C (+50, PAC-3 MSE round at 1175) slot; HQ-9B card
# -> HQ-9A, semi-active. See hq9_rework_1122.py.
import hq9_rework_1122;hq9_rework_1122.apply(t,g,ok,rec)
# ---------- China infantry casualty order + weapon list order (Lateralus 22 Nov 2026 16:4x PST, thread 1572962048705429598: "queue both"):
# SquadMembers.DeathPriority (highest dies first; one keeper per squad at 1) on 498 rows and SquadWeapons.Order (card/HUD list only) on 452 rows,
# 136 China infantry units. See infantry_order_1122.py and docs/engine/infantry-casualty-and-weapon-order.md.
import infantry_order_1122;infantry_order_1122.apply(t,g,ok,rec)
# ---------- China infantry ammunition (Lateralus 22 Nov 2026 17:1x PST, thread 1572962048705429598): QCW-05 SMG 20 -> 160 per soldier, the MP5SD6
# value (KNT); QBU-191 60 -> 100. See infantry_ammo_1122.py.
import infantry_ammo_1122;infantry_ammo_1122.apply(t,g,ok,rec)
# ---------- Light Riflemen 5 PF-89; DXL-4 rate of fire 8 -> 6, OSV-96 6 -> 8 (Lateralus 22 Nov 2026 17:2x PST, thread 1572962048705429598).
# See infantry_1122b.py.
import infantry_1122b;infantry_1122b.apply(t,g,ok,rec)
# ---------- ZTQ-15 Recon / ZTL-191 Recon optics Good -> Very Good; PLAAF Snipers (1144) laser (Lateralus 22 Nov 2026 17:4x PST,
# thread 1572962048705429598). See recon_sniper_1122.py.
import recon_sniper_1122;recon_sniper_1122.apply(t,g,ok,rec)
# ---------- PRP-5G 35 -> 60 points (Lateralus 22 Nov 2026 17:5x PST, thread 1572962048705429598). See prices_1122.py.
import prices_1122;prices_1122.apply(t,g,ok,rec)
# ---------- HJ-16 ground only (Osama 22 Nov 2026 17:5x PST, thread 1567745029781454889: "They should all be ground only"). See hj16_ground_1122.py.
import hj16_ground_1122;hj16_ground_1122.apply(t,g,ok,rec)
# ---------- Vanilla icons on the HQ-9 cards and the HJ-10 NLOS loadout picture (Osama 22 Nov 2026 17:5x PST). See vanilla_icons_1122.py.
rec['_native_icons']={'ammo':{A[i].get('HUDIcon') for i in native['AmmunitionsJson'] if i in A},'weapons':{W[i].get('HUDIcon') for i in native['WeaponsJson'] if i in W}}
import vanilla_icons_1122;vanilla_icons_1122.apply(t,g,ok,rec)
rec.pop('_native_icons')
# ---------- Helicopter flares 10 -> 15 on Z-10K Recon, Z-10 Recon and Mi-8 Cargo (Lateralus 22 Nov 2026 19:4x PST, thread 1568104480459722894):
# their links move to the matching 15-flare rows; guard: every helicopter with flares has 15. See heli_flares_1122.py.
import heli_flares_1122;heli_flares_1122.apply(t,g,ok,rec)
# ---------- AKF-98A <-> KD-88 names swapped (Osama 23 Nov 2026; QQ FA-002/032). See akf98_kd88_names_1123.py.
import akf98_kd88_names_1123;akf98_kd88_names_1123.apply(t,g,ok,rec)
# ---------- ZBD-251: Type 100 CSV 40 mm CT gun, 75 -> 90 pts (Osama 23 Nov 2026). See zbd251_gun_1123.py.
import zbd251_gun_1123;zbd251_gun_1123.apply(t,g,ok,rec)
# ---------- F-35A and F-35C: 1x MAKO per weapon bay, exactly like the F-22 (Osama 23 Nov 2026 00:1x PST, thread 1567745029781454889). See mako_f35_1123.py.
import mako_f35_1123;mako_f35_1123.apply(t,g,ok,rec)
# ---------- PLARF planes renamed as drones: "J-x Drone 歼-x无人机", J-8D stays manned, J-7 -> J-7IIH (Osama 23 Nov 2026 00:2x-01:0x PST, thread 1567745029781454889). See rocket_drones_1123.py.
import rocket_drones_1123;rocket_drones_1123.apply(t,g,ok,rec)
# ---------- PL-15C removed: all become PL-15, +5 pts per swapped missile, "Heavy CAP (PL-15)", MD-22/FH-97A duplicates removed (Osama 23 Nov 2026 01:5x-02:0x PST,
# thread 1567745029781454889; Doc 1kNAPyBk0vK8DRY8JY3JhS3VXlJvAuWzoZUQKojZlgPA). See pl15c_to_pl15_1123.py.
import pl15c_to_pl15_1123;pl15c_to_pl15_1123.apply(t,g,ok,rec)
# ---------- J-8D health 20 -> 10, the same as J-7IIH, J-6W and J-5 (Osama 23 Nov 2026 12:5x PST, thread 1567745029781454889). See j8_health_1123.py.
import j8_health_1123;j8_health_1123.apply(t,g,ok,rec)
# ---------- MD-22: no stray 2x PL-12 in the gun slot; empty default mount + bay slots 3-4 empty on every loadout (Osama 23 Nov 2026 13:0x PST, thread 1567745029781454889). See md22_slots_1123.py.
import md22_slots_1123;md22_slots_1123.apply(t,g,ok,rec)
# ---------- J-10A card renamed J-10B (Osama 23 Nov 2026 14:2x PST, thread 1567745029781454889). See j10b_name_1123.py.
import j10b_name_1123;j10b_name_1123.apply(t,g,ok,rec)
# ---------- 0.9.6 model rework data, merged into main development (Osama 23 Nov 2026 13:1x: "I need you to give me the dev build with models");
# from branch codex/batch/osama/model-rework-096: France (Testing Preview) spec 24 (france_preview.py), US LRHW Dark Eagle (lrhw_1123.py),
# KF-21 Block 1 and US XQ-58A Valkyrie (c5_cards_1123.py). Their models come from work/model-rework-096/stage (asset args).
# France (Testing Preview) unloaded for now (Osama 23 Nov 14:0x: "please unload all the french models for now and lets keep the model build focused on blue dragons").
# France back (Osama 23 Nov 16:2x): EBRC Jaguar, Mirage 2000D, Leclerc XLR only, FA_FRANCE icon.
import france_preview;france_preview.apply(t,g,ok,rec)
# ---------- Eurocorp (preview): country 5 with France (spec 24, moved from the USA) and Germany (spec 25, no cards yet) (Osama 23 Nov 2026 16:4x PST,
# thread 1567745029781454889). See eurocorp_1123.py; layout runtime-qa/NationLayout.cs.
import eurocorp_1123;eurocorp_1123.apply(t,g,ok,rec)
# ---------- Germany (Preview) cards: Leopard 2A6, Puma, Marder 1A3 (Osama 23 Nov 2026 16:5x PST, thread "blue dragons"). See germany_cards_1123.py.
import germany_cards_1123;germany_cards_1123.apply(t,g,ok,rec)
import lrhw_1123;lrhw_1123.apply(t,g,ok,rec)
import c5_cards_1123;c5_cards_1123.apply(t,g,ok,rec)
# ---------- Thermobaric Assault PF-97 ammo corrected 3 -> 6 (Lateralus 23 Nov 2026 14:4x PST, thread 1568104480459722894): 3 carriers x 2.
# See thermobaric_pf97_1123.py.
import thermobaric_pf97_1123;thermobaric_pf97_1123.apply(t,g,ok,rec)
# ---------- Combat Engineers: Thermobaric Rocket loadout (unit 1162) armour 8 -> 10, 8 -> 7 men, HP 40 -> 35, QBZ-191 5 -> 4; smoke 1 on both loadouts (1156 4 -> 1)
# (Lateralus 23 Nov 2026 14:5x PST, thread 1568104480459722894). See thermobaric_breachers_1123.py.
import thermobaric_breachers_1123;thermobaric_breachers_1123.apply(t,g,ok,rec)
# ---------- Taishan Eagles smoke 4 -> 1 and armour 10 -> 8; Whistling Arrows armour 10 -> 8 (Lateralus 23 Nov 2026 15:1x PST, thread 1568104480459722894).
# See sf_recon_armor_1123.py.
import sf_recon_armor_1123;sf_recon_armor_1123.apply(t,g,ok,rec)
# ---------- ZBD-04 for the PLARF Rocket Conscript Force: ZBD-04A copy with BMP-3 base armour, transport for the 12 PLARF infantry cards
# (Osama 23 Nov 2026 15:1x PST, thread "blue dragons"). See zbd04_rf_1123.py.
import zbd04_rf_1123;zbd04_rf_1123.apply(t,g,ok,rec)
# ---------- PLA ZTZ-98 (Osama 23 Nov 2026 15:0x: Shawn's model, "we'll give it to the rocket force"): ZTZ-99 copy in spec 19. See ztz98_1123.py.
import ztz98_1123;ztz98_1123.apply(t,g,ok,rec)
# ---------- Rangers RRC Standoff +0 -> +5; laser for Taishan Eagles, Whistling Arrows, Sharp Swords, Mountain Leopards (Beijing Swords already has it)
# (Lateralus 23 Nov 2026 15:2x PST, thread 1568104480459722894). Existing rows only. See sf_laser_rangers_1123.py.
import sf_laser_rangers_1123;sf_laser_rangers_1123.apply(t,g,ok,rec)
# ---------- Blue Dragon K9 Thunder (K9 Kõu stats on the non-DLC M109A6 body) and K21 KNIFV (M2A3 copy) cards for Shawn's 23 Nov models
# (Osama 23 Nov 2026 15:3x PST, thread "blue dragons"). See blue_dragon_k9_k21_1123.py.
import blue_dragon_k9_k21_1123;blue_dragon_k9_k21_1123.apply(t,g,ok,rec)
# ---------- Thermobaric Assault (1209): QBS-09 2 -> 3, QBZ-191 7 -> 6, armour 6 -> 8, price 60 -> 70 (Lateralus 23 Nov 2026 15:3x PST,
# thread 1568104480459722894). See thermobaric_assault_1123.py.
import thermobaric_assault_1123;thermobaric_assault_1123.apply(t,g,ok,rec)
# ---------- Disposable launchers one per round: Thermobaric Assault 6 PF-97 = 6 carriers x 1 (Lateralus 23 Nov 2026 22:4x PST, thread
# 1572962048705429598). See disposable_launchers_1123.py; its check runs at the end.
import disposable_launchers_1123;disposable_launchers_1123.apply(t,g,ok,rec)
# ---------- China recon infantry stealth: card 2.5 at minimum, sniper teams (2-3 men with a QBU-10) card 3.0 (Lateralus 23 Nov 2026,
# thread 1568104480459722894). See recon_stealth_1123.py.
import recon_stealth_1123;recon_stealth_1123.apply(t,g,ok,rec)
# ---------- Blue Dragon test infantry: Korean and Japanese rifle squads, copies of US Mech. Riflemen with the rigged seller bodies (Osama 23 Nov 2026
# 17:3x PST, thread 1567745029781454889). See blue_dragon_infantry_1123.py; bodies work/bd-inf-20261123.
import blue_dragon_infantry_1123;blue_dragon_infantry_1123.apply(t,g,ok,rec)
# ---------- YJ-18 removed from the game: out of its spec and hidden in the Armory (Osama 23 Nov 2026 17:4x PST, thread 1567745029781454889).
# See yj18_removed_1123.py.
import yj18_removed_1123;yj18_removed_1123.apply(t,g,ok,rec)
# ---------- Baseline QBZ-191 uses the iron-sight icon (Osama 23 Nov 2026 17:5x PST, bugs thread 1573561286803980289: "we do have a qbz 191
# icone without the optic right? can we use that one for the baseline QBZ-191?"). After the KIAyuyu video review: the QBZ-191 (1.2 damage) and the
# QMK (1.5 damage, the scoped rifle) showed the same optic icon. QBZ-191 2003998 -> FA_PLA_WP_QBZ191_PLAIN (already used by the iron-sight rows
# 2014500/2014501); QMK 2019300 keeps FA_PLA_WP_QBZ191 (optic).
ok(W[2003998]['HUDName']=='QBZ-191' and W[2003998]['HUDIcon']=='FA_PLA_WP_QBZ191' and W[2019300]['HUDName']=='QMK' and W[2019300]['HUDIcon']=='FA_PLA_WP_QBZ191','QBZ-191 and QMK share the optic icon before')
ok(W[2014500]['HUDIcon']==W[2014501]['HUDIcon']=='FA_PLA_WP_QBZ191_PLAIN','iron-sight icon exists in the data')
g.put('WeaponsJson',2003998,{'HUDIcon':'FA_PLA_WP_QBZ191_PLAIN'})
ok(W[2003998]['HUDIcon']=='FA_PLA_WP_QBZ191_PLAIN' and W[2019300]['HUDIcon']=='FA_PLA_WP_QBZ191','baseline QBZ-191 plain icon, QMK optic icon')
rec['qbz191_plain_icon']={'weapon':2003998,'icon':'FA_PLA_WP_QBZ191_PLAIN','qmk_keeps':'FA_PLA_WP_QBZ191'}
# ---------- Type 19 removed (Osama 23 Nov 2026 18:0x PST, thread "blue dragons": "and remove the Type 19"). See type19_removed_1123.py.
import type19_removed_1123;type19_removed_1123.apply(t,g,ok,rec)
# ---------- China roster: VN20, VN-17, VT-5 (+Recon), ZTZ-59 and ZTZ-98 hidden but kept; ZTQ-15 Armored -> Motorized; Z-10K / Z-10U names swapped
# (Osama 23 Nov 2026 18:0x-18:1x PST, thread 1567745029781454889). See roster_1123b.py.
import roster_1123b;roster_1123b.apply(t,g,ok,rec)
# ---------- QBZ-95 -> 'QBZ-95-1', QBZ-03 -> 'QBZ-95' (icon), QJZ-89 Team (Armored) hidden (Osama 23 Nov 2026 18:2x-18:3x PST, thread
# 1567745029781454889). See qbz95_qjz89_1123.py.
import qbz95_qjz89_1123;qbz95_qjz89_1123.apply(t,g,ok,rec)
# ---------- China specialization names and explanations (Osama 23 Nov 2026 18:2x PST, bugs thread 1573561286803980289: "PLAGF Heavy Combined Arms
# Brigade", "PLARF Rocket/Reservist Force (should be Rocket force combined with Reservist Foce)", "PLAN Naval/Special Forces (PLAN AND SOF merged together.
# This does NOT mean PLAN special forces)", "PLAGF Medium Combined Arms Brigade (motorized)"; then "can you update the brigade explanation with these new
# explanations"). Only the English half of UIName and the UIDescription change; the internal Name stays (other scripts check it) and the Chinese half
# stays as it is until the QQ poll on the Chinese names (LangNames.cs shows one half per game language).
# QQ poll 23 Nov 18:3x (8 voters, work/qq-spec-names-20261123/tally.md); Osama 18:4x: 1 B 解放军空军, 2 A 陆军重型合成旅, 4 B 海军与特战部队 (Navy AND
# special operations forces), 5 A 陆军中型合成旅. 18:4x: 3 B 火箭军与预备役部队 (Rocket Force AND reserve forces).
_SP=t['SpecializationsJson']
_specs={17:('PLAAF Air Force 空军','PLAAF Air Force 解放军空军',None),
 18:('PLAGF Armored Force 陆军装甲兵','PLAGF Heavy Combined Arms Brigade 陆军重型合成旅',"A heavy combined arms brigade of the PLA Ground Force: China's heaviest tanks and tracked infantry fighting vehicles, backed by self-propelled artillery and mobile air defense. This firepower comes at the cost of having no fixed-wing aircraft."),
 19:('PLARF Rocket Conscript Force 火箭军','PLARF Rocket/Reservist Force 火箭军与预备役部队',"The PLA Rocket Force and the reservist force combined in one specialization. Reservist infantry and older tanks hold the line while the Rocket Force's ballistic missiles and long-range artillery strike deep into enemy territory. An aging fleet of jets provides the air cover."),
 20:('PLAN Special Forces 海军特种部队','PLAN Naval/Special Forces 海军与特战部队',"The PLA Navy and the special operations forces combined in one specialization (not the Navy's own special forces). Marines and elite special forces, supported by carrier aviation and long-range drones, strike from the sea and the air deep behind enemy lines."),
 21:('PLAGF Motorized 陆军摩托化部队','PLAGF Medium Combined Arms Brigade 陆军中型合成旅',"A medium combined arms brigade of the PLA Ground Force: fast wheeled vehicles carry a large infantry force, supported by mobile rocket artillery and air defense, to hit hard and keep moving.")}
for _i,(_old,_new,_desc) in _specs.items():
    ok(_SP[_i]['UIName']==_old,('spec name before',_i,_SP[_i]['UIName']))
    if _new!=_old or _desc:g.put('SpecializationsJson',_i,{'UIName':_new,**({'UIDescription':_desc} if _desc else {})})
    ok(_SP[_i]['UIName']==_new and (not _desc or _SP[_i]['UIDescription']==_desc),('spec name after',_i))
rec['china_spec_names']={i:_SP[i]['UIName'] for i in _specs}
# ---------- Chinese descriptions for the 5 China specs + 海军参谋部远域特种作战大队 (Osama 24 Nov 2026 11:0x PST, thread 1567745029781454889,
# community file work/loc-096-1124/0.9.6.txt). See china_spec_zh_1124.py.
import china_spec_zh_1124;china_spec_zh_1124.apply(t,g,ok,rec)
# ---------- Marine HJ-8H Team -> Marine HJ-12 Team (HJ-12 x4, 105 pts); Motorized GAM-102LR Team -> HJ-8H Team (HJ-8H x6, 65 pts) (Osama 23 Nov
# 2026 18:2x PST, thread 1567745029781454889). See hj_teams_1123.py.
import hj_teams_1123;hj_teams_1123.apply(t,g,ok,rec)
# ---------- US recon helicopters (Lateralus 23 Nov 2026 18:3x PST, thread 1572962048705429598). See recon_helis_us_1123.py.
import recon_helis_us_1123;recon_helis_us_1123.apply(t,g,ok,rec)
# ---------- Russian recon helicopters (Lateralus 23 Nov 2026 18:5x PST, thread 1572962048705429598). See recon_helis_ru_1123.py.
import recon_helis_ru_1123;recon_helis_ru_1123.apply(t,g,ok,rec)
# ---------- China recon helicopters (Lateralus 23 Nov 2026 19:0x PST, thread 1572962048705429598). See recon_helis_cn_1123.py.
import recon_helis_cn_1123;recon_helis_cn_1123.apply(t,g,ok,rec)
# Lateralus 23 Nov 19:5x: 'Mech. Riflemen MMG should get sprint back, everything else is fine'
import mech_mmg_sprint_1123;mech_mmg_sprint_1123.apply(t,g,ok,rec)
# ---------- HQ-17 hidden, not the HQ-17A (Osama 24 Nov 2026 01:1x PST, thread 1567745029781454889). Before the test spec. See hq17_removed_1124.py.
import hq17_removed_1124;hq17_removed_1124.apply(t,g,ok,rec)
# ---------- ZTL-191 Recon hidden, not the ZTL-191 (Osama 24 Nov 2026 02:1x PST, thread 1567745029781454889). Before the test spec. See ztl191_recon_removed_1124.py.
import ztl191_recon_removed_1124;ztl191_recon_removed_1124.apply(t,g,ok,rec)
# ---------- Base ZTZ-96 removed (its model can't ship; the ZTZ-96A stays) (Osama 24 Nov 2026 03:0x PST, thread 1567745029781454889). Before the
# test spec. See ztz96_removed_1124.py.
import ztz96_removed_1124;ztz96_removed_1124.apply(t,g,ok,rec)
# ---------- ZBD-04 out of the Rocket Force: its 12 PLARF transport links go, unit hidden (Osama 24 Nov 2026 03:1x PST, thread 1567745029781454889).
# Before the test spec. See zbd04_rf_removed_1124.py.
import zbd04_rf_removed_1124;zbd04_rf_removed_1124.apply(t,g,ok,rec)
# ---------- China hidden-units test spec 26, off unless UserData/FreedomArrow/test-spec.json switches it on (Osama 23 Nov 2026 18:5x PST,
# thread 1567745029781454889). See test_specs_1123.py and runtime-qa/TestSpec.cs.
import test_specs_1123;test_specs_1123.apply(t,g,ok,rec)
# ---------- ZTQ-15 Light air-droppable (Osama 23 Nov 2026 19:5x PST, thread 1567745029781454889). See ztq15_light_airdrop_1123.py.
import ztq15_light_airdrop_1123;ztq15_light_airdrop_1123.apply(t,g,ok,rec)
# ---------- FH-97A (and the model build's XQ-58A) as UCAVs: 10 HP, no afterburner (Osama 23 Nov 2026 20:3x PST, thread 1567745029781454889).
# See ucav_fh97_xq58_1123.py.
import ucav_fh97_xq58_1123;ucav_fh97_xq58_1123.apply(t,g,ok,rec)
# ---------- X-47B to the Marines (Osama 23 Nov 2026 20:4x PST, thread 1567745029781454889). See x47b_marines_1123.py.
import x47b_marines_1123;x47b_marines_1123.apply(t,g,ok,rec)
# ---------- UCAVs get flares (Osama 23 Nov 2026 20:4x PST, thread 1567745029781454889). See ucav_flares_1123.py.
import ucav_flares_1123;ucav_flares_1123.apply(t,g,ok,rec)
# ---------- X-47B: Air tab, plane optics, ECM 45% + flares (Osama 23 Nov 2026 22:0x PST, thread 1567745029781454889). See x47b_air_tab_1123.py.
import x47b_air_tab_1123;x47b_air_tab_1123.apply(t,g,ok,rec)
# ---------- X-47B bay prices: AIM-120 +15, AIM-260 +40 per bay (Osama 23 Nov 2026 22:1x PST, thread 1567745029781454889). See x47b_bay_prices_1123.py.
import x47b_bay_prices_1123;x47b_bay_prices_1123.apply(t,g,ok,rec)
# ---------- VN-3 (airborne, Kord clone) and ZSL-191 (motorized, ZSL-92 family clone) transports for the MarkII_ China models (Osama 23 Nov 2026
# 20:4x PST, thread "blue dragons"). MODEL BUILD ONLY. See mk_china_1123.py.
import mk_china_1123;mk_china_1123.apply(t,g,ok,rec)
# ---------- QBZ rounds read '5.8 mm ammunition' (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889). See qbz_58_ammo_1123.py.
import qbz_58_ammo_1123;qbz_58_ammo_1123.apply(t,g,ok,rec)
# ---------- Weapons Squad 火力班: one QJZ-171, 45 -> 60 pts (Osama 23 Nov 2026 21:3x PST, thread 1567745029781454889). See weapons_squad_1123.py.
import weapons_squad_1123;weapons_squad_1123.apply(t,g,ok,rec)
# ---------- Rafale C (France preview) + Eurofighter Typhoon (Germany preview) set-piece jets (Osama 23 Nov 2026 20:1x PST, thread "China cosmetic
# work"). Last, so their new unit ids follow every existing card. See euro_jets_1123.py.
import euro_jets_1123;euro_jets_1123.apply(t,g,ok,rec)
# ---------- PLA ZBL-08 Recon (ZZC-07), MarkII_ model (Osama 23 Nov 2026 21:3x PST, thread "China cosmetic work"). See zbl08_recon_1123.py.
import zbl08_recon_1123;zbl08_recon_1123.apply(t,g,ok,rec)
# ---------- PLA PLZ-25 (MarkII_ model) in the navy spec (Osama 23 Nov 2026 21:5x PST, thread "China cosmetic work"). See plz25_navy_1123.py.
import plz25_navy_1123;plz25_navy_1123.apply(t,g,ok,rec)
# ---------- VN-3: 30 pts with the 2A72, +10 HJ-73D option; Kord and Spitsa options removed (Osama 23 Nov 2026 21:4x PST, thread
# 1567745029781454889). MODEL BUILD ONLY (the VN-3 is from mk_china_1123.py). See vn3_loadout_1123.py.
import vn3_loadout_1123;vn3_loadout_1123.apply(t,g,ok,rec)
# ---------- ZSL-191: 30 pts, ZBL-191 armour (12 HP), MG only (Osama 23 Nov 2026 21:5x PST, thread 1567745029781454889). MODEL BUILD ONLY.
# See zsl191_stats_1123.py.
import zsl191_stats_1123;zsl191_stats_1123.apply(t,g,ok,rec)
# ---------- PLZ-10 (Armored Force): PLA PLZ-25 (Vena clone) copy, after plz25_navy_1123 (Osama 23 Nov 2026 22:1x PST, thread "blue dragons").
# MODEL BUILD ONLY. See mk_mortars_1123.py.
import mk_mortars_1123;mk_mortars_1123.apply(t,g,ok,rec)
# ---------- PLA ZRZ-100 UGV in PLAN Special Forces: Uran-9 copy with QJC-88 12.7 mm, 2x HJ-16, 2x ABZ-13 (Osama 23 Nov 2026 22:2x PST, thread
# "blue dragons"). MODEL BUILD ONLY. See zrz100_1123.py.
import zrz100_1123;zrz100_1123.apply(t,g,ok,rec)
# ---------- ZTD-05 = amphibious M10 Booker copy in PLAN Naval/SF (Osama 23 Nov 2026 22:2x PST, thread 1567745029781454889). MODEL BUILD ONLY.
# Last, so its new unit id follows every existing card. See ztd05_booker_1123.py.
import ztd05_booker_1123;ztd05_booker_1123.apply(t,g,ok,rec)
# ---------- ZSD-05 = amphibious 8-seat AMPV transport for PLAN infantry (Osama 23 Nov 2026 22:3x PST, thread 1567745029781454889). MODEL BUILD ONLY.
# Last, so its new unit id follows every existing card. See zsd05_ampv_1123.py.
import zsd05_ampv_1123;zsd05_ampv_1123.apply(t,g,ok,rec)
# ---------- ZBD-05 = ZSD-05 with the autocannon, +10 HJ-73D (Osama 23 Nov 2026 22:3x PST, thread 1567745029781454889). MODEL BUILD ONLY.
# See zbd05_ifv_1123.py.
import zbd05_ifv_1123;zbd05_ifv_1123.apply(t,g,ok,rec)
# ---------- Chinese weapon / round / loadout names on ZTD-05, ZSD-05, ZBD-05, VN-3 (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889).
# MODEL BUILD ONLY. See sinicize_1123.py.
import sinicize_1123;sinicize_1123.apply(t,g,ok,rec)
# ---------- No HJ-12 / APS / reactive armour loadouts on ZSD-05, ZBD-05, ZTD-05 (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889).
# MODEL BUILD ONLY. See plan_trim_options_1123.py.
import plan_trim_options_1123;plan_trim_options_1123.apply(t,g,ok,rec)
# ---------- ZRZ-100: turret via a default loadout option (it had no weapons), QJY-201 + 2x ABZ-13 + 2x HJ-16, 45 pts, 90 road / 20 reverse
# (Osama 24 Nov 2026 00:5x PST, thread 1567745029781454889). MODEL BUILD ONLY. See zrz100_fix_1123.py.
import zrz100_fix_1123;zrz100_fix_1123.apply(t,g,ok,rec)
# ---------- Infantry launcher batch: SRAW MPV, hybrid ignore cover, Bur, Thermobaric Assault, engineer loadouts, Shturmoviki (Lateralus 24 Nov 2026
# 11:3x PST, thread 1572962048705429598). See infantry_launchers_1124.py.
import infantry_launchers_1124;infantry_launchers_1124.apply(t,g,ok,rec)
# ---------- Type 100 CSV loadouts: one four-way swap slot (APS kept with CH-901) and own rows for the transport copies (Osama 24 Nov 2026 00:1x PST,
# bugs thread 1573561286803980289, "make the fix"; MODEL BUILD: needs the 6 new models.json names from work/model-rework-096/stage.py). See type100_fix_1124.py.
import type100_fix_1124;type100_fix_1124.apply(t,g,ok,rec)
# ---------- Type 100 CSV transport only: the recon card goes (Osama 24 Nov 2026 01:0x PST, thread 1567745029781454889). See type100_transport_only_1124.py.
import type100_transport_only_1124;type100_transport_only_1124.apply(t,g,ok,rec)
# ---------- Type 100 CSV 40 mm CT: 2A91 57 mm sound, effects and rate of fire, own damage/pen/range (Osama 24 Nov 2026 01:3x PST, bugs thread
# 1573561286803980289). See type100_2a91_1124.py.
import type100_2a91_1124;type100_2a91_1124.apply(t,g,ok,rec)
# ---------- Type 100 CH-901 loadout rows in the base tab + CH-901 +60 / CH-901+APS +100 (Osama 24 Nov 2026 23:4x PST, bugs thread
# 1573561286803980289). See type100_cat_price_1124.py.
import type100_cat_price_1124;type100_cat_price_1124.apply(t,g,ok,rec)
# ---------- PLAAF infantry air-droppable (SmallWD report, Osama 24 Nov 2026 01:3x PST, bugs thread 1573561286803980289). See plaaf_para_1124.py.
import plaaf_para_1124;plaaf_para_1124.apply(t,g,ok,rec)
# ---------- Chinese bug sheet FA-081/082/084/085 answers (Osama 23 Nov 2026 23:2x PST, bugs thread 1573561286803980289). See qq_sheet_fixes_1123.py.
import qq_sheet_fixes_1123;qq_sheet_fixes_1123.apply(t,g,ok,rec)
# ---------- Falcons: QJZ-171 -> QJY-201, QBU-10 -> QBU-201 (M40A5 stat clone, own icon) (Osama 24 Nov 2026 02:2x PST, thread 1567745029781454889).
# See falcons_weapons_1124.py.
import falcons_weapons_1124;falcons_weapons_1124.apply(t,g,ok,rec)
# ---------- Marine Recon = Force Recon pattern: QTS-11 out, 2 x QBZ-192 + QLG-10A, 2 x QBU-191, death priorities as Force Recon (Osama 24 Nov 2026
# 02:3x PST, thread 1567745029781454889). See marine_recon_1124.py.
import marine_recon_1124;marine_recon_1124.apply(t,g,ok,rec)
# ---------- After 0.9.6: PGL-625 gun damage 4.9 -> 3.5 (QQ FA-101) and the LSDW laser pulse ignores armour (QQ FA-098) (Osama 24 Nov 2026 10:5x PST,
# thread 1567745029781454889). See pgl625_lsdw_1124.py.
import pgl625_lsdw_1124;pgl625_lsdw_1124.apply(t,g,ok,rec)
# ---------- J-5 Drone and J-6W Drone +20 pts (Osama 24 Nov 2026 11:3x PST, thread 1567745029781454889). See j5_j6_price_1124.py.
import j5_j6_price_1124;j5_j6_price_1124.apply(t,g,ok,rec)
# ---------- DF-31A nuclear warhead resupply time 600 -> 6000 (Osama 24 Nov 2026 11:4x PST, thread 1567745029781454889). See df31a_resupply_1124.py.
import df31a_resupply_1124;df31a_resupply_1124.apply(t,g,ok,rec)
# ---------- PF-98 Team (PLARF): HE ignore cover 25% -> 0, AT round range 800 -> 600 m (Osama 24 Nov 2026 11:4x PST, thread
# 1567745029781454889). See pf98_team_1124.py.
import pf98_team_1124;pf98_team_1124.apply(t,g,ok,rec)
# ---------- J-11BHG gets the J-16's Heavy CAP loadout, 175 pts (Osama 24 Nov 2026 11:5x PST, thread 1567745029781454889). See j11bhg_heavy_cap_1124.py.
import j11bhg_heavy_cap_1124;j11bhg_heavy_cap_1124.apply(t,g,ok,rec)
# ---------- Blue Dragon + Euro preview weapons and rounds marked '[TEST] ' (Osama 23 Nov 2026 23:5x PST, thread "China cosmetic work"). LAST.
# See test_weapon_names_1123.py.
import test_weapon_names_1123;test_weapon_names_1123.apply(t,g,ok,rec)
# ---------- (Unit cards English only + guard, 8add5fcd, withdrawn 24 Nov 01:0x: Osama "English and Chinese are fine" about the 42 bilingual
# China infantry cards. They keep "English 中文" as since 0.9.4. The J-5 / J-6W drone cards stay English only, rocket_drones_1123.py.)
# ---------- PLA ZZC-06 (ZBD-04A Recon copy without the 100 mm gun, 45 pts) replaces the ZBD-04A Recon in the Heavy Combined Arms Brigade
# (Osama 24 Nov 2026 01:1x-01:23 PST, threads "China cosmetic work" + "blue dragons"). See zzc06_recon_1124.py.
import zzc06_recon_1124;zzc06_recon_1124.apply(t,g,ok,rec)
# ---------- China vehicle card pictures from Osama's Armory shots (24 Nov 2026 00:5x PST, thread "China cosmetic work"). After the ZZC-06 card
# (its picture, Osama 24 Nov 03:1x). See card_portraits_1124.py.
import card_portraits_1124;card_portraits_1124.apply(t,g,ok,rec)
# ---------- ZTZ-96B front armour = ZTZ-96A, 220 -> 195 pts (Osama 24 Nov 2026 01:25 PST, thread "blue dragons", "96B not 99B"). See ztz96b_1124.py.
import ztz96b_1124;ztz96b_1124.apply(t,g,ok,rec)
# ---------- VN-3 air-droppable (Osama 24 Nov 2026 01:2x PST, thread "China cosmetic work"). See vn3_airdrop_1124.py.
import vn3_airdrop_1124;vn3_airdrop_1124.apply(t,g,ok,rec)
# ---------- China vehicle unit icons (card silhouettes) rendered from their own models (Osama 24 Nov 2026 01:1x PST, thread "China cosmetic
# work": "where are the unit icons"). See card_icons_1124.py.
import card_icons_1124;card_icons_1124.apply(t,g,ok,rec)
# ---------- ZTZ-59D1 removed (Osama 24 Nov 2026 01:1x PST, thread "blue dragons"). Last, after the test-spec section. See ztz59d1_removed_1124.py.
import ztz59d1_removed_1124;ztz59d1_removed_1124.apply(t,g,ok,rec)
# ---------- QBU-10 weapon icon from Osama's photo (24 Nov 2026 02:0x PST, thread "blue dragons"). See qbu10_icon_1124.py.
import qbu10_icon_1124;qbu10_icon_1124.apply(t,g,ok,rec)
# ---------- QCW-05 -> QCQ-171, cosmetic only: name, icon, 9x19 mm round name (Osama 24 Nov 2026 02:1x PST, thread "blue dragons"). See qcq171_1124.py.
import qcq171_1124;qcq171_1124.apply(t,g,ok,rec)
# ---------- France / Germany preview specs: battlegroup size 0 (Osama 24 Nov 2026 02:0x PST, thread "China cosmetic work"). See euro_bg_zero_1124.py.
import euro_bg_zero_1124;euro_bg_zero_1124.apply(t,g,ok,rec)
# ---------- QJB-201 weapon icon from Osama's photo (24 Nov 2026 02:3x PST, thread "China cosmetic work"). See qjb201_icon_1124.py.
import qjb201_icon_1124;qjb201_icon_1124.apply(t,g,ok,rec)
# ---------- Thunder Gods kit: 3 QCQ-171, 1 QJS-161 (Osama 24 Nov 2026 02:4x PST, thread "China cosmetic work"). See thunder_gods_1124.py.
import thunder_gods_1124;thunder_gods_1124.apply(t,g,ok,rec)
# ---------- Euro set 2 (Osama 24 Nov 2026 11:1x PST, thread "blue dragons"): 7 Germany + 2 France preview cards, US MaxxPro MRAP transport. Last. See euro_set_1124.py.
import euro_set_1124;euro_set_1124.apply(t,g,ok,rec)
# ---------- Lynx airborne family stat cards: 9 cards + 2 transports in the airborne spec 17 (Osama 24 Nov 2026 16:0x PST, thread "blue dragons"). See lynx_cards_1124.py.
import lynx_cards_1124;lynx_cards_1124.apply(t,g,ok,rec)
# ---------- Delta Force: base 95, Close Quarters default +0, Standoff +5 = 100 (Lateralus 24 Nov 2026 14:5x PST, thread 1572962048705429598).
# See delta_force_1124.py.
import delta_force_1124;delta_force_1124.apply(t,g,ok,rec)
# ---------- Air-launched HJ-10 shown as AKD-10 on helicopters + Wing Loong (Osama 24 Nov 2026 16:0x PST, thread "China cosmetic work").
# Names only. See akd10_names_1124.py.
import akd10_names_1124;akd10_names_1124.apply(t,g,ok,rec)
# Assaultmen SRAW A creates new unit/weapon/round/option rows: keep it LAST so no row created above changes its id (saved decks keep units by id).
# ---------- Assaultmen SRAW A (new anti-tank SRAW, 140mm HEAT top attack) / B (SRAW MPV) card; Assaultmen SMAW loses its loadout slot
# (Lateralus 24 Nov 2026 12:5x/13:2x, thread 1572962048705429598). See sraw_split_1124.py.
# ---------- NLOS missiles act like vanilla cruise missiles (Osama 24 Nov 2026 17:2x PST, bugs thread 1573561286803980289). See nlos_cruise_1124.py.
import nlos_cruise_1124;nlos_cruise_1124.apply(t,g,ok,rec)
import sraw_split_1124;sraw_split_1124.apply(t,g,ok,rec)
# ---------- Lynx placeholder cards for the four received models with no card (Osama 24 Nov 2026 17:5x, bugs thread 1573561286803980289: "please make
# sure all models have a unit entry so I can at least see"). After the SRAW split so no earlier unit id moves. See lynx_cards_1124.py CARDS_EXTRA.
lynx_cards_1124.apply_extra(t,g,ok,rec)
# ---------- SHORAD radar split (Lateralus 24 Nov 2026 15:5x-16:4x PST, thread 1568104480459722894): SA SHORAD rows 58/60/62 Low range + optics
# 1.25 -> 1.5; gun/IR units on new IR SHORAD rows (range 1.25, optics 1.5); IR rounds of SA units get compensated copies; option B burn times;
# helicopters stay x1.25; radar icon labels. Adds ability/ammo rows: after the SRAW A unit so its ids stay. See lateralus/shorad_radar_1124.py.
# FB-10 = AMRAAM stat clone (Lateralus 24 Nov 2026 18:4x PST); runs BEFORE the SHORAD split so the PGL-625 / Lynx 66 SPAAG count as radar-guided (SA)
# and the FB-10 takes the AMRAAM burn there (Lateralus 18:5x 'queue it': China radar proposal).
import fb10_amraam_1124;print('FB-10',fb10_amraam_1124.apply(t,g,ok,rec,_heli)['changed'])
import shorad_radar_1124;_sr=shorad_radar_1124.apply(t,g,ok,rec,_HR,_heli)
_heli['radar']=_HR.contract(t)['radar'];_heli['ammo'].update({str(k):v for k,v in _sr['heli_ammo'].items()})
ok(sum(1 for r in _heli['radar'] if r.get('label'))>=3,'radar groups with an icon label')
# ---------- Per-weapon radar use (Lateralus 24 Nov 2026 22:2x 'Build it'): IR rounds (except AIM-9) and the Fletcher get no radar range bonus; the card
# shows a radar trait icon on weapons that use it. Lists in helicopter-range.json. See lateralus/radar_weapons_1124.py.
import radar_weapons_1124;print('RADAR WEAPONS',radar_weapons_1124.apply(t,ok,rec,_heli)['exempt'])
print('SHORAD RADAR',{k:_sr[k] for k in ('ir_rows','china_rows','ir_round_copies','heli_ammo')},[(r['abilities'],r.get('label'),r['lowAltRange'],r['lowAltOptics'],r['helicopterRangeMultiplier'],r['helicopterOpticsMultiplier']) for r in _heli['radar']])
# ---------- FK-3000 card (FK-2000 copy) + PCL-181 in the Medium CAB (Osama 24 Nov 2026 17:2x/18:0x PST, thread "China cosmetic work").
# Creates rows: after every other row-creating section. See fk3000_pcl181_1124.py.
import fk3000_pcl181_1124;fk3000_pcl181_1124.apply(t,g,ok,rec)
# ---------- Combat Engineers unit icon (Osama 24 Nov 2026 19:1x PST, #Website: "turn it into a unit icon and then add it"). See engineer_icon_1124.py.
import engineer_icon_1124;engineer_icon_1124.apply(t,g,ok,rec)
# ---------- Lynx family rework (Osama 24 Nov 2026 19:15 PST, thread 1567745029781454889): renames, 4 cards hidden, ammo cuts, Lynx Laser weapon,
# SPAAG without radar (QW-2), Rapid-Fire Gun HJ-8H, Recon optics, Troop Carrier 9 seats. Creates rows: after every other row-creating section, so no
# earlier id moves. See lynx_rework_1124.py.
import lynx_rework_1124;lynx_rework_1124.apply(t,g,ok,rec)
# ---------- Blue Dragon / Eurocorp previews (Osama 24 Nov 2026 21:2x PST: "see the spec and look around ... don't want people to click on it and see the
# stats. Hide the K-1's too"): K1 / K1A1 to the US test spec; stat cards hidden by PreviewCards.cs. Changes rows only. See preview_specs_1124.py.
import preview_specs_1124;preview_specs_1124.apply(t,g,ok,rec)
# ---------- Air-launched fast missiles 600 + MiG-31K / B-52 ARRW / F-35 MAKO prices (Osama 24 Nov 2026 21:1x PST). Changes rows only.
# See air_hypersonic_600_1124.py.
import air_hypersonic_600_1124;air_hypersonic_600_1124.apply(t,g,ok,rec)
# ---------- ZBD-03 x2 hidden for now, ZSD-89A out of Airborne (Osama 24 Nov 2026 23:2x PST, thread "China cosmetic work"). Removes rows only.
# See zbd03_zsd89a_hidden_1124.py.
import zbd03_zsd89a_hidden_1124;zbd03_zsd89a_hidden_1124.apply(t,g,ok,rec)
# ---------- Lynx SPAAG gun 7 damage/s (Osama 24 Nov 2026 23:4x PST, thread "China cosmetic work"). Changes one row. See lynx_spaag_dps_1124.py.
import lynx_spaag_dps_1124;lynx_spaag_dps_1124.apply(t,g,ok,rec)
# ---------- QTS-11 grenade launcher under-barrel (Osama 25 Nov 2026 00:0x PST, thread "blue dragons": a second QTS-11 on every soldier's back).
# Changes IsUnderbarrel only. See qts11_underbarrel_1124.py.
import qts11_underbarrel_1124;qts11_underbarrel_1124.apply(t,g,ok,rec)
# ---------- Lynx unit icons; Lynx Laser weapon "50 kW laser" (Osama 25 Nov 2026 00:1x PST, thread "China cosmetic work"). Creates one weapon row.
# See lynx_icons_1125.py.
import lynx_icons_1125;lynx_icons_1125.apply(t,g,ok,rec)
# ---------- Lynx IFV (Type 100 40 mm CT, 65 pts, no supplies), new Lynx ATV (Troop Carrier with 7 seats), Lynx icons (Osama 25 Nov 2026 00:1x-00:2x
# PST, thread "China cosmetic work"). Creates rows. See lynx_ifv_atv_1125.py.
import lynx_ifv_atv_1125;lynx_ifv_atv_1125.apply(t,g,ok,rec)
# ---------- PF-98 tripod crewed like the SPG-9 (Osama 25 Nov 2026 00:3x PST, thread "blue dragons"). Changes ModelFileName on 2016259 only.
# See pf98_tripod_spg9_1125.py.
import pf98_tripod_spg9_1125;pf98_tripod_spg9_1125.apply(t,g,ok,rec)
# ---------- HQ-7B and PLL-05 to the Medium CAB, CSK-131 9 seats (Osama 25 Nov 2026 00:3x PST, thread "China cosmetic work"). Changes rows only.
# See medcab_moves_1125.py.
import medcab_moves_1125;medcab_moves_1125.apply(t,g,ok,rec)
# ---------- QN-202: Javelin model, 7 damage, 70 mm penetration, 18 rounds (Osama 25 Nov 2026 00:4x PST, thread "blue dragons").
# See qn202_javelin_1125.py.
import qn202_javelin_1125;qn202_javelin_1125.apply(t,g,ok,rec)
# ---------- ZTD-05: the ZTL-11's 105 mm gun-launched missile, 8 rounds (Osama 25 Nov 2026 00:5x PST, thread 1567745029781454889).
# See ztd05_glatgm_1125.py.
import ztd05_glatgm_1125;ztd05_glatgm_1125.apply(t,g,ok,rec)
# ---------- ZBD-05 and VN-3 loadout options showed vanilla icons (Osama 25 Nov 2026 01:1x PST). See option_icon_overrides_1125.py.
import option_icon_overrides_1125;option_icon_overrides_1125.apply(t,g,ok,rec)
# ---------- Lynx Troop Carrier: Unarmed default + HMG / AGL options +5 (Osama 25 Nov 01:5x), Lynx ATV retired (01:1x). See lynx_tc_unarmed_1125.py.
import lynx_tc_unarmed_1125;lynx_tc_unarmed_1125.apply(t,g,ok,rec)
# ---------- Lynx NLOS, CSK-131 out of Airborne, Lynx Laser APS symbol (Osama 25 Nov 2026 01:4x-01:5x PST). See lynx_nlos_csk_1125.py.
import lynx_nlos_csk_1125;lynx_nlos_csk_1125.apply(t,g,ok,rec)
# ---------- Audit fixes after dev.11: Lynx NLOS on the CTL-181's Tigr body and mount (it was hidden), Lynx Cargo 2500 (Osama 25 Nov 2026). See lynx_nlos_body_1125.py.
import lynx_nlos_body_1125;lynx_nlos_body_1125.apply(t,g,ok,rec)
# ---------- Lynx Cargo icon from its own model, crewman removed (Osama 25 Nov 2026 10:0x: "lynx cargo make icon (try to remove the person)").
# See lynx_cargo_icon_1125.py.
import lynx_cargo_icon_1125;lynx_cargo_icon_1125.apply(t,g,ok,rec)
# ---------- ZSD-89A out of PLAN Naval/Special Forces (Osama 25 Nov 2026 01:5x PST). See zsd89a_plan_removed_1125.py.
import zsd89a_plan_removed_1125;zsd89a_plan_removed_1125.apply(t,g,ok,rec)
# ---------- VN-3 30 -> 35 pts (Osama 25 Nov 2026 01:5x PST). See vn3_cost_1125.py.
import vn3_cost_1125;vn3_cost_1125.apply(t,g,ok,rec)
# ---------- Falcons: 4 QMK, the QJY-201 gunner's own gun (Osama 25 Nov 2026 02:3x PST). See falcons_qjy_1125.py.
import falcons_qjy_1125;falcons_qjy_1125.apply(t,g,ok,rec)
# ---------- Lynx Howitzer 80 pts / 3600 m / Hawkeye dispersion / 40 kg; Lynx 120 mm Mortar 8 smoke, 65 pts (Osama 25 Nov 2026 03:1x PST).
# See lynx_arty_1125.py. Creates rows: before the test-spec check, which stays last among the spec sections.
import lynx_arty_1125;lynx_arty_1125.apply(t,g,ok,rec)
# ---------- Lynx 81 mm Mortar: Hawkeye MWS range and dispersion, 60 pts (Osama 25 Nov 2026 03:2x PST). See lynx_m81_1125.py.
import lynx_m81_1125;lynx_m81_1125.apply(t,g,ok,rec)
# ---------- Lynx MRL: one 12-rocket salvo, 24 rockets, 2800 m, HE base + smoke-only loadout +20 (Osama 25 Nov 2026 03:2x PST). See lynx_mrl_1125.py.
import lynx_mrl_1125;lynx_mrl_1125.apply(t,g,ok,rec)
# ---------- ZBD-251 for every Airborne team (Osama 25 Nov 2026 10:0x PST). See zbd251_airborne_1125.py.
import zbd251_airborne_1125;zbd251_airborne_1125.apply(t,g,ok,rec)
# ---------- FK-3000 into the hidden China test spec 26 (Osama 25 Nov 2026 11:4x PST). See fk3000_hidden_1125.py.
# Restored 25 Nov 14:1x (Osama "Make sure glass is tinted and we can add to the release candidate"): Shawn's fixed model (work/fk3000-shawn-1125)
# replaces the tipped-cab one, so the card is back in Medium CAB and in the Armory.
#import fk3000_hidden_1125;fk3000_hidden_1125.apply(t,g,ok,rec)
# ---------- KF51, KF41, Gepard, MAN HX77, VAB preview cards hidden, models held back (Osama 25 Nov 2026 11:4x PST). See euro_held_1125.py.
import euro_held_1125;euro_held_1125.apply(t,g,ok,rec)
# ---------- No shown card in the hidden test specs: PCL-181 out of spec 26 (Osama 25 Nov 2026 03:0x PST). See test_spec_visible_1125.py.
import test_spec_visible_1125;test_spec_visible_1125.apply(t,g,ok,rec)
# ---------- ZBD-05 family swims at 50 (Osama 25 Nov 2026 01:2x PST, thread "China cosmetic work"). May add mobility rows. See zbd05_swim_1125.py.
import zbd05_swim_1125;zbd05_swim_1125.apply(t,g,ok,rec)
# ---------- QQ sheet fixes: QBU-203 name, ZBD-86 Recon card out, CSK-181 transport = CTL-181 with a QJZ-89 RWS (Osama 25 Nov 2026 03:4x PST,
# bugs thread 1573561286803980289). See qq_fixes_1125.py.
import qq_fixes_1125;qq_fixes_1125.apply(t,g,ok,rec)
# ---------- HJ-10 NLOS range = HJ-10 FNF (1600 m) (Osama 25 Nov 2026 10:1x PST, bugs thread). See hj10_nlos_range_1125.py.
import hj10_nlos_range_1125;hj10_nlos_range_1125.apply(t,g,ok,rec)
# ---------- Every APS 2 charges (Osama 25 Nov 2026 12:1x PST, bugs thread; replaces the FEP-only fep_aps_1125.py). See aps_two_charges_1125.py.
import aps_two_charges_1125;aps_two_charges_1125.apply(t,g,ok,rec)
# ---------- ZTZ-99 LSDW +60; LSDW pulse stress 80 -> 70 (Osama 25 Nov 2026 12:2x PST, bugs thread). See ztz99_lsdw_1125.py.
import ztz99_lsdw_1125;ztz99_lsdw_1125.apply(t,g,ok,rec)
# ---------- Thunder Gods second QJS-161 (Osama 25 Nov 2026 18:2x PST, bugs thread). See thunder_gods_qjs2_1125.py.
import thunder_gods_qjs2_1125;thunder_gods_qjs2_1125.apply(t,g,ok,rec)
# ---------- PAP Snow Leopards: one QCQ-171 -> QBS-09 (Osama 25 Nov 2026 18:3x PST, bugs thread). See snow_leopards_qbs_1125.py.
import snow_leopards_qbs_1125;snow_leopards_qbs_1125.apply(t,g,ok,rec)
# ---------- ZTQ-15, ZTQ-15 Recon, ZTQ-15 Light 25 points cheaper (Osama 25 Nov 2026 11:3x PST). See ztq15_cost_1125.py.
import ztq15_cost_1125;ztq15_cost_1125.apply(t,g,ok,rec)
# ---------- Z-20S 0 -> 4 seats, MH-60M SOAR Recon 60 -> 65 pts (Lateralus 25 Nov 2026 18:0x PST). See recon_helo_1125.py.
import recon_helo_1125;recon_helo_1125.apply(t,g,ok,rec)
# ---------- Plane guns: ActualArrow 1.2.2 values on the US/RU rows, China and preview copies by class; existing rows only (Lateralus 25 Nov 2026
# 08:5x, thread 1572962048705429598: "1. Copy 2. Copy 3. Copy 4. Copy 5. A, queue it"). See plane_guns_aa_1125.py.
import plane_guns_aa_1125;plane_guns_aa_1125.apply(t,g,ok,rec)
# ---------- US Combat Engineers: M-25 CDTE 2 -> 1, 75 -> 70 pts (Lateralus 25 Nov 2026 11:5x). See us_combat_engineers_1125.py.
import us_combat_engineers_1125;us_combat_engineers_1125.apply(t,g,ok,rec)
# ---------- Radar only on loadouts with a radar weapon; HHQ-10 and SeaRAM on SA radar (Lateralus 25 Nov 2026 09:17 PST, thread 1568104480459722894:
# "1. Yes that is what I want 2. (a) 3. HHQ-10 ... and the RIM-116 (SeaRAM) ... should benefit from radar and have SA radar"). Creates one ability row and
# one link: keep it the last row-creating section. Then the radar groups (new row) and the per-weapon lists are rebuilt, and every radar loadout must
# carry a radar weapon. See lateralus/radar_loadouts_1125.py.
import radar_loadouts_1125;print('RADAR LOADOUTS',radar_loadouts_1125.apply(t,g,ok,rec,_HR))
_heli['radar']=_HR.contract(t)['radar'];radar_weapons_1124.apply(t,ok,rec,_heli)
radar_loadouts_1125.check(t,ok,rec,_heli['radarWeapons'])
# ---------- SAM ranges brought into line + AMRAAM burn 3.35 (Lateralus 25 Nov 2026 11:0x PST, thread 1568104480459722894: "1.-6. agreed", "AMRAAM: yes
# increase the burn", "queue it all"). Data only, existing rows. See lateralus/sam_ranges_1125.py.
import sam_ranges_1125;print('SAM RANGES',sam_ranges_1125.apply(t,g,ok,rec,_heli))
# ---------- FB-10 = HQ-17A missile stat clone instead of AMRAAM (Lateralus 25 Nov 2026 11:1x PST, "ok queue it"). Existing row only; after sam_ranges.
# See lateralus/fb10_hq17a_1125.py.
import fb10_hq17a_1125;print('FB-10 HQ-17A',fb10_hq17a_1125.apply(t,g,ok,rec,_heli))
# ---------- China tripod weapons crewed like vanilla: gunner kneels at the weapon on the ground (Osama 25 Nov 2026 10:2x: "We need this for all
# the tripod based weapons"). See crew_weapons_1125.py.
import crew_weapons_1125;crew_weapons_1125.apply(t,g,ok,rec)
# ---------- KS-23 slug 4.99 -> 3.5 and GM-94 thermobaric 5 -> 3 base damage (Lateralus 25 Nov 2026 19:0x PST). Existing rows only.
# See lateralus/ks23_gm94_damage_1125.py.
import ks23_gm94_damage_1125;ks23_gm94_damage_1125.apply(t,g,ok,rec)

# Every disposable launcher: one round per carrier, or the vanilla row unchanged (Lateralus 23 Nov 2026 22:4x). Keep this the last section.
rec['disposable_vanilla_multi_round']=disposable_launchers_1123.check(t,ok,a.vanilla)
# The game's WeaponCoverage rule on the patches this build writes: one weapon row without an ammo row and the game applies NO Freedom Arrow data
# (0.9.7-dev.1 / SRAW A, Lateralus 24 Nov 18:0x). See weapon_coverage_check.py.
import weapon_coverage_check;rec['weapon_coverage_rows']=weapon_coverage_check.check(t,patches,ok)
# ---------- ROC specialization and reserved IDs (Osama 25 Nov 2026 00:5x PST, thread 1575071006240931931). Loads tools/roc/roc.py only on its branch
# (codex/batch/shawn/roc) and runs the two checks above again on its rows; on other branches it adds nothing. Fails if any row uses a reserved ID that its
# owner did not make (mod/id-reservations.json), or if a section after this line makes rows. New sections go above the disposable-launcher check.
# ---------- Back-pocket China weapons, no squad yet: QJY-88, QBZ-192 MLOK, VQX191, QBU-202 (Osama 25 Nov 13:3x). See backpocket_weapons_1125.py.
import backpocket_weapons_1125;backpocket_weapons_1125.apply(t,g,ok,rec)
import roc_hook;roc_hook.apply(t,g,ok,rec,recheck=lambda:(disposable_launchers_1123.check(t,ok,a.vanilla),weapon_coverage_check.check(t,patches,ok)))
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
# Type 100 CSV CH-901 round (zbd100.py, Osama 22 Nov 13:5x "Give its CH-901 60mm penetration"): an own copy of 2018448 keeps the NLOS seeker lock
# only if nlos.json lists it. The previous build's copy id (type100_ch901) is replaced, so a shifted row id never leaves a stale entry.
_nf=SRC/'UserData/FreedomArrow/nlos.json';_nl=json.loads(_nf.read_text());_old=_nl.get('type100_ch901');_new=rec['zbd100']['ch901_round']
# 0.9.7 (nlos_cruise_1124.py, Osama 24 Nov 2026 "it should just act like a cruise missile"): nlos.json stays empty; the Type 100 CH-901 round uses the
# Iskander-M guidance like the other NLOS rounds, so it is not added back here.
if 'nlos_cruise_1124' in rec:
    ok(_nl['ammunition']==[] and 'type100_ch901' not in _nl,('nlos.json stays empty',_nl['ammunition']))
else:
    _nl['ammunition']=[x for x in _nl['ammunition'] if x!=_old]+[_new];_nl['type100_ch901']=_new;_nf.write_text(json.dumps(_nl,indent=2)+'\n')
(SRC/_HR.FILE).write_text(json.dumps(_heli,indent=2)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
