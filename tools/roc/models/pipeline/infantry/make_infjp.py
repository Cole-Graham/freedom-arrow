"""ROC body "infjp" (Shawn 27 Nov 18:0x): "Change the body of Mech. Riflemen T112 by the body of Mech. Riflemen, but keep the helmet and face" and
"Use the helmet of SF snipers to combine with the body of mech. riflemen to form the new infantry model for SF Scout". ROC Infantry (Mech. Riflemen)
body with its own head (SM_twhead) and helmet (SM_vestHeadGear.001) removed; in their place the Infantry 2 (T112 / SF Snipers) head, i.e. the
JGSF_soldier_01 faces with the japan_gunner_heads material, and its M1 helmet, scaled so the face is as tall as the old one and moved so its neck
sits where the old neck was. Writes 'ROC Infantry JPhead.blend' beside the ROC Infantry source. usage: blender -b -P make_infjp.py"""
import bpy,bmesh
from mathutils import Vector,Matrix
X='/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125/x'
# 1. in the Infantry 2 file: bake every parent/object transform into the head and helmet meshes, so they keep their places when appended alone
bpy.ops.wm.open_mainfile(filepath=X+'/ROC Infantry 2/ROC Infantry 2/ROC SF 3 shoulders.blend')
for n in ('JGSF_soldier_01','M1'):
    o=bpy.data.objects[n];o.data=o.data.copy();o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
    print('BAKED',n,[round(min((v.co[i] for v in o.data.vertices)),3) for i in range(3)],[round(max((v.co[i] for v in o.data.vertices)),3) for i in range(3)])
bpy.ops.wm.save_as_mainfile(filepath='/tmp/b394wrap/jp_baked.blend')
bpy.ops.wm.open_mainfile(filepath=X+'/ROC Infantry/ROC Infantry/ROC Infantry.blend')
def bbox(o):
    P=[o.matrix_world@v.co for v in o.data.vertices];return Vector([min(p[i] for p in P) for i in range(3)]),Vector([max(p[i] for p in P) for i in range(3)])
old=bpy.data.objects['SM_twhead'];omn,omx=bbox(old)
for n in ('SM_twhead','SM_vestHeadGear.001'):bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
with bpy.data.libraries.load('/tmp/b394wrap/jp_baked.blend') as (src,dst):dst.objects=['JGSF_soldier_01','M1']
head,helm=dst.objects
for o in (head,helm):bpy.context.collection.objects.link(o)
head.name,helm.name='JP_head','JP_helmet'
# keep only the head material's faces
bpy.context.view_layer.objects.active=head;head.data=head.data.copy()
bm=bmesh.new();bm.from_mesh(head.data);hi=[i for i,m in enumerate(head.data.materials) if m and 'heads' in m.name][0]
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=hi],context='FACES');bm.verts.ensure_lookup_table()
for v in [v for v in bm.verts if not v.link_faces]:bm.verts.remove(v)
bm.to_mesh(head.data);bm.free()
hmn,hmx=bbox(head)
s=(omx.z-omn.z)/(hmx.z-hmn.z)              # same face+neck height as the old head
pivot=Vector(((hmn.x+hmx.x)/2,(hmn.y+hmx.y)/2,hmn.z));target=Vector(((omn.x+omx.x)/2,(omn.y+omx.y)/2,omn.z))
M=Matrix.Translation(target)@Matrix.Scale(s,4)@Matrix.Translation(-pivot)
for o in (head,helm):o.matrix_world=M@o.matrix_world
nmn,nmx=bbox(head);hm,hx=bbox(helm)
print('INFJP scale %.2f head z %.1f..%.1f (old %.1f..%.1f) helmet z %.1f..%.1f verts head %d helmet %d'%(s,nmn.z,nmx.z,omn.z,omx.z,hm.z,hx.z,len(head.data.vertices),len(helm.data.vertices)))
bpy.ops.wm.save_as_mainfile(filepath=X+'/ROC Infantry/ROC Infantry/ROC Infantry JPhead.blend');print('SAVED')
