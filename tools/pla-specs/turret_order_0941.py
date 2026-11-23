"""Turret weapon Order <= weapon count (Osama 22 Nov 2026 03:2x PST, thread 1567745029781454889: "Fix and test all of these issues until you've
got it all working", after the 0.9.5-dev.19 checklist run logged 10 NullReferenceExceptions in RefundSystem.GetAmmoResupplyTime on the ZTZ-99A
and ZTZ-99 Arsenal cards). LoadUnits.LoadWeapons puts (Order - weapon rows on the turret) empty slots before a weapon, so a turret whose only
weapon has Order 2 gets [empty, weapon]; the card's purchase-time stat (AddTurretWeaponsAmmoTime) then reads the empty slot and throws, and the
stat is missing. Battles were not affected. Vanilla has no turret with an Order above its row count; the FA rows had 30, all the model-less
12.7 mm "mount 1" pattern [2] with one row, on 35 China units. Order 2 -> 1 (the highest Order the game accepts with one row). See
child-turret-weapon-order notes. Called from batch_0_9_5b.py."""
import collections


def apply(t, g, ok, rec):
    TW = t['TurretWeaponsJson']
    rows = collections.defaultdict(list)
    for r in TW.values():
        if r:rows[r['TurretId']].append(r)
    bad = {k: rs for k, rs in rows.items() if any(r['Order'] > len(rs) for r in rs)}
    ok(all(len(rs) == 1 and rs[0]['Order'] == 2 for rs in bad.values()) and 20 <= len(bad) <= 40,
       ('turrets with Order above their weapon count: all [2] with one row', len(bad)))
    changed = []
    for k, rs in sorted(bad.items()):
        g.put('TurretWeaponsJson', rs[0]['Id'], {'Order': len(rs)})
        changed.append(k)
    after = collections.defaultdict(list)
    for r in TW.values():
        if r:after[r['TurretId']].append(r['Order'])
    ok(not [k for k, o in after.items() if max(o) > len(o)], 'no turret has a weapon Order above its weapon count')
    rec['turret_order_fix'] = {'turrets': changed, 'order': '2 -> 1'}
