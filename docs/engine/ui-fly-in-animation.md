# Menu fly-in animation (GalaxyUI FlyFadeIn)

A menu card that flies in ends at the position it had **before** the layout ran, not where the layout puts it. If a mod moves cards with a layout group (padding, hidden siblings) without also moving the card's own resting position, the card flies to the layout's spot and then snaps to the old one. This is the Play-tab "pop" seen in 0.9.5-dev.35 to dev.38.

## What the game does

Read from GameAssembly 1.2.2.1 (`Plugins.GalaxyUI.Runtime.Animations.FlyFadeIn`, `BrokenArrow.Client.Ecs.UI.Galaxy.GalaxyUiAnimation`):

1. `GalaxyUiBase.OnEnable` (0x49D590) plays the `_onEnabled` animation. `GalaxyUiAnimation.PlayAnimation` (0x49D050) sets `Completed = false`, calls `OnPreStart` at once, then calls `OnStart` after a random `Delay` (through a UniTask when the delay is above 0).
2. `FlyFadeIn.OnPreStart` (0x5B20): `_startPosition = _target.anchoredPosition`; canvas group alpha 0. This runs inside `OnEnable`, before the HorizontalLayoutGroup re-lays the row.
3. `FlyFadeIn.OnStart` (0x5BC0): `_currentPosition = _target.anchoredPosition` (by now the layout's position); moves the card to `_currentPosition - _startValue`; tweens `DOAnchorPos` back to `_currentPosition` and alpha to 1 over `Random(_time)` (default 0.2-0.5 s).
4. `OnComplete` (0x5AC0): `_target.anchoredPosition = _startPosition`; `Completed = true`.

`FlyFadeOut` (`_onDisabled`/`_onHide`) also saves the position in `OnPreStart` and restores it at the end, so the resting position survives closing the menu.

## Consequence

The resting position is a fixed point: each opening ends where the previous one ended, starting from the prefab's serialized position. The layout only changes the flight path.

- Layout padding alone: cards fly to the new spot, then return to the prefab slot (measured 0.9.5-dev.36 at 3840 px: padding 0 -> 406, cards still at x 1472 px).
- Moving the resting position alone: cards fly to the layout's spot, then jump to the new one.

## How Freedom Arrow handles it (0.9.5-dev.39, `RankedPlayTab.cs`)

Before the Play tab first opens, set both: the HorizontalLayoutGroup padding that centres the row, and each card's `anchoredPosition` (anchors x = 0) to the position that layout gives it (`padding + index * (width + spacing) + width * pivot.x`). At rest after each opening the runtime logs the flight target (`_currentPosition`), the resting position and the screen centre (`FREEDOM_ARROW_PLAY_TAB opening N: ...`) and corrects a mismatch once.

Basis: read from game code; the dev.39 behaviour is not yet seen in game.

## The Ranked card is not a game card (24 Nov 2026, Lateralus: slow to appear, snaps to full size)

**Short answer:** Multiplayer and Skirmish are uGUI objects in the Play tab's `HorizontalLayoutGroup`; the game animates them itself. Our Ranked card is an IMGUI overlay (`RankedMenu.OnGUI`) drawn on top of the game UI. It guesses its place, size, fade and hover from the vanilla cards every frame, so it can lag them and copy their states wrongly.

*Details (read from the code and the logged UI tree, not measured in game):*
- **Vanilla card** (`Menu Picture Button - Skirmish`, 300x600): components `Button, RectMask2D, AudioUiEffect, GalaxyUiBase, CanvasGroup, LayoutElement, PlayTabSkirmishButton`; children `image`, `Title`, `Description` (TextMeshPro). `GalaxyUiBase` plays the fade/fly-in on enable and the hover animation; the layout group places it.
- **Ranked card**: `card.png` drawn with `GUI.DrawTexture` beside the last vanilla card (`PlayCards`). It is shown only after several checks: `PlayTab` found (scan every 1 s until found), the Play tab button found and selected (scan every 2 s until found), and a raycast "covered" check cached for 0.25 s. Its alpha copies Skirmish's `CanvasGroup`; its hover is its own `MoveTowards` (8/s).
- **Snap to full size**: the card's base rect is re-taken whenever all vanilla cards have equal widths (`rest`). Moving the pointer from Multiplayer to Skirmish, one card shrinks while the other grows; at the crossing both are equally enlarged, so that frame is taken as the rest layout and the Ranked card is drawn from an enlarged card in one frame.
- **`TextTarget`** (BrokenArrow.Shared.Ecs.Localization, on `Title` and `Description`; GameAssembly 1.2.2.1 `Start` 0x29F0E0, `OnLanguageChange` 0x29ED50, `ChangeKey` 0x29EA10): holds a serialized `_key`; `Start` lower-cases it, caches the TMP/Text component and subscribes to `LocalizationService`; `OnLanguageChange` looks the key up (`Dictionary.TryGetValue`) in the service's `_currentDictionary`, then `_defaultDictionary`, and writes the text. It runs at start and at every language change, so a cloned card's text would turn back into "Skirmish" unless the component is removed or given another key. `ChangeKey(k)` re-runs the lookup; the dictionaries are rebuilt on `ChangeLanguage`, so injected keys would have to be re-added after every language change.
- **`PlayTabSkirmishButton`** (`_button`; `Start`, `OnClick`): adds its click listener at `Start` (runtime, not serialized), so a clone that has this component removed before its first `Start` has no Skirmish click. `GalaxyUiBase` (`_onEnabled`, `_onHover`, `_onEndHover`, `_onClick`, `_onHide`, `_onDisabled`, `_onDestroy` effect containers; pointer enter/exit/click handlers) and `AudioUiEffect` (hover/click sound names) need no change.
- **Done (queued after 0.9.6, Lateralus "queue it")**: `RankedPlayTab.MakeRanked` copies the Skirmish card as `Menu Picture Button - Ranked` into the same row while the Play tab is closed, removes `PlayTabSkirmishButton` and both `TextTarget`s, gives the button a new click event (opens the Ranked page), sets the art `ranked/menu/ranked.png` and the title/description (English or Chinese) at every opening, and places it in the 3-card row with its resting position on the layout position. The IMGUI card code is removed. Not yet seen in game; the log line `FREEDOM_ARROW_PLAY_TAB Ranked card x ..., fly-ins on its own card: N` shows whether the copied fly-in targets the copy.

## Document change log

- 2026-11-22 21:30 PST (America/Los_Angeles) — New: FlyFadeIn save/fly/snap order and the Play-tab fix.
- 2026-11-24 09:4x PST (America/Los_Angeles) — Added: why the IMGUI Ranked card lags and snaps, and the native-card fix direction (Lateralus).
- 2026-11-24 09:5x PST (America/Los_Angeles) — Added: TextTarget and PlayTabSkirmishButton behaviour for a native Ranked card (Lateralus).
- 2026-11-24 10:1x PST (America/Los_Angeles) — Native Ranked card implemented (queued).
