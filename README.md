# ElmoClassicAddons

One source project for the locally maintained Elmo addon family. Interface and messages are English.

| Addon | Release | Clients |
| --- | --- | --- |
| ElmoLeveling | 2.2.0 | Classic Era 11509, Forever 16001 |
| ElmoPlater | 2.4.1 | Classic Era 11509, Forever 16001 |
| ElmoSpellTracker | 1.0.4 | Classic Era 11509, Forever 16001 |
| ElmoQuestEnhanced | 1.2.1 | Classic Era 11509, Forever 16001 |
| ElmoLFG | 1.4.4 | Classic Era 11509, Forever 16001 |
| ElmoLFM | 1.0.8 | Classic Era 11509, Forever 16001 |
| ElmoRare | 1.0.0 | Classic Era 11509, Forever 16001 |
| ElmoBuff | 1.0.2 | Classic Era 11509, Forever 16001 |
| ElmoWaypoint | 1.2.0 | Classic Era 11509, Forever 16001 |

`ElmoLeveling/` is the single implementation shared by both clients. `Compat.lua` and `TalentBranches.lua` adapt available APIs; `scripts/build.py` generates the small `Client.lua` selector and each client manifest. All other runtime files are identical between the two packages. The other addons also share their runtime across both clients. ElmoQuestEnhanced has an Options > AddOns panel for quest completions, multi-objective completions and optional kill/item progress reports to the current group. Client restrictions are preserved: unavailable combat-log timing is not fabricated.

Build all packages from any clone with Python 3:

```sh
python3 scripts/build.py
```

The build reads addon versions from their TOC files. It uses only repository files and Python's standard library, creates staged addons in `.build/`, ZIPs in `dist/` and `.build-report.json`. These generated outputs are ignored by Git. Each ZIP contains one active Elmo addon. ElmoLFG ships only its current addon folder and uses `ElmoLFGDB`; the old settings importers have been retired. All addons have separate Classic and Forever packages from their shared implementations.

The build does not install addons or modify WoW/WTF files. Copy the desired package into the corresponding client's Interface/AddOns folder. Existing commands remain available, alongside `/elmoleveling` (`/elvl`), `/elmoplater` (`/eplater`) and `/elmospelltracker` (`/est`). Current Elmo profiles are retained; former-addon importers and command aliases have been retired.

Tests use Python with `lupa.lua51`. Run the scripts in `scripts/tests/leveling_era`, `scripts/tests/leveling_forever`, `scripts/tests/ElmoPlater`, `scripts/tests/ElmoSpellTracker`, plus `scripts/tests/test_profiles.py`. `scripts/tests/test_forever.py` checks the staged packages and restricted-value fallbacks. These are simulated client checks, not live game validation.

The canonical working repository is `tmp/elmo` in the Classic Era workspace. The previous `Projects/ElmoAddons` path is a compatibility symlink to this repository.

ElmoLFG replaces ClassicQuestLFG. Open it with `/elmolfg` or `/elfg`; the window and minimap button share the same settings. It shares quest reading, UI and recruitment
code between clients. Its tests are in `scripts/tests/ElmoLFG`.

Repository layout: the `Elmo*` addon folders are at the root. Build and maintenance tools and tests live under `scripts/`. Generated `.build/`, `.build-report.json` and `dist/` remain ignored by Git.

All nine addons are accessible from **Options > AddOns** under their Elmo names. Basic switches are available directly; spell bar settings and the LFG window open from their corresponding pages. Current Elmo commands and saved preferences are preserved.

ElmoRare uses native nameplate, target and mouseover units for rare/rare-elite
alerts, with sound and a hover tooltip. `/erare` opens its options and `/erare test`
previews the alert. Its optional skull key uses Blizzard's secure raidtarget
action on the current target after a user key press. Detection coverage depends
on the units WoW exposes. See `ElmoRare/README.md`; Lua 5.1 simulated checks are in
`scripts/tests/ElmoRare/test_addon.py`.

ElmoBuff shows missing or expiring buff icons beside the native player/party
frames. Click an icon to buff that member; it disappears after the aura is
confirmed. Rebuffs are available outside combat. `/ebuff` opens its native
options. See `ElmoBuff/README.md`; Lua 5.1 simulated checks are in
`scripts/tests/ElmoBuff/test_addon.py`.

ElmoPlater retains fixed 2x health bars, adds optional mana and casting bars,
and shows personal debuffs and native quest
kill markers. Priority rules/editors, engagement tracking and custom cross-plate
layer ordering have been removed from the shared runtime. `/eplater` opens its
native options page.

ElmoLFM searches native WHO results by zone and level range, whispers selected
players once and optionally invites contacted players who reply inv. Open
`/elfm` or Options > AddOns > ElmoLFM. No public announcements are sent.
Right-clicking a player row requests a direct group invitation.
Its independent Lua 5.1 checks are in `scripts/tests/ElmoLFM/test_addon.py`.

ElmoLeveling 2.2.0 uses the Sigillo layout: a circular level/XP seal, current zone,
rested XP and general-purpose free bag space. A header clock shows elapsed online
time; remaining XP appears once below the subzone in a 15-point caption. The
antialiased seal uses generated artwork and the native radial renderer when
available, with unsharpened masked textures on older clients. Moon and backpack
icons accompany rested XP and free slots. Separate In bags and Sold · session
counters show carried vendor value and gross recorded vendor-sale income. The subzone
falls back to the minimap name when available. Time per level
is recorded in an expandable history. Idle time
counts. Mob XP records, kill timing and respawn sampling are removed. Purple
equipment upgrade borders retain their rules; class/specialization mappings,
weights and comparison formulas are in `ElmoLeveling/UPGRADE_RULES.md`.

ElmoWaypoint adds `/way x y [note]`, circular map/minimap pins with note tooltips,
a movable directional arrow, a live coordinate frame and a minimap launcher.
`/way current [note]` saves the character's exact current position. Right-click
the launcher for native options and Reset all waypoints.
Points and preferences are saved per character. `/ewp` is an unambiguous alias;
TomTom retains its alternative commands. See `ElmoWaypoint/README.md` and
`scripts/tests/ElmoWaypoint/test_addon.py`.
