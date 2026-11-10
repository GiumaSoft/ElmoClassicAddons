# Sources and compatibility

Original standalone tracker code ported from ClassicLeveling 1.6.3. UI and
messages remain English. No external addon libraries or other addons' code are
bundled. The small TalentBranches.lua table contains numeric spell-to-branch
facts from the installed TalentsForeverBook data for build 1.60.1.70425; actual
ownership and ranks always come from the current native trait configuration.
Definitions are matched by spell ID, so reassigned node IDs cannot inherit an
old talent's branch. Unknown spells are ignored. TalentsForeverBook is not a
runtime dependency.

Local target: WoW Forever 1.60.1.70685, interface 16001, product wowf, verified
from the installed .build.info and Camelot addon manifests on 2026-10-30.

Primary UI/API reference: Blizzard UI source mirror Gethe/wow-ui-source,
forever branch, pinned revision ca8368f2f2380cbe696854f7f2646387c278a61b.

- [XP, unit identity and levels](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua)
- [Combat restrictions and absent Classic event reader](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/CombatLogDocumentation.lua)
- [XP chat event](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/ChatInfoDocumentation.lua)
- [Item stats, prices and uniqueness](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/ItemDocumentation.lua)
- [Native usability](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/PlayerInfoDocumentation.lua)
- [Native tooltip data](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/TooltipInfoDocumentation.lua)
- [Traits and live ranks](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/SharedTraitsDocumentation.lua)
- [Spellbook eligibility](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellBookDocumentation.lua)
- [Native combined/individual bag rendering](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_UIPanels_Game/Mainline/ContainerFrame.lua)
- [Camelot bag overrides](https://github.com/Gethe/wow-ui-source/blob/ca8368f2f2380cbe696854f7f2646387c278a61b/Interface/AddOns/Blizzard_UIPanels_Game/Camelot/ContainerFrame.lua)

Secure post-hooks observe SetItemButtonQuality for modern native bag buttons,
and the installed BetterBags 0.8.4 ItemFrame FinishItemDraw/ResetVisuals methods.
BetterBags files are neither modified nor bundled. GetBagID belongs to each
button in combined bags; the parent container ID is not used as the displayed
bag ID. Borders are independent mouse-disabled child frames.

Secret values are rejected. Restricted combat readers are not invoked; invalid
or restricted events cannot abort loading. Readable mob XP notices provide
history when combat log APIs are absent. Unknown mob levels, timing and XP/s
remain unknown. Relative gear weights are heuristics inherited from the Era
tracker, not a simulation of Forever balance, procs or sets.

Only ElmoLevelingDB holds the tracker profile. Former-addon importers are no longer included or loaded. Existing Elmo profiles are preserved; the installer does not modify SavedVariables files.

Development checks live in scripts/tests/leveling_era and scripts/tests/leveling_forever. They use simulated APIs and do not constitute live-client verification.

Session Combat uses PLAYER_REGEN_DISABLED / PLAYER_REGEN_ENABLED and initializes
from the readable UnitAffectingCombat("player") state. It does not require combat
log access. combatSeconds is saved alongside total seconds; both clocks exclude
offline time, and active combat is restarted at Reset. Older profiles retain
Total with Combat starting at zero. The displayed bag counter is now only
Bags (sell value); the legacy bag-baseline field remains readable for profile
compatibility but has no visible change counter.


Respawn means use the exact readable NPC name as their only grouping key.
Credited kill times enter a bounded FIFO; the first newly observed living GUID
with that name consumes one wait, including mobs at other levels. Public dead to
alive transitions also qualify. Known living GUIDs suppress repeated observations;
up to 1000 identities are retained per area. A five-second public-sighting cache
handles XP-backed kills whose rows settle after their first reappearance.
Samples publish every five seconds into saved total/count records, capped at
100 names. Travel/login clears unfinished waits and observed identities. Clear
preserves learned means; Reset clears means as well. Protected identities are
never inspected or reconstructed. The observations estimate availability, not a
server-provided spawn time.

Both displayed XP/min columns have a separate five-second refresh cadence.
Actual XP awards and 60-second-window calculations stay immediate; Reset forces
the visible counters to zero immediately. Delayed frames retain the cadence's
phase. Shared client behavior passes 15 differential scenarios.

Respawn averages are displayed in rounded whole seconds, e.g. 135s, in both the column and tooltip.

Restricted clients also measure public per-GUID engagement intervals. A readable
UnitAffectingCombat plus group UnitThreatSituation (including status 0), or a
readable UnitIsUnit match from the mob's target to player/pet/party, starts timing.
UNIT_FLAGS, UNIT_HEALTH and threat/target events update observations; the existing
one-second scan catches missed events. Public death ends timing; a GUID-bearing
XP notice can end it when the unit disappears. Name-only XP must match a unique
observed corpse. Five seconds of grace allow death/XP to follow combat clearing;
a repull resets that mob's start. Travel/reset discards unfinished observations.
These intervals and derived XP/s show ~ and retain that marker in saved history.
They do not replace Classic Era's combat-log timestamps. Interface 16000-16999
never registers or reads the Blizzard-only combat-log event, even when the
restriction flag is false outside combat. Primary API reference:
https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
test_kill_timing.py adds twelve Lua 5.1 regressions for correlation, target changes,
group/pet engagement, private values, repulls, reset/travel, persistence, UI
formatting and the Forever combat-log guard. These are simulated checks.
