# ElmoQuestReport 1.0.0

Reports only your quest completions to your current group:

- A completed quest produces one `Quest complete: <quest name>` message.
- For quests with multiple objectives, each completed objective also produces
  one `Objective complete: <native objective text> (<quest name>)` message.
- The destination is party, raid or instance-group chat, as appropriate.

There is no UI, configuration, command, saved profile or Questie dependency.
It does not announce ordinary progress, accepted/abandoned quests, loot or turn-in
events. Completed quests already present on login/reload are a silent baseline.
Solo progress is consumed without sending or replaying messages on group join.
Each objective is identified by quest ID and its original native index, and is
reported once per acceptance. A newly accepted quest that is immediately ready
can report its completion. Missing/private data is retried rather than inferred
from counters alone. Messages are English; names and objective wording come
from the client's quest log. Text stays within the 255-byte chat limit.

Install the package for your client in `Interface/AddOns/ElmoQuestReport` and
restart the client to discover the new addon. Enable it in the AddOns list.
If Questie's own announcements are enabled, disable those options to avoid
receiving the same completion from both addons. Questie settings are not changed.

Shared source supports Classic Era 11509 and Forever 16001. The Era reader
temporarily expands collapsed quest headers only when the journal's visible
structure changes, restoring header states and selection before returning.
The Forever reader uses C_QuestLog directly. A half-second scan also retries
quest data that arrives after the last event. No combat log is accessed.

References: [Questie's announcements](https://github.com/Questie/Questie/blob/master/Modules/QuestieAnnounce.lua),
[Forever quest API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua),
[Classic Era quest API](https://github.com/Gethe/wow-ui-source/blob/classic_era/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua).
This is an independent implementation; no Questie code or assets are bundled.

Validation uses Lua 5.1 with simulated APIs in
`scripts/tests/ElmoQuestReport/test_addon.py`. No live group messages are sent by
the tests. In-game confirmation remains separate from these checks.
