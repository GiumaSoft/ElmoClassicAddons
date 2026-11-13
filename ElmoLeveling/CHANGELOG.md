# 2.2.0

Added two separate gold counters to the compact Sigillo panel. In bags shows
current vendor sell value for carried items of all qualities; Sold · session
records gross vendor-sale proceeds. Wallet gold, looted coins and quest money
are not vendor sales. Purchases, repairs and buybacks do not reduce this gross
sales counter. Sales of items acquired before the session are included.

Observe native buyback receipts and sale requests without invoking merchant
actions. Reconcile full/identical buyback lists and bulk sales against bag
quantities and money, including differently ordered server updates. Repeated
merchant events and existing buyback stock are not new sales. Missing evidence
is not invented: uncertain totals are marked as lower bounds.

Sales persist across reload/login. Restart clears recorded sales together with
the session clock/XP accumulator and preserves level history. Earlier sales
cannot be reconstructed. Bag prices retain pending-data lower bounds.

Increased collapsed height from 170 to 218, keeping the 368-pixel width, location,
XP caption, seal, moon/backpack footer icons and expandable level history.
Moved vendor value from Details into the compact panel; Details retains the
stack/quantity summary. Large amounts fit their own column. Equipment upgrade
formulas and purple borders are unchanged.

# 2.1.3

Leave the subzone line empty when neither the zone APIs nor the minimap provide
a distinct public name. Restored the preview's moon and backpack icons beside
rested XP and free bag slots, with room reserved before each label.

Use a single continuous ring texture per earned/rested arc when the client's
native radial progress renderer is available. Older clients retain masked
quadrants. Disabled pixel-grid snapping and texel sharpening for the complete
ring, cropped pieces and masks, matching scalable textures in TomTom, Questie
and WeakAuras. Existing XP font sizes, history and upgrade rules are preserved.

# 2.1.2

Increased the remaining-XP caption from 12 to 15 points and the seal percentage
from 11 to 13 points. Replaced the 96 solid line segments with an original
256-pixel antialiased ring texture. Native texture masks reveal continuous XP
and rested arcs using the same code on both clients.

Location uses the minimap name when the subzone API is empty or repeats the
zone. Empty, unavailable or private names do not retain a previous location;
the line explicitly displays Subzone unavailable if no distinct name is given.

# 2.1.1

Refined Sigillo into the approved compact layout. Moved the gold elapsed-time
clock into the header and removed the central statistics row. XP remaining is
shown only once below the subzone; it follows the current player XP bar and
does not reset with the session clock. Increased the subzone font from 11 to 14
and the remaining-XP caption to 12. Reduced collapsed height from 202 to 170
while retaining Details, level history, vendor bag value and upgrade rules.

# 2.1.0

Rebuilt the tracker with the Sigillo layout: a circular XP/level seal, prominent
zone and subzone, XP remaining to the next level, one gold/violet time-and-XP
line, rested XP and general-purpose free bag slots. Rounded panel artwork is
original and generated from the repository's script; the seal and crown use
native owned lines and game fonts.

Details expands vertically into time per level, vendor bag value and session
controls. Four history rows form a vertical timeline with paging, preserving
the compact panel width and top edge. The ellipsis menu opens Options > AddOns.
Added `/elvl details` and `/elvl options`.

Zone and rested changes refresh immediately. Missing/private data clears the
corresponding display without reconstructing it. Rested pools may exceed one
level; the seal preview stops at the current level boundary. Specialized bag
slots do not inflate ordinary loot space. Existing saved sessions, level
history, position, and all equipment upgrade rules are preserved.

# 2.0.1

Replaced the 1-hour and 24-hour XP counters with one compact session line:
Time HH:MM:SS · XP +earned. Gold time and purple XP sit inside a subtle bronze
inset panel. Days appear for sessions of 24 hours or longer. Reduced collapsed
panel height while preserving the expandable level-history panel.

The session counts all online idle/out-of-combat time, resumes after reload/login
and continues across hour/day boundaries. Restart resets time and XP together,
without clearing level timing or its history. Equipment upgrade rules and bag
values are unchanged. Removed the retired period counters from runtime and
saved data.

# 2.0.0

Rebuilt the dashboard around actual XP earned in fixed one-hour and 24-hour
online periods from Start/reset. Completed totals are retained beside live
progress for the next period. No averages, medians or extrapolated rates.
Idle and out-of-combat time count; offline time does not. Periods persist across
reload/login. Restarting XP preserves level timing and its history.

The expandable panel now lists time per level in days, hours, minutes and
seconds. Native played-time data can recover the current level's elapsed time;
otherwise the first interval is marked Partial. Subsequent observed levels are
recorded independently of XP resets. Missing historical intervals remain unknown.

Removed mob XP records, kill timing, kills/min, combat timers and respawn
sampling, together with their events and runtime code. Bag sell values and the
mouse-transparent purple upgrade borders remain. Equipment scoring is unchanged.

Published the complete upgrade formula, ten profile weight tables, class/talent
mappings, group-role overrides and equipment replacement rules in UPGRADE_RULES.md.
The same formulas accompany the CurseForge description and release commit.

# 1.6.7

Added an Options > AddOns panel for tracker visibility, position locking, kill history, centering and session controls. Existing character settings are preserved.

Removed former addon-name bridges, old saved-settings importers and obsolete command aliases. Packages contain only the current Elmo addon; existing Elmo character profiles are preserved.
