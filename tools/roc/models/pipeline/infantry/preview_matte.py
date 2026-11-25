"""preview_matte.py RIG.blend OUTPREFIX: matte front / back / close-up renders (Workbench, specular off; Shawn 25 Nov: less reflective)."""
import bpy,sys
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1]
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading
sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_specular_highlight=False;sh.show_cavity=False
s.world=s.world or bpy.data.worlds.new('w');s.world.color=(0.32,0.32,0.32);s.render.film_transparent=False
s.view_settings.view_transform='Standard'
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO'
for name,loc,tgt,scale,res in (('front',(0,-5,1.0),(0,0,1.0),2.1,(700,900)),('back',(0,5,1.0),(0,0,1.0),2.1,(700,900)),('close',(0.25,-5,0.75),(0.25,0,0.75),0.7,(700,700))):
    s.render.resolution_x,s.render.resolution_y=res;cam.data.ortho_scale=scale
    cam.location=loc;cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=f'{out}_{name}.png';bpy.ops.render.render(write_still=True)
