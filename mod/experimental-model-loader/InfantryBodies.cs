using System.Text.Json;
using UnityEngine;
using MelonLoader;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
namespace FAModels;
public partial class Mod
{
    class BodyRule { public int unitId {get;set;} public string[] lods {get;set;} = Array.Empty<string>(); public float[] offset {get;set;} = new float[3]; public bool anchorHands {get;set;} }
    class BodyOffset { public Transform source; public Transform visual; public Vector3 offset; }
    static readonly Dictionary<int,BodyOffset> bodyOffsets=new();
    class BodyView { public UnitModelInfo model; public int unitId; public bool battle; public float created=Time.realtimeSinceStartup; public readonly HashSet<int> applied=new(); public readonly HashSet<int> failed=new(); public float lastDiagnostic; public bool done; }
    class BodyMesh { public Mesh mesh; public Material[] materials; public BodyMesh(Mesh m,Material[] a){mesh=m;materials=a;} }
    static List<BodyRule> bodyRules=new();
    static readonly List<BodyView> bodyViews=new();
    static readonly Dictionary<string,BodyMesh> bodyCache=new();
    static readonly Dictionary<int,Dictionary<int,int>> lodLevels=new();
    static float bodyPoll;
    // 0.3.31 (Osama 15 Nov: the China game had about 3x the slow frames of a vanilla game at the same stage). The 1.6 cm body offset moved a
    // helper on every bone of every China soldier every frame (OnLateUpdate), tens of thousands of engine calls per frame in a 5v5. It is off
    // unless UserData/FAModels/body-offset-on.txt exists; bodies then sit on the native bones (the offset is 1.6 cm, 0.3 cm on 43 rules).
    static bool bodyOffsetsOn;
    static void LoadBodyRules()
    {
        var file=Path.Combine(dir,"infantry-bodies.json"); if(!File.Exists(file))return;
        try {
            var rules=ReadBodyRules(file);
            // Add-on packs (ROC, 25 Nov 2026) bring their own infantry-bodies-<pack>.json. A bad add-on file is skipped alone.
            foreach(var extra in Directory.GetFiles(dir,"infantry-bodies-*.json").OrderBy(x=>x,StringComparer.Ordinal)) {
                try { var add=ReadBodyRules(extra);rules.AddRange(add);MelonLogger.Msg($"FAMODELS body add-on {Path.GetFileName(extra)}: {add.Count} unit(s)"); }
                catch(Exception e){MelonLogger.Error($"FAMODELS body add-on {Path.GetFileName(extra)} rejected: "+e.Message);}
            }
            bodyRules=rules;bodyOffsetsOn=File.Exists(Path.Combine(dir,"body-offset-on.txt"));MelonLogger.Msg($"FAMODELS body offsets {(bodyOffsetsOn?"on":"off")} (body-offset-on.txt)");MelonLogger.Msg($"FAMODELS body prototype ready: {rules.Count} unit(s); native animation and attachments retained");
        } catch(Exception e){bodyRules.Clear();MelonLogger.Error("FAMODELS body rules rejected: "+e.Message);}
    }
    static List<BodyRule> ReadBodyRules(string file)
    {
        var rules=JsonSerializer.Deserialize<List<BodyRule>>(File.ReadAllText(file))??new();
        foreach(var r in rules) {
            if(!InfantryBodyIdentity.IsSupported(r.unitId) || r.lods.Length!=3)throw new InvalidDataException("Body rule must use an approved infantry unit and three LODs");
            if(r.offset.Length!=3 || r.offset.Any(x=>!float.IsFinite(x)||Math.Abs(x)>.15f))throw new InvalidDataException("Invalid body-only offset");
            foreach(var f in r.lods)if(Path.GetFileName(f)!=f || !File.Exists(Path.Combine(dir,f)))throw new InvalidDataException("Missing/unsafe body asset");
        }
        return rules;
    }
    static void QueueBodies(UnitModelInfo model,int unitId,bool battle)
    {
        if(model==null || !bodyRules.Any(r=>r.unitId==unitId) || bodyViews.Any(v=>v.model==model))return;
        bodyViews.Add(new BodyView{model=model,unitId=unitId,battle=battle});
    }
    static Il2CppReferenceArray<Transform> OffsetBodyBones(SkinnedMeshRenderer renderer,BodyRule rule)
    {
        var baseOffset=new Vector3(rule.offset[0],rule.offset[1],rule.offset[2]);
        var bones=renderer.bones;if(baseOffset.sqrMagnitude==0||!bodyOffsetsOn)return bones;
        var result=new Transform[bones.Length];
        for(int i=0;i<bones.Length;i++) {
            var bone=bones[i];if(bone==null)continue;
            float factor=1;
            if(rule.anchorHands) {
                if(bone.name.Contains("Hand"))factor=0;
                else if(bone.name.Contains("ForeArm"))factor=.35f;
                else if(bone.name.EndsWith("Arm"))factor=.75f;
            }
            var offset=baseOffset*factor;
            int key=bone.GetInstanceID();
            if(!bodyOffsets.TryGetValue(key,out var item)) {
                // A child used only by the body renderer follows the native bone exactly.
                // Weapons retain the original bone and all original transforms.
                var child=new GameObject("FAM_BODY_OFFSET_"+bone.name).transform;child.SetParent(bone,false);
                item=new BodyOffset{source=bone,visual=child,offset=offset};bodyOffsets.Add(key,item);
            }
            if((item.offset-offset).sqrMagnitude>.000001f)throw new InvalidDataException("Conflicting body-only offsets");
            item.visual.localPosition=bone.InverseTransformVector(offset);result[i]=item.visual;
        }
        return new Il2CppReferenceArray<Transform>(result);
    }
    public override void OnLateUpdate()
    {
        LateHide();
        try { TickInfantryBodies(true,true); } catch (Exception ex) { MelonLogger.Error("FAMODELS body late poll: " + ex.Message); }
        try { ReviewCamera(); } catch(Exception e) { MelonLogger.Error("PLA_REVIEW camera: "+e.Message); }
        foreach(var key in bodyOffsets.Keys.ToArray()) {
            var item=bodyOffsets[key];
            if(item.source==null || item.visual==null){bodyOffsets.Remove(key);continue;}
            // Convert a fixed world displacement each frame. Translating bind vertices
            // would rotate offsets independently at finger joints and distort the glove.
            item.visual.localPosition=item.source.InverseTransformVector(item.offset);
        }
    }
    // 0.3.29 (Osama 15 Nov: "I'm having frame stutters in game", "we should build it all before the match"): a body file read and
    // checked once into memory; ReadBody only maps its bones onto the native soldier. PreloadBody does this before the match.
    class ParsedSub { public string tex=""; public Vector3[] pos=Array.Empty<Vector3>(); public Vector3[] nrm=Array.Empty<Vector3>(); public Vector2[] uv=Array.Empty<Vector2>(); public int[][] bi=Array.Empty<int[]>(); public float[][] bw=Array.Empty<float[]>(); public int[] idx=Array.Empty<int>(); }
    class ParsedBody { public string[] bones=Array.Empty<string>(); public ParsedSub[] subs=Array.Empty<ParsedSub>(); }
    static readonly Dictionary<string,ParsedBody> parsedBodies=new();
    // 0.3.30 (Osama 15 Nov: "can't we have armory and battle bodies for infantry? ... we need to optimize performance"): in a
    // battle a body uses the battle copy of its texture, X_b (with X_b_n and X_b_mask), when the package has one; the armory keeps
    // X. The battle copies are the same GPU textures one mip level down (2048 -> 1024), about vanilla soldier weight.
    static string BodyTex(string tex,bool battle)
    {
        if(!battle)return tex;
        var b=Path.GetFileNameWithoutExtension(tex)+"_b"+Path.GetExtension(tex);
        return TexExists(b)?b:tex;
    }
    static Material BodyMat(string tex,bool battle)=>Mat(BodyTex(tex,battle),new Color(1,1,1,1),new MatP{metallic=0,smoothness=.25f});
    static ParsedBody ParseBody(string file)
    {
        if(parsedBodies.TryGetValue(file,out var done))return done;
        using var f=new BinaryReader(File.OpenRead(Path.Combine(dir,file)));
        if(new string(f.ReadChars(4))!="FAS1")throw new InvalidDataException("Invalid skinned mesh header");
        int nb=f.ReadInt32();if(nb!=40)throw new InvalidDataException("Expected 40 donor bones");
        var body=new ParsedBody{bones=new string[nb]};
        for(int i=0;i<nb;i++)body.bones[i]=Str(f);
        int ns=f.ReadInt32();if(ns<1||ns>8)throw new InvalidDataException("Invalid material count");
        body.subs=new ParsedSub[ns];
        for(int s=0;s<ns;s++) {
            var sub=new ParsedSub{tex=Str(f)};if(Path.GetFileName(sub.tex)!=sub.tex)throw new InvalidDataException("Unsafe texture name");
            int nv=f.ReadInt32();if(nv<1||nv>200000)throw new InvalidDataException("Invalid vertex count");
            sub.pos=new Vector3[nv];sub.nrm=new Vector3[nv];sub.uv=new Vector2[nv];sub.bi=new int[nv][];sub.bw=new float[nv][];
            for(int k=0;k<nv;k++) {
                var p=new Vector3(f.ReadSingle(),f.ReadSingle(),f.ReadSingle());var n=new Vector3(f.ReadSingle(),f.ReadSingle(),f.ReadSingle());var u=new Vector2(f.ReadSingle(),f.ReadSingle());
                if(!float.IsFinite(p.x+p.y+p.z+n.x+n.y+n.z+u.x+u.y))throw new InvalidDataException("Non-finite vertex");
                int[] bi={f.ReadInt32(),f.ReadInt32(),f.ReadInt32(),f.ReadInt32()};float[] bw={f.ReadSingle(),f.ReadSingle(),f.ReadSingle(),f.ReadSingle()};
                if(bi.Any(x=>x<0||x>=nb)||bw.Any(x=>!float.IsFinite(x)||x<0)||Math.Abs(bw.Sum()-1)>0.001f)throw new InvalidDataException("Invalid weights");
                sub.pos[k]=p;sub.nrm[k]=n;sub.uv[k]=u;sub.bi[k]=bi;sub.bw[k]=bw;
            }
            int ni=f.ReadInt32();if(ni<3||ni%3!=0||ni>600000)throw new InvalidDataException("Invalid index count");
            sub.idx=new int[ni];for(int k=0;k<ni;k++){int v=f.ReadInt32();if(v<0||v>=nv)throw new InvalidDataException("Bad index");sub.idx[k]=v;}
            body.subs[s]=sub;
        }
        if(f.BaseStream.Position!=f.BaseStream.Length)throw new InvalidDataException("Trailing skin data");
        parsedBodies[file]=body;return body;
    }
    // Before the match: read the body file and make its materials (GPU textures), so the first squad of a type does no file work.
    static void PreloadBody(string file){var b=ParseBody(file);foreach(var sub in b.subs)BodyMat(sub.tex,true);}
    static List<string> BodyFiles(int unitId){var l=new List<string>();foreach(var r in bodyRules)if(r.unitId==unitId)l.AddRange(r.lods);return l;}
    static BodyMesh ReadBody(string file,SkinnedMeshRenderer native,bool battle)
    {
        var original=native.sharedMesh;
        // Cache only when bind matrices and native bone ordering are identical via the original mesh ID.
        string key=file+(battle?":battle:":":")+original.GetInstanceID()+":"+string.Join(",",native.bones.Select(b=>b==null?"?":b.name));
        // 0.3.17: the game unloads unused assets between scenes; a destroyed cached mesh or material made every later body
        // apply throw (Mesh.vertexCount NullReferenceException) and fall back to the native body. Rebuild when destroyed.
        if(bodyCache.TryGetValue(key,out var cached)) {
            if(cached.mesh!=null && cached.materials.All(m=>m!=null))return cached;
            bodyCache.Remove(key);MelonLogger.Msg($"FAMODELS body cache rebuilt for {file}: cached mesh or material was unloaded");
        }
        // 0.3.29: the file is parsed once (ParseBody, also before the match by PreloadBody); only the bone mapping is per native mesh.
        var src=ParseBody(file);int nb=src.bones.Length;
        var nativeBones=native.bones;var mapping=new int[nb];
        for(int i=0;i<nb;i++) {
            mapping[i]=-1;
            for(int j=0;j<nativeBones.Length;j++)if(nativeBones[j]!=null && nativeBones[j].name==src.bones[i]){mapping[i]=j;break;}
            // Lower native LODs may omit unused finger bones; only positive weights require a mapping.
        }
        int ns=src.subs.Length;
        var pos=new List<Vector3>();var normals=new List<Vector3>();var uv=new List<Vector2>();var weights=new List<BoneWeight>();var indices=new List<int[]>();var materials=new List<Material>();
        foreach(var sub in src.subs) {
            int start=pos.Count;
            for(int k=0;k<sub.pos.Length;k++) {
                var bi=sub.bi[k];var bw=sub.bw[k];
                for(int z=0;z<4;z++)if(bw[z]>0 && mapping[bi[z]]<0)throw new InvalidDataException("A weighted donor bone is absent in this native LOD");
                weights.Add(new BoneWeight{boneIndex0=bw[0]>0?Math.Max(0,mapping[bi[0]]):0,boneIndex1=bw[1]>0?Math.Max(0,mapping[bi[1]]):0,boneIndex2=bw[2]>0?Math.Max(0,mapping[bi[2]]):0,boneIndex3=bw[3]>0?Math.Max(0,mapping[bi[3]]):0,weight0=bw[0],weight1=bw[1],weight2=bw[2],weight3=bw[3]});
            }
            pos.AddRange(sub.pos);normals.AddRange(sub.nrm);uv.AddRange(sub.uv);
            var ix=new int[sub.idx.Length];for(int k=0;k<ix.Length;k++)ix[k]=sub.idx[k]+start;indices.Add(ix);
            materials.Add(BodyMat(sub.tex,battle));
        }
        var mesh=new Mesh{name="FAM_BODY_"+file,indexFormat=UnityEngine.Rendering.IndexFormat.UInt32,hideFlags=HideFlags.DontUnloadUnusedAsset};
        mesh.vertices=new Il2CppStructArray<Vector3>(pos.ToArray());mesh.normals=new Il2CppStructArray<Vector3>(normals.ToArray());mesh.uv=new Il2CppStructArray<Vector2>(uv.ToArray());mesh.boneWeights=new Il2CppStructArray<BoneWeight>(weights.ToArray());mesh.bindposes=original.bindposes;mesh.subMeshCount=ns;
        for(int s=0;s<ns;s++)mesh.SetTriangles(new Il2CppStructArray<int>(indices[s]),s);
        mesh.RecalculateBounds();mesh.RecalculateTangents();
        var result=new BodyMesh(mesh,materials.ToArray());bodyCache.Add(key,result);return result;
    }
    // 0.3.27 (Osama 14 Nov: "I still see the stand in infantry", then "still infantry standins but much shorter"): the 0.25 s
    // poll let the vanilla soldier show for up to a quarter second, and the first read of a body file (about 0.5 s) froze the
    // screen with the vanilla soldier on it. Squads spawned in the last 5 s are now checked every frame: OnLateUpdate only hides
    // their new vanilla soldiers (hideOnly) before the frame is drawn; the next OnUpdate swaps the body and shows it. The 0.25 s
    // poll stays for older squads (reinforced or re-spawned soldiers).
    // 0.3.34 (Osama 17 Nov 2026, 5v5 detail log): a soldier's body swap builds its mesh (5-8 ms each), and a whole squad swapped in one frame
    // (16-49 ms frames). Swaps now stop after 6 ms in a frame; the rest of that frame's soldiers are hidden (as before a swap) and swapped on
    // the next frames, so no stand-in body shows and no frame takes the whole squad.
    const double BodyBudgetMs=6;public static int BodyDeferred;
    static void TickInfantryBodies(bool young=false,bool hideOnly=false)
    {
        float now=Time.realtimeSinceStartup;long budgetStart=System.Diagnostics.Stopwatch.GetTimestamp();
        if(!young){if(now-bodyPoll<.25f)return;bodyPoll=now;}
        for(int v=bodyViews.Count-1;v>=0;v--) {
            var view=bodyViews[v];
            if(young && now-view.created>5f)continue;
            if(view.done)continue;
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
            // 0.3.31: a squad whose every soldier renderer is swapped (or refused) is not scanned again; the scan re-read each soldier's
            // renderers and bone arrays four times a second for every China squad of the match.
            if(!young && candidates.Count>0 && now-view.created>10f && candidates.All(c=>c.renderer!=null&&(view.applied.Contains(c.renderer.GetInstanceID())||view.failed.Contains(c.renderer.GetInstanceID())))){view.done=true;continue;}
            foreach(var candidate in candidates) {
                var renderer=candidate.renderer;
                if(renderer==null)continue;
                int id=renderer.GetInstanceID();if(view.applied.Contains(id)||view.failed.Contains(id))continue;
                if(renderer.sharedMesh==null||renderer.bones.Length<1)continue;
                if(renderer.sharedMesh.name.StartsWith("FAM_BODY_")){view.applied.Add(id);continue;}
                if(!hideOnly&&(System.Diagnostics.Stopwatch.GetTimestamp()-budgetStart)*1000.0/System.Diagnostics.Stopwatch.Frequency>BodyBudgetMs){hideOnly=true;BodyDeferred++;}
                if(hideOnly){renderer.forceRenderingOff=true;continue;}
                // Use the game's actual LODGroup membership, not a guessed renderer ordering.
                // 0.3.29: the soldier's LOD groups are read once per soldier, not once per renderer.
                if(!lodLevels.TryGetValue(candidate.root.GetInstanceID(),out var levels)) {
                    levels=new Dictionary<int,int>();
                    foreach(var group in candidate.root.GetComponentsInChildren<LODGroup>(true)) {
                        var lods=group.GetLODs();for(int l=0;l<lods.Length;l++)foreach(var r in lods[l].renderers)if(r!=null)levels[r.GetInstanceID()]=Math.Min(l,2);
                    }
                    lodLevels[candidate.root.GetInstanceID()]=levels;
                }
                int level=levels.TryGetValue(id,out var lv)?lv:-1;
                if(level<0) {string n=renderer.name.ToLowerInvariant();if(n.Contains("lod_0")||n.Contains("lod0"))level=0;else if(n.Contains("lod_1")||n.Contains("lod1"))level=1;else if(n.Contains("lod_2")||n.Contains("lod2"))level=2;}
                if(level<0){renderer.forceRenderingOff=false;view.failed.Add(id);MelonLogger.Warning($"FAMODELS body skipped unknown LOD {renderer.name}; native mesh retained");continue;}
                var oldMesh=renderer.sharedMesh;var oldMats=renderer.sharedMaterials;var oldBounds=renderer.localBounds;var oldBones=renderer.bones;
                try {
                    var body=ReadBody(rule.lods[level],renderer,view.battle);
                    renderer.sharedMaterials=new Il2CppReferenceArray<Material>(body.materials);renderer.sharedMesh=body.mesh;
                    renderer.bones=OffsetBodyBones(renderer,rule);
                    // Conservative local bounds for first deformation test; native LOD and visibility logic stays in place.
                    renderer.localBounds=new Bounds(new Vector3(0,.95f,0),new Vector3(3f,3f,3f));
                    renderer.forceRenderingOff=false;
                    view.applied.Add(id);bodySwapsThisFrame++;if(Verbose)MelonLogger.Msg($"FAMODELS body applied unit={view.unitId} after={now-view.created:F2}s soldier={candidate.soldier} renderer={renderer.name} lod={level} bones={renderer.bones.Length} vertices={body.mesh.vertexCount} file={rule.lods[level]} bodyOffset={string.Join(",",rule.offset)}");
                } catch(Exception e) {
                    renderer.sharedMesh=oldMesh;renderer.sharedMaterials=oldMats;renderer.localBounds=oldBounds;renderer.bones=oldBones;renderer.forceRenderingOff=false;view.failed.Add(id);MelonLogger.Error($"FAMODELS body failed {renderer.name}: {e.Message}; native mesh retained");
                }
            }
        }
    }
}
