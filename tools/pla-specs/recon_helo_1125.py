"""Recon utility helicopters (Lateralus 25 Nov 2026 18:0x PST, thread 1568104480459722894: "Give the Z-20S 4 seats / Increase MH-60M SOAR Recon
price 60 -> 65"). Z-20S (1243) InfantrySlots 0 -> 4, the same as the vanilla recon utility helicopters (UH-1Y Venom Recon, MH-60M SOAR Recon,
MH-6 Recon, Ka-60 / Ka-226T / Ka-29 / Mi-8AMTSh Razvedchik). Like them it gets no transport-availability row: seats only. MH-60M SOAR Recon (735)
base Cost 60 -> 65; its gun options (M240 +0, 2x GAU-17 +5, 2x GAU-21 +10) are unchanged. Neither card has swap-unit rows."""
Z20S, SOAR = 1243, 735


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[Z20S]['HUDName'] == 'Z-20S' and (U[Z20S].get('InfantrySlots') or 0) == 0, ('Z-20S 0 seats', U[Z20S].get('InfantrySlots')))
    ok(U[SOAR]['HUDName'] == 'MH-60M SOAR Recon' and U[SOAR]['Cost'] == 60 and not U[SOAR].get('OriginalCost'), ('SOAR Recon 60 pts', U[SOAR]['Cost']))
    swaps = [u['Id'] for u in U.values() if u and u['Id'] not in (Z20S, SOAR) and u['HUDName'] in ('Z-20S', 'MH-60M SOAR Recon')]
    ok(not swaps, ('recon helo swap rows', swaps))
    g.put('Units', Z20S, {'InfantrySlots': 4})
    g.put('Units', SOAR, {'Cost': 65})
    rec['recon_helo_1125'] = {'z20s_seats': [0, 4], 'soar_recon_cost': [60, 65]}
    print('RECON HELO', rec['recon_helo_1125'])
