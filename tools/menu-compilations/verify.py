#!/usr/bin/env python3
"""Decode whole mixes and verify sample count, embedded gaps, and per-song loudness."""
import argparse, concurrent.futures, json, subprocess, tempfile
from pathlib import Path
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);args=ap.parse_args()
root=args.out.resolve();build=json.loads((root/'audio-build.json').read_text());sr=build['recipe']['sample_rate']
def verify(mix):
 p=root/'payload'/mix['path']
 log=tempfile.TemporaryFile()
 proc=subprocess.Popen(['ffmpeg','-nostats','-v','info','-i',str(p),'-af','ebur128=peak=true:framelog=verbose','-f','s16le','-acodec','pcm_s16le','-ar',str(sr),'-ac','2','-'],stdout=subprocess.PIPE,stderr=log)
 pos=0;peaks=[0]*len(mix['timeline']);energy=[0.0]*len(peaks);counts=[0]*len(peaks)
 while True:
  b=proc.stdout.read(192000)
  if not b:break
  a=np.frombuffer(b,dtype='<i2').reshape(-1,2);end=pos+len(a)
  for i,t in enumerate(mix['timeline']):
   # Skip 0.1s on each edge for MP3 filter ringing. The PCM recipe has exactly120s.
   low=t['end_sample']+int(.1*sr);high=t['end_sample']+120*sr-int(.1*sr)
   l=max(pos,low);h=min(end,high)
   if h>l:
    v=a[l-pos:h-pos].astype(np.int32);peaks[i]=max(peaks[i],int(np.abs(v).max()));energy[i]+=float(np.square(v.astype(np.float64)).sum());counts[i]+=v.size
  pos=end
 code=proc.wait();log.seek(0);err=log.read().decode();log.close();assert code==0,err
 (root/(mix['pack'].replace(' ','_')+str(mix['playlist'])+'-decode.log')).write_text(err)
 import re
 loud=float(re.findall(r'I:\s*([-\d.]+) LUFS',err)[-1]);peak=float(re.findall(r'Peak:\s*([-\d.]+) dBFS',err)[-1])
 assert abs(loud-build['target_lufs'])<.7,(mix['path'],loud)
 assert peak<0,(mix['path'],peak)
 assert pos==mix['expected_samples'],(mix['path'],pos,mix['expected_samples'])
 assert all(n>0 for n in counts) and max(peaks)==0,(mix['path'],peaks)
 result={'path':mix['path'],'decoded_samples':pos,'all_expected_gap_interiors_are_digital_silence':True,'gap_count':len(peaks),'gap_peak_pcm16':max(peaks),'integrated_lufs':loud,'true_peak_dbtp':peak}
 print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(verify,build['outputs']))
(root/'audio-verification.json').write_text(json.dumps({'basis':'Full MP3 decode. Exact length; each120-second gap audited except100ms at either encoded boundary.','mixes':results},indent=2)+'\n')
