"""Which tangent-space convention does a normal map use? A real normal map is the gradient of a height field, so its curl is ~0 only with
the right green sign. Compares the mean |curl| with OpenGL (+Y up, what glTF/FAModels expect) and DirectX (green flipped) readings.
Checked against the M60A3 maps, which were flipped DX->GL by hand (26 Nov) and read OpenGL. usage: python normal_convention.py FILE..."""
import sys
import numpy as np
from PIL import Image
def test(f):
    n=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)/127.5-1;nz=np.clip(n[...,2],0.2,1);gx=-n[...,0]/nz;r=[]
    for sgn in (1,-1):r.append(float(np.abs(-np.gradient(gx,axis=0)-np.gradient(-sgn*n[...,1]/nz,axis=1)).mean()))
    return r
if __name__=='__main__':
    for f in sys.argv[1:]:
        a,b=test(f);print('%-44s GL %.4f DX %.4f  %s'%(f.split('/')[-1],a,b,'DX' if b<a*0.85 else ('GL' if a<b*0.85 else '??')))
