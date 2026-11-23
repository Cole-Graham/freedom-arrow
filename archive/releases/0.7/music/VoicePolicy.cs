namespace FAMusic;
internal static class VoicePolicy
{
    public static bool UseCustom(string selectedPack) => !string.IsNullOrEmpty(selectedPack) && selectedPack != "Game music";
}
