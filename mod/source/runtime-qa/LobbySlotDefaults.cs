using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;
using Il2CppBrokenArrow.MissionEditor.MissionResolver;
using Il2CppNetworkCommon.Enums;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Open slots by map size (Lateralus 16 Nov 2026, thread 1571554273639006392: "for a 1v1 map it would be convenient if only 2 slots were
// open by default, 4 slots by default for 2v2, etc. (lobby host can close and open slots, this is different from the available slots coded
// into the map itself)"). Every FA map has 5 available slots per team; a map file has no "closed by default" setting (ScenarioSlotMeta has
// only "lock", which makes a slot unavailable). So when this player creates a lobby with an [FA] [NvN] map, the runtime closes the free
// slots past N on each team, once, as the host would (NetworkLobbyService.ChangeSlotStatus, LobbySlotStatus.Locked). The host can open
// them again. Map changes inside the lobby are left alone.
static class LobbySlotDefaults
{
    static int open=-1,doneLobby;static float since;static string map;
    public static void Install(HarmonyLib.Harmony h)
    {
        var m=AccessTools.Method(typeof(NetworkLobbyService),nameof(NetworkLobbyService.CreateLobby))??throw new MissingMethodException("NetworkLobbyService.CreateLobby");
        h.Patch(m,postfix:new HarmonyMethod(typeof(LobbySlotDefaults),nameof(Created)));
        MelonLogger.Msg("FREEDOM_ARROW_LOBBY_SLOTS installed: a new FA lobby opens 1/2/3/5 slots per team for 1v1/2v2/3v3/4v4 maps (maps.json)");
    }
    static void Created(ScenarioSource initScenario)
    {
        map=initScenario?.Name??"";open=-1;
        // 0.9.6 (Lateralus 23 Nov 2026): the size comes from the map list (MapSizes.cs), not the [NvN] tag; [4v4] maps open 5 per team.
        if(MapSizes.SizeOf(map) is string size)open=MapSizes.PlayersPerTeam(size);
        since=Time.unscaledTime;
        if(open>0)DiagnosticLog.Write("lobby_slots_pending",new{map,open});
    }
    public static void LateUpdate()
    {
        if(open<0)return;
        if(Time.unscaledTime-since>60){DiagnosticLog.Write("lobby_slots_gave_up",new{map});open=-1;return;}
        try
        {
            Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<NetworkLobbyService>(out var lobby,false);
            if(lobby==null||!lobby.IsHost||lobby.LobbyId==0||lobby.LobbyId==doneLobby||lobby.State?.Teams==null)return;
            var closed=new List<string>();
            foreach(var side in new[]{TeamSide.Alpha,TeamSide.Bravo})
            {
                if(!lobby.State.Teams.TryGetValue(side,out var team)||team?.Slots==null)return;   // wait until both teams exist
                for(int i=open;i<team.Slots.Length;i++)
                    if(team.Slots[i]?.Status==LobbySlotStatus.Free){lobby.ChangeSlotStatus(side,(byte)i,LobbySlotStatus.Locked);closed.Add($"{side}{i}");}
            }
            doneLobby=lobby.LobbyId;
            DiagnosticLog.Write("lobby_slots_closed",new{map,open,lobby=lobby.LobbyId,closed});
            MelonLogger.Msg($"FREEDOM_ARROW_LOBBY_SLOTS: {map}: {open} open per team, closed {closed.Count}");
            open=-1;
        }
        catch(Exception e){open=-1;MelonLogger.Error("FREEDOM_ARROW_LOBBY_SLOTS_FAILED: slots left as they are. "+e.Message);}
    }
}
