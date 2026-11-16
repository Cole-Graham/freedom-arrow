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
        1406:0.6,1408:0.6,1305:0.65,1306:0.65,2036:0.65,1135:0.6,1137:0.6,2003:0.6,1118:0.7,1119:0.7,1120:0.7}   # option id: new ECMAccuracyMultiplier
# Lateralus 16 Nov 2026 09:0x PST: "change Su-35S so it is 10% ECM without the pods, and 30% ECM with the pods. change Su-34 / Su-30SM so they
# are 20% ECM without the pods, and 40% ECM with the pods". These planes skip the 10%-per-pod rule: pod options get the pod value, no-pod options
# with an ECM ability get the no-pod value, and the plane's default ECM ability (Su-35S, Su-30SM: the built-in level) is relinked to a copy at
# the no-pod value (it stays the default ability, so the unit still has exactly one default).
OVERRIDE={'Su-35S':(0.10,0.30),'Su-34':(0.20,0.40),'Su-30SM':(0.20,0.40)}   # plane: (ECM without pods, with pods)
EXPECT_NOPOD={1134:0.8,1136:0.8,1138:0.8,1139:0.8}                          # Su-34 no-pod options: option id -> multiplier
EXPECT_DEFAULT={'Su-35S':0.9,'Su-30SM':0.8}                                 # plane -> default ECM multiplier
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
            want=round(1-(OVERRIDE[u['Name']][1] if u['Name'] in OVERRIDE else base+0.10*extra),2)
            ok(o['Id'] in EXPECT and abs(EXPECT[o['Id']]-want)<1e-9,f"{u['Name']} {o['Name']} [{o['Id']}]: ECM multiplier {want} matches the pinned plan")
            slot,cur=ecm_slot(o)
            if cur and abs(mult(cur)-want)<1e-9:done[o['Id']]=cur;continue
            tmpl=cur or dflt
            ok(tmpl is not None,f"{u['Name']} {o['Name']}: has an ECM ability to copy")
            key=(tmpl,want)
            if key not in clones:
                clones[key]=g.add('AbilitiesJson',AB[tmpl],{'Name':f"ECM Plane pods FA {want}",'ECMAccuracyMultiplier':want,'IsDefault':False})   # an option ability is never the unit default
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
    nopod={};dflt_done={}
    for name,(off_,on_) in OVERRIDE.items():
        us=[u for u in U.values() if u.get('Name')==name and u['Id'] in avail];ok(len(us)==1,f'{name}: one unit');u=us[0]
        want=round(1-off_,2)
        for m in [m for m in M.values() if m.get('UnitId')==u['Id']]:
            for o in [o for o in O.values() if o.get('ModificationId')==m['Id'] and o['Id'] not in EXPECT]:
                slot,cur=ecm_slot(o)
                if not cur:continue
                key=(cur,want)
                if key not in clones:clones[key]=g.add('AbilitiesJson',AB[cur],{'Name':f"ECM Plane no pods FA {want}",'ECMAccuracyMultiplier':want,'IsDefault':False})
                g.put('OptionsJson',o['Id'],{f'Ability{slot}Id':clones[key]})
                if not any(x.get('UnitId')==u['Id'] and x.get('AbilityId')==clones[key] for x in UA.values()):
                    g.add('UnitAbilitiesJson',next(x for x in UA.values() if x.get('UnitId')==u['Id']),{'UnitId':u['Id'],'AbilityId':clones[key]})
                nopod[o['Id']]=want
        d=default_ecm(u['Id'])
        if d:
            ok(AB[d].get('IsDefault') is True,f'{name}: default ECM ability {d} is the default')
            key=('default',d,want)
            if key not in clones:clones[key]=g.add('AbilitiesJson',AB[d],{'Name':f"ECM Plane Default FA {want}",'ECMAccuracyMultiplier':want})
            row=next(x for x in UA.values() if x.get('UnitId')==u['Id'] and x.get('AbilityId')==d)
            g.put('UnitAbilitiesJson',row['Id'],{'AbilityId':clones[key]})
            dflt_done[name]=want
    ok(nopod==EXPECT_NOPOD,f'no-pod ECM options as pinned: {nopod}')
    for uid in {m['UnitId'] for m in M.values() if any(o.get('ModificationId')==m['Id'] and o['Id'] in done for o in O.values())}:
        ok(sum(1 for x in UA.values() if x.get('UnitId')==uid and AB.get(x.get('AbilityId'),{}).get('IsDefault'))<=1,f'{U[uid]["Name"]}: at most one default ability')
    ok(dflt_done==EXPECT_DEFAULT,f'default ECM as pinned: {dflt_done}')
    return {'options':{str(k):EXPECT[k] for k in sorted(done)},'noPod':{str(k):v for k,v in nopod.items()},'defaults':dflt_done,'newAbilities':len(clones)}
