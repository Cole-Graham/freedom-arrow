"""Five Euro preview cards hidden, their models held back (Osama 25 Nov 2026 11:4x PST, thread 1567745029781454889: "For next live build, let's hide
the flakpanzer gepard, k41 lynx, kf51 panther, and MAN, and VAB I don't want people to have to download these models. So for now make sure the models
aren't loaded on to the live build"; 11:5x "and hide the EBRC Jaguar"). Each card's one availability row leaves its preview spec (Germany 25, France 24) and the unit is hidden in the
Armory. No transport links. Unit, weapon and ammunition rows stay, so the cards come back by deleting this section. The model files: banned-models.txt
(package.py) and EU_HELD in work/model-rework-096/stage.py."""
CARDS = {1421: ('DE KF51 Panther', 25), 1422: ('DE KF41 Lynx', 25), 1426: ('DE Flakpanzer Gepard', 25), 1427: ('DE MAN HX77', 25), 1428: ('FR VAB', 24), 1300: ('FR EBRC Jaguar', 24)}


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    out = {}
    for uid, (name, spec) in CARDS.items():
        rows = [r for r in SA.values() if r and r['UnitId'] == uid]
        ok(U[uid]['Name'] == name and len(rows) == 1 and rows[0]['SpecializationId'] == spec and not any(r and r['UnitId'] == uid for r in TA.values()),
           (name, 'one preview card, no transport links', [(r['Id'], r['SpecializationId']) for r in rows]))
        g.remove('SpecializationAvailabilitiesJson', rows[0]['Id'])
        g.put('Units', uid, {'DisplayInArmory': False})
        ok(not any(r and r['UnitId'] == uid for r in SA.values()) and U[uid]['DisplayInArmory'] is False, name + ' hidden')
        out[name] = rows[0]['Id']
    for spec in (24, 25):
        ok(any(r and r['SpecializationId'] == spec for r in SA.values()), ('preview spec keeps other cards', spec))
    rec['euro_held_1125'] = out
    print('EURO HELD', out)
