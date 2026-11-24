"""[FA] [1v1] Jelgava: End's JELGAVA layout (Steam Workshop 3832138779), with FA conquest and a camera for each team.
See common.prepare_end: End's script replaced by the FA graft; A B C 2, D E 4 (Lateralus 16 Nov 2026); first to 300."""
import common as C
# Lateralus 23 Nov 2026: "Jelgava: turn bravo spawns south" (End left every spawn facing north).
SPEC=C.end_spec(__file__,'Jelgava','Jelgava','3832138779',facing={'Bravo team':180})
def build(game,out):C.build_pair(game,out,SPEC)
NAME,SKIRMISH_NAME=[f['name'] for f in SPEC['flavors']]
