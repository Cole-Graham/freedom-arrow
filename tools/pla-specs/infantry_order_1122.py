"""China infantry casualty order and weapon list order (Lateralus 22 Nov 2026 16:4x PST, thread 1572962048705429598: "queue both").
Mechanism and rules: docs/engine/infantry-casualty-and-weapon-order.md. Data: docs/engine/infantry-order/*_proposal.json (made over the 0.9.5-dev.33
constants, 657d31e1). SquadMembers.DeathPriority: the alive soldier with the HIGHEST value dies first (KillSquadSolders 0x40CFF0), ties random; the
proposal gives each squad one keeper at 1 (vanilla specialist pattern), other specialists next, grenadiers / disposable-AT riflemen next, plain
riflemen last (highest). SquadWeapons.Order: Arsenal card and HUD weapon list order only (it does not change which weapon fires). China rows only;
every row is checked against the value the proposal was made from, so a squad edited after dev.33 stops the build instead of taking a stale value.
Uncertain choices: the Google Sheet in the BA Reports folder (see the 0.9.5 NOTES). Called from apply_0_9_4_dev1.py."""
import json
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / 'docs/engine/infantry-order'


def apply(t, g, ok, rec):
    SM, SW, U = t['SquadMembersJson'], t['SquadWeaponsJson'], t['Units']
    dp = json.loads((DOC / 'death_priority_proposal.json').read_text())
    wo = json.loads((DOC / 'weapon_order_proposal.json').read_text())
    n = 0
    for u in dp['units']:
        ok(U.get(u['unit_id']) and U[u['unit_id']]['Name'].startswith('PLA'), ('DeathPriority unit is a China unit', u['unit_id']))
        for r in u['rows']:
            m = SM.get(r['squad_members_row_id'])
            ok(m and m['UnitId'] == u['unit_id'] and m.get('DeathPriority') == r['current'],
               ('SquadMembers row as proposed over dev.33', r['squad_members_row_id'], m and m.get('DeathPriority'), r['current']))
            if r['changes']:g.put('SquadMembersJson', m['Id'], {'DeathPriority': r['proposed']});n += 1
    ok(n == len(dp['apply_as_squad_members_overrides']) == 498, ('DeathPriority rows changed', n))
    k = 0
    for u in wo['units']:
        ok(U.get(u['unit_id']) and U[u['unit_id']]['Name'].startswith('PLA'), ('Order unit is a China unit', u['unit_id']))
        for r in u['rows']:
            s = SW.get(r['squad_weapons_row_id'])
            ok(s and s['UnitId'] == u['unit_id'] and s['WeaponId'] == r['weapon_id'] and s.get('Order') == r['current_order'],
               ('SquadWeapons row as proposed over dev.33', r['squad_weapons_row_id'], s and s.get('Order'), r['current_order']))
            if r['changes']:g.put('SquadWeaponsJson', s['Id'], {'Order': r['proposed_order']});k += 1
        orders = sorted(SW[r['squad_weapons_row_id']]['Order'] for r in u['rows'])
        ok(orders == list(range(1, len(orders) + 1)), ('Order is 1..n per unit', u['unit_id'], orders))
    ok(k == len(wo['apply_as_squad_weapons_overrides']) == 452, ('SquadWeapons Order rows changed', k))
    rec['infantry_order'] = {'death_priority_rows': n, 'weapon_order_rows': k, 'units': len(dp['units'])}
