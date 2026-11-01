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

Only ElmoLevelingDB holds the new tracker. The local installation has
a separately tagged, data-only helper under the previous ForeverLeveling folder
to load ForeverLevelingTrackerDB for migration. It preserves the older planner's
ForeverLevelingDB without interpreting it as XP. This helper is not distributed
in the public archive and unrelated addons are not used for import. No
SavedVariables files are edited by the installer. ClassicLeveling remains
separate in _classic_era_.

Development evidence outside the addon: tools/classiclevelingforever/test_addon.py,
its wow_mock.lua fixture and test_parity.py, plus tmp/classiclevelingforever/api/
sources.json, parity.json and installation.json. All 205 unit checks and fifteen
comparisons with ClassicLeveling use simulated APIs; no live-client verification
is claimed.


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
