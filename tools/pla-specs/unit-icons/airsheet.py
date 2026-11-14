import sys
from PIL import Image
L=[a.split(':') for a in sys.argv[2:]]
s2=Image.new('RGBA',(832+420,216*len(L)),(60,60,60,255))
for i,(n,r) in enumerate(L):
    s2.alpha_composite(Image.open(f'out/FA_PLA_{n}_preview.png'),(420,216*i))
    try:im=Image.open(f'ref/{r}.png').convert('RGBA');im.thumbnail((410,210));s2.alpha_composite(im,(0,216*i))
    except FileNotFoundError:pass
s2.save(sys.argv[1])
