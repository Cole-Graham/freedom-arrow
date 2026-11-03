using MelonLoader;
using MelonLoader.Utils;

namespace FreedomArrow;

public class FreedomArrowMod : MelonMod
{
    public override void OnInitializeMelon()
    {
        var root = Path.Combine(MelonEnvironment.UserDataDirectory, "FreedomArrow");
        Directory.CreateDirectory(root);
        DatabaseMerge.Install(root, LoggerInstance);
        ForestCover.Install(root, LoggerInstance);
    }
}
