using System.Numerics;
namespace FreedomArrow;

// Camera-facing strip of constant screen width along the border, independent of Unity so the host tests can check it.
// pixelAngle = 2 * tan(vertical FOV / 2) / screen height: the world size of one pixel at distance 1.
// Each point gets two vertices; the strip is lifted by its own half width so terrain between samples does not cut it.
internal static class BorderGeometry
{
    public const float Lift=1.5f;
    public static void Ribbon(ReadOnlySpan<Vector3> points,Vector3 eye,float pixelAngle,float pixels,Span<Vector3> vertices)
    {
        int n=points.Length;
        if(vertices.Length<2*n)throw new ArgumentException("vertices");
        for(int i=0;i<n;i++)
        {
            var p=points[i];
            var along=points[Math.Min(i+1,n-1)]-points[Math.Max(i-1,0)];
            var half=.5f*pixels*pixelAngle*Vector3.Distance(p,eye);
            p.Y+=Lift+half;
            var side=Vector3.Cross(along,p-eye);
            float length=side.Length();
            // Looking straight along the border: any side direction is equally valid.
            side=length>1e-6f&&float.IsFinite(length)?side/length:Vector3.UnitY;
            vertices[2*i]=p-side*half;vertices[2*i+1]=p+side*half;
        }
    }
}
