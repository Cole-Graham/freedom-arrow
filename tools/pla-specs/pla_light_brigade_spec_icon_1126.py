"""PLA Light Brigade build, Light CAB spec icon (Osama 26 Nov 2026 15:5x PST, thread 1572407822849810463: "See the sword with the lightening? I want to
copy that as our spec icon", on the PLA Special Operations Forces sleeve badge). The Light CAB (70) had the Medium CAB's icon (FA_CHINA_MOTORIZED);
it gets FA_CHINA_LIGHT: the badge's sword and lightning bolt in the China spec icon style (tools/icons-src/make_china_light.py,
mod/source/runtime-qa/icons/FA_CHINA_LIGHT.png, seeded by ChinaUi.Addresses). Edits one field, adds no row. Spec order: Runtime.cs SpecOrder."""
LIGHT = 70


def apply(t, g, ok, rec):
    S = t['SpecializationsJson']
    ok(S[LIGHT]['Name'] == 'PLA PLAGF Light' and S[LIGHT]['Icon'] == 'FA_CHINA_MOTORIZED', 'Light CAB still on the Medium CAB icon')
    g.put('SpecializationsJson', LIGHT, {'Icon': 'FA_CHINA_LIGHT'})
    rec['pla_light_brigade_spec_icon_1126'] = {'spec': LIGHT, 'icon': 'FA_CHINA_LIGHT'}
    print('PLA LIGHT BRIGADE SPEC ICON', rec['pla_light_brigade_spec_icon_1126'])
