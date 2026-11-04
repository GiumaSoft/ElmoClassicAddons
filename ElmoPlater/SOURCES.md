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
normalizes effective scale and frame level. Base bars grow upward to twice the
native health-bar height; the chosen engaged mob doubles that base again.
Global dimensions/stacking are unchanged.

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

Forever's CombatLogDocumentation marks COMBAT_LOG_EVENT_UNFILTERED as restricted:
https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/CombatLogDocumentation.lua
Interface 16000-16999 never registers or unregisters that event, regardless of
IsCombatLogRestricted or getter availability. Other clients unregister it only
after a registration. Public UnitThreatSituation("player", unit), including status
0, and personal harmful auras provide engagement evidence while the player is in
combat. Secret threat values are ignored. GetBuildInfo's interface distinguishes
Forever from Classic Era; WOW_PROJECT_MAINLINE alone does not.

`scripts/tests/ElmoPlater/test_rules.py` exercises A/B/C multi-debuff decisions,
explicit order including AoE, explicit lowest-health rules, resources, own CD,
GCD/charges, refresh/count limits, AND/OR/grouping, restricted values, editor
save/cancel, dropdown paging, adding multiple independent rules, duplication,
ordering and legacy migration. Spellbook options use capability-checked modern
C_SpellBook readers or Classic spell-tab readers; tests cover both paths. `test_prototype.py` checks geometry isolation,
attacked-only enlargement, native containment, debuff rows above the bar,
expiry, colours, and restoration. Both use Lua 5.1 fixtures, not the
native engine. `scripts/tests/test_forever.py` adds modern/restricted API checks.
`test_forever_combat_log.py` rejects both registration and removal of the combat-log
event on Forever, including failures that do not throw through pcall, and checks
public-threat/personal-aura fallback, secret threat and end-of-combat cleanup.
`test_secret_health.py` checks that protected health/max-health values go directly
to StatusBar:SetMinMaxValues/SetValue and protected percentages go to
FontString:SetFormattedText using UnitHealthPercent with CurveConstants.ScaleTo100.
These display APIs accept secret arguments on Forever. Such values are never
compared for priority. Readable debuff rules without health constraints remain
eligible; health rules and unreadable aura conditions cannot match.
https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleStatusBarAPIDocumentation.lua
https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleFontStringAPIDocumentation.lua
Live graphical rendering and overlap targeting have not been certified by mocks.

`scripts/tests/ElmoPlater/test_dynamic_health.py` verifies schema-v1 migration
without duplicating rules, editable strict percentage thresholds, health/debuff
reordering, disabled/deleted rules, no hidden HP fallback, absolute-HP selection
restricted to attacked mobs, health rules without spell/resource dependencies,
additional conditions, unknown data and manager controls. The normal secondary
layering uses GUID only; all health priority comes from the ordered rule list.
