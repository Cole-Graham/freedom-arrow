using BAModManager.Core;
int n=0; void Check(bool v,string l){if(!v)throw new Exception("FAIL "+l);n++;Console.WriteLine("PASS "+l);}
var g=Path.Combine(Path.GetTempPath(),"fa-fm-"+Guid.NewGuid().ToString("N"));var mods=Path.Combine(g,"Mods");Directory.CreateDirectory(mods);Directory.CreateDirectory(Path.Combine(g,"Plugins"));
void W(string rel,string text){var p=Path.Combine(g,rel);Directory.CreateDirectory(Path.GetDirectoryName(p)!);File.WriteAllText(p,text);}
bool E(string rel)=>File.Exists(Path.Combine(g,rel));
var own=new[]{"Mods/FreedomArrow.Runtime.dll","Mods/FAArrowQueue.dll","Mods/FAFlatIncomeMod.dll","Mods/FAModels.dll","Plugins/FAPlugin.dll","UserData/FreedomArrow/x.json"};
foreach(var o in own)W(o,"fa");
W("Mods/MLDatabaseMod.dll","aa");W("Mods/FlatIncomeMod.dll","aa");W("Mods/FAOldThing.dll","old fa");W("Mods/FastLoad.dll","other");
Action<string> log=s=>Console.WriteLine("  log: "+s);
// PLAY: park foreign, switch off stale FA
ForeignMods.Park(g,own,log);
Check(!E("Mods/MLDatabaseMod.dll")&&E("FA-parked-mods/MLDatabaseMod.dll"),"AA DLL parked for an FA game");
Check(!E("Mods/FlatIncomeMod.dll")&&E("FA-parked-mods/FlatIncomeMod.dll"),"AA FlatIncomeMod parked (FA ships FAFlatIncomeMod)");
Check(E("FA-parked-mods/FastLoad.dll"),"FastLoad (FA + lower case) treated as another mod");
Check(!E("Mods/FAOldThing.dll")&&E("Mods/FAOldThing.dll.disabled")&&!E("FA-parked-mods/FAOldThing.dll"),"old FA DLL switched off, not parked");
Check(own.Where(o=>o.EndsWith(".dll")).All(E),"FA DLLs stay for the FA game");
// Play vanilla / other mods
ForeignMods.DisableOwn(g,log);ForeignMods.Restore(g,log);
Check(own.Where(o=>o.EndsWith(".dll")).All(o=>!E(o)&&E(o+".disabled")),"FA DLLs switched off in Mods and Plugins");
Check(E("Mods/MLDatabaseMod.dll")&&E("Mods/FlatIncomeMod.dll")&&E("Mods/FastLoad.dll"),"other mods' DLLs back in Mods");
Check(E("UserData/FreedomArrow/x.json"),"FA data files untouched");
// an older launcher parked an FA DLL: not handed back
W("FA-parked-mods/FAModelsOld.dll","x");ForeignMods.Restore(g,log);Check(!E("Mods/FAModelsOld.dll"),"parked FA DLL is not given to other mods");
// PLAY again
ForeignMods.EnableOwn(g,own,log);ForeignMods.Park(g,own,log);
Check(own.Where(o=>o.EndsWith(".dll")).All(E),"FA DLLs back on for PLAY");
Check(!E("Mods/MLDatabaseMod.dll")&&!E("Mods/FastLoad.dll"),"other mods parked again");
Check(!E("Mods/FAOldThing.dll"),"stale FA DLL stays off");
// a working copy wins over a .disabled one
W("Mods/FAModels.dll.disabled","older");ForeignMods.EnableOwn(g,own,log);Check(File.ReadAllText(Path.Combine(g,"Mods/FAModels.dll"))=="fa","working copy wins");
Directory.Delete(g,true);Console.WriteLine("{\"checks\":"+n+"}");
