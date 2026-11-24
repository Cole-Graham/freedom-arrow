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
- **Fix direction**: a native third card cloned from Skirmish inside the same layout group (game animations, layout, fade, hover and sound), with `PlayTabSkirmishButton` removed and our click handler on `Button.onClick`. Interim: freeze the base rect per screen size and drop the scan delays.

## Document change log

- 2026-11-22 21:30 PST (America/Los_Angeles) — New: FlyFadeIn save/fly/snap order and the Play-tab fix.
- 2026-11-24 09:4x PST (America/Los_Angeles) — Added: why the IMGUI Ranked card lags and snaps, and the native-card fix direction (Lateralus).
