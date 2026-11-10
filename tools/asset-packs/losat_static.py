"""Remove LOSAT bone attachments while preserving every mesh segment byte for byte."""
import struct,io,json,hashlib,argparse
from pathlib import Path

def groups(raw):
 f=io.BytesIO(raw);assert f.read(4)==b'FAM1'
 def i():return struct.unpack('<i',f.read(4))[0]
 def s():return f.read(i()).decode()
 result=[]
 for _ in range(i()):
  name=s();segments=[]
  for _ in range(i()):
   start=f.tell();s();f.read(16);nv=i();assert nv>0;f.read(nv*32);ni=i();assert ni>0 and ni%3==0;f.read(ni*4);segments.append(raw[start:f.tell()])
  result.append((name,segments))
 assert f.tell()==len(raw)
 return result

def static(raw):
 old=groups(raw);assert {n for n,_ in old}=={'root','turret_0'}
 segments=[s for _,ss in old for s in ss]
 out=b'FAM1'+struct.pack('<i',1)+struct.pack('<i',4)+b'root'+struct.pack('<i',len(segments))+b''.join(segments)
 assert groups(out)==[('root',segments)]
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);report={}
 for stem in ['m_losat','m_losat_lo']:
  raw=(a.source/(stem+'.fam')).read_bytes();new=static(raw);name=stem+'_static';(a.output/(name+'.fam')).write_bytes(new);(a.output/(name+'.mat.json')).write_bytes((a.source/(stem+'.mat.json')).read_bytes());report[name]={'source_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(new).hexdigest(),'groups':['root'],'segment_bytes_unchanged':True,'sidecar_unchanged':True}
 (a.output/'static-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
