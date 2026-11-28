"""F-CK-1 canopy (Shawn 28 Nov 03:0x, list 7: "The front cockpit is too transparent and not visible, please use the same material on the rear
cockpit and make sure it is visible"). The whole canopy and windscreen are one key (0.85, 0.90, 0.95, 0.15) on the vanilla F-16 glass
(cockpitDonor US_F16_Glass, base colour grey, alpha 0.05): it shows only where it reflects the sky, so the front half read as no glass.
FAModels 28 Nov: "donorAlpha" gives the entry its own copy of the donor glass with that alpha. 0.22 = a visible smoked canopy, same donor
material front and rear. All four .mat.json files. usage: python fck1_canopy_alpha.py [ALPHA]"""
import sys,os,json
M=os.path.dirname(os.path.abspath(__file__))+'/../veh/models';A=float(sys.argv[1]) if len(sys.argv)>1 else 0.22
for st in ('m_roc_fck1_static','m_roc_fck1_lo_static','m_roc_fck1_lo_static_l1','m_roc_fck1_lo_static_l2'):
    f=f'{M}/{st}.mat.json'
    if not os.path.exists(f):continue
    d=json.load(open(f));n=0
    for k,v in d.items():
        if v.get('cockpitDonor')=='US_F16_Glass':v['donorAlpha']=A;n+=1
    json.dump(d,open(f,'w'),indent=1);print(st,'canopy entries',n,'donorAlpha',A)
