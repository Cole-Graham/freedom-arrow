"""Stryker M-SHORAD: the APKWS laser moves to the option's second ability slot (Lateralus 16 Nov 2026, thread 1571554273639006392: "queue up a
fix to add the laser icon to unit card when the APKSW loadout is selected on the stryker shorad").
Why (read from GameAssembly 6000.3.24f1): UnitsInfoService.ApplyCurrentMods (0x72BB30) sets ActiveAbilities to a copy of the default ability,
then merges one ability per slot: options.FirstOrDefault(o => o.Ability1Id > 0).Ability1, the same for Ability2Id and Ability3Id
(lambdas b__19_34/36/38 test Options +0x90/+0x94/+0x98). The unit card (UnitInfoCard.SetUnitAbilities) shows the laser icon from
ActiveAbilities.IsLaserDesignator. dev.25 put the laser (ability 8) in Ability1 of option 1937, but every M-SHORAD armour option also fills
Ability1 (69 and 70 "Empty ability" 4, 1934 "APS IronFist NoModel" 82). Only the first of those options that the game reads gives its slot-1
ability, so the laser is dropped (and with the APS armour, either the APS or the laser is dropped). No other M-SHORAD option uses slot 2.
A scan of every unit in dev.25 finds no other unit with two modifications filling the same slot with a real ability.
apply(t, g, ok) checks the dev.25 values first; vanilla writes an empty slot as 0."""
UNIT=20;OPTION=1937;LASER=8
def apply(t,g,ok):
    O,M,AB=t['OptionsJson'],t['ModificationsJson'],t['AbilitiesJson']
    ok(M[O[OPTION]['ModificationId']]['UnitId']==UNIT,f'option {OPTION} (APKWS) belongs to the M-SHORAD')
    ok([O[OPTION].get(f'Ability{k}Id') or 0 for k in (1,2,3)]==[LASER,0,0],f'APKWS option has the laser in slot 1 only (dev.25)')
    mods={m['Id'] for m in M.values() if m.get('UnitId')==UNIT}
    ok(not any(o.get('Ability2Id') for o in O.values() if o.get('ModificationId') in mods),'no M-SHORAD option uses ability slot 2')
    ok(AB[LASER].get('IsLaserDesignator') and not AB[LASER].get('IsDefault'),'ability 8 is a non-default laser')
    g.put('OptionsJson',OPTION,{'Ability1Id':0,'Ability2Id':LASER})
    ok([O[OPTION].get(f'Ability{k}Id') or 0 for k in (1,2,3)]==[0,LASER,0],'APKWS option now has the laser in slot 2')
    return {'option':OPTION,'Ability2Id':LASER}
def slot_collisions(U,M,O,AB,units):
    """Units where options of two different modifications fill the same ability slot and one of them is a real ability (not "Empty ability"):
    only one of those abilities reaches the unit. Returns a list of (unit id, name, slot)."""
    flags=('IsLaserDesignator','IsAPS','IsRadar','IsSmoke','IsDecoy','IsResupplyAbility','IsSneakAbility','IsAmphibious')
    def real(a):
        r=AB.get(a,{});return r.get('Name')!='Empty ability' and (r.get('ECMAccuracyMultiplier') not in (None,0,1) or any(r.get(f) for f in flags) or 'APS' in (r.get('Name') or ''))
    bymod={}
    for o in O.values():bymod.setdefault(o.get('ModificationId'),[]).append(o)
    out=[]
    for u in units:
        if u not in U:continue
        for k in (1,2,3):
            per={m['Id']:[o[f'Ability{k}Id'] for o in bymod.get(m['Id'],[]) if o.get(f'Ability{k}Id')] for m in M.values() if m.get('UnitId')==u}
            per={i:v for i,v in per.items() if v}
            if len(per)>1 and any(real(a) for v in per.values() for a in v):out.append((u,U[u].get('Name'),k))
    return out
