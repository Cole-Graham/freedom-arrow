#!/usr/bin/env python3
"""Build menu compilations from a supplied assets archive; no source audio in Git."""
import argparse, concurrent.futures, hashlib, json, re, subprocess, wave, zipfile
from pathlib import Path


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def measure(path):
    p = run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af',
             'loudnorm=I=-16:TP=-1:LRA=11:print_format=json','-f','null','-'])
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}', p.stderr)[-1])


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    recipe=json.loads(Path(__file__).with_name('recipe.json').read_text())
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    src=out/'source';src.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.archive) as z:
        ref=src/'USA-menu.mp3';ref.write_bytes(z.read(recipe['loudness_reference']))
        tracks={}
        for pack,cfg in recipe['packs'].items():
            for num in sorted({n for seq in cfg['playlists'] for n in seq}):
                prefix=cfg['theme_prefix'];bn=f'{prefix} theme {num:02d}.mp3'
                # The supplied GLA pack keeps 11 in Menu, not Battle.
                name=f'UserData/FAMusic/Packs/{pack}/Battle/{bn}'
                if name not in z.namelist():
                    name=f'UserData/FAMusic/Packs/{pack}/Menu/{prefix} theme {num:02d} (main menu).mp3'
                p=src/f'{prefix}-{num:02d}.mp3';p.write_bytes(z.read(name))
                tracks[(pack,num)]={'path':p,'archive_path':name,'sha256':sha(p)}
    reference_cache=out/'reference.json'
    cached=json.loads(reference_cache.read_text()) if reference_cache.exists() else None
    ref_stats=cached['measurement'] if cached and cached['sha256']==sha(ref) else measure(ref)
    reference_cache.write_text(json.dumps({'sha256':sha(ref),'measurement':ref_stats},indent=2)+'\n')
    target=float(ref_stats['input_i'])
    print('US reference',json.dumps(ref_stats),flush=True)
    norm=out/'normalized';norm.mkdir(exist_ok=True)
    def normalize(item):
        key,entry=item;p=entry['path']
        dest=norm/(p.stem+'.wav')
        cache=norm/(p.stem+'.json')
        if cache.exists():
            saved=json.loads(cache.read_text())
            if saved['sha256']==entry['sha256'] and dest.exists() and saved['wav_sha256']==sha(dest):
                print('REUSE',p.stem,flush=True);return key,saved
        if dest.exists():
            # Resume a completed normalization if final concatenation was interrupted.
            check=measure(dest)
            assert abs(float(check['input_i'])-target)<.5
            with wave.open(str(dest)) as w:frames=w.getnframes()
            result={**{k:v for k,v in entry.items() if k!='path'},'normalized':check,
                    'frames':frames,'wav':str(dest),'wav_sha256':sha(dest),
                    'normalization':'two-pass loudnorm; resumed completed PCM'}
            cache.write_text(json.dumps(result,indent=2)+'\n')
            print('RESUMED',p.stem,flush=True);return key,result
        analysis=run(['ffmpeg','-hide_banner','-nostats','-i',str(p),'-af',
                      f"loudnorm=I={target}:TP={recipe['true_peak_limit_dbtp']}:LRA=11:print_format=json",'-f','null','-'])
        stats=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',analysis.stderr)[-1])
        filt=(f"loudnorm=I={target}:TP={recipe['true_peak_limit_dbtp']}:LRA=11:"
              f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
              f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
              f"offset={stats['target_offset']}:linear=true:print_format=json")
        res=run(['ffmpeg','-y','-hide_banner','-nostats','-i',str(p),'-af',filt,
                 '-ar',str(recipe['sample_rate']),'-ac','2','-c:a','pcm_s16le',str(dest)])
        with wave.open(str(dest)) as w:frames=w.getnframes()
        check=measure(dest)
        result={**{k:v for k,v in entry.items() if k!='path'},'input':stats,
                'normalization':json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',res.stderr)[-1]),
                'normalized':check,'frames':frames,'wav':str(dest),'wav_sha256':sha(dest)}
        cache.write_text(json.dumps(result,indent=2)+'\n')
        print(p.stem,check['input_i'],'LUFS',check['input_tp'],'dBTP',flush=True)
        return key,result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        normalized=dict(pool.map(normalize,tracks.items()))
    silence=norm/'silence-120.wav'
    run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
         f"anullsrc=r={recipe['sample_rate']}:cl=stereo",'-t',str(recipe['gap_seconds']),
         '-c:a','pcm_s16le',str(silence)])
    payload=out/'payload';outputs=[]
    for pack,cfg in recipe['packs'].items():
        for idx,seq in enumerate(cfg['playlists'],1):
            dest=payload/'UserData/FAMusic/Packs'/pack/'Menu'/f'Menu - {pack} Compilation {idx}.mp3'
            dest.parent.mkdir(parents=True,exist_ok=True)
            concat=out/f'{cfg["theme_prefix"]}-{idx}.concat.txt';lines=[];timeline=[];frame=0
            for num in seq:
                t=normalized[(pack,num)]
                lines.extend([f"file '{t['wav']}'",f"file '{silence}'"])
                timeline.append({'theme':num,'start_sample':frame,'end_sample':frame+t['frames']})
                frame+=t['frames']+recipe['gap_seconds']*recipe['sample_rate']
            concat.write_text('\n'.join(lines)+'\n')
            run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),
                 '-c:a','libmp3lame','-b:a','320k','-ar',str(recipe['sample_rate']),
                 '-metadata',f'title={pack} Menu Compilation {idx}',str(dest)])
            outputs.append({'pack':pack,'playlist':idx,'order':seq,'path':str(dest.relative_to(payload)),
                            'sha256':sha(dest),'bytes':dest.stat().st_size,'expected_samples':frame,
                            'duration_seconds':frame/recipe['sample_rate'],'timeline':timeline})
            print('BUILT',pack,idx,round(frame/recipe['sample_rate'],3),'seconds',flush=True)
    result={'recipe':recipe,'reference':{'source':recipe['loudness_reference'],'sha256':sha(ref),'measurement':ref_stats},
            'target_lufs':target,'tracks':{f'{k[0]}/{k[1]:02d}':v for k,v in normalized.items()},'outputs':outputs}
    (out/'audio-build.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
