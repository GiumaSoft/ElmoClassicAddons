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
