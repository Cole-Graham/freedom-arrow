from pathlib import Path
import struct,io,numpy as np

def read(path):
 f=io.BytesIO(Path(path).read_bytes());assert f.read(4)==b'FAM1'
 def num():return struct.unpack('<i',f.read(4))[0]
 def st():return f.read(num()).decode()
 out=[]
 for _ in range(num()):
  bone=st()
  for _ in range(num()):
   tex=st();col=struct.unpack('<4f',f.read(16));n=num();pos=np.frombuffer(f.read(n*12),'<f4').reshape(-1,3).copy();norm=np.frombuffer(f.read(n*12),'<f4').reshape(-1,3).copy();uv=np.frombuffer(f.read(n*8),'<f4').reshape(-1,2).copy();ind=np.frombuffer(f.read(num()*4),'<i4').reshape(-1,3).copy();out.append(dict(bone=bone,tex=tex,col=col,pos=pos,norm=norm,uv=uv,ind=ind))
 assert f.tell()==len(f.getvalue());return out

def components(d):
 # Welding for connectivity only; output normals and UV seams remain intact.
 P=d['pos'];_,inv=np.unique(np.round(P,4),axis=0,return_inverse=True);par=list(range(inv.max()+1))
 def find(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for a,b,c in inv[d['ind']]:
  a=find(a);b=find(b);c=find(c);par[b]=a;par[c]=a
 ids=np.array([find(int(i)) for i in inv]);tri=ids[d['ind'][:,0]]
 return tri
