# 3/4 preview of a GLB. usage: blender -b -P view34.py -- IN.glb OUT.png
import bpy,sys,math,mathutils as mu
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0]);sc=bpy.context.scene
ps=[o.matrix_world@mu.Vector(c) for o in sc.objects if o.type=='MESH' for c in o.bound_box];mn=mu.Vector([min(p[i] for p in ps) for i in range(3)]);mx=mu.Vector([max(p[i] for p in ps) for i in range(3)])
c=(mn+mx)/2;r=(mx-mn).length
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam
cam.location=c+mu.Vector((r*0.5,-r*1.0,-r*0.6));cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=50;cam.data.clip_end=r*10
sun=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));sun.data.energy=3.5;sun.rotation_euler=(math.radians(50),0,math.radians(40));sc.collection.objects.link(sun)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.57,0.6,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.8
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=960;sc.render.resolution_y=600;sc.render.filepath=a[1];bpy.ops.render.render(write_still=True)
