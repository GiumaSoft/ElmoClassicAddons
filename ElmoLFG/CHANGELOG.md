# 1.4.4

Fixed dungeon announcements failing with "Invalid escape code in chat message".
The preview keeps vertical bars between missing roles; outgoing announcements
and Edit in chat use plain slash separators. Native quest hyperlinks, Questie
quest links and the custom announcement text remain unchanged.

# 1.4.3

Quest levels now include `+` for elite/group quests and `D` for dungeon quests (for example, `[38+]` and `[38D]`). The active quest list, announcement preview and outgoing announcements share the same labels, with native quest hyperlinks and Questie chat links preserved. Both clients use native quest tags; dungeon labels take precedence over the elite flag.

# 1.4.2

Added an Options > AddOns panel with Autojoin and access to the complete LFG window. Retired the ClassicQuestLFG and QuestLFG settings importers; this package contains only ElmoLFG and preserves the current ElmoLFGDB profile. Remove the old ClassicQuestLFG and QuestLFG folders when updating an older installation.

Removed former addon-name bridges, old saved-settings importers and obsolete command aliases. Packages contain only the current Elmo addon; existing Elmo character profiles are preserved.
