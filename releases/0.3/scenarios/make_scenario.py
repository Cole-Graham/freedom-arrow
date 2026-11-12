"""Build every FA scenario. Map-specific data lives in sibling modules."""
from pathlib import Path
import argparse, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import dead_center_1v1, dead_center_2v2
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    for mod in (dead_center_2v2, dead_center_1v1):mod.build(a.game_dir,a.out)
if __name__=='__main__':main()
