"""Stryker M-SHORAD loadouts (Lateralus 16 Nov 2026 09:0x PST, thread 1571554273639006392: "Change Stryker M-Shorad so it has a laser when
equipped with APKWS loadout, change APKWS loadout to +30, double stinger pod loadout to +40, hellfire loadout to +60, SRAT II / Trophy APS to
+45"). Unit 20. Options (dev.24, Arsenal names): 1937 Fletcher = APKWS (Custom_Option_APKWS_AAM) 40 -> 30 and gets the vehicle laser
designator (ability 8 "Laser Veh", not default, 1500 m, usable on the move, as the BRDM-3), linked to the unit; 1936 double Stinger pod 50 -> 40;
1938 Hellfire 70 -> 60; 1934 SRAT II / APS (Custom_Option_SRAT2_APS) 55 -> 45. apply(t, g, ok) checks every old value first."""
UNIT=20;LASER=8
PRICES={1937:('APKWS (Fletcher)',40,30),1936:('double Stinger pod',50,40),1938:('Hellfire',70,60),1934:('SRAT II / APS',55,45)}
def apply(t,g,ok):
    O,M,AB,UA,U=t['OptionsJson'],t['ModificationsJson'],t['AbilitiesJson'],t['UnitAbilitiesJson'],t['Units']
    ok(U[UNIT].get('Name')=='Stryker M-SHORAD',f'unit {UNIT} is the Stryker M-SHORAD')
    for i,(n,old,new) in PRICES.items():
        ok(M[O[i]['ModificationId']]['UnitId']==UNIT,f'{n} [{i}] belongs to the M-SHORAD')
        ok((O[i].get('Cost') or 0)==old,f'{n} [{i}] costs {old}');g.put('OptionsJson',i,{'Cost':new});ok(O[i]['Cost']==new,f'{n} now {new}')
    a=AB[LASER];ok(a.get('IsLaserDesignator') and not a.get('IsDefault') and a.get('LaserUsableInMove'),'ability 8 is a non-default vehicle laser')
    o=O[1937];ok(not any(o.get(f'Ability{k}Id') for k in (1,2,3)),'APKWS option has no ability yet')
    g.put('OptionsJson',1937,{'Ability1Id':LASER})
    if not any(x.get('UnitId')==UNIT and x.get('AbilityId')==LASER for x in UA.values()):
        g.add('UnitAbilitiesJson',next(x for x in UA.values() if x.get('UnitId')==UNIT),{'UnitId':UNIT,'AbilityId':LASER})
    ok(O[1937].get('Ability1Id')==LASER and any(x.get('UnitId')==UNIT and x.get('AbilityId')==LASER for x in UA.values()),'APKWS option has the linked laser')
    return {'prices':{str(k):v[2] for k,v in PRICES.items()},'laserOn':1937}
