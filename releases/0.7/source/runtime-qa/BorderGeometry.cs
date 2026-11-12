namespace FreedomArrow;

// Screen clipping stays independent of Unity. Keep all drawing inside the game viewport,
// including when the camera crosses an edge or projects very distant endpoints.
internal static class BorderGeometry
{
    public static bool Clip(ref float ax,ref float ay,ref float bx,ref float by,float width,float height)
    {
        if(!float.IsFinite(ax)||!float.IsFinite(ay)||!float.IsFinite(bx)||!float.IsFinite(by)||width<=0||height<=0)return false;
        double x=ax,y=ay,dx=(double)bx-ax,dy=(double)by-ay,t0=0,t1=1;
        bool Edge(double p,double q)
        {
            if(p==0)return q>=0;
            double r=q/p;
            if(p<0){if(r>t1)return false;t0=Math.Max(t0,r);}
            else {if(r<t0)return false;t1=Math.Min(t1,r);}
            return true;
        }
        if(!Edge(-dx,x)||!Edge(dx,width-x)||!Edge(-dy,y)||!Edge(dy,height-y))return false;
        ax=(float)(x+t0*dx);ay=(float)(y+t0*dy);bx=(float)(x+t1*dx);by=(float)(y+t1*dy);
        return true;
    }
}
