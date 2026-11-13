# ElmoLFM 1.0.8

Local recruitment for **Classic Era 1.15.9** and **WoW Forever 1.60.1**, in the dark
and bronze Elmo style. No dependency on ElmoLFG, Questie or another addon.

Open `/elfm` (`/elmolfm`), click the minimap spyglass, or use **Options > AddOns > ElmoLFM**.

The minimap button is visible by default. Left-click opens recruitment, right-click opens options and dragging saves its position. Options includes **Show minimap button**. `/elfm minimap show` restores it; `/elfm minimap hide` hides it.

1. Enter a zone and minimum/maximum level, then click **Prepare /who**.
   For example, `Alterac Mountains`, `38`, `40` produces
   `/who z-"Alterac Mountains" 38-40`. **My zone** fills your current zone.
   The command is prepared in chat; **press Enter in chat** to execute Blizzard's
   native search. ElmoLFM does not call SendWho. The command field in ElmoLFM can
   also be selected and copied into chat manually. Blizzard's WHO results then
   populate the player list. While ElmoLFM is open, native WHO updates also
   populate it without a pending Prepare /who action.
   **Import WHO list** reads the existing WHO cache without starting another
   query. This also works after waiting
   has expired; `/elfm import` imports using the window's fields or saved filters.
   The status shows the number of returned players, unreadable rows and duplicates.
2. Select one or more players using the checkboxes. Rows show name, level,
   class, **Zone**, **Sent** and **Last reply**; hovering shows the full name,
   zone, invitation state and complete latest reply. The list keeps Blizzard's order and includes returned players in
   other areas. Zone and level fields prepare the native query; ElmoLFM applies
   no additional zone or level filtering to its results.
   **Right-click a player's row to invite them directly**, without sending a
   whisper first. **Left-click a player's row to open a whisper** in Blizzard's
   chat editor; type your message and press Enter to send it. Use the checkboxes
   for batch selection. Opening a whisper does not set the Sent check or enable
   automatic reply invitations. Direct invitations
   work with Auto-invite disabled and do not set the Sent check.
3. Edit the whisper message and review its expanded preview.
   `{zone}`, `{min}` and `{max}` are optional placeholders.
   Focus **Whisper message**, then **Shift-click a quest** to insert its link at
   the cursor. Questie's tracker links retain their exact format, for example
   `[[31] Soothing Turtle Bisque (555)]`. Links are preserved in outgoing whispers.
   An insertion that would exceed 255 bytes is rejected whole.
4. Click **Send selected**. Each selected candidate receives one whisper,
   at one-second intervals. The message is captured when you click Send.
5. With **Auto-invite** enabled, a contacted player can reply `inv` or `invite`
   (optionally followed by a role or other text) within ten minutes.

**Sent** shows a read-only green check when Blizzard confirms the outgoing
whisper, or the contacted player replies. An unconfirmed request does not set
the check. **Last reply** shows the latest incoming whisper from that player;
hover the row to read the complete text. Replies are captured even with
Auto-invite disabled, after its ten-minute window, or after Stop recruitment.
Only players contacted through ElmoLFM are tracked, using their full name/realm.
Contact flags and replies remain in memory for the current UI session and are
cleared by reload/logout. Contacting a player again starts a new reply display.

Players who were not contacted are never automatically invited. Turning
auto-invite off removes existing reply permissions; turning it back on applies
to subsequent contacts. Normal group permissions and capacity apply. Pending
invitation requests reserve slots for sixty seconds, preventing direct and
reply-triggered invitations from consuming the same final place.

**Stop recruitment** or `/elfm stop` cancels unsent whispers and reply permissions.
Existing game invitations can still be accepted. Closing the window leaves
the current recruitment running. Reloading or logging in starts no searches,
whispers or invitations; only preferences and window position are saved.

There are no General/LFG/Say announcements, automatic searches or repeating
messages. A player cannot be contacted again for five minutes. Search results
must be refreshed after five minutes. Messages exceeding the native 255-byte
limit are rejected rather than truncated.

## WHO limitations

WHO reports online characters, not willingness to join or membership in somebody
else's group. Existing members of your own group and your character remain
visible with disabled selection. Replies provide confirmation of interest.

The native WHO list is shared with Blizzard's window and other addons, and its
update event carries no request ID. ElmoLFM consumes updates while its window
is open or its prepared search is pending. Public rows are displayed in native
order, including surrounding areas and any returned levels. Only unreadable
rows and duplicate identities are omitted.
Updates from simultaneous searches cannot be identified reliably; avoid issuing
another WHO query while a prepared search is pending. Updates and imports never
replace an active whisper batch.

The list is limited to the first fifty returned characters; broad queries can
be incomplete. A limit notice suggests narrowing the query. ElmoLFM waits for
native results for up to two minutes, allowing time to execute the command.
Stop recruitment cancels waiting. Server throttling may still require a later
manual retry. Private/unavailable data is skipped. WHO handlers are not replaced
and queries are never retried automatically.

Import WHO list reads the current cache, which may be from an earlier search;
it does not refresh online status on the server. Run a fresh native /who when
needed. Closing ElmoLFM stops passive WHO imports unless its prepared search is
still pending.

The user-reported Forever client blocks addon-originated WHO dispatch even from
a click. Preparing chat text does not send a query: the player's Enter key must
execute the native command. This workflow is used in both client packages.
Live verification is still required for chat preparation and result access on
the current build; the simulated checks cannot establish client permissions.

## Installation and validation

Extract the single **ElmoLFM** folder into the selected client's `Interface/AddOns`
directory and restart WoW to discover the new addon. Use its Classic or Forever
package. Settings are saved per character in `ElmoLFMDB`.

`scripts/tests/ElmoLFM/test_addon.py` runs the actual Lua 5.1 implementation against
explicit WHO, chat, group and frame fixtures for both API variants. These are
simulated checks; live server responses, client protection and rendering require
an in-game check. Restricted whisper calls stop the batch and leave unsent
players selected for a later user click.

Source: https://github.com/GiumaSoft/ElmoClassicAddons
