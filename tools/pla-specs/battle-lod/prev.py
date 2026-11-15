import json,os,subprocess,time,sys
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender';S='/home/sam/tars/work/ba-dev/replicas/codex/work/pla-unit-icons-20261114/sil.py'
r=json.load(open(f'{D}/out/results.json'))
for f,v in r.items():   # refresh after the re-runs
    a=read_fam(f'{D}/src/{f}');b=read_fam(f'{D}/out/{f}');v['tris']=[sum(len(s['idx'])//3 for _,ss in x for s in ss) for x in (a,b)];v['bytes']=[os.path.getsize(f'{D}/src/{f}'),os.path.getsize(f'{D}/out/{f}')]
json.dump(r,open(f'{D}/out/results.json','w'),indent=1)
jobs=[(f'{D}/{w}/{f}',f'{D}/prev/{f[:-4]}_{w}.png') for f in r for w in ('src','out')]
def bl():return int(subprocess.run(['pgrep','-c','-f','bin/blender'],capture_output=True,text=True).stdout.strip() or 0)
run=[]
while jobs or run:
    run=[p for p in run if p.poll() is None]
    if jobs and len(run)<2 and bl()<4:
        i,o=jobs.pop(0)
        if not os.path.exists(o):run.append(subprocess.Popen(['nice','-n','10',B,'-b','-P',S,'--',i,o,'35','20'],env=dict(os.environ,MODE='albedo'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
    time.sleep(0.5)
from PIL import Image,ImageDraw
items=sorted(r.items(),key=lambda x:-x[1]['tris'][0])
for si in range(0,len(items),8):
    S_=Image.new("RGB",(1300,8*230),(90,90,90));d=ImageDraw.Draw(S_)
    for j,(f,v) in enumerate(items[si:si+8]):
        for c,w in enumerate(('src','out')):
            im=Image.open(f'{D}/prev/{f[:-4]}_{w}.png').convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((620,200));bg=Image.new('RGBA',im.size,(90,90,90,255));bg.alpha_composite(im);S_.paste(bg.convert('RGB'),(20+650*c,230*j+25))
        d.text((20,230*j+5),f"{v['unit']}: {v['tris'][0]:,} -> {v['tris'][1]:,} triangles",fill=(255,255,255))
    S_.save(f'{D}/prev/sheet{si//8+1}.png')
print("sheets",(len(items)+7)//8)
