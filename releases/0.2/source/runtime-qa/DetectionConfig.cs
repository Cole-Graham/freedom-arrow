using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Client.Ecs.Configs;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Systems;
using MelonLoader;
namespace FreedomArrow;
// Writes FogOfWarConfig values before the battle systems copy them, whenever the tables applied.
static class DetectionConfig
{
    const int Forest=2,Buildings=3;
    static DetectionSettings target,vanilla;
    static void Log(string stage,object data)=>MelonLogger.Msg("FREEDOM_ARROW_DETECTION "+stage+" "+JsonSerializer.Serialize(data));
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        target=DetectionSettings.Parse(File.ReadAllText(Path.Combine(root,"detection-config.json")));
        harmony.Patch(AccessTools.Method(typeof(EcsLoader),"InitBattleSequentialSystem"),
            prefix:new HarmonyMethod(typeof(DetectionConfig),nameof(Before)),postfix:new HarmonyMethod(typeof(DetectionConfig),nameof(After)));
        Log("installed",new{target,status="invocation unproved until a before line appears"});
    }
    static VisibleTerrainType Terrain(FogOfWarConfig cfg,int type)
    {
        VisibleTerrainType found=null;
        foreach(var row in cfg.SourceValues)if((int)row.TerrainType==type){if(found!=null)throw new InvalidDataException("Duplicate terrain "+type);found=row;}
        return found??throw new InvalidDataException("Missing terrain "+type);
    }
    static DetectionSettings Read(FogOfWarConfig c)=>new(c.MaxFlashValue,c.SpottedPenalty,c.SpottedPenaltyBuildings,Terrain(c,Forest).Cover,Terrain(c,Buildings).Cover);
    static void Write(FogOfWarConfig c,DetectionSettings s)
    {
        var forest=Terrain(c,Forest);var buildings=Terrain(c,Buildings);
        c.MaxFlashValue=s.MaxFlashValue;c.SpottedPenalty=s.SpottedPenalty;c.SpottedPenaltyBuildings=s.SpottedPenaltyBuildings;
        forest.Cover=s.ForestCover;buildings.Cover=s.BuildingCover;
    }
    static void Before()
    {
        FogOfWarConfig cfg=null;
        try
        {
            cfg=GameConfig.Instance?.FogOfWarConfig??throw new InvalidDataException("Fog config missing");
            vanilla??=Read(cfg);
            bool apply=Runtime.IsApplied;
            var before=Read(cfg);
            var want=apply?target:vanilla;
            Write(cfg,want);
            var after=Read(cfg);
            if(!after.Same(want))throw new InvalidDataException("Read-back mismatch");
            Log("before",new{apply,before,after});
        }
        catch(Exception e)
        {
            if(cfg!=null&&vanilla!=null)try{Write(cfg,vanilla);}catch{}
            MelonLogger.Error("FREEDOM_ARROW_DETECTION_FAILED: vanilla config kept. "+e.Message);
        }
    }
    static void After()
    {
        try
        {
            var cfg=GameConfig.Instance?.FogOfWarConfig;
            Log("after",new{game=cfg?.Pointer.ToInt64(),fog=FogOfWarSystem.Instance?._config?.Pointer.ToInt64(),shooting=ShootingSystem._fogOfWarConfig?.Pointer.ToInt64(),
                current=cfg==null?null:Read(cfg)});
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_DETECTION_FAILED: after check. "+e.Message);}
    }
}
