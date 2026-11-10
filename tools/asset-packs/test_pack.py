import importlib.util,json,struct,tempfile,zipfile
from pathlib import Path
from build import build
from apply_model_update import apply

def fam(tex):
    s=lambda t:struct.pack('<i',len(t))+t.encode()
    return b'FAM1'+struct.pack('<i',1)+s('')+struct.pack('<i',1)+s(tex)+struct.pack('<4f',1,1,1,1)+struct.pack('<i',3)+bytes(3*32)+struct.pack('<i',3)+struct.pack('<3i',0,1,2)
with tempfile.TemporaryDirectory() as t:
    r=Path(t);game=r/'source';d=game/'UserData/FAModels';d.mkdir(parents=True);(game/'Mods').mkdir();(game/'Mods/FAModels.dll').write_bytes(b'model-loader');(game/'Mods/FAMusic.dll').write_bytes(b'music-loader')
    (d/'a.fam').write_bytes(fam('a.png'));(d/'a_lo.fam').write_bytes(fam('a.png'))
    for f in ['a.png','a_n.png','a_mask.png','a.mat.json']:(d/f).write_bytes(b'asset')
    (d/'unused-PLA.fam').write_bytes(b'not included');(d/'models.json').write_text(json.dumps({'Live':{'file':'a.fam','battle':'a_lo.fam'},'PLA Test':{'file':'unused-PLA.fam'}}))
    m=game/'UserData/FAMusic';(m/'Packs/USA/Menu').mkdir(parents=True);(m/'Packs/USA/Menu/theme.mp3').write_bytes(b'music');(m/'Voice/US').mkdir(parents=True);(m/'Voice/US/line.mp3').write_bytes(b'voice');(m/'pack.txt').write_text('Russia\n');(m/'music-history.txt').write_text('private state')
    cfg=r/'cfg.json';cfg.write_text(json.dumps({'id':'test.assets','name':'Test assets','units':['Live'],'notes':[],'music_roots':['UserData/FAMusic/Packs','UserData/FAMusic/Voice']}))
    full=r/'assets.bamod';result=build(game,full,'0.1.0',cfg)
    install=r/'installed';install.mkdir()
    with zipfile.ZipFile(full) as z:
        assert json.loads(z.read('mod.json'))['type']=='mod'
        assert not any('PLA' in n or '/constants/' in n or n.endswith(('pack.txt','music-history.txt')) for n in z.namelist())
        assert all('UserData/FAModels/'+f in z.namelist() for f in ['a.fam','a_lo.fam','a_n.png','a_mask.png','a.mat.json'])
        for n in z.namelist():
            if n.startswith(('Mods/','UserData/')):p=install/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    (install/'UserData/FAMusic/pack.txt').write_text('Russia\n');mp=install/'UserData/FAModels/models.json';mapping=json.loads(mp.read_text());mapping['Unrelated']={'file':'other.fam'};mp.write_text(json.dumps(mapping))
    (d/'a.png').write_bytes(b'changed image');delta=r/'delta.zip';result=build(game,delta,'0.1.1',cfg,full.with_suffix('.manifest.json'));assert result['changed_files']==1
    apply(delta,install);assert (install/'UserData/FAModels/a.png').read_bytes()==b'changed image';assert json.loads(mp.read_text())['Unrelated']=={'file':'other.fam'};assert (install/'UserData/FAMusic/pack.txt').read_text()=='Russia\n'
    try:apply(delta,install)
    except AssertionError:pass
    else:raise AssertionError('Out-of-order base accepted')
    print('PASS: full manager-format asset archive, dependency closure, no PLA/balance/state, one-file delta, merged mappings, playlist preservation, base guard')
