"""Vanilla maps with the FA game mode. Zones, spawns, cameras, play areas and AI stay native; only zone values are ours.
The Skirmish map is the master (Osama 2026-11-07): values name exactly its zones, and network-only zones are removed.
Add a map: one entry here, its zone UIDs in settings.json MapZoneWeights, and its four native files in native-pins.json."""
import common as C
# name: (scene, network host, Skirmish host, guid stem, zone name -> value[, online flavor from the Skirmish mission])
MAPS={
    # Osama 2026-11-07. The native network map labels India as Golf; the build shows it as India.
    'Airport':('Airport','Airport_network','Airport_Skirmish','6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01',
               dict(Alpha=4,Delta=4,Foxtrot=3,Golf=3,Hotel=3,India=3,Bravo=2,Charlie=2,Echo=2)),
    # Osama 2026-11-07. The network map's extra Hotel (south-west) is not on the Skirmish map, so it is removed.
    'Baltiisk':('Baltiisk','Baltiisk_network','Baltisk_Skirmish','6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c02',
                dict(Delta=4,Echo=4,Foxtrot=3,Golf=3,Alpha=2,Bravo=2,Charlie=2)),
    # Osama 2026-11-07, on the Skirmish map. Bravo was not given; 2, like Kilo across the river. The network Dam has
    # 10 other zones in other places, so the online flavor is built from the Skirmish mission.
    'Dam':('Dam','Dam_network','Dam_Skirmish','6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c03',
           dict(Charlie=4,Delta=4,Hotel=4,India=4,Juliet=4,Alpha=3,Foxtrot=3,Golf=3,Lima=3,Bravo=2,Echo=2,Kilo=2),True),
}
def build(game,out):
    for name,(scene,net,sk,guid,values,*online) in MAPS.items():C.build_pair(game,out,C.vanilla_spec(scene,net,sk,name,guid,values,*online))
