"""Give a model's glass parts a vanilla glass material (FAModels cockpitDonor), keeping the old entry as the fallback FAModels uses if the
donor is not loaded. Shawn 27 Nov 15:0x: Kung Feng VI "remap ... following the model of 9K51 Grad, especially the material of glass", HF-IIE
"fix the glass", and "the vanilla F-16 as a transplant for all plane cockpits". Donors: RU_BM_21_Grad_glass (9K51 Grad, trucks), US_F16_Glass
(planes). usage: python set_glass_donor.py SLUG DONOR KEY_SUBSTRING [KEY_SUBSTRING ...]   (edits all four .mat.json files of the model)"""
import sys,json,glob,os,shutil
D=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';slug,donor,keys=sys.argv[1],sys.argv[2],sys.argv[3:]
for f in sorted(glob.glob(f'{D}/m_roc_{slug}_*static*.mat.json')):
    b=f+'.pre-donor'
    if not os.path.exists(b):shutil.copy(f,b)
    mj=json.load(open(b));n=0
    for k,v in list(mj.items()):
        if any(s in k for s in keys):
            fb={**{x:y for x,y in v.items() if x not in ('cockpitDonor','fallback')},'alpha':'BLEND'}
            if 'fallback' in v:fb=v['fallback']
            mj[k]={'cockpitDonor':donor,'fallback':fb};n+=1
    json.dump(mj,open(f,'w'),indent=1);print(os.path.basename(f),'glass entries ->',donor,n)
