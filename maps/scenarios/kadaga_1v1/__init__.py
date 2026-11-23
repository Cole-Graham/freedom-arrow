"""[FA] [1v1] Kadaga: End's KADAGA layout (Steam Workshop 3832299239), with FA conquest and a camera for each team.
See common.prepare_end: End's script replaced by the FA graft; A B C 2, D E 4 (Lateralus 16 Nov 2026); first to 300."""
import common as C
SPEC=C.end_spec(__file__,'Kadaga','Kadaga Military Base','3832299239')
def build(game,out):C.build_pair(game,out,SPEC)
