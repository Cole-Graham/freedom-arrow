using System.Reflection;
using MelonLoader;
namespace FreedomArrow;
// 0.6 dev.1 (Osama, 7 November 2026): FlatIncomeMod (Speer) ships with Freedom Arrow, but its forest cover stays off.
// Its ForestCover.Post cuts infantry damage in woods by 30%, the same rule as our CoverDamage, so both would cut it twice.
// Post returns at once while its private _broken flag is set (FlatIncomeMod sets it only after an error).
static class ThirdPartyGuard
{
    static bool done;
    public static void Ensure()
    {
        if(done)return;
        var asm=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FlatIncomeMod");
        if(asm==null)return;
        done=true;
        var field=asm.GetType("FlatIncomeMod.ForestCover")?.GetField("_broken",BindingFlags.Static|BindingFlags.NonPublic);
        if(field==null){MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover not found; it may double the forest cut");return;}
        field.SetValue(null,true);
        MelonLogger.Msg($"FREEDOM_ARROW_THIRD_PARTY: FlatIncomeMod forest cover off (FA forest rule only): {field.GetValue(null)}");
    }

    // 0.6 dev.10 (Osama, 7 November 2026): ArrowQueue (unchanged, ActualArrow) runs the Mod game tab against our own
    // matchmaking hub on Sam's deck, not ActualArrow's server. Its match statistics go there too.
    // ArrowQueue keeps these in UserData/ArrowQueue.cfg, which ActualArrow also reads, so the old values are put back
    // when the game closes (MelonLoader runs the quit events before it saves the preferences).
    const string Hub="https://cyberdeck.tailf7ad82.ts.net/hubs/game";
    const string Stats="https://cyberdeck.tailf7ad82.ts.net/hubs/stats";
    // ArrowQueue's own ban guard blocks the game's Skirmish button, which is how Freedom Arrow opens its offline Local AI
    // Skirmish. BALocalSkirmish already refuses every non-scenario online lobby (create, list, invite, quick search),
    // so ArrowQueue's guard is off while Freedom Arrow runs.
    static readonly List<(MelonPreferences_Entry<string> e,string old)> changed=new();
    static (MelonPreferences_Entry<bool> e,bool old)? guard;
    public static void PointArrowQueue()
    {
        if(changed.Count>0||MelonPreferences.GetCategory("ArrowQueue")==null)return;
        var g=MelonPreferences.GetEntry<bool>("ArrowQueue","BlockUnsafeModes");
        if(g==null)MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING: ArrowQueue setting BlockUnsafeModes not found; its guard may block Local AI Skirmish");
        else{guard=(g,g.Value);g.Value=false;}
        foreach(var (id,url) in new[]{("Server",Hub),("StatsServer",Stats)})
        {
            var e=MelonPreferences.GetEntry<string>("ArrowQueue",id);
            if(e==null){MelonLogger.Error($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue setting {id} not found");continue;}
            // A value that is already ours (left by a crash) goes back to ArrowQueue's own default ("").
            changed.Add((e,e.Value==url?"":e.Value));
            e.Value=url;
        }
        MelonLogger.Msg($"FREEDOM_ARROW_MATCHMAKING: ArrowQueue uses {Hub}; its ban guard is off (Freedom Arrow's lobby rules apply)");
    }
    public static void RestoreArrowQueue()
    {
        foreach(var (e,old) in changed)e.Value=old;
        if(guard is {} g){g.e.Value=g.old;guard=null;}
        if(changed.Count>0)MelonLogger.Msg("FREEDOM_ARROW_MATCHMAKING: ArrowQueue settings restored for ActualArrow");
        changed.Clear();
    }
}
