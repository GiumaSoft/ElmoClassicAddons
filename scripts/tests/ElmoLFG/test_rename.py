"""Saved settings and command continuity across the ElmoLFG rename."""
import unittest
import test_core
import test_ui


class RenameSettingsTests(unittest.TestCase):
    def setUp(self):
        test_core.ElmoLFGTests.setUp(self)

    def test_current_profile_preserves_autojoin_custom_text_and_position(self):
        self.lua.execute('''
        ElmoLFGDB={selected={['q:147']=true},autoJoin=false,
            customMessage='A relaxed run',minimap={minimapPos=81},
            playerRole='Healer',recruitmentRoles=true,announcementInterval=90,stopAtPlayers=3}
        local current=ElmoLFGDB
        A.InitializeDB()
        assert(A.db==current and A.db.selected['q:147'])
        assert(not A.db.autoJoin and A.db.customMessage=='A relaxed run')
        assert(A.db.minimap.minimapPos==81 and A.db.playerRole=='Healer')
        assert(A.db.announcementInterval==90 and A.db.stopAtPlayers==3)
        assert(not A.announcing and #sent==0 and #invited==0)
        ''')

    def test_retired_profiles_are_never_loaded_or_imported(self):
        self.lua.execute('''
        ElmoLFGDB=nil
        ClassicQuestLFGDB={autoJoin=false};QuestLFGDB={customMessage='older'}
        C_AddOns={GetAddOnMetadata=function()error('No importer metadata lookup')end,
            LoadAddOn=function()error('No legacy addon should be loaded')end}
        A.InitializeDB()
        assert(A.db==ElmoLFGDB and A.db~=ClassicQuestLFGDB and A.db~=QuestLFGDB)
        assert(A.db.autoJoin and A.db.customMessage==nil and #sent==0 and #invited==0)
        ''')

    def test_current_profile_is_independent_of_stale_legacy_globals(self):
        self.lua.execute('''
        local current=ElmoLFGDB
        ClassicQuestLFGDB={autoJoin=false};QuestLFGDB={customMessage='older'}
        A.InitializeDB();assert(A.db==current and ElmoLFGDB==current)
        ''')


class RenameInterfaceTests(unittest.TestCase):
    def setUp(self):
        test_ui.ElmoLFGUITests.setUp(self)

    def test_only_current_elmo_commands_toggle_the_window(self):
        self.lua.execute('''
        assert(ElmoLFGFrame and not ClassicQuestLFGFrame)
        assert(SLASH_ELMOLFG1=='/elmolfg' and SLASH_ELMOLFG2=='/elfg')
        assert(SLASH_ELMOLFG3==nil and SLASH_ELMOLFG5==nil)
        ElmoLFGFrame:Hide();SlashCmdList.ELMOLFG('');assert(ElmoLFGFrame:IsShown())
        assert(not A.announcing and #sent==0 and #invited==0)
        ''')
