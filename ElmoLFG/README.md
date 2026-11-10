# ElmoLFG 1.4.1

## Options menu

Open **Options > AddOns > ElmoLFG** for Autojoin and a button opening the complete LFG window. Activity selection, channels, announcement text, interval, group size and roles remain in that window. Opening settings never starts recruitment or sends an announcement.

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
installation nor opening settings starts recruitment or sends messages.

## Installation and settings

Use the package for your client and extract the single **ElmoLFG** folder into
`Interface/AddOns`. The former `ClassicQuestLFG` and `QuestLFG` settings importers
are retired and are no longer included or loaded. Remove those obsolete addon
folders when updating an older installation.

Current settings remain in the per-character `ElmoLFGDB`, separately for Classic
Era and Forever. Old saved-variable files are not loaded or imported. Opening
the addon or its options does not start recruitment or send messages.

Questie is optional. Its chat-link format is retained when Questie is active.
Required minimap libraries are bundled, with original credits retained.
The dungeon catalogue contains Classic dungeons; it does not add
Forever-exclusive dungeons or automatically convert your group to a raid.

Source and tests: https://github.com/GiumaSoft/ElmoClassicAddons
Tests run with simulated Lua 5.1 APIs and do not send live chat or invitations.
