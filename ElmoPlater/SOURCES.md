# Sources and validation

Mana/cast API review on 2026-11-12, Forever snapshot
4cd0ab752a77164f654ccbca9d0c1fe8dafceebe:
https://github.com/Gethe/wow-ui-source/blob/4cd0ab752a77164f654ccbca9d0c1fe8dafceebe/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
https://github.com/Gethe/wow-ui-source/blob/4cd0ab752a77164f654ccbca9d0c1fe8dafceebe/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleStatusBarAPIDocumentation.lua

The 2.4.1 mana filter also checks public UnitClass classFilename and UnitIsPlayer
against the current [native Unit API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua).
Only NPCs classified as MAGE, PRIEST, WARLOCK, PALADIN, SHAMAN or DRUID qualify.
No spell observation or external NPC database is required. Unknown/private
classes are omitted rather than inferred from private power values.

UnitBars.lua checks the public UnitPowerType and forwards UnitPower/UnitPowerMax
directly to owned status bars. Public zero maximum hides mana; private maxima
are never compared. UnitCastingInfo/UnitChannelInfo supply the spell name/icon
directly to display methods. Their start/end timestamps are forwarded as the
status-bar min/max range, with GetTime()*1000 as the current value. All inputs
use milliseconds, so no arithmetic is performed on private times. SetMinMaxValues
and SetValue explicitly allow secret arguments from tainted addon code.
Channels use a coloured background covered by the native elapsed fill from the
right, leaving the remaining portion visible without subtracting private times.
Missing timing hides the cast. No duration-object binding, secure-execution
proxy, native cast-frame mutation or combat-log fallback is used.

Power and cast events plus the existing 0.1-second refresh maintain the bars.
Both displays are owned, non-interactive children below the health rectangle;
pool cleanup hides them and clears spell text/icon. Tests cover power changes,
ordinary and opaque cast display inputs, cast/channel direction, interruption,
unavailable timing, spacing, pooled reuse and both persistent options.
The fixtures verify addon behavior, not live API permission or C++ rendering.

Classic Era UI/API snapshot, Interface 11509:
https://github.com/Gethe/wow-ui-source/tree/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns

Forever 1.60.1 build 70862 UI/API snapshot, Interface 16001:
https://github.com/Gethe/wow-ui-source/tree/9dc84f0d3bba/Interface/AddOns

The native pooled UnitFrame owns HealthBarsContainer.healthBar. Addon-owned
UIParent bounds follow that region; only owned bounds/text are measured.
Bars grow upward to twice the native health-bar height. Explicit frame-level
sorting, GUID ordering and priority-dependent geometry have been removed.
Normal parent/child frame ordering draws each bar's own elements. The level
badge uses Blizzard's rounded tooltip border on an owned, non-interactive frame
next to the health rectangle; it is excluded from the click region. Native overlap
and click ordering between mobs remain engine-controlled.

Guarded SetHitTestPoints calls bind the owned rectangle only when
CanChangeHitTestPoints permits it. Cleanup reconstructs Blizzard's published
anchors without calling the restricted getter. Native containing bounds still
clip the hit region. Artwork and debuff icons do not intercept mouse input.

CustomAuraContainerTemplate displays HARMFUL|PLAYER above each owned bar:
https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_AuraContainer/Blizzard_CustomAuraContainer.lua
https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_AuraContainer/Blizzard_CustomAuraButton.lua

Its initialization callback registers icon, duration and application-count text;
subsequent updates never inspect or change adopted buttons. The public container
is bound to the nameplate token, scaled and disabled during pool cleanup. When
it is available, raw aura reads are unnecessary and skipped. Otherwise,
C_Secrets.ShouldAurasBeSecret gates batch/indexed/UnitDebuff legacy readers.
Aura events refresh the changed unit, including target/nameplate aliases.
The 0.1-second update maintains the display and legacy aura expiry. No aura
learning, combat-log subscription, threat or spell readiness checks remain.

Secret HP and max HP go directly to StatusBar:SetMinMaxValues/SetValue. Secret
percentages go to FontString:SetFormattedText through UnitHealthPercent with
CurveConstants.ScaleTo100; no comparison or custom curve consumes those values:
https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleStatusBarAPIDocumentation.lua
https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleFontStringAPIDocumentation.lua

QuestKills.lua reads native active quest IDs and C_QuestLog.GetQuestObjectives:
https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua
Only unfinished monster objectives matching Blizzard's localized
QUEST_MONSTERS_KILLED wording qualify. Classic suffix and Forever prefix counters
are supported. Public creature names must match exactly; item and interaction
objectives are excluded. The texture is WoW's INV_Weapon_ShortBlade_05. No
Questie data or assets are used. All plates share a half-second quest snapshot.
Quest events invalidate it; legacy header discovery restores headers/selection.

The Lua 5.1 tests in scripts/tests/ElmoPlater cover geometry isolation, fixed 2x
height, native click containment, colours, header/debuff layout, pool cleanup,
private health and aura display, native quest markers and settings retirement.
The reduced-runtime regression rejects combat-log registration/reads, threat,
spellbook access and explicit SetFrameLevel calls on both clients. Native options
are also checked by scripts/tests/test_options.py. These are simulated checks;
actual C++ rendering and targeting are not certified by mocks.
