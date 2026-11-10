# ElmoSpellTracker 1.0.3

## Options menu

Open **Options > AddOns > ElmoSpellTracker** for capacity, locking, removal of a saved ability by its number, clearing tracked skills and the existing bar settings window. Changes use the same saved settings and validation as the slash commands.

A standalone **WoW Classic Era and Forever** addon. Your successfully used player abilities
with their own cooldown are learned automatically and displayed in one horizontal bar.
The interface is English. No libraries are required.

## Behaviour

- Use an ability with a real cooldown for the first time: its icon is added.
- New abilities appear to the **right**, in first-use order. Reusing one does not
  duplicate it or change its position. Different ranks share one icon, using the
  most recently used rank for the icon/tooltip/cooldown query.
- An ability on cooldown is desaturated and dimmed, with a central countdown.
  When the cooldown ends the number disappears. The icon stays grey if mana, energy or rage is insufficient, and regains its original colour when enough resource is available. Resource availability is read from the client, including cost modifiers.
- Countdown values are seconds below a minute, `m:ss` for minutes, and whole hours
  for cooldowns of an hour or longer. Values round up until the cooldown ends.
- The initial capacity is **10**. Configure any whole number from **1 to 12**.
- Once full, additional abilities are not added. Increase capacity or remove an
  existing icon, then use the new ability again. Existing icons are not cycled out.
- Lowering capacity hides the extra saved icons; increasing it restores them.
  This prevents an accidental lower setting from deleting your learned list.
- Settings, the ordered skill list and bar position are saved **per character**.
  Cooldown times themselves are always read from the client, including after reload.

Player casts are tracked, including known racial/profession abilities with a real
cooldown. Pet/other-player casts, failed casts, auto-attacks, auto-repeat spells,
passives and unknown item-use spells are excluded. The global cooldown alone does
not qualify an ability, and does not grey out a ready tracked icon.

Abilities whose cooldown starts when an active effect ends are learned on use;
their countdown follows the cooldown reported by the game. If a charge-based
ability has a usable charge, its icon stays coloured; the timer appears when no
charge is available. A temporarily unreadable cooldown is marked `?`, not ready.

## Setup and controls

Restart the selected WoW client after installing this new addon, enable **ElmoSpellTracker**
in the AddOns list, then enter the world.

```
/cst                   Open settings
/cst max 10            Set capacity (1–12)
/cst lock              Hide the drag handle and prevent mouse removal
/cst unlock            Show the drag handle
/cst remove 3          Remove the third saved ability
/cst reset             Clear all tracked abilities; learn again when used
/cst help              Show commands
```

`/classicspellstracker`, `/cct` and `/classiccooldowntracker` are aliases. Settings also provide a numeric capacity
input and Apply, Lock/Unlock and Clear tracked skills buttons.

Drag the small handle on the **left** to move the bar. Right-click an icon to open
settings. **Shift-right-click** an icon while unlocked to remove it. Hover an icon
for the native spell tooltip. The empty unlocked bar shows only its drag handle.
Locking the bar hides the handle; tracked icons continue to work.

The bar only displays information: its icons do not cast spells or send messages.

## Upgrade from ClassicCooldownTracker

The legacy folder now contains only a data importer. It loads the previous per-character settings before ElmoSpellTracker initializes, preserving the spell list, limit, lock and position. Keep the importer enabled until the first successful login with ElmoSpellTracker. New settings are saved as ElmoSpellTrackerDB.

## Validation

`tools/classicspellstracker/test_addon.py` runs the actual addon in Lua 5.1 against
explicit simulated Era spell APIs and frame widgets. The checks cover cooldown
discovery, delayed data, GCD exclusion, ranks, first-use ordering, grey/ready states,
resets, charge availability, native duration objects, legacy fallbacks, capacity,
settings, saved data, dragging, removal and tooltip calls. These checks are not a
live-client visual/interaction test.

From the Era workspace, using Python with `lupa.lua51`:

```
python tools/classicspellstracker/test_addon.py
```

Pinned API references and the implementation boundaries are in `SOURCES.md`.

## Elmo migration

Settings are imported from ClassicSpellsTracker, ClassicCooldownTracker. Legacy settings import remains supported when previous data is available. Restart WoW after installing the new folder. Release version is unchanged.

## Client packages

Choose the `classic` package for Interface 11509 or `forever` for Interface 16001. Both are built from the same source project; the release version is unchanged. Install only the package for your client. Automated checks simulate the APIs; loading and rendering in the actual Forever client still need verification.

Modern `C_Spell` cooldown/charge duration APIs and spell usability are preferred, with legacy fallbacks. Private cooldowns remain grey with `?` until readable; private spell IDs are not learned. Resource changes wake the bar even while cooldowns are idle.
