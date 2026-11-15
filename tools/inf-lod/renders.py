import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender'
p=json.load(open('plan.json'));os.makedirs('ren',exist_ok=True)
jobs=[(d,f) for f,v in sorted(p.items()) if 'after' in v for d in ('orig','out')]
def go(j):
    d,f=j;o=f'ren/{f[:-4]}_{d}.png'
    if not os.path.exists(o):subprocess.run([B,'-b','-P','../inf-fat/render_fas.py','--',f'{d}/{f}',o],capture_output=True)
    return os.path.exists(o)
with ThreadPoolExecutor(4) as ex:r=list(ex.map(go,jobs))
print('renders',sum(r),'of',len(r))
