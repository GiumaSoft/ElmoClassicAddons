# Sources and validation

The editor's condition-type/operator/value rows, AND/OR and grouping concepts
were reviewed against [TellMeWhen's condition editor](https://github.com/ascott18/TellMeWhen/blob/master/Components/Core/Conditions/Config.lua)
and [condition metadata specification](https://github.com/ascott18/TellMeWhen/blob/master/Documentation/Conditions/ConditionDataSpecification.txt).
No TellMeWhen runtime or assets are copied. ElmoPlater evaluates validated data
with a small boolean evaluator; saved settings are never compiled as Lua.
Ordered first-match rules are separate from the conditions inside each rule.

Primary Classic Era UI/API snapshot, Interface 11509:
https://github.com/Gethe/wow-ui-source/tree/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns

Primary Forever UI/API snapshot, Interface 16001:
https://github.com/Gethe/wow-ui-source/tree/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns

The native pooled UnitFrame owns HealthBarsContainer.healthBar. Addon-owned
UIParent bounds follow that region. Only owned bounds are measured. Artwork
normalizes effective scale and frame level. The chosen engaged mob's rectangle
grows upward to twice its usual height. Global dimensions/stacking are unchanged.

[Plater](https://github.com/Tercioo/Plater-Nameplates/blob/master/Plater.lua)
demonstrates owned hit-test frames and guarded native bindings. ElmoPlater binds
SetHitTestPoints only when CanChangeHitTestPoints permits it, then changes its
owned reference frame. Cleanup reconstructs Blizzard's published anchors without
calling the restricted getter. Native containing bounds and click overlap remain
engine-controlled. Personal debuff icons are above the bar, outside the click
rectangle. The separate priority anchor has been removed.

C_UnitAuras.GetAuraDataByIndex uses HARMFUL|PLAYER plus a player-source check,
with UnitDebuff fallback. Aura scans and public combat logs populate a per-character
observed-debuff catalog. Damage, misses and personal harmful auras mark engaged
mobs. GUIDs identify records only. The 0.1-second tick updates priority and expiry;
aura events scan the changed unit. Debuff rules require public usability/resource and
cooldown data. GetSpellCooldownDuration(..., true) ignores GCD; the numeric fallback
compares the spell cooldown with spell 61304's GCD. Charges are checked separately.
Unknown data fails closed rather than fabricating a usable spell or missing aura.

`scripts/tests/ElmoPlater/test_rules.py` exercises A/B/C multi-debuff decisions,
explicit order including AoE, explicit lowest-health rules, resources, own CD,
GCD/charges, refresh/count limits, AND/OR/grouping, restricted values, editor
save/cancel, dropdown paging, adding multiple independent rules, duplication,
ordering and legacy migration. Spellbook options use capability-checked modern
C_SpellBook readers or Classic spell-tab readers; tests cover both paths. `test_prototype.py` checks geometry isolation,
attacked-only enlargement, native containment, debuff rows above the bar,
expiry, colours, and restoration. Both use Lua 5.1 fixtures, not the
native engine. `scripts/tests/test_forever.py` adds modern/restricted API checks.
Live graphical rendering and overlap targeting have not been certified by mocks.

`scripts/tests/ElmoPlater/test_dynamic_health.py` verifies schema-v1 migration
without duplicating rules, editable strict percentage thresholds, health/debuff
reordering, disabled/deleted rules, no hidden HP fallback, absolute-HP selection
restricted to attacked mobs, health rules without spell/resource dependencies,
additional conditions, unknown data and manager controls. The normal secondary
layering uses GUID only; all health priority comes from the ordered rule list.
