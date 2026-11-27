"""[FA] [1v1] Mountain: End's "1v1 Mountain" layout on Coal Mountain (Steam Workshop 3846746372, 27 November 2026), with FA conquest
and a camera for each team. See common.prepare_end_occ (End 27 Nov 2026: "do the same" as Below the Mountain).
- End's named zones are lettered in his order: Village A, Farms B, Destillation units C, Train terminal D, Mountain E; End's zone sizes are kept.
- Spawns 40 (Bravo ground), 43 (Alpha ground), 45 (Alpha helicopter) and 47 (Alpha air) faced 46-175 degrees away from the zones and now face
  them; the others keep End's facing.
- Alpha's ground spawn 43 stood 21 m north of the play area edge (Z 7433, edge 7412), on the railway. End 27 Nov 2026: "ensure the spawn is on a
  road". It is moved about 280 m south-east (X 1944 -> 2182, Z 7433 -> 7288) onto the road that crosses the railway there, 124 m inside the edge
  (placed from the game's tactical map image, about 8 m per pixel).
- Cameras sit between each team's two ground spawns; the helicopter and air spawns are left out.
- The map file lists DLC 3 (Coal Mountain), as coal_mountain_2v2 does."""
import common as C
ZONES=['Village','Farms','Destillation units','Train terminal','Mountain']
def edit(objects):
    s=next(o for o in objects if o.get('_uid')==43 and o.get('_type')==10);assert round(s['pos']['Z'])==7433,s['pos']
    s['pos']['X']=2182.0;s['pos']['Z']=7288.0;C.mag(s['pos'])
SPEC=C.end_occ_spec(__file__,'Mountain','Coal Mountain','3846746372',ZONES,{40,43,45,47},edit)
def build(game,out):C.build_pair(game,out,SPEC)
NAME,SKIRMISH_NAME=[f['name'] for f in SPEC['flavors']]
