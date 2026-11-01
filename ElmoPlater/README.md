# ElmoPlater 2.2.2

Classic Era / Forever nameplates with solid reaction colours, contrasting borders,
health percentage, difficulty-coloured levels and all your active harmful debuffs.
Other players' and pet debuffs are excluded. Claimed mobs are grey and marked
`[CLAIMED]`. Native positioning and targeting remain owned by WoW.

## Configuration

Open `/eplater` (also `/elmoplater`, `/cplater`, `/classicplater`, `/ctarget`,
`/classictarget`). Settings are saved per character.

1. In **New rule**, choose **Health below threshold**, **Lowest health (attacked mobs)**
   or a learned missing debuff, then click **+ Add rule**. Repeat for more rules.
   Debuffs appear after you apply them once; observing an aura never creates a rule.
2. Select an entry in the left list. **Rule type** controls which fields appear.
   The health threshold is editable (default 20%, strictly below). Dropdowns choose the debuff, cast ability,
   enabled status, single-target/AoE application, refresh threshold, mob preference,
   minimum mob counts and target health range. The cast menu also includes active
   abilities from your spellbook. No numeric spell IDs need to be entered.
3. Click **Save rule** to save that entry. **Duplicate** creates an independent
   copy at the bottom. **Move up / Move down** changes precedence; **Remove** deletes
   the selected rule. Long lists and long dropdown menus have Previous / Next pages.
4. Rules work like firewall rules: the **first matching enabled rule wins**.
   Put an AoE rule above a single-target rule to prefer it. The application label
   never silently reorders the list.
5. **Conditions…** adds any number of comparisons joined with AND / OR and
   parentheses. AND takes precedence over OR. These are additional requirements
   alongside the rule's limits. Only debuff rules require cooldown and resource checks. Another dropdown
   selects the spell/debuff to compare, with **This rule** as the default.

Conditions cover target HP/percentage, player health, mana/rage/energy, engaged
mobs, mobs needing the rule's debuff, active configured debuffs, a personal debuff's
presence/time/stacks, a spell's cooldown and combat status. **This rule** uses
the selected rule; another selection checks that spell or debuff. Values are ordinary
numbers; boolean comparisons use 1/0. Missing debuffs have zero remaining time
and stacks. Unavailable/private values do not satisfy comparisons.

Rule limits include minimum engaged mobs, minimum mobs missing or needing a
refresh of this debuff, target health range and refresh threshold in seconds
(0 = missing only). Unknown aura durations are never guessed. **Prefer mobs
already covered** favours candidates with more other active, configured debuffs;
remaining ties use lowest absolute HP. Turn it off for simple lowest-HP ties.

## Priority

Only mobs you attacked during the current combat qualify for the marker,
including your selected target. Nearby untouched mobs do not qualify.

Every priority is an ordinary enabled rule, evaluated from top to bottom:

- **Health below threshold** chooses the lowest remaining absolute HP among mobs
  strictly below the configured percentage (20% by default).
- **Missing debuff** requires an actionable missing/refreshable debuff, a usable
  learned cast ability, enough resources and no own cooldown. GCD is ignored.
  Partial-coverage preference and lowest-HP ties follow the rule settings.
- **Lowest health (attacked mobs)** chooses the lowest absolute remaining HP,
  regardless of percentage, aura readability, resources or cooldowns.

All types respect the minimum engaged count, health range and additional
conditions. The first match wins; later rules do not filter or override it.
Stable GUID breaks final equal-HP ties. GUIDs are never used for targeting.
There is no implicit critical-health gate or lowest-health fallback. With no
matching enabled rule, no bar receives the priority enlargement. Other bars use
stable GUID layering rather than a hidden health ordering.

The migration inserts **Health <20%** before your existing debuff rules and
**Lowest health** after them once. Move, disable, delete or duplicate either rule;
deleted rules stay deleted across reloads. New rules append at the bottom, so
move a general Lowest health rule below more specific rules to keep them reachable.

Example order: Health <20%, Thunder Clap, Rend, Lowest health. If no mob meets
the first rule, ready Thunder Clap can pick a mob missing it. If Thunder Clap is
cooling down, Rend can prefer a partly covered mob. Move Rend above Health <20%
if you want the Rend rule to win even when another mob is below 20%.

The chosen rectangle is drawn in front and doubled in height, growing upward.
The full name and level are centered together above the health bar. Names keep
their natural single-line width, extending beyond either side of the bar when
needed; the level follows the full name with a 6-pixel gap.
Your debuff icons are placed **above** each bar, leaving 20 pixels for the name
and level; additional rows extend upward. There is no separate priority anchor. The doubled bar
is the native click target. WoW retains its containing nameplate bounds and its
own overlap click priority.

## Compatibility and validation

Choose `classic` for Interface 11509 or `forever` for Interface 16001. Both packages
share the runtime. After updating, reload the UI when safe. Existing settings are
imported from ClassicPlater / ClassicTarget when available. A legacy named-debuff
setting is imported as a debuff rule, with the two editable health rules added
once by the v2 rule-schema migration.
`/eplater debuff NAME_OR_ID` replaces the list with one rule; `debuff any` clears it.

The addon does not resize global native nameplates, measure restricted regions,
hook Plater, or target by GUID. Artwork and permitted native hit points are restored
when a pooled nameplate is removed. If identity or health is private, Blizzard's
artwork remains visible. Restricted aura data is not treated as a missing debuff.
When combat logs are restricted, visible personal auras can identify engaged mobs;
damage-only attack history is unavailable. Tracking clears on death/combat end.

Lua 5.1 behavioral checks cover rules, resources/cooldowns, conditions, configuration
save/cancel, dynamic health order/removal/migration, private-value handling and pooled frames. These are simulated API
checks; actual rendering and native click/overlap behavior require an in-game test.
