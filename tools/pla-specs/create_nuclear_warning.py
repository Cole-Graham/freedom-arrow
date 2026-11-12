"""Original DF-31 draft: synthesized two-tone cue + generic eSpeak announcement.

No audio is taken from the Red Alert reference. Replace the resulting WAV with
the final commissioned sound at the same package path. eSpeak is a build tool;
neither it nor its voice data is shipped or needed on the player's computer.
"""
import argparse, array, hashlib, json, math, pathlib, subprocess, tempfile, wave
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--espeak',default='espeak-ng');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'releases/0.6/source/UserData/FreedomArrow/audio/df31-nuclear-warning.wav'
rate=22050
with tempfile.TemporaryDirectory() as tmp:
    voice=pathlib.Path(tmp)/'voice.wav'
    subprocess.run([a.espeak,'-v','en-us','-s','145','-p','32','-a','100','-w',str(voice),'Warning. Nuclear missile launched.'],check=True)
    with wave.open(str(voice)) as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==rate
        speech=array.array('h',w.readframes(w.getnframes()))
    # Two rising and falling tones, then the phrase over a quiet two-tone bed.
    offset=int(1.45*rate); n=offset+len(speech)+int(.3*rate)
    samples=[]
    for i in range(n):
        t=i/rate
        envelope=min(1,t/.03,max(0,(n/rate-t)/.08))
        pulse=min(1,(t%0.4)/.025,(.4-t%0.4)/.04)
        f=540 if int(t/.4)%2==0 else 760
        alarm=(.16 if t<1.4 else .025)*math.sin(2*math.pi*f*t)*max(0,pulse)*envelope
        v=(speech[i-offset]/32768*.80 if offset<=i<offset+len(speech) else 0)+alarm
        samples.append(v)
    peak=max(map(abs,samples)); gain=min(1,.70/peak)
    pcm=array.array('h',(round(x*gain*32767) for x in samples))
    out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm.tobytes())
    receipt={'sound':'original synthesized draft','phrase':'Warning. Nuclear missile launched.','reference_only':'https://www.youtube.com/watch?v=6Ji6d-AmPHY','copied_audio':False,'seconds':n/rate,'peak_dbfs':20*math.log10(peak*gain),'rms_dbfs':20*math.log10(math.sqrt(sum((x*gain)**2 for x in samples)/n)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'runtime_gain':'0.30 times existing ballistic alarm volume; game warning bus','native_listening_test':False}
    out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
