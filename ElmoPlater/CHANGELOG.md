# 2.3.2

On WoW Forever, Blizzard protects enemy health values during combat. ElmoPlater
can still display health bars and percentages through Blizzard-supported display
APIs, but addon code cannot inspect or compare those protected values to rank
mobs by health. For this reason, the rule system, custom target-priority ordering
and experimental health-based layers have been removed. Nameplates, health
percentages, personal debuffs and quest-kill markers remain available. This
simplification applies to both clients because they share the same codebase.

Moved the difficulty-coloured level into a separate, slightly rounded square on the right of the health bar. Kept the fixed 2x base bar height, personal debuffs with countdowns and native quest kill markers. /eplater now opens Options > AddOns.

Removed former addon-name bridges, old saved-settings importers and obsolete command aliases. Packages contain only the current Elmo addon; existing Elmo character profiles are preserved.
