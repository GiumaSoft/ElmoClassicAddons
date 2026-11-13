# ElmoLeveling implementation references

The same Lua implementation serves Classic Era and Forever. `scripts/build.py`
selects interface 11509/16001 and writes the small client selector. ElmoLevelingDB
is per-character; installation never edits SavedVariables files.

## Session and time per level

Actual XP comes from public UnitXP, UnitXPMax and UnitLevel snapshots plus
PLAYER_XP_UPDATE and PLAYER_LEVEL_UP. Elapsed time uses GetTime and saved online
seconds, including idle time. Multiple unobserved level transitions remain
unknown; no award, rate or historical level duration is invented.

RequestTimePlayed and TIME_PLAYED_MSG can recover the current level's played
time. Earlier completed levels cannot be recovered this way. The request uses
the native API without replacing chat handlers. See Blizzard's
[native /played handling](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/SlashCommands.lua).

## Sigillo UI

The refined layout displays the session clock in the header and one remaining-XP
caption below the subzone. Remaining XP uses the current readable UnitXPMax
minus UnitXP and is independent of the saved session XP accumulator. Restart
does not change it. The header clock uses the native measured string width to
fit long durations; the subzone uses a 14-point font, the remaining-XP caption
15 points and the seal percentage 13 points. Details retains
the same width while expanding below the 218-pixel compact panel.

GetRealZoneText/GetZoneText supply the zone. GetSubZoneText supplies the subzone,
with GetMinimapZoneText as a fallback when it is blank or repeats the zone.
Only public, trimmed, distinct names are shown; otherwise the line stays empty.
Zone-change events refresh it, with a one-second update
as a fallback. A previous subzone is never retained after leaving it.

[GetXPExhaustion](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/PlayerScriptDocumentation.lua)
supplies the remaining rested-XP pool. Its ratio to UnitXPMax is displayed as a
percentage of a level, not a bonus rate. A successful nil return means no pool;
an unavailable, failed or private return remains unknown. UPDATE_EXHAUSTION and
PLAYER_UPDATE_RESTING refresh the display. The preview clips at the end of the
current level while the numeric pool can exceed 100%.

[C_Container.GetContainerNumFreeSlots](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/ContainerDocumentation.lua)
returns free slots and bag family. Only readable, valid counts in general bags
(family zero) are added across backpack and carried bags 0–4. Ammo, herb and
other specialized bags are excluded from ordinary loot-space totals. Missing
data displays an unknown count rather than a partial total. Existing vendor
value scanning still includes all carried items and pending prices.

The seal uses an original 256×256 antialiased annulus texture. When the client
provides [SetRadialProgressBarPercent](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleTextureBaseAPIDocumentation.lua),
the renderer clips one whole texture for each earned/rested arc. There are no
quadrant joins, cooldown clocks or animation timers in that path. Capability
detection, rather than the client name, selects it.

Older clients use four cropped quadrants for each earned/rested arc. A
half-plane texture mask reveals the partially filled quadrant; completed
quadrants have no mask. These owned
[texture masks](https://github.com/Gethe/wow-ui-source/blob/classic_era/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleTextureAPIDocumentation.lua)
are supported on both clients. Texture pixel-grid snapping and texel sharpening
are disabled for every seal texture and mask, as in the installed TomTom and
Questie renderers and [WeakAuras' circular progress textures](https://github.com/WeakAuras/WeakAuras2/blob/main/WeakAuras/BaseRegions/CircularProgressTexture.lua).
This preserves linear filtering and fractional positions at arbitrary UI scales.
Arc visibility and clipping update only when public XP/rested fractions change.
The crown still uses native lines.
Private values never enter arithmetic or texture coordinates. The panel does
not observe targets, nameplates, combat logs or other players.

Media/Panel.tga is an original 64×64 RGBA rounded nine-slice atlas. Reproduce it
with `python3 scripts/leveling_panel.py` from the repository root. UI.lua retains
its ten-pixel corners when Details expands. Reproduce Media/Ring.tga and
Media/RingMask.tga with `python3 scripts/leveling_ring.py`. The annulus has a
one-display-pixel alpha falloff at its 76-pixel UI size. Body and title fonts
come from the game; no third-party font or image is bundled.

Media/Moon.tga and Media/Backpack.tga are original 64×64 alpha line icons,
displayed at 14 pixels next to the rested and free-slot labels. Reproduce them
with `python3 scripts/leveling_icons.py`. The backpack follows the low-space
label's gold warning color. These icons are decorative and do not intercept
mouse input.

## Vendor sales

The separate A.Sales observer in Bags.lua observes MERCHANT_SHOW, MERCHANT_UPDATE, MERCHANT_CLOSED and
PLAYER_MONEY. Like Blizzard's [merchant UI](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_UIPanels_Game/Vanilla/MerchantFrame.lua),
it reads GetNumBuybackItems, GetBuybackItemInfo and GetBuybackItemLink. Buyback
price is already the total for the stack and is added once, without multiplying
by quantity again. Retained rows are matched in order across updates to avoid
counting old stock, repeated events and buybacks as new sales.

Read-only secure post-hooks observe UseContainerItem, SellCursorItem,
PickupContainerItem and SellAllJunkItems when present. They never replace or
invoke those native actions. A sale request is not income by itself. Cached
public bag quantities/prices and GetMoney corroborate actual removed items and
received money when identical/full buyback lists or bulk sales lose receipt
rows. Money and bag responses can arrive in either order. Gross visible
receipts remain independent of unrelated wallet gains, purchases and repairs.
Requests expire after ten seconds; uncertain amounts remain uncounted and a
readable-data gap marks the counter as a lower bound. This is observation,
not merchant automation, and has not yet been validated against live server
transaction ordering.

ElmoLevelingDB.vendorSales is the persistent nonnegative copper total for the
current session. Restart resets it; wallet totals are never used as this
counter. Sales made before tracking started are not inferred from a balance.

## Equipment upgrades and verification

UPGRADE_RULES.md describes the unchanged class/role formulas in Upgrades.lua.
Native bags and BetterBags hooks remain independent of tracker visibility.
Price times stack quantity determines carried vendor value; unavailable item
data stays pending until the public item cache supplies it.

Lua 5.1 fixtures in scripts/tests/leveling_era and leveling_forever execute the
actual code. They cover sessions, rollover, idle time, logout/reload, level
history, class profiles, bag comparisons, Sigillo data updates, unknown/private
values, rested pools, specialized bags and expansion controls. Simulated APIs
do not establish live-client rendering or permissions.
