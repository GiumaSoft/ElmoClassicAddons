# 1.2.0

Added `/way current [note]` to save an exact waypoint at the character's current
position. It uses the player's zone rather than the map being browsed, and
does not save stale coordinates when position data is unavailable.

Added a movable current-coordinate frame with the zone name and live X/Y
percentages. It works independently of the arrow and saved points, retains its
own screen position, and has visibility, click-through locking and position
reset in Options > AddOns and `/ewp coords` commands. The arrow and coordinate
frame share one public position sample per update. Existing points and pins
are preserved.

# 1.1.0

Added circular, numbered waypoint pins on the world map and minimap. The active
waypoint has a gold border. Hover either pin to read its note next to the mouse;
left-click to select the waypoint and show the arrow again. Pins remain visible
when the arrow or launcher is hidden, and are removed when their waypoint is
deleted. Notes now retain up to 255 bytes, preserving existing saved labels.

Bundled unmodified HereBeDragons 2.18 libraries for map projection, parent maps,
minimap zoom, rotation and edge positioning. Pins work without TomTom. Reset
removes only ElmoWaypoint's pins, and pin frames are reused.

# 1.0.0

Initial Classic Era and Forever release. `/way x y [label]` creates and selects
a waypoint in the current player zone. A movable Elmo-style arrow shows its
relative direction, distance in yards, coordinates and zone; it turns green on
arrival. Up to 50 points are saved per character and remain until removed.

Added the minimap map icon: left-click toggles the arrow, right-click opens
options with Reset all waypoints, and dragging saves the icon position. Native
Options > AddOns also provides next/remove, visibility, locking and position reset.

Supports decimal dots/commas, `/ewp` and `/elmowaypoint`. Uses the normal Blizzard
slash importer to register `/way` after TomTom while retaining its alternate
commands and handlers. Missing/private map data pauses navigation. No external
waypoint library, character movement or path planning is used.
