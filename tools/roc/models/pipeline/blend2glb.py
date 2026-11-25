# .blend -> GLB, relinking missing images by file name from the given folders. usage: blender -b IN.blend -P blend2glb.py -- OUT.glb DIR [DIR...]
import bpy,sys,os
a=sys.argv[sys.argv.index('--')+1:];out,dirs=a[0],a[1:]
idx={}
for d in dirs:
    for r,_,fs in os.walk(d):
        for f in fs:idx.setdefault(f.lower(),os.path.join(r,f))
fixed=miss=0
for im in bpy.data.images:
    if im.source!='FILE' or im.packed_file:continue
    p=bpy.path.abspath(im.filepath)
    if not os.path.exists(p):
        q=idx.get(os.path.basename(p.replace('\\','/')).lower())
        if q:im.filepath=q;im.reload();fixed+=1
        else:miss+=1;print('MISSING',im.name,p)
for o in list(bpy.data.objects):
    if o.type not in('MESH','EMPTY') or not o.visible_get():bpy.data.objects.remove(o,do_unlink=True)
print('BLEND2GLB relinked',fixed,'missing',miss,'meshes',sum(o.type=='MESH' for o in bpy.data.objects))
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_visible=True)
