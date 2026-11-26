"""PLA Light Brigade build, card names (Osama 26 Nov 2026 03:0x PST, thread 1567745029781454889: "Beijing Swords renamed Flying Tigers").
Branch codex/batch/osama/pla-light-brigade only.
- Beijing Swords 蓝剑 (1187, Light CAB Recon tab): card name (HUDName) -> 'Flying Tigers'. English only: Osama gave no Chinese name (no new bilingual
  names, 24 Nov rule). The row Name 'PLA Beijing Swords 蓝剑' stays, as other tools find the unit by it."""
BEIJING_SWORDS = 1187


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[BEIJING_SWORDS]['HUDName'] == 'Beijing Swords 蓝剑' and not any(u and u.get('HUDName') == 'Flying Tigers' for u in U.values()), 'Beijing Swords 1187; name free')
    g.put('Units', BEIJING_SWORDS, {'HUDName': 'Flying Tigers'})
    rec['pla_light_brigade_names_1126'] = {1187: ('Beijing Swords 蓝剑', 'Flying Tigers')}
    print('PLA LIGHT BRIGADE NAMES', rec['pla_light_brigade_names_1126'])
