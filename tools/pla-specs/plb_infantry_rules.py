"""PLA Light Brigade Models test build: infantry body and weapon model rules (Osama 26 Nov 2026 04:1x PST, thread 1567745029781454889: "Please make
sure the new units have PLA skins and equipment visually"; 04:3x "can you build it with the new voice lines?"). Branch
codex/batch/osama/pla-light-brigade only.
- Bodies: the new squads (unit IDs 6000-6999, FAModels 0.3.49-plb.1 approves that block) get add-on rules in infantry-bodies-plb.json, each a copy of
  the squad it was made from (Sky Wolf Commandos <- Sea Dragons 1191, Tiger Brigade <- Marines 1192, Marine Scouts <- Marine Recon 1224, PAP AA
  Patrol <- Moto. Riflemen 1196). The pinned infantry-bodies.json does not change.
- Weapons (infantry-weapons.json): the new squads take the weapon rules of their source squad. Then every China infantry squad that has a body rule
  gets a rule for each weapon it carries that has none, copied from a rule for the same weapon (or its stand-in below) on another squad:
  QJY-88 -> the QJY-201 model, VQX191 / QBZ URGI -> the QBZ-192, squad QLZ-87 -> the QLU-11 (Osama: "uses the QLU-11 model for now"), long-range
  PF-98 -> the PF-98. Weapons with no PLA model (SIG 516, SPAS-12, ARWEN 37) keep the game's own model.
usage: python plb_infantry_rules.py CONSTANTS_DIR VANILLA_DIR SRC_DIR OUT_DIR   (SRC_DIR: infantry-bodies.json + infantry-weapons.json of Assets 0.2.104)"""
import json, sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parents[2] / 'mod')]
from pipeline.tables import FIELD_TO_FILE

C, V, SRC, OUT = map(Path, sys.argv[1:5])
t = {}
for tab, fn in FIELD_TO_FILE.items():
    t[tab] = {r['Id']: r for r in json.loads((V / (tab + '.json')).read_text())}
    for k, v in json.loads((C / fn).read_text()).items():
        if v is None: t[tab].pop(int(k), None)
        else: t[tab].setdefault(int(k), {'Id': int(k)}).update(v)
U, W, SM = t['Units'], t['WeaponsJson'], t['SquadMembersJson']
bodies, weapons = json.loads((SRC / 'infantry-bodies.json').read_text()), json.loads((SRC / 'infantry-weapons.json').read_text())
name = lambda u: U[u]['Name']
NEW = {'PLA Sky Wolf Commandos': 1191, 'PLA Tiger Brigade': 1192, 'PLA Marine Scouts': 1224, 'PLA PAP AA Patrol': 1196}
new = {next(i for i, u in U.items() if u and u.get('Name') == n): src for n, src in NEW.items()}
assert all(6000 <= i <= 6999 for i in new), new
add = []
for uid, src in new.items():
    (b,) = [r for r in bodies if r['unitId'] == src]; add.append({**b, 'unitId': uid})
    weapons += [{**r, 'unitId': uid} for r in weapons if r['unitId'] == src]
by_w = lambda wid, slot: next((r for r in weapons if r['weaponId'] == wid and r['slot'] == slot), None) or next((r for r in weapons if r['weaponId'] == wid), None)
hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
qjy88, = [i for i in hud('QJY-88') if 'infantry' in W[i]['Name']]
stand_in = {qjy88: 2012411, 3000000: 2013087}   # QJY-88 -> QJY-201 model, QBZ URGI (first plb weapon) -> QBZ-192
stand_in.update({i: 2013087 for i in hud('VQX191')})
stand_in.update({i: 2004002 for i, w in W.items() if w and w.get('Name') == 'PLA infantry QLZ-87 squad (QLU-11 model)'})
stand_in.update({i: 2011832 for i, w in W.items() if w and w.get('Name') == 'PLA infantry PF-98 long range'})
assert W[3000000]['HUDName'] == 'QBZ URGI' and len(stand_in) == 5, stand_in
body_units = {r['unitId'] for r in bodies} | set(new)
filled, novis = [], set()
for uid in sorted(body_units):
    if uid not in U or not U[uid]: continue
    have = {(r['weaponId'], r['slot']) for r in weapons if r['unitId'] == uid}
    for m in [r for r in SM.values() if r and r.get('UnitId') == uid]:
        for f, slot in (('PrimaryWeaponId', 'primary'), ('SpecialWeaponId', 'special')):
            wid = m.get(f)
            if not wid or (wid, slot) in have: continue
            d = by_w(wid, slot) or (by_w(stand_in[wid], slot) if wid in stand_in else None)
            if not d: novis.add(W[wid]['HUDName']); continue
            weapons.append({**d, 'unitId': uid, 'weaponId': wid, 'slot': slot, 'soldierIndex': -1}); have.add((wid, slot)); filled.append((U[uid]['HUDName'], W[wid]['HUDName'], slot, d['file']))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'infantry-bodies-plb.json').write_text(json.dumps(add, indent=2) + '\n')
(OUT / 'infantry-weapons.json').write_text(json.dumps(weapons, indent=2) + '\n')
print('bodies', [(U[r['unitId']]['HUDName'], r['lods'][0]) for r in add])
print('weapon rules', len(weapons), 'filled', len(filled)); [print('  ', x) for x in filled]
print('no PLA model (game model kept):', sorted(novis))
