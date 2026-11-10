"""Actual addon Lua with simulated Era/Forever APIs; never sends in-game chat."""
from pathlib import Path
import os
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[3]
ADDON = Path(os.environ.get('ELMO_TEST_ADDON', ROOT / 'ElmoQuestEnhanced'))
STUB = r'''
frames,sent,quests,log={},{},{},{}
SlashCmdList={};settingsRegistry={};settingsCategories={};settingsCheckboxes={}
Settings={VarType={Boolean='boolean'}}
function Settings.RegisterVerticalLayoutCategory(name)
 local category={name=name,id=9001}
 function category:GetID()return self.id end
 settingsCategories[#settingsCategories+1]=category;return category
end
function Settings.RegisterAddOnSetting(category,variable,key,db,kind,label,default)
 assert(kind=='boolean')
 local setting={category=category,variable=variable,key=key,db=db,label=label,default=default}
 function setting:GetValue()return self.db[self.key]end
 function setting:SetValue(value)assert(type(value)=='boolean');self.db[self.key]=value end
 settingsRegistry[key]=setting;return setting
end
function Settings.CreateCheckbox(category,setting,tooltip)
 settingsCheckboxes[#settingsCheckboxes+1]={category=category,setting=setting,tooltip=tooltip}
end
function Settings.RegisterAddOnCategory(category)category.registered=true end
function Settings.OpenToCategory(id)openedCategory=id end
group='PARTY';LE_PARTY_CATEGORY_INSTANCE=2;selection=2;expanded=0;restored=0
function CreateFrame()
 local f={scripts={},events={}}
 function f:SetScript(k,v)self.scripts[k]=v end
 function f:RegisterEvent(e)self.events[e]=true end
 frames[#frames+1]=f;return f
end
function IsLoggedIn()return false end
function IsInGroup(category)return category==2 and group=='INSTANCE_CHAT' or category==nil and group~=false end
function IsInRaid()return group=='RAID' end
function SendChatMessage(message,channel)
 if failSend then error('Temporary send failure')end
 sent[#sent+1]={message=message,channel=channel}
end
function fire(event,...)
 for _,f in ipairs(frames)do if f.events[event]then f.scripts.OnEvent(f,event,...)end end
end
function tick()
 for _,f in ipairs(frames)do f.scripts.OnUpdate(f,.5)end
end
function update()fire('QUEST_LOG_UPDATE');tick()end
function add(id,title,count)
 local q={title=title,complete=false,objectives={}}
 for i=1,count do q.objectives[i]={text='Objective '..i..': 0/2',type='item',finished=false,numFulfilled=0,numRequired=2}end
 quests[id]=q;log[#log+1]={id=id};return q
end
function finish(id,index)
 local o=quests[id].objectives[index];o.finished=true;o.numFulfilled=2;o.text='Objective '..index..': 2/2'
end
function progress(id,index,count)
 local o=quests[id].objectives[index]
 o.numFulfilled=count;o.text='Objective '..index..': '..count..'/'..o.numRequired
end
C_QuestLog={
 GetQuestObjectives=function(id)return quests[id] and quests[id].objectives end,
 IsComplete=function(id)return quests[id] and quests[id].complete end,
 GetInfo=function(index)
  local row=log[index];if not row then return end
  if row.header then return {title=row.title,isHeader=true,isCollapsed=row.closed}end
  return {title=quests[row.id].title,questID=row.id,isHeader=false}
 end,
}
function IsQuestComplete(id)return quests[id] and quests[id].complete end
function visible()
 local result,hidden={},false
 for _,r in ipairs(log)do
  if r.header then hidden=r.closed end
  if r.header or not hidden then result[#result+1]=r end
 end
 return result
end
function GetNumQuestLogEntries()
 local count=0;for _,r in ipairs(log)do if r.id then count=count+1 end end
 return #visible(),count
end
function GetQuestLogTitle(index)
 local row=visible()[index];if not row then return end
 if row.header then return row.title,0,nil,true,row.closed end
 local q=quests[row.id];return q.title,10,nil,false,false,q.complete and 1 or nil,nil,row.id
end
function ExpandQuestHeader()expanded=expanded+1;for _,r in ipairs(log)do if r.header then r.closed=false end end end
function CollapseQuestHeader(index)restored=restored+1;visible()[index].closed=true end
function GetQuestLogSelection()return selection end
function SelectQuestLogEntry(index)selection=index end
'''


class Scenarios:
    modern = True

    def setUp(self):
        self.vm = LuaRuntime(unpack_returned_tuples=True)
        self.vm.execute(STUB)
        if self.modern:
            self.vm.execute('C_ChatInfo={SendChatMessage=SendChatMessage};SendChatMessage=nil')
        else:
            self.vm.execute('C_QuestLog.GetInfo=nil;C_QuestLog.IsComplete=nil')
        self.vm.execute('A={}')
        for filename in (ADDON / 'ElmoQuestEnhanced.toc').read_text().splitlines():
            if filename.endswith('.lua'):
                self.vm.execute((ADDON / filename).read_text(), 'ElmoQuestEnhanced', self.vm.globals().A)
        self.vm.execute("fire('ADDON_LOADED','ElmoQuestEnhanced')")
        self.vm.execute("add(100,'Test quest',1);fire('PLAYER_LOGIN');tick()")

    def check(self, code):
        self.vm.execute(code)

    def test_single_objective_reports_only_the_quest(self):
        self.check('''finish(100,1);quests[100].complete=true;update()
        assert(#sent==1 and sent[1].message=='[ElmoQuestEnhanced] Quest complete: Test quest')
        assert(sent[1].channel=='PARTY')''')

    def test_multi_objectives_then_whole_quest_once(self):
        self.check('''add(101,'Multiple',2);update()
        finish(101,1);update();assert(#sent==1 and sent[1].message:find('Objective 1: 2/2',1,true))
        finish(101,2);quests[101].complete=true;update()
        assert(#sent==3 and sent[2].message:find('Objective 2: 2/2',1,true))
        assert(sent[3].message=='[ElmoQuestEnhanced] Quest complete: Multiple')
        for i=1,10 do update();fire('QUEST_WATCH_UPDATE',101);tick()end
        assert(#sent==3)''')

    def test_progress_counts_do_not_override_finished_false(self):
        self.check('''add(101,'Criteria quest',2);update()
        quests[101].objectives[1].numFulfilled=2;update();assert(#sent==0)
        finish(101,1);update();assert(#sent==1)''')

    def test_initially_completed_quests_are_only_a_baseline(self):
        self.check('''local q=add(101,'Already done',2);finish(101,1);finish(101,2);q.complete=true
        update();tick();assert(#sent==0)''')

    def test_newly_accepted_quest_can_be_immediately_complete(self):
        self.check('''add(101,'Already have the items',1);finish(101,1);quests[101].complete=true
        fire('QUEST_ACCEPTED',1,101);tick()
        assert(#sent==1 and sent[1].message:find('Quest complete:',1,true))''')

    def test_baseline_completed_objectives_are_not_announced_again(self):
        self.check('''add(101,'Partly done',2);finish(101,1);update()
        finish(101,2);quests[101].complete=true;update()
        assert(#sent==2 and sent[1].message:find('Objective 2: 2/2',1,true))''')

    def test_solo_progress_is_not_replayed_when_joining(self):
        self.check('''group=false;finish(100,1);quests[100].complete=true;update()
        group='PARTY';update();assert(#sent==0)
        add(101,'New quest',1);update();finish(101,1);quests[101].complete=true;update()
        assert(#sent==1)''')

    def test_raid_and_instance_destination(self):
        self.check('''group='RAID';finish(100,1);quests[100].complete=true;update()
        assert(#sent==1 and sent[1].channel=='RAID')
        add(101,'Instance quest',1);update();group='INSTANCE_CHAT'
        finish(101,1);quests[101].complete=true;update()
        assert(#sent==2 and sent[2].channel=='INSTANCE_CHAT')''')

    def test_missing_objective_data_is_retried_without_a_new_event(self):
        self.check('''local rows=quests[100].objectives;quests[100].objectives=nil;update()
        quests[100].objectives=rows;finish(100,1);quests[100].complete=true;tick()
        assert(#sent==1)''')

    def test_inconsistent_complete_flag_waits_for_finished_rows(self):
        self.check('''quests[100].complete=true;update();assert(#sent==0)
        finish(100,1);tick();assert(#sent==1)''')

    def test_failed_send_retries_without_duplicate_announcements(self):
        self.check('''failSend=true;finish(100,1);quests[100].complete=true;update();assert(#sent==0)
        failSend=false;tick();tick();assert(#sent==1)''')

    def test_identical_text_in_different_objective_slots(self):
        self.check('''add(101,'Identical',2);update()
        finish(101,1);finish(101,2)
        quests[101].objectives[2].text=quests[101].objectives[1].text
        update();assert(#sent==2)''')

    def test_empty_rows_preserve_native_indices(self):
        self.check('''local q=add(101,'Empty row',3)
        q.objectives[1]={text='',type='log',finished=false};update()
        finish(101,2);update();assert(#sent==1 and sent[1].message:find('Objective 2',1,true))
        finish(101,3);q.complete=true;update();assert(#sent==3)''')

    def test_secret_rows_are_not_inspected_or_consumed(self):
        self.check('''local secret=setmetatable({}, {__index=function()error('Secret read')end})
        issecretvalue=function(v)return rawequal(v,secret)end
        local rows=quests[100].objectives;quests[100].objectives=secret;update();assert(#sent==0)
        quests[100].objectives=rows;finish(100,1);quests[100].complete=true;update();assert(#sent==1)''')

    def test_repeatable_quest_can_report_after_removal_and_reaccept(self):
        self.check('''finish(100,1);quests[100].complete=true;update();assert(#sent==1)
        fire('QUEST_REMOVED',100);quests[100].complete=false
        quests[100].objectives[1].finished=false;fire('QUEST_ACCEPTED',1,100);tick()
        finish(100,1);quests[100].complete=true;update();assert(#sent==2)''')

    def test_lost_item_does_not_reannounce_the_same_completed_objective(self):
        self.check('''add(101,'Items',2);update();finish(101,1);update();assert(#sent==1)
        quests[101].objectives[1].finished=false;update();finish(101,1);update();assert(#sent==1)''')

    def test_acceptance_turn_in_and_loot_are_not_announced(self):
        self.check('''fire('QUEST_ACCEPTED',1,100);tick()
        fire('CHAT_MSG_LOOT','An item');fire('QUEST_TURNED_IN',100);tick();assert(#sent==0)''')

    def test_loading_screen_does_not_consume_completion(self):
        self.check('''fire('PLAYER_LEAVING_WORLD');finish(100,1);quests[100].complete=true;tick()
        assert(#sent==0);fire('PLAYER_ENTERING_WORLD');tick();assert(#sent==1)''')

    def test_long_utf8_messages_remain_valid_and_within_chat_limit(self):
        self.check("quests[100].title=string.rep('é',180);finish(100,1);quests[100].complete=true;update()")
        message = self.vm.globals().sent[1].message
        self.assertLessEqual(len(message.encode('utf-8')), 255)

    def test_settings_are_registered_in_addons_with_saved_defaults(self):
        self.check('''assert(#frames==1 and ElmoQuestEnhanced==A and Questie==nil)
        assert(A.db==ElmoQuestEnhancedDB and A.db.reportQuests and A.db.reportObjectives and not A.db.reportProgress)
        assert(#settingsCategories==1 and settingsCategories[1].registered)
        assert(settingsCategories[1].name=='ElmoQuestEnhanced' and #settingsCheckboxes==3)
        assert(settingsRegistry.reportQuests:GetValue() and settingsRegistry.reportObjectives:GetValue())
        assert(not settingsRegistry.reportProgress:GetValue())
        SlashCmdList.ELMOQUESTENHANCED();assert(openedCategory==settingsCategories[1]:GetID())
        assert(SLASH_ELMOQUESTENHANCED1=='/eqe' and SLASH_ELMOQUESTENHANCED2=='/elmoquestenhanced')
        fire('PLAYER_ENTERING_WORLD');fire('ADDON_LOADED','OtherAddon');tick()
        assert(#settingsCategories==1 and #sent==0,'Registration and opening settings must not report quests')''')

    def test_existing_saved_choices_are_preserved(self):
        self.check('''A.db=nil;ElmoQuestEnhancedDB={reportQuests=false,reportObjectives=false,reportProgress=true}
        A.InitializeSettings()
        assert(not A.db.reportQuests and not A.db.reportObjectives and A.db.reportProgress)
        assert(not settingsRegistry.reportQuests:GetValue() and settingsRegistry.reportProgress:GetValue())''')

    def test_disabled_quest_reports_are_not_replayed_when_reenabled(self):
        self.check('''settingsRegistry.reportQuests:SetValue(false)
        finish(100,1);quests[100].complete=true;update();assert(#sent==0)
        settingsRegistry.reportQuests:SetValue(true);update();assert(#sent==0)
        add(101,'New completion',1);update();finish(101,1);quests[101].complete=true;update()
        assert(#sent==1 and sent[1].message:find('New completion',1,true))''')

    def test_disabled_objective_reports_still_allow_quest_reports(self):
        self.check('''settingsRegistry.reportObjectives:SetValue(false)
        add(101,'Multiple',2);update();finish(101,1);update();assert(#sent==0)
        settingsRegistry.reportObjectives:SetValue(true);update();assert(#sent==0)
        settingsRegistry.reportObjectives:SetValue(false)
        finish(101,2);quests[101].complete=true;update()
        assert(#sent==1 and sent[1].message=='[ElmoQuestEnhanced] Quest complete: Multiple')''')

    def test_objective_reports_are_independent_of_quest_reports(self):
        self.check('''settingsRegistry.reportQuests:SetValue(false)
        add(101,'Multiple',2);update();finish(101,1);update();finish(101,2);quests[101].complete=true;update()
        assert(#sent==2 and sent[1].message:find('Objective complete:',1,true))
        assert(sent[2].message:find('Objective complete:',1,true))''')

    def test_progress_reports_kills_items_and_remaining_counts_once(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        add(101,'Kills and items',2);quests[101].objectives[1].type='monster';update()
        progress(101,1,1);fire('QUEST_WATCH_UPDATE',101);tick()
        assert(#sent==1 and sent[1].message=='[ElmoQuestEnhanced] Objective progress: Objective 1: 1/2 (1 remaining) (Kills and items)')
        progress(101,2,1);fire('BAG_UPDATE_DELAYED');tick()
        assert(#sent==2 and sent[2].message:find('Objective 2: 1/2 (1 remaining)',1,true))
        for i=1,5 do update();tick()end;assert(#sent==2)
        finish(101,1);update()
        assert(#sent==3 and sent[3].message:find('Objective complete:',1,true),'Completion replaces duplicate progress')''')

    def test_progress_only_includes_final_zero_remaining(self):
        self.check('''settingsRegistry.reportQuests:SetValue(false)
        settingsRegistry.reportObjectives:SetValue(false);settingsRegistry.reportProgress:SetValue(true)
        progress(100,1,1);update();finish(100,1);quests[100].complete=true;update()
        assert(#sent==2 and sent[2].message:find('2/2 (0 remaining)',1,true))
        update();assert(#sent==2)''')

    def test_progress_disabled_or_solo_is_consumed_without_replay(self):
        self.check('''progress(100,1,1);update();assert(#sent==0)
        settingsRegistry.reportProgress:SetValue(true);update();assert(#sent==0)
        add(101,'Solo items',2);update();group=false;progress(101,1,1);update()
        group='PARTY';update();assert(#sent==0)
        finish(101,1);update();assert(#sent==1 and sent[1].message:find('Objective complete:',1,true))''')

    def test_losing_items_is_silent_but_collecting_again_reports_progress(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        progress(100,1,1);update();assert(#sent==1)
        progress(100,1,0);update();assert(#sent==1)
        progress(100,1,1);update();assert(#sent==2)''')

    def test_initial_counts_and_objective_requirement_changes_are_silent(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        add(101,'Already collected',2);progress(101,1,1);update();assert(#sent==0)
        quests[101].objectives[1].numRequired=5;progress(101,1,2);update();assert(#sent==0)
        progress(101,1,3);update();assert(#sent==1 and sent[1].message:find('2 remaining',1,true))''')

    def test_progress_skips_non_count_objectives_and_private_or_missing_counts(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        add(101,'Event',2);quests[101].objectives[1].type='event';update()
        progress(101,1,1);update();assert(#sent==0)
        local secret=setmetatable({}, {__index=function()error('Private read')end})
        issecretvalue=function(v)return rawequal(v,secret)end
        progress(100,1,1);quests[100].objectives[1].numFulfilled=secret;update();assert(#sent==0)
        quests[100].objectives[1].numFulfilled=1;update();assert(#sent==1)
        quests[100].objectives[1].numRequired=nil;update();assert(#sent==1)''')

    def test_progress_waits_for_consistent_finished_flag(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        progress(100,1,2);update();assert(#sent==0)
        quests[100].objectives[1].finished=true;update()
        assert(#sent==1 and sent[1].message:find('0 remaining',1,true))''')

    def test_failed_progress_send_retries_and_coalesces_to_latest_count(self):
        self.check('''settingsRegistry.reportProgress:SetValue(true)
        quests[100].objectives[1].numRequired=5;update()
        failSend=true;progress(100,1,1);update();assert(#sent==0)
        progress(100,1,2);update();failSend=false;tick();tick()
        assert(#sent==1 and sent[1].message:find('2/5 (3 remaining)',1,true))''')

    def test_old_folder_compatibility_stub_cannot_send_duplicate_reports(self):
        stub = ADDON.parent / 'ElmoQuestReport/Legacy.lua'
        if not stub.is_file():
            stub = ROOT / 'compat/ElmoQuestReport/Legacy.lua'
        self.vm.execute(stub.read_text(), 'ElmoQuestReport', self.vm.table())
        self.check('''assert(#frames==1 and ElmoQuestEnhanced==A and ElmoQuestReport==nil)
        finish(100,1);quests[100].complete=true;update();tick()
        assert(#sent==1 and sent[1].message=='[ElmoQuestEnhanced] Quest complete: Test quest')''')


class ForeverTests(Scenarios, unittest.TestCase):
    modern = True


class EraTests(Scenarios, unittest.TestCase):
    modern = False

    def test_collapsed_headers_and_selection_are_restored_without_a_scan_loop(self):
        self.check('''table.insert(log,1,{title='Zone',header=true,closed=true});selection=1
        update();assert(log[1].closed and selection==1 and expanded==1 and restored==1)
        finish(100,1);quests[100].complete=true;update();tick()
        assert(#sent==1 and expanded==1 and log[1].closed and selection==1)''')


if __name__ == '__main__':
    unittest.main()
