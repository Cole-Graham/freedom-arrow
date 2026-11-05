using System.Text.Json.Nodes;
using FreedomArrow;
if(args.Length!=2)throw new ArgumentException("pinned vanilla JSON directory and package payload root required");
string vanilla=args[0],root=args[1];int checks=0,writes=0;var merged=new Dictionary<string,JsonArray>();
void Check(bool yes,string why){if(!yes)throw new Exception(why);checks++;}
var compatibility=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"compatibility.json"))).AsObject();
var files=JsonNode.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"table-files.json"))).AsObject();
foreach(var entry in files){string t=entry.Key,f=entry.Value.GetValue<string>();var source=JsonNode.Parse(File.ReadAllText(Path.Combine(vanilla,t+".json"))).AsArray();var original=source.ToJsonString();var patches=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"constants",f))).AsObject();
merged[t]=RowPlanner.Apply(source,patches,true,(id,field,before,after,added)=>writes++);Check(source.ToJsonString()==original,t+" source mutation");Check(merged[t].Count==source.Count+patches.Count(p=>!source.Any(row=>row["Id"].ToJsonString()==p.Key)),t+" row count");}
JsonNode Row(string t,int id)=>merged[t].Single(r=>r["Id"].GetValue<int>()==id);
foreach(var rule in JsonNode.Parse(File.ReadAllText(Path.Combine(root,"reference-schema.json"))).AsObject()){
var patches=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"constants",files[rule.Key].GetValue<string>()))).AsObject();
foreach(var patch in patches)foreach(var link in rule.Value.AsObject())if(patch.Value.AsObject().ContainsKey(link.Key)){
int id=patch.Value[link.Key].GetValue<int>();bool nullable=link.Value[1].GetValue<bool>();Check(id==0&&nullable||merged[link.Value[0].GetValue<string>()].Any(r=>r["Id"].GetValue<int>()==id),rule.Key+" dangling "+link.Key);}}
Check(merged["Units"].Count==545,"structural split leaked");Check(Row("Units",628)["Cost"].GetValue<int>()==50,"Uran ambiguous price held");Check(Row("Units",703)["Cost"].GetValue<int>()==240,"unfinished B3A held");Check(Row("Units",252)["Cost"].GetValue<int>()==55,"ambiguous Konkurs held");
foreach(var pair in new[]{(158,564,190),(158,565,200),(158,566,230),(615,3033,80),(214,2101,35),(214,491,55),(214,492,60),(214,493,75),(9,625,100)})Check(Row("Units",pair.Item1)["Cost"].GetValue<int>()+Row("OptionsJson",pair.Item2)["Cost"].GetValue<int>()==pair.Item3,"configured cost "+pair);
Check(Row("ArmorsJson",2000000)["MaxHealthPoints"].GetValue<int>()==8,"shared BRDM3 base changed");Check(Row("ArmorsJson",2000096)["MaxHealthPoints"].GetValue<int>()==12,"Vilkas shared armor changed");Check(Row("ArmorsJson",2000100)["HeatArmorSides"].GetValue<int>()==100,"B10/B11 buff leak");
int[] expectHpOptions={504,505,1881,1882,3067,3070,3071,3072};foreach(int id in expectHpOptions){int armor=Row("OptionsJson",id)["ArmorId"].GetValue<int>();Check(Row("ArmorsJson",armor)["MaxHealthPoints"].GetValue<int>()==(id<3000?10:8),"HP "+id);}
Check(Row("OptionsJson",2082)["Ability2Id"].GetValue<int>()==82&&Row("UnitAbilitiesJson",1029)["AbilityId"].GetValue<int>()==82,"AMPV invariant");
foreach(int id in new[]{12,23,505,701,713})Check(Row("AmmunitionsJson",id)["Damage"].GetValue<double>()==10,"tank sabot "+id);
foreach(int id in new[]{44,508,2000149,2000174})Check(Row("AmmunitionsJson",id)["Damage"].GetValue<double>()==10.5,"Javelin "+id);
Check(Row("AmmunitionsJson",506)["Damage"].GetValue<double>()==2.5,"XM913 excluded");Check(Row("AmmunitionsJson",498)["Damage"].GetValue<double>()==8.5,"MT12 pending");
foreach(int id in new[]{2000013,2000014,2000015})Check(Row("ArmorsJson",id)["MaxHealthPoints"].GetValue<int>()==12,"core Bradley HP "+id);
Check(Row("ArmorsJson",2000052)["MaxHealthPoints"].GetValue<int>()==12&&Row("ArmorsJson",2000052)["HeatArmorRear"].GetValue<int>()==400&&Row("ArmorsJson",2000052)["HeatArmorSides"].GetValue<int>()==60,"ACV literal rear");
foreach(int id in new[]{8,1894,25,1931,42,1895}){int aid=Row("OptionsJson",id)["ArmorId"].GetValue<int>();Check(Row("ArmorsJson",aid)["HeatArmorFront"].GetValue<int>()==600&&Row("ArmorsJson",aid)["HeatArmorSides"].GetValue<int>()==600&&Row("ArmorsJson",aid)["MaxHealthPoints"].GetValue<int>()==12,"selected SRAT "+id);}
Check(Row("ArmorsJson",2000017)["MaxHealthPoints"].GetValue<int>()==14,"RV/ATGM SRAT untouched");
foreach(int id in new[]{2000017,2000018})Check(Row("ArmorsJson",id)["HeatArmorFront"].GetValue<int>()==250&&Row("ArmorsJson",id)["HeatArmorSides"].GetValue<int>()==200,"RV/ATGM SRAT armor "+id);
foreach(var (option,armor,front,side,hp) in new[]{(56,47,400,250,16),(1781,288,700,400,17)}){var row=Row("ArmorsJson",armor);Check(Row("OptionsJson",option)["ArmorId"].GetValue<int>()==armor&&row["HeatArmorFront"].GetValue<int>()==front&&row["HeatArmorSides"].GetValue<int>()==side&&row["MaxHealthPoints"].GetValue<int>()==hp,"M6 Linebacker option "+option);}
Check(Row("ArmorsJson",15)["MaxHealthPoints"].GetValue<int>()==14,"M6 Linebacker base HP");
Check(Row("OptionsJson",1759)["Cost"].GetValue<int>()==20,"M2A3 ESV BUSK3 price open");
Check(Row("AmmunitionsJson",2000177)["Damage"].GetValue<double>()==10.5,"Spike LR");Check(Row("AmmunitionsJson",2000173)["Damage"].GetValue<double>()==12,"Spike-SR held");
foreach(var triple in new[]{(14,1904,90),(14,1905,80),(180,1958,40),(183,381,85),(453,1949,110),(185,388,30),(41,60,40),(41,2082,70)})Check(Row("Units",triple.Item1)["Cost"].GetValue<int>()+Row("OptionsJson",triple.Item2)["Cost"].GetValue<int>()==triple.Item3,"US configured "+triple);
Check(Row("Units",421)["Cost"].GetValue<int>()+new[]{1866,1871,1875}.Sum(i=>Row("OptionsJson",i)["Cost"].GetValue<int>())==50,"Battleship defaults provisional50");
// Detection proposal. Expected values are written here again on purpose, independent of the generator contract.
var tiers=new Dictionary<double,double>{[500]=900,[600]=1300,[700]=1450,[875]=1650,[1000]=2300,[1200]=2800};
int[] heldSensors={6,9,10,24,25,35};var drones=new Dictionary<int,double>{[32]=6400,[33]=5250,[34]=4650};
JsonArray Vanilla(string t)=>JsonNode.Parse(File.ReadAllText(Path.Combine(vanilla,t+".json"))).AsArray();
foreach(var s in Vanilla("SensorsJson")){int id=s["Id"].GetValue<int>();var m=Row("SensorsJson",id);double g=s["OpticsGround"].GetValue<double>();
Check(m["OpticsGround"].GetValue<double>()==(heldSensors.Contains(id)?g:drones.TryGetValue(id,out var drone)?drone:tiers[g]),"optics "+id);Check(m["OpticsLowAltitude"].GetValue<double>()==s["OpticsLowAltitude"].GetValue<double>()&&m["OpticsHighAltitude"].GetValue<double>()==s["OpticsHighAltitude"].GetValue<double>(),"air optics "+id);}
foreach(var u in Vanilla("Units")){int id=u["Id"].GetValue<int>(),type=u["Type"].GetValue<int>(),cat=u["CategoryType"].GetValue<int>(),role=u["Role"].GetValue<int>();var m=Row("Units",id);double s=u["Stealth"].GetValue<double>();
double want=id==445?s:type==4&&cat!=4?1.0:type!=2||cat==4?s:s==0.333?s:cat==0?0.4:0.5;
Check(m["Stealth"].GetValue<double>()==want&&m["CurrentStealth"].GetValue<double>()==want,"stealth "+id);}
foreach(int id in new[]{51,52,425,480,512,757,1713,2085,2086})Check(Row("OptionsJson",id)["StealthOverride"].GetValue<double>()==1,"vehicle override "+id);
Check(Row("OptionsJson",1486)["StealthOverride"].GetValue<double>()==0.4&&Row("OptionsJson",3074)["StealthOverride"].GetValue<double>()==0.5,"held overrides");
var detection=DetectionSettings.Parse(File.ReadAllText(Path.Combine(root,"detection-config.json")));
Check(detection.MaxFlashValue==2.2f&&detection.SpottedPenalty==1.5f&&detection.SpottedPenaltyBuildings==1.5f&&detection.ForestCover==3f&&detection.BuildingCover==4f,"detection config values");
foreach(string bad in new[]{"{}","{\"MaxFlashValue\":0.5,\"SpottedPenalty\":1.5,\"SpottedPenaltyBuildings\":1.5,\"ForestCover\":3,\"BuildingCover\":4}","{\"MaxFlashValue\":2.2,\"SpottedPenalty\":1.5,\"SpottedPenaltyBuildings\":1.5,\"ForestCover\":3}"})
{bool refused=false;try{DetectionSettings.Parse(bad);}catch(InvalidDataException){refused=true;}Check(refused,"bad detection config accepted");}
Console.WriteLine($"PASS: {checks} real RowPlanner/harness-reference checks; {writes} planned field writes across24 tables; native database/models/armory untested.");
