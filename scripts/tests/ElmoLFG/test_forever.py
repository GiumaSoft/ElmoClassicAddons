"""Forever quest-log compatibility; API calls are simulated, never sent to WoW."""
import unittest
from lupa.lua51 import LuaRuntime
from test_core import ROOT, WOW_STUB
from test_ui import FRAMES

FOREVER_STUB = r'''
local link = GetQuestLink
C_QuestLog = {
    GetNumQuestLogEntries = GetNumQuestLogEntries,
    GetInfo = function(index)
        local row = log[index]
        if row then return {title=row.title, level=row.level, questID=row.id,
            isHeader=row.header, isCollapsed=row.collapsed} end
    end,
    GetQuestLink = link,
    GetLogIndexForQuestID = function(id)
        for index, row in ipairs(log) do if row.id==id then return index end end
    end,
    GetQuestTagInfo = function(id)
        for _, row in ipairs(log)do
            if row.id==id then return {tagName=row.tag or 'Group',tagID=row.tagID,isElite=row.elite} end
        end
    end,
    IsComplete = function(id)
        for _, row in ipairs(log) do if row.id==id then return row.complete==1 end end
        return false
    end,
    IsFailed = function(id)
        for _, row in ipairs(log) do if row.id==id then return row.complete==-1 end end
        return false
    end,
}
GetNumQuestLogEntries, GetQuestLogTitle, GetQuestLink = nil, nil, nil
GetQuestLogSelection, SelectQuestLogEntry, ExpandQuestHeader, CollapseQuestHeader = nil, nil, nil, nil
C_ChatInfo = {SendChatMessage=SendChatMessage}
SendChatMessage = nil
'''


class ForeverTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(WOW_STUB + FOREVER_STUB)
        self.lua.execute('A={}')
        for name in ('Data.lua', 'Core.lua', 'Roles.lua'):
            self.lua.execute((ROOT/name).read_text(), 'ElmoLFG', self.lua.globals().A)
        self.lua.execute("A.InitializeDB(); A.ReadQuests(true); A.db.channel='channel:LookingForGroup'")

    def test_dungeon_send_avoids_raw_role_pipes_and_preserves_native_quest_links(self):
        self.lua.execute("""
        level=37;A.db.selected={['d:smcath']=true};A.SetPlayerRole('dps')
        setParty({{name='Tank',role='TANK'}})
        A.SetAnnouncementText('- /w me inv (autojoin)')
        local original=C_ChatInfo.SendChatMessage
        C_ChatInfo.SendChatMessage=function(message,...)
            assert(not message:find('| ',1,true),'SendChatMessage(): Invalid escape code in chat message')
            return original(message,...)
        end
        local ok,reason=A.SendAnnouncement();assert(ok,reason)
        assert(sent[1].message=='LFM Scarlet Monastery - Cathedral need 1 Heal / 2 Dps - /w me inv (autojoin)')
        now=130;A.db.selected['q:147']=true
        A.SetAnnouncementText(C_QuestLog.GetQuestLink(147)..' ready')
        ok,reason=A.SendAnnouncement();assert(ok,reason)
        local wire,err,bytes=A.BuildMessage(true)
        assert(not err and bytes==#wire and sent[2].message==wire)
        assert(wire:find('|Hquest:147:10|h',1,true) and wire:find('need 1 Heal / 2 Dps',1,true))
        """)

    def test_native_tag_ids_label_elite_and_dungeon_quests_in_both_link_formats(self):
        self.lua.execute('''
        log[2].level=38;log[2].tagID=1;log[2].tag='Groupe'
        log[3].level=38;log[3].tagID=81;log[3].tag='Donjon';log[3].elite=true
        A.ReadQuests(false);A.db.selected={['q:147']=true,['q:83']=true}
        assert(A.QuestLevel(A.quests[1])=='38+' and A.QuestLevel(A.quests[2])=='38D')
        for _,questie in ipairs({false,true})do
            Questie=questie and {started=true} or nil
            local preview,err,bytes=A.BuildMessage()
            local wire=A.BuildMessage(true)
            assert(not err and bytes==#wire)
            assert(preview:find('[38+]',1,true) and preview:find('[38D]',1,true))
            assert(wire:find('[38+]',1,true) and wire:find('[38D]',1,true))
        end
        log[2].tagID=nil;log[2].elite=true;A.ReadQuests(false)
        assert(A.QuestLevel(A.quests[1])=='38+')
        log[2].elite=false;log[2].tag='Unknown';A.ReadQuests(false)
        assert(A.QuestLevel(A.quests[1])=='38')
        ''')

    def test_collapsed_quests_need_no_header_or_selection_changes(self):
        self.lua.execute('''
        assert(A.questReady and #A.quests==2 and A.quests[1].id==147)
        assert(A.quests[1].zone=='Elwynn Forest' and A.quests[2].zone=='Elwynn Forest')
        assert(log[1].collapsed and selection==2 and expanded==0 and restored==0)
        A.ReadQuests(false); assert(#A.quests==2 and expanded==0)
        ''')

    def test_forever_ids_completion_failure_and_native_links(self):
        self.lua.execute('''
        log[2].id=96393; log[2].complete=-1
        A.ReadQuests(false)
        assert(A.quests[1].id==96393 and A.quests[1].complete==-1)
        assert(A.quests[1].tag=='Group' and #A.quests==2)
        assert(A.quests[1].link:find('|Hquest:96393:',1,true))
        ''')

    def test_modern_log_with_global_quest_link_api(self):
        self.lua.execute('''
        GetQuestLink=C_QuestLog.GetQuestLink; C_QuestLog.GetQuestLink=nil
        A.quests={}; A.ReadQuests(true)
        assert(A.questReady and #A.quests==2)
        assert(A.quests[1].link:find('|Hquest:147:',1,true))
        ''')

    def test_incomplete_log_retains_last_snapshot_and_selections(self):
        self.lua.execute('''
        A.db.selected['q:147']=true
        local getter=C_QuestLog.GetInfo
        C_QuestLog.GetInfo=function(index) if index~=3 then return getter(index) end end
        local quests=A.ReadQuests(true)
        assert(not A.questReady and #quests==2 and A.db.selected['q:147'])
        assert(not A.SendAnnouncement() and #sent==0)
        ''')

    def test_modern_entry_counts_do_not_discard_readable_quests(self):
        self.lua.execute('''
        for _, total in ipairs({0, 2, 4, 40}) do
            C_QuestLog.GetNumQuestLogEntries=function() return 2, total end
            A.quests={}
            A.ReadQuests(true)
            assert(A.questReady and #A.quests==2,
                'The visible/aggregate count must not gate the modern journal')
        end
        ''')

    def test_unloaded_title_retains_the_snapshot_until_data_arrives(self):
        self.lua.execute('''
        A.db.selected['q:147']=true
        log[2].title=nil; A.ReadQuests(true)
        assert(not A.questReady and #A.quests==2 and A.db.selected['q:147'])
        log[2].title='Manhunt'; A.ReadQuests(true)
        assert(A.questReady and #A.quests==2)
        ''')

    def test_removed_quests_are_pruned_before_namespaced_chat_send(self):
        self.lua.execute('''
        A.db.selected['q:147']=true; A.db.selected['d:dm']=true
        table.remove(log,2)
        assert(A.SendAnnouncement())
        assert(A.db.selected['q:147']==nil and sent[1].message:find('Deadmines',1,true))
        assert(not sent[1].message:find('147',1,true))
        ''')

    def test_questie_wire_format_supports_forever_quests(self):
        self.lua.execute('''
        Questie={started=true}; log[2].id=96393; A.ReadQuests(true)
        A.db.selected['q:96393']=true
        assert(A.SendAnnouncement())
        assert(sent[1].message:find('[[10+] Manhunt (96393)]',1,true))
        ''')

    def test_window_loads_and_refreshes_with_only_modern_quest_apis(self):
        self.lua.execute(FRAMES)
        self.lua.execute('''
        GetQuestDifficultyColor, QuestDifficultyColors = nil, nil
        C_PlayerInfo={GetContentDifficultyQuestForPlayer=function(id) assert(id>0); return 2 end}
        function GetDifficultyColor(difficulty) assert(difficulty==2); return {r=1,g=1,b=0} end
        ''')
        for name in ('Theme.lua', 'UI.lua'):
            self.lua.execute((ROOT/name).read_text(), 'ElmoLFG', self.lua.globals().A)
        self.lua.execute('''
        fire('ADDON_LOADED','ElmoLFG'); A.Toggle()
        assert(ElmoLFGFrame:IsShown() and A.questReady and #A.quests==2)
        fire('QUEST_LOG_UPDATE')
        assert(log[1].collapsed and expanded==0 and restored==0 and #sent==0)
        ''')

    def test_completed_quests_are_hidden_and_deselected_until_incomplete_again(self):
        self.lua.execute('''
        A.db.selected['q:1097']=true; A.db.selected['q:147']=true
        A.ReadQuests(false)
        assert(#A.quests==2 and not A.db.selected['q:1097'])
        log[2].complete=1; A.ReadQuests(false)
        assert(#A.quests==1 and A.quests[1].id==83 and not A.db.selected['q:147'])
        log[2].complete=nil; A.ReadQuests(false)
        assert(#A.quests==2 and A.quests[1].id==147 and not A.db.selected['q:147'])
        log[2].complete=1; log[3].complete=1; A.ReadQuests(false)
        assert(A.questReady and #A.quests==0)
        ''')

    def load_window(self):
        self.lua.execute(FRAMES)
        for name in ('Theme.lua', 'UI.lua'):
            self.lua.execute((ROOT/name).read_text(), 'ElmoLFG', self.lua.globals().A)
        self.lua.execute("fire('ADDON_LOADED','ElmoLFG')")

    def test_timer_recovers_incomplete_snapshot_after_the_last_quest_event(self):
        self.load_window()
        self.lua.execute('''
        A.Toggle(); A.db.selected['q:147']=true
        log[2].title=nil; fire('QUEST_LOG_UPDATE')
        assert(not A.questReady and A.db.selected['q:147'])
        log[2].title='Loaded quest title'; ticker()
        assert(A.questReady and A.quests[1].name=='Loaded quest title')
        assert(A.db.selected['q:147'] and #sent==0)
        -- The background retry also works while the window is closed.
        ElmoLFGFrame:Hide()
        log[2].title=nil; fire('QUEST_LOG_UPDATE'); assert(not A.questReady)
        log[2].title='Loaded while hidden'; ticker()
        assert(A.questReady and A.quests[1].name=='Loaded while hidden' and #sent==0)
        ''')

    def test_open_window_refreshes_accept_complete_and_abandon_without_another_event(self):
        self.load_window()
        self.lua.execute('''
        A.Toggle()
        log[#log+1]={title='New quest',id=96393,level=10}; ticker()
        assert(#A.quests==3 and A.quests[3].id==96393)
        A.db.selected['q:96393']=true; log[#log].complete=1; ticker()
        assert(#A.quests==2 and not A.db.selected['q:96393'])
        A.db.selected['q:147']=true; table.remove(log,2); ticker()
        assert(#A.quests==1 and A.quests[1].id==83 and not A.db.selected['q:147'])
        local visible=0
        for _,f in ipairs(frames)do
            if f.data and f.data.kind~='dungeon' and f.kind=='Button' and f:IsShown() then
                assert(f.data.complete~=1); visible=visible+1
            end
        end
        assert(visible==1 and #sent==0)
        ''')

    def test_specific_quest_events_refresh_a_hidden_window(self):
        self.load_window()
        self.lua.execute('''
        assert(not ElmoLFGFrame:IsShown())
        log[#log+1]={title='Accepted quest',id=96393,level=10}
        fire('QUEST_ACCEPTED',96393)
        assert(#A.quests==3 and A.quests[3].id==96393)
        A.db.selected['q:96393']=true
        log[#log].complete=1; fire('QUEST_AUTOCOMPLETE',96393)
        assert(#A.quests==2 and not A.db.selected['q:96393'])
        table.remove(log); fire('QUEST_TURNED_IN',96393)
        A.db.selected['q:147']=true; table.remove(log,2); fire('QUEST_REMOVED',147)
        assert(#A.quests==1 and A.quests[1].id==83 and not A.db.selected['q:147'])
        assert(#sent==0)
        ''')


if __name__ == '__main__':
    unittest.main(verbosity=2)
