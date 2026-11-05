"""Behavior checks using the same Lua 5.1 language as the Era client.

Run with Python that provides lupa: python tests/test_core.py
"""
from pathlib import Path
import os
import unittest

from lupa.lua51 import LuaRuntime

ROOT = Path(os.environ.get("ELMO_TEST_ADDON", str(Path(__file__).resolve().parents[3] / "ElmoLFG")))

WOW_STUB = r'''
now, level, sent, expanded, restored, selection = 100, 10, {}, 0, 0, 2
units = {player={name="Tester",realm="Realm",class="WARRIOR",guid="Player-0"}}
log = {
    {title="Elwynn Forest", header=true, collapsed=true},
    {title="Manhunt", id=147, level=10},
    {title="Red Linen Goods", id=83, level=9},
    {title="Stormwind", header=true, collapsed=false},
    {title="Elmore's Task", id=1097, level=15, complete=1},
}
function visible()
    local result, hidden = {}, false
    for _, row in ipairs(log) do
        if row.header then hidden = row.collapsed end
        if row.header or not hidden then result[#result+1] = row end
    end
    return result
end
function GetNumQuestLogEntries()
    local total = 0
    for _, row in ipairs(log) do if not row.header then total=total+1 end end
    return #visible(), total
end
function GetQuestLogTitle(index)
    local row = visible()[index]
    if row then return row.title, row.level or 0, nil, row.header, row.collapsed, row.complete, nil, row.id end
end
function ExpandQuestHeader(index)
    expanded=expanded+1
    for _, row in ipairs(log) do if row.header then row.collapsed=false end end
end
function CollapseQuestHeader(index) visible()[index].collapsed=true; restored=restored+1 end
function GetQuestLogSelection() return selection end
function SelectQuestLogEntry(index) selection=index end
function GetQuestLink(id) return "|cffffff00|Hquest:"..id..":10|h[Quest "..id.."]|h|r" end
function UnitLevel() return level end
function UnitClass(unit)
    local member=units[unit or "player"]
    if member then return member.class=="WARRIOR" and "Warrior" or member.class, member.class end
end
function UnitName(unit) local member=units[unit or "player"];if member then return member.name, member.realm end end
UnitFullName=UnitName
function UnitGUID(unit) local member=units[unit];return member and member.guid end
function UnitGroupRolesAssigned(unit) return units[unit] and units[unit].role or "NONE" end
function GetRealmName() return "Realm" end
function Ambiguate(name) return name:match("^[^-]+") end
function GetTime() return now end
inGuild, inGroup, inRaid, leader, assistant, memberCount = false, false, false, true, false, 0
invited, partyMembers = {}, {}
function IsInGuild() return inGuild end
function IsInGroup() return inGroup end
function IsInRaid() return inRaid end
function UnitIsGroupLeader() return leader end
function UnitIsGroupAssistant() return assistant end
function GetNumGroupMembers() return memberCount end
function UnitInParty(name) return partyMembers[name] end
function UnitInRaid() return false end
function setParty(members)
    for key in pairs(units) do if key~="player" then units[key]=nil end end
    partyMembers={}; memberCount=#members+1; inGroup=#members>0
    if not inGroup then memberCount=0 end
    for i,member in ipairs(members) do
        member.realm=member.realm or "Realm";member.class=member.class or "WARRIOR"
        member.guid=member.guid or ("Player-"..member.name.."-"..member.realm)
        units["party"..i]=member;partyMembers[member.name]=true
        partyMembers[member.name.."-"..member.realm]=true
    end
end
C_PartyInfo = {InviteUnit=function(name) invited[#invited+1]=name end}
channelId, channelName = 4, "LookingForGroup"
function GetChannelList()
    if channelId then return channelId, channelName, false end
end
function SendChatMessage(message, kind, language, target)
    sent[#sent+1] = {message=message, kind=kind, target=target}
end
ChatFrameUtil = {OpenChat=function(text) opened=text end}
'''


class ElmoLFGTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(WOW_STUB)
        self.lua.execute("A = {}")
        for name in ("Data.lua", "Core.lua", "Roles.lua"):
            self.lua.execute(ROOT.joinpath(name).read_text(), "ElmoLFG", self.lua.globals().A)
        self.lua.execute("A.InitializeDB(); A.ReadQuests(true); A.db.channel='channel:LookingForGroup'")

    def check(self, code):
        self.lua.execute(code)

    def test_closed_headers_included_and_original_state_restored(self):
        self.check('''
            assert(#A.quests==2 and A.quests[1].id==147)
            assert(log[1].collapsed==true and log[4].collapsed==false)
            assert(selection==2 and expanded==1 and restored==1)
            A.ReadQuests(false)
            assert(expanded==1, "self-generated quest log events must not start an expansion loop")
        ''')

    def test_departed_quest_removed_even_from_closed_header_before_send(self):
        self.check('''
            A.db.selected["q:147"]=true; A.db.selected["d:dm"]=true
            table.remove(log, 2)
            assert(A.SendAnnouncement())
            assert(A.db.selected["q:147"]==nil)
            assert(not sent[1].message:find("147",1,true))
            assert(sent[1].message:find("Deadmines",1,true))
        ''')

    def test_dungeon_entry_boundaries_and_no_upper_level_cutoff(self):
        self.check('''
            level=7; assert(#A.AvailableDungeons()==0)
            level=8; assert(#A.AvailableDungeons()==1)
            level=10; assert(#A.AvailableDungeons()==5)
            level=15; assert(#A.AvailableDungeons()==8)
            level=20; assert(#A.AvailableDungeons()==12)
            level=45; assert(#A.AvailableDungeons()==26)
            level=60; assert(#A.AvailableDungeons()==26)
            level=10; A.db.selected["d:ubrs"]=true
            assert(#A.SelectedActivities()==0)
        ''')

    def test_channel_renumbering_and_missing_channel_do_not_misroute(self):
        self.check('''
            A.db.selected["d:dm"]=true; channelId=7
            assert(A.SendAnnouncement())
            assert(sent[1].kind=="CHANNEL" and sent[1].target=="7")
            channelId=nil; now=200
            assert(not A.SendAnnouncement())
            assert(#sent==1)
        ''')

    def test_manual_send_cooldown_and_chat_edit_never_sends(self):
        self.check('''
            A.db.selected["d:dm"]=true
            assert(A.EditAnnouncement()); assert(#sent==0 and opened:find("/4 ",1,true)==1)
            assert(A.SendAnnouncement()); assert(not A.SendAnnouncement()); assert(#sent==1)
            now=130; assert(A.SendAnnouncement()); assert(#sent==2)
            A.db.roles={}; now=160; assert(A.SendAnnouncement())
            assert(not sent[3].message:find("(DPS)",1,true))
        ''')

    def test_all_selected_activities_preserved_and_utf8_byte_limit_enforced(self):
        self.check('''
            A.db.selected["q:147"]=true; A.db.selected["q:83"]=true
            A.quests[1].link="|Hquest:147:10|h["..string.rep("x",150).."]|h"
            A.quests[2].link="|Hquest:83:10|h["..string.rep("y",150).."]|h"
            local text, err=A.BuildMessage()
            assert(err and text:find("|Hquest:147:",1,true) and text:find("|Hquest:83:",1,true))
            assert(not text:find("Quest: [Manhunt]",1,true), "never fall back to a plain quest title")
            A.db.note=string.rep("è",120)
            text, err=A.BuildMessage(); assert(err and #text>255)
            assert(not A.SendAnnouncement() and #sent==0)
        ''')

    def test_quest_links_are_required_and_roles_are_optional_in_both_modes(self):
        self.check('''
            A.db.selected["q:147"]=true; A.db.roles={}
            local text, err=A.BuildMessage()
            assert(not err and text:find("|Hquest:147:",1,true))
            assert(text:find("LFM Quest 4/5: ",1,true)==1)
            A.db.mode="LFM"; text, err=A.BuildMessage()
            assert(not err and text:find("LFM Quest 4/5: ",1,true)==1 and not text:find("need",1,true))
            function GetQuestLink() return nil end
            assert(not A.SendAnnouncement() and #sent==0)
            assert(not A.StartAnnouncing() and not A.announcing)
        ''')

    def test_questie_shift_click_format_is_sent_while_preview_keeps_native_links(self):
        self.check('''
            Questie={started=true}
            A.db.selected["q:147"]=true; A.db.selected["q:83"]=true; A.db.roles={}
            local preview, err, bytes=A.BuildMessage()
            local wire=A.BuildMessage(true)
            assert(not err and preview:find("|Hquest:147:",1,true))
            assert(wire=="LFM Quest 4/5: [[10] Manhunt (147)][[9] Red Linen Goods (83)] - /w me inv (autojoin)")
            assert(bytes==#wire)
            assert(A.SendAnnouncement() and sent[1].message==wire)
            assert(A.EditAnnouncement() and opened=="/4 "..wire)
            assert(#sent==1, "editing must not publish another announcement")
        ''')

    def test_sent_format_is_recognized_by_the_installed_questie_chat_filter(self):
        questie_filter = ROOT.parent / "Questie/Modules/QuestLinks/ChatFilter.lua"
        if not questie_filter.is_file():
            self.skipTest("Questie's installed chat filter is not available")
        self.check('''
            Questie={started=true}
            A.db.selected["q:147"]=true; A.db.selected["q:83"]=true
            A.quests[1].name="In Defense of the King's Lands"
            A.quests[2].name="The Trogg Threat"
            local modules={
                QuestieCompat={AddMessageEventFilter=function() end},
                QuestieDB={QuestPointers={[147]=true,[83]=true}},
                QuestieLink={GetQuestHyperLink=function(_,id)
                    return "|Hquestie:"..id..":sender|h[Verified quest "..id.."]|h"
                end},
            }
            QuestieLoader={
                ImportModule=function(_,name) return assert(modules[name]) end,
                CreateModule=function() TestedChatFilter={}; return TestedChatFilter end,
            }
            function HaveQuestData() return true end
        ''')
        self.lua.execute(questie_filter.read_text())
        self.check('''
            local wire=A.BuildMessage(true)
            local chat={historyBuffer={elements={true}}}
            for _, event in ipairs({"CHAT_MSG_SAY","CHAT_MSG_CHANNEL"}) do
                local hidden, rendered=TestedChatFilter.Filter(chat,event,wire,"Tester")
                assert(hidden==false)
                assert(rendered:find("|Hquestie:147:",1,true))
                assert(rendered:find("|Hquestie:83:",1,true))
            end
        ''')

    def test_numeric_interval_accepts_every_integer_from_30_to_300_only(self):
        self.check('''
            for interval=30,300 do
                assert(A.SetAnnouncementInterval(tostring(interval)))
                assert(A.db.announcementInterval==interval)
            end
            for _, invalid in ipairs({0,29,301,1000,35.5,"abc",""}) do
                assert(not A.SetAnnouncementInterval(invalid))
                assert(A.db.announcementInterval==300)
            end
            A.InitializeDB(); assert(A.db.announcementInterval==300)
        ''')

    def test_guild_announcements_repeat_at_the_current_interval(self):
        self.check('''
            inGuild=true; A.db.channel="GUILD"; A.db.selected["d:dm"]=true
            assert(A.SetAnnouncementInterval(35)); assert(A.StartAnnouncing())
            assert(A.announcing and #sent==1 and A.nextAnnouncement==135)
            now=134; assert(A.TickAnnouncing()==nil and #sent==1)
            now=135; assert(A.TickAnnouncing() and #sent==2)
            A.SetAnnouncementInterval(60); assert(A.nextAnnouncement==195)
            now=194; assert(A.TickAnnouncing()==nil and #sent==2)
            now=195; assert(A.TickAnnouncing() and #sent==3)
            A.StopAnnouncing(); now=300; A.TickAnnouncing()
            assert(not A.announcing and #sent==3)
        ''')

    def test_public_announcements_wait_for_one_click_without_building_a_backlog(self):
        self.check('''
            A.db.selected["q:147"]=true; assert(A.StartAnnouncing()); assert(#sent==1)
            now=130; assert(A.TickAnnouncing() and A.announcementPending and #sent==1)
            now=200; assert(A.TickAnnouncing()==nil and #sent==1)
            assert(A.SendAnnouncement()); assert(#sent==2 and not A.announcementPending)
            assert(sent[2].message:find("|Hquest:147:",1,true))
            assert(A.nextAnnouncement==230)
            now=230; A.TickAnnouncing(); assert(A.announcementPending)
            A.StopAnnouncing(); assert(not A.announcementPending and A.nextAnnouncement==nil)
        ''')

    def test_channel_loss_or_change_stops_announcements(self):
        self.check('''
            A.db.selected["d:dm"]=true; assert(A.StartAnnouncing())
            channelId=nil; now=130; assert(not A.TickAnnouncing())
            assert(not A.announcing and #sent==1)
            channelId=4; now=160; assert(A.StartAnnouncing())
            A.db.channel="SAY"; assert(not A.TickAnnouncing())
            assert(not A.announcing and #sent==2)
        ''')

    def test_invalid_selection_stops_an_active_session_and_cancels_pending_post(self):
        self.check('''
            A.db.selected["q:147"]=true; assert(A.StartAnnouncing())
            now=130; A.TickAnnouncing(); assert(A.announcementPending)
            table.remove(log,2); A.ReadQuests(true)
            assert(not A.TickAnnouncing())
            assert(not A.announcing and not A.announcementPending and #sent==1)
        ''')

    def test_whisper_invites_only_while_announcing_including_pending_public_posts(self):
        self.check('''
            A.HandleWhisper("inv please", "Alice-Realm"); assert(#invited==0)
            A.db.selected["q:147"]=true; assert(A.StartAnnouncing())
            assert(A.HandleWhisper("Hi, INV please", "Alice-Realm"))
            assert(#invited==1 and invited[1]=="Alice-Realm")
            A.HandleWhisper("hello", "Bob"); A.HandleWhisper("inv", "Tester-Realm")
            now=110; A.HandleWhisper("invite", "Alice-Realm"); assert(#invited==1)
            now=130; A.TickAnnouncing(); assert(A.announcementPending)
            assert(A.HandleWhisper("invite me", "Bob")); assert(#invited==2)
            A.StopAnnouncing(); A.HandleWhisper("inv", "Charlie"); assert(#invited==2)
        ''')

    def test_whisper_invites_obey_permissions_capacity_and_existing_membership(self):
        self.check('''
            A.SetPlayerTarget(10)
            A.db.selected["q:147"]=true; assert(A.StartAnnouncing())
            inGroup=true; leader=false; memberCount=2
            assert(not A.HandleWhisper("inv", "Alice")); assert(#invited==0)
            leader=true; memberCount=5
            assert(not A.HandleWhisper("inv", "Alice")); assert(#invited==0)
            memberCount=2; partyMembers.Alice=true
            A.HandleWhisper("inv", "Alice"); assert(#invited==0)
            partyMembers.Alice=nil; assert(A.HandleWhisper("inv", "Alice")); assert(#invited==1)
        ''')

    def test_group_target_stops_announcements_and_invites_after_players_join(self):
        self.check('''
            A.SetPlayerTarget(2); A.db.selected["d:dm"]=true
            assert(A.GroupSize()==1 and A.StartAnnouncing())
            assert(A.HandleWhisper("inv heal", "Alice"))
            memberCount=2; inGroup=true
            assert(A.CheckGroupTarget()); assert(not A.announcing and not A.announcementPending)
            A.HandleWhisper("inv", "Bob"); now=200; A.TickAnnouncing()
            assert(#invited==1 and #sent==1)
            assert(not A.StartAnnouncing(), "do not post when the target is already reached")
            assert(#sent==1)
        ''')

    def test_lowering_group_target_stops_immediately_and_invalid_targets_are_rejected(self):
        self.check('''
            A.db.selected["d:dm"]=true; assert(A.StartAnnouncing())
            memberCount=3; inGroup=true
            local ok, result=A.SetPlayerTarget(3)
            assert(ok and result and not A.announcing)
            for _, value in ipairs({0,1,41,100,2.5,"abc",""}) do
                assert(not A.SetPlayerTarget(value)); assert(A.db.stopAtPlayers==3)
            end
            assert(A.SetPlayerTarget(40) and A.db.stopAtPlayers==40)
        ''')

    def test_board_active_quest_links_dungeon_aliases_and_word_boundaries(self):
        self.check('''
            A.ReceiveMessage("LFM |cffffff00|Hquest:147:10|h[Localized title]|h|r", "Alice-Realm", "General")
            A.ReceiveMessage("LFG SFK", "Bob-Realm", "LookingForGroup")
            A.ReceiveMessage("LFG Scholomance", "HighLevel", "LookingForGroup")
            A.ReceiveMessage("LFG stockades", "Stocks", "LookingForGroup")
            A.ReceiveMessage("LFG WC", "Tester-Realm", "LookingForGroup")
            A.ReceiveMessage("Selling items in WC", "Seller", "LookingForGroup")
            assert(#A.messages==2)
            level=60; assert(#A.MatchActivities("LFM stockades")==1)
            assert(A.MatchActivities("LFM stockades")[1]=="The Stockade")
        ''')

    def test_board_selection_filter_deduplication_and_expiry(self):
        self.check('''
            A.ReceiveMessage("LFG SFK", "Alice", "LookingForGroup")
            A.ReceiveMessage("LFG WC", "Bob", "LookingForGroup")
            now=110; A.ReceiveMessage("LFG SFK", "Alice", "LookingForGroup")
            assert(#A.messages==2 and A.messages[1].sender=="Alice")
            A.db.selectedOnly=true; A.db.selected["d:wc"]=true
            assert(#A.VisibleMessages()==1 and A.VisibleMessages()[1].sender=="Bob")
            now=401; assert(#A.VisibleMessages()==0)
            A.db.selectedOnly=false; assert(#A.VisibleMessages()==1)
            now=411; assert(#A.VisibleMessages()==0)
        ''')

    def test_quest_slots_follow_actual_party_capacity_and_join_leave(self):
        self.check('''
            A.db.selected["q:147"]=true
            assert(A.BuildMessage():find("LFM Quest 4/5: ",1,true)==1)
            setParty({{name="Alice"},{name="Bob"}})
            assert(A.BuildMessage():find("LFM Quest 2/5: ",1,true)==1)
            A.SetPlayerTarget(4)
            assert(A.BuildMessage():find("LFM Quest 2/5: ",1,true)==1)
            setParty({})
            assert(A.BuildMessage():find("LFM Quest 4/5: ",1,true)==1)
            A.SetPlayerTarget(2)
            assert(A.BuildMessage():find("LFM Quest 4/5: ",1,true)==1)
            inRaid=true;memberCount=10
            assert(A.BuildMessage():find("LFM Quest 30/40: ",1,true)==1)
        ''')

    def test_exact_dungeon_message_and_single_player_role(self):
        self.check('''
            A.db.selected["d:dm"]=true; A.SetPlayerRole("dps")
            assert(A.BuildMessage()=="LFM The Deadmines need 1 Tank | 1 Heal | 2 Dps - /w me inv role (tank, heal, dps)(autojoin)")
            A.SetPlayerRole("tank")
            assert(A.RoleText()=="Tank" and not A.db.roles.DPS)
            assert(A.BuildMessage():find("need 1 Heal | 3 Dps",1,true))
            A.SetPlayerRole("heal")
            assert(A.RoleText()=="Healer" and not A.db.roles.Tank)
            assert(A.BuildMessage():find("need 1 Tank | 3 Dps",1,true))
        ''')

    def test_mixed_activities_keep_both_formats_and_all_links(self):
        self.check('''
            Questie={started=true}
            A.db.selected["q:147"]=true;A.db.selected["q:83"]=true;A.db.selected["d:dm"]=true
            local message,err=A.BuildMessage(true)
            assert(not err and message:find("LFM Quest 4/5: [[10] Manhunt (147)][[9] Red Linen Goods (83)]; The Deadmines need 1 Tank | 1 Heal | 2 Dps",1,true)==1)
            local suffix=" - /w me inv role (tank, heal, dps)(autojoin)"
            assert(message:sub(-#suffix)==suffix)
        ''')

    def test_role_counts_use_native_roles_and_update_when_members_leave(self):
        self.check('''
            A.db.selected["d:dm"]=true;A.SetPlayerRole("dps")
            setParty({{name="Alice",role="TANK"},{name="Bob",role="HEALER"}})
            assert(A.DungeonRoleText()=="2 Dps")
            setParty({{name="Alice",role="TANK"}})
            assert(A.DungeonRoleText()=="1 Heal/2 Dps")
            setParty({})
            assert(A.DungeonRoleText()=="1 Tank/1 Heal/2 Dps")
        ''')

    def test_unknown_hybrid_roles_are_never_assumed_to_be_damage(self):
        self.check('''
            A.db.selected["d:dm"]=true;A.SetPlayerRole("tank")
            setParty({{name="Priest",class="PRIEST"},{name="Mage",class="MAGE"}})
            assert(A.DungeonRoleText()=="2 slots (assign group roles)")
            local group=A.GroupComposition()
            assert(group.have.Tank==1 and group.have.DPS==1 and group.unknown==1)
            assert(A.SetMemberRole(group.roster[2].key,"heal"))
            assert(A.DungeonRoleText()=="2 Dps")
            assert(A.SetMemberRole(group.roster[2].key,"Auto"))
            assert(A.GroupComposition().unknown==1)
            A.SetPlayerRole(nil)
            assert(A.BuildMessage():find("need 2 slots (assign group roles)",1,true))
        ''')

    def test_classic_without_native_role_api_uses_declared_roles(self):
        self.check('''
            UnitGroupRolesAssigned=nil
            A.db.selected["d:dm"]=true;A.SetPlayerRole("tank")
            setParty({{name="Priest",class="PRIEST"}})
            assert(A.GroupComposition().unknown==1)
            assert(A.RecordMemberRole("Priest-Realm","heal"))
            assert(A.DungeonRoleText()=="3 Dps")
        ''')

    def test_conflicting_roles_do_not_advertise_more_places_than_are_free(self):
        self.check('''
            A.db.selected["d:dm"]=true;A.SetPlayerRole("tank")
            setParty({{name="OtherTank",role="TANK"}})
            assert(A.DungeonRoleText()=="3 slots (check group roles)")
        ''')

    def test_dungeon_invites_require_one_recognizable_role(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            for _,message in ipairs({"inv","inv thanks","inv tank heal","inv tank dps","inv mistank"}) do
                assert(not A.HandleWhisper(message,"Alice"))
            end
            assert(#invited==0)
            assert(A.HandleWhisper("Hi! INV role (HEALER)","Alice"))
            assert(#invited==1 and A.pendingRoles[A.NameKey("Alice")].role=="Healer")
            assert(#sent==1,"no automatic whisper replies")
        ''')

    def test_whisper_roles_count_only_after_joining_and_are_not_double_counted(self):
        self.check('''
            A.db.selected["d:dm"]=true;A.SetPlayerRole("dps");assert(A.StartAnnouncing())
            assert(A.HandleWhisper("inv tank","Alice-Realm"))
            assert(A.DungeonRoleText()=="1 Tank/1 Heal/2 Dps")
            setParty({{name="Alice"}})
            assert(A.DungeonRoleText()=="1 Heal/2 Dps")
            assert(A.pendingRoles[A.NameKey("Alice")]==nil)
            assert(A.HandleWhisper("inv heal","Bob"))
            setParty({{name="Alice"},{name="Bob",class="PRIEST"}})
            assert(A.DungeonRoleText()=="2 Dps")
            A.SyncGroupRoles();A.SyncGroupRoles()
            local group=A.GroupComposition()
            assert(group.have.Tank==1 and group.have.Healer==1 and group.have.DPS==1)
            setParty({{name="Bob",class="PRIEST"}})
            assert(A.DungeonRoleText()=="1 Tank/2 Dps")
        ''')

    def test_pending_invites_reserve_roles_and_expire(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            assert(A.HandleWhisper("inv tank","Alice"))
            assert(not A.HandleWhisper("inv tank","Bob") and #invited==1)
            now=221
            assert(A.HandleWhisper("inv tank","Bob") and #invited==2)
            assert(A.pendingRoles[A.NameKey("Alice")]==nil)
        ''')

    def test_pending_role_corrections_and_realm_aliases_do_not_duplicate_invites(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            assert(A.HandleWhisper("inv tank","Alice"))
            now=105
            assert(A.HandleWhisper("inv heal","Alice-Realm"))
            assert(#invited==1 and A.pendingRoles[A.NameKey("Alice")].role=="Healer")
            assert(A.HandleWhisper("inv tank","Bob"))
            assert(not A.HandleWhisper("inv heal","OtherHeal"))
            A.HandleWhisper("inv heal","ALICE-Realm")
            assert(#invited==2)
        ''')

    def test_pending_invites_do_not_overfill_damage_or_group_capacity(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            assert(A.HandleWhisper("inv dps","Alice"));assert(A.HandleWhisper("inv dps","Bob"))
            assert(not A.HandleWhisper("inv dps","Charlie"))
            assert(A.HandleWhisper("inv tank","Tank"));assert(A.HandleWhisper("inv heal","Heal"))
            assert(not A.HandleWhisper("inv heal","OtherHeal") and #invited==4)
        ''')

    def test_existing_members_can_correct_their_role_without_another_invite(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            setParty({{name="Priest",class="PRIEST"}})
            assert(A.HandleWhisper("inv heal","Priest-Realm"))
            assert(#invited==0 and A.DungeonRoleText()=="1 Tank/2 Dps")
            A.StopAnnouncing();A.HandleWhisper("inv tank","Priest-Realm")
            assert(A.GroupComposition().have.Healer==1)
        ''')

    def test_member_departure_clears_old_role_and_rejoin_needs_confirmation(self):
        self.check('''
            A.db.selected["d:dm"]=true
            setParty({{name="Alice"}});assert(A.RecordMemberRole("Alice","tank"))
            assert(A.DungeonRoleText()=="1 Heal/2 Dps")
            setParty({});A.SyncGroupRoles()
            setParty({{name="Alice"}})
            assert(A.GroupComposition().unknown==1)
        ''')

    def test_full_realm_names_keep_different_players_separate(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            assert(A.IsSelf("Tester-Realm") and not A.IsSelf("Tester-Other"))
            assert(A.HandleWhisper("inv tank","Tester-Other"))
            assert(A.HandleWhisper("inv heal","Alice-Other"))
            setParty({{name="Tester",realm="Other"},{name="Alice",realm="Other"}})
            assert(A.DungeonRoleText()=="2 Dps")
        ''')

    def test_failed_invitation_does_not_reserve_a_role(self):
        self.check('''
            A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            C_PartyInfo.InviteUnit=function()error("blocked")end
            assert(not A.HandleWhisper("inv tank","Alice"))
            assert(next(A.pendingRoles)==nil)
        ''')

    def test_dungeon_recruitment_stops_at_five_even_with_larger_quest_target(self):
        self.check('''
            A.SetPlayerTarget(10);A.db.selected["d:dm"]=true;assert(A.StartAnnouncing())
            setParty({{name="A",role="TANK"},{name="B",role="HEALER"},{name="C",class="MAGE"},{name="D",class="ROGUE"}})
            assert(A.CheckGroupTarget() and not A.announcing)
            assert(not A.StartAnnouncing() and #sent==1)
        ''')

    def test_old_lfm_needed_roles_are_not_mistaken_for_the_players_role(self):
        self.check('''
            ElmoLFGDB={mode="LFM",roles={Tank=true},selected={}}
            A.InitializeDB()
            assert(A.db.playerRole==nil and next(A.db.roles)==nil)
            A.SetPlayerRole("heal");A.InitializeDB()
            assert(A.db.playerRole=="Healer" and A.db.roles.Healer)
        ''')

    def test_every_addon_file_parses_as_lua51(self):
        for path in ROOT.glob("*.lua"):
            result = self.lua.eval("loadstring")(path.read_text(), str(path))
            self.assertFalse(isinstance(result, tuple), result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
