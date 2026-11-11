"""Put the supplied gloss values directly in HDRP mask alpha.

The glTF exporter does not preserve the source gloss-to-roughness math node as
expected. Correct the packed output from the original maps, without repainting.
"""
from pathlib import Path
import argparse
import json
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source_maps', type=Path)
    ap.add_argument('converted_models', type=Path)
    a = ap.parse_args()
    results = []
    for stem in ['m_blackeagle_cg', 'm_blackeagle_lo']:
        for index, name in [(0, 'smoothiness2.tga'), (1, 'track_smoothiness.tga')]:
            p = a.converted_models / (stem + '_tex' + str(index) + '_mask.png')
            pixels = np.asarray(Image.open(p).convert('RGBA')).copy()
            original = pixels.copy()
            gloss = Image.open(a.source_maps / name).convert('L').resize(
                (pixels.shape[1], pixels.shape[0]), Image.Resampling.LANCZOS)
            pixels[:, :, 3] = np.asarray(gloss)
            assert np.array_equal(pixels[:, :, :3], original[:, :, :3])
            Image.fromarray(pixels).save(p)
            results.append({'file': p.name, 'source': name,
                'smoothness_median': float(np.median(pixels[:, :, 3]) / 255)})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
