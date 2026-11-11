using System.Text.Json;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using FreedomArrow;
static class Program
{
    static int checks;
    static void Check(bool yes,string reason){if(!yes)throw new Exception(reason);checks++;}
    static void Main(string[] args)
    {
        var ready=AaObservationPolicy.Describe(true,false,100,false,false,false,false,true,true,true);
        Check(ready.Length==0,"Ready selected target has no invented rejection reason");
        var missing=AaObservationPolicy.Describe(true,false,100,false,false,false,false,false,false,false);
        Check(missing.SequenceEqual(new[]{"no_selected_target_native_reason_unknown"}),"No target does not claim range/visibility/overkill rejection");
        var busy=AaObservationPolicy.Describe(false,true,0,true,true,true,true,true,false,false);
        Check(busy.Length==9,"Concurrent observations are retained, rather than one fabricated priority cause");
        foreach(var tag in new[]{"weapon_disabled","hold_fire_component_present","empty_magazine","magazine_reloading","burst_cooldown","weapon_cycle_active","aiming_in_progress","selected_target_can_aim_false","selected_target_outside_margin"})
            Check(busy.Contains(tag),"Missing observed constraint "+tag);
        Check(!busy.Concat(ready).Concat(missing).Any(s=>s.Contains("overkill")),"Overkill flag must not be treated as a hard no-fire rule: lat.2 PIVADS fired while flagged");
        Check(AaObservationPolicy.AimingInProgress(true,0)==false,"Persistent zero-time aim component is not active aiming");
        Check(AaObservationPolicy.AimingInProgress(true,-1)==false,"Expired timer is not active aiming");
        Check(AaObservationPolicy.AimingInProgress(true,.5f)==true,"Positive timer reports aiming");
        Check(AaObservationPolicy.AimingInProgress(false,.5f)==false,"Absent component cannot report active aiming");
        foreach(float special in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
            Check(AaObservationPolicy.AimingInProgress(true,special)==null,"Non-finite timer is unknown, not a valid aiming duration");
        Check(AaObservationPolicy.AimingInProgress(true,null)==null,"Missing timer is unknown");
        bool strictRejected=false;try{JsonSerializer.Serialize(new{score=float.PositiveInfinity});}catch(ArgumentException){strictRejected=true;}
        Check(strictRejected,"Fixture reproduces lat.3 serializer failure");
        var specialPayload=new{score=float.PositiveInfinity,nested=new{negative=double.NegativeInfinity,timer=(float?)float.NaN},
            values=new[]{1f,float.NaN,float.PositiveInfinity},normal=12.5};
        using(var parsed=JsonDocument.Parse(AaLogJson.Serialize(specialPayload)))
        {
            var x=parsed.RootElement;
            Check(x.GetProperty("score").GetString()=="Infinity","Infinity is preserved as a valid JSON string");
            Check(x.GetProperty("nested").GetProperty("negative").GetString()=="-Infinity","Nested negative infinity preserved");
            Check(x.GetProperty("nested").GetProperty("timer").GetString()=="NaN","Nullable NaN preserved");
            Check(x.GetProperty("values")[1].GetString()=="NaN","Array NaN preserved");
            Check(x.GetProperty("values")[0].GetSingle()==1,"Ordinary array values remain numeric");
            Check(x.GetProperty("normal").GetDouble()==12.5,"Ordinary numeric values unchanged");
        }
        using(var parsed=JsonDocument.Parse(AaLogJson.Serialize(new{nextRecord=42})))
            Check(parsed.RootElement.GetProperty("nextRecord").GetInt32()==42,"Following record remains writable after non-finite data");
        Check(AaObservationPolicy.AngleError(179,-179)==2,"Yaw wrap-around takes the short path");
        Check(AaObservationPolicy.AngleError(-179,179)==2,"Yaw wrap reverse");
        Check(AaObservationPolicy.AngleError(360,0)==0,"Full turn matches zero");
        Check(AaObservationPolicy.AngleError(float.NaN,0)==null,"Invalid yaw remains unknown");
        string temp=Path.Combine(Path.GetTempPath(),"fa-test-bundle-"+Guid.NewGuid());
        try
        {
            Directory.CreateDirectory(Path.Combine(temp,"UserData/FreedomArrow/diagnostics"));
            Directory.CreateDirectory(Path.Combine(temp,"UserData/FAConquestPrototype"));
            Directory.CreateDirectory(Path.Combine(temp,"MelonLoader"));
            DateTime start=DateTime.UtcNow;
            string[] included={"UserData/FreedomArrow/diagnostics/aa-targeting-current.jsonl","UserData/FreedomArrow/diagnostics/runtime-current.jsonl",
                "UserData/FAConquestPrototype/shots-run1.jsonl","UserData/FAConquestPrototype/shots-run2.jsonl","UserData/FAConquestPrototype/events-current.jsonl","MelonLoader/Latest.log"};
            foreach(string f in included)File.WriteAllText(Path.Combine(temp,f),"{\"test\":true}\n");
            string old=Path.Combine(temp,"UserData/FAConquestPrototype/shots-old.jsonl");File.WriteAllText(old,"old");File.SetLastWriteTimeUtc(old,start.AddHours(-1));
            File.WriteAllText(Path.Combine(temp,"private.txt"),"must not collect");
            string archive=TestLogBundle.Create(temp,start,"test/../7");
            Check(Path.GetDirectoryName(archive)==Path.Combine(temp,"UserData/FreedomArrow/diagnostics"),"Bundle path remains in diagnostics");
            using var zip=System.IO.Compression.ZipFile.OpenRead(archive);
            foreach(string f in included)Check(zip.GetEntry(f)!=null,"All current-session runs retained: "+f);
            Check(zip.GetEntry("private.txt")==null&&zip.GetEntry("UserData/FAConquestPrototype/shots-old.jsonl")==null,"Unrelated and old files excluded");
            Check(zip.Entries.Count==included.Length+1,"Only scoped logs and inventory included");
            using var inventory=new StreamReader(zip.GetEntry("bundle.json")!.Open());
            using var parsedInventory=JsonDocument.Parse(inventory.ReadToEnd());
            Check(parsedInventory.RootElement.GetProperty("copied").GetArrayLength()==included.Length,"Inventory records copied logs");
        }
        finally{if(Directory.Exists(temp))Directory.Delete(temp,true);}
        using var fs=File.OpenRead(args[0]);using var pe=new PEReader(fs);var md=pe.GetMetadataReader();
        var codes=typeof(OpCodes).GetFields(BindingFlags.Public|BindingFlags.Static).Where(f=>f.FieldType==typeof(OpCode))
            .Select(f=>(OpCode)f.GetValue(null)!).ToDictionary(o=>unchecked((ushort)o.Value));
        string Owner(EntityHandle h)
        {
            if(h.Kind==HandleKind.TypeReference){var t=md.GetTypeReference((TypeReferenceHandle)h);return md.GetString(t.Namespace)+"."+md.GetString(t.Name);}
            if(h.Kind==HandleKind.TypeDefinition)return md.GetString(md.GetTypeDefinition((TypeDefinitionHandle)h).Name);
            return h.Kind.ToString();
        }
        string Method(EntityHandle h)
        {
            if(h.Kind==HandleKind.MethodSpecification)return Method(md.GetMethodSpecification((MethodSpecificationHandle)h).Method);
            if(h.Kind==HandleKind.MemberReference){var m=md.GetMemberReference((MemberReferenceHandle)h);return Owner(m.Parent)+"."+md.GetString(m.Name);}
            if(h.Kind==HandleKind.MethodDefinition){var m=md.GetMethodDefinition((MethodDefinitionHandle)h);return Owner(m.GetDeclaringType())+"."+md.GetString(m.Name);}
            return h.Kind.ToString();
        }
        bool Observer(TypeDefinitionHandle h)
        {
            var t=md.GetTypeDefinition(h);return md.GetString(t.Name)=="GroundAaLog"||(!t.GetDeclaringType().IsNil&&Observer(t.GetDeclaringType()));
        }
        var calls=new List<string>();var fired=new List<string>();int methods=0;
        foreach(var th in md.TypeDefinitions.Where(Observer))foreach(var mh in md.GetTypeDefinition(th).GetMethods())
        {
            var m=md.GetMethodDefinition(mh);if(m.RelativeVirtualAddress==0)continue;methods++;
            var il=pe.GetMethodBody(m.RelativeVirtualAddress).GetILBytes()!;int i=0;
            while(i<il.Length)
            {
                ushort key=il[i++];if(key==0xfe)key=(ushort)(0xfe00|il[i++]);var op=codes[key];int n;
                if(op.OperandType==OperandType.InlineSwitch){n=4+4*BitConverter.ToInt32(il,i);}
                else n=op.OperandType switch{OperandType.InlineNone=>0,OperandType.ShortInlineBrTarget or OperandType.ShortInlineI or OperandType.ShortInlineVar=>1,OperandType.InlineVar=>2,OperandType.InlineI8 or OperandType.InlineR=>8,_=>4};
                if(op.OperandType==OperandType.InlineMethod)
                {
                    string name=Method(MetadataTokens.EntityHandle(BitConverter.ToInt32(il,i)));calls.Add(name);
                    if(md.GetString(m.Name)=="Fired")fired.Add(name);
                }
                i+=n;
            }
        }
        Check(methods>10,"Compiled observer and nested code inspected");
        foreach(var banned in new[]{"Harmony","TargetSearchHelper","OverkillScoringSystem","BattleSystemHelpers","WriteField","GenerateRandom","NextFloat","SetWeaponState","SetAmmoState"})
            Check(!calls.Any(x=>x.Contains(banned)),"Observer must not invoke/patch combat logic: "+banned);
        Check(fired.Count>0,"Compiled existing shot callback inspected");
        foreach(var banned in new[]{"NativeEcs","Entity.","UnityEngine","Snapshot","World","UnitComponent","WeaponComponent"})
            Check(!fired.Any(x=>x.Contains(banned)),"Callback must enqueue only, without ECS/Unity reads: "+banned);
        Console.WriteLine($"PASS: {checks} passive-observer policy and compiled-IL boundary checks; {methods} methods inspected. Native ECS invocation/performance untested.");
    }
}
