"""Chinese bug sheet FA-067..FA-090 answers (Osama 23 Nov 2026 23:2x PST, bugs thread 1573561286803980289):
- FA-084 "Reservists should be shooting at very low damage, but it should be changed to the QBZ-95 in the new version and we'll call it 5.8":
  the Reservists' rifle round 2019304 (only used by the ex-QBZ-03, shown as QBZ-95 since qbz95_qjz89_1123.py) is already named '5.8 mm ammunition'
  in this batch (0.9.5b live still shows 5.45x39mm); checked here only. Stats unchanged (0.36 damage, kept low on purpose).
- FA-085 "Z-20T ... should both have seats, so lets give it seats": Z-20T (1245) InfantrySlots 0 -> 8, like the armed Black Hawk MH-60M DAP and
  the Mi-24 family (8 each). It stays an attack helicopter, not a transport option on infantry cards (as those vanilla units).
- FA-081 "we should reduce the overpressure range to somewhere more normal with large missiles (let's take JAGM for example)": HJ-10 NLOS round
  2009623 OverpressureRadius 5.0 -> 0.0, the JAGM / Hellfire value. Overpressure > 0 also forces roof armour on a direct hit
  (docs: overpressure-direct-hit), so this ends top-armour hits from the HJ-10.
- FA-082 "FB-10 should be IIR which is fnf": PGL-625 FB-10 round 2009373 Seeker 100 (semi-active) -> 10, the vanilla IR fire-and-forget seeker
  of the Stinger / Igla / Mistral rows. Seeker angle and distance unchanged."""
RESERVIST_AMMO, QBZ95_AMMO_NAME, Z20T, HJ10, FB10 = 2019304, '5.8 mm ammunition', 1245, 2009623, 2009373


def apply(t, g, ok, rec):
    U, A, W, WA = t['Units'], t['AmmunitionsJson'], t['WeaponsJson'], t['WeaponAmmunitionsJson']
    users = {W[r['WeaponId']]['Name'] for r in WA.values() if r and r['AmmunitionId'] == RESERVIST_AMMO}
    # Already renamed to '5.8 mm ammunition' earlier in this batch (found 23 Nov 23:3x); only checked here.
    ok(A[RESERVIST_AMMO]['HUDName'] == QBZ95_AMMO_NAME and A[RESERVIST_AMMO]['Damage'] == 0.36 and users == {'PLA infantry QBZ-03'}, ('Reservist rifle round', A[RESERVIST_AMMO]['HUDName'], users))
    ok(any(a and a.get('HUDName') == QBZ95_AMMO_NAME for a in A.values()), 'QBZ-95 round name exists')
    ok(U[Z20T]['HUDName'] == 'Z-20T' and U[Z20T]['InfantrySlots'] == 0 and U[272]['InfantrySlots'] == 8, 'Z-20T seats before, MH-60M DAP 8')
    ok(A[HJ10]['HUDName'] == 'HJ-10 NLOS' and A[HJ10]['OverpressureRadius'] == 5.0 and A[456]['OverpressureRadius'] == 0.0, 'HJ-10 OP 5, JAGM 0')
    ok(A[FB10]['HUDName'] == 'FB-10 ammunition' and A[FB10]['Seeker'] == 100 and A[18]['Seeker'] == 10, 'FB-10 semi-active, Stinger IR')
    g.put('Units', Z20T, {'InfantrySlots': 8})
    g.put('AmmunitionsJson', HJ10, {'OverpressureRadius': 0.0})
    g.put('AmmunitionsJson', FB10, {'Seeker': 10})
    ok(A[RESERVIST_AMMO]['HUDName'] == QBZ95_AMMO_NAME and A[RESERVIST_AMMO]['Damage'] == 0.36 and U[Z20T]['InfantrySlots'] == 8
       and A[HJ10]['OverpressureRadius'] == 0.0 and A[FB10]['Seeker'] == 10, 'after')
    rec['qq_sheet_fixes_1123'] = {'reservist_round_already': [RESERVIST_AMMO, QBZ95_AMMO_NAME], 'z20t_seats': [0, 8],
                                  'hj10_overpressure': [5.0, 0.0], 'fb10_seeker': [100, 10]}
