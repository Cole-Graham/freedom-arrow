# Pose test of a rigged body: arms raised to a rifle hold, a knee bent, head turned; front + side render. usage: blender -b RIG.blend -P posetest.py -- OUT.png
import bpy,sys,math
out=sys.argv[sys.argv.index('--')+1:][0];arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
P={'RightArm':(0,-40,-50),'RightForeArm':(0,-70,0),'LeftArm':(0,30,40),'LeftForeArm':(0,60,0),'LeftUpLeg':(-35,0,0),'LeftLeg':(50,0,0),'Head':(0,25,0),'Spine1':(10,0,0)}
for n,(x,y,z) in P.items():
    b=arm.pose.bones.get(n)
    if b:b.rotation_mode='XYZ';b.rotation_euler=(math.radians(x),math.radians(y),math.radians(z))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.render.resolution_x=600;s.render.resolution_y=800
cam=s.camera or bpy.data.objects.new('cam',bpy.data.cameras.new('cam'))
if cam.name not in s.collection.objects and not cam.users_collection:s.collection.objects.link(cam)
s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.2
for i,(loc,rot) in enumerate((((0,-5,1.0),(90,0,0)),((5,0,1.0),(90,0,90)))):
    cam.location=loc;cam.rotation_euler=[math.radians(a) for a in rot];s.render.filepath=out.replace('.png',f'_{i}.png');bpy.ops.render.render(write_still=True)
print('POSED',[n for n in P if arm.pose.bones.get(n)])
