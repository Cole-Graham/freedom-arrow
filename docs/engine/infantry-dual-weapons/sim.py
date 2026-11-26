"""Raiders CQC (unit 70) inside 100 m: Mk18 x12 and M1014 x4 share 4 men. Engine rules modelled (1.2.2.1 code, ../infantry-dual-weapons.md):
- weapon cooldown and reload run N x faster with N alive carriers (BurstCooldownSystem / MagazineReloadingSystem, UsingAliveSoldierCount);
- a man is queued for a weapon when its next shot is <= AimingAnimationDuration (0.5 s) away, round-robin over that weapon's carriers,
  skipping men already aiming for any weapon (TryGetNextAliveAndAvailableSoldier, IsAiming);
- the shot fires only with a queued man (ShootingSystem.CheckInfantryConditions), who is then freed (TryGetSoldierEffectSpawnPoint).
Simplified: one queued man per upcoming shot, aim time ignored, both weapons always have a target."""
import sys
LEAD=0.5;DT=0.01;T=600.0
def run(share=True,seed=0):
    men={i:False for i in range(14)}            # aiming?
    # member order 113..126 -> 0..13: dual 0,1,5,6 (113,114,118,119); M32 2,3; LAW 4,7..13
    rifle=[0,1,4,5,6,7,8,9,10,11,12,13];shot=[0,1,5,6]
    W={'Mk18':dict(c=rifle,mag=30,gap=4.0,rel=4.0),'M1014':dict(c=shot,mag=8,gap=2.0,rel=4.0)}
    for w in W.values():w.update(next=0.0,left=w['mag'],q=[],last=-1,shots=0,wait=0.0)
    t=0.0
    while t<T:
        for name,w in W.items():
            n=len(w['c'])
            # queue men for upcoming shot
            if w['next']-t<=LEAD and not w['q']:
                for k in range(1,n+1):
                    i=(w['last']+k)%n;m=w['c'][i]
                    busy=men[m] if share else (m in [x for x in w['q']])
                    if not busy:w['q'].append(m);men[m]=True;w['last']=i;break
            if t>=w['next']:
                if w['q']:
                    m=w['q'].pop(0);men[m]=False;w['shots']+=1;w['left']-=1
                    if w['left']==0:w['left']=w['mag'];w['next']=t+w['rel']/n
                    else:w['next']=t+w['gap']/n
                else:w['wait']+=DT
        t+=DT
    return {k:(round(v['shots']/T*60,1),round(v['wait'],1)) for k,v in W.items()}
print('shared men (engine):',run(True))
print('no sharing (DPM today):',run(False))
