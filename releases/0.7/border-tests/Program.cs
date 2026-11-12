using System.Numerics;
using FreedomArrow;
int passed=0;
void Check(bool ok,string what){if(!ok)throw new Exception($"Case {passed}: {what}");passed++;}
const float Pixel=.001f;
var line=new[]{new Vector3(0,0,0),new Vector3(100,0,0),new Vector3(200,0,0)};
var v=new Vector3[6];
// Seen from above at 1000 units: 4 pixels = 4 units across, perpendicular to the border, lifted by half width.
BorderGeometry.Ribbon(line,new Vector3(100,1000,0),Pixel,4,v);
float w=Vector3.Distance(v[2],v[3]);
Check(Math.Abs(w-4)<.01f,$"width {w}");
Check(Math.Abs(Vector3.Dot(Vector3.Normalize(v[3]-v[2]),Vector3.UnitX))<1e-4f,"perpendicular");
Check(Math.Abs((v[2].Y+v[3].Y)/2-(BorderGeometry.Lift+2))<.01f,"lift");
// Twice as far: twice as wide in world units, the same on screen.
BorderGeometry.Ribbon(line,new Vector3(100,2000,0),Pixel,4,v);
Check(Math.Abs(Vector3.Distance(v[2],v[3])-8)<.02f,"distance scaling");
// Seen from the side at ground level: the strip stands up toward the camera, so it does not collapse to zero height.
BorderGeometry.Ribbon(line,new Vector3(100,0,-1000),Pixel,4,v);
Check(Math.Abs(v[3].Y-v[2].Y)>3.9f,"side view");
// Looking straight along the border: fallback direction, finite vertices.
BorderGeometry.Ribbon(line,new Vector3(-1000,0,0),Pixel,4,v);
Check(v.All(p=>float.IsFinite(p.X)&&float.IsFinite(p.Y)&&float.IsFinite(p.Z)),"degenerate view");
// Endpoints use one-sided tangents.
BorderGeometry.Ribbon(line,new Vector3(0,1000,0),Pixel,4,v);
Check(Math.Abs(Vector3.Distance(v[0],v[1])-4)<.01f,"endpoint");
Console.WriteLine($"PASS {passed} border strip cases. No native render claim.");
