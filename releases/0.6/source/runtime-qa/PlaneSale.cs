using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Configs;
using Il2CppBrokenArrow.Client.Ecs.Economy.Systems;
using Il2CppBrokenArrow.Client.Ecs.Shop.UI;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using Il2CppTMPro;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Aircraft sale rework, part 1 (Lateralus 15 Nov 2026, thread 1571554273639006392, test build only: "when you sell your planes you get 100% of the
// points back, but over a 5 minute window"; 14:30 PST: damaged/unarmed planes 100%, shot-down planes nothing, buy-again delay unchanged, no cap;
// 14:42 PST: "it would be better if we could tweak the engine's actual parameters that control refunds").
// Native RefundSystem.RefundUnit(in Entity, bool onlyCount) RVA 0x6DBEC0 (from the code, work/plane-refund-20261109/REPORT.md):
//   refund = clamp(RefundMultiplier x (Cost x (1 - HealthCostMultiplier x HP lost) - _supplyMul x missing ammo/flare supply), Min%..Max% of Cost)
// and, when onlyCount is false, adds it to the owner's PlayerInfo.Points (0x6DCC87-0x6DCCD2). Those settings are global, so for units of
// category Aircrafts (UnitCategoryType 6) the values in plane-refund.json are swapped in for the call and restored after it (same method as the
// unshipped 0.7 PlaneRefund.cs). For a real sale the instant payment is taken back and paid out evenly over PayoutSeconds (game time).
// Helicopters (5), pilots and every other unit keep the native refund. Lost planes: RefundUnit is not called, so nothing is paid (vanilla too).
// HUD: a line above the points in the shop button (MainShopButtonUI) shows the points per minute still coming from sold planes.
static class PlaneSale
{
    const int MaxLog=300;
    sealed class Settings{public int Category=6;public float Max=100,Min=20,Health=0,Supply=0,Multiplier=1,Seconds=300;public string Icon="US_F15C-Label";}
    sealed class Saved{public bool Swapped;public GameConfig Cfg;public float Max,Min,Health,Multiplier,Supply;}
    sealed class Payout{public PlayerInfo Player;public IntPtr Ptr,Session;public float Amount,Paid,Start,NextLog;public int Unit;}
    static Settings s=new();
    static bool on,broken;
    static int logged;
    static readonly object Gate=new();
    static readonly List<Payout> payouts=new();
    static TextMeshProUGUI label;static MainShopButtonUI labelOwner;
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var file=Path.Combine(root,"plane-refund.json");if(!File.Exists(file))return;
        var c=JsonNode.Parse(File.ReadAllText(file))!;
        float F(string k,float d)=>c[k]?.GetValue<float>()??d;
        s=new Settings{Category=c["Category"]?.GetValue<int>()??6,Max=F("MaximumRefundPercent",100),Min=F("MinimumRefundPercent",20),
            Health=F("HealthCostMultiplier",0),Supply=F("SupplyMultiplier",0),Multiplier=F("RefundMultiplier",1),Seconds=F("PayoutSeconds",300),Icon=c["HudIcon"]?.GetValue<string>()??"US_F15C-Label"};
        if(!(s.Seconds>0)||s.Max<s.Min)throw new InvalidDataException("plane-refund.json: PayoutSeconds > 0 and Maximum >= Minimum");
        var m=AccessTools.Method(typeof(RefundSystem),"RefundUnit")??throw new MissingMethodException("RefundSystem.RefundUnit");
        harmony.Patch(m,prefix:new HarmonyMethod(typeof(PlaneSale),nameof(Before)){priority=Priority.First},
            postfix:new HarmonyMethod(typeof(PlaneSale),nameof(After)){priority=Priority.First},
            finalizer:new HarmonyMethod(typeof(PlaneSale),nameof(Finally)));
        var ui=AccessTools.Method(typeof(MainShopButtonUI),"GameUpdate")??throw new MissingMethodException("MainShopButtonUI.GameUpdate");
        harmony.Patch(ui,postfix:new HarmonyMethod(typeof(PlaneSale),nameof(HudAfter)));
        on=true;
        MelonLogger.Msg($"FREEDOM_ARROW_PLANE_SALE installed: category {s.Category} refunds use max {s.Max}% min {s.Min}% health x{s.Health} supply x{s.Supply} multiplier {s.Multiplier}, paid over {s.Seconds} s");
        DiagnosticLog.Write("plane_sale_installed",new{s.Category,s.Max,s.Min,s.Health,s.Supply,s.Multiplier,s.Seconds});
    }
    static bool IsPlane(Entity e,out UnitComponent u)
    {
        u=null;if(!e.IsAlive||!e.Has<UnitComponent>())return false;
        u=NativeEcs.Read<UnitComponent>(e);return u?.UnitData!=null&&(int)u.UnitData.CategoryType==s.Category;
    }
    static void Before(in Entity __0,out Saved __state)
    {
        __state=new Saved();
        if(!on||broken||!Runtime.IsApplied)return;
        try
        {
            if(!IsPlane(__0,out _))return;
            var cfg=GameConfig.Instance;if(cfg==null)return;
            __state.Cfg=cfg;__state.Max=cfg.MaximumRefundPercent;__state.Min=cfg.MinimumRefundPercent;__state.Health=cfg.HealthCostMultiplier;
            __state.Multiplier=cfg.RefundMultiplier;__state.Supply=RefundSystem._supplyMul;
            Monitor.Enter(Gate);__state.Swapped=true;
            cfg.MaximumRefundPercent=s.Max;cfg.MinimumRefundPercent=s.Min;cfg.HealthCostMultiplier=s.Health;cfg.RefundMultiplier=s.Multiplier;
            RefundSystem._supplyMul=__state.Supply*s.Supply;
        }
        catch(Exception x){Restore(__state);Fail(x);}
    }
    static void After(in Entity __0,bool __1,float __result,Saved __state)
    {
        if(__state?.Swapped!=true)return;
        try
        {
            if(!IsPlane(__0,out var u))return;
            if(__1||!(__result>0))
            {
                if(logged<MaxLog&&!__1){logged++;DiagnosticLog.Write("plane_sale",new{t=Time.time,unit=u.UnitData.Id,cost=u.UnitData.Cost,refund=__result,note="nothing to pay"});}
                return;
            }
            var p=u.Owner?.TryCast<PlayerInfo>();if(p==null)return;
            float before=p.Points.Value;p.Points=before-__result;
            payouts.Add(new Payout{Player=p,Ptr=p.Pointer,Session=CurrentSession(),Amount=__result,Start=Time.time,NextLog=Time.time+60,Unit=u.UnitData.Id});
            if(logged<MaxLog){logged++;DiagnosticLog.Write("plane_sale",new{t=Time.time,unit=u.UnitData.Id,name=u.UnitData.Name,cost=u.UnitData.Cost,refund=__result,
                pointsWithInstant=before,pointsAfterTakeBack=p.Points.Value,perMinute=__result/s.Seconds*60f,s.Seconds,active=payouts.Count});}
        }
        catch(Exception x){Fail(x);}
    }
    static Exception Finally(Exception __exception,Saved __state){Restore(__state);return __exception;}
    static void Restore(Saved st)
    {
        if(st==null||!st.Swapped)return;
        try{st.Cfg.MaximumRefundPercent=st.Max;st.Cfg.MinimumRefundPercent=st.Min;st.Cfg.HealthCostMultiplier=st.Health;st.Cfg.RefundMultiplier=st.Multiplier;RefundSystem._supplyMul=st.Supply;}
        finally{st.Swapped=false;Monitor.Exit(Gate);}
    }
    // Main thread: pay every frame the share that game time has made due.
    public static void LateUpdate()
    {
        if(!on||broken||payouts.Count==0)return;
        try
        {
            // 15 Nov 2026 test (Lateralus 15:26 PST "it doesn't seem to work at all"): the first version compared the session with a value that
            // started at zero and cleared every payout on the first frame after a sale, so the points were taken back and never paid.
            // Each payout now remembers its own session and is only dropped when that session has really ended.
            var cur=CurrentSession();
            float now=Time.time;
            for(int i=payouts.Count-1;i>=0;i--)
            {
                var q=payouts[i];
                if(q.Session!=cur){payouts.RemoveAt(i);if(logged<MaxLog){logged++;DiagnosticLog.Write("plane_sale_dropped",new{t=now,unit=q.Unit,q.Amount,q.Paid,reason="match ended"});}continue;}
                float due=Math.Min(q.Amount,q.Amount*(now-q.Start)/s.Seconds),d=due-q.Paid;
                if(d>0){q.Player.Points=q.Player.Points.Value+d;q.Paid=due;}
                if(now>=q.NextLog&&logged<MaxLog){logged++;q.NextLog=now+60;DiagnosticLog.Write("plane_sale_progress",new{t=now,unit=q.Unit,q.Amount,q.Paid,points=q.Player.Points.Value});}
                if(q.Paid>=q.Amount-1e-4f){payouts.RemoveAt(i);if(logged<MaxLog){logged++;DiagnosticLog.Write("plane_sale_paid",new{t=now,unit=q.Unit,q.Amount,seconds=now-q.Start});}}
            }
        }
        catch(Exception x){Fail(x);}
    }
    static IntPtr CurrentSession()
    {
        var g=Il2CppBrokenArrow.Client.Ecs.Controllers.GameController.Instance;
        return g?.GameSession==null?IntPtr.Zero:g.GameSession.Pointer;
    }
    public static void SceneChanged(){payouts.Clear();label=null;labelOwner=null;icon=null;lastText=null;}
    // HUD (Lateralus 15:42 PST: "use the plane icon, I think the F-15C icon will work best ... obviously you will have to shrink it. Also, the padding
    // between the Air refund income and the players current points pool, should be the same as the padding for the regular income below it").
    // A copy of the income text sits above the points; its gap to the points equals the points-to-income gap, measured from the rendered text
    // bounds. The F-15C map label sprite (IconsLoader address HudIcon, default US_F15C-Label) is scaled to the text height left of "+N".
    static UnityEngine.UI.Image icon;static string lastText;static bool hudLogged;
    static void HudAfter(MainShopButtonUI __instance,PlayerInfo __0)
    {
        if(!on||broken||__0==null)return;
        try
        {
            float perMin=0;foreach(var q in payouts)if(q.Ptr==__0.Pointer)perMin+=q.Amount/s.Seconds*60f;
            var inc=__instance._incomeText;var score=__instance._scoreText;if(inc==null||score==null)return;
            if(label==null||labelOwner==null||labelOwner.Pointer!=__instance.Pointer)
            {
                var go=UnityEngine.Object.Instantiate(inc.gameObject,inc.transform.parent);go.name="FA_PlaneSaleIncome";
                label=go.GetComponent<TextMeshProUGUI>();labelOwner=__instance;lastText=null;icon=null;
                var ig=new GameObject("FA_PlaneSaleIcon");ig.transform.SetParent(go.transform,false);
                icon=ig.AddComponent<UnityEngine.UI.Image>();icon.preserveAspect=true;icon.raycastTarget=false;
                var sp=IconsLoader.LoadSprite(s.Icon,false,icon);
                if(sp==null){UnityEngine.Object.Destroy(ig);icon=null;}
                go.SetActive(false);
            }
            bool show=perMin>=0.5f;
            if(label.gameObject.activeSelf!=show)label.gameObject.SetActive(show);
            if(!show)return;
            string text=(icon==null?"AIR +":"+")+Mathf.RoundToInt(perMin);
            if(text==lastText)return;
            lastText=text;label.text=text;Layout(score,inc);
        }
        catch(Exception x){Fail(x);}
    }
    static float Edge(TMP_Text t,bool top)
    {
        var r=t.rectTransform;return r.localPosition.y+(top?t.textBounds.max.y:t.textBounds.min.y)*r.localScale.y;
    }
    static void Layout(TextMeshProUGUI score,TextMeshProUGUI inc)
    {
        score.ForceMeshUpdate();inc.ForceMeshUpdate();label.ForceMeshUpdate();
        float gap=Edge(score,false)-Edge(inc,true);
        var lr=label.rectTransform;var lp=lr.localPosition;lp.x=inc.rectTransform.localPosition.x;lp.y+=Edge(score,true)+gap-Edge(label,false);lr.localPosition=lp;
        if(icon!=null)
        {
            var b=label.textBounds;float h=b.size.y*1.15f;var sp=icon.sprite;float w=sp==null?h:h*sp.rect.width/Math.Max(1f,sp.rect.height);
            var ir=icon.rectTransform;var piv=lr.pivot;ir.anchorMin=piv;ir.anchorMax=piv;ir.pivot=new Vector2(0.5f,0.5f);ir.sizeDelta=new Vector2(w,h);
            ir.anchoredPosition=new Vector2(b.min.x-0.35f*b.size.y-w/2f,b.center.y);icon.color=label.color;
        }
        if(!hudLogged){hudLogged=true;DiagnosticLog.Write("plane_sale_hud",new{icon=icon!=null?s.Icon:null,gap,scoreBottom=Edge(score,false),incomeTop=Edge(inc,true),
            scoreTop=Edge(score,true),labelBottom=Edge(label,false)});}
    }
    static void Fail(Exception x)
    {
        if(broken)return;broken=true;
        DiagnosticLog.Write("plane_sale_failed",new{error=x.ToString()});
        MelonLogger.Error("FREEDOM_ARROW_PLANE_SALE_FAILED: native refunds from now on. "+x.Message);
    }
}
