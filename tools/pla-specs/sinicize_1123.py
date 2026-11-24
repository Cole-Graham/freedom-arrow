"""Chinese names on the new PLAN / airborne vehicles (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889: "and make sure you rename everything so
its chinese", "including weapons and ammunition"). MODEL BUILD ONLY. Runs after ztd05_booker / zsd05_ampv / zbd05_ifv / vn3_loadout.
English text only (no bilingual names: no-bilingual-card-names). The vanilla US / Russian rows are not renamed: these four units get their own
renamed copies of the weapons, rounds and (shared vanilla) turrets, with identical stats, as plz25_navy_1123.py did for the PLZ-25.
- ZTD-05 (Booker copy): M35 -> 105 mm rifled gun (105 mm APFSDS, 105 mm HESH); M240 -> Type 86 7.62 mm; M2 -> QJC-88 12.7 mm; Iron Fist APS option
  -> GL-5 APS. The Booker's unused XM913 ammunition rows are dropped.
- ZSD-05 / ZBD-05 (AMPV copies): M2 -> QJC-88 12.7 mm; Mk19 -> QLZ-87 35 mm AGL; Bushmaster II -> 30 mm autocannon (30 mm AP / HE); M240 -> Type 86
  7.62 mm; Javelin -> HJ-12 (same stats as the Javelin); BRAT2 APS option -> Reactive armour + GL-5 APS.
- VN-3: 2A72 -> 30 mm autocannon (30 mm AP / HE); PKT -> Type 86 7.62 mm (7.62x54mm -> 7.62 mm)."""
UNITS = ('PLA ZTD-05', 'PLA ZSD-05', 'PLA ZBD-05', 'PLA VN-3')
WEAP = {657: '105 mm rifled gun', 27: 'Type 86 7.62 mm', 18: 'QJC-88 12.7 mm', 21: 'QLZ-87 35 mm AGL', 23: '30 mm autocannon', 76: 'HJ-12',
        2: '30 mm autocannon', 7: 'Type 86 7.62 mm'}
AMMO = {505: '105 mm APFSDS', 504: '105 mm HESH', 19: '12.7 mm', 27: '7.62 mm', 50: '35 mm HE grenade', 22: '30 mm AP', 53: '30 mm HE',
        2000174: 'HJ-12', 207: '30 mm HE', 208: '30 mm AP', 9: '7.62 mm'}
OPTS = {'Custom_Option_M35_105mm_gun': '105 mm rifled gun', 'Custom_Option_IronFist_APS': 'GL-5 APS', 'Custom_Option_BRAT2_APS': 'Reactive armour + GL-5 APS',
        'Custom_Option_M2_HMG': 'QJC-88 12.7 mm', 'Custom_Option_Mk19_AGL': 'QLZ-87 35 mm AGL', 'Custom_Option_Bushmaster2_autocannon': '30 mm autocannon',
        'Bushmaster II, Javelin': '30 mm autocannon + HJ-12', 'Autocannon + HJ-73D (4x)': '30 mm autocannon + HJ-73D (4x)',
        'Custom_Option_2A72': '30 mm autocannon', '2A72 + HJ-73D (4x)': '30 mm autocannon + HJ-73D (4x)'}
FOREIGN = ('M2 ', 'Browning', 'M240', 'Mk19', 'Bushmaster', 'Javelin', 'M35', 'M393', 'M900', '2А72', '2A72', 'PKT', 'x173', 'x165', 'x99', 'x51',
           '40×53', 'x54', 'IronFist', 'Iron Fist', 'BRAT', 'XM913', '50x228')


def apply(t, g, ok, rec):
    U, T, TW, TU, W, A, WA, O, M = (t[k] for k in ('Units', 'TurretsJson', 'TurretWeaponsJson', 'TurretUnitsJson', 'WeaponsJson', 'AmmunitionsJson',
                                                    'WeaponAmmunitionsJson', 'OptionsJson', 'ModificationsJson'))

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    wmap, amap, tmap, out = {}, {}, {}, {}
    def wcopy(w):
        if w not in wmap: wmap[w] = g.add('WeaponsJson', W[w], {'Name': f"PLA CN {W[w]['Name']}", 'HUDName': WEAP[w]})
        return wmap[w]
    def acopy(a):
        if a not in amap: amap[a] = g.add('AmmunitionsJson', A[a], {'Name': f"PLA CN {A[a]['Name']}", 'HUDName': AMMO[a]})
        return amap[a]
    for name in UNITS:
        (u,) = [i for i, x in U.items() if x and x.get('Name') == name]
        own = {}
        for r in rows('TurretUnitsJson', UnitId=u):
            tid = r['TurretId']; tws = rows('TurretWeaponsJson', TurretId=tid)
            if not any(w['WeaponId'] in WEAP for w in tws): own[tid] = tid; continue
            if tid in g.native['TurretsJson']:       # shared vanilla turret: renamed copy, once
                if tid not in tmap:
                    tmap[tid] = g.add('TurretsJson', T[tid], {'Name': f"PLA CN {T[tid]['Name']}"})
                    for w in tws: g.add('TurretWeaponsJson', w, {'TurretId': tmap[tid], 'WeaponId': wcopy(w['WeaponId']) if w['WeaponId'] in WEAP else w['WeaponId']})
                own[tid] = tmap[tid]
            else:                                    # this batch's own turret: repoint in place
                for w in tws:
                    if w['WeaponId'] in WEAP: g.put('TurretWeaponsJson', w['Id'], {'WeaponId': wcopy(w['WeaponId'])})
                own[tid] = tid
            g.put('TurretUnitsJson', r['Id'], {'TurretId': own[tid]})
        onturret = {w['WeaponId'] for x in own.values() for w in rows('TurretWeaponsJson', TurretId=x)}
        for r in rows('WeaponAmmunitionsJson', UnitId=u):
            nw = wmap.get(r['WeaponId'], r['WeaponId'])
            if nw not in onturret: g.remove('WeaponAmmunitionsJson', r['Id']); continue
            g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': nw, **({'AmmunitionId': acopy(r['AmmunitionId'])} if r['AmmunitionId'] in AMMO else {})})
        for m in rows('ModificationsJson', UnitId=u):
            for o in rows('OptionsJson', ModificationId=m['Id']):
                ch = {k: own[v] for k, v in o.items() if k.startswith('Turret') and k.endswith('Id') and v in own}
                if o['UIName'] in OPTS: ch['UIName'] = OPTS[o['UIName']]
                if ch: g.put('OptionsJson', o['Id'], ch)
        shown = [W[w['WeaponId']]['HUDName'] for r in rows('TurretUnitsJson', UnitId=u) for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])]
        shown += [A[r['AmmunitionId']]['HUDName'] for r in rows('WeaponAmmunitionsJson', UnitId=u)]
        shown += [o['UIName'] for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id'])]
        ok(not any(f in s for s in shown for f in FOREIGN), (name, 'no US / Russian names', sorted(set(shown))))
        ok({r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)} == {w['WeaponId'] for r in rows('TurretUnitsJson', UnitId=u)
            for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])}, (name, 'ammunition rows = weapons on its turrets'))
        out[name] = sorted(set(shown))
    ok(all(W[w]['HUDName'] in ('M35', 'M240', 'M2 Browning', 'Mk19 AGL', 'Bushmaster II', 'Javelin', '2А72 30mm', 'PKT') for w in WEAP), 'vanilla weapon names untouched')
    rec['sinicize'] = {'weapons': len(wmap), 'rounds': len(amap), 'turrets': len(tmap), 'shown': out}
    print('SINICIZE', rec['sinicize'])
