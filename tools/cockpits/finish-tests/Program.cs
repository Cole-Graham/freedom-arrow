FAModels.Mod.Test();
namespace UnityEngine {
 public sealed class Material {
  public Dictionary<string,float> Floats=new(); public HashSet<string> Keywords=new();
  public void SetFloat(string key,float value)=>Floats[key]=value;
  public void EnableKeyword(string key)=>Keywords.Add(key);
  public void DisableKeyword(string key)=>Keywords.Remove(key);
 }
}
namespace FAModels {
 public partial class Mod {
  public static void Test() {
   int checks=0; void Check(bool ok){if(!ok)throw new Exception("Canopy finish regression");checks++;}
   var m=new UnityEngine.Material();m.SetFloat("_Metallic",1);m.SetFloat("_Smoothness",0);m.SetFloat("_SurfaceType",1);m.SetFloat("_AlphaCutoff",.5f);m.SetFloat("_EnableBlendModePreserveSpecularLighting",0);m.EnableKeyword("_ENABLE_FOG_ON_TRANSPARENT");
   var baseline=new Dictionary<string,float>(m.Floats);ApplyCanopyFinish(m,false);
   Check(m.Floats.Count==baseline.Count && baseline.All(x=>m.Floats[x.Key]==x.Value));Check(m.Keywords.SetEquals(new[]{"_ENABLE_FOG_ON_TRANSPARENT"}));
   ApplyCanopyFinish(m,true);
   Check(m.Floats["_Metallic"]==0);Check(m.Floats["_MetallicRemapMin"]==0 && m.Floats["_MetallicRemapMax"]==0);
   Check(m.Floats["_Smoothness"]==.95f);Check(m.Floats["_SmoothnessRemapMin"]==.90f && m.Floats["_SmoothnessRemapMax"]==.98f);
   Check(m.Floats["_EnableBlendModePreserveSpecularLighting"]==1);Check(m.Keywords.Contains("_BLENDMODE_PRESERVE_SPECULAR_LIGHTING"));
   Check(m.Floats["_EnableFogOnTransparent"]==0 && !m.Keywords.Contains("_ENABLE_FOG_ON_TRANSPARENT"));
   Check(m.Floats["_SurfaceType"]==1 && m.Floats["_AlphaCutoff"]==.5f);
   var first=new Dictionary<string,float>(m.Floats);ApplyCanopyFinish(m,true);Check(first.All(x=>m.Floats[x.Key]==x.Value));
   Console.WriteLine($"PASS: {checks} checks; opt-in glass preserves specular, clamps packed maps, leaves alpha/non-canopy settings intact. Unity rendering untested.");
  }
 }
}
