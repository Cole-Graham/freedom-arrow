"""ROC specialization data (Osama 25 Nov 2026 00:5x PST, thread 1575071006240931931; details from Shawn1989 in that thread).
Runs only on branch codex/batch/shawn/roc, last in the batch (tools/pla-specs/roc_hook.py), inside g.scope('roc').
Make every new row with g.add(table, row_to_copy, fields): it takes the next free ID in the ROC block of mod/id-reservations.json.
g.put(table, max(U)+1, ...) fails here on purpose. Editing an existing live row is allowed, but list it in rec['roc']['live_edits'].

Stage 1 (25 Nov 02:1x, Shawn 02:0x "go on with the others"): spec "Joint Arms Battalion and Coastal Operations Command" (a copy of USMC, spec 3)
and one card per row of Shawn's sheet "Freedom Arrow_ROC Deck" (1uSs2Ti-ix4nVDT8-uEouP3pe-Xfqt4deouh-mLWoe38). Each card is a full copy of the
vanilla US unit in the sheet's template column, with its loadout options; it still looks and fights like that unit. Prices are the parent's, except
the infantry and M1A2T, which take Shawn's card files. Weapons, squad sizes and models come in later stages.
Left out: Hsiung Feng IIE (Shawn: "leave Hsiung Feng IIE"), CM-26 (role not known). DLC templates are replaced by non-DLC ones (review 25 Nov)."""

SPEC_TEMPLATE = 3          # USMC
# Sheet name: (HUDName, parent unit id, parent HUDName, cost or None = parent's)
CARDS = {
    # 27 new-model rows (vanilla stand-in models until the ROC models are converted)
    'ROC AH-64E': ('AH-64E Apache Guardian', 270, 'AH-64E Guardian', None),
    'ROC F-CK-1': ('F-CK-1 Ching-kuo', 285, 'F-16C Fighting Falcon', None),
    'ROC Antelope': ('Antelope', 10, 'AN/TWQ-1 Avenger', None),
    'ROC C-130HE': ('C-130HE Hercules', 302, 'C-130J-30 Hercules', None),
    'ROC Chung Hsiang II': ('Chung Hsiang II', 328, 'Forpost', None),
    'ROC CM-11': ('CM-11 Brave Tiger', 14, 'M60A1', None),
    'ROC CM-12': ('CM-12', 14, 'M60A1', None),
    'ROC CM-21': ('CM-21', 185, 'M113A3', None),
    'ROC CM-22': ('CM-22 Mortar Carrier', 189, 'M1064A3', None),
    'ROC CM-25': ('CM-25 TOW', 187, 'M901A3', None),
    'ROC CM-32': ('CM-32 Clouded Leopard', 22, 'Stryker ICV', None),
    'ROC CM-33': ('CM-33 Clouded Leopard', 22, 'Stryker ICV', None),
    'ROC CM-34': ('CM-34 Clouded Leopard IFV', 22, 'Stryker ICV', None),             # sheet: CV-9035 (DLC)
    'ROC F-5F': ('F-5F Tiger II', 285, 'F-16C Fighting Falcon', None),
    'ROC F-16V': ('F-16V Viper', 284, 'F-16V Viper', None),
    'ROC F-16A': ('F-16A Fighting Falcon', 285, 'F-16C Fighting Falcon', None),
    'ROC Kung Feng VI': ('Kung Feng VI', 92, '9K51 Grad', None),
    'ROC Land Sword II': ('Land Sword II', 389, 'SLAMRAAM', None),                     # sheet: NASAMS (DLC2)
    'ROC M41D': ('M41D Walker Bulldog', 182, 'M551A1 Sheridan', None),
    'ROC M60A3 TTS': ('M60A3 TTS', 14, 'M60A1', None),
    'ROC M110A2': ('M110A2', 422, '2S7M Malka', None),
    'ROC Mirage 2000-5': ('Mirage 2000-5', 285, 'F-16C Fighting Falcon', None),
    'ROC Thunderbolt-2000': ('Thunderbolt-2000', 376, 'M270A1 MLRS', None),
    'ROC Tien Kung III': ('Tien Kung III', 251, 'Patriot PAC-3', None),
    'ROC UH-60M': ('UH-60M Black Hawk', 81, 'UH-60M Blackhawk', None),
    # 9 reused US units
    'ROC M1167': ('M1167 HMMWV TOW', 6, 'Humvee TOW-2', None),
    'ROC JLTV': ('JLTV', 467, 'M-ATV', None),
    'ROC M1A2T': ('M1A2T Abrams', 191, 'M1A2 SEP v3', 250),
    'ROC M109A5': ('M109A5', 247, 'M109A6 Paladin', None),                            # sheet: M109A5Ö (DLC2)
    'ROC M109A7': ('M109A7 Paladin', 162, 'M109A7 Paladin', None),
    'ROC OH-58D': ('OH-58D Kiowa Warrior', 267, 'OH-58D Kiowa Warrior', None),
    'ROC CH-47SD': ('CH-47SD Chinook', 17, 'CH-47 Chinook', None),
    'ROC M142 HIMARS': ('M142 HIMARS', 11, 'M142 HIMARS', None),
    'ROC MQ-9B': ('MQ-9B SkyGuardian', 103, 'MQ-9 Reaper', None),
    # 14 infantry (parents from Shawn's card files; SF parents chosen by squad size)
    'ROC DMS Team': ('DMS Team', 69, 'Stinger team', 60),                             # card file: RBS 70 (DLC2)
    'ROC Marine AT': ('Marine AT', 62, 'Troopers AT', 90),
    'ROC Marine Frogmen CQC': ('Marine Frogmen CQC', 336, 'Force Recon CQC', 70),
    'ROC Marine Frogmen': ('Marine Frogmen', 61, 'Force Recon', 90),
    'ROC Marine': ('Marine', 62, 'Troopers AT', 80),
    'ROC Mech. Riflemen T112': ('Mech. Riflemen T112', 57, 'Mech. Riflemen', 60),
    'ROC Mech. Riflemen': ('Mech. Riflemen', 57, 'Mech. Riflemen', 50),
    'ROC Reserve Marine': ('Reserve Marine', 407, 'Reserve Marines', 45),
    'ROC Reserver': ('Reserver', 407, 'Reserve Marines', 45),
    'ROC Reserver Kestrel': ('Reserver Kestrel', 407, 'Reserve Marines', 50),
    'ROC SF Scout': ('SF Scout', 65, 'Cavalry Scouts', 90),
    'ROC SF Section': ('SF Section', 276, 'Pararescue', 100),
    'ROC SF Snipers': ('SF Snipers', 278, 'Army Snipers', 70),
    'ROC SF Snipers M107': ('SF Snipers M107', 340, 'Army Snipers', 85),
}
SPEC_NAME = 'ROC Joint Arms Coastal'
SPEC_UI = 'Joint Arms Battalion and Coastal Operations Command 聯合兵種營及濱海作戰指揮部'


def apply(t, g, ok, rec):
    U, S, SA, TA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(S[SPEC_TEMPLATE]['Name'] == 'USMC' and S[SPEC_TEMPLATE]['CountryId'] == 2, 'USMC spec template')
    spec = g.add('SpecializationsJson', S[SPEC_TEMPLATE], {'Name': SPEC_NAME, 'UIName': SPEC_UI, 'ShowInHangar': True, 'ContentMembership': -1,
        'UIDescription': 'ROC TEST. Every card is a copy of a US unit: models, weapons and stats are placeholders.'})
    ok(spec == 60, ('ROC spec id', spec))
    res, dropped, unarmed, zero = {}, [], [], []
    for name, (hud, parent, phud, cost) in CARDS.items():
        p = U[parent]
        ok(p['HUDName'].strip() == phud and p.get('ContentMembership', -1) == -1 and p.get('DisplayInArmory') is not None, (name, 'parent', parent, p['HUDName']))
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(p)
        d.update({'Name': name, 'HUDName': hud, 'Cost': p['Cost'] if cost is None else cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None,
                  'DisplayInArmory': True, 'CountryId': 2})
        uid = g.add('Units', d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'SquadMembersJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        armed = {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=parent)}
        for r in rows('SquadWeaponsJson', UnitId=parent):   # a vanilla squad-weapon row without an ammo row would make the game refuse all FA data
            if r['WeaponId'] in armed: g.add('SquadWeaponsJson', r, {'UnitId': uid})
            else: unarmed.append((name, r['Id'], r['WeaponId']))
        nopt = 0
        nmod = 0
        for m in rows('ModificationsJson', UnitId=parent):
            keep = []
            for o in rows('OptionsJson', ModificationId=m['Id']):
                if o.get('ReplaceUnitId'): dropped.append((name, o['Id'], o.get('UIName'), o['ReplaceUnitId']))   # would spawn the US swap unit
                else: keep.append(o)
            if not keep: continue
            nm = g.add('ModificationsJson', m, {'UnitId': uid}); nmod += 1
            for o in keep: g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        # A selectable turret weapon needs an ammo row on the unit (audit_mp_equipment); a vanilla parent may lack one (M1064A3 M121).
        # 0 rounds, the FA pattern for a mounted weapon that does not fire.
        tur = {r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)} | {v for m in rows('ModificationsJson', UnitId=uid)
               for o in rows('OptionsJson', ModificationId=m['Id']) for k, v in o.items() if k.startswith('Turret') and k.endswith('Id') and isinstance(v, int) and v > 0}
        have = {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)}
        wa0 = rows('WeaponAmmunitionsJson', UnitId=uid)
        for r in t['TurretWeaponsJson'].values():
            if r and r['TurretId'] in tur and r['WeaponId'] not in have and wa0:
                g.add('WeaponAmmunitionsJson', wa0[0], {'WeaponId': r['WeaponId'], 'Quantity': 0}); have.add(r['WeaponId']); zero.append((name, r['WeaponId']))
        n = max([r['MaxAvailabilityXp0'] for r in rows('SpecializationAvailabilitiesJson', UnitId=parent)] or [4])
        sa = next(r for r in rows('SpecializationAvailabilitiesJson', SpecializationId=SPEC_TEMPLATE))
        g.add('SpecializationAvailabilitiesJson', sa, {'UnitId': uid, 'SpecializationId': spec, 'MaxAvailabilityXp0': n,
              'MaxAvailabilityXp1': 0, 'MaxAvailabilityXp2': 0, 'MaxAvailabilityXp3': 0})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'SquadMembersJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        res[name] = {'unit': uid, 'hud': hud, 'parent': f'{phud} ({parent})', 'cost': U[uid]['Cost'], 'cards': n, 'options': nopt,
                     'men': len(rows('SquadMembersJson', UnitId=uid))}
    stage2 = squads(t, g, ok, res, rows)
    # Transports: every ROC infantry card may ride in every ROC ground vehicle or helicopter whose seats fit the squad.
    carriers = {r['UnitId'] for r in TA.values() if r}                            # units the game already uses as transports
    cars = [v['unit'] for v in res.values() if U[v['unit']].get('InfantrySlots', 0) > 0 and U[v['unit']]['Type'] != 2
            and int(v['parent'].rsplit('(', 1)[1][:-1]) in carriers]
    links = 0
    for v in res.values():
        if U[v['unit']]['Type'] != 2: continue
        sa = rows('SpecializationAvailabilitiesJson', UnitId=v['unit'], SpecializationId=spec)[0]
        v['transports'] = [U[c]['HUDName'] for c in cars if U[c]['InfantrySlots'] >= v['men']]
        for c in cars:
            if U[c]['InfantrySlots'] >= v['men']:
                g.add('TransportAvailabilitiesJson', next(iter(TA.values())), {'SpecializationAvailabilityId': sa['Id'], 'UnitId': c}); links += 1
    ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == spec) == sorted(v['unit'] for v in res.values()), 'ROC spec = the ROC cards')
    ok(all(v['transports'] for v in res.values() if U[v['unit']]['Type'] == 2), ('every ROC squad has a transport', [k for k, v in res.items() if U[v['unit']]['Type'] == 2 and not v['transports']]))
    rec['roc'] = {'spec': spec, 'cards': res, 'transports': [U[c]['HUDName'] for c in cars], 'transport_links': links,
                  'dropped_swap_options': dropped, 'skipped_squad_weapons_without_ammo': unarmed, 'zero_round_rows': zero, 'stage2': stage2, 'live_edits': []}
    print('ROC', len(res), 'cards; units', min(v['unit'] for v in res.values()), '-', max(v['unit'] for v in res.values()),
          '; transport links', links, '; dropped swap options', len(dropped))


# ---------- Stage 2 (25 Nov 03:3x): ROC squads from Shawn's ba-recard card files (work/roc-20261125/cards; SF Scout / SF Section from the card
# pictures; SF Snipers from the sheet). Every man carries one main gun; launchers, grenade launchers and MANPADS ride on top (vanilla pattern).
# A ROC gun with no game model of its own is a renamed copy of the closest base-game US gun (no DLC guns), so it looks and shoots like that gun.
# Shawn 25 Nov 03:3x: "Kestrel-1 is actually Taiwanese version of M72A4, can duplicate the data from M72A4" (the game has no M72A4; vanilla M72A3,
# FA name M72A7, 66 mm HEAT, base game); "T74 is Taiwan's licensed version of the Belgian FN MAG" (vanilla Ksp 58B = FN MAG, base-game model).
DONOR = {'M4A1': 50, 'T91': 50, 'T91 CQC': 67, 'T91K1': 70, 'T-112': 70, 'T65K2': 362, 'T75': 60, 'T75 SFAW': 53, 'T74': 643, 'M203': 58,
         'T85': 58, 'MGL-140': 68, 'Kestrel-1': 1019, 'M72A3 LAW': 1019, 'M72A4 LAW': 1019, 'M72A10 LAW': 212, 'APILAS': 631, 'Javelin': 62,
         'Javelin LWCLU': 659, 'DMS FIM-92K': 65, 'REPR-20': 57, 'AXMC': 640, 'M107': 56, 'M1014': 45, 'Flashbang': 590}
# name: (men, armour points, [main guns (name, men)], [extra weapons (name, men)], {weapon: rounds for the whole squad, from the card})
SQUADS = {
    'ROC DMS Team': (4, 8, [('M4A1', 4)], [('DMS FIM-92K', 1)], {'M4A1': 1800, 'DMS FIM-92K': 8}),
    'ROC Marine AT': (9, 8, [('M4A1', 6), ('T75', 3)], [('M203', 2), ('Kestrel-1', 3), ('Javelin', 1)],
                      {'M4A1': 3600, 'T75': 3600, 'M203': 96, 'Kestrel-1': 3, 'Javelin': 2}),
    # the card lists T91 CQC x6 and M1014 x2 on 6 men: as the vanilla parent, 4 rifles + 2 shotguns; the flashbang takes one LAW slot
    'ROC Marine Frogmen CQC': (6, 10, [('T91 CQC', 4), ('M1014', 2)], [('M72A10 LAW', 5), ('Flashbang', 1)],
                               {'T91 CQC': 1920, 'M1014': 80, 'M72A10 LAW': 5, 'Flashbang': 1}),
    'ROC Marine Frogmen': (6, 8, [('T91K1', 3), ('REPR-20', 2), ('M107', 1)], [('APILAS', 3)],
                           {'T91K1': 1440, 'REPR-20': 200, 'M107': 60, 'APILAS': 3}),
    'ROC Marine': (9, 8, [('M4A1', 6), ('T75', 3)], [('M203', 2), ('Kestrel-1', 6)], {'M4A1': 3600, 'T75': 3600, 'M203': 96, 'Kestrel-1': 6}),
    'ROC Mech. Riflemen T112': (6, 8, [('T-112', 4), ('T75', 1), ('T74', 1)], [('MGL-140', 1), ('Kestrel-1', 4)],
                                {'T-112': 2400, 'T75': 1200, 'T74': 1200, 'MGL-140': 120, 'Kestrel-1': 4}),
    'ROC Mech. Riflemen': (6, 8, [('T91', 4), ('T75', 2)], [('T85', 2), ('M72A4 LAW', 4)], {'T91': 2400, 'T75': 2400, 'T85': 96, 'M72A4 LAW': 4}),
    'ROC Reserve Marine': (10, 6, [('M4A1', 7), ('T74', 3)], [('M72A3 LAW', 3)], {'M4A1': 3600, 'T74': 3600, 'M72A3 LAW': 3}),
    'ROC Reserver': (9, 6, [('T65K2', 6), ('T75', 3)], [('M72A3 LAW', 3), ('T85', 3)], {'T65K2': 3600, 'T75': 3600, 'M72A3 LAW': 3, 'T85': 144}),
    'ROC Reserver Kestrel': (9, 6, [('T65K2', 6), ('T75', 3)], [('Kestrel-1', 3), ('T85', 3)], {'T65K2': 3600, 'T75': 3600, 'Kestrel-1': 3, 'T85': 144}),
    'ROC SF Scout': (3, 8, [('T91K1', 3)], [('Javelin LWCLU', 1)], {'T91K1': 1440, 'Javelin LWCLU': 3}),
    'ROC SF Section': (6, 10, [('T91 CQC', 4), ('T75 SFAW', 1), ('AXMC', 1)], [('APILAS', 4), ('M1014', 1)],
                       {'T91 CQC': 1920, 'T75 SFAW': 1200, 'AXMC': 60, 'APILAS': 4, 'M1014': 80}),
    'ROC SF Snipers': (3, 8, [('T91K1', 1), ('REPR-20', 1), ('AXMC', 1)], [], {}),
    'ROC SF Snipers M107': (3, 8, [('T91K1', 1), ('REPR-20', 1), ('M107', 1)], [], {}),
}


def squads(t, g, ok, res, rows):
    W, WA = t['WeaponsJson'], t['WeaponAmmunitionsJson']
    made, out = {}, {}

    def weapon(name):
        donor = DONOR[name]
        if name not in made:
            made[name] = donor if W[donor]['HUDName'].strip() == name else g.add('WeaponsJson', W[donor], {'Name': 'ROC ' + name, 'HUDName': name})
        return made[name], donor
    for card, (men, armour, mains, extras, rounds) in SQUADS.items():
        uid = res[card]['unit']
        ok(sum(n for _, n in mains) == men and all(n <= men for _, n in extras) and sum(n for _, n in extras) <= men, (card, 'men vs weapons'))
        tmpl = rows('SquadMembersJson', UnitId=uid)[0]
        for tab in ('SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=uid): g.remove(tab, r['Id'])
        members = [{**tmpl, 'UnitId': uid, 'PrimaryWeaponId': 0, 'SpecialWeaponId': 0} for _ in range(men)]
        i = 0
        for name, n in mains:
            for m in members[i:i + n]: m['PrimaryWeaponId'] = weapon(name)[0]
            i += n
        i = 0
        for name, n in extras:
            for m in members[i:i + n]: m['SpecialWeaponId'] = weapon(name)[0]
            i += n
        for m in members: m.pop('Id', None); g.add('SquadMembersJson', m)
        sw = next(iter(t['SquadWeaponsJson'].values()))
        for order, (name, n) in enumerate(mains + extras):
            wid, donor = weapon(name)
            g.add('SquadWeaponsJson', sw, {'UnitId': uid, 'WeaponId': wid, 'Order': order})
            src = min(r['UnitId'] for r in WA.values() if r and r['WeaponId'] == donor)      # the donor gun's own ammo rows, as the PLA designer
            for r in sorted(rows('WeaponAmmunitionsJson', UnitId=src, WeaponId=donor), key=lambda r: (r['Order'], r['Id'])):
                q = max(1, round(rounds[name] / n)) if name in rounds else r['Quantity']
                g.add('WeaponAmmunitionsJson', r, {'UnitId': uid, 'WeaponId': wid, 'Quantity': q})
        for ua in rows('UnitArmorsJson', UnitId=uid):
            g.put('ArmorsJson', ua['ArmorId'], {'MaxHealthPoints': men * 5, 'ArmorValue': armour})
        res[card]['men'] = men
        out[card] = {'men': men, 'hp': men * 5, 'armour': armour, 'weapons': [f'{x} x{n}' for x, n in mains + extras]}
    return {'squads': out, 'weapons': {k: v for k, v in made.items()}}
