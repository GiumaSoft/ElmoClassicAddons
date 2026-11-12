# 1.0.7

Right-click a player row to request a group invitation directly. Left-click
and checkboxes continue to select players for whispers. Direct invitations
work independently of Auto-invite and prior contact, preserve displayed replies
and do not mark a whisper as sent. They share normal group permissions,
capacity checks and pending-slot reservations with reply-triggered invitations.

# 1.0.6

Replaced the Status text column with a read-only Sent check and Last reply.
Sent is checked on matching outgoing-whisper confirmation or an incoming reply.
The latest reply is shown beside the contacted player, with full text in the
row tooltip, independently of the Auto-invite setting. Contact flags and replies
remain for the current UI session without extending invitation permissions.
Players who have replied are no longer counted as awaiting a reply.

# 1.0.5

Display the full public Blizzard WHO snapshot in native order, including other
zones and returned levels, with a visible Zone column. Own-group members remain
visible with disabled selection. Removed extra zone/level filtering.

Shift-click quest links into the focused Whisper message editor. Questie's
tracker links preserve their exact bracket format and no longer untrack the
quest when linking into ElmoLFM. Other clicks retain normal behavior. Links are
inserted at the cursor and preserved in outgoing whispers; oversized insertions
are rejected without truncation.

# 1.0.4

The open recruitment window now consumes native WHO updates without requiring a
pending prepared search. Added Import WHO list and /elfm import to read the
existing WHO cache, including after the wait expires, without dispatching WHO.
The status identifies the filters used and counts rows excluded by level, zone,
own group, unreadable data and duplication. WHO updates and imports preserve an
active whisper batch. /elfm status includes the loaded version and query.

# 1.0.3

Fixed WHO imports discarding the entire player list when a returned character
was outside the selected zone or level range. Each row is now filtered
individually, preserving valid candidates and reporting excluded rows.
The WHO limit notice remains visible when only the first fifty results arrive.

# 1.0.2

Removed addon-originated WHO dispatch after a protected-action failure was
reported on Forever. Prepare /who fills chat; the player presses Enter to execute
Blizzard's native search. A selectable command field provides manual copying.
Matching public WHO results populate the recruitment list. Waiting now lasts up
to two minutes to allow time to execute the command, and Stop cancels it.

# 1.0.1

Added a draggable minimap launcher with left-click recruitment, right-click options, saved visibility/position and an Options > AddOns visibility checkbox. Bundled the same unmodified LibDataBroker/LibDBIcon libraries used by ElmoLFG.

Aligned WHO dispatch with Blizzard's direct click-driven call and Social origin. Protected-action failures now end the pending search immediately, while response timeouts distinguish missing events from unreadable results.

# 1.0.0

Initial Classic Era and Forever release. Find online players through a manual WHO search by zone and level range, select multiple candidates, preview a custom message and send a single whisper to each selected player. Optional auto-invite accepts replies starting with `inv` or `invite` from contacted players for ten minutes. Includes group-permission and pending-slot checks, a stop control, per-character settings and Options > AddOns access. No public-channel announcements or repeating recruitment posts.
