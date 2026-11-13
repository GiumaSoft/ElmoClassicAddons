# Equipment upgrade formulas

These are the exact rules implemented in `Upgrades.lua`. The purple border marks
a currently usable item with a higher estimated leveling score than an allowed
equipped replacement. The weights are relative heuristics, shared by Classic Era
and Forever; they do not simulate damage, healing, survival or best-in-slot gear.

## Score and comparison

```text
score(item, slot, profile) =
    sum(item.stat × profile.statWeight, for every stat except weapon DPS)
  + item.flatHealth × profile.StaminaWeight / 10
  + item.flatMana × profile.IntellectWeight / 15
  + item.weaponDPS × applicableDPSWeight(slot, profile)

upgrade = usable AND validReplacement AND uniqueLimitsSatisfied
          AND candidateScore > replacedEquipmentScore + 0.001
```

An absent stat or weight contributes zero. Flat health and mana are converted
only by the terms above; they are not added as primary stats a second time.
An empty equipment slot has score zero. Equal scores do not get a purple border.
For a two-handed candidate, the replaced score is main-hand plus off-hand.

## Profile selection by class and specialization

The branch with the most allocated talent points selects the specialization.
Ties choose the first branch in the table below. With no allocated points, the
default column applies. Forever reads current C_Traits ranks and maps each
recognized talent spell to a branch using `TalentBranches.lua`; unknown spells
are ignored. Classic reads its three talent tabs. The same weights apply to
all specializations mapped to the same profile.

| Class | Branch 1 | Branch 2 | Branch 3 | No talents |
| --- | --- | --- | --- | --- |
| Hunter | Beast Mastery: Hunter | Marksmanship: Hunter | Survival: Hunter | Hunter |
| Rogue | Assassination: Rogue | Combat: Rogue | Subtlety: Rogue | Rogue |
| Warrior | Arms: Warrior damage | Fury: Warrior damage | Protection: Protection | Warrior damage |
| Paladin | Holy: Healing | Protection: Protection | Retribution: Paladin damage | Paladin damage |
| Shaman | Elemental: Caster damage | Enhancement: Shaman melee | Restoration: Healing | Shaman melee |
| Druid | Balance: Caster damage | Feral: Druid feral | Restoration: Healing | Druid feral |
| Priest | Discipline: Healing | Holy: Healing | Shadow: Caster damage | Caster damage |
| Mage | Arcane: Caster damage | Fire: Caster damage | Frost: Caster damage | Caster damage |
| Warlock | Affliction: Caster damage | Demonology: Caster damage | Destruction: Caster damage | Caster damage |

An explicitly assigned native group role takes precedence:

- **TANK:** Druid uses Druid tank; Warrior, Paladin and Shaman use Protection.
- **HEALER:** Paladin, Shaman, Druid and Priest use Healing.
- **DAMAGER:** Priest uses Caster damage; Druid uses Druid feral for branch 2
  and Caster damage otherwise; Warrior and Paladin use their damage profiles;
  Shaman uses Caster damage for branch 1 and Shaman melee otherwise.
- **NONE** or unavailable role: keep the talent/default choice.

The current implementation has ten profiles. It does not use separate weights
for every individual talent build or custom Forever specialization.

## Primary and armor weights

| Profile | Strength | Agility | Stamina | Intellect | Spirit | Armor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hunter | 0.1 | 2 | 0.6 | 0.3 | 0.15 | 0.01 |
| Rogue | 1 | 2 | 0.6 | 0 | 0.05 | 0.01 |
| Warrior damage | 2 | 1 | 0.8 | 0 | 0.2 | 0.02 |
| Paladin damage | 1.8 | 0.6 | 0.8 | 0.5 | 0.3 | 0.02 |
| Shaman melee | 1.5 | 1 | 0.7 | 0.6 | 0.3 | 0.02 |
| Druid feral | 1.5 | 1.7 | 0.9 | 0.1 | 0 | 0.02 |
| Protection | 0.7 | 1.1 | 1.5 | 0 | 0 | 0.06 |
| Druid tank | 1 | 1.2 | 1.5 | 0 | 0 | 0.06 |
| Caster damage | 0 | 0 | 0.5 | 1 | 0.5 | 0.005 |
| Healing | 0 | 0 | 0.4 | 1 | 0.8 | 0.005 |

## Attack, spell and weapon weights

| Profile | AP | Ranged AP | Feral AP | Spell power | Healing | Melee DPS | Ranged DPS | Wand DPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hunter | 0.5 | 1 | 0 | 0 | 0 | 0 | 8 | 0 |
| Rogue | 0.5 | 0 | 0 | 0 | 0 | 8 | 0 | 0 |
| Warrior damage | 1 | 0 | 0 | 0 | 0 | 8 | 0 | 0 |
| Paladin damage | 0.5 | 0 | 0 | 0.3 | 0 | 7 | 0 | 0 |
| Shaman melee | 0.5 | 0 | 0 | 0.4 | 0 | 7 | 0 | 0 |
| Druid feral | 0.5 | 0 | 0.5 | 0 | 0 | 0 | 0 | 0 |
| Protection | 0.3 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| Druid tank | 0.3 | 0 | 0.3 | 0 | 0 | 0 | 0 | 0 |
| Caster damage | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0.5 |
| Healing | 0 | 0 | 0 | 0.8 | 1 | 0 | 0 | 0 |

Weapon DPS is used only for weapon items. Slot 18 uses Wand DPS for wands and
Ranged DPS otherwise. Main-hand uses Melee DPS; off-hand uses half the Melee DPS
weight. Hunter melee weapons and all feral/bear weapons are therefore stat sticks.

## Secondary and defensive weights

| Profile | Crit | Hit | Spell crit | Spell hit | MP5 | Defense | Dodge | Parry | Block | Block value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hunter | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rogue | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Warrior damage | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Paladin damage | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Shaman melee | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Druid feral | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Protection | 5 | 8 | 0 | 0 | 0 | 2 | 10 | 10 | 8 | 1 |
| Druid tank | 5 | 8 | 0 | 0 | 0 | 1 | 10 | 0 | 0 | 0 |
| Caster damage | 0 | 0 | 8 | 10 | 2 | 0 | 0 | 0 | 0 | 0 |
| Healing | 0 | 0 | 5 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |

MP5 is mana restored per five seconds. Weights multiply the values returned by
the item-stat API. Supplemental English Classic tooltip percentages are used
as percentage points (for example, 1% contributes `1 × weight`); there is no
level-dependent conversion of rating to percentage.

## Replacement and data rules

- The candidate must be equippable and currently usable, with a required level
  no higher than the character's level. Fishing poles, bags and unsupported
  equipment types are excluded.
- Rings and trinkets are tested against both corresponding slots. The border
  appears when at least one legal replacement improves the score.
- A generic one-handed weapon can also replace the off-hand after Dual Wield
  is learned, while no two-handed main-hand is equipped. Dedicated off-hand
  weapons require Dual Wield. A shield or held item cannot be added while a
  two-handed main-hand remains equipped.
- Unique and unique-category limits are checked against equipment remaining
  after the proposed replacement. A two-handed replacement removes both hands
  from that check.
- Missing candidate or equipped-item data waits for loading. A required weapon
  DPS value must be loaded before comparison; unknown equipment is never treated
  as an empty, zero-score slot.
- Native aliases for one stat use their maximum value, not their sum. Recognized
  flat English tooltip bonuses are summed within the tooltip, then merged with
  the native stat using `max(native, tooltip)`, preventing double counting.
- Changes to equipment, level, talents, spells or assigned role invalidate the
  cached result. Actual level and equipped links are also checked once a second.
- Borders apply to the backpack and four carried bags, including native combined
  bags and supported BetterBags item frames. They are mouse-transparent.

## Worked examples and limits

For a Hunter, an armor item with +5 Agility, +3 Stamina and 100 Armor scores
`5 × 2 + 3 × 0.6 + 100 × 0.01 = 12.8`. It receives a border when a legal equipped
replacement scores less than `12.799`.

For a Holy/Discipline Priest using Healing weights, +10 Intellect, +5 Spirit,
+12 generic spell power and +20 healing score
`10 × 1 + 5 × 0.8 + 12 × 0.8 + 20 × 1 = 43.6` before other stats.
For Shadow/Caster damage the same stats score
`10 × 1 + 5 × 0.5 + 12 × 1 + 20 × 0 = 24.5`.

Item level and rarity add no score. Procs, on-use effects, set bonuses,
school-specific spell bonuses, resistances, stat caps, weapon speed, rotations
and encounter requirements are not modeled. Tooltip supplementation supports
English. A purple border is an estimate under these rules, not a guarantee that
an item is better for every build or situation. The addon never equips gear or
changes talents automatically.
