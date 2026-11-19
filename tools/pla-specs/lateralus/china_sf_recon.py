"""China SF smoke/launcher/sprint and cheap-recon lasers (Lateralus 16 Nov 2026 16:5x PST, thread 1571942037488410817):
"Lower Sea Dragons smoke from 4 -> 1 / Mountain Lions have 3 HJ-12 launchers, they should only have 1 launcher with 3 ammo / Mountain Lions smoke
4 -> 1 / remove sprint from Mountain Lions / Whistling Arrows smoke 4 -> 1 / Thunder Gods smoke 4 -> 1 / Taishan Eagles PF-89 ammo 1 -> 4 /
Remove all lasers from cheap recon infantry (40 points and less)".
- "Mountain Lions" = Mountain Leopards 高原雪豹 (unit 1186), the only Mountain squad. Sea Dragons = both squads of that name (1190, 1191).
- Smoke = the squad's own ability row SmokeAmmunitionQuantity (each row has one user). Sprint = IsInfantrySprint.
- HJ-12: three members carried it (special weapon, 1 round each). Members 2015362 (QBU-10) and 2015364 lose it; 2015363 keeps it with 3 rounds
  (weapon-ammo row 2015368 Quantity 1 -> 3; Quantity is per carrier).
- Lasers: infantry with squad members, Role 32 recon, cost <= 40 and a laser-designator ability. Rows with one user are edited; Razvedka 725 and
  Scouts 726 share row 2000609 with 15 dearer squads, so they get a copy without the laser.
apply(t, g, ok) checks every old value first; check(merged) returns what is missing in a finished package."""
SMOKE={2013379:1190,2013408:1191,2013253:1186,2013189:1184,2012021:1143}  # ability row: unit
HJ12={'weapon':2011864,'keep':2015363,'drop':(2015362,2015364),'ammo_row':2015368}
PF89={'unit':1203,'ammo_row':2015568,'weapon':2011887}
LASER_OWN={2012177:1149,2012570:1164,2004807:1014,2005030:1027,2012591:1165,2014056:1213}  # ability row: unit (one user each)
LASER_SHARED={725:2000609,726:2000609}  # unit: shared ability row
NO_LASER={'IsLaserDesignator':False,'LaserMaxRange':0.0,'LaserUsableInMove':False}
def apply(t,g,ok):
    U,AB,UAB,SM,WA=t['Units'],t['AbilitiesJson'],t['UnitAbilitiesJson'],t['SquadMembersJson'],t['WeaponAmmunitionsJson']
    users=lambda a:sorted(r['UnitId'] for r in UAB.values() if r['AbilityId']==a)
    for a,u in SMOKE.items():
        ok(users(a)==[u] and AB[a]['IsSmoke'] and AB[a]['SmokeAmmunitionQuantity']==4,f'{U[u]["HUDName"]}: own ability {a}, smoke 4')
        g.put('AbilitiesJson',a,{'SmokeAmmunitionQuantity':1})
    ok(AB[2013253]['IsInfantrySprint'] is True,'Mountain Leopards sprint');g.put('AbilitiesJson',2013253,{'IsInfantrySprint':False})
    ok(sorted(r['Id'] for r in SM.values() if r['UnitId']==1186 and r.get('SpecialWeaponId')==HJ12['weapon'])==sorted((HJ12['keep'],*HJ12['drop'])),'Mountain Leopards: 3 HJ-12 carriers')
    ok(WA[HJ12['ammo_row']]['UnitId']==1186 and WA[HJ12['ammo_row']]['WeaponId']==HJ12['weapon'] and WA[HJ12['ammo_row']]['Quantity']==1,'HJ-12 1 round')
    for m in HJ12['drop']:g.put('SquadMembersJson',m,{'SpecialWeaponId':0})
    g.put('WeaponAmmunitionsJson',HJ12['ammo_row'],{'Quantity':3})
    r=WA[PF89['ammo_row']];ok((r['UnitId'],r['WeaponId'],r['Quantity'])==(PF89['unit'],PF89['weapon'],1),'Taishan Eagles PF-89 1 round')
    g.put('WeaponAmmunitionsJson',PF89['ammo_row'],{'Quantity':4})
    cheap=sorted(u['Id'] for u in U.values() if u.get('Role')==32 and (u.get('Cost') or 0)<=40 and any(s['UnitId']==u['Id'] for s in SM.values())
                 and any(AB.get(x['AbilityId'],{}).get('IsLaserDesignator') for x in UAB.values() if x['UnitId']==u['Id']))
    ok(cheap==sorted([*LASER_OWN.values(),*LASER_SHARED]),f'cheap recon with lasers {cheap}')
    for a,u in LASER_OWN.items():
        ok(users(a)==[u] and AB[a]['IsLaserDesignator'],f'{U[u]["HUDName"]}: own laser ability {a}');g.put('AbilitiesJson',a,NO_LASER)
    copy=None;ok(AB[2000609]['IsLaserDesignator'] and len(users(2000609))==17,'shared laser ability 2000609 has 17 users')
    for u,a in LASER_SHARED.items():
        copy=copy or g.add('AbilitiesJson',AB[a],{**NO_LASER,'Name':AB[a]['Name']+' no laser (FA cheap recon)'})
        row=[x for x in UAB.values() if x['UnitId']==u and x['AbilityId']==a];ok(len(row)==1,f'{u}: one link to {a}')
        g.put('UnitAbilitiesJson',row[0]['Id'],{'AbilityId':copy})
    left=[u['Id'] for u in U.values() if u.get('Role')==32 and (u.get('Cost') or 0)<=40
          and any(AB.get(x['AbilityId'],{}).get('IsLaserDesignator') for x in UAB.values() if x['UnitId']==u['Id'])]
    ok(not left and AB[2000609]['IsLaserDesignator'] and len(users(2000609))==15,'no cheap recon laser left; shared row keeps its laser for 15 squads')
    ok(all(AB[a]['SmokeAmmunitionQuantity']==1 for a in SMOKE) and not AB[2013253]['IsInfantrySprint'] and WA[HJ12['ammo_row']]['Quantity']==3
       and WA[PF89['ammo_row']]['Quantity']==4,'smoke 1, no sprint, HJ-12 3, PF-89 4')
    return {'smoke_1':SMOKE,'sprint_removed':1186,'hj12':{'carrier':HJ12['keep'],'removed':HJ12['drop'],'rounds':[1,3]},'pf89_rounds':[1,4],
            'lasers_removed':sorted([*LASER_OWN.values(),*LASER_SHARED]),'no_laser_copy':copy}
def check(T):
    """T(table) -> merged rows of the finished package. Returns a list of problems."""
    AB,UAB,SM,WA,U=T('AbilitiesJson'),T('UnitAbilitiesJson'),T('SquadMembersJson'),T('WeaponAmmunitionsJson'),T('Units')
    # By unit, not by ability row: from 0.9.1-dev.4 the squads link shared rows with the same values (ability row cleanup, Lateralus 19 Nov 2026).
    def smoke(u):return [AB.get(x['AbilityId'],{}).get('SmokeAmmunitionQuantity') for x in UAB.values() if x.get('UnitId')==u and AB.get(x['AbilityId'],{}).get('IsSmoke')]
    bad=[f'unit {u} smoke {smoke(u)} (want [1])' for u in SMOKE.values() if smoke(u)!=[1]]
    if any(AB.get(x['AbilityId'],{}).get('IsInfantrySprint') for x in UAB.values() if x.get('UnitId')==1186):bad.append('Mountain Leopards still sprint')
    if [r['Id'] for r in SM.values() if r.get('UnitId')==1186 and r.get('SpecialWeaponId')==HJ12['weapon']]!=[HJ12['keep']]:bad.append('Mountain Leopards HJ-12 carriers != 1')
    if WA.get(HJ12['ammo_row'],{}).get('Quantity')!=3:bad.append('HJ-12 rounds != 3')
    # 4 PF-89 rounds in the squad: 1 carrier x 4 (dev.33) or, from dev.44 (Osama "4 disposable AT weapons"), 4 carriers x 1 like vanilla disposables
    pf=WA.get(PF89['ammo_row'],{}).get('WeaponId',PF89['weapon'])
    carriers=sum(1 for r in SM.values() if r.get('UnitId')==PF89['unit'] and pf in (r.get('PrimaryWeaponId'),r.get('SpecialWeaponId')))
    if WA.get(PF89['ammo_row'],{}).get('Quantity',0)*max(carriers,1)!=4:bad.append('Taishan Eagles PF-89 rounds != 4')
    bad+=[f'unit {u} still has a laser' for u in [*LASER_OWN.values(),*LASER_SHARED]
          if any(AB.get(x['AbilityId'],{}).get('IsLaserDesignator') for x in UAB.values() if x.get('UnitId')==u)]
    return bad
