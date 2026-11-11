using System.Numerics;
using System.Text.Json.Nodes;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using FreedomArrow;
using P=FreedomArrow.CramPredictionPolicy;

int checks=0;
void Check(bool ok,string name){checks++;if(!ok)throw new Exception(name);}
P.Solution Solve(Vector3 aim,float speed,float gravity=0)
{
    float h=MathF.Sqrt(aim.X*aim.X+aim.Z*aim.Z),tan,time;Vector3 fire;
    if(gravity==0){time=aim.Length()/speed;fire=Vector3.Normalize(aim);tan=aim.Y/h;}
    else
    {
        float v2=speed*speed,disc=v2*v2-gravity*(gravity*h*h+2*aim.Y*v2);
        if(disc<0)return new(aim,default,0,0,false);
        // Double precision here avoids cancellation in the independent oracle.
        tan=(float)(((double)v2-Math.Sqrt(disc))/(gravity*h));
        float cos=1/MathF.Sqrt(1+tan*tan);
        fire=new Vector3(aim.X/h*cos,tan*cos,aim.Z/h*cos);time=h/(speed*cos);
    }
    return new(aim,fire,time,tan,true);
}
float LinearIntercept(Vector3 r,Vector3 v,float speed)
{
    double a=v.LengthSquared()-speed*speed,b=2*Vector3.Dot(r,v),c=r.LengthSquared();
    double disc=b*b-4*a*c;var roots=new[]{(-b+Math.Sqrt(disc))/(2*a),(-b-Math.Sqrt(disc))/(2*a)};
    return (float)roots.Where(t=>t>0).Min();
}
Check(P.Scope(345,262,256,200),"C-RAM SEAD scope");
Check(Unsafe.SizeOf<CramBallisticValue>()==44&&!RuntimeHelpers.IsReferenceOrContainsReferences<CramBallisticValue>(),"Wire value is reference-free and 44 bytes");
foreach(var (field,offset) in new[]{("VectorToTarget",0),("InitialProjectileSpeed",12),("FireVector",16),
    ("FireAngleTan",28),("TimeToImpact",32),("GravityMultiplyer",36),("CanShoot",40),("Initialized",41),("Padding",42)})
    Check((int)Marshal.OffsetOf<CramBallisticValue>(field)==offset,"Wire offset: "+field);
unsafe
{
    byte* buffer=stackalloc byte[64];new Span<byte>(buffer,64).Fill(0xA5);
    var value=new CramBallisticValue{VectorToTarget=new(1,2,3),InitialProjectileSpeed=1610,
        FireVector=Vector3.UnitZ,TimeToImpact=.5f,GravityMultiplyer=1,CanShoot=1,Initialized=1,Padding=0xABCD};
    Unsafe.WriteUnaligned(buffer,value);
    Check(*(float*)(buffer+12)==1610&&buffer[40]==1&&buffer[41]==1,"Native byte/float fields match wire format");
    // A pointer-based native helper may update these known fields without any
    // dependency on a generated managed struct/class or bool marshaling.
    *(float*)(buffer+32)=.25f;buffer[40]=0;
    var read=Unsafe.ReadUnaligned<CramBallisticValue>(buffer);
    Check(read.TimeToImpact==.25f&&read.CanShoot==0&&read.Initialized==1&&read.Padding==0xABCD,"Native field updates preserve adjacent flags/padding");
    Check(new ReadOnlySpan<byte>(buffer+44,20).ToArray().All(b=>b==0xA5),"44-byte write preserves 48/64-byte trailing padding");
}
foreach(var s in new[]{(261,262,256,200),(345,62,256,200),(345,262,16,200),(345,262,256,1)})
    Check(!P.Scope(s.Item1,s.Item2,s.Item3,s.Item4),"Unrelated weapon/ammo/type/seeker excluded");
var history=new CramMotionHistory();
Check(!history.Observe(1,new(0,-50,-700),out _,out _),"First sample falls back");
for(int i=0;i<30;i++)Check(!history.Observe(1,new(0,-50,-700),out _,out _),"Duplicate frame does not invent history");
Check(history.Observe(1.15f,new(0,-80,-700),out var acceleration,out var interval),"Fresh history available");
Check(Math.Abs(acceleration.Y+200)<.01&&Math.Abs(interval-.15)<.001,"Acceleration from previous velocity");
Check(!history.Observe(.5f,Vector3.Zero,out _,out _),"Time reset clears history");
Check(!history.Observe(2,Vector3.Zero,out _,out _),"Long gap clears history");
var other=new CramMotionHistory();Check(!other.Observe(2,Vector3.One,out _,out _),"Independent target history");
var native=Solve(new(0,400,700),1610);
Check(!P.TryCorrect(native,Vector3.Zero,Vector3.Zero,a=>Solve(a,1610),out _,out var why)&&why=="steady_velocity","Steady motion retains native");
Check(!P.TryCorrect(native,new(float.NaN,0,0),Vector3.One,a=>Solve(a,1610),out _,out _),"Non-finite motion rejected");
Check(!P.TryCorrect(native,Vector3.Zero,Vector3.One,_=>throw new Exception(),out _,out why)&&why=="solver_exception","Solver exception retains native");
Check(!P.TryCorrect(native,Vector3.Zero,Vector3.One,_=>new(default,default,0,0,false),out _,out _),"Unreachable solve rejected");
Check(!P.TryCorrect(native with{Time=1},Vector3.Zero,Vector3.One,a=>Solve(a,1610),out _,out _),"Long horizon retains native");

// Independent target-motion/flight oracle, including projectile gravity. Verify
// that a corrected direction and its time reach the same accelerating target.
foreach(float gravity in new[]{0f,9.81f})
foreach(var velocity in new[]{new Vector3(100,-100,-650),new Vector3(-80,-80,-500)})
{
    var position=new Vector3(120,400,1000);var accel=new Vector3(0,-160,20);float speed=1610;
    float t=LinearIntercept(position,velocity,speed);P.Solution start=default;
    for(int i=0;i<20;i++){start=Solve(position+velocity*t,speed,gravity);t=start.Time;}
    Check(P.TryCorrect(start,velocity,accel,a=>Solve(a,speed,gravity),out var result,out why),"Moving/diving target converges: "+why);
    var target=position+velocity*result.Solution.Time+.5f*accel*result.Solution.Time*result.Solution.Time;
    var projectile=result.Solution.Fire*speed*result.Solution.Time-new Vector3(0,.5f*gravity*result.Solution.Time*result.Solution.Time,0);
    Check(Vector3.Distance(projectile,target)<.5f,"Coherent direction and time reach accelerating target");
    Check(result.Offset.Length()<=P.MaxCorrection+.001&&result.Offset.Length()<=start.Aim.Length()*P.MaxFraction+.001,"Final correction stays bounded");
    Check(result.Iterations<=P.MaxIterations&&result.Iterations>0,"Iteration bound");
}
Check(P.TryCorrect(native,Vector3.Zero,new(0,-100000,0),a=>Solve(a,1610),out var capped,out _)
    ?capped.Limited&&capped.Offset.Length()<=P.MaxCorrection+.001:true,"Extreme acceleration is capped or rejected");

// Replay the supplied lat.9 positions with the actual bounded/re-solved policy.
// This is a fixed-TOI data study, not a simulated collision or hit-rate test.
if(args.Length>0)
{
    var rows=JsonNode.Parse(File.ReadAllText(args[0]))!.AsArray();var before=new List<float>();var after=new List<float>();int rejected=0,better=0;
    Vector3 V(JsonNode n)=>new(n[0]!.GetValue<float>(),n[1]!.GetValue<float>(),n[2]!.GetValue<float>());
    foreach(var q in rows.Where(q=>q!["kind"]!.GetValue<string>()=="shot_callback_deferred"&&q["margin"]!.GetValue<bool>()))
    {
        var n=Solve(V(q!["aim"]!),1610) with{Time=q["toi"]!.GetValue<float>()};
        // Native-time scoring is deliberately separate from the coherent solver
        // tests above: reuse each logged future point only as a rough replay.
        if(!P.TryCorrect(n,V(q["velocity"]!),V(q["acceleration"]!),a=>Solve(a,1610),out var r,out _)){rejected++;continue;}
        float old=q["error_norm"]!.GetValue<float>();
        var future=V(q["future_interpolated_position"]!)+V(q["velocity"]!)*(r.Solution.Time-n.Time);
        float error=Vector3.Distance(V(q["shooter"]!)+r.Solution.Aim,future);
        before.Add(old);after.Add(error);if(error<old)better++;
        Check(r.Offset.Length()<=60.001f,"Replay bounded");
    }
    Check(before.Count>20,"Replay covers recorded firing-adjacent samples");
    float Median(List<float> xs){xs.Sort();return xs[xs.Count/2];}
    Console.WriteLine($"Exploratory replay: {before.Count} accepted, {rejected} native fallback, {better} lower approximate error; medians {Median(before):F3} -> {Median(after):F3}. Not a hit rate or held-out test.");
}
if(args.Length>1)
{
    using var fs=File.OpenRead(args[1]);using var pe=new PEReader(fs);var md=pe.GetMetadataReader();
    var type=md.TypeDefinitions.Select(md.GetTypeDefinition).Single(t=>md.GetString(t.Name)=="CramPrediction");
    var nested=md.GetTypeDefinition(type.GetNestedTypes().Single(h=>md.GetString(md.GetTypeDefinition(h).Name)=="LeadNative"));
    var invoke=md.GetMethodDefinition(nested.GetMethods().Single(h=>md.GetString(md.GetMethodDefinition(h).Name)=="Invoke"));
    // Raw signature: void plus four pointer arguments and the approximation int;
    // no reference/non-blittable IL2CPP structs cross the unmanaged callback ABI.
    var sig=md.GetBlobReader(invoke.Signature);sig.ReadSignatureHeader();Check(sig.ReadCompressedInteger()==5,"Five native callback arguments");
    Check(sig.ReadSignatureTypeCode()==SignatureTypeCode.Void,"Native callback returns void");
    foreach(var expected in new[]{SignatureTypeCode.IntPtr,SignatureTypeCode.IntPtr,SignatureTypeCode.IntPtr,SignatureTypeCode.Int32,SignatureTypeCode.IntPtr})
        Check(sig.ReadSignatureTypeCode()==expected,"Pointer-only callback ABI");
    var angle=md.GetTypeDefinition(type.GetNestedTypes().Single(h=>md.GetString(md.GetTypeDefinition(h).Name)=="AngleNative"));
    var ai=md.GetMethodDefinition(angle.GetMethods().Single(h=>md.GetString(md.GetMethodDefinition(h).Name)=="Invoke"));
    var aSig=md.GetBlobReader(ai.Signature);aSig.ReadSignatureHeader();Check(aSig.ReadCompressedInteger()==2,"Two native angle arguments");
    Check(aSig.ReadSignatureTypeCode()==SignatureTypeCode.Void&&aSig.ReadSignatureTypeCode()==SignatureTypeCode.IntPtr&&aSig.ReadSignatureTypeCode()==SignatureTypeCode.IntPtr,"Angle solver has pointer-only ABI");
}
Console.WriteLine($"PASS: {checks} prediction scope/history/bounds/coherent-flight/replay/ABI checks. Native hook invocation remains untested.");
