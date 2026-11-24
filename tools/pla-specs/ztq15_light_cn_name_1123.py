"""ZTQ-15 Light Chinese name (Osama 23 Nov 2026 21:0x PST, thread 1567745029781454889: "Ztq-15 light in Chinese localization should be ZTQ-15
airborne"). HUDName 'ZTQ-15 Light' -> bilingual 'ZTQ-15 Light ZTQ-15空降型': runtime-qa/LangNames.cs shows 'ZTQ-15 Light' in English and
'ZTQ-15空降型' (airborne variant) in Chinese (it splits at the last space before the first CJK character, so the Chinese half has no space)."""
UNIT, EN, ZH = 1268, 'ZTQ-15 Light', 'ZTQ-15空降型'


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[UNIT]['HUDName'] == EN, 'ZTQ-15 Light card')
    g.put('Units', UNIT, {'HUDName': f'{EN} {ZH}'})
    s = U[UNIT]['HUDName']; i = next(k for k, c in enumerate(s) if '一' <= c <= '鿿'); j = s.rfind(' ', 0, i)
    ok((s[:j].strip(), s[j:].strip()) == (EN, ZH), ('LangNames halves', s))
    rec['ztq15_light_cn_name'] = {'unit': UNIT, 'HUDName': s}
    print('ZTQ-15 LIGHT CN', rec['ztq15_light_cn_name'])
