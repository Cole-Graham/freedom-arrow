"""PLA Light Brigade build, machine guns (Osama 26 Nov 2026 01:2x PST, thread 1567745029781454889: "I want to make a separate build for
splitting China with SOF with the new MG, the QJY-88 ... this is the new basic GPMG. The QJY-201 becomes the new shock MG. I want you to replace the
current QJY-201 with the QJY-88, and then we make the QJY-201 the shock GPMG that is identical to the VDV brigade's PKP-M"; "We'll call this PLA
Light brigade"). Branch codex/batch/osama/pla-light-brigade only.
- Every infantry QJY-201 gunner (weapon 2012411, 25 men in 17 squads) -> the QJY-88 (backpocket_weapons_1125.py: PKM T1 copy, own round
  '7.62 mm ammunition'). Each squad's card row and ammo row follow, with the same round count (400).
- The QJY-201 (2012411) and its round (2012412) become exact stat copies of the VDV PKP-M (weapon 125 'MMG 7.62 PKPM T2', round 362 '7.62x54mm').
  Name, HUD name, icon and 3D model stay the QJY-201's. No squad carries it after this section; shock / SOF squads get it when Osama names them.
- Vehicle and helicopter QJY-201 mounts (2009261, 2011045, 2011625) are separate weapons and do not change."""
QJY201, QJY201_AMMO, PKPM, PKPM_AMMO = 2012411, 2012412, 125, 362
KEEP_W = ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName')
KEEP_A = ('Id', 'Name', 'HUDName')


def apply(t, g, ok, rec):
    U, W, A, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    live = lambda tab: [r for r in t[tab].values() if r]
    q88 = rec['backpocket_weapons_1125']['QJY-88']; QJY88, QJY88_AMMO = q88['weapon'], q88['ammo']
    ok(W[QJY201]['HUDName'] == 'QJY-201' and A[QJY201_AMMO]['HUDName'] == '7.62 mm ammunition', 'infantry QJY-201 + round')
    ok(W[PKPM]['HUDName'] == 'PKP-M' and A[PKPM_AMMO]['HUDName'] == '7.62x54mm', 'VDV PKP-M + round')
    ok(W[QJY88]['HUDName'] == 'QJY-88', 'QJY-88 from the back-pocket section')
    # the QJY-201 round is fired only by the infantry QJY-201, so changing it touches nothing else
    ok({r['WeaponId'] for r in live('WeaponAmmunitionsJson') if r['AmmunitionId'] == QJY201_AMMO} == {QJY201}, 'round 2012412 only on the QJY-201')
    men = [r for r in live('SquadMembersJson') if QJY201 in (r['PrimaryWeaponId'], r['SpecialWeaponId'])]
    units = sorted({r['UnitId'] for r in men})
    for r in men:
        g.put('SquadMembersJson', r['Id'], {f: QJY88 for f in ('PrimaryWeaponId', 'SpecialWeaponId') if r[f] == QJY201})
    for r in live('SquadWeaponsJson'):
        if r['WeaponId'] == QJY201 and r['UnitId'] in units: g.put('SquadWeaponsJson', r['Id'], {'WeaponId': QJY88})
    for r in live('WeaponAmmunitionsJson'):
        if r['WeaponId'] == QJY201 and r['UnitId'] in units:
            ok(r['AmmunitionId'] == QJY201_AMMO, ('QJY-201 ammo row', r['Id'], r['AmmunitionId']))
            g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': QJY88, 'AmmunitionId': QJY88_AMMO})
    g.put('WeaponsJson', QJY201, {k: v for k, v in W[PKPM].items() if k not in KEEP_W})
    g.put('AmmunitionsJson', QJY201_AMMO, {k: v for k, v in A[PKPM_AMMO].items() if k not in KEEP_A})
    # checks after
    ok(not [r for r in live('SquadMembersJson') if QJY201 in (r['PrimaryWeaponId'], r['SpecialWeaponId'])], 'no squad member carries the QJY-201')
    ok(not [r for r in live('SquadWeaponsJson') if r['WeaponId'] == QJY201] and not [r for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == QJY201],
       'no card or ammo row left on the QJY-201')
    for u in units:
        carried = {w for r in live('SquadMembersJson') if r['UnitId'] == u for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
        ok({r['WeaponId'] for r in live('SquadWeaponsJson') if r['UnitId'] == u} == carried == {r['WeaponId'] for r in live('WeaponAmmunitionsJson') if r['UnitId'] == u},
           ('card + ammo = carried weapons', U[u]['HUDName']))
    same = lambda x, y, skip: all(x.get(k) == y[k] for k in y if k not in skip)
    ok(same(W[QJY201], W[PKPM], KEEP_W) and same(A[QJY201_AMMO], A[PKPM_AMMO], KEEP_A), 'QJY-201 = PKP-M stats')
    ok(W[QJY201]['HUDName'] == 'QJY-201' and A[QJY201_AMMO]['HUDName'] == '7.62 mm ammunition', 'QJY-201 keeps its names')
    rec['pla_light_brigade_mg_1126'] = {'qjy88': QJY88, 'qjy88_ammo': QJY88_AMMO, 'gunners': len(men),
                                         'squads': {U[u]['HUDName']: sum(1 for r in men if r['UnitId'] == u) for u in units}}
    print('PLA LIGHT BRIGADE MG', rec['pla_light_brigade_mg_1126'])
