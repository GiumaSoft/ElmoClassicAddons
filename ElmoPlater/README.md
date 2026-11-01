# ElmoPlater 2.0.7 prototype

A shared Classic Era / Forever nameplate prototype, with native positioning and native clicks.

- Solid-colour rectangular health bar without a gradient, health percentage, name and level.
- Red hostile or attackable neutral in combat, yellow attackable neutral out of combat, green non-attackable friendly; grey and CLAIMED for a denied tap. Red bars have white borders.
- Contrasting borders: white on red bars, near-black on yellow, green and grey bars. Selected and priority mobs have a thicker border.
- Your debuffs above each bar, including timers and stack counts. Other players and pets are excluded.
- Level colours: grey/green follow the client's creature difficulty colour, yellow for -2 through +2 levels, orange for +3 through +5, red above +5. Skull-level mobs display red `Lv. ??`. These are difficulty indicators, not a calculation of the exact XP award.
- Visual priority includes the selected target: health strictly below 20% comes first, then missing debuff, then lowest remaining HP (absolute hit points). Exactly 20% belongs to the non-critical group. Unavailable HP sorts after known HP within the same priority group; stable GUID breaks further ties.
- Among mobs you attacked in the current combat, the first mob's rectangle is twice its normal height, growing upward, with a thicker contrasting border. The selected target receives the same enlargement when it ranks first. Selection does not override the priority order. Nearby mobs you have not attacked never receive this enlargement. Your damage, missed attacks and applied harmful debuffs qualify; other players' attacks do not. Tracking clears on death, leaving the world or combat ending.
- Native hit-test points follow the custom rectangle, including its added upper half. Binding uses `CanChangeHitTestPoints()` and waits for an allowed tick; the bound rectangle then follows priority and size changes.
- No separate icon bar, targeting by GUID, global native nameplate resizing, restricted geometry measurements or hooks.

The custom rectangle follows the existing native health-bar bounds. Only the first eligible rectangle grows upward to twice that height; its name, level and debuffs follow its new top edge. Native graphics are hidden while skinned and restored on removal. Native targeting uses hit-test points anchored to this rectangle; no Lua targeting action runs on click. When permitted, cleanup restores Blizzard's normal hit-test layout using the published UI anchors, without reading restricted native geometry. WoW retains its containing nameplate bounds and engine click priority; live verification is still required for overlapping bars and the enlarged upper half.

Renamed from ClassicTarget. Restart WoW after installing the new folder, then enable ElmoPlater. Existing ClassicTarget data-only helpers can supply older settings without running the previous interface. New settings use ElmoPlaterDB and existing settings are imported once. Existing v1 global overrides are recovered once, if needed. Enemy/friendly nameplate visibility follows the game's settings.

Commands:

```
/cplater                 Status and help
/cplater debuff Rend     Prioritize a missing named debuff within each health group
/cplater debuff 772      Select a debuff by spell ID (same-name ranks count)
/cplater debuff any      Default: no personal debuff active
```

Aliases: /classicplater, /ctarget and /classictarget.

All settings and messages are English. This is a prototype: Lua 5.1 checks use simulated APIs; the redesign still needs a live reload and visual test.

## Elmo migration

Settings are imported from ClassicPlater, ClassicTarget. Legacy settings import remains supported when previous data is available. Restart WoW after installing the new folder. Release version is unchanged.

## Client packages

Choose the `classic` package for Interface 11509 or `forever` for Interface 16001. Both are built from the same source project; the release version is unchanged. Install only the package for your client. Automated checks simulate the APIs; loading and rendering in the actual Forever client still need verification.

Combat-log registration is capability-checked. If the log is restricted, visible personal harmful auras can still identify attacked mobs; damage-only attack history is unavailable. If unit identity or health is private, the addon leaves Blizzard artwork visible instead of hiding the health bar or fabricating priority. Restricted aura data is not treated as a missing debuff.
