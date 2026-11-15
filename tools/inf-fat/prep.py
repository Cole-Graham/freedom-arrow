import zipfile,json,os,struct
import texture2ddecoder as t2d
from PIL import Image
z=zipfile.ZipFile('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/0.8/FreedomArrow-0.9.0-dev.10-complete.bamod');D='UserData/FAModels/'
rules=json.loads(z.read(D+'infantry-bodies.json'));bodies=sorted({r['lods'][0] for r in rules})
def texnames(b):
    o=4;nb=struct.unpack_from('<i',b,o)[0];o+=4
    for _ in range(nb):n=struct.unpack_from('<i',b,o)[0];o+=4+n
    ns=struct.unpack_from('<i',b,o)[0];o+=4;out=[]
    for _ in range(ns):
        n=struct.unpack_from('<i',b,o)[0];o+=4;out.append(b[o:o+n].decode());o+=n
        nv=struct.unpack_from('<i',b,o)[0];o+=4+nv*64;ni=struct.unpack_from('<i',b,o)[0];o+=4+ni*4
    return out
def decode(fat):
    d=open(fat,'rb').read();w,h,fmt,m,lin,n=struct.unpack_from('<6i',d,4);raw=d[28:28+w*h]
    px=(t2d.decode_bc5 if fmt==27 else t2d.decode_bc7)(raw,w,h)
    return Image.frombytes('RGBA',(w,h),px,'raw','BGRA').transpose(Image.FLIP_TOP_BOTTOM)
for bf in bodies:
    st=bf[:-4];b=z.read(D+bf)
    for w in ('png','gpu'):
        d=f'prev/{st}/{w}';os.makedirs(d,exist_ok=True);open(f'{d}/{bf}','wb').write(b)
        for t in texnames(b):
            if os.path.exists(f'{d}/{t}'):continue
            if w=='png':open(f'{d}/{t}','wb').write(open('png/'+t,'rb').read())
            else:decode('fat/'+t[:-4]+'.fat').save(f'{d}/{t}')
json.dump(bodies,open('bodies.json','w'));print('ok',len(bodies))
