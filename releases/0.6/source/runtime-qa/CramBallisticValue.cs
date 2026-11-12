using System.Numerics;
using System.Runtime.InteropServices;

namespace FreedomArrow;

// Private blittable wire value. Generated IL2CPP proxy representations can vary
// between installations; no generated BallisticDataStruct crosses this boundary.
// Flags are explicit bytes, not automatically marshaled managed bool fields.
[StructLayout(LayoutKind.Sequential,Pack=4)]
internal struct CramBallisticValue
{
    public Vector3 VectorToTarget;
    public float InitialProjectileSpeed;
    public Vector3 FireVector;
    public float FireAngleTan,TimeToImpact,GravityMultiplyer;
    public byte CanShoot,Initialized;
    public ushort Padding;
}
