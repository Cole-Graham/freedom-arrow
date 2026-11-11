namespace FAModels;
internal static class InfantryBodyIdentity
{
    // Existing weapon demo, approved appearance fixtures, and the branch draft roles.
    internal static bool IsSupported(int unitId) => unitId == 901 || unitId >= 985 && unitId <= 1027;
}
