"""Map stable legacy option IDs into the native network's signed 16-bit range."""
def apply(effective, patches, mapping):
    mapping={int(k):v for k,v in mapping.items()}
    options=effective['OptionsJson']; changes=patches['OptionsJson']
    unsafe={k for k in options if not 0<k<=32767}
    assert unsafe==set(mapping),('unsafe option mapping changed',unsafe^set(mapping))
    assert len(set(mapping.values()))==len(mapping)
    assert all(0<v<=32767 and v not in options for v in mapping.values())
    for old,new in mapping.items():
        row=options.pop(old);row['Id']=new;options[new]=row
        patch=changes.pop(str(old));assert 'Id' not in patch
        changes[str(new)]=patch
    assert all(0<k<=32767 for k in options)
    # Saved deck files may contain original int IDs or IDs already narrowed by the game.
    migration=dict(mapping)
    for old,new in mapping.items():
        narrowed=(old+32768)%65536-32768
        assert narrowed not in options and (narrowed not in migration or migration[narrowed]==new)
        migration[narrowed]=new
    return migration
