# ElmoRare 1.0.0

Classic Era / Forever rare alerts, using native public data. No Questie or rare
database is required. This addon does not share sightings over chat/networks.

## Detection

An alive, non-player-controlled creature classified by WoW as `rare` or
`rareelite` produces a local chat notice, optional raid-warning sound and a
12-second alert. Hover the alert for its name, level, classification, source and
NPC ID when available. Drag to move it; right-click to dismiss it.

Nearby detection uses `NAME_PLATE_UNIT_ADDED` and the native nameplate unit
tokens. Enable enemy nameplates outside combat. Target and mouseover detection
also work. A half-second scan retries delayed data and handles recycled tokens.
WoW controls which units and range are available; this is not a complete radar
for all rares in the zone, and it does not scan unexposed creatures or cache
entries. Private identity/classification/death/control data is skipped safely.
No HP, aura or combat-log data is read.

Each creature GUID alerts once while observed. The same GUID can alert again
after five minutes without observation; a different spawn GUID alerts separately.
The session cache is bounded to 256 rare GUIDs. Sightings are not persisted.

## Options and preview

Open **Options > AddOns > ElmoRare** or `/erare` (`/elmorare`). Detection, sound,
popup/tooltip and alert position settings are saved per character.

- `/erare test`: preview the popup and enabled sound; it creates no real sighting.
- `/erare on` / `/erare off`: enable or disable detection.
- `/erare last`: display the last sighting again.
- `/erare status`: report detection, tracked nameplates and secure-key availability.

The preview can be used without a rare nearby. It never targets or marks a mob.
Audio respects WoW's sound settings; the addon does not change volume/CVars.

## Optional skull key

In **Options > Key Bindings**, search **ElmoRare** and assign
**ElmoRare: Skull on current target**. The binding is unassigned by default.
Select the rare yourself, then press that key. It marks the current target, so
check your target before pressing it. Normal group permissions still apply.

The key invokes Blizzard's `SecureActionButtonTemplate` `raidtarget` action,
configured once with `unit=target`, `marker=8`, `action=set`. Addon Lua never
calls `SetRaidTarget`, `TargetUnit`, a secure action handler or `:Click()`.
The standalone secure button is not parented to the dynamic popup and is never
rebound to detected nameplate tokens. If first loaded during combat, button
creation waits until combat ends. Client support and actual marker behavior
must be validated in game; simulated APIs do not prove secure execution.
`Bindings.xml` is loaded implicitly by WoW and is not listed in the TOC.

## Sources

API/source verification against Forever build **1.60.1.70862**:

- [UnitClassification and identity APIs](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua)
- [Native nameplate API](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/NamePlateDocumentation.lua)
- [Blizzard secure raidtarget action](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua#L582)

Tests: `scripts/tests/ElmoRare/test_addon.py`, using Lua 5.1 with explicit simulated
APIs. Live rare detection, range, sound and hardware-driven marking require an
in-game test. Other rare-alert addons may independently sound their own alerts.
