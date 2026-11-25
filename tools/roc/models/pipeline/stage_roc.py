"""ROC model stage (ROC-only; never merged into the live model stage): every converted model's armory / battle / LOD .fam, .mat.json and .fat
files under stage/UserData/FAModels, plus roc-models.json = the models.json entries keyed by ROC card Name. A ROC Models version adds these
entries to the live models.json. usage: python3 stage_roc.py"""
import os,json,glob,shutil
H=os.path.dirname(os.path.abspath(__file__))+'/..';V=H+'/veh';S=H+'/stage/UserData/FAModels'
CARD={'cm34':'ROC CM-34','cm33':'ROC CM-33','cm22':'ROC CM-22','cm11':'ROC CM-11','antelope':'ROC Antelope','m41d':'ROC M41D',
      'tb2000':'ROC Thunderbolt-2000','kf6':'ROC Kung Feng VI','tk3':'ROC Tien Kung III','cm26':None,
      'cm21':'ROC CM-21','cm32':'ROC CM-32','lsw2':'ROC Land Sword II','f16v':'ROC F-16V','f5f':'ROC F-5F','m110a2':'ROC M110A2','uh60m':'ROC UH-60M'}   # CM-26 has no card yet (role unknown)
shutil.rmtree(H+'/stage',ignore_errors=True);os.makedirs(S)
models={};n=0
for s,card in CARD.items():
    st=f'm_roc_{s}'
    files=[f for f in glob.glob(f'{V}/models/{st}_*') if f.endswith(('.fam','.mat.json'))]+glob.glob(f'{V}/fat/{st}_*.fat')
    for f in files:shutil.copy(f,S);n+=1
    lods=[f'{st}_lo_static_{l}.fam' for l in ('l1','l2') if os.path.exists(f'{S}/{st}_lo_static_{l}.fam')]
    for need in (f'{st}_static.fam',f'{st}_lo_static.fam'):assert os.path.exists(f'{S}/{need}'),need
    if card:models[card]={'file':f'{st}_static.fam','battle':f'{st}_lo_static.fam','align':False,'lods':lods}
json.dump(models,open(H+'/stage/roc-models.json','w'),indent=1,ensure_ascii=False)
mb=sum(os.path.getsize(f'{S}/{f}') for f in os.listdir(S))/1e6
print('ROC stage',n,'files',round(mb,1),'MB;',len(models),'card entries:',', '.join(models))
