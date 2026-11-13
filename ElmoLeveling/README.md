# ElmoLeveling 2.0.0

Actual XP earned over one hour and 24 hours, time per level, and purple equipment
upgrade borders for **Classic Era 1.15.9** and **WoW Forever 1.60.1**.
The English dashboard keeps the dark and bronze Elmo style.

## Actual XP periods

The first measurement starts when the addon first runs. **Restart**, `/elvl start`
or `/elvl reset` begins both periods again from zero. They are fixed one-hour
and 24-hour periods from that start, using online time. All idle, travel, city,
AFK and out-of-combat time counts; offline time does not. Reloading, logging out
or changing zones does not reset a measurement.

Each period adds only XP actually awarded to the player's XP bar, including
kills, quests, exploration and rested bonuses. There is no average, median,
per-minute conversion or extrapolation to a full hour/day.

```text
periodXP = sum(actual player XP awards recorded within that online period)
periodElapsed = online seconds since that period started
```

Before the first hour or day completes, its large number shows actual XP earned
so far and is labelled **first 1h** / **first 24h**, **In progress**. When a period
completes, the large number retains its actual completed total, labelled
**last full 1h** / **last full 24h**. The line below shows the next period's actual
XP and elapsed time. Periods continue through idle time; an entirely idle
completed period correctly records zero XP. An award exactly at a boundary
belongs to the new period. Only the most recent completed total is retained.

Existing pre-2.0 session totals are not invented as new hour/day measurements.
If several levels are skipped between readable XP snapshots, the intervening
XP requirements cannot be reconstructed safely: the totals show **--** and
request a fresh start rather than publish an estimated award.

## Time per level

Click **Levels [+]** to expand the current level and up to 100 recorded completed
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
The same full formulas are included in the CurseForge project description and
the release commit message.

**Bags (sell value)** continues to show vendor price times quantity in the
backpack and four carried bags. Missing prices stay pending until loaded.
Equipment, bank contents, auction prices and wallet gold are excluded.

## Controls and installation

Open `/elvl` or `/elmoleveling` to show/hide the dashboard. `/elvl show`, `hide`,
`lock`, `unlock` and `center` remain available. `/elvl start` and `reset` restart
the XP periods. Visibility, dragging lock, level-history expansion, centering,
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
fixtures. They cover period boundaries, idle time, reload/logout, XP rollover,
level timing, current profiles, item comparisons and both client variants.
Live server permissions and rendering still require an in-game check.

Source: https://github.com/GiumaSoft/ElmoClassicAddons
