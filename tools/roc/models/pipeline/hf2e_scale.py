"""HF-IIE size (Shawn 28 Nov 12:3x: "This model is too small, scale to the size similar to PAC-2 in vanilla game"). The model was 9.3 m long
(27 Nov: "HF-IIE size stays 9.3 m"); the vanilla Patriot PAC-2 tractor + launcher is 16.2 m (US_PATRIOT_PAC2 chassis z -7.95..8.25). x1.72 =
16.0 m, uniform, so the cab (2.4 m wide, windows 1.3-2.7 m high) is truck-sized and the drivers fit. Works on the four .fam files as they were
before the drivers (veh/x/hf2e/pre-drivers); run drivers/add_drivers.py hf2e afterwards (the seat is in the scaled frame). usage: python hf2e_scale.py"""
import os,sys,struct,shutil
import numpy as np
T=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,T);from famread import read_fam
M=T+'/../veh/models';B=T+'/../veh/x/hf2e/pre-drivers';BK=T+'/../veh/x/hf2e/pre-scale';os.makedirs(BK,exist_ok=True);K=1.72
def S(b):b=b.encode();return struct.pack('<i',len(b))+b
for st in ('m_roc_hf2e_static','m_roc_hf2e_lo_static','m_roc_hf2e_lo_static_l1','m_roc_hf2e_lo_static_l2'):
    if not os.path.exists(f'{BK}/{st}.fam'):shutil.copy(f'{B}/{st}.fam',f'{BK}/{st}.fam')
    V=read_fam(f'{BK}/{st}.fam');o=[b'FAM1',struct.pack('<i',len(V))]
    for bone,ss in V:
        o+=[S(bone),struct.pack('<i',len(ss))]
        for x in ss:
            P=(np.array(x['pos'],np.float32)*K).ravel().tolist();nv=len(P)//3
            o+=[S(x['tex']),struct.pack('<4f',*x['col']),struct.pack('<i',nv),struct.pack('<%df'%(3*nv),*P),struct.pack('<%df'%(3*nv),*x['nrm']),struct.pack('<%df'%(2*nv),*x['uv']),struct.pack('<i',len(x['idx'])),struct.pack('<%di'%len(x['idx']),*x['idx'])]
    open(f'{M}/{st}.fam','wb').write(b''.join(o));print(st,'x',K)
