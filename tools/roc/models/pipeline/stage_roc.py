"""ROC model stage (ROC-only; never merged into the live model stage): every converted model's armory / battle / LOD .fam, .mat.json and .fat
files under stage/UserData/FAModels, plus roc-models.json = the models.json entries keyed by ROC card Name. A ROC Models version adds these
entries to the live models.json. usage: python3 stage_roc.py"""
import os,json,glob,shutil
H=os.path.dirname(os.path.abspath(__file__))+'/..';V=H+'/veh';S=H+'/stage/UserData/FAModels'
CARD={'cm34':'ROC CM-34','cm33':'ROC CM-33',   # CM-33 back 27 Nov 18:4x as the Mk19 variant of the CM-32 (cm32_kitbash.py cm33)
     'cm11':'ROC CM-11','antelope':'ROC Antelope','m41d':'ROC M41D',
      'tb2000':'ROC Thunderbolt-2000','kf6':'ROC Kung Feng VI','tk3':'ROC Tien Kung III',   # CM-26 removed from the ROC set (Shawn 27 Nov 00:0x)
      'cm21':'ROC CM-21','cm32':'ROC CM-32','lsw2':'ROC Land Sword II','f16v':'ROC F-16V','f5f':'ROC F-5F','m110a2':'ROC M110A2','uh60m':'ROC UH-60M',
      'ah64e':'ROC AH-64E','m60a3':'ROC M60A3 TTS','fck1':'ROC F-CK-1','c130':'ROC C-130HE','chx2':'ROC Chung Hsiang II',   # Shawn's 26 Nov uploads
      'f16a':'ROC F-16A','mirage':'ROC Mirage 2000-5',
      'hf2e':'ROC Hsiung Feng IIE',
      'cm12':'ROC CM-12',   # Shawn 27 Nov 00:0x: the CM-12.zip model (file CM11.fbx) is the right CM-12
      'ec225':'ROC EC225'}   # Shawn 27 Nov 00:2x, ROC SAR paint (livery_ec225.py)
shutil.rmtree(H+'/stage',ignore_errors=True);os.makedirs(S)
models={};n=0
for s,card in CARD.items():
    st=f'm_roc_{s}'
    fams=[f for f in glob.glob(f'{V}/models/{st}_*') if f.endswith(('.fam','.mat.json'))]
    for f in fams:shutil.copy(f,S);n+=1
# textures: only the .fat files a staged .fam uses (with their _n/_mask maps and @Scheme sets); 27 Nov: the CM-32/CM-33 rebuilds left old maps behind
import sys;sys.path.insert(0,H+'/tools');from famread import read_fam
used={x['tex'][:-4] for f in glob.glob(S+'/*.fam') for b,ss in read_fam(f) for x in ss if x['tex']}
for f in glob.glob(f'{V}/fat/m_roc_*.fat'):
    b=os.path.basename(f)[:-4].split('@')[0]
    for suf in ('_n','_mask'):
        if b.endswith(suf):b=b[:-len(suf)]
    if b in used:shutil.copy(f,S);n+=1
for s,card in CARD.items():
    st=f'm_roc_{s}'
    lods=[f'{st}_lo_static_{l}.fam' for l in ('l1','l2') if os.path.exists(f'{S}/{st}_lo_static_{l}.fam')]
    for need in (f'{st}_static.fam',f'{st}_lo_static.fam'):assert os.path.exists(f'{S}/{need}'),need
    if card:models[card]={'file':f'{st}_static.fam','battle':f'{st}_lo_static.fam','align':False,'lods':lods}
# infantry bodies (inf/, 25-26 Nov) and their add-on rules; the T91 rifle (t91/) and its hand rules
WT='/home/sam/tars/work/ba-dev/replicas/codex/work/roc-wt/tools/roc/models'
BODY={l.rsplit('_',1)[0]+'_' for r in json.load(open(WT+'/infantry-bodies-roc.json')) for l in r['lods']}   # only bodies a rule uses (27 Nov: SF Scout -> roc_sf4)
inf=[f for f in glob.glob(H+'/inf/lod/roc_*.fas')+glob.glob(H+'/inf/fat/roc_*.fat') if any(os.path.basename(f).startswith(b) for b in BODY)]+[WT+'/infantry-bodies-roc.json']
t91=[f for f in glob.glob(H+'/t91/models/w_roc_*') if f.endswith(('.fam','.mat.json'))]+glob.glob(H+'/t91/fat/w_roc_*.fat')   # T91 + Kestrel-1 (27 Nov)
for f in inf+t91:shutil.copy(f,S);n+=1
for r in json.load(open(WT+'/infantry-bodies-roc.json')):
    for f in r['lods']:assert os.path.exists(f'{S}/{f}'),f
shutil.copy(H+'/t91/rules.json',H+'/stage/roc-weapon-rules.json')
# Shawn 27 Nov 14:4x in game: the CM-34 faced backwards (turret at the front); the M41D was ~70 % of its size (5.8 m with the gun; real M41 8.2 m
# with the gun, 3.2 m wide; model 2.3 m wide). FAModels entries take yaw (degrees) and scale for both the Arsenal and battle models.
# Shawn 27 Nov 15:0x: "CM-22 Model is too poor, replace it by the model of CM-21" (same M113-family hull; the CM-22's own files stay unshipped).
if 'ROC CM-21' in models:models['ROC CM-22']=dict(models['ROC CM-21'])
for card,extra in {'ROC CM-34':{'yaw':180},'ROC M41D':{'scale':1.4}}.items():
    if card in models:models[card].update(extra)
json.dump(models,open(H+'/stage/roc-models.json','w'),indent=1,ensure_ascii=False)
# paint schemes (Shawn 26 Nov: "2 basecolor skins for Mirage 2000, make them options"): <tex>@<Scheme>.fat came with the fat/ glob above;
# paint-schemes-roc.json is an add-on read by the ROC-branch FAModels; button swatches = 256x144 crop of the armory colour texture centre
from PIL import Image
PAINT={'ROC Mirage 2000-5':('m_roc_mirage_static_tex0',['GreyCamo']),
       'ROC Hsiung Feng IIE':('m_roc_hf2e_static_tex4',['Camo']),
       'ROC CM-34':('m_roc_cm34_static_tex0',['Dust','Mosaic']),
       'ROC CM-32':('m_roc_cm34_static_tex0',['Dust','Mosaic']),'ROC CM-33':('m_roc_cm34_static_tex0',['Dust','Mosaic'])}   # Shawn 27 Nov 02:2x: CM-32 with the CM-34 sets (camo3d.py blocks)   # Shawn 27 Nov 02:1x: the SHAMO (desert) and MAISAIKE (mosaic) sets from his folder   # Shawn 26 Nov 21:5x: optional Woodland camo (camo_hf2e.py)
os.makedirs(S+'/paint',exist_ok=True)
def swatch(f):
    im=Image.open(f).convert('RGB');w,h=im.size;cw,ch=int(w*0.5),int(w*0.5*144/256);x,y=(w-cw)//2,(h-ch)//2;return im.crop((x,y,x+cw,y+ch)).resize((256,144),Image.LANCZOS)
pf=lambda u:''.join(c if c.isalnum() else '_' for c in u)
for u,(tex,schemes) in PAINT.items():
    swatch(f'{V}/models/{tex}.png').save(f'{S}/paint/{pf(u)}@Default.png')
    for sc in schemes:
        assert os.path.exists(f'{S}/{tex}@{sc}.fat'),(tex,sc);swatch((glob.glob(f'{V}/x/*/scheme*/out/{tex}@{sc}.png')+glob.glob(f'{V}/x/*/camo_maps/{tex}@{sc}.png')+glob.glob(f'{V}/x/*/schemes/{tex}@{sc}.png'))[0]).save(f'{S}/paint/{pf(u)}@{sc}.png')
json.dump({u:sc for u,(t,sc) in PAINT.items()},open(S+'/paint-schemes-roc.json','w'),indent=1)
mb=sum(os.path.getsize(f'{S}/{f}') for f in os.listdir(S))/1e6
print('ROC stage',n,'files',round(mb,1),'MB;',len(models),'card entries:',', '.join(models))
