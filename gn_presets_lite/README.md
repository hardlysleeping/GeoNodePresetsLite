# GN Presets Lite

A read-only companion to GN Presets. It lets someone open a `.blend` file, an appended
node group, or a linked asset that contains Geometry Nodes presets and **switch between
those presets** — without being able to change, rename, reorder, delete, or add to them.

Presets are read from the node group itself, so a Lite user sees exactly the presets the
author saved: the same names, the same order, the same values. Nothing is imported,
downloaded, or kept in a separate file.

Requires **Blender 5.2 or newer**.

## Why it exists

Presets live on the node group. If you share a procedural asset, sending the whole
add-on with it is overkill for someone who only wants to try the looks you built.
Ship the asset, point people at Lite, and they get the preset dropdown and Recall —
nothing that can damage the library you published.

## What it does

| Control | Behaviour |
| --- | --- |
| **Preset** dropdown | Lists every preset stored on that node group, in the author's order, each marked *Saved* or *Empty (keep current values)*. |
| **Saved preset** | Selecting it applies its stored input values to this modifier straight away. |
| **Empty preset** | Selecting it leaves the current values alone — there is nothing to restore. |
| **Recall** (↺) | Reapplies the selected preset, discarding unsaved edits to the live inputs. Dimmed when the preset already matches. |
| **Position readout** (`2/4`) | Where the selected preset sits in the author's list. |

The same controls appear in the **Geometry Nodes modifier panel** and in the **3D Viewport
sidebar**, under a *GN Presets Lite* tab.

## What it deliberately does not do

There is no Save, New Preset, Rename, Delete, Reorder, auto-save or Clear All. Those
actions are not hidden or disabled in the interface — they are absent from the add-on, so
nothing in Lite can write to a preset library.

Presets are stored on the node group, which means:

- two modifiers using the same node group share one preset list, but each keeps its own
  selected preset;
- a linked node group's presets are fully readable and recallable here;
- the node group's own defaults are never modified by recalling a preset.

## Install

**From a ZIP:** **Edit → Preferences → Get Extensions → dropdown → Install from Disk**, pick
`GN-Presets-Lite-1.0.0.zip`, then enable **GN Presets Lite**.

**With updates:** in **Edit → Preferences → Extensions → Repositories → Manage Repositories**, add
`https://hardlysleeping.github.io/GeoNodePresetsLite/index.json` as a repository, then install
**GN Presets Lite** from it. Blender checks that index for new versions and installs them with its
**Update** button.

Lite can be installed next to the full GN Presets add-on; it reuses the library the full
version writes instead of defining a second one.

## Sharing presets with someone else

1. The author saves presets with the full **GN Presets** add-on, in the node group that
   ships with the asset.
2. The asset is shared as a `.blend`, an appended node group, or a linked asset library.
3. The recipient installs **GN Presets Lite** and opens the asset: the preset dropdown is
   populated and every preset can be recalled.
4. Editing the list itself needs the full add-on:
   [github.com/hardlysleeping/GeoNodePresets](https://github.com/hardlysleeping/GeoNodePresets).

## Animation presets

If a shared preset carries keyframed input values, the **Animation Presets** switch in the
Lite preferences controls whether those curves are recalled too. With it off, presets
recall plain values and animated inputs keep one animation in every preset. Either way,
stored animation is never deleted by recalling a preset.

## Notes

- Unsupported input types (rotation, matrix, …) are skipped rather than approximated; the
  recall result reports what was skipped.
- Driven inputs are never overwritten: the driver keeps that input the same in every
  preset.
- Presets saved against an older interface still recall every input that still exists.

## Licence

GPL-3.0-or-later. See [LICENSE](LICENSE).