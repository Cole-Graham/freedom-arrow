# Godswords English set in their own voice (Osama 17 Nov 2026 17:49 PST: "B is the final candidate for the godswords").
# Voice: saved "FA Godswords 9A Haoran" pb1mQsOfvyjk6y2mBhom. Settings B: eleven_v4, stability 0, similarity 1.0, style 0.6, old_radio.
# Tags (Osama 17:3x 'very flat'): calm lines [confident] [relaxed], combat lines [urgent] [intense], then [heavy Chinese accent].
# Lines: shared + Godswords lines from lines.py (original set) and lines_callouts.py. Blood Wolves keep San Chi.
# Out: wolves/godswords/listen/{orig,callouts}/{Shared,Godswords}/<trigger>/NN.mp3; STT re-roll on non-speech sounds or wrong words; -16 LUFS.
import json,os,re,subprocess,sys,hashlib,uuid,urllib.request,urllib.error,time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'wolves')
import lines as L0, lines_callouts as L1
K=open(os.path.expanduser('~/.config/ba-codex/elevenlabs.key')).read().strip()
VID='pb1mQsOfvyjk6y2mBhom';CACHE='wolves/godswords/cache';OUT='wolves/godswords/listen';os.makedirs(CACHE,exist_ok=True)
def retag(tags):return '[urgent] [intense]' if '[urgent]' in tags else '[confident] [relaxed]'
J=[]
for src,mod in (('orig',L0),('callouts',L1)):
    for t,ls in mod.BW.items():
        for n,l in enumerate(ls,1):J.append(dict(path=f'{src}/Shared/{t}/{n:02d}.mp3',trigger=t,line=l,unit='both',src=src))
    for t,ls in mod.UNIQUE['Godswords'].items():
        for n,l in enumerate(ls,1):J.append(dict(path=f'{src}/Godswords/{t}/{n:02d}.mp3',trigger=t,line=l,unit='Godswords',src=src))
for j in J:tags,en=j['line'].split('|');j.update(en=en,text=f'{retag(tags)} [heavy Chinese accent] {en}')
def lufs(f):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',f,'-af','apad=pad_dur=1,ebur128','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.findall(r'I:\s+(-?[0-9.]+) LUFS',r)[-1])
def req(url,data,headers):
    for a in range(8):
        try:return urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers),timeout=180).read()
        except urllib.error.HTTPError as e:
            if e.code in (409,429,500,502,503):time.sleep(5*(a+1));continue
            raise RuntimeError(f'{e.code} {e.read()[:200]}')
def tts(text):
    b={'text':text,'model_id':'eleven_v4','voice_settings':{'stability':0.0,'similarity_boost':1.0,'style':0.6},'audio_effects':{'filter_preset_id':'old_radio'}}
    return req(f'https://api.elevenlabs.io/v1/text-to-speech/{VID}?output_format=mp3_44100_128',json.dumps(b).encode(),{'xi-api-key':K,'Content-Type':'application/json'})
def stt(f):
    b=uuid.uuid4().hex;data=open(f,'rb').read()
    body=(f'--{b}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1\r\n--{b}\r\nContent-Disposition: form-data; name="tag_audio_events"\r\n\r\ntrue\r\n--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()+data+f'\r\n--{b}--\r\n'.encode()
    t=json.loads(req('https://api.elevenlabs.io/v1/speech-to-text',body,{'xi-api-key':K,'Content-Type':'multipart/form-data; boundary='+b}))
    return t['text'],[w['text'] for w in t.get('words',[]) if w.get('type')=='audio_event']
norm=lambda s:set(re.sub(r'[^a-z0-9 ]','',s.lower().replace('-',' ')).split())
NUMS={'1688':{'one','six','eight'},'12':{'twelve'},'200':{'two','hundred'},'360':{'three','sixty'}}
def words_ok(en,heard):
    a,b=norm(en),norm(heard)
    for k,v in NUMS.items():
        if k in b:b|=v
    b|={''.join(x for x in w) for w in b}
    return len(a&b)/max(1,len(a))>=0.6
def run(j):
    c=f"{CACHE}/{hashlib.sha1(j['text'].encode()).hexdigest()[:16]}.mp3"
    for tries in range(1,4):
        if not os.path.exists(c):d=tts(j['text']);open(c+'.part','wb').write(d);os.replace(c+'.part',c)
        heard,ev=stt(c)
        if not ev and words_ok(j['en'],heard):break
        if tries<3:os.replace(c,c+f'.bad{tries}')
    out=f"{OUT}/{j['path']}";os.makedirs(os.path.dirname(out),exist_ok=True)
    g=-16.0-lufs(c)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',c,'-af',f'volume={g:.2f}dB,alimiter=limit=0.84:attack=1:release=40:level=false','-c:a','libmp3lame','-b:a','160k',out],check=True)
    return dict(j,heard=heard,events=ev,tries=tries,ok=words_ok(j['en'],heard),lufs=round(lufs(out),1))
with ThreadPoolExecutor(4) as ex:R=list(ex.map(run,J))
json.dump(R,open('wolves/godswords/results.json','w'),ensure_ascii=False,indent=0)
open(f'{OUT}/LINES.txt','w').write(''.join(f"{r['path']}\t{r['en']}\n" for r in R))
print('clips',len(R),'with events',[r['path'] for r in R if r['events']],'word mismatch',[(r['path'],r['en'],r['heard']) for r in R if not r['ok']],'re-rolled',sum(r['tries']>1 for r in R),'LUFS',min(r['lufs'] for r in R),max(r['lufs'] for r in R))
