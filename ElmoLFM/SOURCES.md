# Native API references

Reviewed against Blizzard's Forever UI source on 2026-11-11, through the
Gethe/wow-ui-source mirror:

- [WHO search, returned fields and WHO_LIST_UPDATE](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/FriendListDocumentation.lua):
  C_FriendList.SendWho, SetWhoToUi, GetNumWhoResults and GetWhoInfo. The result
  structure contains identity, level, class, race, guild and area; it provides
  no group-membership or recruitment-availability field.
- [Blizzard WHO window](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_GroupFinder_VanillaStyle/Mainline/WhoList.lua):
  MAX_WHOS_FROM_SERVER is 50. ElmoLFM reads a matching snapshot without
  changing the native row pool, filters, selection, handlers or visibility.
  It temporarily routes WHO results to the list, then restores routing according
  to the native WHO window's current visibility.
- [Whisper API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/ChatInfoDocumentation.lua):
  C_ChatInfo.SendChatMessage, CHAT_MSG_WHISPER and CHAT_MSG_WHISPER_INFORM.
  Only WHISPER is sent, to recipients selected by the user. The Sent check uses
  matching WHISPER_INFORM confirmation or a reply. WHISPER records the latest
  public reply for an existing contact, keyed by full name and realm, even when
  Auto-invite is disabled. Private arguments are ignored. Reply text is not saved
  in SavedVariables; displaying a reply does not extend invitation permission.
- [Invitations](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/PartyInfoDocumentation.lua):
  C_PartyInfo.CanInvite and InviteUnit, used by row right-clicks and authorized
  auto-invite replies. Direct invitations require no prior whisper and leave
  native invitation confirmations to Blizzard. No confirmation-only API, forced group
  conversion, invitation acceptance or target/character control is used.

Global WHO/chat/invite API equivalents support Classic Era builds without a
corresponding namespaced entry point. These are client API fallbacks, not former
addon importers. There are no former-addon aliases or settings migrations.

The local two-minute wait for native WHO results, one-second whisper spacing, five-minute
recontact interval and ten-minute reply authorization are addon policies, not
claims about the server's exact throttle or delivery guarantees.

The frame theme is the locally authored ElmoLFG theme, copied into this standalone
addon under the same MIT license. LibStub, CallbackHandler-1.0, LibDataBroker-1.1 and LibDBIcon-1.0 are bundled for the minimap launcher, unchanged from ElmoLFG; their source credits are retained in Libs. No textures are bundled.

ElmoLFM does not invoke SendWho. Following a reported protected-action failure on
Forever, it prepares the command using ChatFrameUtil.OpenChat or ChatFrame_OpenChat.
The player must press Enter in chat; alternatively, the displayed command can
be copied into chat manually. Only Blizzard's native handler dispatches WHO.
See [native WHO slash command](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/SlashCommands.lua)
and [chat text preparation](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameUtil.lua).
No slash-command hook, replacement handler or protected-action proxy is used.
ADDON_ACTION_BLOCKED/FORBIDDEN end waiting if a relevant action is blocked.
Simulated checks do not prove acceptance by the live client or server.

WHO_LIST_UPDATE is also consumed when the recruitment window is open and no
whisper batch is active. Import WHO list reads the same public API cache on
request, without requiring a pending search and without invoking SendWho.
Imports preserve the public WHO row order, zones and levels, including players
in other areas. Only unreadable rows and duplicate identities are omitted.
Own-group members and the player remain visible but cannot be selected for
recruitment. Cached results may predate the latest prepared command.

Link insertion uses a secure post-hook on ChatFrameUtil.InsertLink or the
Classic ChatEdit_InsertLink equivalent, limited to the visible focused editor.
Blizzard's return value and chat-window getters are unchanged.
See [native link insertion](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_ChatFrameBase/Mainline/ChatFrameUtilOverrides.lua).
Questie's tracker requires a native active chat window before linking, so the
optional adapter routes focused Shift-clicks on its own reusable tracker rows
to ElmoLFM instead of untracking. It reads TrackerLinePool.GetLine and
TrackerData.GetQuestLink, preserves the returned bracket text and delegates
other clicks to the original Questie handler. No Questie source is modified.
