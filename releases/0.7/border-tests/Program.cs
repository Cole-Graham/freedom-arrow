using FreedomArrow;
int passed=0;
void Clip(float ax,float ay,float bx,float by,bool expected,params float[] endpoints)
{
    bool got=BorderGeometry.Clip(ref ax,ref ay,ref bx,ref by,100,80);
    if(got!=expected)throw new Exception($"Visibility {passed}: {got} != {expected}");
    if(got&&endpoints.Length>0)
    {
        float[] actual={ax,ay,bx,by};
        for(int i=0;i<4;i++)if(Math.Abs(actual[i]-endpoints[i])>.002)throw new Exception($"Endpoint {passed}/{i}: {actual[i]} != {endpoints[i]}");
    }
    passed++;
}
Clip(10,20,90,70,true,10,20,90,70);
Clip(-20,40,120,40,true,0,40,100,40);
Clip(120,40,-20,40,true,100,40,0,40);
Clip(50,-100,50,100,true,50,0,50,80);
Clip(-10,-10,100,100,true,0,0,80,80);
Clip(-10,90,110,-30,true,0,80,80,0);
Clip(-10,0,-10,80,false);
Clip(0,90,100,90,false);
Clip(0,0,0,80,true,0,0,0,80);
Clip(100,80,100,80,true,100,80,100,80);
Clip(-100,-100,-10,-10,false);
Clip(float.NaN,0,100,80,false);
Clip(0,0,float.PositiveInfinity,80,false);
Clip(-1e20f,40,1e20f,40,true,0,40,0,40); // Precision loss stays bounded; never send huge coordinates to GUI.
Console.WriteLine($"PASS {passed} border clipping cases. No native render claim.");
