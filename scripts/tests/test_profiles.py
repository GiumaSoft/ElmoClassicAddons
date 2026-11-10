"""Current profiles survive removal of retired addon importers. Simulated Lua 5.1."""
from pathlib import Path
import importlib.util
import unittest

HERE = Path(__file__).resolve().parent

def fixture(name, path):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ProfileTests(unittest.TestCase):
    def test_leveling_preserves_current_profile_and_never_loads_importers(self):
        module = fixture('leveling_profile', 'leveling_era/test_addon.py')
        case = module.LevelingTests(); case.setUp()
        case.vm.execute("""
        ElmoLevelingDB={xp=37,seconds=20,locked=true,hidden=true}
        local saved=ElmoLevelingDB
        ClassicLevelingDB={xp=9999};ForeverLevelingTrackerDB={xp=8888}
        MOCK.start()
        assert(A.db==saved and saved.xp==37 and saved.seconds==20 and saved.locked and saved.hidden)
        assert(ClassicLeveling==nil and ClassicLevelingForever==nil and ForeverLeveling==nil)
        assert(ClassicLevelingDB.xp==9999 and ForeverLevelingTrackerDB.xp==8888)
        """)

    def test_plater_preserves_current_preferences_without_old_target_settings(self):
        module = fixture('plater_profile', 'ElmoPlater/fixture.py')
        vm, _ = module.create_vm()
        vm.execute("""
        ElmoPlaterDB={plateAuraSize=30,questKills=false}
        local saved=ElmoPlaterDB
        ClassicTargetDB={plateAuraSize=16,questKills=true}
        C_AddOns={LoadAddOn=function()error('Retired importer called')end}
        MOCK.start()
        assert(A.db==saved and saved.plateAuraSize==30 and not saved.questKills)
        assert(ClassicTarget==nil and ClassicPlater==nil and ClassicTargetDB.plateAuraSize==16)
        assert(SLASH_ELMOPLATER3==nil and SlashCmdList.CLASSICTARGET==nil)
        """)

    def test_spell_tracker_keeps_current_bar_and_ignores_retired_profiles(self):
        module = fixture('spell_profile', 'ElmoSpellTracker/test_addon.py')
        case = module.CooldownTests(); case.setUp()
        case.vm.execute("""
        MOCK.spell(100)
        ElmoSpellTrackerDB={maxSkills=6,locked=true,spells={100},point='CENTER',x=42,y=10}
        local saved=ElmoSpellTrackerDB
        ClassicSpellsTrackerDB={maxSkills=2,spells={999}}
        C_AddOns={LoadAddOn=function()error('Retired importer called')end}
        MOCK.start()
        assert(A.db==saved and saved.locked and saved.maxSkills==6 and saved.spells[1]==100 and saved.x==42)
        assert(ClassicSpellsTracker==nil and SlashCmdList.CLASSICSPELLSTRACKER==nil)
        assert(ClassicSpellsTrackerDB.spells[1]==999)
        """)

if __name__ == '__main__':
    unittest.main()
