# ElmoLeveling 1.6.7

## Options menu

Open **Options > AddOns > ElmoLeveling** for visibility, position locking, kill-history expansion, centering, session reset and history clearing. Existing slash commands and tracker controls remain available.

An English leveling dashboard for **WoW Classic Era 1.15.9 (11509)** and **WoW Forever 1.60.1 (16001)**. Both packages use the same source files; the build generates only the client selector and manifest. API capability checks handle talents, tooltips, spells and protected combat data.

## Dashboard

- **XP/min (60s):** actual XP gained in the last 60 online seconds. Recent and
  Average XP/min displays refresh every 5 seconds; awards are recorded immediately.
- **XP/hr (60m):** actual XP gained in the last 3600 online seconds.
- **Average:** session XP divided by online elapsed time, converted to minute/hour.
- Session XP, current character name and level.
- **Combat / Total:** time in combat and all online time, in hours, minutes and seconds.
- **Bags (sell value):** native vendor price times item count in the backpack and four carried bags.
- A movable and lockable 332 x 195 pixel panel, expanding to 408 x 400.

Recent XP/min and XP/hr reset to zero at each new login. Their current windows
survive `/reload` and zone transitions. Session totals, averages, timers and
saved mob history are preserved.

Idle online time counts; offline time does not. Settings and counters are saved
per character. Both Combat and Total reset with Reset, including when already in
combat. Combat uses public player combat-state events and works independently
of Forever's restricted combat log. Existing Total time is preserved on upgrade;
Combat begins at zero because old combat time was not recorded. Missing item prices show a partial value and wait for loading
before reporting a complete value. Equipped items, bank contents, auction
prices and wallet gold are excluded from bag value.

## Mob history and Forever limitations

Click **Kills/min [+]** to expand the **100 most recent recorded kills**.
Columns are **Mob | Lvl | XP@lvl | Time | XP/s | Respawn avg**. For example, `75@7` means
75 XP received while your character was level 7. Scroll with the mouse wheel
or Up/Down. **Clear** removes the history without resetting XP or bag counters.

Forever restricts combat-log access and does not expose Classic's event reader.
The addon therefore records readable **mob XP chat messages**. Kills/min counts
those records over the last 60 online seconds. Zero-XP kills cannot be counted
through this source. A mob level is used only when public unit data can identify
it; unavailable or secret levels/identities stay **?**.

On Forever, **Time** and **XP/s** use an observed per-creature estimate, marked
with **~**. Timing starts when public unit data shows that the mob is fighting
you, your pet or a party member, and stops at its observed death. If the unit
disappears but its GUID is present in the XP notice, that notice closes the timer.
Looking at a mob does not start timing; changing targets does not reset it.
Evading and pulling again starts a new timer. Without an identifiable start or
an unambiguous XP-to-mob match, both fields remain **--**. New fights after
`/reload` can be measured; historical unknown times cannot be recovered.

Classic Era retains first-hit/miss-to-death combat-log timing. Protected values
are not decoded or reconstructed on either client.

## Equipment upgrades

A **purple border** marks currently usable estimated upgrades in native Forever
bags, including combined bags, and in the installed BetterBags Camelot edition.
Borders are mouse-transparent and do not alter item clicks or quality textures.
The meter can be hidden while borders continue to update.
Level and equipped item links are checked once a second, so delayed client
updates also invalidate the comparison and refresh existing borders.

The comparison uses relative class/role leveling weights and relevant weapon
DPS. Native group roles take precedence; otherwise current C_Traits ranks select
the dominant branch. Spell-to-branch facts are bundled; Talents Forever is not
required. Unknown changed spells are ignored instead of inheriting old node
ranks. Untalented characters use their class's solo leveling profile.

Rings/trinkets compare both slots and respect unique/category limits. A two-hand
replacement includes the lost offhand, and offhand weapons require trained Dual
Wield. Hunter melee and Feral weapons are scored as stat sticks. Missing equipped
item data waits for loading instead of becoming a zero-score baseline.

These are **leveling estimates**, retaining ClassicLeveling's relative weights,
not a simulation of Forever's class balance or a BiS ranking. Procs, on-use/set
bonuses, school-specific spell bonuses, resistances, stat caps, weapon speed and
ability rotations are not modeled. Supplemental flat tooltip bonuses support
English; native stats are read through C_Item. Gear is never equipped and talents
are never changed automatically.

## Commands

- `/elvl` or `/elmoleveling`: show/hide the dashboard.
- `/elvl show` / `/elvl hide`: set visibility.
- `/elvl lock` / `/elvl unlock`: control dragging.
- `/elvl center`: restore the default position.
- `/elvl reset`: reset XP, history, kill frequency and both session timers.
- `/elvl help`: show command help.


## Install and existing profiles

Use the package labelled **classic** for Classic Era and **forever** for Forever. Place the ElmoLeveling folder in the corresponding client's Interface/AddOns directory and restart the client.

The tracker uses **ElmoLevelingDB** per character. The public archive
contains only the ElmoLeveling addon folder.

Existing ElmoLeveling profiles are preserved. Former-addon importers are no longer included or loaded. The installer does not modify SavedVariables files.

## Validation

Automated checks execute the actual Lua files using Lua 5.1 and mocked APIs. They cover XP, bags, history, timing, equipment upgrades, current-profile preservation and both client API variants. Live-client behavior and appearance still require an in-game check.

The release packager
refuses a mismatch between both TOCs and the displayed addon version.
# ElmoLeveling


## Observed respawn average

**Respawn avg** is the mean time from a recorded kill to a newly observed living
mob with the **same name**. Mob level and individual identity do not group the
result: Boar at level 4 and Boar at level 8 contribute to the same average.
Each newly observed mob completes one waiting kill, oldest first. Repeated
sightings and mobs already observed alive before the kill add no samples.

The column refreshes every **5 seconds**. It shows **--** until the first sample,
then an estimate such as **135s** (seconds). Hover the row to
see the sample count. The current average is shared by all rows with that name;
**Time** remains the duration of that individual kill.

Observations come from targets, mouseover, visible nameplates and party targets.
This measures observed availability, so a mob outside observable units can be
seen later than its actual spawn. No server respawn schedule is assumed.

Averages are saved per character, for at most 100 names. Area changes and
reload/login discard unfinished waits, preserving measured averages. **Clear**
removes the mob list while averages continue; **Reset** also clears averages.

Respawn sampling uses public XP kill notices and readable living units. Protected
unit identities are skipped. It works independently of exact kill-time data,
which can remain unavailable in Forever.
