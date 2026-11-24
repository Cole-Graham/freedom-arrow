"""Unit cards show English only (Osama 24 Nov 2026 01:0x PST, thread "China cosmetic work": "what the fuck is this localization?", after
23 Nov 13:0x "it should have been English OR chinese not both" and 22:1x "what the fuck did I say about localization?").
The card label is not resolved through LocalizationService: dev.18 on his PC logged FREEDOM_ARROW_LANG_NAMES "first name via
TryResolveSimpleKey: 'PLAAF Air Force'" (spec names split by language) while the J-5/J-6W drone cards still showed "J-5 Drone 歼-5无人机".
So every unit HUDName "English 中文" keeps its English half. The Chinese halves are listed in rec for a later, proven card hook.
GUARD: no unit HUDName may contain Chinese characters. Runs LAST in the batch."""
import re
CJK = re.compile(r'[　-〿㐀-鿿＀-￯]')


def apply(t, g, ok, rec):
    U = t['Units']; zh = {}
    for uid, u in sorted(U.items()):
        h = (u or {}).get('HUDName') or ''
        m = CJK.search(h)
        if not m: continue
        en = h[:m.start()].strip()
        ok(en and not CJK.search(en), ('English half', uid, h))
        g.put('Units', uid, {'HUDName': en}); zh[uid] = (en, h[m.start():].strip())
    ok(not any(CJK.search((u or {}).get('HUDName') or '') for u in U.values()), 'no Chinese characters in any card name')
    rec['card_names_english'] = {'count': len(zh), 'zh': zh}
    print('CARD NAMES ENGLISH', len(zh), [v[0] for v in zh.values()])
