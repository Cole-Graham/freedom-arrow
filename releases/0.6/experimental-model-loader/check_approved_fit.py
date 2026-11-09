"""Read-only check of Sam's approved body/weapon configuration and geometry."""
import hashlib,json,sys
from pathlib import Path

def main():
    game=Path(sys.argv[1])
    approved=json.loads(Path(__file__).with_name('approved-infantry-fit.json').read_text())
    assets=game/'UserData/FAModels';errors=[]
    for filename,digest in {**approved['file_hashes'],**approved['weapon_mesh_hashes']}.items():
        path=assets/filename
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:errors.append(filename)
    loader=game/'Mods/FAModels.dll'
    if not loader.is_file() or hashlib.sha256(loader.read_bytes()).hexdigest()!=approved['loader_sha256']:errors.append('Mods/FAModels.dll')
    if errors:
        print('Approved infantry fit differs: '+', '.join(errors));return 1
    print('Approved infantry fit matches: body/weapon rules, 3 body meshes, 8 weapon meshes, loader.');return 0

if __name__=='__main__':raise SystemExit(main())
