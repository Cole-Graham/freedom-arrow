using System.Text.Json;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
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
    static float startingPoints;
    static float? originalPoints;
    static float buildingFloor,buildingPerSoldier;
    static (float floor,float perSoldier)? originalBuilding;
    static float minorMobility;
    static float? originalMinorMobility;
    // Suppression move speed (Lateralus batch, 8 November 2026): Buff Config StressModifiers[Shocked/Panicked].MovementSpeedMultiplier, vanilla 0.6 / 0.2.
    static float shockedSpeed,panickedSpeed;
    static (float shocked,float panicked)? originalStressSpeed;
    // Flare re-roll cap (Lateralus batch, 9 November 2026): BattleSystemSettings.MAX_FLARES_COUNT_MISSILE_REROLL, vanilla 1.
    // A missile re-rolls at each new flare; this is how many burning flares that re-roll counts (MissileHitChance.cs).
    static int flareRerollCap;
    static int? originalFlareRerollCap;
    static void WriteBuildings()
    {
        var b=GameConfig.Instance?.BuildingsConfig??throw new InvalidDataException("Buildings config missing");
        originalBuilding??=(b.DamageModifierFloor,b.DamageModifierPerSoldier);
        (b.DamageModifierFloor,b.DamageModifierPerSoldier)=Runtime.IsApplied?(buildingFloor,buildingPerSoldier):originalBuilding.Value;
        MelonLogger.Msg($"FREEDOM_ARROW_BUILDING_DAMAGE floor {b.DamageModifierFloor} perSoldier {b.DamageModifierPerSoldier}");
        // Yellow mobility crit speed. The battle systems keep this same config object.
        var buff=GameConfig.Instance.BuffConfig??throw new InvalidDataException("Buff config missing");
        originalMinorMobility??=buff.MinorMobilityMultiplier;
        buff.MinorMobilityMultiplier=Runtime.IsApplied?minorMobility:originalMinorMobility.Value;
        MelonLogger.Msg($"FREEDOM_ARROW_YELLOW_MOBILITY speed {buff.MinorMobilityMultiplier} turn {buff.MinorMobilityMultiplierRotation}");
        var shocked=buff.StressModifiers[StressLevel.Shocked];var panicked=buff.StressModifiers[StressLevel.Panicked];
        originalStressSpeed??=(shocked.MovementSpeedMultiplier,panicked.MovementSpeedMultiplier);
        (shocked.MovementSpeedMultiplier,panicked.MovementSpeedMultiplier)=Runtime.IsApplied?(shockedSpeed,panickedSpeed):originalStressSpeed.Value;
        MelonLogger.Msg($"FREEDOM_ARROW_STRESS_SPEED shocked {shocked.MovementSpeedMultiplier} panicked {panicked.MovementSpeedMultiplier}");
        var battle=GameConfig.Instance.BattleSystemSettings??throw new InvalidDataException("Battle system settings missing");
        originalFlareRerollCap??=battle.MAX_FLARES_COUNT_MISSILE_REROLL;
        battle.MAX_FLARES_COUNT_MISSILE_REROLL=Runtime.IsApplied?flareRerollCap:originalFlareRerollCap.Value;
        MelonLogger.Msg($"FREEDOM_ARROW_FLARE_REROLL_CAP {battle.MAX_FLARES_COUNT_MISSILE_REROLL} (initial roll {battle.MAX_FLARES_COUNT_MISSILE_INITIAL})");
    }
    static void Log(string stage,object data)=>MelonLogger.Msg("FREEDOM_ARROW_DETECTION "+stage+" "+JsonSerializer.Serialize(data));
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        target=DetectionSettings.Parse(File.ReadAllText(Path.Combine(root,"detection-config.json")));
        harmony.Patch(AccessTools.Method(typeof(EcsLoader),"InitBattleSequentialSystem"),
            prefix:new HarmonyMethod(typeof(DetectionConfig),nameof(Before)),postfix:new HarmonyMethod(typeof(DetectionConfig),nameof(After)));
        var game=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")));
        startingPoints=game["DefaultPlayerMoney"].GetValue<float>();
        if(!(startingPoints>=0&&startingPoints<=5000))throw new InvalidDataException("DefaultPlayerMoney out of range");
        buildingFloor=game["BuildingDamageFloor"].GetValue<float>();buildingPerSoldier=game["BuildingDamagePerSoldier"].GetValue<float>();
        if(!(buildingFloor>=0&&buildingFloor<=1&&buildingPerSoldier>=0&&buildingPerSoldier<=0.1f))throw new InvalidDataException("Building damage settings out of range");
        minorMobility=game["MinorMobilityMultiplier"].GetValue<float>();
        if(!(minorMobility>0&&minorMobility<=1))throw new InvalidDataException("MinorMobilityMultiplier out of range");
        shockedSpeed=game["ShockedMoveSpeed"].GetValue<float>();panickedSpeed=game["PanickedMoveSpeed"].GetValue<float>();
        if(!(shockedSpeed>0&&shockedSpeed<=1&&panickedSpeed>0&&panickedSpeed<=1))throw new InvalidDataException("Stress move speed out of range");
        flareRerollCap=game["FlareRerollCap"].GetValue<int>();
        if(!(flareRerollCap>=1&&flareRerollCap<=100))throw new InvalidDataException("FlareRerollCap out of range");
        harmony.Patch(AccessTools.Method(typeof(ScenarioController),"LoadTeamsAndPlayers"),prefix:new HarmonyMethod(typeof(DetectionConfig),nameof(BeforePlayers)));
        Log("installed",new{target,startingPoints,status="invocation unproved until a before line appears"});
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
    // Scenario lobby options can still set their own starting points after this.
    static void BeforePlayers()
    {
        try
        {
            var game=GameConfig.Instance??throw new InvalidDataException("Game config missing");
            originalPoints??=game.DefaultPlayerMoney;
            game.DefaultPlayerMoney=Runtime.IsApplied?startingPoints:originalPoints.Value;
            MelonLogger.Msg($"FREEDOM_ARROW_START_POINTS {game.DefaultPlayerMoney}");
            WriteBuildings();
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_START_POINTS_FAILED: "+e.Message);}
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
            WriteBuildings();
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
