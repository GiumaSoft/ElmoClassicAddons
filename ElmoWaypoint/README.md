# ElmoWaypoint 1.2.0

A small waypoint addon for **Classic Era 1.15.9** and **WoW Forever 1.60.1**,
with a directional arrow, circular map/minimap pins, notes, live coordinates
and the dark and bronze Elmo style.

## Use

```text
/way 52.8 44.3
/way 52.8 44.3 Meet the group at the entrance
/way current
/way current Meet here
```

Coordinates are percentages from **0 to 100** in the player's current zone,
not the zone currently being browsed on the world map. Decimal dots and commas
are accepted (`52.8` or `52,8`). `/ewp` and `/elmowaypoint` accept the same commands.

The screen arrow turns relative to the direction your character faces and
shows straight-line distance in yards, destination coordinates and its zone.
Within eight yards it turns green and shows **Arrived**. Waypoints remain saved
until removed, so moving away resumes normal navigation.

Adding a waypoint selects it and shows the arrow. Up to 50 waypoints are saved
per character. Adding the same coordinates in the same zone selects the existing
point; an optional new note updates it. Notes use plain text, with a maximum of
255 bytes, and are saved with the coordinates.

`/way current [note]` saves the character's exact current coordinates in the
current zone, selects the point and shows its pins and arrow. It uses the
character's position regardless of which map you are browsing. If the native
position is unavailable, no point is added; previous coordinates are not reused.

## Current coordinates

A separate dark and bronze frame displays your **current zone and coordinates**,
updated while moving, even with no waypoint or with the arrow hidden. It is
visible by default, above the arrow, and can be dragged with the left mouse
button. Its screen position is saved per character, independently of the arrow.
Right-click it for **Options > AddOns > ElmoWaypoint**.

The options can show/hide the frame, lock it to allow clicks through it, and
reset its position. `/ewp coords show`, `hide`, `lock`, `unlock` and `center`
provide the same controls. Unavailable/private position displays **Position
unavailable** and placeholder coordinates until readable data returns.

## Map and minimap pins

Each saved waypoint has a **circular, numbered icon** on its zone map and parent
maps. Its minimap icon follows player movement, zoom and minimap rotation. A
destination outside the minimap's range stays on its edge while in that zone.
The selected waypoint has a gold border; other waypoints have a muted border.

Hover either icon to see the **full note in a tooltip next to the cursor**,
along with the zone and coordinates. Left-click an icon to select that saved
waypoint and restore the arrow. Hiding the arrow or minimap launcher does not
hide waypoint pins. Removing a waypoint or resetting the list removes its pins.

## Minimap and options

The draggable map-shaped launcher is separate from the circular waypoint pins
and is visible by default:

- **Left-click:** show/hide the arrow without deleting waypoints.
- **Right-click:** open **Options > AddOns > ElmoWaypoint**, including
  **Reset all waypoints**.
- **Drag:** move the minimap icon; its position is saved.

The options also provide **Next waypoint**, **Remove current waypoint**,
**Reset arrow position**, arrow visibility, minimap visibility and position
locking, plus current-coordinate controls. The arrow can be dragged when
unlocked; locking makes it click-through.
Reset affects only ElmoWaypoint's saved points, leaving other navigation addons
and Blizzard's own waypoint untouched.

## Commands

```text
/ewp                 Open options
/way current [note]  Save a waypoint at your current position
/ewp next            Cycle to the next saved waypoint
/ewp remove          Remove the current waypoint
/ewp reset           Reset all ElmoWaypoint waypoints
/ewp show            Show the arrow
/ewp hide            Hide the arrow
/ewp lock            Lock the arrow and allow clicks through it
/ewp unlock          Allow dragging the arrow
/ewp center          Restore the default arrow position
/ewp minimap show    Restore the minimap launcher
/ewp minimap hide    Hide the minimap launcher
/ewp coords show     Show current coordinates
/ewp coords hide     Hide current coordinates
/ewp coords lock     Lock the coordinates frame (click-through)
/ewp coords unlock   Allow dragging the coordinates frame
/ewp coords center   Restore its default screen position
```

`/way reset` and `/way next` also work. With no saved waypoint, the arrow stays
hidden. Settings and points survive reload/logout in **ElmoWaypointDB**.

## TomTom coexistence

TomTom is optional. When both addons are enabled, ElmoWaypoint loads after it
and registers `/way` for ElmoWaypoint through Blizzard's normal slash-command
importer. TomTom's `/tway`, `/tomtomway`, APIs, saved points and UI remain available.
Use `/ewp` for an unambiguous ElmoWaypoint command if another addon later claims
`/way`. No TomTom source or images are bundled. The independent HereBeDragons
libraries are bundled, so map/minimap pins also work without TomTom installed.

## Navigation coverage

The implementation uses native player map coordinates, world-coordinate
conversion and facing. It can continue pointing across zones on the same
native continent. Position or facing that is unavailable/private pauses the
arrow and displays the reason without discarding the waypoint. Different
continents cannot be connected by this direct bearing.

This is a straight directional pointer: terrain, walls, roads, stairs, portals
and transport routes are not planned. Availability in interiors/instances
follows the native map APIs. There is no character movement or interaction.

## Installation and validation

Extract the single **ElmoWaypoint** folder into the chosen client's
`Interface/AddOns`. Restart WoW to discover a newly installed addon, enable it
in the addon list, then try `/way 52.8 44.3` while outdoors.

The source is shared by both client packages. Original library credits and
HereBeDragons' upstream license metadata are retained in **Libs**.

Lua 5.1 tests execute the actual code and libraries with public map/UI fixtures.
They cover cardinal headings, turning, map scale, zone changes, unavailable or
private data, command registration alongside TomTom, saved notes, actual
HereBeDragons map projection, minimap zoom/rotation, pin tooltips, selection,
reset, current-position commands, moving coordinates, independently saved frame
preferences and coexistence with other addons' pins. They do not establish
live-client permissions or rendering.
See [Native API references](SOURCES.md).
