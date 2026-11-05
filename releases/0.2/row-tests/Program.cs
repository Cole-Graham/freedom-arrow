using System.Text.Json.Nodes;
using FreedomArrow;
if(args.Length!=2)throw new ArgumentException("pinned vanilla JSON directory and package payload root required");
string vanilla=args[0],root=args[1];int checks=0,writes=0;var merged=new Dictionary<string,JsonArray>();var allPatches=new Dictionary<string,JsonObject>();
void Check(bool yes,string why){if(!yes)throw new Exception(why);checks++;}
var compatibility=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"compatibility.json"))).AsObject();
var files=JsonNode.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"table-files.json"))).AsObject();
foreach(var entry in files){string t=entry.Key,f=entry.Value.GetValue<string>();var source=JsonNode.Parse(File.ReadAllText(Path.Combine(vanilla,t+".json"))).AsArray();var original=source.ToJsonString();var patches=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"constants",f))).AsObject();
allPatches[t]=patches;merged[t]=RowPlanner.Apply(source,patches,true,(id,field,before,after,added)=>writes++);Check(source.ToJsonString()==original,t+" source mutation");Check(merged[t].Count==source.Count+patches.Count(p=>p.Value!=null&&!source.Any(row=>row["Id"].ToJsonString()==p.Key))-patches.Count(p=>p.Value==null),t+" row count");}
JsonNode Row(string t,int id)=>merged[t].Single(r=>r["Id"].GetValue<int>()==id);
foreach(var rule in JsonNode.Parse(File.ReadAllText(Path.Combine(root,"reference-schema.json"))).AsObject()){
var patches=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"constants",files[rule.Key].GetValue<string>()))).AsObject();
foreach(var patch in patches)foreach(var link in rule.Value.AsObject())if(patch.Value!=null&&patch.Value.AsObject().ContainsKey(link.Key)){
int id=patch.Value[link.Key].GetValue<int>();bool nullable=link.Value[1].GetValue<bool>();Check(id==0&&nullable||merged[link.Value[0].GetValue<string>()].Any(r=>r["Id"].GetValue<int>()==id),rule.Key+" dangling "+link.Key);}}
Check(merged["Units"].Count==552,"only the seven card splits may add a unit");Check(Row("Units",628)["Cost"].GetValue<int>()==25,"Uran default loadout totals 70");Check(Row("Units",703)["Cost"].GetValue<int>()==105,"T-72B3A 105");Check(Row("Units",252)["Cost"].GetValue<int>()==50,"BRDM Konkurs 50");
foreach(var pair in new[]{(716,564,190),(716,566,230),(717,3033,80),(718,1905,80),(719,381,85),(720,1949,110),(714,2049,90),(714,2050,90),(715,480,35),(214,2101,35),(214,491,55),(214,492,60),(214,493,75),(9,625,100)})Check(Row("Units",pair.Item1)["Cost"].GetValue<int>()+Row("OptionsJson",pair.Item2)["Cost"].GetValue<int>()==pair.Item3,"configured cost "+pair);
Check(Row("ArmorsJson",2000000)["MaxHealthPoints"].GetValue<int>()==8,"shared BRDM3 base changed");Check(Row("ArmorsJson",2000096)["MaxHealthPoints"].GetValue<int>()==12,"Vilkas shared armor changed");Check(Row("ArmorsJson",2000100)["HeatArmorSides"].GetValue<int>()==100,"B10/B11 buff leak");
int[] expectHpOptions={504,505,1881,1882,3067,3070,3071,3072};foreach(int id in expectHpOptions){int armor=Row("OptionsJson",id)["ArmorId"].GetValue<int>();Check(Row("ArmorsJson",armor)["MaxHealthPoints"].GetValue<int>()==(id<3000?10:8),"HP "+id);}
Check(Row("OptionsJson",2082)["Ability2Id"].GetValue<int>()==82&&Row("UnitAbilitiesJson",1029)["AbilityId"].GetValue<int>()==82,"AMPV invariant");
foreach(int id in new[]{12,23,505,701,713})Check(Row("AmmunitionsJson",id)["Damage"].GetValue<double>()==10,"tank sabot "+id);
foreach(int id in new[]{44,508,2000149,2000174})Check(Row("AmmunitionsJson",id)["Damage"].GetValue<double>()==10.5,"Javelin "+id);
Check(Row("AmmunitionsJson",506)["Damage"].GetValue<double>()==2.5,"XM913 excluded");Check(Row("AmmunitionsJson",498)["Damage"].GetValue<double>()==8.5,"MT12 pending");
foreach(int id in new[]{2000013,2000014,2000015})Check(Row("ArmorsJson",id)["MaxHealthPoints"].GetValue<int>()==12,"core Bradley HP "+id);
Check(Row("ArmorsJson",2000052)["MaxHealthPoints"].GetValue<int>()==12&&Row("ArmorsJson",2000052)["HeatArmorRear"].GetValue<int>()==400&&Row("ArmorsJson",2000052)["HeatArmorSides"].GetValue<int>()==60,"ACV literal rear");
foreach(int id in new[]{8,1894,25,42}){int aid=Row("OptionsJson",id)["ArmorId"].GetValue<int>();Check(Row("ArmorsJson",aid)["HeatArmorFront"].GetValue<int>()==600&&Row("ArmorsJson",aid)["HeatArmorSides"].GetValue<int>()==600&&Row("ArmorsJson",aid)["MaxHealthPoints"].GetValue<int>()==12,"selected SRAT "+id);}
Check(Row("ArmorsJson",2000017)["MaxHealthPoints"].GetValue<int>()==12&&Row("ArmorsJson",2000018)["MaxHealthPoints"].GetValue<int>()==12,"RV/ATGM SRAT uparmor HP");
foreach(int id in new[]{2000017,2000018})Check(Row("ArmorsJson",id)["HeatArmorFront"].GetValue<int>()==250&&Row("ArmorsJson",id)["HeatArmorSides"].GetValue<int>()==200,"RV/ATGM SRAT armor "+id);
foreach(var (option,armor,front,side,hp) in new[]{(56,47,400,250,14),(1781,288,700,400,14)}){var row=Row("ArmorsJson",armor);Check(Row("OptionsJson",option)["ArmorId"].GetValue<int>()==armor&&row["HeatArmorFront"].GetValue<int>()==front&&row["HeatArmorSides"].GetValue<int>()==side&&row["MaxHealthPoints"].GetValue<int>()==hp,"M6 Linebacker option "+option);}
Check(Row("ArmorsJson",15)["MaxHealthPoints"].GetValue<int>()==14,"M6 Linebacker base HP");
Check(Row("OptionsJson",1759)["Cost"].GetValue<int>()==25,"M2A3 ESV BUSK3 +25");
Check(Row("AmmunitionsJson",2000177)["Damage"].GetValue<double>()==10.5,"Spike LR");Check(Row("AmmunitionsJson",2000173)["Damage"].GetValue<double>()==12,"Spike-SR held");
foreach(var triple in new[]{(14,1904,90),(180,1958,40),(185,388,30),(41,60,40),(41,2082,70)})Check(Row("Units",triple.Item1)["Cost"].GetValue<int>()+Row("OptionsJson",triple.Item2)["Cost"].GetValue<int>()==triple.Item3,"US configured "+triple);
Check(Row("Units",421)["Cost"].GetValue<int>()+new[]{1866,1871,1875}.Sum(i=>Row("OptionsJson",i)["Cost"].GetValue<int>())==50,"Battleship defaults provisional50");
// Detection proposal. Expected values are written here again on purpose, independent of the generator contract.
// Values come from the contract, so tuning needs no test edit. The class rules are written out here on purpose.
var contract=JsonNode.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"detection-contract.json"))).AsObject();
var tiers=contract["optics_ground_tiers"].AsObject().ToDictionary(x=>double.Parse(x.Key),x=>x.Value.GetValue<double>());
var heldSensors=contract["optics_held_sensors"].AsArray().Select(x=>x.GetValue<int>()).ToArray();var drones=contract["optics_ground_drones"].AsObject().ToDictionary(x=>int.Parse(x.Key),x=>x.Value.GetValue<double>());
var unitStealth=contract["stealth_unit_values"].AsObject().ToDictionary(x=>int.Parse(x.Key),x=>x.Value.GetValue<double>());var classStealth=contract["stealth"].AsObject();
JsonArray Vanilla(string t)=>JsonNode.Parse(File.ReadAllText(Path.Combine(vanilla,t+".json"))).AsArray();
foreach(var s in Vanilla("SensorsJson")){int id=s["Id"].GetValue<int>();var m=Row("SensorsJson",id);double g=s["OpticsGround"].GetValue<double>();
Check(m["OpticsGround"].GetValue<double>()==(heldSensors.Contains(id)?g:drones.TryGetValue(id,out var drone)?drone:tiers[g]),"optics "+id);Check(m["OpticsLowAltitude"].GetValue<double>()==s["OpticsLowAltitude"].GetValue<double>()&&m["OpticsHighAltitude"].GetValue<double>()==s["OpticsHighAltitude"].GetValue<double>(),"air optics "+id);}
foreach(var u in Vanilla("Units")){int id=u["Id"].GetValue<int>(),type=u["Type"].GetValue<int>(),cat=u["CategoryType"].GetValue<int>(),role=u["Role"].GetValue<int>();var m=Row("Units",id);double s=u["Stealth"].GetValue<double>();
double want=unitStealth.TryGetValue(id,out var unitValue)?unitValue:type==4&&cat!=4?classStealth["vehicle"].GetValue<double>():type!=2||cat==4?s:s==0.333?classStealth["sniper"].GetValue<double>():cat==0?classStealth["recon_infantry"].GetValue<double>():classStealth["infantry"].GetValue<double>();
Check(m["Stealth"].GetValue<double>()==want&&m["CurrentStealth"].GetValue<double>()==want,"stealth "+id);}
foreach(var o in contract["stealth_override_options"].AsObject())Check(Row("OptionsJson",int.Parse(o.Key))["StealthOverride"].GetValue<double>()==o.Value.GetValue<double>(),"recon override "+o.Key);
foreach(int id in new[]{478,479,506,507,1708,1711,1712,1896,1897})Check(Row("OptionsJson",id)["StealthOverride"].GetValue<double>()==1,"recon option at 1.0 "+id);
Check(Row("OptionsJson",1486)["StealthOverride"].GetValue<double>()==0.4&&Row("OptionsJson",3074)["StealthOverride"].GetValue<double>()==0.5,"held overrides");
var detection=DetectionSettings.Parse(File.ReadAllText(Path.Combine(root,"detection-config.json")));
Check(detection.ForestCover>=1&&detection.BuildingCover>=1,"detection config values");
foreach(string bad in new[]{"{}","{\"MaxFlashValue\":0.5,\"SpottedPenalty\":1.5,\"SpottedPenaltyBuildings\":1.5,\"ForestCover\":3,\"BuildingCover\":4}","{\"MaxFlashValue\":2.2,\"SpottedPenalty\":1.5,\"SpottedPenaltyBuildings\":1.5,\"ForestCover\":3}"})
{bool refused=false;try{DetectionSettings.Parse(bad);}catch(InvalidDataException){refused=true;}Check(refused,"bad detection config accepted");}
// dev.11 recon prices and the uparmor HP rule. Written here again on purpose, independent of the generator contract.
foreach(var (id,cost) in new[]{(152,20),(23,25),(209,50),(238,230),(217,45),(455,25),(458,40),(173,25),(383,50),(167,25),(215,40),(48,30),(99,25),(29,40),(2,240),(387,60),(37,80),(16,65),(26,55),(186,50),(51,40),(249,35),(35,25),(21,40),(49,35),(467,30),(184,35),(543,45),(499,35),(505,35),(425,30),(1,35)})Check(Row("Units",id)["Cost"].GetValue<int>()==cost,"dev.11 price "+id);
foreach(var (id,cost) in new[]{(1960,5),(1961,10),(478,0),(479,40),(1708,55),(50,20),(2049,0),(2050,0),(480,0),(2047,0),(2048,0),(1710,20)})Check(Row("OptionsJson",id)["Cost"].GetValue<int>()==cost,"dev.11 option "+id);
foreach(var (id,hp) in new[]{(2000103,12),(2000104,12),(326,12),(336,12),(2000020,10),(2000021,10),(2000022,10),(2000023,10),(2000221,14),(2000003,12),(2000004,12),(120,14)})Check(Row("ArmorsJson",id)["MaxHealthPoints"].GetValue<int>()==hp,"dev.11 HP "+id);
foreach(var u in Vanilla("Units")){int id=u["Id"].GetValue<int>();if(u["Type"].GetValue<int>()!=4)continue;Check(merged["UnitArmorsJson"].Where(l=>l["UnitId"].GetValue<int>()==id).Select(l=>Row("ArmorsJson",l["ArmorId"].GetValue<int>())["MaxHealthPoints"].GetValue<int>()).Distinct().Count()<=1,"uparmor changes HP "+id);}
// dev.17 structural checks. Written here again on purpose, independent of the generator contract.
IEnumerable<int> Linked(string t,string f,int u)=>merged[t].Where(r=>r["UnitId"].GetValue<int>()==u).Select(r=>r[f].GetValue<int>()).OrderBy(x=>x);
string WName(int w)=>w==0?"":Row("WeaponsJson",w)["Name"].GetValue<string>();
JsonNode[] Members(int u)=>merged["SquadMembersJson"].Where(r=>r["UnitId"].GetValue<int>()==u).ToArray();
int Carry(int u,string w)=>Members(u).Count(m=>WName(m["PrimaryWeaponId"].GetValue<int>()).Contains(w)||WName(m["SpecialWeaponId"].GetValue<int>()).Contains(w));
foreach(var (u,size) in new[]{(66,5),(147,5),(343,5),(408,5),(320,8),(110,5),(352,5),(402,8),(128,7),(355,7)}){Check(Members(u).Length==size,"team size "+u);Check(Carry(u,"ATGM")==1,"one launcher "+u);}
Check(Carry(519,"ATGM")==2,"Baltic Milan keeps two for now");Check(Carry(701,"AT4")==6&&Members(701).Length==9,"Troopers six AT-4 carriers");Check(Carry(62,"ATGM")==1,"Troopers AT one Javelin");
foreach(int u in new[]{66,147,343,408})Check(Linked("UnitArmorsJson","ArmorId",u).All(a=>Row("ArmorsJson",a)["MaxHealthPoints"].GetValue<int>()==25),"five-man health "+u);
int PoolOf(int u)=>merged["SpecializationAvailabilitiesJson"].Single(r=>r["UnitId"].GetValue<int>()==u)["MaxAvailabilityXp0"].GetValue<int>();
foreach(var (u,n) in new[]{(467,4),(714,2),(209,2),(715,2),(158,3),(716,3),(615,3),(717,3),(14,3),(718,3),(183,2),(719,2),(453,3),(720,3),(701,8),(62,4),(320,4),(408,4)})Check(PoolOf(u)==n,"availability "+u);
foreach(int o in new[]{565,1462,1775,1792,1895,1898,1931,1939,2117,1951,1843,1844,3316,3317})Check(merged["OptionsJson"].All(r=>r["Id"].GetValue<int>()!=o),"deleted option "+o);
foreach(int m in new[]{515,804})Check(merged["ModificationsJson"].All(r=>r["Id"].GetValue<int>()!=m),"deleted menu "+m);
foreach(var u in merged["Units"].Select(r=>r["Id"].GetValue<int>())){var sw=merged["SquadWeaponsJson"].Where(r=>r["UnitId"].GetValue<int>()==u).Select(r=>r["WeaponId"].GetValue<int>()).ToArray();Check(sw.Distinct().Count()==sw.Length,"squad weapons unique "+u);foreach(var m in merged["SquadMembersJson"].Where(r=>r["UnitId"].GetValue<int>()==u))foreach(var f in new[]{"PrimaryWeaponId","SpecialWeaponId"}){int w=m[f].GetValue<int>();Check(w==0||sw.Contains(w),"member weapon listed "+u+" "+w);}}
foreach(var o in merged["OptionsJson"])Check(merged["ModificationsJson"].Any(r=>r["Id"].GetValue<int>()==o["ModificationId"].GetValue<int>()),"option menu exists "+o["Id"]);
foreach(var (u,cost) in new[]{(110,65),(352,95),(320,90),(408,105),(147,80),(343,100),(62,110),(701,70)})Check(Row("Units",u)["Cost"].GetValue<int>()==cost,"infantry price "+u);
foreach(var (u,turrets) in new[]{(158,new[]{417,418}),(716,new[]{206,207}),(14,new[]{12,110}),(718,new[]{895,896}),(209,new[]{346,348,818}),(715,new[]{347}),(467,new[]{957,959,961}),(714,new[]{958,960,961})})Check(Linked("TurretUnitsJson","TurretId",u).SequenceEqual(turrets.OrderBy(x=>x)),"split turrets "+u);
WeaponCoverage.Validate(merged,allPatches);checks++;
Console.WriteLine($"PASS: {checks} real RowPlanner/harness-reference checks; {writes} planned field writes across24 tables; native database/models/armory untested.");
