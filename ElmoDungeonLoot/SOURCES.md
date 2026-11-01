# ElmoDungeonLoot 2.2 data sources

This build targets **Classic Era 1.15.9 / Interface 11509**. Forever and Season of
Discovery loot, quests and APIs are not loaded. No external addon is required.

## Boss-specific loot associations

[AtlasLootClassic](https://github.com/Hoizame/AtlasLootClassic), revision
`8e99341e4e779328460bf7684c0d5b22ce50ddf1`,
`AtlasLootClassic_DungeonsAndRaids/data.lua`, SHA-256
`ab12de3f642620ff52e5bb0c47139e4146e3c7021be99d55af76e5eae7bda557`.

The Classic branch supplies the 26 dungeon/wing catalog and curated encounter loot.
All recorded item categories are retained, including recipes, companions and quest
items. Global key/book catalogs, vendors, quest rewards, raids and Scourge Invasion
tables are excluded. Shared trash loot is separate from encounter loot.
Encounter-specific means attributed to that encounter by the source; it does not
assert that an item can never be obtained elsewhere. Drop probabilities are not claimed.

## NPC levels, basic item stats and additional quest drops

[CMaNGOS ClassicDB](https://github.com/cmangos/classic-db), revision
`603ece109099ce44a5447a1b1cffd65c7272d71c`,
`Full_DB/ClassicDB_1_12_1_z2815.sql.gz`, SHA-256
`4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0`.

The journal extracts NPC level ranges, basic item metadata, primary attributes,
armor, resistances, shield block, weapon damage/speed, and item requirements.
Direct quest-only drops and quest starters supplement the curated boss tables.
Oggleflint, Bazzalan, the four remaining Stockade encounters, Lorgus Jett and
Roogug remain listed even when no equipment table exists. Native cached item and
tooltip data override bundled numbers. Unknown use/proc/set effects are labeled
for the native tooltip, never converted into invented numeric bonuses.

ClassicDB is a community 1.12 reference, not Blizzard's live server database.

## Dungeon quests, prerequisite graph and giver coordinates

[QuestieDB](https://github.com/Questie/QuestieDB), revision
`7901fee2753cecb577a72c2e4b7126198e05baec`:

- `data/Classic/classicQuestDB.lua`
- `data/Classic/classicNpcDB.lua`
- `data/Classic/classicObjectDB.lua`
- `data/Classic/classicItemDB.lua`
- `support/Zones/areaIdToUiMapId.lua`

Quest IDs are intersected with the ClassicDB quest catalog to exclude later/SoD
quests. Dungeon association uses recorded quest zones, objective NPCs/objects,
quest-item sources and in-dungeon starters. Ordinary crafting materials and
world-drop quest starters do not make an unrelated turn-in a dungeon quest.
Boss targets disambiguate wing-specific quests where the source allows it.
The complete transitive prerequisite graph is bundled, preserving AND/OR and
active-parent relations. All faction/race/class filtering is performed at runtime.
These are raw Classic source records; Questie runtime corrections are not executed.
Coordinates are map percentages; absent coordinates are explicitly marked missing.

`tmp/classicdungeon/questie-source/sources.json` records each pinned file's URL,
SHA-256 and size. The generator verifies these hashes before using the data.
English zone labels come from the locally installed Questie lookup table;
the native Era map API supplies names when available.

## Reproduction and verification

Run with a Python environment containing `lupa.lua51`:

```
python tools/classicdungeon/build_journal.py --output Interface/AddOns/ElmoDungeonLoot
python tools/classicdungeon/test_journal.py
```

The source cache is under `tmp/classicdungeon`. `build_catalog.py` preserves the
original 1.x source downloader and Classic AtlasLoot sandbox, reused by the new
generator. All tests use simulated client APIs; no live game state is changed.

The 2.1 search filters the same native/bundled numeric values rendered in the item
table. `tests_search.lua` adds name parsing, all numeric fields/operators, 150-condition
AND expressions, boundary values, cache behavior, malformed input and actual UI filtering.

The 2.2 categorical search uses native/static item class, subclass and inventory
type IDs. It does not infer an item's armor type or slot from its English name.
`GetItemInfoInstant` supplies type/slot/icon information when available before the
full native item cache loads. Tests cover material/slot alternatives, aliases,
robes, one/two-handed weapons, off-hand items, cold-cache metadata and actual rows.

## Forever API verification

Interface 16001 uses the shared runtime. Compared with the [Blizzard Forever UI/API source](https://github.com/Gethe/wow-ui-source/tree/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns), revision `ca8368f2f2380cbe696854f7f2646387c278a61b`: nameplate unit-frame health anchors and guarded hit-test methods, `C_Spell` cooldown/charge duration objects, aura readers, restricted combat-log detection and `C_QuestLog` readers. Capability checks and secret-value guards preserve client restrictions. Tests in `scripts/tests/test_forever.py` are offline simulations and do not certify live C++ rendering or native click overlap.

## Separate Forever catalogue

`CatalogForever.lua` and `QuestCatalogForever.lua` are compiled factual data, selected by `scripts/build.py` for the Forever package. They do not require the former ForeverDungeonLoot or route planner at runtime. The Era catalogue is never used as a fallback for Forever items.

Loot associations and bundled stats come from the local [ForeverChanges dungeon snapshot](https://foreverchanges.pro/dungeons), retrieved 2026-10-18, source build 1.60.1.70425, observations through 2026-10-03; SHA-256 `ab3d3342dbebd379151ead0d14380e30fa9a8da962461202cae14f275330793f`. The source is unofficial and includes data-mined/incomplete encounters. Quest membership, faction/class variants, chains and giver coordinates reuse the locally generated Forever preparation snapshot, based on [QuestieDB](https://github.com/Questie/QuestieDB) revision `e9a67d1a2753a0e64c4c96bf7864788fac7b765f` plus documented ForeverChanges/Hall of Thanes corrections. NPC level bounds come from that same pinned QuestieDB snapshot. Unavailable facts remain missing. `Catalog.meta` records both input hashes. Original static source data/derived factual associations are not a live guarantee of current server drops.

To regenerate explicitly: `python scripts/build_forever_catalog.py --loot /path/to/source_catalog.json --quests /path/to/Forever-preparation-Data.lua --database /path/to/pinned-QuestieDB`. This needs `lupa.lua51` and the pinned development inputs. Normal packaging uses only the committed catalogues and Python standard library. No upstream runtime code is included.
