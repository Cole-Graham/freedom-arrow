import sys,json,numpy as np;sys.path.insert(0,'../tools')
from famread import read_fam
from PIL import Image,ImageDraw
M='../veh/models/';out=[]
for slug,(x0,y0,z0,yaw) in __import__('add_drivers_seats').SEATS.items():
    V=read_fam(f'{M}m_roc_{slug}_static.fam');mj=json.load(open(f'{M}m_roc_{slug}_static.mat.json'));gk={k for k,v in mj.items() if v.get('cockpitDonor') or v.get('clearGlass')}
    zc=z0+(0.6 if yaw==0 else -0.6);ims=[]
    for view in ('side','front'):
        im=Image.new('RGB',(400,300),'white');d=ImageDraw.Draw(im);sc=110
        def pr(p):
            h=(p[:,2]-zc) if view=='side' else p[:,0]
            return np.c_[200+h*sc*(1 if (view=='front' or yaw==0) else -1),150-(p[:,1]-y0-0.3)*sc]
        for layer in ('veh','glass','drv'):
            for b,q in V:
                for x in q:
                    k=x['tex']+'|'+','.join('%.4f'%c for c in x['col']);isd='roc_infantry' in x['tex'];isg=k in gk
                    if {'veh':isd or isg,'glass':not isg,'drv':not isd}[layer]:continue
                    if not len(x['idx']):continue
                    P=np.array(x['pos']).reshape(-1,3);I=np.array(x['idx'],int).reshape(-1,3);c=P[I].mean(1)
                    m=(np.abs(c[:,2]-zc)<1.8) if view=='side' else (np.abs(c[:,2]-zc)<1.2)
                    if view=='side':m&=c[:,0]<0.05 if layer!='drv' else c[:,0]<0
                    Q=pr(P)
                    for t in I[m][::(1 if layer!='veh' else 2)]:
                        pts=[tuple(Q[j]) for j in t]
                        if layer=='veh':d.polygon(pts,fill=(205,205,205))
                        elif layer=='glass':d.polygon(pts,outline=(0,90,255))
                        else:d.polygon(pts,fill=(220,30,30))
        d.text((5,5),f'{slug} {view}',fill=(0,0,0));ims.append(im)
    out.append(ims)
S=Image.new('RGB',(800,300*len(out)),'white')
for i,(a,b) in enumerate(out):S.paste(a,(0,300*i));S.paste(b,(400,300*i))
S.save('/tmp/l8prev/drivers_check.png')
