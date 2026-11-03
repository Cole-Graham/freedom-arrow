"""Classifies which research files encode (range, altitude) pairs.

Files in the air-defense group write range -> real_world.low_alt and
altitude -> real_world.high_alt. All other files write the single range into
real_world.ground.
"""
AIR_DEFENSE_FILES = {
    "MANPADS_RESEARCH.md",
    "AIR_TO_AIR_RESEARCH.md",
    "SAM_SYSTEMS_RESEARCH.md",
}


def is_air_defense(filename: str) -> bool:
    return filename in AIR_DEFENSE_FILES
