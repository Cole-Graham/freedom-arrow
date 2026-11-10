def apply(data, contract, put):
    fields = ('LowAltRange', 'HighAltRange', 'Damage')
    for key, row in contract['ammo'].items():
        aid = int(key)
        current = data['AmmunitionsJson'][aid]
        assert [current[f] for f in fields] == row['before'], ('SPAAG baseline changed', aid)
        assert len(row['after']) == len(fields)
        put('AmmunitionsJson', aid, dict(zip(fields, row['after'])),
            'Lateralus half-Actual Arrow SPAAG range/damage test; SEAD speed unchanged')
