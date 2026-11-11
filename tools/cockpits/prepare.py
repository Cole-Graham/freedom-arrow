"""Split only canopy faces in the pinned model pack; preserve geometry and opaque texture UVs."""
from pathlib import Path
import argparse,hashlib,io,json,struct,zipfile
import numpy as np
from PIL import Image
from fam import read,components
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--donor-mesh',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
z=zipfile.ZipFile(a.base);mapping=json.loads(z.read('UserData/FAModels/models.json'))
policy={}
for n in ['PLA J-20','PLA J-20S','PLA J-31','PLA J-35','PLA J-36','PLA J-50','YF-23 Black Widow II']:policy[n]='SOURCE'
for n in ['PLA J-10C','PLA J-10S','PLA J-11B','PLA J-15','PLA J-15D','PLA J-16','PLA J-16D','PLA Su-30MKK','Su-47 Berkut','F-14 Tomcat','F-21 Super Tomcat']:policy[n]='US_F16_Glass'
for n in ['Su-75 Checkmate','Su-57D']:policy[n]='!RU_SU-57glass'
assert len(policy)==20
# Canonical F-22 glass UVs. Only the broad canopy island is used; sensor windows on the same material are excluded.
d=json.loads(a.donor_mesh.read_text());dp=np.array(d['pos']);du=np.array(d['uv']);di=np.array(d['idx']);sub=d['sub'][1];used=np.unique(di[sub[0]//2:sub[0]//2+sub[1]]);used=used[(du[used,0]<.7)&(du[used,1]<.3)];dp=dp[used];du=du[used];dp=(dp-dp.min(0))/np.maximum(np.ptp(dp,axis=0),1e-6)
files={}
for n,donor in policy.items():
 for key in ['file','battle']:
  fn=mapping[n][key]
  if fn in files:assert files[fn]['donor']==donor;files[fn]['units'].append(n);continue
  files[fn]={'donor':donor,'units':[n],'copy':key}
texcache={}
def pixels(tex,uv):
 if tex not in texcache:texcache[tex]=np.array(Image.open(io.BytesIO(z.read('UserData/FAModels/'+tex))).convert('RGBA'))
 im=texcache[tex];xy=(np.c_[uv[:,0]%1,1-uv[:,1]%1]*[im.shape[1]-1,im.shape[0]-1]).round().astype(int);return im[xy[:,1],xy[:,0]]
def mask(fn,d):
 C=d['pos'][d['ind']].mean(1);guard=(abs(C[:,0])<1)&(C[:,2]>1.5)&(C[:,2]<9)&(C[:,1]>2)
 t=d['tex'];b=Path(fn).stem
 if b.startswith('m_su57d'):return guard&(C[:,1]>2.5)&(t.endswith('_tex3.png') or t.endswith('_tex8.png'))
 if b.startswith('m_su75_t75'):return guard&t.endswith('_tex2.png')
 if b.startswith(('m_su47','m_f14','m_yf23','j11b')):return guard&(d['col'][3]<.9)
 if b.startswith('j10t'):return guard&t.endswith('_tex18.png' if '_lo' in b else '_tex17.png')
 # These atlases include frames and glass. Restrict by known canopy atlas and position, then source alpha.
 suffix={'m_j20_':'_tex3.png','m_j20s':'_tex0.png','m_j35n_fixed':'_tex0.png','m_j35_':'_tex1.png','m_j36':'_tex1.png','m_j50':'_tex1.png','m_j10c':'_tex1.png','m_j15d':'_tex0.png','m_j15_':'_tex0.png','m_j16':'_tex0.png'}
 want=next((v for k,v in suffix.items() if b.startswith(k)),None)
 if want is None:raise ValueError('No canopy rule: '+fn)
 if not t.endswith(want) or not guard.any():return np.zeros(len(C),bool)
 alpha=pixels(t,d['uv'][d['ind']].mean(1))[:,3];sel=guard&(alpha<110)
 # HUD cards inside some combined hull meshes have a low alpha too; they have negligible fore/aft span.
 if sel.any():
  ii=np.where(sel)[0];temp={**d,'ind':d['ind'][sel]};cc=components(temp)
  for c in np.unique(cc):
   which=ii[cc==c];P=d['pos'][np.unique(d['ind'][which])]
   if np.ptp(P[:,2])<.2:sel[which]=False
 return sel

def compact(d,I):
 used=np.unique(I);remap=np.full(len(d['pos']),-1,np.int32);remap[used]=np.arange(len(used));return {**d,'pos':d['pos'][used].copy(),'norm':d['norm'][used].copy(),'uv':d['uv'][used].copy(),'ind':remap[I]}
def encode(ds):
 f=io.BytesIO();f.write(b'FAM1');bones=list(dict.fromkeys(d['bone'] for d in ds));f.write(struct.pack('<i',len(bones)))
 def st(s):b=s.encode();f.write(struct.pack('<i',len(b)));f.write(b)
 for bone in bones:
  group=[d for d in ds if d['bone']==bone];st(bone);f.write(struct.pack('<i',len(group)))
  for d in group:
   st(d['tex']);f.write(struct.pack('<4f',*d['col']));f.write(struct.pack('<i',len(d['pos'])))
   for k in ['pos','norm','uv']:f.write(d[k].astype('<f4').tobytes())
   f.write(struct.pack('<i',d['ind'].size));f.write(d['ind'].astype('<i4').tobytes())
 return f.getvalue()
def trihashes(d,uv=True):
 P=d['pos'][d['ind']];N=d['norm'][d['ind']];U=d['uv'][d['ind']]
 return sorted(sha(np.concatenate([P[i].ravel(),N[i].ravel()]+([U[i].ravel()] if uv else [])).astype('<f4').tobytes()) for i in range(len(P)))
report={'units':policy,'base_sha256':hashlib.file_digest(a.base.open('rb'),'sha256').hexdigest(),'files':{},'native_verified':False}
for fn,info in files.items():
 raw=z.read('UserData/FAModels/'+fn);temp=a.out/('_input_'+fn);temp.write_bytes(raw);ds=read(temp);temp.unlink();sels=[mask(fn,d) for d in ds];source_mp=json.loads(z.read('UserData/FAModels/'+str(Path(fn).with_suffix('.mat.json')))) if 'UserData/FAModels/'+str(Path(fn).with_suffix('.mat.json')) in z.namelist() else {};overrides={};count=sum(int(s.sum()) for s in sels);assert count>0,fn
 selected=np.concatenate([d['pos'][np.unique(d['ind'][s])] for d,s in zip(ds,sels) if s.any()]);lo=selected.min(0);extent=np.maximum(np.ptp(selected,axis=0),1e-6);out=[];opaque_before=[];all_before=[]
 for d,s in zip(ds,sels):
  all_before+=trihashes(d,False)
  if (~s).any():q=compact(d,d['ind'][~s]);out.append(q);opaque_before+=trihashes(q)
  if s.any():
   q=compact(d,d['ind'][s])
   if info['donor']=='SOURCE':
    original_key=d['tex']+'|'+','.join(f'{v:.4f}' for v in d['col'])
    settings=dict(source_mp.get(original_key,{}));settings.update(alpha='BLEND');settings.pop('clearGlass',None);settings.pop('opacity',None);settings.pop('cockpitDonor',None)
    if d['tex']:
     stem=Path(d['tex']).stem;alias=stem+'_source_canopy';q['tex']=alias+'.png'
     for suffix in ['.png','_n.png','_mask.png']:
      member='UserData/FAModels/'+stem+suffix
      if member in z.namelist():(a.out/(alias+suffix)).write_bytes(z.read(member))
    overrides[q['tex']+'|'+','.join(f'{v:.4f}' for v in q['col'])]=settings
   else:q['tex']='';q['col']=[1,1,1,.998]
   if info['donor']=='US_F22_Glass':
    pp=(q['pos']-lo)/extent
    for start in range(0,len(pp),256):
     distance=((pp[start:start+256,None,:]-dp[None,:,:])**2).sum(2);q['uv'][start:start+256]=du[distance.argmin(1)]
   out.append(q)
 b=encode(out);(a.out/fn).write_bytes(b);after=read(a.out/fn)
 assert sorted(all_before)==sorted(h for d in after for h in trihashes(d,False)),('geometry changed',fn)
 if info['donor']=='SOURCE':
  assert sorted(h for d in ds for h in trihashes(d))==sorted(h for d in after for h in trihashes(d)),('source UV changed',fn)
 else:assert sorted(opaque_before)==sorted(h for d in after if not (abs(d['col'][3]-.998)<1e-5 and d['tex']=='') for h in trihashes(d)),('opaque UV changed',fn)
 # Direct old alpha glass outside the canopy guard remains under its original material.
 matfn=str(Path(fn).with_suffix('.mat.json'));zn='UserData/FAModels/'+matfn;mp=json.loads(z.read(zn)) if zn in z.namelist() else {};mp.update(overrides) if info['donor']=='SOURCE' else mp.update({'|1.0000,1.0000,1.0000,0.9980':{'cockpitDonor':info['donor']}});(a.out/matfn).write_text(json.dumps(mp,indent=2)+'\n')
 report['files'][fn]={**info,'before_sha256':sha(raw),'after_sha256':sha(b),'glass_faces':count,'glass_bounds':[lo.tolist(),(lo+extent).tolist()],'geometry_unchanged':True,'opaque_uv_unchanged':True}
 print(fn,count,flush=True)
(a.out/'cockpit-policy.json').write_text(json.dumps(report,indent=2)+'\n');print('DONE',len(policy),'unit entries',len(files),'model copies',flush=True)
