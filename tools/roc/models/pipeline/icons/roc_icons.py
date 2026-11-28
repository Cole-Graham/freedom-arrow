"""ROC vehicle/aircraft card icons (Shawn 28 Nov 03:3x: "Can you change all these icons for none infantry unit? Using the way you did for
other nations' units"): white vanilla-style silhouettes rendered from each card's own ROC battle model, as the China icons
(pla-unit-icons-20261114: sil.py + style.py for ground and helicopters, side view, front right; air.py 3/4 view for fixed-wing).
Output: final/FA_PLA_VEH_ROC_<KEY>.png + _OUTLINE.png (ChinaUi seeds every FA_PLA_* resource). One Blender at a time here.
usage: python3 roc_icons.py [SLUG ...]"""
import sys,os,subprocess,shutil,json
D=os.path.dirname(os.path.abspath(__file__));M=D+'/../veh/models';B='/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender'
PY='/nix/store/00dsik9nawmyscdmpg0m64yfcfxpg548-python3-3.13.13-env/bin/python3'
GROUND=['cm11','cm12','cm21','cm32','cm33','cm34','antelope','m41d','tb2000','kf6','tk3','lsw2','m110a2','m60a3','hf2e','mtwv']
HELI=['uh60m','ah64e','ah1w','ec225'];AIR=['f16a','f16v','f5f','fck1','mirage','c130','chx2']
AZ={'tb2000':'180','ah64e':'180'}   # ah64e: the .fam faces backwards; the card entry turns it 180 (yaw)
for s in (sys.argv[1:] or GROUND+HELI+AIR):
    f=f'm_roc_{s}_lo_static'
    for ext in ('.fam','.mat.json'):
        if os.path.exists(f'{M}/{f}{ext}'):shutil.copy(f'{M}/{f}{ext}',f'{D}/fam/{f}{ext}')
    K='ROC_'+s.upper();fam=f'{D}/fam/{f}.fam'
    if s in AIR:
        sys.path.insert(0,D+'/../tools');from famread import read_fam
        nz=max(max(x['pos'][2::3]) for b,q in read_fam(fam) for x in q)
        subprocess.run([PY,f'{D}/air.py',K,fam,'35','40',str(nz)],cwd=D,check=True,env=dict(os.environ,CANOPY='none'),stdout=subprocess.DEVNULL)
    else:
        subprocess.run(['nice','-n','10',B,'-b','-P',f'{D}/sil.py','--',fam,f'{D}/out/FA_PLA_{K}_raw.png',AZ.get(s,'0'),'0'],check=True,capture_output=True)
        subprocess.run([PY,f'{D}/style.py',f'{D}/out/FA_PLA_{K}_raw.png',f'FA_PLA_{K}'],cwd=D,check=True,stdout=subprocess.DEVNULL)
        shutil.copy(f'{D}/out/FA_PLA_{K}-Label.png',f'{D}/final/FA_PLA_VEH_{K}.png');shutil.copy(f'{D}/out/outline_FA_PLA_{K}-Label.png',f'{D}/final/FA_PLA_VEH_{K}_OUTLINE.png')
    print('icon',s,flush=True)
print('ICONSDONE')
