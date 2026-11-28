"""PLAN spec name (Osama 27 Nov 2026 17:2x PST, thread 1567745029781454889: "in the chinese PLAN translation it should be PLAN and PLAGF amphibious CAB"
/ 17:3x "make this the name for the spec now"): spec 20 'PLAN Naval/Special Forces 海军参谋部远域特种作战大队' -> 'PLAN & PLAGF Amphibious CAB
海军陆战队·陆军两栖合成旅' (海军陆战队 = PLAN Marine Corps, 陆军两栖合成旅 = PLA Army amphibious combined arms brigade). Description unchanged."""
SPEC, OLD, NEW = 20, 'PLAN Naval/Special Forces 海军参谋部远域特种作战大队', 'PLAN & PLAGF Amphibious CAB 海军陆战队·陆军两栖合成旅'


def apply(t, g, ok, rec):
    S = t['SpecializationsJson']
    ok(S[SPEC]['UIName'] == OLD, ('spec 20 name as read', S[SPEC]['UIName']))
    g.put('SpecializationsJson', SPEC, {'UIName': NEW})
    rec['plan_spec_name_1127'] = [OLD, NEW]
    print('PLAN SPEC NAME', rec['plan_spec_name_1127'])
