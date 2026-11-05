# ElmoLFG 1.4.0

Find groups for active quests and Classic dungeons in Classic Era 1.15.9 and
WoW Forever 1.60.1. Renamed from ClassicQuestLFG, with one shared implementation.

Open `/elmolfg` or `/elfg`, or click the minimap button. Existing `/qlfg`,
`/questlfg`, `/cqlfg` and `/classicquestlfg` commands remain available.

- Select active quests or available dungeons and choose your announcement channel.
- Completed quests, including quests ready to turn in, are removed from the list
  and selection. The journal refreshes on quest events and retries delayed data.
- The announcement preview combines current activities, available group roles
  and your editable custom message. Assign missing roles with **Group roles**.
- **Post announce** sends once. **Start announcing** starts a session with a
  configurable interval from 30 to 300 seconds and a **Stop at** group size.
- The saved **Autojoin** checkbox controls new automatic invites from `inv`
  whispers while announcing. Turning it off keeps announcements running.
  Dungeon invitations still require an available role.
- Public channel, Say and Yell repeats use a click-to-post reminder. Other
  destinations follow the client's available chat APIs. The 255-byte limit and
  posting cooldown apply to the complete outgoing message.

Announcements and invitations are stopped after login or reload. Neither
installation nor settings migration starts recruitment or sends messages.

## Installation and previous settings

Use the package for your client and extract **all three folders** into
`Interface/AddOns`: `ElmoLFG`, `ClassicQuestLFG` and `QuestLFG`. Restart WoW to
discover the new addon, then enable ElmoLFG. Keep the legacy importers enabled
for the first migration if you used an older version.

The two old folders now contain only load-on-demand saved-variable importers;
they create no windows, minimap buttons, chat handlers or timers. Their manifests
replace the previous runtime manifests, preventing a second active interface.
Existing ElmoLFG settings take precedence, then ClassicQuestLFG settings, then
QuestLFG settings. Settings are saved per character in `ElmoLFGDB` and remain
separate between Classic Era and Forever.

Questie is optional. Its chat-link format is retained when Questie is active.
Required minimap libraries are bundled, with original credits retained.
The dungeon catalogue contains Classic dungeons; it does not add
Forever-exclusive dungeons or automatically convert your group to a raid.

Source and tests: https://github.com/GiumaSoft/ElmoClassicAddons
Tests run with simulated Lua 5.1 APIs and do not send live chat or invitations.
