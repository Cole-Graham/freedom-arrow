using System.Text.Json;
using UnityEngine;
using MelonLoader;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
namespace FAModels;
public partial class Mod
{
    class BodyRule { public int unitId {get;set;} public string[] lods {get;set;} = Array.Empty<string>(); }
    class BodyView { public UnitModelInfo model; public int unitId; public float created=Time.realtimeSinceStartup; public readonly HashSet<int> applied=new(); public readonly HashSet<int> failed=new(); public float lastDiagnostic; }
    class BodyMesh { public Mesh mesh; public Material[] materials; public BodyMesh(Mesh m,Material[] a){mesh=m;materials=a;} }
    static List<BodyRule> bodyRules=new();
    static readonly List<BodyView> bodyViews=new();
    static readonly Dictionary<string,BodyMesh> bodyCache=new();
    static float bodyPoll;
    static void LoadBodyRules()
    {
        var file=Path.Combine(dir,"infantry-bodies.json"); if(!File.Exists(file))return;
        try {
            var rules=JsonSerializer.Deserialize<List<BodyRule>>(File.ReadAllText(file))??new();
            foreach(var r in rules) {
                if(r.unitId!=901 || r.lods.Length!=3)throw new InvalidDataException("Body prototype is restricted to unit 901 and three LODs");
                foreach(var f in r.lods)if(Path.GetFileName(f)!=f || !File.Exists(Path.Combine(dir,f)))throw new InvalidDataException("Missing/unsafe body asset");
            }
            bodyRules=rules;MelonLogger.Msg($"FAMODELS body prototype ready: {rules.Count} unit(s); native animation and attachments retained");
        } catch(Exception e){bodyRules.Clear();MelonLogger.Error("FAMODELS body rules rejected: "+e.Message);}
    }
    static void QueueBodies(UnitModelInfo model,int unitId)
    {
        if(model==null || !bodyRules.Any(r=>r.unitId==unitId) || bodyViews.Any(v=>v.model==model))return;
        bodyViews.Add(new BodyView{model=model,unitId=unitId});
    }
    static BodyMesh ReadBody(string file,SkinnedMeshRenderer native)
    {
        var original=native.sharedMesh;
        // Cache only when bind matrices and native bone ordering are identical via the original mesh ID.
        string key=file+":"+original.GetInstanceID()+":"+string.Join(",",native.bones.Select(b=>b==null?"?":b.name));
        if(bodyCache.TryGetValue(key,out var cached))return cached;
        using var f=new BinaryReader(File.OpenRead(Path.Combine(dir,file)));
        if(new string(f.ReadChars(4))!="FAS1")throw new InvalidDataException("Invalid skinned mesh header");
        int nb=f.ReadInt32();if(nb!=40)throw new InvalidDataException("Expected 40 donor bones");
        var nativeBones=native.bones;var mapping=new int[nb];
        for(int i=0;i<nb;i++) {
            string name=Str(f);mapping[i]=-1;
            for(int j=0;j<nativeBones.Length;j++)if(nativeBones[j]!=null && nativeBones[j].name==name){mapping[i]=j;break;}
            // Lower native LODs may omit unused finger bones; only positive weights require a mapping.
        }
        int ns=f.ReadInt32();if(ns<1||ns>8)throw new InvalidDataException("Invalid material count");
        var pos=new List<Vector3>();var normals=new List<Vector3>();var uv=new List<Vector2>();var weights=new List<BoneWeight>();var indices=new List<int[]>();var materials=new List<Material>();
        for(int s=0;s<ns;s++) {
            string tex=Str(f);if(Path.GetFileName(tex)!=tex)throw new InvalidDataException("Unsafe texture name");
            int nv=f.ReadInt32();if(nv<1||nv>200000)throw new InvalidDataException("Invalid vertex count");
            int start=pos.Count;
            for(int k=0;k<nv;k++) {
                var p=new Vector3(f.ReadSingle(),f.ReadSingle(),f.ReadSingle());var n=new Vector3(f.ReadSingle(),f.ReadSingle(),f.ReadSingle());var u=new Vector2(f.ReadSingle(),f.ReadSingle());
                if(!float.IsFinite(p.x+p.y+p.z+n.x+n.y+n.z+u.x+u.y))throw new InvalidDataException("Non-finite vertex");
                int[] bi={f.ReadInt32(),f.ReadInt32(),f.ReadInt32(),f.ReadInt32()};float[] bw={f.ReadSingle(),f.ReadSingle(),f.ReadSingle(),f.ReadSingle()};
                if(bi.Any(x=>x<0||x>=nb)||bw.Any(x=>!float.IsFinite(x)||x<0)||Math.Abs(bw.Sum()-1)>0.001f)throw new InvalidDataException("Invalid weights");
                for(int z=0;z<4;z++) { if(bw[z]>0 && mapping[bi[z]]<0)throw new InvalidDataException("A weighted donor bone is absent in this native LOD"); if(bw[z]==0)bi[z]=0; }
                pos.Add(p);normals.Add(n);uv.Add(u);weights.Add(new BoneWeight{boneIndex0=Math.Max(0,mapping[bi[0]]),boneIndex1=Math.Max(0,mapping[bi[1]]),boneIndex2=Math.Max(0,mapping[bi[2]]),boneIndex3=Math.Max(0,mapping[bi[3]]),weight0=bw[0],weight1=bw[1],weight2=bw[2],weight3=bw[3]});
            }
            int ni=f.ReadInt32();if(ni<3||ni%3!=0||ni>600000)throw new InvalidDataException("Invalid index count");
            var ix=new int[ni];for(int k=0;k<ni;k++){int v=f.ReadInt32();if(v<0||v>=nv)throw new InvalidDataException("Bad index");ix[k]=v+start;}indices.Add(ix);
            materials.Add(Mat(tex,new Color(1,1,1,1),new MatP{metallic=0,smoothness=.25f}));
        }
        if(f.BaseStream.Position!=f.BaseStream.Length)throw new InvalidDataException("Trailing skin data");
        var mesh=new Mesh{name="FAM_BODY_"+file,indexFormat=UnityEngine.Rendering.IndexFormat.UInt32};
        mesh.vertices=new Il2CppStructArray<Vector3>(pos.ToArray());mesh.normals=new Il2CppStructArray<Vector3>(normals.ToArray());mesh.uv=new Il2CppStructArray<Vector2>(uv.ToArray());mesh.boneWeights=new Il2CppStructArray<BoneWeight>(weights.ToArray());mesh.bindposes=original.bindposes;mesh.subMeshCount=ns;
        for(int s=0;s<ns;s++)mesh.SetTriangles(new Il2CppStructArray<int>(indices[s]),s);
        mesh.RecalculateBounds();mesh.RecalculateTangents();
        var result=new BodyMesh(mesh,materials.ToArray());bodyCache.Add(key,result);return result;
    }
    static void TickInfantryBodies()
    {
        if(Time.realtimeSinceStartup-bodyPoll<.25f)return;bodyPoll=Time.realtimeSinceStartup;
        for(int v=bodyViews.Count-1;v>=0;v--) {
            var view=bodyViews[v];
            if(view.model?.PrefabRootScript==null){if(Time.realtimeSinceStartup-view.created>30)bodyViews.RemoveAt(v);continue;}
            var rule=bodyRules.First(r=>r.unitId==view.unitId);
            var soldiers=view.model.SquadSolders;if(soldiers==null)continue;
            var candidates=new List<(SkinnedMeshRenderer renderer,GameObject root,int soldier)>();
            for(int si=0;si<soldiers.Length;si++) {
                var soldier=soldiers[si];if(soldier==null||soldier.ViewObject==null)continue;
                var root=soldier.ViewObject;
                // Soldier ViewObjects are not guaranteed to be descendants of the squad prefab root.
                foreach(var renderer in root.GetComponentsInChildren<SkinnedMeshRenderer>(true)) candidates.Add((renderer,root,si));
                if(soldier.MeshRenderers!=null)foreach(var renderer in soldier.MeshRenderers) {
                    var skin=renderer?.TryCast<SkinnedMeshRenderer>();if(skin!=null && !candidates.Any(c=>c.renderer==skin))candidates.Add((skin,root,si));
                }
            }
            if(Time.realtimeSinceStartup-view.lastDiagnostic>10 && view.applied.Count==0) {
                view.lastDiagnostic=Time.realtimeSinceStartup;MelonLogger.Msg($"FAMODELS body scan unit={view.unitId} soldiers={soldiers.Length} skins={candidates.Count} applied={view.applied.Count} failed={view.failed.Count}");
            }
            foreach(var candidate in candidates) {
                var renderer=candidate.renderer;
                if(renderer==null||renderer.sharedMesh==null||renderer.bones.Length<1)continue;
                int id=renderer.GetInstanceID();if(view.applied.Contains(id)||view.failed.Contains(id))continue;
                if(renderer.sharedMesh.name.StartsWith("FAM_BODY_")){view.applied.Add(id);continue;}
                // Use the game's actual LODGroup membership, not a guessed renderer ordering.
                int level=-1;
                foreach(var group in candidate.root.GetComponentsInChildren<LODGroup>(true)) {
                    var lods=group.GetLODs();for(int l=0;l<lods.Length;l++)foreach(var r in lods[l].renderers)if(r==renderer)level=Math.Min(l,2);
                }
                if(level<0) {string n=renderer.name.ToLowerInvariant();if(n.Contains("lod_0")||n.Contains("lod0"))level=0;else if(n.Contains("lod_1")||n.Contains("lod1"))level=1;else if(n.Contains("lod_2")||n.Contains("lod2"))level=2;}
                if(level<0){view.failed.Add(id);MelonLogger.Warning($"FAMODELS body skipped unknown LOD {renderer.name}; native mesh retained");continue;}
                var oldMesh=renderer.sharedMesh;var oldMats=renderer.sharedMaterials;var oldBounds=renderer.localBounds;
                try {
                    var body=ReadBody(rule.lods[level],renderer);
                    renderer.sharedMaterials=new Il2CppReferenceArray<Material>(body.materials);renderer.sharedMesh=body.mesh;
                    // Conservative local bounds for first deformation test; native LOD and visibility logic stays in place.
                    renderer.localBounds=new Bounds(new Vector3(0,.95f,0),new Vector3(3f,3f,3f));
                    view.applied.Add(id);MelonLogger.Msg($"FAMODELS body applied unit={view.unitId} soldier={candidate.soldier} renderer={renderer.name} lod={level} bones={renderer.bones.Length} vertices={body.mesh.vertexCount} file={rule.lods[level]}");
                } catch(Exception e) {
                    renderer.sharedMesh=oldMesh;renderer.sharedMaterials=oldMats;renderer.localBounds=oldBounds;view.failed.Add(id);MelonLogger.Error($"FAMODELS body failed {renderer.name}: {e.Message}; native mesh retained");
                }
            }
        }
    }
}
