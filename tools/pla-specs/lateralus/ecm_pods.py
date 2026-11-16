"""Plane ECM pods give 10% ECM each (Lateralus 16 Nov 2026 08:3x PST, thread 1571554273639006392: "I also want make ECM pods give 10% ECM per
pod on planes.... queue that up as well").
How ECM works in the data (0.9.0-dev.24): the option chosen in a pylon slot gives the plane its whole ECM through an ability with
ECMAccuracyMultiplier (ECM % = 1 - multiplier; EA-18G 0.55 = 45%). Pods are the option's turrets named "Helper ECM ..." (Khibiny and Vitebsk
come as a left/right pair = 2 pods); options with no helper turrets count from the name (2xECM = 2; wingtip "ECM" = 2; ECMPod/1xECM = 1).
Rule: in each plane slot, the options with the fewest pods are the base (their ECM, or the plane's default ECM ability when they have none).
Every option with more pods gets base + 10% per extra pod. Slots where every option has the same pods (EA-6B inner, F-16 ECM slots, EA-18G
inner) are not pod choices and stay as they are. New ECM levels are copies of the option's current ECM ability (or the plane's default one)
with only the multiplier and name changed, linked to the unit (UnitAbilities), so shared ability rows are never edited.
apply(t, g, ok) uses the pla_graph Graph (g.put/g.add); EXPECT pins the result so a data change cannot silently alter it."""
import re
EXPECT={809:0.65,811:0.75,880:0.55,950:0.75,952:0.75,3089:0.65,20141:0.7,1344:0.65,1346:0.65,1682:0.8,1683:0.7,1206:0.65,1660:0.65,2010:0.65,2012:0.65,
        1406:0.5,1408:0.5,1305:0.65,1306:0.65,2036:0.65,1135:0.5,1137:0.5,2003:0.5,1118:0.5,1119:0.5,1120:0.5}   # option id: new ECMAccuracyMultiplier
def apply(t,g,ok):
    O,M,U,AB,UA,TJ=(t[k] for k in ('OptionsJson','ModificationsJson','Units','AbilitiesJson','UnitAbilitiesJson','TurretsJson'))
    avail={r.get('UnitId') for r in t['SpecializationAvailabilitiesJson'].values()}
    mult=lambda a:AB.get(a,{}).get('ECMAccuracyMultiplier')
    def ecm_slot(o):
        for i in (1,2,3):
            a=o.get(f'Ability{i}Id')
            if a and mult(a) not in (None,0,1,1.0):return i,a
        return None,None
    def pods(o):
        n=sum(1 for i in range(21) if o.get(f'Turret{i}Id') and 'ECM' in (TJ.get(o[f'Turret{i}Id'],{}).get('Name') or '').upper())
        if n:return n
        nm=(o.get('Name') or '').upper();m=re.search(r'(\d)\s*X\s*ECM|ECM\w*\s*X\s*(\d)',nm)
        if m:return int(m.group(1) or m.group(2))
        return (2 if 'WINGTIP' in nm else 1) if re.search(r'\bECM',nm) else 0
    def default_ecm(uid):
        for ua in UA.values():
            a=ua.get('AbilityId');n=AB.get(a,{}).get('Name','')
            if ua.get('UnitId')==uid and mult(a) not in (None,0,1) and 'Default' in n and 'Not Default' not in n:return a
    clones={};done={}
    for m in list(M.values()):
        u=U.get(m.get('UnitId'))
        if not u or u.get('CategoryType')!=6 or u['Id'] not in avail:continue
        opts=[o for o in O.values() if o.get('ModificationId')==m['Id']]
        counts={o['Id']:pods(o) for o in opts}
        if not opts or max(counts.values())==min(counts.values()):continue
        low=min(counts.values());baseopts=[o for o in opts if counts[o['Id']]==low]
        bm=[mult(ecm_slot(o)[1]) for o in baseopts if ecm_slot(o)[1]]
        dflt=default_ecm(u['Id'])
        base=1-(max(set(bm),key=bm.count) if bm else (mult(dflt) if dflt else 1.0))
        for o in opts:
            extra=counts[o['Id']]-low
            if extra<=0:continue
            want=round(1-(base+0.10*extra),2)
            ok(o['Id'] in EXPECT and abs(EXPECT[o['Id']]-want)<1e-9,f"{u['Name']} {o['Name']} [{o['Id']}]: ECM multiplier {want} matches the pinned plan")
            slot,cur=ecm_slot(o)
            if cur and abs(mult(cur)-want)<1e-9:done[o['Id']]=cur;continue
            tmpl=cur or dflt
            ok(tmpl is not None,f"{u['Name']} {o['Name']}: has an ECM ability to copy")
            key=(tmpl,want)
            if key not in clones:
                clones[key]=g.add('AbilitiesJson',AB[tmpl],{'Name':f"ECM Plane pods FA {want}",'ECMAccuracyMultiplier':want})
            na=clones[key]
            if slot is None:
                slot=next((i for i in (1,2,3) if not o.get(f'Ability{i}Id')),None);ok(slot is not None,f"{o['Name']}: free ability slot")
            g.put('OptionsJson',o['Id'],{f'Ability{slot}Id':na})
            if not any(x.get('UnitId')==u['Id'] and x.get('AbilityId')==na for x in UA.values()):
                tmpl_ua=next(x for x in UA.values() if x.get('UnitId')==u['Id'])
                g.add('UnitAbilitiesJson',tmpl_ua,{'UnitId':u['Id'],'AbilityId':na})
            ok(abs(mult(O[o['Id']][f'Ability{slot}Id'])-want)<1e-9,f"{o['Name']} now ECM {round((1-want)*100)}%")
            done[o['Id']]=na
    ok(set(done)==set(EXPECT),f'every pinned ECM option handled: missing {sorted(set(EXPECT)-set(done))}')
    return {'options':{str(k):EXPECT[k] for k in sorted(done)},'newAbilities':len(clones)}
