# ElmoClassicAddons

One source project for the locally maintained Elmo addon family. Interface and messages are English.

| Addon | Release | Clients |
| --- | --- | --- |
| ElmoLeveling | 1.6.4 | Classic Era 11509, Forever 16001 |
| ElmoPlater | 2.2.4 | Classic Era 11509, Forever 16001 |
| ElmoDungeonLoot | 2.2.0 | Classic Era 11509, Forever 16001 |
| ElmoSpellTracker | 1.0.2 | Classic Era 11509, Forever 16001 |

`ElmoLeveling/` is the single implementation shared by both clients. `Compat.lua` and `TalentBranches.lua` adapt available APIs; `scripts/build.py` generates the small `Client.lua` selector and each client manifest. All other runtime files are identical between the two packages. The other three addons also share their runtime across both clients. ElmoDungeonLoot packages separate Era and Forever loot/quest catalogues. Client restrictions are preserved: unavailable combat-log timing is not fabricated.

Build all packages from any clone with Python 3:

```sh
python3 scripts/build.py
```

The build reads addon versions from their TOC files. It uses only repository files and Python's standard library, creates staged addons in `.build/`, ZIPs in `dist/` and `.build-report.json`. These generated outputs are ignored by Git. Each ZIP contains one Elmo addon. All four addons have separate Classic and Forever packages from their shared implementations.

The build does not install addons or modify WoW/WTF files. Copy the desired package into the corresponding client's Interface/AddOns folder. Existing commands remain available, alongside `/elmoleveling` (`/elvl`), `/elmoplater` (`/eplater`), `/elmodungeonloot` (`/edl`) and `/elmospelltracker` (`/est`). Runtime compatibility with older saved profiles is retained; the completed one-time migration installer and its local configuration have been removed.

Tests use Python with `lupa.lua51`. Run the scripts in `scripts/tests/leveling_era`, `scripts/tests/leveling_forever`, `scripts/tests/ElmoPlater`, `scripts/tests/ElmoSpellTracker`, plus `scripts/tests/dungeon/test_journal.py` and `scripts/tests/test_migration.py`. `scripts/tests/test_forever.py` checks the staged packages, 630 Forever journal renders, modern quest APIs and restricted-value fallbacks. These are simulated client checks, not live game validation.

The canonical working repository is `tmp/elmo` in the Classic Era workspace. The previous `Projects/ElmoAddons` path is a compatibility symlink to this repository.

Repository layout: the four `Elmo*` addon folders are at the root. Build and maintenance tools, tests and legacy test fixtures live under `scripts/`. Generated `.build/`, `.build-report.json` and `dist/` remain ignored by Git.
