# PLA TEST Build 28

**Three targeted emblem corrections, white-outline grey-fill right-facing weapon HUD and Russia → USA → China country controls. Original approved masters and all gameplay/model/music data retained. Native inspection pending.**

## Historical Build27

# PLA TEST Build 27

**Replaces Blood Wolves, Mountain Hunters and Blue Sword with photographed central motifs. All26 custom unit-icon families now use clean white/transparent exports; baked grey-green shading and low-alpha halos are removed. Original approved masters are preserved; other silhouettes/layouts remain. Four service badges retain their approved star/八一 contrast; Motorized badge is whitened consistently. Gameplay, models, offsets, weapon HUD, rigging, music and audio stayBuild26. Native appearance pending.**

## Historical Build26

# PLA TEST Build 26

**Corrects the runtime MelonInfo version that remained23 and caused Build25 to refuse its PLA payload. All Build25 artwork, geometry, contrast, gameplay and shared assets are retained. Compiled identity is now checked against channel/build metadata before packaging. Native verification pending.**

## Historical Build25

# PLA TEST Build 25

**Four branch badges now give the 八一 characters stronger contrast against the star. Only existing fill/stroke colors change. Exact shapes, alpha, sizes and positions are preserved; all approved unit icons and gameplay remain Build24. Native appearance pending.**

## Historical Build24

# PLA TEST Build 24

**Approved infantry unit emblems and five branch spec badges. All Build23 gameplay data, weapon HUD art, models, rigging, audio and FA Music1.5.0 retained. Native appearance pending.**

Thirteen approved unit profiles use the reviewed shapes; the earlier requested Godsword blade-only correction is included. Air Force, Ground Force, Rocket Force and Navy spec icons reuse actual branch-badge central SVG geometry; Motorized reuses its approved unit emblem. No new combat statistics or roster assignments.

## Historical Build23

# PLA TEST Build 23

**Build23 combines the complete Build22 emblem/name refinement with the installed FA Music1.5.0 native Home selector. Every game-table field and all64 addressed icon PNGs match Build22; approved Thunder Gods and Whistling Arrows remain untouched. Audio, models, ammo, stats, rigging, preferences and Build17 grouping are retained. The music selector was tested separately on Build21; the combinedBuild23 pack remains untested in-game.**

## Historical Build19 identity and initial badge pass

# PLA TEST Build 19

**Build19 adds patch-derived monochrome unit icons to all90 designer squads and standardizes14 named-team labels from published sources. Generic squads retain their role names with parent-branch insignia; exact-patch and motif/fallback evidence are recorded separately. The eight custom weapon profiles now face right and use filled pale normal/outline sprites with a dark keyline, matching actual native infantry HUD captures. Build17 grouping, all28 rigging fixtures, portraits, ammo, stats, loadouts and model alignment are retained. Native appearance remains untested.**

## Historical Build18 weapon-art candidate

# PLA TEST Build 18

**Weapon HUD revision: replaces the rejected block sketches with detailed native stand-in art for 341 entries and eight custom Chinese profile families (16 normal/outline sprites) for ten entries. Four custom profiles come from the approved meshes; four bullpup profiles use photo references or marked family approximations. Build17 Arsenal grouping is retained. Unit artwork, ammo, weapon stats, loadouts, models and rigging are unchanged. Native HUD validation is pending.**

## Historical Build17 UI correction

# PLA TEST Build 17

**Arsenal specialization presentation fix: shared PLA units follow a selected specialization heading instead of remaining under their first eligible heading. Native availability, search, category/type filters, normal/photo cards and callbacks stay in use. Build16 weapon-family HUD artwork and all existing gameplay, infantry sizes, models, offsets and music are retained. Native UI verification is pending.**

## Historical Build16 weapon HUD update

# PLA TEST Build 16

**Weapon HUD artwork update: 307 vehicle weapon definitions and 44 designer-infantry weapon definitions use 108 physical-family silhouette assets. Related variants share art. Unit portraits, unit thumbnails, ammunition icons, stocks, loadouts, performance, models and saved rigging are unchanged from Build 15. These are simplified recognition drawings; prototype and unnamed weapon geometry remains provisional. Native HUD validation is pending.**

## Historical Build 15 model update

# PLA TEST Build 15

**Final family-model reuse correction: J-20B uses the installed J-20 mesh, J-8II uses J-8 and Y-20B uses Y-20. VT-1A, VT-4, Type 80, Type 63 APC and Type 89/89A reuse the closest installed PLA tank/APC family meshes. This changes nine visual bindings, with Build14 weapons, ammunition, armor, squads, spec pools, camo and saved offsets unchanged. These are explicit related-family stand-ins, not newly acquired exact meshes. Native validation remains pending.**

## Historical Build14 implementation

# PLA TEST Build 14

**This complete PLA draft imports all 90 named squad-designer rows and gives all 160 equipment cards isolated weapon/ammunition definitions with custom HUD artwork. Equipment remains assigned across the five PLA branches, each of the six named gunships retains a Recon card, and all 28 original infantry rigging fixtures stay in Test. Native Arsenal, deck and combat validation remains pending.**

- Infantry names, sizes, Recon flags, selected rifles, extra weapon counts, fixed munitions and design notes follow the saved live sheet rows 8–97. The 18 earlier combat drafts are hidden and their data retained to avoid duplicate playable designs. The 15 named Test concepts remain in Test alongside the 28 rigging fixtures.
- Use installed PLA bodies and saved arm/hand fit. Airborne, Motorized and conscripts use desert uniforms; Ground Force and Marines/SF use green. Armor uses the corresponding native regular/shock/elite tier with five HP per soldier. Missing handheld meshes keep their documented native analog; no missing model is described as installed.
- Ground and rotorcraft get explicit fixed armament drafts. Aircraft have PLA labels and appropriate native analog kits; transports/surveillance platforms remain unarmed, legacy fighters do not inherit modern missile kits, and ground-attack drones carry guided bombs/missiles. This is a design baseline, not final Chinese performance or a full set of weapon upgrade options.
- HJ-10/AFT-10 use the M6 Linebacker chassis and exact vanilla Hellfire ammunition behavior: 36-degree loft, terminal-guidance seeker, reacquisition, eight ready/eight total missiles and no unrelated Bradley cannon. The installed PLA AFT-10 mesh remains the visible model. Code/data support the guidance description; firing over buildings is not yet proven in a game.
- Weapon and ammunition HUD icons are embedded transparent silhouettes. Stocks preserve the native logical-shot/HUD-multiplier relationship; any rounding is listed in the armament receipt. Type 96 total load is sourced at 42 rounds; ammunition mixes and unsourced capacities remain explicit drafts.
- Utility transports are shared and capacity-checked against the exact squad sizes. The basic truck is available to oversized squads. Gunships and unmanned aircraft carry no infantry. No squad is shrunk to fit a transport.
- Approved mesh/texture files, canopy finish, immediate stand-in hiding, rigging comparisons, weapon/body offsets, music and preferences are retained. Available PLA meshes are reused for related variants; pending assets use the closest native stand-in.
- RU/US selectors and spec controls stay visible with their cards hidden. No naval unit or White Emperor is playable. YJ-18 remains a ground cruise-missile launcher. Public LIVE dev.45 remains locked.

## Evidence and editable drafts

The package includes `pla-vehicle-armament.json`, `pla-infantry-designer.json` and `pla-spec-assignments.json`, with source IDs, stocks, model bindings, camo, troop counts and limits. The Google Sheet remains editable. A table/package check does not prove animations, custom sprites, guidance, reload timing or combat behavior in the native game.

## Historical Build 13 context

# PLA TEST Build 13

**All equipment now belongs to the five main PLA specs. Test contains only the 28 infantry appearance/rigging fixtures. The six named gunships each have a separate recon card. Basic ground and helicopter transports are shared where appropriate. This is an editable draft; native Arsenal, deck creation and combat validation remain pending.**

- Airforce / Airborne gets the air and airborne equipment; Armored gets heavy tracked systems; Rocket Force / Conscripts gets missile/rocket support and legacy/reserve equipment; Marines / SF gets amphibious ground equipment and SF; Motorized gets mobile wheeled systems. Existing deliberate support attachments are retained.
- All six recon gunships inherit their parent's weapons, sensor baseline and provisional cost. Their CategoryType is Recon; they are real separate unit definitions, ready for later optic/loadout/price edits. The previous six planned rows are promoted to these IDs.
- Z-20 utility lift serves all five specs. Z-8L serves Airforce and Marines; Z-9 basic lift serves the light/mobile branches. Basic APCs and IFVs are reused without creating duplicate unit definitions. Every infantry transport link is checked against its actual squad size.
- Gunships are excluded from troop transport choices. The Z-9WA, Z-19 and Z-21 donor troop capacities are cleared; no weapon, armor, sensor or price buffs are added.
- Infantry rigging fixtures remain Test-only, including all approved outfit comparisons and the two extra model-list infantry fixtures. The 18 branch infantry roles remain in their assigned specs.
- Approved geometry, textures, canopies, loading behavior, body/weapon offsets, music and preferences are retained. Russia/USA selector/spec controls remain visible with their unit cards hidden. Public LIVE dev.45 stays locked.
- The equipment design sheet remains the editing surface; human design fields must be preserved during roster synchronization.

- No ships, submarines or UUVs are playable. White Emperor is excluded. YJ-18 is a ground cruise-launcher draft in Rocket Force, using native Iskander-K appearance and two cruise missiles until its final design is supplied.

## Historical Build 12 context

# PLA TEST Build 12

**Named stand-ins cover all 157 Model links entries that identify a model or reuse choice. This adds 102 units, reuses existing cards where appropriate, moves SF into Marines / SF, and restores RU/US selectors and specs for UI testing with their unit cards hidden. It retains the combined Build 11 arm repair and aircraft loading/canopy changes. Native filtering still needs validation after the fix.**

## Current changes

- Airforce / Airborne keeps the airborne line squad. SF Assault, SF Recon and QTS-11 Digital Scouts are Marines / SF only. All outfit comparisons remain in Test.
- Model availability and ownership are separate from card creation. Missing/pending model files use named donor stand-ins, with no claim of final Chinese weapons or statistics. New unassigned designs are parked in Test.
- One actual platform can serve several specs or catalogue source rows. Alternate paint/seller packages do not automatically produce duplicate unit definitions. New role variants can be designed separately.
- SR-5 now uses the approved native HIMARS visual. HQ-17 retains native TOR. Approved body/weapon offsets, infantry geometry, canopy finish and immediate stand-in hiding remain intact.
- Russia and USA country/spec controls remain. Their unit DisplayInArmory flags are off. Keeping the native country groups avoids the single-country duplicate mask seen in Build 11; native behavior remains to be tested.
- PLA equipment designs is the canonical editable equipment sheet. PLA equipment by spec links to it and groups entries by spec and class. It contains 174 current/draft equipment records and six planned recon gunships. Infantry uses the separate squad designer; infantry already in the game is retained. Recon plans do not add speculative game units or weapon statistics.
- The public LIVE dev.45 launcher lock remains unchanged. No multiplayer test was performed.

## Earlier Build 11 context

**First PLA branch draft: five planned specializations, a Test pool, and 18 donor-based infantry roles in one complete pack. The arm fit is replaced to preserve forearm and hand thickness. Data and offline previews can be checked; native Arsenal, deck creation and combat remain unverified.**

## Changes in this pack

Build 11 combines the Build 9 branch/Test/infantry work with Build 10 immediate stand-in hiding. Loading failure still restores the original model.


- China is the only selectable nation in the test pack. Russia and USA cards/specs are hidden, while their donor data remains internally.
- Airforce / SF, Ground Force / Armored, Rocket Force / Conscripts, Naval / Marines and Motorized have separate primary/shared unit pools. Category budgets are provisional at 5,000 points per spec.
- Test contains 52 cards: unused or additional vehicle variants, all 25 infantry appearance variants and the seven-man weapon demonstration squad. This is a developer pool, not a balanced combat spec.
- Eighteen new infantry roles use the existing PLA bodies and QBZ-191, QBU-191, QTS-11 and QLU-11 where applicable. Heavy Chinese weapons use explicitly documented native stand-ins. Costs and behavior are provisional donor baselines.
- All 25 appearance variants receive the replacement arm fit. Forearm cross-sections use rotation plus length fitting; hands use a rigid rotation. Approved body and weapon offsets and woodland helmet clearance remain unchanged.
- Existing aircraft canopy repairs and reflections from pinned Build 8 are preserved. Existing vehicle combat statistics, textures, music and voices remain unchanged by this task.
- New transports are limited to the correct branches and sufficient infantry capacity.

## Testing and later integration

Use the complete numbered PLA pack, not historical PLA.infantry or PLA.48 prototypes. This candidate is not installed. Native country 4, deck creation and in-game animation need testing. No multiplayer test was performed.

Later, merge the source feature into LIVE with fresh IDs and without the PLA-only visibility rules. Four existing PLA unit IDs conflict with current LIVE definitions. Do not copy the PLA archive over LIVE or change the public dev.45 lock.

## Preserved project guide and earlier release notes

The following material is retained as historical context from the Build5 source. The current PLA-only candidate is described above.

## freedom-arrow

**Unreleased 0.6 development — ActualArrow features:** [build instructions and changes](releases/0.6/README.md) on `codex/0.6-development`. 0.5 stays on `codex/0.5-development` (accuracy, [changes](releases/0.5/README.md)); 0.4 stays on `codex/0.4-development`.

**Unreleased 0.4 development:** [build instructions and changes](releases/0.4/README.md) on `codex/0.4-development`. 0.3 stays on `codex/0.3-development`.

**Unreleased 0.3 development:** [build instructions and changes](releases/0.3/README.md). 0.2 stays on `codex/0.2-development`.

**0.2 development:** [build instructions, included changes and held work](releases/0.2/README.md). The dev.38 data candidate is built offline; recon and card splits remain incomplete, and in-game acceptance is pending. Its release build uses `releases/0.2/build.py`, not the generic channel package command. Lateralus's optics/stealth/noise cleanup is preserved.

**Prepared 0.1 candidate:** [download, scope and source](releases/0.1/README.md) · [Linux deployment](docs/releases/0.1-linux.md). This review branch keeps detection, stealth and concealment vanilla; revised live acceptance and multiplayer remain unverified.

Tools and data for a Broken Arrow gameplay mod. Gameplay changes live in JSON constants. A MelonLoader plugin inside the `.bamod` applies those constants when the game loads. Players install and launch the mod with [BAModManager](thirdparty-tools/BAModManager-main/README.md): the Mod Manager for development, and BAModLauncher for release.

The game is a Unity 6 IL2CPP title. The database is one `DataBaseCompiled` object inside `BrokenArrow_Data/data.unity3d`: 24 AES-256-CBC JSON tables. BAModLauncher is what players press. It installs MelonLoader and this modpack, starts the game with Anti-Cheat disabled, and **Play vanilla with no mods** removes MelonLoader's `version.dll`.

Do not play ranked or quick match while MelonLoader is installed.

### Layout

| Path | What it is |
| --- | --- |
| `pipeline/` | Extract, patch, inject, rebase, and pack a `.bamod` |
| `runtime/FreedomArrow/` | MelonLoader plugin that applies constants and formulas |
| `mod/constants/` | Stable gameplay changes to the 24 tables |
| `mod/manifest.json` | Game build the stable constants were last reconciled with |
| `mod/formulas/` | Stable injected formulas, one file per game method |
| `mod/testing/constants/` | Testing gameplay changes |
| `mod/testing/formulas/` | Testing injected formulas |
| `mod/testing/manifest.json` | Game build the testing constants were last reconciled with |
| `mod/modpack.json` | Modpack id, version, and GitHub repos for Stable and Testing |
| `config.template.YAML` | Committed config template |
| `thirdparty-tools/BAModManager-main/` | BAModManager and BAModLauncher source |
| `thirdparty-tools/` | Also vendors Bodkin, MelonLoader, Il2CppDumper, and ILSpy |
| `BrokenArrow_Data/` | Local game data. Gitignored |
| `cache/` | Vanilla snapshots and launcher backups. Gitignored |
| `dist/` | Patched bundles. Gitignored |

### Onboarding

You need Python 3.11 or newer, and a Broken Arrow install that contains `BrokenArrow.exe` and `BrokenArrow_Data/data.unity3d`. A copy of `BrokenArrow_Data` in the repo root is valid when `game_root` is the repo root.

From the repo root:

```text
python -m pip install -r pipeline/requirements.txt
copy config.template.YAML config.YAML
```

On Linux or macOS, `cp config.template.YAML config.YAML`.

Edit `config.YAML` and set `game_root` to the install directory. Quote the path. Forward slashes work on Windows and Linux. Examples are in the template. `config.YAML` is gitignored. Every pipeline command stops if it is missing.

Leave `write_game_bundle` false until you intend to copy a bundle over the game. `discover`, `decrypt`, `survey`, `il2cpp`, `apply`, and `package` never write inside `game_root`. `inject` writes `dist/`, not the game. `hangar` writes inside `game_root`, and only when that flag is true.

Build the plugin before packaging:

```text
dotnet build runtime/FreedomArrow/FreedomArrow.csproj -c Release
dotnet run --project runtime/FreedomArrow.Tests/FreedomArrow.Tests.csproj -c Release
```

The console checks load the real plugin and exercise registration, generated hook calls, and encrypted table preparation. They do not start Unity or prove native hooks or combat behavior. The plugin and console checks target .NET 6, matching the bundled MelonLoader host.

Run commands from the repo root so Python can import `pipeline`:

```text
python -m pipeline decrypt
python -m pipeline apply
python -m pipeline inject
python -m unittest pipeline.tests.test_pipeline pipeline.tests.test_package
```

`decrypt` reads the live database and writes `cache/vanilla/<build-id>/`. When an object has `MainBuildDatabase` and level 2, that object is the live database. Otherwise the one with the most units is used, and every candidate path id and unit count is printed. The first run hashes `data.unity3d` and extracts `globalgamemanagers.assets`. Later runs reuse that snapshot.

`inject` repacks the whole archive into `dist/<channel>/data.unity3d`. On a current game that is several gigabytes and takes a few minutes. It also writes `dist/<channel>/channel.json` with the vanilla build id the bundle was built from.

### How constants are written

This section is the authoring shape. The cost object is an example of that shape. It is not a catalogue of mechanics.

A constant file names the place the game or the plugin actually applies the change. A number is a new literal. A string names something that already exists: a field, a return value, a component, or an enum. Do not add a key the game or the hook does not have.

**Existing table data.** `mod/constants/<table>.json` is one of the 24 database tables. An empty object changes nothing. The example sets one field on one row:

```json
{
  "1": { "Cost": 40 }
}
```

A list of rows with an `Id` field is also accepted. The pipeline rejects an unknown file, a missing `Id`, a type change, and a foreign key that does not point at a row. Rows you do not mention stay as the original ciphertext, so an empty constants directory round-trips to the original object bytes.

**Serialized config edits are not implemented.** `mod/configs/<ClassName>.json` and `mod/testing/configs/<ClassName>.json` are reserved for a future ScriptableObject application path. Packaging rejects JSON files there. If JSON files are already installed under `UserData/FreedomArrow/configs`, plugin startup reports the unsupported input and leaves gameplay hooks uninstalled. Reading fields from `dump.cs` or decoding a config asset does not apply edits to that asset.

**Code at a method.** `mod/formulas/<Class>/<Method>.json` names a game method and the parameters its hook reads. The file has `method`, `change`, and `parameters`. `change` is `after`, `before`, `inside`, or `instead`. Only `after` is accepted today. The other three are rejected until a hook implements them.

This file shape is one `after` hook. No hook is registered until a class is added to `FormulaHost`.

```json
{
  "method": "Game.OtherClass.OtherMethod",
  "change": "after",
  "parameters": {
    "scale": 1
  }
}
```

`parameters` are the values for that hook. A new method is a new file plus a hook. `package` checks the envelope only.

Day-to-day and release are `package`, then BAModManager or BAModLauncher PLAY. The plugin applies whatever constants and formulas are in the package. **Play vanilla** stays the manager's button.

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

`decrypt`, `apply`, and `rebase` are the offline checks. `apply` merges constants and checks links without touching the game. `inject` and `hangar` are diagnostics. `hangar` still requires `write_game_bundle`: it installs `dist/stable/data.unity3d`, launches the game, and restores the previous file when the process exits.

### BAModManager

Source is in [thirdparty-tools/BAModManager-main](thirdparty-tools/BAModManager-main/README.md). It builds two programs. The Mod Manager is for development. BAModLauncher is what players get. Both already have **PLAY** and **Play vanilla with no mods**. Stable and Testing on the launcher are two GitHub repos, each publishing a `.bamod`.

Build them from that directory with the .NET 8 SDK:

```text
build.bat
build_launcher.bat owner/freedom-arrow owner/freedom-arrow-testing
```

`build.bat` writes the Mod Manager zip. `build_launcher.bat` with two `owner/repo` arguments writes a launcher whose Stable and Testing buttons follow those repos. Fill `repo` and `testingRepo` in [mod/modpack.json](mod/modpack.json) with the same names before you publish.

Pack the mod for either channel:

```text
python -m pipeline package --channel stable
python -m pipeline package --channel testing
```

Each command writes `dist/<channel>/FreedomArrow-<version>.bamod`. The zip contains `mod.json` (`"type": "modpack"`), `Mods/FreedomArrow.dll`, the non-empty constant files under `UserData/FreedomArrow/constants/`, and formula files under `UserData/FreedomArrow/formulas/`. BAModManager installs those paths. The patched `data.unity3d` is not inside the package: it is several gigabytes, and the manager does not replace `BrokenArrow_Data`. When `mod/modpack.json` has repos, packaging also writes `dist/launcher.json`:

```json
{ "modpack": "owner/freedom-arrow", "testing": "owner/freedom-arrow-testing" }
```

Put that file next to `BAModLauncher.exe` if you are using the generic launcher instead of `build_launcher.bat`. Publish each `.bamod` as a GitHub release asset. The tag must match `version` in `mod/modpack.json` (`v0.1.0` for version `0.1.0`). PLAY downloads a newer release when the tag is newer than the installed modpack. Keep `id` unchanged across versions.

Drag the `.bamod` onto BAModManager to confirm it installs before you publish it. PLAY in either program starts the game with Anti-Cheat disabled. **Play vanilla with no mods** removes `version.dll` and starts the normal game.

### After a game update

Steam replacing `data.unity3d` is expected. Keep the previous vanilla snapshot in `cache/` until the new one is reconciled.

```text
python -m pipeline update --channel stable
python -m pipeline update --channel testing
```

`update` decrypts the new bundle, rebases that channel's constants, applies them, and injects. A constant is kept when the game did not change that field. When both sides changed it, the row disappeared, or the field's type changed, rebase writes `cache/rebase-conflicts-<channel>.json` and leaves the manifest on the old build. Read the report, edit the constants, then either run `rebase` again or, after you have decided to keep your values, run:

```text
python -m pipeline rebase --channel stable --accept
```

`--accept` records the new build id and leaves the constants in place.

### Commands

| Command | What it does |
| --- | --- |
| `discover` | Find `DataBaseCompiled` by name and record path id, script, and build id |
| `decrypt` | Write the 24 JSON tables and their original ciphertext |
| `survey` | Catalog cover, forest, stealth, and suppression values into `cache/survey/<build-id>/report.json`. Reads the bundle only |
| `il2cpp` | Dump `GameAssembly.dll` from `game_root` and write cover-config fields and values to `cache/il2cpp/<build-id>/configs.json` |
| `apply --channel` | Merge that channel's constants onto the vanilla snapshot |
| `inject --channel` | Repack `dist/<channel>/data.unity3d` and `channel.json` |
| `package --channel` | Write `dist/<channel>/FreedomArrow-<version>.bamod`, including `Mods/FreedomArrow.dll` |
| `rebase --channel` | Three-way merge of the previous snapshot, the new snapshot, and the constants |
| `update --channel` | Decrypt, rebase, apply, and inject |
| `hangar` | Install the stable bundle, launch, and restore on exit |

`python -m pipeline <command> --help` prints the flags. `--config` selects a file other than `config.YAML`.

### Third-party tools

`thirdparty-tools/BodkinToolkit` is an earlier editor whose write path hardcodes a PathID and drops JSON fields the schema does not name. Do not round-trip the game database through its YAML. The AES field order in `pipeline/tables.py` matches Bodkin's list; the lookup and the authoring format do not.

MelonLoader, Il2CppDumper, and ILSpy are vendored beside BAModManager. The manager downloads MelonLoader when a player presses PLAY. Il2CppDumper and ILSpy are for later UI and behaviour work.

### License

Apache License 2.0. See [LICENSE](LICENSE).

## Document change log

- 2026-11-04 16:54:02 PST (America/Los_Angeles) — Added an unreleased0.2 development/build pointer and explicit recon/card/runtime limits; preserved the0.1 candidate and upstream cleanup.
- 2026-11-04 17:30:00 PST (America/Los_Angeles) — Updated the development pointer to dev.4.
- 2026-11-04 17:54:19 PST (America/Los_Angeles) — Updated the development pointer to dev.5.
- 2026-11-04 18:01:47 PST (America/Los_Angeles) — Updated the development pointer to dev.6.
- 2026-11-04 18:07:58 PST (America/Los_Angeles) — Updated the development pointer to dev.7.
- 2026-11-04 18:11:00 PST (America/Los_Angeles) — Updated the development pointer to dev.8.
- 2026-11-04 18:26:32 PST (America/Los_Angeles) — Updated the development pointer to dev.9.
- 2026-11-04 18:37:44 PST (America/Los_Angeles) — Updated the development pointer to dev.10.
- 2026-11-04 19:05:03 PST (America/Los_Angeles) — Updated the development pointer to dev.11.
- 2026-11-04 19:11:24 PST (America/Los_Angeles) — Updated the development pointer to dev.12.
- 2026-11-04 19:24:04 PST (America/Los_Angeles) — Updated the development pointer to dev.14.
- 2026-11-04 19:37:31 PST (America/Los_Angeles) — Updated the development pointer to dev.16.
- 2026-11-04 19:42:51 PST (America/Los_Angeles) — Updated the development pointer to dev.17.
- 2026-11-05 14:52:23 PST (America/Los_Angeles) — Added the 0.4 development pointer; 0.3 stays on its branch.
- 2026-11-06 14:40 PST (America/Los_Angeles) — Added the 0.5 development pointer (accuracy); 0.4 stays on its branch.
- 2026-11-07 12:43 PST (America/Los_Angeles) — Added the 0.6 development pointer (ActualArrow features); 0.5 stays on its branch.

- 2026-11-10 23:19:11 PST (America/Los_Angeles) — Created the PLA-only five-branch draft instructions,prototype limits and later merge boundary.

- 2026-11-10 23:36:02 PST (America/Los_Angeles) — Preserved earlier guide content and every prior document-log entry under the current Build6 summary.

- 2026-11-11 00:04:13 PST (America/Los_Angeles) — Prepared Build 9 with five branches plus Test, 18 infantry roles and replacement arm fit; preserved Build 8 cockpit work. Native checks remain pending.

- 2026-11-11 00:21:03 PST (America/Los_Angeles) — Combined Build 9 specs and arm repair with Build 10 immediate hiding, retaining failure restoration and canopy assets. Native checks remain pending.

- 2026-11-11 00:59:21 PST (America/Los_Angeles) — Added Build 12 catalogue stand-ins, Marines/SF assignment, RU/US UI controls and linked unit-design sheets. Native filter fix awaiting game validation.

- 2026-11-11 01:12:58 PST (America/Los_Angeles) — Restricted the design tabs to equipment; retained existing infantry in the complete game pack.

- 2026-11-11 01:46:18 PST (America/Los_Angeles) — Assigned equipment to the five specs, added separate recon gunships and shared lift, retained Test-only rigging fixtures.

- 2026-11-11 01:50:37 PST (America/Los_Angeles) — Applied Osama’s no-naval/no-White-Emperor direction and the YJ-18 ground cruise-launcher role.

- 2026-11-11 02:55:11 PST (America/Los_Angeles) — Build 14: imported 90 designer squads, explicit equipment armament and custom weapon/ammo HUD icons, matching infantry camo/armor, capacity-checked transport and vanilla Linebacker guidance for HJ-10. Native validation pending.

- 2026-11-11 03:17:32 PST (America/Los_Angeles) — Build15: corrected nine available PLA family-model bindings; Build14 gameplay tables remain unchanged. Native validation pending.

- 2026-11-11 10:45:47 PST (America/Los_Angeles) — Build16: replaced weapon-class HUD symbols with physical-family weapon silhouettes on equipment and designer infantry. Unit art and gameplay retained. Native visual verification pending.
- 2026-11-11 10:58:01 PST (America/Los_Angeles) — Build17: selected-spec shared-card grouping and normal/photo reset support; retains Build16 weapon HUD art. Native UI verification pending.

- 2026-11-11 11:43:40 PST (America/Los_Angeles) — Replaced rejected weapon sketches, added normal/outline contours, documented native stand-ins and retained the Build17 UI correction.

- 2026-11-11 12:11:09 PST (America/Los_Angeles) — Added researched infantry identity/patch adaptations and corrected custom weapon facing and filled-outline style; preserved all gameplay and approved model bindings.

- 2026-11-11 12:30:17 PST (America/Los_Angeles) — Replaced support/specialty branch badges with weapon/equipment icons and removed SF wreaths while enlarging central emblems; all other game data retained.

- 2026-11-11 12:55:47 PST (America/Los_Angeles) — Build21: refined SF contours and transparent overlap gaps, restored short English labels, and assigned17 mixed rifle/security cards patch art while retaining dedicated weapon-team icons and all gameplay data.

- 2026-11-11 13:02:37 PST (America/Los_Angeles) — Build22 feedback: fierce leopard, coiled sea dragon, visible sword, detailed birds; larger star-free Airborne/Rocket patch motifs; Sky Hunters/Mountain Hunters labels; approved Thunder Gods/Whistling Arrows retained.

- 2026-11-11 13:09:29 PST (America/Los_Angeles) — Build23 merges the verified installed FA Music1.5.0 player with unchanged Build22 art/game data to prevent a full-package switch from reverting the native music selector.

- 2026-11-11 17:15:13 PST (America/Los_Angeles) — Integrated approved unit art and branch spec badges into Build24; retained Build23 gameplay/model/music data.
- 2026-11-11 18:58:42 PST (America/Los_Angeles) — Build25 changes star/八一 color contrast only; source geometry and all other icons retained.
- 2026-11-11 20:22:37 PST (America/Los_Angeles) — Corrected runtime build identity and added compiled-attribute regression check; Build25 artwork retained.
- 2026-11-11 21:12:34 PST (America/Los_Angeles) — Source-photo motif copies and clean-white unit icon export; all original masters preserved.
- 2026-11-11 22:33:26 PST (America/Los_Angeles) — Three unit emblems,16weapon HUD sprites and country-control order corrected.
