"""Osama 27 Nov 2026 21:2x-23:0x PST, thread 1567745029781454889: "whistling arrows 4 hp", then "whistling arrows 95 pts" / "and 4 man total".
Whistling Arrows 响箭 (1184): 3 -> 4 men (the 4th is a copy of the plain QBZ-192 rifleman, death priority 3; the man removed on 20 Nov was a QBU-10
marksman) and 5 -> 4 HP per man: squad pool 15 -> 16 (health per soldier = Armors.MaxHealthPoints / men, docs/engine/damage-falloff.md). Armour
stays 8. The armour link moves to an existing row equal to vanilla 279 except MaxHealthPoints 16 (ability-row-reuse rule); only when none exists is
a copy added. Price: osama_whistling_price_1127. Adds rows, so it runs before the plb scope."""


def apply(t, g, ok, rec):
    U, UA, AR, W = t['Units'], t['UnitArmorsJson'], t['ArmorsJson'], t['WeaponsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ids = [k for k, u in U.items() if u and (u.get('HUDName') or '').strip().startswith('Whistling Arrows')]
    ok(ids == [1184], ('Whistling Arrows units', ids))
    men = rows('SquadMembersJson', UnitId=1184)
    plain = [m for m in men if W[m['PrimaryWeaponId']]['HUDName'] == 'QBZ-192' and not m.get('SpecialWeaponId')]
    ok(len(men) == 3 and len(plain) == 1, ('3 men, one plain QBZ-192 rifleman', len(men)))
    g.add('SquadMembersJson', plain[0], {})
    base = AR[279]; ign = {'Id', 'Name', 'MaxHealthPoints'}
    same = lambda a: all(a.get(k) == base.get(k) for k in set(a) | set(base) if k not in ign)
    hit = [k for k, a in AR.items() if a and same(a) and a.get('MaxHealthPoints') == 16]
    row = hit[0] if hit else g.add('ArmorsJson', base, {'Name': 'Armor Infantry Shock 4Men 4HP', 'MaxHealthPoints': 16})
    (link,) = rows('UnitArmorsJson', UnitId=1184)
    a = AR[link['ArmorId']]
    ok(a['ArmorValue'] == 8 and a['MaxHealthPoints'] == 15, ('armour 8 / 15 before', a['ArmorValue'], a['MaxHealthPoints']))
    old = link['ArmorId']; g.put('UnitArmorsJson', link['Id'], {'ArmorId': row})
    kit = sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=1184))
    ok(len(kit) == 4 and kit.count('QBZ-192') == 2, ('kit after', kit))
    rec['osama_whistling_hp_1127'] = {'men': [3, 4], 'hp_per_man': [5, 4], 'pool': [15, 16], 'armor_row': [old, row], 'row_reused': bool(hit), 'kit': kit}
    print('WHISTLING ARROWS', rec['osama_whistling_hp_1127'])
