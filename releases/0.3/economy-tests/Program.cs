using System.Text.Json;
using FreedomArrow.Conquest;
int checks = 0;
void Check(bool yes, string why) { if (!yes) throw new Exception(why); checks++; }
void Throws(Action action, string why)
{ try { action(); } catch { checks++; return; } throw new Exception("Expected rejection: " + why); }
Check(Math.Abs(EconomyWindow.PerSecond(200)*60-200)<0.0001, "minute/second conversion");
foreach (float bad in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity,-1,0,5001})
    Throws(()=>EconomyWindow.PerSecond(bad), "invalid configured income");
new Settings { FixedIncomePerMinute = 200 }.Validate(); checks++;
new Settings { FixedIncomePerMinute = 0 }.Validate(); checks++;
Throws(()=>new Settings { FixedIncomePerMinute = float.NaN }.Validate(), "configuration NaN");
var window = new EconomyWindow();
var original = new EconomyState(true, 1.6666666f, 0.15f);
var state = original;
void Write(EconomyState s) => state = s;
Throws(()=>window.Begin(()=>throw new Exception("injected snapshot failure"),Write),"snapshot failure");
Check(!window.Active && state==original,"snapshot failure does not leave an active window");
window.Begin(()=>state,Write);
Check(window.Active && state == new EconomyState(false,0,0), "both native reductions scoped off");
Throws(()=>window.Begin(()=>state,Write), "nested transaction");
window.End(Write);
Check(!window.Active && state == original, "full restoration");
window.End(Write);Check(state==original, "idempotent close");
// A setter can fail after changing some state. Begin must retain the original snapshot.
Throws(()=>window.Begin(()=>state,s=>{state=s;throw new Exception("injected partial write");}), "partial begin");
Check(window.Active,"rollback remains pending");window.End(Write);Check(state==original,"partial begin rollback");
window.Begin(()=>state,Write);
Throws(()=>window.End(s=>throw new Exception("injected restore fault")),"restore fault");
Check(window.Active,"failed restore can retry");window.End(Write);Check(state==original,"restore retry");
// New sessions must not be overwritten with an older session's saved globals.
window.Begin(()=>state,Write);state=new EconomyState(false,0.7f,0.2f);window.Discard();
window.End(Write);Check(state==new EconomyState(false,0.7f,0.2f),"discard preserves newer owner");
for(int i=0;i<3;i++)
{var before=state;window.Begin(()=>state,Write);window.End(Write);Check(state==before,"repeat lifecycle");}
// Online, the native clock can be running before the mode starts. Ticks keep their absolute schedule.
var noZones=new List<Zone>();var lateSettings=new Settings{OpeningDelaySeconds=180,TickSeconds=30};lateSettings.Validate();
var late=new Ledger(lateSettings,"map",2700);Check(late.Advance(80,noZones).Count==0&&late.NextTick==lateSettings.OpeningDelaySeconds,"late attach before the opening delay keeps the first tick");
var later=new Ledger(lateSettings,"map",2700);later.Advance(lateSettings.OpeningDelaySeconds+95,noZones);Check(later.NextTick==300&&later.MissedTicks==0,"late attach joins the shared schedule");
var hitch=new Ledger(lateSettings,"map",2700);hitch.Advance(0,noZones);Check(hitch.Advance(lateSettings.OpeningDelaySeconds+65,noZones).Count==0&&hitch.MissedTicks==3&&hitch.NextTick==lateSettings.OpeningDelaySeconds+90,"a long stall skips ticks and does not fault");Check(hitch.Advance(lateSettings.OpeningDelaySeconds+90,noZones).Count==1,"scoring continues after a stall");
Check(Math.Abs(FreedomArrow.CoverDamagePolicy.Factor(0.7f,0)-0.7f)<1e-6,"forest total");
Check(FreedomArrow.CoverDamagePolicy.Factor(0.7f,1)==1&&Math.Abs(FreedomArrow.CoverDamagePolicy.Factor(0.7f,0.5f)-0.85f)<1e-6,"IgnoreCover removes protection in proportion");
Throws(()=>FreedomArrow.CoverDamagePolicy.Factor(0,0),"zero taken refused");
// [FA] Central Village zone values, from the packaged settings.
var fa=JsonSerializer.Deserialize<Settings>(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"../../../../source/UserData/FAConquestPrototype/settings.json")),new JsonSerializerOptions{PropertyNameCaseInsensitive=true})!;fa.Validate();
const string cv="[FA] Central Village";var cvIds=Enumerable.Range(53,10).ToArray();
Check(cvIds.Select(i=>fa.Weight(cv,i)).SequenceEqual(new[]{4,4,3,3,2,2,4,4,4,4})&&fa.Weight("other map",53)==1,"Central Village zone values");
Check(fa.ZoneLabel(cv,53)=="+4"&&fa.ZoneLabel(cv,55)=="+3"&&fa.ZoneLabel(cv,57)=="+2"&&fa.ZoneLabel("other map",53)=="+1","zone labels");
Check(new[]{31,32,33,35,36,37,50,159,178,179}.Select(i=>fa.Weight("[FA] Central Village Skirmish",i)).SequenceEqual(new[]{4,4,3,3,2,2,4,4,4,4}),"Central Village Skirmish zone values");
Check(fa.OpeningDelaySeconds==300&&fa.RoundBanner(0)=="ROUND 1: NO SCORING  5:00"&&fa.RoundBanner(299.5)=="ROUND 1: NO SCORING  0:01"&&fa.RoundBanner(300)=="ROUND 2: ZONES SCORE"&&fa.RoundBanner(308)==null,"round banner");
var faLedger=new Ledger(fa,cv,2700);var faHeld=new List<Zone>{new(53,0,false)};Check(faLedger.Advance(299,faHeld).Count==0&&faLedger.Advance(300,faHeld).Count==1&&faLedger.Alpha==4,"no score before 5:00, first tick at 5:00");
Check(fa.Ending=="score_or_time"&&fa.ScoreLimit==300,"first to 300");
var faWin=new Ledger(fa,cv,2700);var faAll=cvIds.Select(i=>new Zone(i,1,false)).ToList();
for(int t=300;t<=510;t+=30)faWin.Advance(t,faAll);Check(faWin.Bravo==272&&!faWin.ReachedScoreLimit,"272 of 300 does not end the match");
faWin.Advance(540,faAll);Check(faWin.Bravo==306&&faWin.ReachedScoreLimit&&faWin.ScoreLimitWinner==1&&faWin.Finished,"300 ends the match at 9:00 at the fastest");
Check(fa.ResolveMap(Settings.OnlineUnknownMap,cvIds)==cv&&fa.ResolveMap(Settings.OnlineUnknownMap,cvIds.Skip(1))==Settings.OnlineUnknownMap&&fa.ResolveMap("other map",cvIds)=="other map","Central Village map resolution");
var cvTick=new Ledger(fa,cv,2700).Forecast(new List<Zone>{new(53,0,false),new(54,0,false),new(57,0,false),new(55,1,false),new(62,1,true)});
Check(cvTick.AlphaHeld==10&&cvTick.BravoHeld==3&&cvTick.Alpha==7&&cvTick.Bravo==0,"Central Village weighted advantage");
Console.WriteLine($"PASS: {checks} host policy/configuration checks. No native hook, HUD, credit or upkeep measurement.");
