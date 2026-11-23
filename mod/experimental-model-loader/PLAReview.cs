using System.Text.Json;
using UnityEngine;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal;
namespace FAModels;
public partial class Mod
{
    // Test-copy opt-in only. Uses native armory card selection; never creates a battle.
    static float reviewPoll; static string lastReviewRequest="";
    static int reviewUnit;
    static void TickPlaReview()
    {
        if(Time.realtimeSinceStartup-reviewPoll<1)return;reviewPoll=Time.realtimeSinceStartup;
        string file=Path.Combine(dir,"pla-review-unit.txt");if(!File.Exists(file))return;
        string request=File.ReadAllText(file).Trim();
        if(!int.TryParse(request.Split(':')[0],out int uid)||(uid!=901&&(uid<985||uid>1009)))return;
        var preview=UnityEngine.Object.FindObjectOfType<ArsenalUnitPreview>();
        if(preview==null||!preview.gameObject.activeInHierarchy||preview.GetHangarCards==null)return;
        var cards=preview.GetHangarCards;if(!cards.ContainsKey(uid))return;
        reviewUnit=uid;
        if(request!=lastReviewRequest) {
            var card=cards[uid];card.OnSelect.Invoke(card.Unit);lastReviewRequest=request;
            MelonLogger.Msg($"PLA_REVIEW native armory card selected: unit={uid}");
        }
        var views=bodyViews.Where(v=>v.unitId==uid&&v.model?.PrefabRootScript!=null).ToArray();
        var handOffsets=bodyOffsets.Values.Where(b=>b.source!=null&&b.visual!=null&&b.source.name.Contains("Hand")).Select(b=>(b.visual.position-b.source.position).magnitude).ToArray();
        File.WriteAllText(Path.Combine(dir,"pla-review-state.json"),JsonSerializer.Serialize(new {requested=uid,displayed=preview.DisplayedUnit?.Id,soldiers=views.Select(v=>v.model.SquadSolders?.Length??0).ToArray(),applied=views.Sum(v=>v.applied.Count),failed=views.Sum(v=>v.failed.Count),handBones=handOffsets.Length,maxHandOffset=handOffsets.Length==0?0:handOffsets.Max(),time=Time.realtimeSinceStartup}));
    }
    static void ReviewCamera()
    {
        if(reviewUnit==0||!File.Exists(Path.Combine(dir,"pla-review-unit.txt")))return;
        var preview=UnityEngine.Object.FindObjectOfType<ArsenalUnitPreview>();
        if(preview==null||!preview.gameObject.activeInHierarchy||preview.DisplayedUnit?.Id!=reviewUnit)return;
        var view=bodyViews.LastOrDefault(v=>v.unitId==reviewUnit&&v.model?.PrefabRootScript!=null);
        if(view==null||Camera.main==null||view.model.SquadSolders==null)return;
        var roots=view.model.SquadSolders.Where(s=>s?.ViewObject!=null).Select(s=>s.ViewObject.transform).ToArray();
        if(roots.Length==0)return;var center=Vector3.zero;foreach(var root in roots)center+=root.position;center/=roots.Length;center+=Vector3.up*.9f;
        var camera=Camera.main.transform;
        string detailFile=Path.Combine(dir,"pla-review-detail.txt");
        string detail=File.Exists(detailFile)?File.ReadAllText(detailFile).Trim():"";
        if(detail=="hands"||detail=="helmet") {
            var root=roots[0];center=root.position+Vector3.up*(detail=="helmet"?1.72f:1.25f);
            camera.position=center+root.forward*(detail=="helmet"?.75f:1.25f)+root.right*.4f+Vector3.up*.12f;
        } else camera.position=center+roots[0].forward*7+roots[0].right*3+Vector3.up*2;
        camera.LookAt(center);
    }
}
