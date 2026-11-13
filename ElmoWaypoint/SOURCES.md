# Native API references

Reviewed for Forever 1.60.1 on 2026-11-13, using Blizzard's UI source through the
Gethe mirror, and compared with the installed Classic/Forever addon environment.

- [C_Map API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/MapDocumentation.lua):
  GetBestMapForUnit("player"), GetPlayerMapPosition, GetWorldPosFromMapPos and
  GetMapInfo. Coordinates are supplied by CreateVector2D and read with GetXY.
  GetMapWorldSize documents map dimensions in yards. No world-map selection or
  native user-waypoint state is changed.
  `/way current` stores the player's current normalized position without
  rounding. The live coordinates frame and arrow share the same sample per
  update, with finite map IDs and X/Y values validated before use. Missing or
  private data clears the displayed coordinates and prevents saving a point.
- [Native line drawing](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleLineAPIDocumentation.lua):
  six owned lines draw the arrow and outline using public, computed offsets.
  No custom bitmap, third-party arrow asset or protected-value drawing is used.
- [Native slash import](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameUtil.lua):
  ImportAllListsToHash processes prior registrations before the addon declares
  its SLASH_ELMOWAYPOINT aliases and SlashCmdList entry. Classic's
  ChatFrame_ImportAllListsToHash equivalent is accepted when present. No native
  handler, private hash table or TomTom handler is replaced.
- [Native slash dispatch](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameEditBox.lua):
  the next normal chat dispatch imports the new aliases. TomTom is an optional
  load-order dependency only; it is not required for navigation.

GetPlayerFacing supplies radians with north at zero and positive rotation
counterclockwise toward west. Native world position x is the north axis and y
the west axis. The installed TomTom/HereBeDragons and ForeverDungeonJournal
implementations were inspected to verify this convention. The arrow itself
uses the native conversion and the formula below; no TomTom code or assets are
included.

```text
dNorth = targetWorldX - playerWorldX
dWest  = targetWorldY - playerWorldY
distance = sqrt(dNorth^2 + dWest^2)
relativeAngle = normalize(atan2(dWest, dNorth) - GetPlayerFacing(), -pi, pi)
```

The source only performs this arithmetic on readable finite values. Opaque
positions/coordinates or facing produce a waiting status. World coordinates
from different continent IDs are never compared. The eight-yard arrival radius
and 50-waypoint limit are addon choices.

LibStub, CallbackHandler-1.0, LibDataBroker-1.1 and LibDBIcon-1.0 are copied
unmodified from the existing ElmoLFM bundle. See Libs/README.md and source headers.
The new addon code and documentation use the repository's MIT license.

## Map/minimap pins

[HereBeDragons 2.18](https://github.com/Nevcairiel/HereBeDragons/tree/2.18-release)
by Nevcairiel is bundled unmodified: HereBeDragons-2.0 revision 35 and
HereBeDragons-Pins-2.0 revision 17. Upstream declares BSD in its TOC. See
Libs/HereBeDragons/UPSTREAM.md for provenance and license metadata.

The addon registers its owned buttons through AddWorldMapIconMap and
AddMinimapIconMap, using its own reference for removal. HBD integrates with
Blizzard's MapCanvas data provider and handles zone/parent-map transforms,
minimap rotation, zoom, visibility and out-of-range edge placement. Each button
uses a native TempPortraitAlphaMask for its circular border and background.
GameTooltip:SetOwner(button, "ANCHOR_CURSOR") anchors the wrapped note next to
the mouse; no global tooltip hooks are installed.
