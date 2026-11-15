"""Render a .fas infantry body (bind pose) with its textures from the same folder, Cycles, front 3/4. usage: blender -b -P render_fas.py -- IN.fas OUT.png"""
import bpy,sys,os,struct,math
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1];d=os.path.dirname(src)
b=open(src,'rb').read();o=4
def i32():
    global o;v=struct.unpack_from('<i',b,o)[0];o+=4;return v
def s():
    n=i32();global o;r=b[o:o+n].decode();o+=n;return r
nb=i32()
for _ in range(nb):s()
ns=i32();bpy.ops.wm.read_factory_settings(use_empty=True);allp=[]
for k in range(ns):
    tex=s();nv=i32();V=[];UV=[]
    for _ in range(nv):
        x,y,z,nx,ny,nz,u,v=struct.unpack_from('<8f',b,o);o+=32;o+=32
        V.append((-x,-z,y));UV.append((u,1+v))
    ni=i32();I=struct.unpack_from('<%di'%ni,b,o);o+=4*ni
    me=bpy.data.meshes.new(f'b{k}');me.from_pydata(V,[],[tuple(I[j:j+3]) for j in range(0,ni,3)]);uvl=me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:uvl.data[li].uv=UV[me.loops[li].vertex_index]
    for p in me.polygons:p.use_smooth=True
    m=bpy.data.materials.new(tex);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
    if os.path.exists(os.path.join(d,tex)):
        tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(os.path.join(d,tex));nt.links.new(tx.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.75;me.materials.append(m)
    ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);allp+=V
xs=[p[0] for p in allp];ys=[p[1] for p in allp];zs=[p[2] for p in allp];c=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2);h=max(zs)-min(zs)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.render.resolution_x=600;sc.render.resolution_y=800
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.62,0.7,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.9
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(50),0,math.radians(-30)));bpy.context.object.data.energy=3.5
t=math.radians(-110);r=h*1.6
bpy.ops.object.camera_add(location=(c[0]+r*math.cos(t),c[1]+r*math.sin(t),c[2]+h*0.15));cam=bpy.context.object;sc.camera=cam;cam.data.lens=60
k=cam.constraints.new('TRACK_TO');bpy.ops.object.empty_add(location=c);k.target=bpy.context.object;k.track_axis='TRACK_NEGATIVE_Z';k.up_axis='UP_Y'
sc.render.filepath=os.path.abspath(out);bpy.ops.render.render(write_still=True)
