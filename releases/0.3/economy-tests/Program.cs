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
Check(Math.Abs(FreedomArrow.CoverDamagePolicy.Factor(0.6f,0)-0.6f)<1e-6&&Math.Abs(FreedomArrow.CoverDamagePolicy.Factor(0.3f,0)-0.3f)<1e-6,"cover totals");
Check(FreedomArrow.CoverDamagePolicy.Factor(0.3f,1)==1&&Math.Abs(FreedomArrow.CoverDamagePolicy.Factor(0.6f,0.5f)-0.8f)<1e-6,"IgnoreCover removes protection in proportion");
Throws(()=>FreedomArrow.CoverDamagePolicy.Factor(0,0),"zero taken refused");
Console.WriteLine($"PASS: {checks} host policy/configuration checks. No native hook, HUD, credit or upkeep measurement.");
