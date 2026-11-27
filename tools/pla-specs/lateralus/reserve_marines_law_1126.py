"""Reserve Marines (407): M72A7 LAW ammunition 5 -> 8 (Lateralus 26 Nov 2026 17:0x PST, thread 1572962048705429598, "queue it up").
The LAW is a disposable launcher (Weapons.Type 63): one round per carrier, more rounds = more carriers (Lateralus 23 Nov; disposable_launchers_1123
fails on Quantity > 1). So three riflemen who carry only an M16A4 also carry a LAW: 5 -> 8 carriers, head count and rifles unchanged.
Chosen by death priority, lowest first (they die last): 780 (3), 772 (4), 777 (4).
Squad rate (SquadReload.cs, 12.16 x carriers^(1/3) per minute): 8 carriers -> 24.32/min, reload 60 x 8 / 24.32 = 19.737 s. The 407:1019 entry of
squad-reload.json said 5 carriers (20.793/min, 14.428 s): with 8 carriers and the old reload the squad would fire 33.3/min. reload_entry() is the
new entry; the batch writes the table with only this entry changed. Existing rows only: no ID moves."""

RESERVE_MARINES, LAW, WA_ROW = 407, 1019, 4110
NEW_CARRIERS = (780, 772, 777)


def apply(t, g, ok, rec):
    U, W, SM, WA = t['Units'], t['WeaponsJson'], t['SquadMembersJson'], t['WeaponAmmunitionsJson']
    ok(U[RESERVE_MARINES]['HUDName'].strip() == 'Reserve Marines' and W[LAW]['HUDName'] == 'M72A7 LAW' and W[LAW]['Type'] == 63, 'Reserve Marines LAW rows')
    members = [m for m in SM.values() if m and m['UnitId'] == RESERVE_MARINES]
    carriers = lambda: sum(1 for m in members if LAW in (m.get('PrimaryWeaponId'), m.get('SpecialWeaponId')))
    ok(carriers() == 5 and WA[WA_ROW]['UnitId'] == RESERVE_MARINES and WA[WA_ROW]['WeaponId'] == LAW and WA[WA_ROW]['Quantity'] == 1, ('LAW before', carriers(), WA[WA_ROW]))
    ok(any(r and r['UnitId'] == RESERVE_MARINES and r['WeaponId'] == LAW for r in t['SquadWeaponsJson'].values()), 'LAW squad weapon row')
    for mid in NEW_CARRIERS:
        m = SM[mid]
        ok(m['UnitId'] == RESERVE_MARINES and m['PrimaryWeaponId'] == 362 and not m.get('SpecialWeaponId'), ('rifleman only', mid, m))
        g.put('SquadMembersJson', mid, {'SpecialWeaponId': LAW})
    ok(carriers() == 8 and len(members) == 13, ('LAW after', carriers(), len(members)))
    rec['reserve_marines_law_1126'] = {'carriers': '5 -> 8', 'ammo': '5 -> 8', 'members': list(NEW_CARRIERS), 'squad_reload': reload_entry()}
    print('RESERVE MARINES LAW', rec['reserve_marines_law_1126'])


def reload_entry(k=12.16, exponent=0.3333333333, n=8):
    rate = k * n ** exponent
    return {'carriers': n, 'rate': round(rate, 3), 'reload': round(60 * n / rate, 3)}
