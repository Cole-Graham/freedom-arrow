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
        foreach(int t in new[]{128,256,512,1024})Check(AaCooldownPolicy.ProjectileType(t),"Native projectile category "+t);
        foreach(int t in new[]{0,1,2,4,8,16,32,384})Check(!AaCooldownPolicy.ProjectileType(t),"Ordinary/composite target excluded "+t);
        foreach(int t in new[]{2,4,32})
        {
            Check(AaCooldownPolicy.Defender(t,false,true),"Interception guns qualify on land/ships "+t);
            Check(AaCooldownPolicy.Defender(t,true,false),"Existing AA still qualifies "+t);
            Check(!AaCooldownPolicy.Defender(t,false,false),"Non-AA weapon excluded "+t);
        }
        Check(!AaCooldownPolicy.Defender(8,true,true)&&!AaCooldownPolicy.Defender(16,true,true),"Helicopter/aircraft guidance unchanged");
        var late=new[]{new AaCooldownPolicy.Contributor(1,4,true,false)};
        bool Release(AaCooldownPolicy.Contributor[] cs,bool native=true,bool ground=true,bool blocked=false,double age=.01,int incoming=0,ulong caller=2,float deadline=2)
            =>AaCooldownPolicy.Release(native,ground,blocked,age,incoming,caller,deadline,cs);
        Check(Release(late),"A clearly late future reservation is released");
        Check(!Release(late,native:false),"Never turn native false into true");
        Check(!Release(late,ground:false),"Non-ground-AA caller unchanged");
        Check(!Release(late,blocked:true),"Explicit blocked-shooter inclusion respected");
        Check(!Release(late,age:.076),"Stale snapshot retains native decision");
        Check(!Release(late,age:-1),"Invalid clock retains native decision");
        Check(!Release(late,incoming:1),"Airborne incoming interceptor preserved");
        Check(!Release(late,incoming:-1),"Unknown incoming protection preserved");
        Check(!Release(Array.Empty<AaCooldownPolicy.Contributor>()),"Empty list cannot vacuously release");
        Check(!Release(late,caller:1),"Excluding the only contributor cannot release");
        Check(!Release(new[]{new AaCooldownPolicy.Contributor(1,4,false,false)}),"Unknown readiness retains native");
        Check(!Release(new[]{new AaCooldownPolicy.Contributor(1,4,true,true)}),"Already launched contribution preserved");
        Check(!Release(new[]{new AaCooldownPolicy.Contributor(2,4,true,true)}),"Excluded launcher's airborne contribution preserved");
        Check(!Release(late.Append(new AaCooldownPolicy.Contributor(3,.3f,true,false)).ToArray()),"Mixed timely/late reservations retain native");
        Check(Release(late.Append(new AaCooldownPolicy.Contributor(2,0,true,false)).ToArray()),"Caller's own future shot excluded while others clearly late");
        Check(!AaCooldownPolicy.ClearlyLate(3.1f,2),"Boundary tolerance does not aggressively exclude");
        Check(AaCooldownPolicy.Remaining(2,4,3)==4,"Overlapping timers use max, not sum");
        Check(AaCooldownPolicy.Remaining(-2,0,-1)==0,"Expired timers clamp to zero");
        foreach(float f in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(!AaCooldownPolicy.ClearlyLate(f,2),"Nonfinite readiness falls back");
            Check(!AaCooldownPolicy.ClearlyLate(4,f),"Nonfinite deadline falls back");
            Check(float.IsNaN(AaCooldownPolicy.Remaining(f,0,0)),"Nonfinite timer is unknown");
        }
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
        var calls=new List<string>();var fired=new List<string>();var callback=new List<string>();var controller=new List<string>();int methods=0,callbackMethods=0,patches=0;
        foreach(var th in md.TypeDefinitions.Where(h=>Observer(h)||md.GetString(md.GetTypeDefinition(h).Name)=="AaCooldown"))foreach(var mh in md.GetTypeDefinition(th).GetMethods())
        {
            bool obs=Observer(th);var m=md.GetMethodDefinition(mh);if(m.RelativeVirtualAddress==0)continue;if(obs)methods++;
            bool cb=!obs&&md.GetString(m.Name) is "After" or "Key";if(cb)callbackMethods++;
            var il=pe.GetMethodBody(m.RelativeVirtualAddress).GetILBytes()!;int i=0;
            while(i<il.Length)
            {
                ushort key=il[i++];if(key==0xfe)key=(ushort)(0xfe00|il[i++]);var op=codes[key];int n;
                if(op.OperandType==OperandType.InlineSwitch){n=4+4*BitConverter.ToInt32(il,i);}
                else n=op.OperandType switch{OperandType.InlineNone=>0,OperandType.ShortInlineBrTarget or OperandType.ShortInlineI or OperandType.ShortInlineVar=>1,OperandType.InlineVar=>2,OperandType.InlineI8 or OperandType.InlineR=>8,_=>4};
                if(op.OperandType==OperandType.InlineMethod)
                {
                    string name=Method(MetadataTokens.EntityHandle(BitConverter.ToInt32(il,i)));
                    if(obs){calls.Add(name);if(md.GetString(m.Name)=="Fired")fired.Add(name);}
                    else {controller.Add(name);if(cb)callback.Add(name);if(name.EndsWith("Harmony.Patch"))patches++;}
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
        Check(callbackMethods==2&&callback.Count>0,"Actual compiled cooldown callback and key helper inspected");
        foreach(var banned in new[]{"NativeEcs","UnityEngine","BattleSystemHelpers","TargetSearchHelper","DiagnosticLog","File.","StreamWriter","Reflection","Entity.get_","Entity.Has"})
            Check(!callback.Any(x=>x.Contains(banned)),"Cooldown callback cannot read native state or do IO: "+banned);
        foreach(var banned in new[]{"WriteField","SetWeaponState","SetAmmoState","TargetSearchHelper","GenerateRandom"})
            Check(!controller.Any(x=>x.Contains(banned)),"Cooldown controller cannot mutate combat/search state: "+banned);
        Check(patches==1,"Exactly one cooldown behavior hook; no diagnostic hook group");
        Console.WriteLine($"PASS: {checks} passive-observer policy and compiled-IL boundary checks; {methods} methods inspected. Native ECS invocation/performance untested.");
    }
}
