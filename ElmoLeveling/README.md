# ElmoLeveling 2.2.0

The **Sigillo** leveling tracker for **Classic Era 1.15.9** and **WoW Forever
1.60.1**: a compact aristocratic layout, live location and level progress,
elapsed time, XP remaining, bag vendor value, session vendor sales, expandable level history, and purple equipment
upgrade borders. The English UI keeps Elmo's dark, bronze, gold and violet theme.

## Sigillo layout

The 368 × 218 tracker shows:

- An antialiased circular level seal, with earned XP in violet and a muted rested-XP preview.
- Current zone and subzone, with XP remaining shown once below it in a larger 15-point font.
- A compact gold session clock in the header, beside the addon name.
- Two separate gold counters: **In bags** and **Sold · session**.
- A moon icon and rested XP as a percentage of the current level's XP requirement.
- A backpack icon and free slots in general-purpose carried bags. Specialized bags are excluded.

Hover the seal for progress information or the location for its full name.
If the subzone name is empty or repeats the zone, the tracker tries the minimap
name. If neither supplies a distinct location, the subzone line stays empty
without retaining an earlier location.
At the level cap the seal shows **MAX**. Missing/private XP, location, rested or
bag-space data shows an unavailable state; previously displayed percentages are
not reused. The rested pool can exceed one level, while its preview arc stops
at the end of the current level. It is not a bonus-rate percentage.

**Details** opens the vertical level history and carried-item counts below the seal,
keeping the panel width and top edge. Four level entries are visible per page;
scroll or use Up/Down to reach the rest. Lock/Unlock and Restart are in Details.
The **...** menu opens **Options > AddOns > ElmoLeveling**. Drag the header when
unlocked to move the tracker; the saved position is retained across reload/login.

## Session clock and XP remaining

The header shows elapsed time, for example:

```text
Time 02:01:38
```

Below the subzone, the violet count is the XP required for the next level,
for example **44,546 XP to level 43**. It is calculated from the current player
bar (`UnitXPMax - UnitXP`); it is not a session total or a rate. There is no
second XP counter or central statistics row. The larger subzone font and
single remaining-XP line keep the location readable.

After 24 hours the clock includes days, for example `1d 03:12:09`. There are no
hourly/day counters or projections. **Restart**, `/elvl start` or `/elvl reset`
restarts the session timer. All online time counts, including idle, travel, city, AFK and
out-of-combat time. Offline time does not count. The session resumes after
reload/login and is not reset by changing zones or crossing an hour/day boundary.

Restart does not change XP remaining or level history. Kills, quests and other
awards reduce the remaining count as the player's XP bar changes; after a level
up, the new level's requirement is displayed. If current XP is unavailable,
the line says **XP unavailable**. Missing historical awards do not prevent a
readable current-level remaining count. Existing saved profiles are preserved.

## Gold counters

**In bags** is the vendor sell value of the items currently in the backpack and
four carried bags: unit sell price multiplied by stack quantity, for all item
qualities. Wallet gold, equipped gear, bank contents and auction prices are
excluded. Items already present when the session starts are included. Missing
prices display `>=` until the item cache supplies them.

**Sold · session** records gross vendor proceeds from sales of any item quality,
including items acquired before this session. It is not the wallet balance or
its net change: looted coins, quest rewards, purchases and repairs do not count.
Buying an item back does not subtract its earlier sale; selling it again is a
new sale. Failed sale attempts are not income.

Selling an item reduces **In bags** and increases **Sold · session**. The addon
only observes transactions; it never sells, buys, repairs or moves items.
Recorded sales persist across reload/login with the existing session. **Restart**,
`/elvl start` and `/elvl reset` clear the sales counter together with session
time/XP, preserving level history. Sales before this feature began tracking
cannot be reconstructed.

The tracker matches native buyback receipts and reconciles observed sale
requests, bag removals and money updates when a full buyback list would hide
identical or bulk sales. If readable evidence is missing, it omits unconfirmed
amounts and shows `>=` for the recorded lower bound. Tooltips explain both
counters. Amounts retain gold, silver and copper precision.

## Time per level

Click **Details** to expand the current level and up to 100 recorded completed
level transitions. Times use **days, hours, minutes and seconds**, for example
`1d 03h 12m 09s`. Scroll with the mouse wheel or Up/Down.

- **In progress:** the current level's known online time, including idle time.
- **Complete:** the full observed online time from one level to the next.
- **Partial:** tracking began during that level and its earlier time is unknown.
- **Unavailable:** several unobserved levels cannot be timed separately.

The addon requests Blizzard's native played-time data once when entering the
world after login/reload. A readable reply supplies the current level's full
online time, including time played before installation. No chat handler is
replaced. If the API is unavailable or restricted, local timing continues and
its first interval is marked Partial. Past completed level times cannot be
recovered from the current played-time reply.

Level timing and history persist across reload/login, exclude offline time,
and remain independent of **Restart**. **Options > AddOns > ElmoLeveling >
Clear completed level history** clears completed rows without restarting the
current level or XP measurements. At the level cap, the current row shows
**Max level**; recorded prior transitions remain available.

## Equipment upgrades

The **purple border** remains active in native bags (including combined bags)
and the installed BetterBags edition, even when the dashboard is hidden.
It compares currently usable items against equipped replacements using relative
class/role leveling weights. Gear is never equipped automatically.

The complete, unchanged rules are in [Equipment upgrade formulas](UPGRADE_RULES.md):

- The exact weighted score and strict improvement threshold.
- Class, specialization, no-talent defaults and group-role precedence.
- Every primary, secondary, spell, healing, armor and weapon-DPS weight.
- Rings/trinkets, two-hand/off-hand costs, Dual Wield and unique limits.
- Data-loading behavior, examples and what the model does not evaluate.

These are estimates, not damage/healing simulations or best-in-slot rankings.
UPGRADE_RULES.md is included in both client packages and defines the comparisons
used by the purple borders.

Bag vendor value is always visible in the compact panel; Details retains the
carried-item stack and quantity summary.

## Controls and installation

Open `/elvl` or `/elmoleveling` to show/hide the dashboard. `/elvl show`, `hide`,
`lock`, `unlock` and `center` remain available. `/elvl details` toggles Details;
`/elvl options` opens native settings. `/elvl start` and `reset` restart
the session. Visibility, dragging lock, level-history expansion, centering,
restart and history clearing are accessible from **Options > AddOns > ElmoLeveling**.

Use the package labelled **classic** for Classic Era and **forever** for Forever.
Extract its ElmoLeveling folder into the client's `Interface/AddOns` directory.
After replacing an existing installation, `/reload` loads the new version.

Both client packages share the same source. Preferences and current tracking
are saved per character in **ElmoLevelingDB**. Existing visibility, position,
locking and bag baseline are preserved. Retired mob/respawn samples are removed
from this addon's saved data when it loads; other addons' data is untouched.

## Native API references and validation

XP uses public UnitXP, UnitXPMax, UnitLevel, PLAYER_XP_UPDATE and PLAYER_LEVEL_UP.
Level timing observes [TIME_PLAYED_MSG](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SystemDocumentation.lua)
and requests the same [RequestTimePlayed API used by /played](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/SlashCommands.lua).
No combat-log, mob-XP chat, target, mouseover or nameplate observation is used.

Automated Lua 5.1 checks execute the actual addon with explicit native-API
fixtures. They cover long sessions, idle time, reload/logout, XP rollover,
level timing, current profiles, item comparisons and both client variants.
Live server permissions and rendering still require an in-game check.

Source: https://github.com/GiumaSoft/ElmoClassicAddons
