"""[FA] [1v1] Below the Mountain: End's "1v1 BELOW THE MOUTAIN" layout on Coal Mountain (Steam Workshop 3846746484, 27 November 2026),
with FA conquest and a camera for each team. See common.prepare_end_occ (End 27 Nov 2026: cameras between the ground spawns).
- End's five zones were unnamed ("Objective zone 1-5", icon 0). They are lettered in his order, 1-5 = Alpha-Echo.
- Spawns 31, 32, 34 and 36 faced 77-137 degrees away from the zones and now face them; 33 and 35 keep End's facing.
- The map file lists DLC 3 (Coal Mountain), as coal_mountain_2v2 does."""
import common as C
# Lateralus 27 Nov 2026: "1v1 Below the Mountain: A E C - 2 points, B D - 4 points" (End's first ask was +1 on every zone).
VALUES=dict(Alpha=2,Bravo=4,Charlie=2,Delta=4,Echo=2)
# Spawns more than 45 degrees off (before): Alpha ground 31 129, 32 -77, air 36 137; Bravo ground 34 -131. Bravo 33 (-45) and air 35 (-41) keep End's facing.
SPEC=C.end_occ_spec(__file__,'Below the Mountain','Coal Mountain','3846746484',[f'Objective zone {i}' for i in range(1,6)],VALUES,{31,32,34,36})
def build(game,out):C.build_pair(game,out,SPEC)
NAME,SKIRMISH_NAME=[f['name'] for f in SPEC['flavors']]
