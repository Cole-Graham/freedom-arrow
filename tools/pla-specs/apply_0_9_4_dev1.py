"""Freedom Arrow 0.9.4-dev.1 batch data over exact 0.9.3 (build 242). Opened by BA Codex thread 1567745029781454889 (Osama, Spetsnaz Alpha stand-off RPG-30).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent),str(Path(__file__).parent/'lateralus')]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.4-dev.1';PREV='0.9.3'
# 0.9.3 (build 242, the playtest released 20 Nov 2026) was built in out/local-093r242.
BASE=json.loads((REL/f'out/local-093r242/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
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
# 12 images, BROKEN ARROW mark removed (work/osama-art-20261120; PAP support-hand finger fixed), 816x549 with the vanilla bottom fade -> releases/0.6/source/
# runtime-qa/icons/FA_CN_INF_<CARD>-Portrait.png, registered in CardIcons.cs (needs the runtime DLL rebuild). PortraitFileName only.
_CARDS={
 'AIRBORNE_HELO':['Airborne 空降兵','Assault Raiders 突击队','Pathfinders 先遣队','Recon 侦察组'],
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
ok(len(_done)==34,('34 cards (Snipers and QJZ-89 Team are two cards each)',len(_done)))
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
# ---------- 11. Dedicated tank-hunter teams fire 15 rounds per minute; Tank Hunters 6 men (Osama 21 Nov 2026 13:16 PST, thread 1567745029781454889:
# "dedicate tank hunter teams should have 15 RPM on their AT weapons ... Rangers MAAWS and Tank hunters (which by the way should be 6 man). Long range fire
# support like SPG and PF-98 tripod are not included"; 13:2x "yes make sure line infantry get seperate weapons from fire support"). Reloadable launchers
# reload 6 s (10 rounds/min); these teams get 4 s (15/min). A launcher row shared with any other squad is copied for the team, so line infantry and fire
# support keep 10/min. PF-98 Tank Hunters (1155) is in no specialization (Osama: "There are no PF-98 tank hunters anymore"): left out.
SW=t['SquadWeaponsJson'];AR=t['ArmorsJson'];UA=t['UnitArmorsJson']
_TH={74:('Rangers RAWS',(202,787)),410:('Rangers MAAWS',(505,788)),127:('RPG-29 Vampyr',(172,)),1139:('Tank Hunters',(2011919,))}
_sw_users=lambda w:{r['UnitId'] for r in SW.values() if r.get('WeaponId')==w}|{m['UnitId'] for m in SM.values() if w in (m.get('PrimaryWeaponId'),m.get('SpecialWeaponId'))}|{r['UnitId'] for r in WA.values() if r.get('WeaponId')==w}
_th={}
for _u,(_n,_ws) in _TH.items():
    ok(U[_u]['HUDName'].strip().startswith(_n),(_n,_u))
    for _w in _ws:
        ok(W[_w]['Type']==62 and W[_w]['MagazineSize']==1 and (W[_w]['MagazineReloadTimeMin'],W[_w]['MagazineReloadTimeMax'])==(6.0,6.0),(_n,_w,'reloadable launcher, 6 s'))
        _others=_sw_users(_w)-{_u}
        if _others:
            _c=g.add('WeaponsJson',W[_w],{'Name':(W[_w].get('Name') or '')+' FA tank hunter','MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
            for r in [r for r in SW.values() if r.get('UnitId')==_u and r.get('WeaponId')==_w]:g.put('SquadWeaponsJson',r['Id'],{'WeaponId':_c})
            for r in [r for r in WA.values() if r.get('UnitId')==_u and r.get('WeaponId')==_w]:g.put('WeaponAmmunitionsJson',r['Id'],{'WeaponId':_c})
            for m in [m for m in SM.values() if m.get('UnitId')==_u]:
                for k in ('PrimaryWeaponId','SpecialWeaponId'):
                    if m.get(k)==_w:g.put('SquadMembersJson',m['Id'],{k:_c})
            ok(_u not in _sw_users(_w) and _sw_users(_c)=={_u},(_n,_w,'team moved to its own copy'))
            ok(all((W[_w]['MagazineReloadTimeMin'],W[_w]['MagazineReloadTimeMax'])==(6.0,6.0) for _ in [0]),(_n,_w,'shared original stays 6 s for',sorted(_others)))
            _th.setdefault(f'{_u} {_n}',[]).append({'weapon':_w,'copy':_c,'others_keep_10_per_min':sorted(U[o]['HUDName'].strip() for o in _others if U.get(o))})
        else:
            g.put('WeaponsJson',_w,{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
            _th.setdefault(f'{_u} {_n}',[]).append({'weapon':_w,'in_place':True})
    _tw=[r['WeaponId'] for r in SW.values() if r.get('UnitId')==_u and W.get(r['WeaponId'],{}).get('Type')==62]
    ok(_tw and all((W[w]['MagazineReloadTimeMin'],W[w]['MagazineReloadTimeMax'])==(4.0,4.0) for w in _tw),(_n,'every launcher 4 s',_tw))
ok((W[2016259]['HUDName'],W[2016259]['MagazineReloadTimeMin'],W[2016259]['MagazineReloadTimeMax'])==('PF-98 (tripod)',6.0,6.0),'PF-98 Team tripod launcher untouched (fire support)')
# Tank Hunters 1139: 8 -> 6 men. Two plain QBZ-191 riflemen out (newest first); the PF-98A gunner stays; armour 8Men (84) -> vanilla 6Men (82), same AV 6.
_ms=[m for m in SM.values() if m.get('UnitId')==1139];_rf=[m for m in _ms if m.get('PrimaryWeaponId')==2003998 and not m.get('SpecialWeaponId')]
ok(len(_ms)==8 and len(_rf)==7,('Tank Hunters 8 men, 7 riflemen',len(_ms),len(_rf)))
for m in sorted(_rf,key=lambda m:m['Id'])[-2:]:g.remove('SquadMembersJson',m['Id'])
_ua=[r for r in UA.values() if r.get('UnitId')==1139];ok(len(_ua)==1 and _ua[0]['ArmorId']==84 and AR[82]['Name']=='Armor Infantry 6Men' and AR[82]['ArmorValue']==AR[84]['ArmorValue']==6,('Tank Hunters armour row',_ua))
g.put('UnitArmorsJson',_ua[0]['Id'],{'ArmorId':82})
_ms=[m for m in SM.values() if m.get('UnitId')==1139]
ok(len(_ms)==6 and sum(1 for m in _ms if m.get('SpecialWeaponId'))==1 and AR[82]['MaxHealthPoints']==30,'Tank Hunters 6 men, 1 PF-98A, 30 HP')
rec['tank_hunter_15_per_min']={'reload_s':[6.0,4.0],'teams':_th,'tank_hunters_men':[8,6],'tank_hunters_armor':[84,82]}
# ---------- 12. Helicopter range and optics (Lateralus 21 Nov 2026, thread 1568104480459722894; proposal in the Lateralus 0.9 Changelog, "Helicopter range"
# tab; tested in 0.9.4-dev.1-test1..test4 from codex/batch/lateralus/heli-range; 13:2x PST "queue up all of the proposal for the next 0.9.4 dev build").
# lateralus/heli_range.py: radar row 59 low-altitude optics 1.0 -> 2.0; long-range SAM sensor low optics 2650 -> 2000; long-range radar helicopter range x1.25;
# helicopter-range.json for runtime-qa/HeliRange.cs and HeliRangeCard.cs.
import heli_range as _HR
_HR.apply(t,g,ok);_heli=_HR.contract(t)
ok(len(_heli['radar'])>0 and not _HR.check(lambda tab:t[tab]),'helicopter range contract and radar row 59')
rec['heli_range']={'radar_low_optics':{str(k):list(v) for k,v in _HR.FIX.items()},'radar_groups':len(_heli['radar']),'ammo':len(_heli['ammo'])}
# ---------- 11b. Assaultmen SMAW (Osama 21 Nov 2026 13:2x PST: "for Assaultmen SMAW we do want the increase in ROF. however, we reduce their thermobaric
# damage to compensate so their DPS is the same as before the rof change. Also give them 9 thermobaric ammo"; Mech. Riflemen MAAWS stays: "line infantry so no").
# SMAW (61) and its thermobaric round (41) are used only by Assaultmen SMAW (63), so both change in place. Reload 6 -> 4 s; thermobaric damage x4/6 = 4.0 -> 2.667
# (same damage per second); thermobaric rounds 6 -> 9 (same total damage, 24). The anti-tank round keeps 10 damage and gets the faster reload.
_SMAW,_TB,_AS=61,41,63
ok(W[_SMAW]['HUDName']=='SMAW' and (W[_SMAW]['MagazineReloadTimeMin'],W[_SMAW]['MagazineReloadTimeMax'],W[_SMAW]['MagazineSize'])==(6.0,6.0,1),'SMAW reloads 6 s')
ok(_sw_users(_SMAW)=={_AS},('SMAW only on Assaultmen SMAW',_sw_users(_SMAW)))
_tbwa=[r for r in WA.values() if r.get('AmmunitionId')==_TB]
ok(len(_tbwa)==1 and _tbwa[0]['UnitId']==_AS and _tbwa[0]['WeaponId']==_SMAW and _tbwa[0]['Quantity']==6 and A[_TB]['Damage']==4.0,('thermobaric round only on Assaultmen SMAW, 6 rounds, 4 damage',_tbwa))
g.put('WeaponsJson',_SMAW,{'MagazineReloadTimeMin':4.0,'MagazineReloadTimeMax':4.0})
g.put('AmmunitionsJson',_TB,{'Damage':round(4.0*4/6,3)})
g.put('WeaponAmmunitionsJson',_tbwa[0]['Id'],{'Quantity':9})
ok(abs(A[_TB]['Damage']/4.0-4.0/6.0)<1e-3 and abs(A[_TB]['Damage']*9-24)<0.01,('thermobaric DPS and total damage unchanged',A[_TB]['Damage']))
ok(all(A[r['AmmunitionId']]['Damage']==10.0 for r in WA.values() if r.get('UnitId')==_AS and r.get('WeaponId')==_SMAW and r.get('AmmunitionId')!=_TB),'SMAW anti-tank round keeps 10 damage')
ok(not any(m.get('UnitId')==707 and W.get(m.get('SpecialWeaponId'),{}).get('MagazineReloadTimeMin')==4.0 for m in SM.values()),'Mech. Riflemen MAAWS (line infantry) unchanged')
rec['assaultmen_smaw']={'unit':_AS,'weapon':_SMAW,'reload_s':[6.0,4.0],'thermobaric':_TB,'damage':[4.0,A[_TB]['Damage']],'rounds':[6,9]}
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
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(SRC/_HR.FILE).write_text(json.dumps(_heli,indent=2)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
