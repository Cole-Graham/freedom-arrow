# How we take unit card images

**Short answer:** take a night screenshot of the unit in the Arsenal, in the **Basic Hangar Indoors** hangar, from the front diagonal, looking down. Keep the hangar background, darken the edges so the light falls on the unit, then make the three card files the game uses. This copies the look of the vanilla cards.

Agreed with Osama on 27 November 2026 (thread "blue dragons"). **Status:** process only. Basic Hangar Indoors (`HangarIndoors.cs`, `298266fa`) gets its first in-game test in the next dev build. No card has been made this way yet.

---

## 📋 Step by step

1. **Hangar:** in the main menu, select **Basic Hangar Indoors**. Every unit stands on the spot where the basic hangar shows planes, and only one model is on the spot at a time.
2. **Time:** set the hangar time to **Night**, with the hangar menu's time button.
3. **Unit:** open the unit in the Arsenal. Use its default paint unless the card needs a different one.
4. **Camera:** use the same angle and distance for every unit (see "The angle" below).
5. **Interface:** hide the interface with the hangar's hide button, so the shot has no menus in it.
6. **Screenshot:** take a full-resolution screenshot of the game window.
7. **Edges:** darken the edges with the script, to the vanilla brightness curve (see "Edge darkening" below).
8. **Card files:** make the full picture, `_BASIC` and `_HOVER` (see "The three card files" below).
9. **Check:** look at every card before it goes into a build. Check that the unit is complete, centred and not cut off, and that the `_BASIC` cutout has clean edges.

---

## 📐 The angle

- **Direction:** front three-quarter view. The nose (or gun) points to the **left** of the picture.
- **Height:** the camera is a little above the unit and looks down at a diagonal ("that perfect front diagonal top down view", Osama).
- **Position:** the unit is in the centre. It takes about the middle half of the picture width, with floor visible all around it.
- **Same for every unit:** keep the same angle and distance, so all the cards match. A big unit (a plane, a long truck) can use a little more distance, so it is not cut off.

---

## 🔦 Edge darkening

We keep the screenshot's own background, but the edges must be darker so the light is on the unit, as on the vanilla cards.

Brightness measured on 34 vanilla DLC3 cards (0 = black, 255 = white; centre of the measurement at 55 % of the picture height):

- **Lit floor around the unit:** about 89.
- **Halfway to the edge:** about 55 to 64.
- **Edges:** about 47 to 55.
- **Corners and the top strip:** about 26 to 30. This is the darkest part.

The script darkens our screenshot until it has the same curve. The unit itself is not changed.

---

## 🖼️ The three card files

Each vanilla card is three images of **816 × 550** pixels. FA cards are made at twice this size (1632 × 1100) and use the same proportions.

- **`NAME-Portrait`** (opaque): the full picture, with background.
- **`NAME-Portrait_BASIC`** (transparent background): the unit only, cut out. On vanilla cards the unit fills about 11 to 27 % of the picture.
  - Made with background removal, then checked by eye.
  - Use image generation only to clean up a rough cutout edge. It must not change the unit.
- **`NAME-Portrait_HOVER`** (transparent edges): the full picture with soft oval edges that fade to transparent.
  - The oval is the same on all vanilla cards (within 45 of 255 levels), so a script copies it exactly.
  - Alpha: 0 at the border, about 115 at 15 % in, about 205 to 216 in the centre.

**Today:** `CardIcons.cs` points all three names of an FA card at one PNG. When we make real `_BASIC` and `_HOVER` files, `CardIcons.cs` must point each name at its own file.

---

## 📁 References

- **Vanilla cards used for the measurements:** `work/assetripper-20261107/export-dlc3-primary/Assets/Resources_moved/Images/UnitPortraits/DLC3` (35 units, from our earlier game export).
- **Comparison sheet** (full picture, `_BASIC` and `_HOVER` side by side): `work/hangar-indoor-1127/cards/vanilla-cards.jpg`, posted in the "blue dragons" thread.
- **Older card script** (Armory side shots, card shape only): `work/mk-card-art-1124/make.py`.
- **Hangar code:** `mod/source/runtime-qa/HangarIndoors.cs`.

---

## Document change log

- 2026-11-27 16:2x PST (America/Los_Angeles): First version, from Osama's instructions in the "blue dragons" thread (hangar, night, angle, edge darkening, image generation only for cutout edges) and measurements of 34 vanilla DLC3 cards.
