# Source and validation

Priority is lexicographic: health below 20%, missing personal debuff,
then lowest remaining absolute HP. The selected target participates in the same ordering and can receive the doubled height. Simulated
checks include different maximum health values to distinguish HP from percentage,
and verify that the enlarged rectangle follows the new tie-breaker.

Client: WoW Classic Era 1.15.9 / Interface 11509.
Primary UI snapshot: https://github.com/Gethe/wow-ui-source/tree/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns

The native NamePlateBase owns a pooled UnitFrame with HealthBarsContainer.healthBar. An addon-owned UIParent bounds frame follows that existing health region. Only this owned frame is measured to extend the first eligible attacked rectangle upward to twice its normal height. Global native nameplate dimensions and stacking bounds are not changed. One-time migration restores the prior build's saved global size/inset overrides outside combat.

Installed Plater.lua (around lines 3778-3788 and 9129-9136) binds an owned hitTestFrame using guarded native hit-test APIs and later resizes that frame. ElmoPlater uses the same principle: SetHitTestPoints anchors to the owned rectangle, guarded by CanChangeHitTestPoints. The published FrameAPINamePlateDocumentation describes combat restrictions and the unit-assignment-tick exception. Binding is deferred when disallowed; changing the already bound owned rectangle updates its referenced region. Cleanup reconstructs Blizzard's normal hit points from NamePlateUnitFrameMixin:ApplyFrameOptions instead of calling the restricted GetHitTestPoints getter. Native containing bounds and overlap handling remain engine-controlled.

API source: https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/FrameAPINamePlateDocumentation.lua
Plater source: https://github.com/Tercioo/Plater-Nameplates/blob/master/Plater.lua

Personal auras use C_UnitAuras.GetAuraDataByIndex(..., "HARMFUL|PLAYER") with an additional player-only source check and a legacy UnitDebuff fallback. The combat log tracks player-sourced damage, misses and harmful debuffs by destination GUID, and clears tracked mobs on death or combat end. GUIDs are used for tracking only. Unit health and faction events update rectangles; aura events rescan only the affected unit. A 0.1-second timer handles expiry and graphical ranking. Solid WHITE8X8 replaces the shaded status-bar texture.

The installed Plater demonstrates UIParent-based artwork, effective-scale normalization and frame-level ordering. No Plater source/assets are copied or modified.

Validation: tools/classicplater/test_prototype.py executes the two runtime files in Lua 5.1 against native-frame, combat-log and aura fixtures. It checks unchanged global dimensions/insets, guarded click binding, targeting through the added upper half in combat, deferred writes on blocked ticks, selected-target participation, health strictly below 20% before missing debuffs, the exact 20% boundary, attacked-only enlargement, combat cleanup, solid fill, aura ownership/ranks/expiry, reaction colours and pooled-frame restoration. The modeled containing native rectangle is larger than its health bar, and click tests retain native clipping. Mocks do not verify live rendering or actual C++ hit-test and overlapping click behavior.
