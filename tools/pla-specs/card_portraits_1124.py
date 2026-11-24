"""Card pictures for the new China vehicles from Osama's Armory side shots (Osama 24 Nov 2026 00:5x PST, thread "China cosmetic work":
"Make units cards starting with this ZTD-05", then ZSD-05, ZRZ-100, ZBD-05, VN-3; 01:2x ZBL-08 Recon, ZSL-191; 02:1x US XQ-58A Valkyrie, thread "blue dragons"). Images: work/mk-card-art-1124 (make.py) ->
mod/source/runtime-qa/icons/FA_CN_<X>-Portrait.png, embedded by CardIcons.cs (Portrait/_BASIC/_HOVER). Sets PortraitFileName on the card and
on its own loadout rows (Name = card name + ' ...'); the small card label (ThumbnailFileName) stays as it is. Add a line to CARDS for the next one."""
import os
CARDS = {'PLA ZTD-05': 'FA_CN_ZTD05', 'PLA ZSD-05': 'FA_CN_ZSD05', 'PLA ZRZ-100': 'FA_CN_ZRZ100', 'PLA ZBD-05': 'FA_CN_ZBD05', 'PLA VN-3': 'FA_CN_VN3',
         'PLA ZBL-08 Recon': 'FA_CN_ZBL08R', 'PLA ZSL-191': 'FA_CN_ZSL191',
         'US XQ-58A Valkyrie': 'FA_US_XQ58A',
         'PLA ZZC-06': 'FA_CN_ZZC06'}   # 03:1x thread 1567745029781454889: "make an ew card for the ZZC-06" (Armory shot); runs after zzc06_recon_1124   # 02:1x thread blue dragons: "Valkyrie new icon, make na icon out of this" (Armory shot)
ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')
CS = os.path.join(ICONS, '..', 'CardIcons.cs')


def apply(t, g, ok, rec):
    U = t['Units']; cs = open(CS).read(); done = {}
    for name, key in CARDS.items():
        addr = key + '-Portrait'
        ok(os.path.isfile(os.path.join(ICONS, addr + '.png')), addr + '.png in runtime-qa/icons')
        ok(all(f'("{addr}{s}","{addr}.png")' in cs for s in ('', '_BASIC', '_HOVER')), addr + ' in CardIcons.cs')
        ids = sorted(i for i, u in U.items() if u and (u.get('Name') == name or (u.get('Name') or '').startswith(name + ' '))
                     and '(old' not in u['Name'] and 'Catalogue' not in u['Name'])
        ok(any(U[i]['Name'] == name for i in ids), name + ' card exists')
        for i in ids: g.put('Units', i, {'PortraitFileName': addr})
        done[name] = ids
    ok(all(U[i]['PortraitFileName'] == CARDS[n] + '-Portrait' for n, ids in done.items() for i in ids), 'portraits set')
    rec['card_portraits_1124'] = {n: len(v) for n, v in done.items()}
    print('CARD PORTRAITS', {n: v for n, v in done.items()})
