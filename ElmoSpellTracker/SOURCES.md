# Client API references

Target: **Classic Era, Interface 11509**. This addon uses player spell APIs and
native UI widgets. It bundles no spell/cooldown database and no third-party code.

The implementation was checked against Blizzard's Classic Era UI/API source,
mirrored by [Gethe/wow-ui-source](https://github.com/Gethe/wow-ui-source/tree/4192ac60067fc55566182291bc67c85dd9b6794d),
revision **`4192ac60067fc55566182291bc67c85dd9b6794d`**:

- [`SpellDocumentation.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellDocumentation.lua):
  spell information, cooldown and charge reads, duration objects and spell-data requests.
- [`SpellSharedDocumentation.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellSharedDocumentation.lua):
  the `SpellCooldownInfo` / `SpellChargeInfo` structures and on-hold/active semantics.
- [`SpellBookDocumentation.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellBookDocumentation.lua):
  known player spells and spellbook/override membership.
- [`LuaDurationObjectAPIDocumentation.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/LuaDurationObjectAPIDocumentation.lua):
  `GetRemainingDuration()` returns the remaining real-time duration by default.
- [`UnitDocumentation.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua):
  `UNIT_SPELLCAST_SUCCEEDED` carries unit, cast GUID and spell ID.
- [`Blizzard_CooldownBroadcaster.lua`](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_CooldownBroadcaster/Blizzard_CooldownBroadcaster.lua):
  client cooldown event handling and the start/duration time-span convention.

Snapshots, source hashes and the exact URLs used for verification are stored under
`tmp/classicspellstracker/api/sources.json` in the development workspace. These
files are not required by the installed addon.

## Implementation boundaries

`C_Spell.GetSpellCooldownDuration(spellID, true)` is the preferred source for
remaining time: the `true` explicitly excludes the global cooldown. The addon does
not rely on `isOnGCD` outside a cooldown event, as the structure's documentation
warns that field is not reliable in that context. Available charge duration
objects are used in the same way for recharging spells.

When duration objects are unavailable, the adapter uses the native start/duration
fields and compares the cooldown with the standard GCD probe (spell 61304).
Legacy spell globals, including base-cooldown metadata, are used when available.
The compatibility paths are tested separately; this build targets Era 11509.

Cooldown data may arrive after the cast-success event. A bounded five-second
pending queue allows later cooldown/spell-data events to complete discovery.
The updater runs at most ten times per second while a visible cooldown or a
pending discovery needs it, then stops. There is no network connection, chat send,
inventory scan, protected spell cast or third-party communication.

The source under `Interface/AddOns/ElmoSpellTracker` is original addon code.
Spell artwork, spell data, the game fonts and native tooltips are supplied by the client.

## Resource availability (1.0.2)

`C_Spell.IsSpellUsable(spellID)` returns `insufficientPower` as its second result, explicitly covering mana, rage and other resources. That flag controls resource greying independently of cooldown status. `IsUsableSpell` supplies the legacy fallback. Player `UNIT_POWER_UPDATE`, `UNIT_MAXPOWER`, `UNIT_DISPLAYPOWER` and `SPELL_UPDATE_USABLE` wake the display after it becomes idle.

Reference: [Classic Era Spell API](https://github.com/Gethe/wow-ui-source/blob/4192ac60067fc55566182291bc67c85dd9b6794d/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellDocumentation.lua#L631).
