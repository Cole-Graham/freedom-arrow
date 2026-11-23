using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.BattleEnd;
using Il2CppNetworkCommon.Enums;
namespace FreedomArrow.Conquest;
// Lateralus 21 Nov 2026 (thread 1572962048705429598): "the vanilla game also differentiates between "major" and "minor" victories. For our game mode,
// we want a Major victory be a conquest lead great than 30%" ... "queue both". The server picks the level itself (its War Goals table on the
// native victory-point gap; our SendEndGame carries only the team), so every FA win showed "Minor victory". The result screen's model
// (BattleEndScreenModel, built only by its (winnerTeam, fightStatistics, isScenarioLobby) constructor: one direct native caller in 1.2.2.1)
// keeps a writable VictoryLevel. This postfix keeps the server's winner and side (victory or defeat for this player) and sets the size from the
// final FA score: Major when the leader has more than MajorVictoryMarginPercent (30) % more points than the other side, else Minor. Draws,
// total, technical and desertion results are left alone. Display only: the server's stored level does not change.
public sealed partial class Prototype
{
    static int? finalAlpha,finalBravo;static DateTime finalAt;static bool resultHookBroken;
    static void RecordFinal(){if(ledger==null)return;finalAlpha=ledger.Alpha;finalBravo=ledger.Bravo;finalAt=DateTime.UtcNow;}
    static void InstallResultLevel()
    {
        var ctor=typeof(BattleEndScreenModel).GetConstructors().FirstOrDefault(c=>c.GetParameters() is var p&&p.Length==3&&p[0].ParameterType==typeof(TeamSide))
            ??throw new MissingMethodException("BattleEndScreenModel(TeamSide, FightStatistic, bool)");
        instance!.HarmonyInstance.Patch(ctor,postfix:new HarmonyMethod(typeof(Prototype),nameof(ResultLevelAfter)));
        Log("hook_registered",new{type=typeof(BattleEndScreenModel).FullName,name=".ctor(TeamSide, FightStatistic, bool)"});
    }
    static void ResultLevelAfter(BattleEndScreenModel __instance)
    {
        if(resultHookBroken||__instance==null||finalAlpha is not int a||finalBravo is not int b||(DateTime.UtcNow-finalAt).TotalSeconds>600)return;
        try
        {
            var level=__instance.VictoryLevel;
            bool win=level is VictoryLevelType.MinorVictory or VictoryLevelType.MajorVictory;
            bool loss=level is VictoryLevelType.MinorDefeat or VictoryLevelType.MajorDefeat;
            if(!win&&!loss)return;
            int hi=Math.Max(a,b),lo=Math.Min(a,b);
            bool major=(long)hi*100>(long)lo*(100+config.MajorVictoryMarginPercent);
            var set=win?(major?VictoryLevelType.MajorVictory:VictoryLevelType.MinorVictory):(major?VictoryLevelType.MajorDefeat:VictoryLevelType.MinorDefeat);
            __instance.VictoryLevel=set;
            Log("result_level",new{server=level.ToString(),shown=set.ToString(),alpha=a,bravo=b,config.MajorVictoryMarginPercent,winner=__instance.WinnerTeam.ToString()});
            finalAlpha=finalBravo=null;
        }
        catch(Exception e){resultHookBroken=true;MelonLogger.Error("FREEDOM_ARROW_RESULT_LEVEL_FAILED: the server's level is shown. "+e.Message);}
    }
}
