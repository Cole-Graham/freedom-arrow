"""Loadout options no longer replace China card icons with vanilla labels (Osama 25 Nov 2026 01:1x PST, thread 1567745029781454889: the ZBD-05
showed a small vanilla IFV icon in the PLAN Naval/Special Forces list). The card copies kept their parent's option rows, and an option's
ThumbnailOverride replaces the card icon: ZBD-05 (AMPV copy) options 31353/31354 'US_AMPV_BUSHMASTER-Label', VN-3 (BMP-97 copy) options
31285/31287 'DLC3_BPM97_2A72-Label' / 'DLC3_BPM97_SPITSA_ATGM-Label'. They now show the card's own icon. The check after it: no China card
(FA_ icon) has an option with a vanilla icon override."""
FIX = {1413: (31353, 31354), 1402: (31285, 31287)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    mu = {m['Id']: m['UnitId'] for m in M.values() if m}
    ok([U[u]['Name'] for u in FIX] == ['PLA ZBD-05', 'PLA VN-3'], 'ZBD-05 1413, VN-3 1402')
    before = {}
    for u, opts in FIX.items():
        for o in opts:
            ok(mu[O[o]['ModificationId']] == u and not O[o]['ThumbnailOverride'].startswith('FA_'), ('own option with a vanilla icon', u, o))
            before[o] = O[o]['ThumbnailOverride']
            g.put('OptionsJson', o, {'ThumbnailOverride': U[u]['ThumbnailFileName']})
    left = [(o['Id'], o['ThumbnailOverride']) for o in O.values() if o and o.get('ThumbnailOverride') and not o['ThumbnailOverride'].startswith('FA_')
            and (U.get(mu.get(o['ModificationId'])) or {}).get('ThumbnailFileName', '').startswith('FA_')]
    ok(not left, ('China cards with a vanilla option icon', left))
    rec['option_icon_overrides_1125'] = {'before': before}
    print('OPTION ICONS', before)
