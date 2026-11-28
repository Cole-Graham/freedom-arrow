# FAModels canopy glass and borrowed cockpit glass

**Short answer:** a jet canopy can borrow the game's own glass material (for example the F-35B canopy, `US_F35B_Glass`). FAModels can only borrow it after the game has loaded that material in the current session. Until then FAModels draws a stand-in ("fallback") glass. From FAModels 0.3.50 a model's `.mat.json` can make that stand-in keep full reflections (`"preserveSpecular": true`). The J-20 uses this.

Basis: read from the FAModels code (`mod/experimental-model-loader/FAModels.cs` `Mat`, `Cockpits.cs` `CockpitMaterial` / `UpgradeFallbacks`) and from Osama's game log of 26 Nov 2026. The 0.3.50 look is theoretical, not yet seen in a game.

---

## Details

**Where the glass settings live.** Each model part has an entry in the model's `.mat.json`, keyed `texture|r,g,b,a`. A canopy entry with `"cockpitDonor": "US_F35B_Glass"` asks for the game's material of that name.

**When the donor is not loaded.** `CockpitMaterial` searches the loaded materials and asset bundles. If the donor is not there, `Mat` logs once:

```
FAMODELS_COCKPIT_FALLBACK US_F35B_Glass: Cockpit donor unavailable: US_F35B_Glass; no substituted material was applied; clear glass used until the donor loads
```

It then uses the entry's own `"fallback"` settings (0.3.43), or clear glass if there are none. The fallback material is remembered, and `UpgradeFallbacks` copies the donor onto it in place when the donor appears (tries after 10, 20 and 40 s, and on scene changes). The log line is `FAMODELS_COCKPIT_UPGRADED`.

Seen on 26 Nov 2026 21:32 (Osama's PC, Arsenal, J-20): the fallback line above, no upgrade line. The F-35B glass is in memory only after an F-35B has been shown.

**Why the fallback was not reflective.** Every see-through (BLEND) FAModels material turns off HDRP "preserve specular lighting", so reflections fade with the glass opacity. That rule came from the F-14 canopy on 9 Nov (clear glass looked milky white). For a tinted canopy it removes most of the reflection.

**0.3.50 change.** `MatP.preserveSpecular` (default false). When true on a BLEND part, FAModels keeps `_EnableBlendModePreserveSpecularLighting` = 1 and its keyword. A cockpit `"fallback"` block can carry it. The value is part of the material cache key. FAModels 0.3.49 and older ignore the field.

```json
"m_j20_cg_canopyhd.png|1.0000,1.0000,1.0000,1.0000": {
  "cockpitDonor": "US_F35B_Glass",
  "fallback": { "alpha": "BLEND", "metallic": 0.0, "smoothness": 0.95, "clearGlass": false, "preserveSpecular": true }
}
```

**Other jets with the same donor fallback** (not changed): F-2, F-35 (K and J2B sets), J-8II, KF-21 (both sets), Mirage 2000, Rafale, Typhoon. Each needs only the same one field in its `.mat.json` files.

**Seen 27 Nov 2026 22:0x (Osama's PC, Arsenal, dev.8):** after an F-35B was shown and the J-20S selected again, still no `FAMODELS_COCKPIT_UPGRADED` line after 45 s; the J-20S canopy stayed on its milky fallback. The upgrade tries are limited (3 per stand-in). So in the Arsenal a donor canopy can stay on its fallback for the whole session. The J-20S canopy no longer uses a donor: its own gold glass texture with `metallic` 0.5, `smoothness` 0.92, BLEND and `preserveSpecular` (seen in game with test files, 22:09). Measured in a game.

## Document change log

- 2026-11-26 21:4x PST (America/Los_Angeles) — New page: donor glass, the fallback, and the 0.3.50 `preserveSpecular` option (Osama: J-20 canopy not reflective).
- 2026-11-27 22:1x PST (America/Los_Angeles) — Donor glass may never upgrade in the Arsenal (seen); J-20S switched to its own glass.
