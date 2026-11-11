"""Stage the requested F-21 size change without changing an installed game.

Use the current full models.json as input; include the staged mapping in the
next asset package and publish its manifest when the playtest batch is released.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('current_mapping', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.current_mapping.read_bytes()
    mapping = json.loads(source)
    name = 'F-21 Super Tomcat'
    before = dict(mapping[name])
    assert before['file'] == 'm_f14_cg.fam'
    assert before['battle'] == 'm_f14_lo.fam'
    assert before.get('align') is False
    assert before.get('scale', 1) in (1, 1.1), 'Recheck changed baseline scale'
    mapping[name] = {**before, 'scale': 1.1}
    encoded = (json.dumps(mapping, indent=2) + '\n').encode()
    assert args.current_mapping.resolve() != args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(json.dumps({
        'unit': name,
        'baseline_scale': 1,
        'target_scale': 1.1,
        'before': before,
        'after': mapping[name],
        'input_sha256': hashlib.sha256(source).hexdigest(),
        'output_sha256': hashlib.sha256(encoded).hexdigest(),
        'installed': False,
        'native_verified': False,
    }, indent=2))


if __name__ == '__main__':
    main()
