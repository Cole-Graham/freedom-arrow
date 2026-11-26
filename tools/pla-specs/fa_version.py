"""Freedom Arrow version order (Lateralus 19 Nov 2026: playtests are 0.9.1, 0.9.2, ...; dev builds toward them are 0.9.1-dev.N).
Hotfixes are lettered (Lateralus 22 Nov 2026: "0.9.4b, 0.9.4c"), with dev builds toward them as 0.9.4b-dev.N.
Order: 0.9.0-dev.44 < 0.9.1-dev.1 < 0.9.1 < 0.9.1b-dev.1 < 0.9.1b < 0.9.1c < 0.9.2-dev.1 < 0.9.2."""
import re
PATTERN=r'0\.(\d+)\.(\d+)([b-z])?(?:-dev\.(\d+))?'
def key(v):
    m=re.fullmatch(PATTERN+r'(?:-[a-z]+\d*)?',v)   # a local test build such as 0.9.7-dev.9-roc1 sorts as 0.9.7-dev.9
    if not m:raise ValueError(f'not a Freedom Arrow version: {v}')
    minor,patch,letter,dev=int(m[1]),int(m[2]),(ord(m[3])-ord('a')) if m[3] else 0,m[4]
    t=(0,minor,patch,letter,0,int(dev)) if dev is not None else (0,minor,patch,letter,1,0)
    return t+(1 if v!=m[0].split('-roc')[0] and re.search(r'-[a-z]+\d*$',v) and not re.fullmatch(PATTERN,v) else 0,)   # ROC branch: a test build sorts just after its base (it carries later changes)
def at_least(v,ref):return key(v)>=key(ref)
