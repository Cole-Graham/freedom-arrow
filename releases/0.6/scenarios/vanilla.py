"""Vanilla maps with the FA game mode. Zones, spawns, cameras, play areas and AI stay native; only zone values are ours.
Add a map: one entry here, its zone UIDs in settings.json MapZoneWeights, and its four native files in native-pins.json."""
import common as C
# name: (scene, network host, Skirmish host, guid stem, zone name -> value)
MAPS={
    # Osama 2026-11-07. The native network map labels India as Golf; the build shows it as India.
    'Airport':('Airport','Airport_network','Airport_Skirmish','6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01',
               dict(Alpha=4,Delta=4,Foxtrot=3,Golf=3,Hotel=3,India=3,Bravo=2,Charlie=2,Echo=2)),
}
def build(game,out):
    for name,(scene,net,sk,guid,values) in MAPS.items():C.build_pair(game,out,C.vanilla_spec(scene,net,sk,name,guid,values))
