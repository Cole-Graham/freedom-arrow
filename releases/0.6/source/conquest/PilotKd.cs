using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.BattleEnd.Tabs.Results;
using Il2CppNetworkCommon.Messages.Clients;

namespace FreedomArrow.Conquest;
// 0.9.0-dev.13 (Osama 15 Nov 2026: "Make sure Pilots don't count of a player's K/D"). The end-of-match panel
// (BattleStatisticPanel.Init) shows Destruction, Losses and their ratio from the player's ClientStatistic. Before it does,
// pilots (units 322-327, the ejected crews) are taken out of both counts: each pilot in a unit's KilledUnits is one kill
// fewer, and each of the player's own pilots that died and was not refunded (rescued) is one loss fewer. Score points,
// rating and the server's own records are not changed; the in-match scoreboard ratio comes from the server and still counts them.
public sealed partial class Prototype
{
    static bool pilotKdOff;
    static int pilotKdLogged;
    static readonly HashSet<IntPtr> pilotKdDone=new();
    static void InstallPilotKd()
    {
        Patch(typeof(BattleStatisticPanel),"Init",nameof(PilotKdBefore),null);
        MelonLogger.Msg("FREEDOM_ARROW_PILOT_KD installed: pilots are left out of the end-of-match kills, losses and K/D");
    }
    public static void PilotKdBefore(ClientStatistic __0)
    {
        if(pilotKdOff||__0==null)return;
        try
        {
            if(!pilotKdDone.Add(__0.Pointer))return;
            int kills=0,losses=0,deaths=0;
            var units=__0.UnitData.GetEnumerator();var unitsMove=units.Cast<Il2CppSystem.Collections.IEnumerator>();
            while(unitsMove.MoveNext())
            {
                var u=units.Current.Value;if(u==null)continue;
                bool dead=u.DeathTime>0&&!u.WasRefunded;
                if(dead)deaths++;
                if(dead&&PilotUnits.Contains(u.Id))losses++;
                if(u.KilledUnits==null)continue;
                var victims=u.KilledUnits.GetEnumerator();var victimsMove=victims.Cast<Il2CppSystem.Collections.IEnumerator>();
                while(victimsMove.MoveNext())if(victims.Current!=null&&PilotUnits.Contains(victims.Current.Id))kills++;
            }
            int d0=__0.Destruction,l0=__0.Losses;
            __0.Destruction=Math.Max(0,d0-kills);__0.Losses=Math.Max(0,l0-losses);
            if(++pilotKdLogged<=8)MelonLogger.Msg($"FREEDOM_ARROW_PILOT_KD player {__0.Id}: kills {d0} -> {__0.Destruction} ({kills} pilots), losses {l0} -> {__0.Losses} ({losses} pilots); dead units counted here {deaths}");
        }
        catch(Exception e){pilotKdOff=true;MelonLogger.Warning("FREEDOM_ARROW_PILOT_KD off, panel shows the game's own numbers: "+e.Message);}
    }
}
