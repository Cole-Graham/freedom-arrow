# PLA unit and weapon HUD artwork

**Build 20 uses weapon/equipment-led unit icons for 59 support and specialty squads. All 14 named SF cards retain their sourced or documented fallback central emblems, with wreaths removed and the emblems enlarged. The 17 other branch cards retain their existing icons. Names, portraits, ammo, stats, loadouts, models, rigging and the Build 17 grouping correction are unchanged. Native appearance is untested.**

## Build 20 unit-icon policy

Named formations use central emblems without a wreath. Specialist teams use a native infantry weapon/equipment thumbnail that matches their function; QLU11 and the Test QTS cell use the existing approved model-derived contours. Native icons are shape/class stand-ins, not newly verified exact Chinese weapon drawings. The artwork source and donor unit ID are recorded per card.

**Build 19 adds patch-derived monochrome unit icons to all 90 designer squads and standardizes14 named-team labels from published sources. Generic squads retain their role names with parent-branch insignia; exact-patch and motif/fallback evidence are recorded separately. The eight custom weapon profiles now face right and use filled pale normal/outline sprites with a dark keyline, matching actual native infantry HUD captures. Build 17 grouping, all 28 rigging fixtures, portraits, ammo, stats, loadouts and model alignment are retained. Native appearance remains untested.**

## Historical Build18 pass (superseded style)

**Weapon HUD revision: replaces the rejected block sketches with detailed native stand-in art for 341 entries and eight custom Chinese profile families (16 normal/outline sprites) for ten entries. Four custom profiles come from the approved meshes; four bullpup profiles use photo references or marked family approximations. Build17 Arsenal grouping is retained. Unit artwork, ammo, weapon stats, loadouts, models and rigging are unchanged. Native HUD validation is pending.**

## Comparison and limits

The source comparison uses actual native weapon art visible in the 2 November Arsenal captures, alongside old and revised custom icons in equal preview slots. Gameplay values in those captures belong to ActualArrow 1.1.20 and are not a vanilla balance baseline. Offline texture exports showed artifacts, so they were rejected as visual approval evidence.

Native game addresses are resolved from the native weapon definitions, with closer physical-shape substitutions for selected missiles, guns and machine guns. They are explicit stand-in art, not exact drawings of every Chinese weapon. No native artwork pixels are repackaged. The source index records the bundle checksum.

Custom profiles face left and use natural aspect ratios, a pale foreground, real contour holes and separate outline resources. QBZ-191, QBU-191, QLU-11 and QTS-11 are unions of projected installed mesh triangles. QBZ-192 shares the QBZ-191 family mesh. QBZ-95 and QBU-88 follow public photo references; QBZ-97 and QBB-95 remain related-family approximations. Source links and mesh checksums are recorded in the receipts.

## Rebuild and checks

Run the pinned prepare.py, then render_weapon_hud.py with the RSVG renderer. project_weapon_mesh.py requires Shapely and rebuilds vector contours from FAM geometry without changing the models. reference_weapon_vectors.py rebuilds the editable reference paths. preview_weapon_hud.py creates the HTML comparison from unchanged images.

extract_baseline.py reconstructs all effective Build17 rows from the exact predecessor archive. verify_weapon_hud.py permits only weapon HUDIcon changes and checks all custom sprites and native addresses. The resource-check project compares the compiled PNG bytes with the approved source. Package with package_hud.py over the pinned Build17 archive, preserving its UI receipt and every model/music payload.

## Document change log

- 2026-11-11 10:52:55 PST (America/Los_Angeles) — Added weapon-only scope, source/approximation limits, model projection provenance and rebuild checks.

- 2026-11-11 11:43:40 PST (America/Los_Angeles) — Build18: replaced rejected family sketches, recorded native-art reuse, separate outlines, actual capture comparison and evidence limits.

- 2026-11-11 12:11:09 PST (America/Los_Angeles) — Build19 corrects facing to muzzle-right and uses filled outline sprites; adds patch-derived unit thumbnails and explicit name/patch provenance.

- 2026-11-11 12:30:17 PST (America/Los_Angeles) — Added the wreath-free SF/weapon-team policy, native donor references and presentation-only scope.
