"""Real ElmoLFM Lua in isolated WHO/chat/party fixtures. No live game actions."""
from pathlib import Path
import os
import unittest
from lupa.lua51 import LuaRuntime

HERE = Path(__file__).parent
ADDON = Path(os.environ.get("ELMO_TEST_ADDON", HERE.resolve().parents[2] / "ElmoLFM"))


def create_vm(legacy=False, profile=None):
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute((HERE / "wow_mock.lua").read_text())
    namespace = vm.table()
    load = vm.eval('function(s,n,ns) assert(loadstring(s,"@"..n))("ElmoLFM",ns) end')
    for line in (ADDON / "ElmoLFM.toc").read_text().splitlines():
        if line.endswith(".lua"):
            load((ADDON / line.replace("\\", "/")).read_text(), line, namespace)
    vm.globals().A = namespace
    if profile is not None:
        vm.globals().ElmoLFMDB = vm.table_from(profile, recursive=True)
    if legacy:
        vm.execute("MOCK.legacy()")
    vm.execute("MOCK.start()")
    return vm


class RecruitmentTests(unittest.TestCase):
    legacy = False

    def setUp(self):
        self.vm = create_vm(self.legacy)

    def check(self, code):
        self.vm.execute(code)

    def test_load_settings_and_open_window_have_no_network_actions(self):
        self.check("""
        assert(SLASH_ELMOLFM1=='/elfm' and SLASH_ELMOLFM2=='/elmolfm')
        assert(ElmoLFMDB==A.db and A.db.minimum==37 and A.db.maximum==41)
        assert(#MOCK.categories==1 and MOCK.categories[1].registered)
        A.Settings.Open();assert(MOCK.openCategory==123)
        A.Command('');assert(ElmoLFMFrame:IsShown())
        A.Command('');assert(not ElmoLFMFrame:IsShown())
        A.Command('');assert(ElmoLFMFrame:IsShown())
        assert(#MOCK.requests==0 and #MOCK.sent==0 and #MOCK.invited==0)
        """)

    def test_exact_zone_and_level_query_and_no_automatic_repeats(self):
        self.check("""
        assert(A.Search('  Alterac Mountains  ','38','40'))
        assert(#MOCK.requests==0 and MOCK.chatCommand=='/who z-"Alterac Mountains" 38-40')
        assert(MOCK.routing[1]==true);MOCK.enterChat()
        assert(MOCK.requests[1]=='z-"Alterac Mountains" 38-40')
        MOCK.results({MOCK.player('Alice',38),MOCK.player('Bob',40)})
        assert(#A.results==2 and MOCK.routing[2]==false)
        MOCK.advance(100);assert(#MOCK.requests==1 and #MOCK.sent==0)
        """)

    def test_invalid_filters_do_not_query(self):
        self.check("""
        for _,args in ipairs({{'',38,40},{'Bad" zone',38,40},{'Zone\\nName',38,40},
            {'Zone',40,38},{'Zone',0,40},{'Zone',38,61},{'Zone',38.5,40},{'Zone','?',40}})do
            assert(not A.Search(unpack(args)))
        end
        assert(#MOCK.requests==0)
        """)

    def test_native_search_wait_timeout_and_late_response(self):
        self.check("""
        assert(A.Search('Alterac Mountains',38,40))
        assert(not A.Search('Alterac Mountains',38,40))
        MOCK.advance(30);assert(A.search and #MOCK.requests==0)
        MOCK.advance(90);assert(not A.search and A.error and MOCK.routing[2]==false)
        MOCK.results({MOCK.player('Late')});assert(#A.results==0)
        assert(A.Search('Alterac Mountains',38,40))
        MOCK.enterChat();MOCK.results({})
        assert(A.Search('Alterac Mountains',38,40))
        assert(#MOCK.requests==1)
        """)

    def test_external_results_are_ignored_until_requested_and_other_zones_are_included(self):
        self.check("""
        MOCK.results({MOCK.player('Stranger')});assert(#A.results==0)
        assert(A.Search('Alterac Mountains',38,40))
        MOCK.results({MOCK.player('Foreign',39,'Duskwood')})
        assert(#A.results==1 and A.results[1].area=='Duskwood' and not A.error and not A.search)
        """)

    def test_reported_fifty_row_list_matches_blizzard_without_additional_level_filter(self):
        self.check("""
        local result={MOCK.player('Below Range',35)}
        for i=2,50 do result[i]=MOCK.player('Player'..i,38+(i%3)) end
        MOCK.search(result)
        assert(#A.results==50 and A.results[1].level==35 and not A.search and not A.error)
        assert(A.status:find('WHO limit reached',1,true))
        MOCK.selectAll();assert(A.SendSelected() and #MOCK.sent==1)
        """)

    def test_mixed_zone_and_level_rows_preserve_the_native_order(self):
        self.check("""
        MOCK.search({MOCK.player('Low',35),MOCK.player('High',41),
            MOCK.player('Elsewhere',39,'Duskwood'),MOCK.player('Alice',38),
            MOCK.player('Bob',40)})
        assert(#A.results==5 and A.results[1].name=='Low' and A.results[2].name=='High')
        assert(A.results[3].name=='Elsewhere' and A.results[3].area=='Duskwood')
        """)

    def test_all_fifty_native_rows_in_other_zones_are_visible_with_their_zone(self):
        self.check("""
        A.UI.Open()
        local native={}
        for i=1,50 do
            native[i]=MOCK.player('Player'..i,30+(i%12),i<=3 and 'Alterac Mountains' or 'Hillsbrad Foothills')
        end
        MOCK.search(native)
        assert(#A.results==50 and A.results[4].area=='Hillsbrad Foothills')
        local visible=0
        for _,widget in ipairs(MOCK.frames)do
            if widget.kind=='Button' and widget.player and widget:IsShown()then
                visible=visible+1
                assert(widget.zone:GetText()==widget.player.area)
                assert(widget.name:GetText()==widget.player.name)
            end
        end
        assert(visible==50 and A.UI.frame.summary:GetText():find('50 players',1,true))
        """)

    def test_shift_click_questie_inserts_the_exact_bracket_link_at_the_cursor(self):
        self.check("""
        MOCK.questie();A.UI.Open()
        local editor=A.UI.frame.message
        editor:SetText('LFM  please');editor:SetCursorPosition(4);editor:SetFocus()
        MOCK.shift=true;MOCK.click(MOCK.questRow)
        local expected='LFM [[31] Soothing Turtle Bisque (555)] please'
        assert(editor:GetText()==expected and A.db.message==expected and A.Message()==expected)
        assert(not MOCK.untracked and not MOCK.questNormalClicks and not MOCK.chatCommand)
        assert(#MOCK.sent==0 and #MOCK.requests==0)
        """)

    def test_questie_normal_clicks_and_shift_clicks_outside_the_message_are_preserved(self):
        self.check("""
        MOCK.questie();A.UI.Open()
        local editor=A.UI.frame.message
        editor:SetText('Draft');editor:SetFocus()
        MOCK.click(MOCK.questRow);assert(MOCK.questNormalClicks==1 and editor:GetText()=='Draft')
        editor:ClearFocus();MOCK.shift=true;MOCK.click(MOCK.questRow)
        assert(MOCK.untracked==1 and editor:GetText()=='Draft')
        editor:SetFocus();MOCK.questRow.scripts.OnClick(MOCK.questRow,'RightButton')
        assert(MOCK.questNormalClicks==3 and editor:GetText()=='Draft')
        """)

    def test_questie_recycled_rows_and_repeated_editor_focus_do_not_duplicate_links(self):
        self.check("""
        MOCK.questie();A.UI.Open()
        local editor=A.UI.frame.message
        editor:SetText('');editor:SetFocus();editor:ClearFocus();editor:SetFocus()
        MOCK.questRow:SetOnClick('quest')
        MOCK.shift=true;MOCK.click(MOCK.questRow)
        assert(editor:GetText()=='[[31] Soothing Turtle Bisque (555)]')
        assert(not MOCK.untracked and not MOCK.questNormalClicks)
        """)

    def test_native_link_insertion_preserves_the_original_return_value_and_payload(self):
        self.check("""
        A.UI.Open();local editor=A.UI.frame.message
        editor:SetText('Quest: ');editor:SetFocus()
        local link='|cffffff00|Hquest:555:31|h[Soothing Turtle Bisque]|h|r'
        local insert=ChatFrameUtil and ChatFrameUtil.InsertLink or ChatEdit_InsertLink
        assert(insert(link)==false)
        assert(editor:GetText()=='Quest: '..link and A.db.message=='Quest: '..link)
        assert(MOCK.nativeLink==link and not MOCK.chatCommand and #MOCK.sent==0)
        """)

    def test_link_insertion_is_limited_to_the_visible_focused_message_editor(self):
        self.check("""
        A.UI.Open();local editor=A.UI.frame.message
        editor:SetText('Draft');editor:SetFocus()
        A.UI.frame.zone:SetFocus()
        local insert=ChatFrameUtil and ChatFrameUtil.InsertLink or ChatEdit_InsertLink
        insert('[[31] Soothing Turtle Bisque (555)]')
        assert(editor:GetText()=='Draft')
        editor:SetFocus();A.UI.frame:Hide()
        insert('[[31] Soothing Turtle Bisque (555)]')
        assert(editor:GetText()=='Draft')
        """)

    def test_quest_link_overflow_is_rejected_whole_without_untracking_the_quest(self):
        self.check("""
        MOCK.questie();A.UI.Open();local editor=A.UI.frame.message
        editor:SetText(string.rep('x',250));editor:SetFocus();MOCK.shift=true
        MOCK.click(MOCK.questRow)
        assert(editor:GetText()==string.rep('x',250) and A.error)
        assert(not MOCK.untracked and not MOCK.questNormalClicks)
        assert(#MOCK.sent==0 and #MOCK.requests==0)
        """)

    def test_whispers_keep_the_inserted_questie_text_unchanged(self):
        self.check("""
        MOCK.questie();A.UI.Open()
        MOCK.search({MOCK.player('Alice',39,'Hillsbrad Foothills')})
        local editor=A.UI.frame.message
        editor:SetText('LFM ');editor:SetFocus();MOCK.shift=true;MOCK.click(MOCK.questRow)
        MOCK.selectAll();assert(A.SendSelected())
        assert(MOCK.sent[1].message=='LFM [[31] Soothing Turtle Bisque (555)]')
        """)

    def test_visible_recruitment_imports_native_searches_without_preparing_its_own(self):
        self.check("""
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        assert(not A.search and not A.query)
        MOCK.results({MOCK.player('Low',35),MOCK.player('Alice',38),MOCK.player('Bob',40)})
        assert(#A.results==3 and not A.search and A.query=='z-"Alterac Mountains" 38-40')
        MOCK.click(A.UI.frame.selectAll)
        assert(A.UI.frame.send:IsEnabled() and #MOCK.requests==0 and #MOCK.sent==0)
        MOCK.click(A.UI.frame.send);assert(#MOCK.sent==1)
        """)

    def test_existing_who_cache_can_be_imported_after_waiting_has_expired(self):
        self.check("""
        assert(A.Search('Alterac Mountains',38,40));MOCK.advance(120)
        assert(not A.search and A.error)
        MOCK.who={MOCK.player('Alice',38),MOCK.player('Bob',40)}
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        MOCK.click(A.UI.frame.import)
        assert(#A.results==2 and not A.error and not A.search and #MOCK.requests==0)
        MOCK.click(A.UI.frame.selectAll);assert(A.UI.frame.send:IsEnabled())
        """)

    def test_import_uses_current_query_and_displays_all_public_who_rows(self):
        self.check("""
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        MOCK.who={MOCK.player('Low',35),MOCK.player('Elsewhere',39,'Duskwood')}
        MOCK.click(A.UI.frame.import)
        assert(#A.results==2 and A.returned==2)
        assert(A.status:find('Showing 2 of 2 Blizzard WHO players',1,true))
        A.UI.frame.minimum:SetText('35');MOCK.click(A.UI.frame.import)
        assert(#A.results==2 and A.results[1].name=='Low' and A.db.minimum==35)
        assert(#MOCK.requests==0 and not MOCK.chatCommand)
        """)

    def test_import_command_reads_cache_without_a_query_and_clears_old_campaign_tickets(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        assert(A.tickets[A.NameKey('Alice')])
        A.db.zone,A.db.minimum,A.db.maximum='Duskwood',28,30
        MOCK.who={MOCK.player('Bob',29,'Duskwood')}
        A.Command('import')
        assert(ElmoLFMFrame:IsShown() and #A.results==1 and A.results[1].name=='Bob')
        assert(not A.search and next(A.tickets)==nil)
        assert(#MOCK.requests==1 and #MOCK.sent==1)
        A.Command('status');assert(MOCK.printed:find(A.version,1,true))
        """)

    def test_external_who_updates_do_not_replace_an_active_whisper_batch(self):
        self.check("""
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected()
        MOCK.results({MOCK.player('Stranger')})
        assert(#A.results==2 and A.queue and not A.UI.frame.import:IsEnabled())
        assert(not A.ImportWho('Alterac Mountains',38,40))
        MOCK.advance(1);assert(#MOCK.sent==2 and MOCK.sent[2].target=='Bob')
        """)

    def test_unreadable_cache_does_not_erase_results_and_import_cannot_dispatch_who(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')})
        MOCK.privateCount=MOCK.secret()
        assert(not A.ImportWho('Alterac Mountains',38,40))
        assert(#A.results==1 and A.error and A.status:find('readable WHO count',1,true))
        assert(#MOCK.requests==1 and #MOCK.sent==0 and #MOCK.invited==0)
        """)

    def test_self_and_group_members_are_visible_but_cannot_be_contacted_and_duplicates_are_removed(self):
        self.check("""
        MOCK.members['friend-myrealm']=true
        MOCK.raidMembers['raider-myrealm']=7
        MOCK.search({MOCK.player('Tester-MyRealm'),MOCK.player('Friend'),
            MOCK.player('Raider'),MOCK.player('Alice-MyRealm',40),MOCK.player('alice-My Realm',40),
            MOCK.player('Bob',38),MOCK.player('Alice-OtherRealm',40)})
        assert(#A.results==6 and A.results[1].name=='Tester-MyRealm' and A.results[5].name=='Bob')
        for index=1,3 do assert(not A.Contactable(A.results[index])) end
        assert(A.whoSkipped.duplicate==1)
        MOCK.selectAll();A.SendSelected();MOCK.advance(1);MOCK.advance(1)
        assert(#MOCK.sent==3 and MOCK.sent[1].target=='Alice-MyRealm' and MOCK.sent[2].target=='Bob')
        """)

    def test_who_limit_is_visible_and_capped(self):
        self.check("""
        local result={}
        for i=1,70 do result[i]=MOCK.player('Player'..i) end
        assert(A.Search('Alterac Mountains',38,40));MOCK.results(result,140)
        assert(#A.results==50 and A.status:find('limit',1,true))
        """)

    def test_multiple_selection_whispers_only_selected_players_once(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob'),MOCK.player('Cara')})
        A.selected[A.NameKey('Alice')]=true;A.selected[A.NameKey('Cara')]=true
        assert(#MOCK.sent==0)
        assert(A.SendSelected());assert(#MOCK.sent==1 and MOCK.sent[1].target=='Alice')
        MOCK.advance(.5);assert(#MOCK.sent==1)
        MOCK.advance(.5);assert(#MOCK.sent==2 and MOCK.sent[2].target=='Cara' and not A.queue)
        MOCK.advance(100);assert(#MOCK.sent==2 and #MOCK.invited==0)
        MOCK.selectAll();A.SendSelected();assert(#MOCK.sent==3 and MOCK.sent[3].target=='Bob')
        """)

    def test_message_placeholders_and_utf8_byte_limit(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll()
        A.db.message='Meet in {zone}, {min}-{max}!';assert(A.SendSelected())
        assert(MOCK.sent[1].message=='Meet in Alterac Mountains, 38-40!')
        A.db.message=string.rep('è',128);local _,err=A.Message();assert(err)
        A.db.message='  \\n  ';assert(A.Message()==nil)
        """)

    def test_queue_uses_reviewed_message_snapshot_and_stops_on_request(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob'),MOCK.player('Cara')});MOCK.selectAll()
        A.db.message='Reviewed message';A.SendSelected();A.db.message='Changed later'
        MOCK.advance(1);assert(MOCK.sent[2].message=='Reviewed message')
        A.Stop();MOCK.advance(10)
        assert(#MOCK.sent==2 and not A.queue and next(A.tickets)==nil)
        A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        """)

    def test_right_click_invites_without_a_whisper_or_auto_invite_permission(self):
        self.check("""
        A.UI.Open();MOCK.who={MOCK.player('Alice-OtherRealm')};A.Command('import')
        A.SetAutoInvite(false)
        local row=MOCK.row('Alice-OtherRealm');local key=row.player.key
        A.selected[key]=true;A.Refresh()
        MOCK.click(row,'RightButton')
        assert(#MOCK.invited==1 and MOCK.invited[1]=='Alice-OtherRealm')
        assert(A.selected[key] and row.check:GetChecked())
        assert(#MOCK.requests==0 and #MOCK.sent==0 and next(A.tickets)==nil)
        assert(next(A.contacts)==nil and not row.sent:IsShown())
        GameTooltip.lines={};row.scripts.OnEnter()
        local pending=false
        for _,line in ipairs(GameTooltip.lines)do if line=='Invite requested' then pending=true end end
        assert(pending)
        MOCK.click(row,'RightButton')
        assert(#MOCK.invited==1 and A.status:find('already pending',1,true))
        """)

    def test_left_click_and_checkbox_still_select_without_inviting(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')})
        local row=MOCK.row('Alice');local key=row.player.key
        MOCK.click(row);assert(A.selected[key] and row.check:GetChecked())
        MOCK.click(row);assert(not A.selected[key] and not row.check:GetChecked())
        MOCK.click(row.check);assert(A.selected[key] and row.check:GetChecked())
        assert(#MOCK.invited==0 and #MOCK.sent==0)
        """)

    def test_right_click_rejects_self_group_members_full_groups_and_missing_permission(self):
        self.check("""
        A.UI.Open();MOCK.members[A.NameKey('Friend')]=true
        MOCK.search({MOCK.player('Tester-MyRealm'),MOCK.player('Friend'),MOCK.player('Alice')})
        MOCK.click(MOCK.row('Tester-MyRealm'),'RightButton')
        MOCK.click(MOCK.row('Friend'),'RightButton')
        assert(#MOCK.invited==0 and A.status:find('already in your group',1,true))
        MOCK.groupCount=5;MOCK.click(MOCK.row('Alice'),'RightButton')
        assert(#MOCK.invited==0 and A.error and A.status:find('full',1,true))
        MOCK.groupCount=2;MOCK.permissions=false;MOCK.click(MOCK.row('Alice'),'RightButton')
        assert(#MOCK.invited==0 and A.error and A.status:find('permission',1,true))
        assert(next(A.invites)==nil and #MOCK.sent==0)
        """)

    def test_manual_and_reply_invites_share_the_last_pending_slot(self):
        self.check("""
        A.UI.Open();MOCK.groupCount=4
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')})
        A.selected[A.NameKey('Bob')]=true;assert(A.SendSelected())
        MOCK.click(MOCK.row('Alice'),'RightButton');A.HandleWhisper('inv','Bob')
        assert(#MOCK.invited==1 and MOCK.invited[1]=='Alice' and A.FreeSlots()==0)
        MOCK.advance(60);A.HandleWhisper('inv','Bob')
        assert(#MOCK.invited==2 and MOCK.invited[2]=='Bob')
        """)

    def test_failed_right_click_does_not_reserve_a_slot_or_retry_automatically(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')})
        MOCK.inviteError=true;MOCK.click(MOCK.row('Alice'),'RightButton')
        assert(#MOCK.invited==0 and next(A.invites)==nil and A.error)
        assert(A.status:find('Invite blocked',1,true) and next(A.contacts)==nil)
        MOCK.inviteError=false;MOCK.advance(1);assert(#MOCK.invited==0)
        MOCK.click(MOCK.row('Alice'),'RightButton')
        assert(#MOCK.invited==1 and A.invites[A.NameKey('Alice')])
        """)

    def test_contacted_player_can_be_invited_without_erasing_the_reply_or_sent_flag(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')})
        A.selected[A.NameKey('Alice')]=true;A.SendSelected()
        A.SetAutoInvite(false);A.HandleWhisper('Ready as healer','Alice')
        local row=MOCK.row('Alice');assert(not row.check:IsEnabled())
        MOCK.click(row,'RightButton')
        local contact=A.contacts[row.player.key]
        assert(#MOCK.invited==1 and #MOCK.sent==1)
        assert(contact.sent and contact.reply=='Ready as healer' and contact.state=='Invite requested')
        assert(row.sent:IsShown() and row.reply:GetText()=='Ready as healer')
        """)

    def test_only_contacted_players_with_an_invitation_reply_are_invited(self):
        self.check("""
        MOCK.search({MOCK.player('Alice-OtherRealm'),MOCK.player('Bob')})
        A.selected[A.NameKey('Alice-OtherRealm')]=true;A.SendSelected()
        for _,message in ipairs({'hi','invisible','no invite','not interested'})do A.HandleWhisper(message,'Alice-OtherRealm')end
        A.HandleWhisper('inv','Bob');A.HandleWhisper('inv','Alice-MyRealm')
        assert(#MOCK.invited==0)
        A.HandleWhisper('  INV tank please','alice-OtherRealm')
        assert(#MOCK.invited==1 and MOCK.invited[1]=='Alice-OtherRealm')
        A.HandleWhisper('invite','Alice-OtherRealm');assert(#MOCK.invited==1)
        """)

    def test_auto_invite_off_and_expired_replies(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        A.SetAutoInvite(false);A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        A.SetAutoInvite(true);A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        MOCK.advance(300);MOCK.selectAll();assert(not A.SendSelected())
        assert(A.Search('Alterac Mountains',38,40));MOCK.results({MOCK.player('Alice')})
        MOCK.selectAll();A.SendSelected();MOCK.advance(600);A.HandleWhisper('inv','Alice')
        assert(#MOCK.invited==0)
        """)

    def test_pending_invites_reserve_the_last_slot_and_can_expire(self):
        self.check("""
        MOCK.groupCount=4
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected();MOCK.advance(1)
        A.HandleWhisper('inv','Alice');A.HandleWhisper('inv','Bob')
        assert(#MOCK.invited==1 and A.FreeSlots()==0)
        MOCK.advance(60);A.HandleWhisper('inv','Bob')
        assert(#MOCK.invited==2 and MOCK.invited[2]=='Bob')
        """)

    def test_lost_invitation_permissions_block_sends_and_later_invites(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll()
        MOCK.groupCount=2;MOCK.permissions=false;assert(not A.SendSelected() and #MOCK.sent==0)
        MOCK.permissions=true;A.SendSelected();MOCK.permissions=false
        A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        MOCK.permissions=true;MOCK.members[A.NameKey('Alice')]=true
        A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        """)

    def test_request_errors_stop_the_batch_without_authorizing_unsent_players(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected()
        MOCK.sendError=true;MOCK.advance(1)
        assert(#MOCK.sent==1 and not A.queue and A.error)
        A.HandleWhisper('inv','Bob');assert(#MOCK.invited==0)
        MOCK.advance(10);assert(#MOCK.sent==1)
        """)

    def test_client_hardware_restriction_stops_without_retrying_in_a_loop(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll()
        MOCK.hardwareOnly=true;MOCK.hardware=true;A.SendSelected();MOCK.hardware=false;MOCK.advance(1)
        assert(#MOCK.sent==1 and not A.queue and A.error)
        MOCK.advance(100);assert(#MOCK.sent==1)
        """)

    def test_full_group_stops_the_remaining_whisper_batch(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected()
        MOCK.groupCount=5;MOCK.fire('GROUP_ROSTER_UPDATE');MOCK.advance(1)
        assert(#MOCK.sent==1 and not A.queue and next(A.tickets)==nil)
        """)

    def test_saved_preferences_and_reload_do_not_resume_recruitment(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected()
        A.db.message='Saved';A.db.autoInvite=false
        """)
        db = self.vm.globals().ElmoLFMDB
        reloaded = create_vm(self.legacy, {key: db[key] for key in ("zone", "minimum", "maximum", "message", "autoInvite")})
        reloaded.execute("""
        assert(A.db.message=='Saved' and not A.db.autoInvite and not A.queue and not A.search)
        A.HandleWhisper('inv','Alice')
        assert(#MOCK.invited==0 and #MOCK.sent==0 and #MOCK.requests==0 and next(A.tickets)==nil)
        """)

    def test_selection_and_changed_filters_require_an_explicit_matching_search(self):
        self.check("""
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        MOCK.click(A.UI.frame.search);MOCK.results({MOCK.player('Alice'),MOCK.player('Bob')})
        MOCK.click(A.UI.frame.selectAll)
        assert(A.UI.frame.send:IsEnabled() and #MOCK.sent==0)
        A.UI.frame.zone:SetText('Duskwood');assert(not A.UI.frame.send:IsEnabled())
        A.UI.frame.zone:SetText('Alterac Mountains');assert(A.UI.frame.send:IsEnabled())
        MOCK.click(A.UI.frame.send);assert(#MOCK.sent==1)
        """)

    def test_private_player_fields_counts_and_chat_arguments_are_skipped(self):
        self.check("""
        local secret=MOCK.secret()
        assert(A.Search('Alterac Mountains',38,40))
        MOCK.privateCount=secret;MOCK.results({});assert(A.search)
        MOCK.privateCount=nil
        local unreadable=MOCK.player('Unreadable');MOCK.blockedTable=unreadable
        if not C_FriendList then unreadable.fullName=secret end
        local hiddenLevel=MOCK.player('Private level');hiddenLevel.level=secret
        MOCK.results({secret,unreadable,hiddenLevel,MOCK.player('Alice')})
        assert(#A.results==1 and A.results[1].name=='Alice')
        MOCK.selectAll();A.SendSelected()
        A.HandleWhisper(secret,'Alice');A.HandleWhisper('inv',secret)
        assert(#MOCK.invited==0)
        """)

    def test_chat_unavailable_leaves_a_manual_command_and_no_automatic_retries(self):
        self.check("""
        A.UI.Open();A.UI.frame.minimum:SetText('38');A.UI.frame.maximum:SetText('40')
        MOCK.openChatError=true
        assert(A.Search('Alterac Mountains',38,40))
        assert(A.search and A.UI.frame.query:GetText()=='/who z-"Alterac Mountains" 38-40')
        assert(#MOCK.requests==0 and not MOCK.chatCommand)
        MOCK.advance(120);assert(not A.search and MOCK.routing[2]==false)
        assert(#MOCK.requests==0)
        """)

    def test_visible_native_who_window_keeps_its_routing_after_search(self):
        self.check("""
        WhoFrame=CreateFrame('Frame')
        MOCK.search({MOCK.player('Alice')})
        assert(MOCK.routing[#MOCK.routing]==true and WhoFrame:IsShown())
        WhoFrame:Hide();MOCK.advance(10);assert(A.Search('Alterac Mountains',38,40))
        A.Stop();assert(MOCK.routing[#MOCK.routing]==false and not WhoFrame:IsShown())
        """)

    def test_delivery_event_and_campaign_change(self):
        self.check("""
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll()
        MOCK.informImmediately=true;A.SendSelected()
        assert(A.contacts[A.NameKey('Alice')].state=='Whisper sent')
        MOCK.advance(10);assert(A.Search('Duskwood',28,30))
        A.HandleWhisper('inv','Alice');assert(#MOCK.invited==0)
        """)

    def test_sent_check_requires_the_matching_delivery_confirmation(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        local row=MOCK.row('Alice')
        assert(not row.sent:IsShown() and row.reply:GetText()=='')
        MOCK.fire('CHAT_MSG_WHISPER_INFORM','Unrelated message','Alice')
        MOCK.fire('CHAT_MSG_WHISPER_INFORM',A.Message(),'SomeoneElse')
        assert(not row.sent:IsShown())
        MOCK.fire('CHAT_MSG_WHISPER_INFORM',A.Message(),'Alice')
        assert(row.sent:IsShown() and row.reply:GetText()=='')
        assert(A.contacts[A.NameKey('Alice')].sent and #MOCK.sent==1)
        """)

    def test_negative_replies_are_shown_with_auto_invite_disabled_and_full_tooltip_text(self):
        self.check("""
        A.UI.Open();A.SetAutoInvite(false)
        MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        local reply='Sorry, already in a group.\\nMaybe later, after this quest.'
        MOCK.fire('CHAT_MSG_WHISPER',reply,'Alice')
        local row=MOCK.row('Alice')
        assert(row.sent:IsShown() and row.reply:GetText()=='Sorry, already in a group. Maybe later, after this quest.')
        assert(A.contacts[A.NameKey('Alice')].reply==reply and #MOCK.invited==0)
        GameTooltip.lines={};row.scripts.OnEnter()
        local found=false
        for _,line in ipairs(GameTooltip.lines)do if line==reply then found=true end end
        assert(found)
        """)

    def test_latest_reply_is_associated_with_the_correct_full_player_name(self):
        self.check("""
        A.UI.Open()
        MOCK.search({MOCK.player('Alice-OtherRealm'),MOCK.player('Alice-MyRealm')})
        MOCK.selectAll();A.SendSelected();MOCK.advance(1)
        MOCK.fire('CHAT_MSG_WHISPER','Maybe later','ALICE-OtherRealm')
        MOCK.fire('CHAT_MSG_WHISPER','No thanks','Alice-MyRealm')
        MOCK.fire('CHAT_MSG_WHISPER','Actually yes','alice-otherrealm')
        assert(MOCK.row('Alice-OtherRealm').reply:GetText()=='Actually yes')
        assert(MOCK.row('Alice-MyRealm').reply:GetText()=='No thanks')
        MOCK.fire('CHAT_MSG_WHISPER','Private conversation','Stranger')
        assert(not A.contacts[A.NameKey('Stranger')] and #MOCK.invited==0)
        """)

    def test_invitation_replies_are_displayed_and_still_invite_once(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        MOCK.fire('CHAT_MSG_WHISPER','inv healer please','Alice')
        assert(MOCK.row('Alice').sent:IsShown() and MOCK.row('Alice').reply:GetText()=='inv healer please')
        assert(#MOCK.invited==1 and A.contacts[A.NameKey('Alice')].state=='Invite requested')
        MOCK.fire('CHAT_MSG_WHISPER','invite','Alice');assert(#MOCK.invited==1)
        assert(MOCK.row('Alice').reply:GetText()=='invite')
        """)

    def test_contact_flags_and_late_replies_survive_reimport_without_extending_invitation_permission(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        MOCK.fire('CHAT_MSG_WHISPER_INFORM',A.Message(),'Alice')
        MOCK.advance(601);assert(not A.tickets[A.NameKey('Alice')])
        assert(A.UI.ImportWho() and MOCK.row('Alice').sent:IsShown())
        MOCK.fire('CHAT_MSG_WHISPER','inv','Alice')
        assert(MOCK.row('Alice').reply:GetText()=='inv' and #MOCK.invited==0)
        A.Stop();MOCK.fire('CHAT_MSG_WHISPER','Thanks anyway','Alice')
        assert(MOCK.row('Alice').reply:GetText()=='Thanks anyway' and #MOCK.invited==0)
        """)

    def test_new_contact_clears_the_previous_reply_and_requires_a_new_confirmation(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')});MOCK.selectAll();A.SendSelected()
        MOCK.fire('CHAT_MSG_WHISPER','No thanks','Alice')
        MOCK.advance(300);A.UI.ImportWho();MOCK.selectAll();A.SendSelected()
        local row=MOCK.row('Alice')
        assert(not row.sent:IsShown() and row.reply:GetText()=='' and #MOCK.sent==2)
        MOCK.fire('CHAT_MSG_WHISPER_INFORM',A.Message(),'Alice')
        assert(row.sent:IsShown() and row.reply:GetText()=='')
        """)

    def test_failed_whispers_and_private_reply_arguments_do_not_create_false_flags(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice')});MOCK.selectAll()
        MOCK.sendError=true;A.SendSelected()
        assert(not MOCK.row('Alice').sent:IsShown() and not A.contacts[A.NameKey('Alice')])
        MOCK.fire('CHAT_MSG_WHISPER','Hello','Alice')
        assert(MOCK.row('Alice').reply:GetText()=='')
        MOCK.sendError=false;MOCK.selectAll();A.SendSelected()
        MOCK.fire('CHAT_MSG_WHISPER',MOCK.secret(),'Alice')
        MOCK.fire('CHAT_MSG_WHISPER','Secret sender',MOCK.secret())
        assert(not MOCK.row('Alice').sent:IsShown() and MOCK.row('Alice').reply:GetText()=='')
        """)

    def test_a_player_who_replied_is_no_longer_counted_as_awaiting_a_reply(self):
        self.check("""
        A.UI.Open();MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')})
        MOCK.selectAll();A.SendSelected();MOCK.advance(1)
        assert(A.UI.frame.summary:GetText():find('2 awaiting replies',1,true))
        MOCK.fire('CHAT_MSG_WHISPER','No thanks','Alice')
        assert(A.UI.frame.summary:GetText():find('1 awaiting replies',1,true))
        assert(#MOCK.invited==0 and #MOCK.sent==2)
        """)

    def test_lost_permissions_or_unknown_group_data_stop_new_messages(self):
        self.check("""
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected()
        MOCK.groupCount=2;MOCK.permissions=false;MOCK.advance(1)
        assert(#MOCK.sent==1 and not A.queue and next(A.tickets)==nil)
        MOCK.permissions=true
        GetNumGroupMembers=function()return MOCK.secret()end
        assert(not A.SendSelected() and #MOCK.sent==1)
        """)

    def test_open_from_options_shows_recruitment_and_hides_settings(self):
        self.check("""
        SettingsPanel:Show()
        MOCK.click(MOCK.button('Open recruitment window'))
        assert(ElmoLFMFrame:IsShown() and not SettingsPanel:IsShown())
        assert(#MOCK.requests==0 and #MOCK.sent==0 and #MOCK.invited==0)
        """)

    def test_reply_counter_and_joined_members_update_after_an_invitation(self):
        self.check("""
        A.UI.Open()
        MOCK.search({MOCK.player('Alice'),MOCK.player('Bob')});MOCK.selectAll();A.SendSelected();MOCK.advance(1)
        A.HandleWhisper('inv','Alice')
        assert(A.UI.frame.summary:GetText():find('1 awaiting replies',1,true))
        MOCK.members[A.NameKey('Alice')]=true;MOCK.groupCount=2;MOCK.fire('GROUP_ROSTER_UPDATE')
        assert(not A.tickets[A.NameKey('Alice')] and not A.invites[A.NameKey('Alice')])
        assert(A.UI.frame.summary:GetText():find('1 awaiting replies',1,true))
        """)

    def test_minimap_button_opens_window_and_options_without_network_actions(self):
        self.check("""
        local button=LibStub('LibDBIcon-1.0'):GetMinimapButton('ElmoLFM')
        assert(button and button:IsShown() and button.db==A.db.minimap)
        button.scripts.OnClick(button,'LeftButton');assert(ElmoLFMFrame:IsShown())
        button.scripts.OnClick(button,'LeftButton');assert(not ElmoLFMFrame:IsShown())
        button.scripts.OnClick(button,'RightButton');assert(MOCK.openCategory==123)
        assert(#MOCK.requests==0 and #MOCK.sent==0 and #MOCK.invited==0)
        """)

    def test_minimap_drag_and_visibility_preferences(self):
        self.check("""
        local button=LibStub('LibDBIcon-1.0'):GetMinimapButton('ElmoLFM')
        button.scripts.OnDragStart(button);MOCK.advance(.2);button.scripts.OnDragStop(button)
        assert(math.abs(A.db.minimap.minimapPos-180)<.01)
        A.Command('minimap hide');assert(A.db.minimap.hide and not button:IsShown())
        A.Command('minimap');assert(not A.db.minimap.hide and button:IsShown())
        """)
        hidden = create_vm(self.legacy, {"minimap": {"minimapPos": 73, "hide": True}})
        hidden.execute("""
        local button=LibStub('LibDBIcon-1.0'):GetMinimapButton('ElmoLFM')
        assert(not button:IsShown() and A.db.minimap.minimapPos==73)
        """)

    def test_search_button_only_prepares_chat_until_the_player_presses_enter(self):
        self.check("""
        A.UI.Open()
        MOCK.click(A.UI.frame.search)
        assert(#MOCK.requests==0 and A.search and MOCK.chatCommand)
        MOCK.advance(5);assert(#MOCK.requests==0)
        MOCK.enterChat();MOCK.results({MOCK.player('Alice')})
        assert(#MOCK.requests==1 and #A.results==1 and not A.search)
        """)

    def test_blocked_who_exits_immediately_without_waiting_for_a_timeout(self):
        self.check("""
        assert(A.Search('Alterac Mountains',38,40))
        MOCK.fire('ADDON_ACTION_BLOCKED','ElmoLFM','C_FriendList.SendWho()')
        assert(not A.search and A.error and A.status:find('blocked',1,true))
        assert(MOCK.routing[#MOCK.routing]==false)
        local message=A.status;MOCK.advance(30);assert(A.status==message and #MOCK.requests==0)
        """)

    def test_copy_command_and_native_results_work_without_a_callable_sender(self):
        self.check("""
        if C_FriendList then C_FriendList.SendWho=nil else SendWho=nil end
        ChatFrameUtil,ChatFrame_OpenChat=nil,nil
        A.UI.Open();MOCK.click(A.UI.frame.search)
        assert(A.search and #MOCK.requests==0)
        local command=A.UI.frame.query
        command.scripts.OnEditFocusGained(command);assert(command.highlighted)
        MOCK.chatCommand=command:GetText();MOCK.enterChat()
        MOCK.results({MOCK.player('Alice')})
        assert(#A.results==1 and not A.search)
        """)

    def test_cancelled_native_chat_is_not_executed_on_timer_or_reload(self):
        self.check("""
        assert(A.Search('Alterac Mountains',38,40));MOCK.chatCommand=nil
        MOCK.advance(30);assert(A.search and #MOCK.requests==0)
        A.Stop();MOCK.results({MOCK.player('Late')})
        assert(not A.search and #A.results==0 and #MOCK.requests==0)
        """)


class EraTests(RecruitmentTests):
    legacy = True


if __name__ == "__main__":
    unittest.main()
