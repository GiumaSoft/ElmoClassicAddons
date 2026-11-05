"""Saved settings and command continuity across the ElmoLFG rename."""
import unittest
import test_core
import test_ui


class RenameSettingsTests(unittest.TestCase):
    def setUp(self):
        test_core.ElmoLFGTests.setUp(self)

    def test_classic_settings_import_preserves_autojoin_custom_text_and_position(self):
        self.lua.execute('''
        ElmoLFGDB=nil
        ClassicQuestLFGDB={selected={['q:147']=true},autoJoin=false,
            customMessage='A relaxed run',minimap={minimapPos=81},
            playerRole='Healer',recruitmentRoles=true,announcementInterval=90,stopAtPlayers=3}
        local old=ClassicQuestLFGDB
        A.InitializeDB()
        assert(A.db==old and ElmoLFGDB==old and A.db.selected['q:147'])
        assert(not A.db.autoJoin and A.db.customMessage=='A relaxed run')
        assert(A.db.minimap.minimapPos==81 and A.db.playerRole=='Healer')
        assert(A.db.announcementInterval==90 and A.db.stopAtPlayers==3)
        assert(not A.announcing and #sent==0 and #invited==0)
        ''')

    def test_new_settings_take_precedence_and_oldest_name_is_supported(self):
        self.lua.execute('''
        local current=ElmoLFGDB
        ClassicQuestLFGDB={autoJoin=false};QuestLFGDB={customMessage='older'}
        A.InitializeDB();assert(A.db==current and ElmoLFGDB==current)
        ElmoLFGDB=nil;ClassicQuestLFGDB=nil
        A.InitializeDB();assert(A.db==QuestLFGDB and A.db.customMessage=='older')
        ''')

    def test_load_on_demand_importer_reads_the_old_saved_variable_before_migration(self):
        self.lua.execute('''
        ElmoLFGDB=nil;ClassicQuestLFGDB=nil;QuestLFGDB=nil
        C_AddOns={GetAddOnMetadata=function(folder,key)
            assert(key=='X-ElmoLFG-Legacy');return folder=='ClassicQuestLFG' and '1'
        end,LoadAddOn=function(folder)
            assert(folder=='ClassicQuestLFG');ClassicQuestLFGDB={autoJoin=false,customMessage='Imported'}
        end}
        A.InitializeDB()
        assert(A.db==ClassicQuestLFGDB and not A.db.autoJoin and A.db.customMessage=='Imported')
        assert(#sent==0 and #invited==0)
        ''')

    def test_unmarked_old_addons_are_not_explicitly_started_by_the_importer(self):
        self.lua.execute('''
        ElmoLFGDB=nil;ClassicQuestLFGDB=nil;QuestLFGDB=nil
        C_AddOns={GetAddOnMetadata=function()return nil end,
            LoadAddOn=function()error('Must not start old runtime')end}
        A.InitializeDB();assert(A.db==ElmoLFGDB and A.db.autoJoin and #sent==0)
        ''')


class RenameInterfaceTests(unittest.TestCase):
    def setUp(self):
        test_ui.ElmoLFGUITests.setUp(self)

    def test_new_name_and_all_previous_commands_toggle_the_same_window(self):
        self.lua.execute('''
        assert(ElmoLFGFrame and not ClassicQuestLFGFrame)
        assert(SLASH_ELMOLFG1=='/elmolfg' and SLASH_ELMOLFG2=='/elfg')
        assert(SLASH_ELMOLFG3=='/qlfg' and SLASH_ELMOLFG4=='/questlfg')
        assert(SLASH_ELMOLFG5=='/cqlfg' and SLASH_ELMOLFG6=='/classicquestlfg')
        ElmoLFGFrame:Hide();SlashCmdList.ELMOLFG('');assert(ElmoLFGFrame:IsShown())
        assert(not A.announcing and #sent==0 and #invited==0)
        ''')
