# ElmoClassicAddons

One source project for the locally maintained Elmo addon family. Interface and messages are English.

| Addon | Release | Clients |
| --- | --- | --- |
| ElmoLeveling | 1.6.6 | Classic Era 11509, Forever 16001 |
| ElmoPlater | 2.3.1 | Classic Era 11509, Forever 16001 |
| ElmoSpellTracker | 1.0.3 | Classic Era 11509, Forever 16001 |
| ElmoQuestEnhanced | 1.2.0 | Classic Era 11509, Forever 16001 |
| ElmoLFG | 1.4.1 | Classic Era 11509, Forever 16001 |
| ElmoRare | 1.0.0 | Classic Era 11509, Forever 16001 |
| ElmoBuff | 1.0.1 | Classic Era 11509, Forever 16001 |

`ElmoLeveling/` is the single implementation shared by both clients. `Compat.lua` and `TalentBranches.lua` adapt available APIs; `scripts/build.py` generates the small `Client.lua` selector and each client manifest. All other runtime files are identical between the two packages. The other addons also share their runtime across both clients. ElmoQuestEnhanced has an Options > AddOns panel for quest completions, multi-objective completions and optional kill/item progress reports to the current group. Client restrictions are preserved: unavailable combat-log timing is not fabricated.

Build all packages from any clone with Python 3:

```sh
python3 scripts/build.py
```

The build reads addon versions from their TOC files. It uses only repository files and Python's standard library, creates staged addons in `.build/`, ZIPs in `dist/` and `.build-report.json`. These generated outputs are ignored by Git. Each ZIP contains one active Elmo addon. ElmoLFG ships only its current addon folder and uses `ElmoLFGDB`; the old settings importers have been retired. ElmoQuestEnhanced includes an inactive `ElmoQuestReport` compatibility folder to prevent duplicate reports after its rename. All addons have separate Classic and Forever packages from their shared implementations.

The build does not install addons or modify WoW/WTF files. Copy the desired package into the corresponding client's Interface/AddOns folder. Existing commands remain available, alongside `/elmoleveling` (`/elvl`), `/elmoplater` (`/eplater`) and `/elmospelltracker` (`/est`). Runtime compatibility with older saved profiles is retained; the completed one-time migration installer and its local configuration have been removed.

Tests use Python with `lupa.lua51`. Run the scripts in `scripts/tests/leveling_era`, `scripts/tests/leveling_forever`, `scripts/tests/ElmoPlater`, `scripts/tests/ElmoSpellTracker`, plus `scripts/tests/test_migration.py`. `scripts/tests/test_forever.py` checks the staged packages and restricted-value fallbacks. These are simulated client checks, not live game validation.

The canonical working repository is `tmp/elmo` in the Classic Era workspace. The previous `Projects/ElmoAddons` path is a compatibility symlink to this repository.

ElmoLFG replaces ClassicQuestLFG. Open it with `/elmolfg` or `/elfg`; all previous
quest-LFG commands remain aliases. It shares quest reading, UI and recruitment
code between clients. Its tests are in `scripts/tests/ElmoLFG`.

Repository layout: the `Elmo*` addon folders are at the root. Build and maintenance tools, tests and legacy test fixtures live under `scripts/`. Generated `.build/`, `.build-report.json` and `dist/` remain ignored by Git.

All seven addons are accessible from **Options > AddOns** under their Elmo names. Basic switches are available directly; spell bar settings and the LFG window open from their corresponding pages. Existing commands and saved preferences are preserved.

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

ElmoPlater retains fixed 2x health bars, personal debuffs and native quest
kill markers. Priority rules/editors, engagement tracking and custom cross-plate
layer ordering have been removed from the shared runtime. `/eplater` opens its
native options page.
