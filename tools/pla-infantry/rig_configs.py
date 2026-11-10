"""Fit the supplied Type21 meshes to the original BA Ranger skeleton.

Run in Blender. Source files remain external; no source weights are assumed.
"""
import argparse, json, math, struct, sys
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--donor',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--resume',action='store_true');ap.add_argument('--no-previews',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);a.source=a.source.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
configs=json.loads((Path(__file__).resolve().parents[2]/'releases/0.6/pla-configurations-contract.json').read_text())

def ws(f,s):
 b=s.encode();f.write(struct.pack('<i',len(b))+b)
def xyz(v):return (-v.x,v.z,-v.y)
audits=[]
for ci,c in enumerate(configs):
 cached=a.out/c['key']/'audit.json'
 if a.resume and cached.exists():
  audits.append(json.loads(cached.read_text()));(a.out/'configurations.json').write_text(json.dumps(audits,indent=2)+'\n');continue
 bpy.ops.wm.read_factory_settings(use_empty=True)
 directory=a.source/c['kind'];desert=c['camo']=='desert'
 fbx=directory/('PLA_21_HuangMo.fbx' if desert else 'PLA_21_CongLin.fbx') if c['kind']=='regular' else next(directory.glob('*.fbx'))
 bpy.ops.import_scene.fbx(filepath=str(fbx));objects={o.name:o for o in bpy.data.objects if o.type=='MESH'}
 if c['kind']=='regular':names=[n for n in objects if n!='Object001']
 else:
  names=['Object017','SM_FrogShirt001' if desert else 'SM_FrogShirt','SM_pants001' if desert else 'SM_pants','SM_boots','SM_PMC_Gloves_NonameTactical02_D','SM_PMC_Gloves_NonameTactical02_D001','SM_pla_belt','SM_pla_headset','SM_pla_helmet001' if desert else 'SM_helmet_US_fastHD_Color']
  if c['vest'] in ['carrier','heavy']:names+=['PMC_Armor_901Elite4Pouches_D_hm' if desert else 'PMC_Armor_901Elite4Pouches_D']
  if c['vest']=='heavy':names+=['heavy-vest-protect_hm' if desert else 'heavy-vest-protect']
  if c['vest']=='condor':names+=['SM_PMC_Armor_CondorModularOperatorGen2_D001' if desert else 'SM_PMC_Armor_CondorModularOperatorGen2_D']
  if c['vest']=='light':names+=['SM_vest001' if desert else 'SM_vest']
 if c.get('gear'):
  gear=c['gear']
  if gear=='assault':names+=['SM_backbag001' if desert else 'SM_backbag','SM_BackPanel_Spiritus','SM_bag_beltback','Object002','Object004','Object005','Object015','Object016','SM_SafarilandHolster','SM_ANPRC155' if desert else 'SM_ANPRC152']
  if gear in ['night_up','night_down']:
   if not desert:names.remove('SM_helmet_US_fastHD_Color');names.append('SM_pla_helmet')
   names+=['SM_gear_pla_bnvd_up' if gear=='night_up' else 'SM_gear_pla_bnvd_ON']
  if gear in ['goggles_up','goggles_down']:names+=['SM_pla_goggles_down001' if gear=='goggles_up' else 'SM_pla_goggles_down']
  if gear=='condor_pouches':names+=['CondorModularOperatorGen2_hm' if desert else 'CondorModularOperatorGen2_D','SM_ANPRC157' if desert else 'SM_ANPRC154']
  if gear=='condor_pouches_b':names+=['CondorModularOperatorGen2_Pouches_D']
  if gear=='grenadier':names+=['SM_GPouchV005','SM_GPouchV006','SM_GPouchV007','SM_GPouchV008','SM_ANPRC156'] if desert else ['SM_GPouchV1','SM_GPouchV1.001','SM_GPouchV002','SM_GPouchV004','SM_ANPRC152.001','SM_PMC_Trousers_CryePrecisionG3_01_D']
 selected_names=list(names);source=[objects[n] for n in names]
 for o in list(bpy.data.objects):
  if o not in source:bpy.data.objects.remove(o,do_unlink=True)
 textures={};missing=[]
 for o in source:
  chosen=o.data.uv_layers.active
  assert chosen is not None,o.name
  for layer in list(o.data.uv_layers):
   if layer!=chosen:o.data.uv_layers.remove(layer)
  chosen.name='BA_DiffuseUV';o.data.uv_layers.active_index=0;chosen.active_render=True
  # Imported source is an equipment sheet. Bring only detached alternatives back to X=0.
  vv=[o.matrix_world@Vector(v) for v in o.bound_box];center=(min(v.x for v in vv)+max(v.x for v in vv))/2
  world=o.matrix_world.copy()
  if abs(center)>.7:world.translation.x-=center
  o.parent=None;o.matrix_world=world
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  # Match the donor A-pose around the shoulders; body-only offset stays in the loader.
  soft=(c['kind']=='regular' and o.name in ['SM_CC_Arm','SM_UniformPla21']) or (c['kind']=='special' and ('FrogShirt' in o.name or 'Gloves' in o.name))
  for v in o.data.vertices:
   p=v.co.copy()
   if soft and p.z>.86 and abs(p.x)>.20:
    sign=1 if p.x>0 else -1;t=math.radians(14)*min(1,max(0,(abs(p.x)-.2)/.10));x=abs(p.x)-.245;z=p.z-1.46;p.x=sign*(.245+x*math.cos(t)-z*math.sin(t));p.z=1.46+x*math.sin(t)+z*math.cos(t)
   v.co=p
  for mat in o.data.materials:
   if not mat:continue
   images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if mat.use_nodes else []
   paths=[directory/Path(im.filepath.replace('\\','/')).name for im in images]
   paths=[p if p.exists() else p.with_suffix('.tga') for p in paths]
   paths=[p for p in paths if p.exists()]
   base=next((p for p in paths if any(t in p.stem.lower() for t in ['color','_co','_d','col','boots_base'])),paths[0] if paths else None)
   normal=next((p for p in paths if any(t in p.stem.lower() for t in ['normal','_nrm','_norm','_n'])),None)
   if o.name=='SM_CC_Arm':base=directory/'T_Arm_color.png';normal=directory/'T_Arm_Normal.png'
   if o.name=='xuezi2':base=directory/'T_boots_Color.png';normal=directory/'T_boots_Normal.png'
   if base is None or not base.exists():missing.append([o.name,mat.name]);continue
   # Make the inspected source's diffuse map explicit, avoiding broken absolute author paths.
   mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(base),check_existing=True);mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.nodes.active=tex
   textures[mat.name]={'base':str(base),'normal':str(normal) if normal and normal.exists() else None}
 assert not missing,missing
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(a.donor.resolve()),bone_heuristic='TEMPERANCE');refs=[o for o in bpy.data.objects if o not in before];arm=next(o for o in refs if o.type=='ARMATURE');donor=next(o for o in refs if o.type=='MESH' and o.name.startswith('lod_0'))
 for o in source:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  for g in donor.vertex_groups:o.vertex_groups.new(name=g.name)
  mod=o.modifiers.new('Native surface weights','DATA_TRANSFER');mod.object=donor;mod.use_vert_data=True;mod.data_types_verts={'VGROUP_WEIGHTS'};mod.vert_mapping='POLYINTERP_NEAREST';mod.layers_vgroup_select_src='ALL';mod.layers_vgroup_select_dst='NAME';bpy.ops.object.modifier_apply(modifier=mod.name)
  # Plates/helmets follow the torso or head, rather than stretching between limbs.
  rigid=any(t in o.name.lower() for t in ['vest','armor','helmet','headset','object017','head_wj'])
  if rigid:
   bone='Head' if any(t in o.name.lower() for t in ['helmet','headset','head_wj','object017']) else 'Spine2'
   for g in o.vertex_groups:g.remove(list(range(len(o.data.vertices))))
   o.vertex_groups[bone].add(list(range(len(o.data.vertices))),1,'REPLACE')
  bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4);bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
  mod=o.modifiers.new('BA animation','ARMATURE');mod.object=arm;o.parent=arm
 for o in refs:
  if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in source:o.select_set(True)
 bpy.context.view_layer.objects.active=source[0];bpy.ops.object.join();base=bpy.context.object;lods=[];budget=[]
 names=[b.name for b in arm.data.bones];ni={n:i for i,n in enumerate(names)};assert len(names)==40
 folder=a.out/c['key'];folder.mkdir(exist_ok=True)
 for level,ratio in [(0,1),(1,.20),(2,.075)]:
  obj=base.copy();obj.data=base.data.copy();bpy.context.collection.objects.link(obj);obj.name=c['key']+f'_lod{level}';bpy.context.view_layer.objects.active=obj
  if ratio<1:
   dec=obj.modifiers.new('LOD budget','DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_move_up(modifier=dec.name);bpy.ops.object.modifier_apply(modifier=dec.name)
  bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4);bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
  me=obj.data;me.calc_loop_triangles();me.update();assert me.uv_layers.active
  uv=me.uv_layers.active.data;used=[(i,m) for i,m in enumerate(me.materials) if any(t.material_index==i for t in me.loop_triangles)]
  assert all(any(g.weight>0 for g in v.groups) for v in me.vertices)
  with (folder/f'lod{level}.fas').open('wb') as f:
   f.write(b'FAS1'+struct.pack('<i',len(names)))
   for n in names:ws(f,n)
   f.write(struct.pack('<i',len(used)))
   for mi,mat in used:
    loops=[li for t in me.loop_triangles if t.material_index==mi for li in t.loops];ws(f,mat.name);f.write(struct.pack('<i',len(loops)))
    for li in loops:
     lp=me.loops[li];v=me.vertices[lp.vertex_index];u=uv[li].uv;groups=sorted([(ni[obj.vertex_groups[g.group].name],g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])[:4];total=sum(w for _,w in groups);groups=[(i,w/total) for i,w in groups]+[(0,0)]*(4-len(groups));f.write(struct.pack('<8f4i4f',*xyz(v.co),*xyz(lp.normal),u.x,u.y,*[i for i,w in groups],*[w for i,w in groups]))
    inds=[i for j in range(0,len(loops),3) for i in (j,j+2,j+1)];f.write(struct.pack('<i',len(inds))+struct.pack('<'+'i'*len(inds),*inds))
  budget.append({'lod':level,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'unweighted':0});lods.append(obj)
 bpy.data.objects.remove(base,do_unlink=True)
 for o in lods:o.hide_render=o!=lods[0];o.hide_set(o!=lods[0])
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/'rig.blend'))
 s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.render.resolution_x=700;s.render.resolution_y=900;s.render.resolution_percentage=100
 cam=bpy.data.objects.new('Audit camera',bpy.data.cameras.new('Audit camera'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.2;cam.location=(2.2,-5,1.2);cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/'rest.png')
 if not a.no_previews or ci<2:bpy.ops.render.render(write_still=True)
 audit={**c,'unit':985+ci,'selected_objects':selected_names,'textures':textures,'lods':budget,'native_tested':False}
 (folder/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');audits.append(audit)
 (a.out/'configurations.json').write_text(json.dumps(audits,indent=2)+'\n');print('CONFIG COMPLETE',c['key'],flush=True)
