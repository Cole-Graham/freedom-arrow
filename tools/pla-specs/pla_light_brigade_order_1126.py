"""PLA Light Brigade build, weapon list order and casualty order of the re-kitted squads (Osama 26 Nov 2026 10:4x PST, thread 1567745029781454889: "can
you reorder these weapons so that the'yre consistent with vanilla? It should be rifle, then smg, then shotgun, then lmg, then launcher. Also make sure
the death priority is consistent?", with the Sea Dragons card: QCQ-05, QBS-09, PF-97, QBZ URGI, QJS-161). Branch codex/batch/osama/pla-light-brigade
only; the last plb section. Rules: docs/engine/infantry-casualty-and-weapon-order.md (vanilla pattern, read from data; 22 Nov), with Osama's order.
- SquadWeapons.Order (Arsenal card and HUD list only): rifle -> SMG -> shotgun -> MG -> marksman -> grenade launcher -> AGL -> sniper -> reloadable RPG ->
  disposable launcher -> MANPADS -> anything else (by Weapons.Type: 1/5, 25, 40, 26/30, 2/3, 60, 61, 4, 62, 63, 85).
- SquadMembers.DeathPriority (highest dies first, ties random): one keeper at 1 = the squad's top specialist (reloadable RPG > MANPADS > sniper > AGL, the
  vanilla order; with none, the leader with a disposable launcher, else the current 1); 2 = other specialists, MGs, shotguns, SMGs, marksmen, grenade
  launchers; 3 = riflemen with a disposable launcher; riflemen with nothing else 3 in squads of up to 6, 4 in larger squads (vanilla ranges).
- Squads: those this branch re-kitted or created: Sea Dragons, Flying Tigers, Sky Wolf Commandos, Tiger Brigade, Marine Scouts, PAP AA Patrol,
  Falcons, Taishan Eagles, Airborne, QLU-11 Team, Mountaineers. Weapons, counts and prices do not change."""
SQUADS = ['Sea Dragons 蛟龙', 'Flying Tigers', 'Sky Wolf Commandos 天狼突击队', 'Tiger Brigade 猛虎旅', 'Marine Scouts', 'PAP AA Patrol', 'Falcons 猎鹰',
          'Taishan Eagles 泰山雄鹰', 'Airborne 空降兵', 'QLU-11 Team', 'Mountaineers 高寒山地特战分队']
LIST = [(1, 5), (25,), (40,), (26, 30), (2, 3), (60,), (61,), (4,), (62,), (63,), (85,)]
KEEP = [62, 85, 4, 61]          # keeper class, best first (no ATGM in these squads)


def apply(t, g, ok, rec):
    U, W = t['Units'], t['WeaponsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    typ = lambda w: W[w]['Type'] if w else None
    rank = lambda w: next((i for i, ts in enumerate(LIST) if typ(w) in ts), len(LIST))
    out = {}
    for name in SQUADS:
        (uid,) = [i for i, u in U.items() if u and u.get('HUDName') == name and rows('SquadMembersJson', UnitId=i)][:1] or [None]
        ok(uid, ('squad', name))
        sw = rows('SquadWeaponsJson', UnitId=uid)
        for n, r in enumerate(sorted(sw, key=lambda r: (rank(r['WeaponId']), W[r['WeaponId']]['HUDName'], r['Id'])), 1):
            if r.get('Order') != n: g.put('SquadWeaponsJson', r['Id'], {'Order': n})
        men = rows('SquadMembersJson', UnitId=uid); big = len(men) > 6
        kinds = lambda m: {typ(m['PrimaryWeaponId']), typ(m.get('SpecialWeaponId'))} - {None}
        keeper = next((m for k in KEEP for m in men if k in kinds(m)), None) or next((m for m in men if 63 in kinds(m) and m.get('DeathPriority') == 1), None) \
            or next((m for m in men if 63 in kinds(m)), None) or next((m for m in men if m.get('DeathPriority') == 1), men[0])
        for m in men:
            k = kinds(m)
            if m is keeper: v = 1
            elif k & {62, 85, 4, 61, 26, 30, 40, 25, 2, 3, 60}: v = 2
            elif 63 in k: v = 3
            else: v = 4 if big else 3
            if m.get('DeathPriority') != v: g.put('SquadMembersJson', m['Id'], {'DeathPriority': v})
        men = rows('SquadMembersJson', UnitId=uid)
        ok(sum(m['DeathPriority'] == 1 for m in men) == 1, (name, 'one keeper'))
        ok(sorted(r['Order'] for r in rows('SquadWeaponsJson', UnitId=uid)) == list(range(1, len(sw) + 1)), (name, 'Order 1..n'))
        out[name] = {'list': [W[r['WeaponId']]['HUDName'] for r in sorted(rows('SquadWeaponsJson', UnitId=uid), key=lambda r: r['Order'])],
                     'death': sorted(((m['DeathPriority'], W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '')) for m in men))}
    rec['pla_light_brigade_order_1126'] = out
    for k, v in out.items(): print('ORDER', k, v['list'], v['death'])
