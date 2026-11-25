# 3ds Max file -> GLB (io_scene_max 1.9.2), keeping the textures the importer links. usage: blender -b -P max2glb.py -- IN.max OUT.glb
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/blue-dragon-models-20261122/tools-max/io_scene_max')
bpy.ops.wm.read_factory_settings(use_empty=True)
import io_scene_max;io_scene_max.register();bpy.ops.import_scene.max(filepath=a[0])
for o in list(bpy.data.objects):
    if o.type not in('MESH','EMPTY'):bpy.data.objects.remove(o,do_unlink=True)
print('MAX2GLB meshes',sum(o.type=='MESH' for o in bpy.data.objects),'images',[i.name for i in bpy.data.images][:20])
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB')
