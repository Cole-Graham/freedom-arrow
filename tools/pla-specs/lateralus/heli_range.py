"""Helicopter range and optics (Lateralus 21 Nov 2026, thread 1568104480459722894; proposal: Lateralus 0.9 Changelog, "Helicopter range" tab).
- Row 19: every radar ability row has RadarLowAltOpticsModifier = RadarLowAltWeaponRangeModifier. In 0.9.3 only row 59
  "Radar LongRange Static" differs (optics 1.0, range 2.0; Patriot, Buk, IRIS-T SLM, S-300/S-350/S-400, HQ-6A/9B/9C/11/12/16).
- Rows 16-17 and 20 (Option B): each radar row gets a helicopter range multiplier and a helicopter optics multiplier. They start at the
  row's own low-altitude multipliers, so nothing changes in game until a value is edited.
- Row 3/6: helicopter range per ammo id ("ammo": {id: range in game units, as LowAltRange}). Lateralus 21 Nov 11:37: start at the current
  low-altitude values, so every ammo that can target helicopters (TargetType flag 8) gets its LowAltRange (GroundRange if 0).
- Rows 12-14: helicopter optics per sensor ("sensors", matched by the observer's ground/low/high optics), starting at OpticsLowAltitude.
- Row 18: "heliUnits" = units with at least one weapon whose ammo can target helicopters (card lines are shown only for them).
The runtime (runtime-qa/HeliRange.cs) finds a unit's radar row by the values the game copies into RadarAbilityComponent, so rows with the
same values must have the same helicopter multipliers (checked here).
apply(t, g, ok) checks the old values first; contract(t) returns helicopter-range.json; check(merged) lists what is missing in a package."""
FIX={59:(1.0,2.0)}  # ability row: (old, new) RadarLowAltOpticsModifier
FILE='UserData/FreedomArrow/helicopter-range.json'
AMMO={}  # ammo id: helicopter range (game units) that differs from its LowAltRange; others start at LowAltRange
EDIT={}  # ability row: {'helicopterRangeMultiplier': x, 'helicopterOpticsMultiplier': y}; empty = start at today's values
def radar_rows(AB):return {i:a for i,a in AB.items() if a and a.get('IsRadar')}
def key(a):return (float(a['RadarLowAltOpticsModifier']),float(a['RadarHighAltOpticsModifier']),float(a['RadarLowAltWeaponRangeModifier']),
                   float(a['RadarHighAltWeaponRangeModifier']),float(a['RadarSwitchCooldown']),bool(a['IsRadarStatic']))
def apply(t,g,ok):
    AB=t['AbilitiesJson']
    for i,(old,new) in FIX.items():
        a=AB[i];ok(a['IsRadar'] and a['RadarLowAltOpticsModifier']==old and a['RadarLowAltWeaponRangeModifier']==new,(i,'radar low optics',a['RadarLowAltOpticsModifier']))
        g.put('AbilitiesJson',i,{'RadarLowAltOpticsModifier':new})
    rows=radar_rows(AB)
    ok(all(a['RadarLowAltOpticsModifier']==a['RadarLowAltWeaponRangeModifier'] for a in rows.values()),'every radar row: low optics = low range multiplier')
    A=t['AmmunitionsJson']
    for i,r in AMMO.items():ok(i in A and int(A[i].get('TargetType') or 0)&8 and r>0,(i,'helicopter range ammo can target helicopters'))
def contract(t):
    AB,U,UA=t['AbilitiesJson'],t['Units'],t['UnitAbilitiesJson']
    users={}
    for r in UA.values():
        if r:users.setdefault(r['AbilityId'],set()).add(r['UnitId'])
    groups={}
    for i,a in sorted(radar_rows(AB).items()):
        k=key(a);v=EDIT.get(i,{})
        m=(float(v.get('helicopterRangeMultiplier',a['RadarLowAltWeaponRangeModifier'])),float(v.get('helicopterOpticsMultiplier',a['RadarLowAltOpticsModifier'])))
        assert m[0]>0 and m[1]>0,(i,m)
        gr=groups.setdefault(k,{'abilities':[],'names':[],'multipliers':m})
        assert gr['multipliers']==m,(i,'radar rows with the same values need the same helicopter multipliers',gr['abilities'])
        gr['abilities'].append(i);gr['names'].append(a.get('Name'))
    radar=[{'abilities':gr['abilities'],'names':gr['names'],'lowAltOptics':k[0],'highAltOptics':k[1],'lowAltRange':k[2],'highAltRange':k[3],
            'switchCooldown':k[4],'static':k[5],'helicopterRangeMultiplier':gr['multipliers'][0],'helicopterOpticsMultiplier':gr['multipliers'][1]}
           for k,gr in groups.items()]
    A,WA,S=t['AmmunitionsJson'],t['WeaponAmmunitionsJson'],t['SensorsJson']
    used={r['AmmunitionId'] for r in WA.values() if r}
    heli_ammo={i for i in used if i in A and int(A[i].get('TargetType') or 0)&8}
    ammo={str(i):float(AMMO.get(i,A[i]['LowAltRange'] if A[i].get('LowAltRange') else A[i]['GroundRange'])) for i in sorted(heli_ammo)}
    heli_units=sorted({r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] in heli_ammo})
    trip={}
    for i,r in sorted(S.items()):
        if not r:continue
        k=(float(r['OpticsGround']),float(r['OpticsLowAltitude']),float(r['OpticsHighAltitude']))
        trip.setdefault(k,[]).append(i)
    sensors=[{'sensors':ids,'ground':k[0],'low':k[1],'high':k[2],'helicopterOptics':k[1]} for k,ids in trip.items()]
    return {'note':'Helicopter range and optics (Lateralus 21 Nov 2026). Radar entries are matched by the values in RadarAbilityComponent. '
                   'Multipliers replace the low-altitude ones only when the target is a helicopter at Low altitude and the radar is on.',
            'ammo':ammo,'radar':radar,'sensors':sensors,'heliUnits':heli_units,'perfLogSeconds':60}
def check(get):
    AB=get('AbilitiesJson');miss=[]
    for i,(old,new) in FIX.items():
        if AB.get(i,{}).get('RadarLowAltOpticsModifier')!=new:miss.append(f'ability {i} RadarLowAltOpticsModifier {new}')
    return miss
