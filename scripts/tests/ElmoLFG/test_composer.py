"""Automatic prefix plus editable custom tail, using real Lua and simulated UI."""
import unittest
import test_ui


class ElmoLFGComposerTests(unittest.TestCase):
    def setUp(self):
        test_ui.ElmoLFGUITests.setUp(self)
        self.lua.execute("level=40; A.db.selected={['d:gnomer']=true}; A.SetPlayerRole('dps'); A.Refresh(true)")

    def check(self, code):
        self.lua.execute(code)

    def test_default_hint_is_not_a_custom_override(self):
        self.check("""
            assert(not A.IsCustomAnnouncement())
            assert(ElmoLFGCustomMessage:GetText()=='- /w me inv role (tank, heal, dps)(autojoin)')
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Tank | 1 Heal | 2 Dps - /w me inv role (tank, heal, dps)(autojoin)')
        """)

    def test_preview_is_read_only_and_custom_input_is_editable(self):
        self.check("""
            assert(ElmoLFGAnnouncementPreview.kind=='Frame')
            assert(ElmoLFGAnnouncementPreview.text.kind=='FontString')
            assert(ElmoLFGCustomMessage.kind=='EditBox')
            assert(ElmoLFGAnnouncementPreview.text:GetText()==A.BuildMessage())
        """)

    def test_typing_changes_only_the_tail_without_posting(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run')
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Tank | 1 Heal | 2 Dps friendly run')
            assert(A.GetAnnouncementText()=='friendly run' and #sent==0)
        """)

    def test_refresh_does_not_reset_the_input_or_caret(self):
        self.check("""
            local input=ElmoLFGCustomMessage;local set=input.SetText;input.writes=0
            input.SetText=function(self,text)self.writes=self.writes+1;return set(self,text)end
            input:SetText('friendly run');local writes=input.writes
            for i=1,10 do now=now+1;ElmoLFGFrame.scripts.OnUpdate(ElmoLFGFrame,1)end
            assert(input:GetText()=='friendly run' and input.writes==writes)
        """)

    def test_own_role_changes_rebuild_the_prefix(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');A.SetPlayerRole('tank');A.Refresh(true)
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Heal | 3 Dps friendly run')
            assert(ElmoLFGCustomMessage:GetText()=='friendly run')
        """)

    def test_party_join_and_leave_update_vacancies_without_changing_custom_text(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run')
            setParty({{name='Alice',role='TANK'}});fire('GROUP_ROSTER_UPDATE')
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Heal | 2 Dps friendly run')
            setParty({{name='Alice',role='TANK'},{name='Bob',class='PRIEST',role='HEALER'}})
            fire('GROUP_ROSTER_UPDATE');assert(A.BuildMessage()=='LFM Gnomeregan need 2 Dps friendly run')
            setParty({{name='Alice',role='TANK'}});fire('GROUP_ROSTER_UPDATE')
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Heal | 2 Dps friendly run')
        """)

    def test_role_picker_rebuilds_an_edited_announcement(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');setParty({{name='Alice'}})
            fire('GROUP_ROSTER_UPDATE');assert(A.BuildMessage():find('need 3 slots (assign group roles)',1,true))
            click('Group roles');local row
            for _,f in ipairs(frames)do if f.member and f.member.name=='Alice-Realm'then row=f end end
            row.buttons.Tank.scripts.OnClick(row.buttons.Tank)
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Heal | 2 Dps friendly run')
            assert(ElmoLFGAnnouncementPreview.text:GetText()==A.BuildMessage())
        """)

    def test_custom_text_cannot_replace_the_prefix(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('LFM somewhere else')
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Tank | 1 Heal | 2 Dps LFM somewhere else')
        """)

    def test_empty_custom_text_is_valid(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('');local message,err=A.BuildMessage();assert(not err)
            assert(message=='LFM Gnomeregan need 1 Tank | 1 Heal | 2 Dps')
            assert(A.SendAnnouncement() and sent[1].message==A.BuildMessage(true))
        """)

    def test_custom_text_survives_activity_changes(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');A.db.selected={['d:dm']=true};A.Refresh(true)
            assert(A.BuildMessage()=='LFM The Deadmines need 1 Tank | 1 Heal | 2 Dps friendly run')
            A.db.selected={['q:147']=true};A.Refresh(true)
            assert(A.BuildMessage():find('LFM Quest 4/5:',1,true)==1)
            assert(A.GetAnnouncementText()=='friendly run')
        """)

    def test_default_hint_follows_selection_without_becoming_custom(self):
        self.check("""
            A.db.selected={['q:147']=true};A.Refresh(true)
            assert(ElmoLFGCustomMessage:GetText()=='- /w me inv (autojoin)' and not A.IsCustomAnnouncement())
            A.db.selected={['d:gnomer']=true};A.Refresh(true)
            assert(ElmoLFGCustomMessage:GetText():find('inv role',1,true) and not A.IsCustomAnnouncement())
        """)

    def test_reset_restores_the_default_tail_with_current_roles(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');A.SetPlayerRole('tank');A.Refresh(true)
            click('Reset text');assert(not A.IsCustomAnnouncement())
            assert(A.BuildMessage()=='LFM Gnomeregan need 1 Heal | 3 Dps - /w me inv role (tank, heal, dps)(autojoin)')
        """)

    def test_post_uses_the_latest_composition(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');setParty({{name='Alice',role='TANK'}})
            fire('GROUP_ROSTER_UPDATE');click('Post announce')
            assert(#sent==1 and sent[1].message=='LFM Gnomeregan need 1 Heal / 2 Dps friendly run')
        """)

    def test_cathedral_post_does_not_send_invalid_role_escape_codes(self):
        self.check("""
            level=37;A.db.selected={['d:smcath']=true};A.SetPlayerRole('dps')
            setParty({{name='Tank',role='TANK'}})
            ElmoLFGCustomMessage:SetText('- /w me inv (autojoin)');fire('GROUP_ROSTER_UPDATE')
            local original=SendChatMessage
            SendChatMessage=function(message,...)
                assert(not message:find('| ',1,true),'SendChatMessage(): Invalid escape code in chat message')
                return original(message,...)
            end
            click('Post announce')
            assert(#sent==1,'Dungeon announcement was rejected by the chat API')
            assert(sent[1].message=='LFM Scarlet Monastery - Cathedral need 1 Heal / 2 Dps - /w me inv (autojoin)')
        """)

    def test_guild_repeats_rebuild_roles_with_the_custom_tail(self):
        self.check("""
            inGuild=true;A.db.channel='GUILD';ElmoLFGCustomMessage:SetText('friendly run')
            assert(A.StartAnnouncing())
            setParty({{name='Alice',role='TANK'},{name='Bob',class='PRIEST',role='HEALER'}})
            fire('GROUP_ROSTER_UPDATE');now=130;ticker()
            assert(#sent==2 and sent[2].message=='LFM Gnomeregan need 2 Dps friendly run')
        """)

    def test_public_reminder_keeps_current_roles_and_waits_for_a_click(self):
        self.check("""
            A.db.channel='YELL';ElmoLFGCustomMessage:SetText('friendly run');assert(A.StartAnnouncing())
            fire('CHAT_MSG_WHISPER','inv tank','Alice-Realm');setParty({{name='Alice'}})
            fire('GROUP_ROSTER_UPDATE');now=130;ticker();assert(A.announcementPending and #sent==1)
            click('Post announce');assert(#sent==2)
            assert(sent[2].message=='LFM Gnomeregan need 1 Heal / 2 Dps friendly run')
        """)

    def test_edit_in_chat_opens_the_current_assembled_message(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');setParty({{name='Alice',role='TANK'}})
            fire('GROUP_ROSTER_UPDATE');assert(A.EditAnnouncement())
            assert(opened=='/4 LFM Gnomeregan need 1 Heal / 2 Dps friendly run')
        """)

    def test_byte_limit_includes_the_prefix_and_utf8(self):
        self.check("""
            local prefix=A.BuildGeneratedMessage(true)
            ElmoLFGCustomMessage:SetText(string.rep('x',255-#prefix-1))
            local message,err,n=A.BuildMessage(true);assert(not err and n==255 and #message==255)
            ElmoLFGCustomMessage:SetText(A.GetAnnouncementText()..'x')
            message,err,n=A.BuildMessage(true);assert(err and n==256)
            assert(not A.SendAnnouncement() and #sent==0)
            ElmoLFGCustomMessage:SetText(string.rep('é',128))
            message,err,n=A.BuildMessage(true);assert(err and n==#prefix+1+256)
        """)

    def test_roster_change_clears_a_resolved_size_error(self):
        self.check("""
            local prefix=A.BuildGeneratedMessage(true)
            ElmoLFGCustomMessage:SetText(string.rep('x',256-#prefix-1))
            local _,err=A.BuildMessage();assert(err);local errorLabel
            for _,f in ipairs(frames)do if f.kind=='FontString' and f:GetText()==err then errorLabel=f end end
            assert(errorLabel)
            setParty({{name='Alice',role='TANK'}});fire('GROUP_ROSTER_UPDATE')
            local message;message,err=A.BuildMessage();assert(not err)
            assert(errorLabel:GetText()=='' and #message<=255)
        """)

    def test_shorter_custom_text_fixes_an_oversized_legacy_note(self):
        self.check("""
            A.db.note=string.rep('x',300);A.Refresh(true);local _,err=A.BuildMessage();assert(err)
            ElmoLFGCustomMessage:SetText('brief run');local message;message,err=A.BuildMessage();assert(not err)
            assert(message=='LFM Gnomeregan need 1 Tank | 1 Heal | 2 Dps brief run')
        """)

    def test_custom_text_cannot_bypass_activity_or_link_validation(self):
        self.check("""
            ElmoLFGCustomMessage:SetText('friendly run');A.db.selected={};A.Refresh(true)
            assert(not A.SendAnnouncement() and #sent==0)
            A.db.selected={['q:147']=true};GetQuestLink=function()return nil end;A.Refresh(true)
            assert(not A.SendAnnouncement() and #sent==0)
        """)

    def test_a_short_edit_cannot_replace_an_oversized_prefix(self):
        self.check("""
            A.db.selected={['q:147']=true}
            GetQuestLink=function(id)return '|Hquest:'..id..':10|h['..string.rep('x',300)..']|h' end
            A.Refresh(true);ElmoLFGCustomMessage:SetText('');local _,err=A.BuildMessage();assert(err)
            assert(not A.SendAnnouncement() and #sent==0)
        """)

    def test_questie_links_are_converted_in_the_prefix_and_custom_tail(self):
        self.check("""
            Questie={started=true};A.db.selected={['q:147']=true};A.Refresh(true)
            ElmoLFGCustomMessage:SetText(GetQuestLink(147)..' 100% ready')
            local display,err,n=A.BuildMessage();assert(not err and display:find('|Hquest:147:',1,true))
            local wire=A.BuildMessage(true);assert(not wire:find('|Hquest:',1,true))
            assert(wire:find('[[10] Manhunt (147)] 100% ready',1,true))
            assert(n==#wire and A.SendAnnouncement() and sent[1].message==wire)
        """)

    def test_native_links_custom_separators_and_whitespace_are_preserved(self):
        self.check("""
            A.db.selected={['q:147']=true};A.Refresh(true)
            ElmoLFGCustomMessage:SetText(GetQuestLink(147)..' 100% ready')
            assert(A.BuildMessage(true):find('|Hquest:147:',1,true))
            ElmoLFGCustomMessage:SetText('  relaxed | '..string.char(10)..' room  ')
            assert(A.BuildMessage(true):sub(-14)=='relaxed | room')
        """)

    def test_custom_text_is_saved_and_old_notes_survive_until_edited(self):
        self.check("""
            A.db.note='old route';A.Refresh(true)
            assert(ElmoLFGCustomMessage:GetText()=='- old route - /w me inv role (tank, heal, dps)(autojoin)')
            ElmoLFGCustomMessage:SetText('new route');assert(A.db.note=='')
            A.InitializeDB();A.Refresh(true)
            assert(A.db.customMessage=='new route' and ElmoLFGCustomMessage:GetText()=='new route')
        """)


if __name__ == '__main__':
    unittest.main(verbosity=2)
