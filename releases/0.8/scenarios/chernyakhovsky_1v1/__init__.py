"""[FA] [1v1] Chernyakhovsky: End's CHERNYAKHOVSKY layout (Steam Workshop 3832031239), with FA conquest and a camera for each team.
See common.prepare_end: End's script replaced by the FA graft; Bravo (centre) 3, other zones 2; first to 100."""
import common as C
SPEC=C.end_spec(__file__,'Chernyakhovsky','Chernyakhovsk','3832031239')
def build(game,out):C.build_pair(game,out,SPEC)
