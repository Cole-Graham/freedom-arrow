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
                  'dropped_swap_options': dropped, 'skipped_squad_weapons_without_ammo': unarmed, 'zero_round_rows': zero, 'live_edits': []}
    print('ROC', len(res), 'cards; units', min(v['unit'] for v in res.values()), '-', max(v['unit'] for v in res.values()),
          '; transport links', links, '; dropped swap options', len(dropped))
