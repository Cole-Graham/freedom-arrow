"""Sam-approved appearance policy, 11 November 2026. Cosmetic presets only."""
def body_preset(unit, spec, troop_type, name):
    # Class wins over branch: every current SF squad uses a night variant.
    if troop_type == 'Special forces':
        return (997, 998, 999, 1000)[unit % 4]
    if spec == 21:
        if troop_type == 'Engineers':
            return 994
        if unit in (1200, 1209):
            return 996
        if unit in (1201, 1202, 1206):
            return 1002
        return 1004
    if spec == 18:
        return (1003, 1001, 1003, 1001, 995)[unit % 5]
    # PLAN naval flight-deck/service crews are deliberately outside this rule.
    if spec == 20 and name.startswith('Marine '):
        return 1003
    return None
