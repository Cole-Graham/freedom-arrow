"""[FA] [1v1] Central Village: End's CENTRAL VILLAGE layout (Steam Workshop 3832287948), with FA conquest and a camera for each team.
See common.prepare_end: End's script replaced by the FA graft; Bravo (centre) 3, other zones 2; first to 100."""
import common as C
SPEC=C.end_spec(__file__,'Central Village','Central Village','3832287948')
def build(game,out):C.build_pair(game,out,SPEC)
