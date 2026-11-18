# Word-for-word checked generation (Osama 18 Nov 2026 01:3x PST: "let's regenerate it ... word for word check it all").
# 16-17 Nov the clips were only checked for non-speech sounds; 56 came back with the line doubled ("收到，收到，飞过去") and 9 with extra words
# ("Cool。", "Danke."). Every clip must now pass: speech-to-text (scribe_v1, audio events tagged) has no audio events, no Latin words, the same
# number of syllables as the script, and at most max(1, n//5) syllables that differ in pinyin (radio-filtered speech gives STT homophones such as
# 步兵/不平; those are not re-rolled). A failing clip is regenerated (new take) up to TAKES times; the passing take is levelled to -16 LUFS.
# usage (from work/china-voices): python v2/gen_checked.py [--check-only]
import json,os,re,subprocess,sys,uuid,urllib.request,urllib.error,time,hashlib
from concurrent.futures import ThreadPoolExecutor
from pypinyin import lazy_pinyin
sys.path[:0]=['v2','.']
import build_jobs as B
K=open(os.path.expanduser('~/.config/ba-codex/elevenlabs.key')).read().strip()
V={'Philip':'exurTFaGNF2gnRcPNH8I','Kang':'8G6jifm9f1BhHXadvwOt','Brody':'TbEd6wZh117FdOyTGS3q'}
STAB=float(os.environ.get('FA_STAB','0'));FIRST=int(os.environ.get('FA_FIRST','0'));ONLY=os.environ.get('FA_ONLY');CACHE='v2/cache';OUT='v2/listen';STT='v2/stt_checked.json';TAKES=6
stt_done=json.load(open(STT)) if os.path.exists(STT) else json.load(open('v2/stt_final.json'))   # seeded: 16 Nov transcripts of the shipped clips
def H(s):return re.sub(r'[^\u4e00-\u9fff]','',s or '')
from check2 import check
def check_v1(zh,t):
    if not t or 'error' in t:return False,'no transcript'
    if t.get('events'):return False,'events '+','.join(t['events'])
    if re.search(r'[A-Za-z]{2,}',t.get('text','')):return False,'latin words'
    a,b=lazy_pinyin(H(zh)),lazy_pinyin(H(t['text']))
    if len(a)!=len(b):return False,f'{len(b)} syllables, script {len(a)}'
    diff=sum(x!=y for x,y in zip(a,b))
    return (diff<=max(1,len(a)//5)),f'{diff} syllables differ'
def stt(path):
    b=uuid.uuid4().hex;data=open(path,'rb').read()
    body=(f'--{b}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1\r\n--{b}\r\nContent-Disposition: form-data; name="tag_audio_events"\r\n\r\ntrue\r\n--{b}\r\nContent-Disposition: form-data; name="language_code"\r\n\r\nzho\r\n--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()+data+f'\r\n--{b}--\r\n'.encode()
    for a in range(5):
        try:
            r=urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text',data=body,headers={'xi-api-key':K,'Content-Type':'multipart/form-data; boundary='+b})
            t=json.load(urllib.request.urlopen(r,timeout=120))
            return {'text':t['text'],'events':[w['text'] for w in t.get('words',[]) if w.get('type')=='audio_event']}
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503):time.sleep(5*(a+1));continue
            return {'error':e.code}
        except Exception:time.sleep(3)
    return {'error':'retries'}
def tts(voice,text,take):
    c=f"{CACHE}/{hashlib.sha1((f'{voice}|{text}|v4|old_radio'+(f'|s{STAB}' if STAB else '')).encode()).hexdigest()[:16]}"+(f'_t{take}' if take else '')+'.mp3'
    if os.path.exists(c) and os.path.getsize(c)>1000:return c
    body=json.dumps({'text':text,'model_id':'eleven_v4','voice_settings':{'stability':STAB,'similarity_boost':0.75},'audio_effects':{'filter_preset_id':'old_radio'}}).encode()
    for a in range(5):
        try:
            req=urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{V[voice]}?output_format=mp3_44100_128",data=body,headers={'xi-api-key':K,'Content-Type':'application/json'})
            d=urllib.request.urlopen(req,timeout=120).read();open(c+'.part','wb').write(d);os.replace(c+'.part',c);return c
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503):time.sleep(4*(a+1));continue
            raise RuntimeError(f'TTS {e.code} {e.read()[:200]}')
        except Exception:time.sleep(3)
    raise RuntimeError('TTS retries')
def lufs(f):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',f,'-af','apad=pad_dur=1,ebur128','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.findall(r'I:\s+(-?[0-9.]+) LUFS',r)[-1])
def level(src,dst):
    os.makedirs(os.path.dirname(dst),exist_ok=True);g=-16.0-lufs(src)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',src,'-af',f'volume={g:.2f}dB,alimiter=limit=0.84:attack=1:release=40:level=false','-c:a','libmp3lame','-b:a','160k',dst],check=True)
def run(j):
    out=f"{OUT}/{j['path']}"
    if os.path.exists(out):
        t=stt_done.get(j['path']) or stt(out);stt_done[j['path']]=t
        ok,why=check(j['zh'],t)
        if ok:return dict(path=j['path'],status='kept',why=why,heard=t.get('text'))
        if CHECK_ONLY:return dict(path=j['path'],status='FAIL',why=why,heard=t.get('text'),zh=j['zh'])
        first=max(1,FIRST)   # the shipped take failed: new takes only
    else:
        if CHECK_ONLY:return dict(path=j['path'],status='MISSING',zh=j['zh'])
        first=FIRST
    tries=[]
    for take in range(first,first+TAKES):
        raw=tts(j['voice'],j['text'],take);tmp=f'/tmp/t1571/cv_{uuid.uuid4().hex}.mp3';level(raw,tmp)
        t=stt(tmp);ok,why=check(j['zh'],t);tries.append(f"{take}:{t.get('text')}({why})")
        if ok:
            os.makedirs(os.path.dirname(out),exist_ok=True);os.replace(tmp,out);stt_done[j['path']]=t
            return dict(path=j['path'],status='new' if first==0 else 'regenerated',take=take,heard=t.get('text'),zh=j['zh'],tries=tries)
        os.remove(tmp)
    return dict(path=j['path'],status='FAIL',zh=j['zh'],tries=tries)
CHECK_ONLY='--check-only' in sys.argv
if __name__=='__main__':
    J=list(B.jobs())
    if ONLY:keep=set(open(ONLY).read().split());J=[j for j in J if j['path'] in keep]
    # FA_ONE_TAG: three style tags on a short line make eleven_v4 say the line twice (停车待命 -> 停车待命，停车待命 in 12 of 12 takes, 18 Nov);
    # the first tag alone gave one clean reading in 3 of 3 tests. Used only for the lines that failed with all tags.
    if os.environ.get('FA_NO_TAG'):J=[dict(j,text=j['zh']) for j in J]   # last resort: plain text, voice and filter unchanged
    if os.environ.get('FA_ONE_TAG'):J=[dict(j,text=j['text'].split(']')[0]+'] '+j['zh']) for j in J]
    with ThreadPoolExecutor(4) as ex:R=list(ex.map(run,J))
    json.dump(stt_done,open(STT,'w'),ensure_ascii=False,indent=0)
    json.dump(R,open(os.environ.get('FA_OUT','v2/checked.json'),'w'),ensure_ascii=False,indent=0)
    import collections;print(collections.Counter(r['status'] for r in R))
    for r in R:
        if r['status'] in ('FAIL','MISSING'):print(r)
