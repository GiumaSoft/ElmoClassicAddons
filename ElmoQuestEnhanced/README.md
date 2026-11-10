# ElmoQuestEnhanced 1.2.1

Reports your quest completions and optional kill/item progress to your current group.
Open **Options > AddOns > ElmoQuestEnhanced**, or type `/eqe` or
`/elmoquestenhanced`, to configure three independent checkboxes:

- **Report completed quests** (on by default): one `Quest complete: <quest name>`
  message when a quest becomes complete.
- **Report completed objectives** (on by default): for quests with multiple
  objectives, one `Objective complete: <native objective text> (<quest name>)`
  message per completed objective.
- **Report remaining objectives (kills/items)** (off by default): each observed
  increase in a native kill/item count produces `Objective progress: <native
  objective text> (<number> remaining) (<quest name>)`. For example, collecting
  a second item out of five reports `2/5` and `3 remaining`. Decreasing counts
  are silent; collecting the items again can report new progress. A completed
  objective report replaces a progress report for that same completion when
  both options are enabled; progress alone can report `0 remaining`.

Settings are saved per character and apply as soon as the checkbox changes.
The destination is party, raid or instance-group chat, as appropriate. Disabled
reports are consumed without replaying them when reenabled. Questie is not required.
Accepted/abandoned quests, unrelated loot and turn-in events are not announced.
Existing completions and counts on login/reload are a silent baseline.
Solo progress is consumed without sending or replaying messages on group join.
Each objective is identified by quest ID and its original native index, and is
reported once per acceptance. A newly accepted quest that is immediately ready
can report its completion. Missing/private data is retried rather than inferred
from counters alone. Messages are English; names and objective wording come
from the client's quest log. Text stays within the 255-byte chat limit.

Extract the single ElmoQuestEnhanced folder into Interface/AddOns. Former
compatibility folders are no longer included; current ElmoQuestEnhancedDB
settings are preserved.

Shared source supports Classic Era 11509 and Forever 16001. The Era reader
temporarily expands collapsed quest headers only when the journal's visible
structure changes, restoring header states and selection before returning.
The Forever reader uses C_QuestLog directly. A half-second scan also retries
quest data that arrives after the last event. No combat log is accessed.

References: [Questie's announcements](https://github.com/Questie/Questie/blob/master/Modules/QuestieAnnounce.lua),
[Forever quest API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua),
[Classic Era quest API](https://github.com/Gethe/wow-ui-source/blob/classic_era/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua),
[Blizzard Settings registration](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_Settings_Shared/Blizzard_Settings.lua).
This is an independent implementation; no Questie code or assets are bundled.

Validation uses Lua 5.1 with simulated APIs in
`scripts/tests/ElmoQuestEnhanced/test_addon.py`. No live group messages are sent by
the tests. In-game confirmation remains separate from these checks.
