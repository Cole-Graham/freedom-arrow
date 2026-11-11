using System.Numerics;

namespace FreedomArrow;

// Pure math shared with the offline tests. The caller supplies the native
// fixed-point ballistic solver; this class never reads or changes game state.
internal static class CramPredictionPolicy
{
    public const float MinHistory=.075f,MaxHistory=.25f,MaxHorizon=.75f;
    public const float MaxAcceleration=1500,MaxCorrection=60,MaxFraction=.1f;
    public const int MaxIterations=8;
    public readonly record struct Solution(Vector3 Aim,Vector3 Fire,float Time,float Tan,bool CanShoot);
    public readonly record struct Result(Solution Solution,Vector3 Acceleration,Vector3 Offset,int Iterations,bool Limited);
    public static bool Finite(Vector3 v)=>float.IsFinite(v.X)&&float.IsFinite(v.Y)&&float.IsFinite(v.Z);
    // Native target masks remain authoritative: no new targeting capability.
    // AntiAirGun includes radar-assisted guns whose IsRadarDependent flag is
    // false (including C-RAM). Also allow a radar-dependent autocannon.
    public static bool Gun(int weaponType,bool radarDependent,int trajectory,int seeker,long targetMask)
        =>(weaponType==115||(weaponType==114&&radarDependent))&&trajectory==10&&seeker==0
            &&(targetMask&(128|256|512|1024))!=0;
    public static bool Scope(int weaponType,bool radarDependent,int trajectory,int seeker,long targetMask,int targetType)
        =>Gun(weaponType,radarDependent,trajectory,seeker,targetMask)
            &&targetType is 128 or 256 or 512 or 1024&&(targetMask&targetType)!=0;
    // Scope validation must include long ship hulls. The full hull diagonal
    // plus 15 units is conservative and capped at 512. Invalid dimensions
    // retain 15 units. This does not change firing range.
    public static float OriginRadius(float length,float width,float height)
    {
        var size=new Vector3(length,width,height);
        if(!Finite(size)||length<0||width<0||height<0)return 15;
        return Math.Clamp(size.Length()+15,15,512);
    }
    public static Vector3 Limit(Vector3 value,float maximum,out bool limited)
    {
        float length=value.Length();limited=length>maximum;
        return limited?value*(maximum/length):value;
    }
    static bool Valid(Solution s)=>s.CanShoot&&Finite(s.Aim)&&Finite(s.Fire)&&float.IsFinite(s.Tan)
        &&float.IsFinite(s.Time)&&s.Time>=.005f&&s.Time<=MaxHorizon&&Math.Abs(s.Fire.LengthSquared()-1)<.01f;
    public static bool TryCorrect(Solution native,Vector3 velocity,Vector3 acceleration,
        Func<Vector3,Solution> solve,out Result result,out string reason)
    {
        result=default;reason="invalid_input";
        if(!Valid(native)||!Finite(velocity)||!Finite(acceleration)||velocity.LengthSquared()>10000f*10000)return false;
        if(acceleration.LengthSquared()<.01f){reason="steady_velocity";return false;}
        acceleration=Limit(acceleration,MaxAcceleration,out bool limited);
        float maximum=Math.Min(MaxCorrection,native.Aim.Length()*MaxFraction),time=native.Time;
        if(maximum<=0)return false;
        for(int i=0;i<MaxIterations;i++)
        {
            var turn=Limit(.5f*acceleration*time*time,maximum,out bool clipped);limited|=clipped;
            var aim=native.Aim+velocity*(time-native.Time)+turn;
            if(!Finite(aim)||(aim-native.Aim).Length()>maximum){reason="correction_bounds";return false;}
            Solution next;
            try{next=solve(aim);}catch{reason="solver_exception";return false;}
            if(!Valid(next)){reason="invalid_solution";return false;}
            if(Math.Abs(next.Time-time)<.0001f)
            {
                result=new(next,acceleration,aim-native.Aim,i+1,limited);reason="applied";return true;
            }
            time=next.Time;
        }
        reason="no_convergence";return false;
    }
}

// At most 32 samples per target; equal-time callbacks cannot create a zero-dt
// acceleration. World/scene changes are handled by the native bridge.
internal sealed class CramMotionHistory
{
    readonly List<(float Time,Vector3 Velocity)> samples=new(32);
    public float LastTime=>samples.Count==0?float.NegativeInfinity:samples[^1].Time;
    public bool Observe(float now,Vector3 velocity,out Vector3 acceleration,out float interval)
    {
        acceleration=default;interval=0;
        if(!float.IsFinite(now)||!CramPredictionPolicy.Finite(velocity))return false;
        if(now<LastTime||now-LastTime>.5f)samples.Clear();
        if(now>LastTime)
        {
            if(samples.Count==32)samples.RemoveAt(0);
            samples.Add((now,velocity));
        }
        int best=-1;float distance=float.MaxValue;
        for(int i=0;i<samples.Count;i++)
        {
            float dt=now-samples[i].Time;
            if(dt<CramPredictionPolicy.MinHistory||dt>CramPredictionPolicy.MaxHistory)continue;
            float score=Math.Abs(dt-.15f);
            if(score<distance){best=i;distance=score;}
        }
        if(best<0)return false;
        interval=now-samples[best].Time;acceleration=(velocity-samples[best].Velocity)/interval;
        return CramPredictionPolicy.Finite(acceleration);
    }
}
