# ElmoPlater 2.3.1

Classic Era / Forever nameplates with solid reaction colours, contrasting
borders, health percentage, difficulty-coloured levels and your harmful debuffs.
Claimed mobs are grey and marked `[CLAIMED]`. Native positioning, overlap and
click ordering remain owned by WoW.

## WoW Forever API restrictions

On WoW Forever, Blizzard protects enemy health values during combat. ElmoPlater
can still display health bars and percentages through Blizzard-supported display
APIs, but addon code cannot inspect or compare those protected values to rank
mobs by health. For this reason, the rule system, custom target-priority ordering
and experimental health-based layers have been removed. Nameplates, health
percentages, personal debuffs and quest-kill markers remain available. This
simplification applies to both clients because they share the same codebase.

## Changes in 2.3.0

Removed the priority rule engine, rule/condition editors, spell readiness checks,
observed-debuff catalogue, engagement tracking and combat-log dependency. Removed
GUID sorting, explicit cross-nameplate frame levels, priority enlargement and the
experimental foreground health-bar copy. Obsolete rule settings are discarded
when the addon initializes. The shared change applies to both clients.

The base health bar remains twice the native health-bar height, growing upward.
The selected target keeps its thicker border. The name remains centered
above each bar, with debuff icons above the header. The level appears in a
separate square to the right of the health bar, with a bronze, slightly rounded
border and difficulty-coloured text. No priority logic changes
bar geometry or targeting.

## Options

Open **Options > AddOns > ElmoPlater**, or `/eplater` (`/elmoplater`), for:

- Show/hide the quest kill knife.
- Debuff icon size, from 14 to 36 pixels.

Settings are saved per character. Previous `/cplater`, `/classicplater`,
`/ctarget` and `/classictarget` commands remain aliases for the same options page.
`/eplater status` reports tracked bars and health readability; `/eplater auras`
reports the active aura display and skips direct queries when Blizzard manages
that display or restricts aura data.

## Personal debuffs

Where available, Blizzard's aura container draws icons, countdowns and stacks,
including restricted combat auras. The container countdown is a number without
an `s`, uses a 20% larger font and sits above its icon. Stacks remain at the
bottom right. The addon never inspects the adopted aura buttons.

Clients without that template retain the legacy personal-aura display. Other
players' and pet debuffs are excluded. Restricted or unavailable raw aura data
is skipped. No spellbook, learned-debuff catalogue or combat log is needed to
display auras.

## Quest kill marker

A 16-pixel knife appears four pixels to the left of the health bar when the mob
matches an unfinished kill objective in your active quest log. It disappears
when the objective or quest is complete, or the quest is abandoned. Item-drop
bags are not shown.

Use `/eplater questkills off` to disable the knife, `/eplater questkills on`
to enable it, or `/eplater questkills` to report its state. The setting defaults
to enabled. Disabling it stops quest scans and immediately hides existing knives.

Both clients use the native quest log and Blizzard's localized kill wording;
Questie is not required or read. Creature names must match the objective exactly.
Group objectives such as "Troggs slain" cannot reliably identify individual
creatures without a database, so ambiguous matches are omitted. Private or
unavailable data is skipped and retried. Legacy collapsed headers and selected
quests are restored after discovery; cached quest IDs avoid repeating expansions
on progress updates.

## Native frame boundaries

Addon artwork does not intercept mouse input. Guarded native hit-test bindings
follow the owned health rectangle and remain clipped by Blizzard's nameplate
bounds. Removing or pooling a plate restores native artwork and click anchors.
Global nameplate dimensions and stacking settings are not changed during normal
operation. One-time recovery of old dimension/hit-test overrides is retained.

Source and installed-package checks use Lua 5.1 mocks in
`scripts/tests/ElmoPlater`. These verify geometry, auras, opaque HP display, quest
markers, cleanup and absence of retired dependencies; live rendering and overlap
behaviour remain subject to in-game testing. See `SOURCES.md` for API references.
