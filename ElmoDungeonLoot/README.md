# ElmoDungeonLoot 2.2.0

A standalone **Classic Era and Forever** dungeon journal with a dark leather, bronze and gold
interface inspired by the installed TalentsClassic planner. All interface text is English.

Open with `/cdungeon`, `/classicdungeon` or `/cdl`. `/cdungeon reset` centers the window.
Restart the client after installing this major update so its new data modules load.
The title bar moves the window, its position and selected dungeon are saved per character,
and Escape closes it. The window scales down to fit the screen.

Choose a dungeon from the scrollable dropdown. The two panels scroll independently:

- **Boss loot:** encounter name and level, followed by every recorded specific drop.
  Item columns show name, required level, numeric stats, and whether your current
  character meets the requirements. Shared trash drops are clearly separated below
  the encounters. Recipes, pets and quest items are retained. A boss without a known
  exclusive drop table remains listed with an explicit message.
- **Dungeon quests:** quests for the character's faction, race and class, including
  quests not yet accepted. Each entry shows its giver (or starting item/object),
  zone and map-percentage coordinates, with current log/completion/prerequisite
  state. Click a chain to expand every transitive prerequisite and its giver.
  Alternative and cumulative prerequisites remain distinct.

Hover an item row for the native WoW item tooltip. Shift-click an item or quest to
insert its link into an open chat edit box. Quest tooltips include additional giver
locations and recorded profession requirements.

## Search item names, armor types, slots and numeric stats

The search bar filters loot in the selected dungeon as you type. Match an item name
(case-insensitive), armor types, slots, numeric stat conditions, or any combination. There is no
two-condition limit: **every condition must match** (AND). Separate conditions with
commas, spaces, `AND`, `;` or `&`. Use **Clear** to restore the complete loot table.
Groups with no matching drops are hidden while a filter is active. Quests are not filtered.

Examples:

```
gloves
cloth|leather
ring|trinket|neck
cloth|leather, head|chest, sta >= 5
type:mail, slot:shoulders, agi >= 5
agi >= 5
agi >= 5, sta >= 2, armor >= 40, req <= 25
boots, agility >= 5, stamina >= 2, quality >= 3
dps >= 12.3 AND speed <= 2.5
"Gold-flecked Gloves", int >= 3
```

Supported operators are `>`, `>=`, `<`, `<=`, `=`, `==`, `!=` and `~=`. Use a decimal
point. Percent-based stats use percentage points: `crit >= 1.5%` means at least
1.5 percent. Missing known stats count as zero. Unavailable cold-cache Equip bonuses
are excluded until live data can establish their value; results refresh as data loads.

The **?** tooltip lists all search fields. These include every displayed normalized
numeric stat (primary attributes, armor, resistances, AP, spell/healing bonuses,
hit/crit, defense, dodge/parry/block, regeneration and more), DPS, `speed`, `mindmg`,
`maxdmg`, required level (`req`), item level (`ilvl`) and quality (0 poor, 1 common,
2 uncommon, 3 rare, 4 epic, 5 legendary). Full primary names such as `agility` and
`stamina` work as aliases. Raw `ITEM_MOD_*` keys can query additional native numeric
stats. The parser treats text as data and never executes Lua expressions.
Invalid expressions produce an inline error. Numeric OR/NOT expressions are not supported.

Armor filters use item class/subclass IDs, not words in the item name: **cloth,
leather, mail, plate**. Slot filters use the native/static inventory type:
**head, neck, shoulder, back, chest, shirt, wrist, hands, waist, legs, feet,
ring, trinket, mainhand, offhand, ranged, relic, shield, twohand, bag, ammo, tabard**.
Aliases include `helm`, `shoulders`, `cloak`, `robe`, `bracers`, `gloves`, `belt`,
`pants`, `boots`, `finger`, `main_hand`, `off_hand` and `quiver`.

Use `|` to join categorical alternatives. For example, `cloth|leather, head|chest,
sta >= 5` means (cloth OR leather) AND (head OR chest) AND at least 5 stamina.
`cloth|ring|trinket` can include jewelry alongside cloth armor. The explicit forms
`type:cloth` / `type=cloth` and `slot:ring` / `slot=ring` are also accepted;
`armor:cloth` is equivalent to `type:cloth`. Numeric `armor >= 40` keeps its usual meaning.
Reserved category words can still be searched as literal names by quoting them,
for example `"ring"`. Pipe alternatives apply to types/slots, not numeric expressions.
There is no limit of two types, slots or stat conditions.

## Item and quest data

Basic numeric item stats and weapon damage/speed are bundled, so a cold client
cache does not leave the table empty. Cached native item data and tooltip values
take precedence, and the selected dungeon's item data is requested in small batches.
An unavailable native eligibility result is shown as **Check requirements**.
Use/proc/set effects are described from the live tooltip; before that arrives the
row explicitly says additional effects are available in the tooltip.

Quest availability can depend on events, reputation, professions, alternatives and
server state. The journal reports the requirements it can establish and otherwise
says **Check quest giver**, rather than promising that a quest can be accepted.
Missing source coordinates are labeled **coordinates not recorded**. Coordinates
for a patrolling NPC represent a recorded spawn, not a live position.
Some quests span multiple wings and may therefore appear in more than one guide.

The previous 1.x upgrade scoring, spec weights and equipped/bag comparisons have
been removed. No inventory scan, item movement, talent learning, automatic chat
message, or network connection is performed.

## Validation

`tools/classicdungeon/test_journal.py` runs the real addon in Lua 5.1 against explicit
simulated Era APIs. It covers cold/live stats, faction/class/race filters,
prerequisite graphs, coordinates, all-loot visibility, dropdown selection,
tooltips, links, row heights, scroll limits and request batching, including 468
class/faction/dungeon render combinations. These checks do not replace a live-client
visual and interaction check after `/reload`.

Pinned sources, source notices, factual-data limitations and reproduction commands
are in `SOURCES.md` and `ATTRIBUTION.md`.

## Elmo migration

Settings are imported from ClassicDungeon. Legacy settings import remains supported when previous data is available. Restart WoW after installing the new folder. Release version is unchanged.

## Client packages

Choose the `classic` package for Interface 11509 or `forever` for Interface 16001. Both are built from the same source project; the release version is unchanged. Install only the package for your client. Automated checks simulate the APIs; loading and rendering in the actual Forever client still need verification.

The Forever package bundles its own 35-dungeon catalogue, including Hall of Thanes, with 1,434 recorded drops and 636 quests including prerequisites. Era keeps its original 26-dungeon catalogue. Quest givers and chains use faction/class-specific Forever records and the modern quest log. Native item data/tooltip values replace bundled stats once loaded. The snapshot contains incomplete or datamined tables; an empty encounter is explicitly marked, and unknown minimum entry levels or coordinates are not invented. Snapshot provenance is in SOURCES.md.
