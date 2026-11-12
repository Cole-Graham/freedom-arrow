namespace FreedomArrow;

// UI-only alpha preparation. Source PNGs and portrait textures are unchanged.
static class CutoutMask
{
    public static byte[] Clean(byte[] alpha,int width,int height)
    {
        if(width<=0||height<=0||alpha.Length!=checked(width*height))throw new ArgumentException("cutout dimensions");
        // All nine sources carry their unwanted edge debris/haze in low-opacity alpha.
        // Preserve every solid pixel, including disconnected equipment and canopy frames.
        var result=new byte[alpha.Length];
        for(int i=0;i<result.Length;i++)if(alpha[i]>=192)result[i]=255;
        return result;
    }
}
