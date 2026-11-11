# PLA weapon HUD artwork

**Build16 replaces weapon-class symbols on 307 equipment weapon definitions and 44 designer-infantry weapon definitions. Unit portraits, unit thumbnails, ammunition icons and gameplay remain unchanged.**

There are 108 embedded transparent PNG resources. Related weapons can share a physical-family silhouette. These are recognition drawings for review at game HUD size, not dimensional drawings or proof of exact variant geometry.

QBZ-191, QBU-191, QLU-11 and QTS-11 use side profiles projected from the exact installed weapon meshes. The editable projections record source hashes in `hud-model-vectors/model-projection.json`. Remaining profiles are original vector sketches. Observed online photo sources, authors and evidence limits are recorded in `weapon-hud-references.json`; the HJ-10 folding-wing photo is an export-family reference. Prototype/unspecified weapons retain family approximations.

The art does not establish final weapon designations, missile models, statistics or ammunition types. In particular, the existing generic gun names and prototype labels still require unit design work.

## Rebuild

Run the normal pinned `prepare.py`, then `render_weapon_hud.py --renderer PATH_TO_RSVG_CONVERT`. Mesh source SVGs are already versioned; `project_weapon_mesh.py` regenerates them from the existing FAM files. `preview_weapon_hud.py` makes review sheets. `verify_weapon_hud.py` compares every effective database field against Build15 and checks alpha/dimensions. The resource-check project verifies the actual compiled PNG bytes.

## Document change log

- 2026-11-11 10:52:55 PST (America/Los_Angeles) — Added weapon-only scope, source/approximation limits, model projection provenance and rebuild checks.
