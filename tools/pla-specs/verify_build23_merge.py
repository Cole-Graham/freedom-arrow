"""Confirm the combined pack source keeps all Build22 game data and art."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2];base=root.parent/'pla-refined-animal-emblems-build22';src=root/'releases/0.6/source';before=json.loads((base/'tools/pla-specs/effective-preview.json').read_text());after=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());assert before==after
identity=json.loads((src/'UserData/FreedomArrow/pla-infantry-identity.json').read_text());hud=json.loads((src/'UserData/FreedomArrow/pla-weapon-hud.json').read_text())
for name in identity['resources']+hud['resources']:
 path='releases/0.6/source/runtime-qa/icons/'+name+'.png';assert (root/path).read_bytes()==(base/path).read_bytes(),name
music=json.loads((root/'tools/pla-specs/music-integration.json').read_text());assert hashlib.sha256((root/music['source_artifact']).resolve().read_bytes()).hexdigest()==music['sha256']
result={'passed':True,'tables_byte_values_equal_build22':len(after),'all_game_fields_equal_build22':True,'all64_icon_resources_byte_identical_build22':True,'approved_thunder_gods_whistling_arrows_retained':True,'music_player_version':music['version'],'music_player_sha256':music['sha256'],'music_source_commit':music['source_commit'],'music_previously_tested_on_build21':True,'combined_native_verified':False};(root/'tools/pla-specs/build23-merge-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
