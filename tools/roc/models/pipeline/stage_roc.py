"""ROC model stage (ROC-only; never merged into the live model stage): every converted model's armory / battle / LOD .fam, .mat.json and .fat
files under stage/UserData/FAModels, plus roc-models.json = the models.json entries keyed by ROC card Name. A ROC Models version adds these
entries to the live models.json. usage: python3 stage_roc.py"""
import os,json,glob,shutil
H=os.path.dirname(os.path.abspath(__file__))+'/..';V=H+'/veh';S=H+'/stage/UserData/FAModels'
CARD={'cm34':'ROC CM-34','cm33':'ROC CM-33','cm22':'ROC CM-22','cm11':'ROC CM-11','antelope':'ROC Antelope','m41d':'ROC M41D',
      'tb2000':'ROC Thunderbolt-2000','kf6':'ROC Kung Feng VI','tk3':'ROC Tien Kung III','cm26':None,
      'cm21':'ROC CM-21','cm32':'ROC CM-32','lsw2':'ROC Land Sword II','f16v':'ROC F-16V','f5f':'ROC F-5F','m110a2':'ROC M110A2','uh60m':'ROC UH-60M',
      'ah64e':'ROC AH-64E','m60a3':'ROC M60A3 TTS','fck1':'ROC F-CK-1','c130':'ROC C-130HE','chx2':'ROC Chung Hsiang II'}   # Shawn's 26 Nov uploads   # CM-26 has no card yet (role unknown)
shutil.rmtree(H+'/stage',ignore_errors=True);os.makedirs(S)
models={};n=0
for s,card in CARD.items():
    st=f'm_roc_{s}'
    files=[f for f in glob.glob(f'{V}/models/{st}_*') if f.endswith(('.fam','.mat.json'))]+glob.glob(f'{V}/fat/{st}_*.fat')
    for f in files:shutil.copy(f,S);n+=1
    lods=[f'{st}_lo_static_{l}.fam' for l in ('l1','l2') if os.path.exists(f'{S}/{st}_lo_static_{l}.fam')]
    for need in (f'{st}_static.fam',f'{st}_lo_static.fam'):assert os.path.exists(f'{S}/{need}'),need
    if card:models[card]={'file':f'{st}_static.fam','battle':f'{st}_lo_static.fam','align':False,'lods':lods}
# infantry bodies (inf/, 25-26 Nov) and their add-on rules; the T91 rifle (t91/) and its hand rules
WT='/home/sam/tars/work/ba-dev/replicas/codex/work/roc-wt/tools/roc/models'
inf=glob.glob(H+'/inf/lod/roc_*.fas')+glob.glob(H+'/inf/fat/roc_*.fat')+[WT+'/infantry-bodies-roc.json']
t91=[f for f in glob.glob(H+'/t91/models/w_roc_t91*') if f.endswith(('.fam','.mat.json'))]+glob.glob(H+'/t91/fat/w_roc_t91*.fat')
for f in inf+t91:shutil.copy(f,S);n+=1
for r in json.load(open(WT+'/infantry-bodies-roc.json')):
    for f in r['lods']:assert os.path.exists(f'{S}/{f}'),f
shutil.copy(H+'/t91/rules.json',H+'/stage/roc-weapon-rules.json')
json.dump(models,open(H+'/stage/roc-models.json','w'),indent=1,ensure_ascii=False)
mb=sum(os.path.getsize(f'{S}/{f}') for f in os.listdir(S))/1e6
print('ROC stage',n,'files',round(mb,1),'MB;',len(models),'card entries:',', '.join(models))
