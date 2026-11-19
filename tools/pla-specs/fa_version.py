"""Freedom Arrow version order (Lateralus 19 Nov 2026: playtests are 0.9.1, 0.9.2, ...; dev builds toward them are 0.9.1-dev.N).
Order: 0.9.0-dev.44 < 0.9.1-dev.1 < 0.9.1-dev.2 < 0.9.1 < 0.9.2-dev.1 < 0.9.2."""
import re
PATTERN=r'0\.(\d+)\.(\d+)(?:-dev\.(\d+))?'
def key(v):
    m=re.fullmatch(PATTERN,v)
    if not m:raise ValueError(f'not a Freedom Arrow version: {v}')
    minor,patch,dev=int(m[1]),int(m[2]),m[3]
    return (0,minor,patch,0,int(dev)) if dev is not None else (0,minor,patch,1,0)
def at_least(v,ref):return key(v)>=key(ref)
