"""Build every FA scenario. Map-specific data lives in sibling modules."""
from pathlib import Path
import argparse, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import highway_2v2, chkalovsk_2v2, dead_center_1v1, dead_center_2v2, airport_5v5, baltiisk_3v3, dam_3v3, oil_rush_5v5, cold_harbor_5v5
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    for mod in (dead_center_2v2, dead_center_1v1, chkalovsk_2v2, highway_2v2, airport_5v5, baltiisk_3v3, dam_3v3, oil_rush_5v5, cold_harbor_5v5):mod.build(a.game_dir,a.out)
if __name__=='__main__':main()
