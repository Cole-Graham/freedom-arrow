using UnityEngine;

namespace FAModels;
public partial class Mod
{
    // Opt-in only: retain source alpha/images, but shade the selected canopy as smooth dielectric glass.
    // Preserve specular keeps Fresnel reflections visible even where the source alpha is low.
    static void ApplyCanopyFinish(Material material, bool sourceCanopy)
    {
        if (!sourceCanopy) return;
        material.SetFloat("_EnableBlendModePreserveSpecularLighting", 1f);
        material.EnableKeyword("_BLENDMODE_PRESERVE_SPECULAR_LIGHTING");
        material.SetFloat("_Metallic", 0f);
        material.SetFloat("_Smoothness", 0.95f);
        // The hull's packed map shares this glass atlas. Restrict its remaps to glass rather than metal/rough paint.
        material.SetFloat("_MetallicRemapMin", 0f);
        material.SetFloat("_MetallicRemapMax", 0f);
        material.SetFloat("_SmoothnessRemapMin", 0.90f);
        material.SetFloat("_SmoothnessRemapMax", 0.98f);
        material.SetFloat("_EnableFogOnTransparent", 0f);
        material.DisableKeyword("_ENABLE_FOG_ON_TRANSPARENT");
    }
}
