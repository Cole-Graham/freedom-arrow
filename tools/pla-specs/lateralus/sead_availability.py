"""SEAD plane availability (Lateralus 16 Nov 2026 15:2x PST, thread 1571554273639006392: "give me a proposal for increasing the availability of
SEAD planes, where planes with strike loadouts stay at their current card count, but other SEAD planes go up by 1"; 15:27 "queue it").
Same split as the SEAD price proposal (sheet 1Y0rUZ0Do1uMdGyENd1TsnvSWi4ecTLYMQSBLrEiLCC4, Availability tab): planes not ticked "keep" in
the Planes tab get +1 card; strike planes and the SEAD helicopters keep their count. Card count = SpecializationAvailabilitiesJson
MaxAvailabilityXp0 (each of these planes has one deck row). apply(t, put, ok) checks every old value first."""
# unit id: (name, spec availability row, cards now, cards new)
ROWS={1242:('PLA J-11D',2016116,2,3),974:('PLA J-15D',2008266,2,3),977:('PLA J-16D',2008269,2,3),966:('PLA J-20S',2008260,2,3),
      1251:('PLA J-31',2014513,2,3),921:('PLA J-35',2008203,2,3),929:('PLA J-36',2014507,2,3),744:('FA MiG-29S',2001361,2,3),
      311:('MiG-29K',547,2,3),308:('Su-24MP',570,2,3),377:('EA-6B Prowler',673,2,3),286:('F-16CJ',785,2,3),742:('FA EA-18G Growler',2001270,2,3)}
def apply(t,put,ok):
    SA,U=t['SpecializationAvailabilitiesJson'],t['Units']
    for uid,(name,row,old,new) in ROWS.items():
        ok(U[uid]['Name']==name,f'unit {uid} is {name}')
        rows=[r for r in SA.values() if r.get('UnitId')==uid];ok([r['Id'] for r in rows]==[row],f'{name}: one deck row {row}')
        r=SA[row];ok(r.get('MaxAvailabilityXp0')==old and not any(r.get(f'MaxAvailabilityXp{i}') for i in (1,2,3)),f'{name}: {old} cards')
        put('SpecializationAvailabilitiesJson',row,{'MaxAvailabilityXp0':new})
        ok(SA[row]['MaxAvailabilityXp0']==new,f'{name}: now {new} cards')
    return {str(u):[v[0],v[2],v[3]] for u,v in ROWS.items()}
