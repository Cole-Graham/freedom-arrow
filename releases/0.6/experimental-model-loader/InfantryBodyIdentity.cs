namespace FAModels;
internal static class InfantryBodyIdentity { internal static bool IsSupported(int unitId) => unitId == 901 || (unitId >= 985 && unitId <= 1027) || unitId == 1108 || unitId == 1109; }
