"""Autojoin preference and checkbox behavior with simulated chat/invitations."""
import unittest
import test_ui


class AutojoinTests(unittest.TestCase):
    def setUp(self):
        test_ui.ElmoLFGUITests.setUp(self)

    def check(self, code):
        self.lua.execute(code)

    def test_checkbox_stops_only_new_invites_and_takes_effect_immediately(self):
        self.check('''
        assert(A.db.autoJoin==true and ElmoLFGAutojoin:GetChecked())
        A.db.selected['q:147']=true;assert(A.StartAnnouncing())
        assert(A.HandleWhisper('inv','Alice') and #invited==1)
        local count=#sent
        ElmoLFGAutojoin:SetChecked(false)
        ElmoLFGAutojoin.scripts.OnClick(ElmoLFGAutojoin)
        A.HandleWhisper('inv','Bob')
        assert(not A.db.autoJoin and A.announcing and #invited==1 and #sent==count)
        assert(not A.GetAnnouncementText():find('autojoin',1,true))
        ElmoLFGAutojoin:SetChecked(true)
        ElmoLFGAutojoin.scripts.OnClick(ElmoLFGAutojoin)
        assert(A.HandleWhisper('inv','Bob') and #invited==2 and #sent==count)
        ''')

    def test_disabled_preference_survives_database_initialization(self):
        self.check('''
        A.db.autoJoin=false;A.InitializeDB();A.Refresh(true)
        assert(A.db.autoJoin==false and not ElmoLFGAutojoin:GetChecked())
        A.db.selected['q:147']=true
        local ok,message=A.StartAnnouncing()
        assert(ok and message:find('off',1,true) and A.announcing)
        A.HandleWhisper('inv','Alice');assert(#invited==0)
        ''')

    def test_custom_text_survives_toggling_the_flag(self):
        self.check('''
        A.SetAnnouncementText('My custom invitation text');A.Refresh(true)
        ElmoLFGAutojoin:SetChecked(false)
        ElmoLFGAutojoin.scripts.OnClick(ElmoLFGAutojoin)
        assert(A.GetAnnouncementText()=='My custom invitation text' and #sent==0)
        ''')

    def test_pending_announcement_prompt_and_status_reflect_disabled_autojoin(self):
        self.check('''
        A.db.selected['q:147']=true;assert(A.StartAnnouncing())
        ElmoLFGAutojoin:SetChecked(false)
        ElmoLFGAutojoin.scripts.OnClick(ElmoLFGAutojoin)
        now=130;ticker();ElmoLFGFrame:Hide()
        assert(ElmoLFGAnnouncementPrompt:IsShown())
        assert(ElmoLFGAnnouncementPrompt.detail:GetText():find('Autojoin OFF',1,true))
        A.HandleWhisper('inv','Alice');assert(#invited==0 and #sent==1)
        local off=false
        for _,f in ipairs(frames)do
            if f.kind=='FontString' and f:GetText():find('Auto-invite: OFF',1,true)then off=true end
        end
        assert(off)
        ''')

    def test_dungeon_invites_still_require_an_available_role_when_enabled(self):
        self.check('''
        A.db.selected['d:dm']=true;A.SetPlayerRole('dps');assert(A.StartAnnouncing())
        assert(not A.HandleWhisper('inv','Alice') and #invited==0)
        assert(A.HandleWhisper('inv tank','Alice') and #invited==1)
        ElmoLFGAutojoin:SetChecked(false)
        ElmoLFGAutojoin.scripts.OnClick(ElmoLFGAutojoin)
        A.HandleWhisper('inv heal','Bob');assert(#invited==1)
        ''')


if __name__ == '__main__':
    unittest.main()
