# F-CK-1: drop stores, landing gear and display props; orient nose +X / up +Z like the F-2 GLB; link TX_IDF_* colour/normal maps.
# usage: blender -b -P plane_prep.py -- IN.glb OUT.glb TEXROOT|- DROP_REGEX
import bpy,sys,re,os,glob,numpy as np,mathutils as mu
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
DROP=a[3]
n=0
for o in [o for o in bpy.data.objects if o.type=='MESH' and re.search(DROP,o.name)]:bpy.data.objects.remove(o,do_unlink=True);n+=1
ms=[o for o in bpy.data.objects if o.type=='MESH'];print('DROPPED',n,'KEPT',len(ms))
for o in ms:
    mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw
for o in [o for o in bpy.data.objects if o.type!='MESH']:bpy.data.objects.remove(o,do_unlink=True)
P=np.array([tuple(o.matrix_world@v.co) for o in ms for v in o.data.vertices]);mn,mx=P.min(0),P.max(0);ext=mx-mn
L=int(np.argmax(ext));lo,hi=mn[L],mx[L];span=hi-lo
others=[i for i in range(3) if i!=L]
def width(s):q=P[s];return float(np.ptp(q[:,others[0]])+np.ptp(q[:,others[1]]))
nose=1 if width(P[:,L]>hi-0.1*span)<width(P[:,L]<lo+0.1*span) else -1
up=others[int(np.argmin(ext[others]))]
# up direction: the canopy (IDF_cop) sits above the fuselage centre line
cop=[o for o in ms if re.search(r'(?i)cop|cockpit|canopy|glass|cpt',o.name)]
c=np.array([tuple(o.matrix_world@v.co) for o in cop for v in o.data.vertices]).mean(0) if cop else (mn+mx)/2
upsign=1 if c[up]>=(mn[up]+mx[up])/2 else -1
if os.environ.get('UPSIGN'):upsign=int(os.environ['UPSIGN'])
X=np.zeros(3);X[L]=nose;Z=np.zeros(3);Z[up]=upsign;Y=np.cross(Z,X)
M=mu.Matrix([list(X),list(Y),list(Z)]).to_4x4()   # rows: new axes in old coordinates -> rotate old into new
for o in ms:o.matrix_world=M@o.matrix_world
print('ORIENT long',L,'nose',nose,'up',up,'sign',upsign,'ext',ext.round(1).tolist())
files={os.path.basename(f).lower():f for f in glob.glob(a[2]+'/**/*.png',recursive=True)} if a[2]!='-' else {}
def tex(mat,kind):
    for k in (f'tx_{mat}_{kind}.png',f'tx_{mat}_001_{kind}.png'):
        if k.lower() in files:return files[k.lower()]
for m in bpy.data.materials:
    key=m.name.split('.')[0];bc=tex(key,'BaseColor') or tex(key,'Diffuse')
    if not bc:continue
    m.use_nodes=True;nt=m.node_tree;b=next(x for x in nt.nodes if x.type=='BSDF_PRINCIPLED')
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(bc);nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    nr=tex(key,'Normal')
    if nr:
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=bpy.data.images.load(nr);tn.image.colorspace_settings.name='Non-Color';nm=nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    print('TEX',m.name,os.path.basename(bc),'normal' if nr else '')
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB')
