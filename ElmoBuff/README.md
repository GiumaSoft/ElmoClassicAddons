# ElmoBuff

Small, clickable missing-buff icons beside Blizzard player and party frames.
Dark backgrounds, bronze borders and gold highlights match the other Elmo tools.
Supports Classic Era and Forever without SmartBuff, Questie or another dependency.

Click an icon to cast its buff on that member through Blizzard's
`SecureActionButtonTemplate`. The current target is preserved. An icon disappears
only after the aura is positively identified: clicking, a failed cast or a cast
request alone does not hide it. A red `!` means out of range; move closer to retry.

This first version rebuffs **outside combat**. Native secure state drivers hide
the icons and disable their spell actions in combat. Addon Lua never changes
protected frames or reads auras in combat. Raids and pets are excluded.

Supported buffs:

| Class | Buffs |
| --- | --- |
| Priest | Fortitude, Divine Spirit, optional Shadow Protection |
| Mage | Arcane Intellect |
| Druid | Mark of the Wild, optional Thorns |
| Paladin | All enabled, learned alternatives: Might, Wisdom and Kings |

Only learned spellbook ranks are used. A lower rank is selected for low-level
members. Localized spell names are read from the client; equivalent group buffs
count as present. Spirit and Intellect are omitted for classes without mana.

Existing single/group versions and different ranks in each supported buff family
suppress the icon while present. Early refresh applies only to your own exact
cast rank. A foreign caster's buff can be improved by talents even at the same
rank, so it is conservatively left in place until it expires; the addon does not
guess its strength from spell ID or rank. Unreadable caster/rank data also prevents
an early replacement. All matching auras are retained, so an expiring weaker
entry cannot overwrite coverage by another existing buff. This is family-based
coverage, not a universal comparison of unrelated stat buffs or consumables.

Mutually exclusive buff families share the same behavior for every supported
class: all enabled, learned alternatives appear while no conflicting buff is
present. A confirmed active buff suppresses its incompatible alternatives for
that member. Failed or unconfirmed casts leave the choices available. When the
buff expires or is removed, the alternatives return. If early refresh is
enabled, only the existing buff can reappear for refresh, without switching to
another family. Compatible buffs such as Fortitude and Divine Spirit, or Mark
of the Wild and Thorns, remain independent.

Blessing conflicts are tracked per caster. Another paladin's blessing covers
that same family without blocking a different blessing from you. Your own
normal or Greater blessing suppresses your other alternatives. Unreadable
ownership is treated as unknown rather than enabling a conflicting cast.
Options provides individual blessing checkboxes instead of preselecting one.

Unreadable or restricted aura data is treated as unknown, never as a missing
buff. Restrictions can therefore suppress suggestions even outside combat.

Open **Options > AddOns > ElmoBuff**, or `/ebuff` (`/elmobuff`), to choose buffs,
include your own frame, set the refresh threshold (default 60 seconds; 0 means
missing only), choose right/left/above placement and adjust icon size. `/ebuff on`,
`/ebuff off` and `/ebuff status` are also available. Settings are per character.

Native party frames, including compact party frames, are only read as anchors;
they are never modified. Custom replacements that hide every native party frame
are outside this version's scope. No window, keybinding or chat report is added.

Implementation references for Forever 1.60.1 build 70862:

- [Blizzard secure spell action](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua)
- [Spellbook and learned-spell API](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellBookDocumentation.lua)
- [Aura API and access restrictions](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitAuraDocumentation.lua)
- [Secure state drivers](https://github.com/Gethe/wow-ui-source/blob/9dc84f0d3bba/Interface/AddOns/Blizzard_RestrictedAddOnEnvironment/SecureStateDriver.lua)

`scripts/tests/ElmoBuff/test_addon.py` exercises the real Lua 5.1 source with
explicit aura, frame and secure-click mocks. These checks do not replace a live
client test of Blizzard's hardware-event and protection implementation.
