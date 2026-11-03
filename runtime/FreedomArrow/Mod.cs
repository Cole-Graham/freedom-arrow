using MelonLoader;
using MelonLoader.Utils;

[assembly: MelonInfo(typeof(FreedomArrow.FreedomArrowMod), "Freedom Arrow", "0.1.0", "Freedom Arrow contributors")]
[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("FreedomArrow.Tests")]

namespace FreedomArrow;

public class FreedomArrowMod : MelonMod
{
    public override void OnInitializeMelon()
    {
        var root = Path.Combine(MelonEnvironment.UserDataDirectory, "FreedomArrow");
        Directory.CreateDirectory(root);
        try
        {
            CheckSupportedInputs(root);
        }
        catch (InvalidDataException ex)
        {
            LoggerInstance.Error(ex.Message);
            return;
        }
        DatabaseMerge.Install(root, LoggerInstance);
        ForestCover.Install(root, LoggerInstance);
    }

    internal static void CheckSupportedInputs(string root)
    {
        var directory = Path.Combine(root, "configs");
        if (Directory.Exists(directory) && Directory.EnumerateFiles(directory, "*", SearchOption.AllDirectories)
            .Any(path => string.Equals(Path.GetExtension(path), ".json", StringComparison.OrdinalIgnoreCase)))
            throw new InvalidDataException("ScriptableObject config edits are not implemented. Remove JSON files from " + directory + "; gameplay hooks were not installed.");
    }
}
