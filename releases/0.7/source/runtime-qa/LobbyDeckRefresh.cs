using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.TeamPanel;
using Il2CppNetworkCommon.Enums;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// The first dropdown fill can precede the initial scenario/team metadata. Refill the
// local card after initialization, through the same native path as a map change.
// Do not force an enabled dropdown, select a deck, change ready status or send a map RPC.
internal static class LobbyDeckRefresh
{
    sealed class Pending
    {
        public TeamPanelPlayerInfo Card;
        public float Started,Next;
        public int Attempts;
        public string Map;
    }
    static readonly Dictionary<IntPtr,Pending> pending=new();
    static bool filling;
    public static void Install(HarmonyLib.Harmony h)
    {
        foreach(string name in new[]{"Init","FillDeckDropdown"})
            h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),name)??throw new MissingMethodException(name),
                postfix:new HarmonyMethod(typeof(LobbyDeckRefresh),nameof(Queue)));
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),"Release"),prefix:new HarmonyMethod(typeof(LobbyDeckRefresh),nameof(Release)));
        DiagnosticLog.Write("lobby_deck_refresh_installed",new{maxSeconds=15,maxAttempts=30,scope="local unready FA scenario card; native validation retained"});
    }
    static void Queue(TeamPanelPlayerInfo __instance)
    {
        if(filling||__instance==null||pending.ContainsKey(__instance.Pointer)||pending.Count>=32)return;
        pending[__instance.Pointer]=new Pending{Card=__instance,Started=Time.unscaledTime,Next=Time.unscaledTime+.5f};
    }
    static void Release(TeamPanelPlayerInfo __instance){if(__instance!=null)pending.Remove(__instance.Pointer);}
    public static void Clear()=>pending.Clear();
    public static void Update()
    {
        if(pending.Count==0)return;
        float now=Time.unscaledTime;
        foreach(var pair in pending.ToArray())
        {
            var p=pair.Value;if(now<p.Next)continue;
            p.Next=now+.5f;
            try
            {
                var card=p.Card;
                if(card==null||card.WasCollected||card._destroyed||now-p.Started>15||p.Attempts>=30){pending.Remove(pair.Key);continue;}
                if(!card._initialized||card._clientInfo==null||card._authService?.CurrentUser==null||card._lobbyService?.State==null)continue;
                var state=card._lobbyService.State;
                if(state.Options==null||state.ScenarioMeta==null)continue;
                if(card._clientInfo.Id!=card._authService.CurrentUser.Id||state.Options.LobbyType!=LobbyType.Scenario)
                {pending.Remove(pair.Key);continue;}
                string map=state.ScenarioMeta.Guid+"/"+state.ScenarioMeta.Hash;
                if(!state.ScenarioMeta.Name.StartsWith("[FA] ",StringComparison.Ordinal)
                    ||state.Status!=LobbyStatus.Pending||card._clientInfo.Status!=ClientLobbyStatus.NotReady
                    ||(card._clientInfo.TeamSide!=TeamSide.Alpha&&card._clientInfo.TeamSide!=TeamSide.Bravo))
                {pending.Remove(pair.Key);continue;}
                if(p.Map!=null&&p.Map!=map){pending.Remove(pair.Key);continue;}p.Map=map;
                if(!card.isActiveAndEnabled||!card._deckChoosingAllowed)continue;
                // Close no popup and disturb no working selector. On a missing/disabled list,
                // retain ArrowQueue's country filter and all native DLC/scenario restrictions.
                if(card._deckList!=null&&card._deckList.Count>0&&card._deckAccessible)
                {pending.Remove(pair.Key);continue;}
                p.Attempts++;
                filling=true;
                try {card.FillDeckDropdown();card.UpdateDeckAccessibility();}
                finally {filling=false;}
                int count=card._deckList?.Count??0;
                DiagnosticLog.Write("lobby_deck_refresh",new{attempt=p.Attempts,decks=count,accessible=card._deckAccessible,scenario=state.ScenarioMeta.Name});
                if(count>0&&card._deckAccessible)pending.Remove(pair.Key);
            }
            catch(Exception e)
            {
                filling=false;pending.Remove(pair.Key);
                DiagnosticLog.Write("lobby_deck_refresh_failed",new{error=e.ToString()});
                MelonLogger.Warning("FREEDOM_ARROW_LOBBY_DECK_REFRESH_FAILED: "+e.Message);
            }
            break; // At most one native refill per frame.
        }
    }
}
