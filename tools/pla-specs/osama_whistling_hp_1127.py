"""Osama 27 Nov 2026 21:2x PST, thread 1567745029781454889: "whistling arrows 4 hp". Whistling Arrows 响箭 (1184, 3 men) health 5 -> 4 per man:
squad pool 15 -> 12 (health per soldier = Armors.MaxHealthPoints / men, docs/engine/damage-falloff.md). Armour stays 8. The armour link moves to
an existing row equal to vanilla 279 "Armor Infantry Shock 3Men" except MaxHealthPoints 12 (ability-row-reuse rule); only when none exists is a
copy of 279 added. Every unit row named Whistling Arrows (copies in other specs) gets the same change. Adds a row, so it runs before the plb scope."""


def apply(t, g, ok, rec):
    U, UA, AR = t['Units'], t['UnitArmorsJson'], t['ArmorsJson']
    ids = [k for k, u in U.items() if u and (u.get('HUDName') or '').strip().startswith('Whistling Arrows')]
    ok(1184 in ids, ('Whistling Arrows units', ids))
    base = AR[279];ign = {'Id', 'Name', 'MaxHealthPoints'}
    same = lambda a: all(a.get(k) == base.get(k) for k in set(a) | set(base) if k not in ign)
    hit = [k for k, a in AR.items() if a and same(a) and a.get('MaxHealthPoints') == 12]
    row = hit[0] if hit else g.add('ArmorsJson', base, {'Name': 'Armor Infantry Shock 3Men 4HP', 'MaxHealthPoints': 12})
    done = {}
    for uid in ids:
        links = [k for k, l in UA.items() if l and l.get('UnitId') == uid]
        ok(len(links) == 1, (uid, 'one armour link', links))
        a = AR[UA[links[0]]['ArmorId']]
        ok(a['ArmorValue'] == 8 and a['MaxHealthPoints'] == 15, (uid, 'armour 8 / 15 before', a['ArmorValue'], a['MaxHealthPoints']))
        done[uid] = [UA[links[0]]['ArmorId'], row]
        g.put('UnitArmorsJson', links[0], {'ArmorId': row})
    rec['osama_whistling_hp_1127'] = {'units': done, 'hp_per_man': [5, 4], 'pool': [15, 12], 'row_reused': bool(hit)}
    print('WHISTLING ARROWS HP', rec['osama_whistling_hp_1127'])
