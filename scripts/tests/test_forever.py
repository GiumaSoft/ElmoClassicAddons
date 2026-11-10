"""Dual-client package checks plus modern/restricted API regressions. No live input."""
import os
import sys
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STAGE=ROOT/'.build'/'forever'

class ForeverTests(unittest.TestCase):
    def test_all_packages_and_versions(self):
        for client,interface in [('classic',11509),('forever',16001)]:
            for source in sorted(ROOT.glob('Elmo*')):
                manifest=source/(source.name+'.toc')
                if not manifest.is_file():continue
                name=source.name
                version=next(line.split(':',1)[1].strip() for line in manifest.read_text().splitlines()
                    if line.startswith('## Version:'))
                path=ROOT/'.build'/client/name
                toc=(path/(name+'.toc')).read_text()
                self.assertIn('## Interface: '+str(interface),toc)
                self.assertIn('## Version: '+version,toc)
                vm=LuaRuntime()
                compile=vm.eval('function(s,n)assert(loadstring(s,n))end')
                for file in path.rglob('*.lua'):compile(file.read_text(),str(file))

    def test_forever_nameplates_and_restricted_fallback(self):
        sys.path.insert(0,str(HERE/'ElmoPlater'))
        from fixture import create_vm
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            vm,_=create_vm()
        vm.execute('''
        function GetBuildInfo()return '1.60.1','70790','',16001 end
        MOCK.start()
        MOCK.event('PLAYER_ENTERING_WORLD')
        local mob,plate=MOCK.mob('nameplate9','Creature-forever','Forever enemy')
        local record=A.units.nameplate9
        assert(record and record.frame:IsShown() and plate.UnitFrame.alpha==0)
        SECRET=setmetatable({}, {__index=function()error('Secret value indexed')end})
        function issecretvalue(v)return rawequal(v,SECRET)end
        local health,guid=UnitHealth,UnitGUID
        UnitHealth=function(unit)if unit=='nameplate9' then return SECRET end;return health(unit)end
        A.Update(false)
        assert(record.frame:IsShown() and plate.UnitFrame.alpha==0 and record.privateHealth)
        assert(rawequal(record.frame.bar.value,SECRET) and not A.priorityTarget)
        UnitHealth=health;A.Update(false)
        assert(record.frame:IsShown() and plate.UnitFrame.alpha==0)
        UnitGUID=function(unit)if unit=='nameplate9' then return SECRET end;return guid(unit)end
        A.Update(false);assert(not record.frame:IsShown() and plate.UnitFrame.alpha==1)
        UnitGUID=guid
        local aura=C_UnitAuras.GetAuraDataByIndex
        C_UnitAuras.GetAuraDataByIndex=function()return SECRET end
        A.Update(true);assert(not record.missing and not record.aurasKnown)
        C_UnitAuras.GetAuraDataByIndex=aura
        assert(A.RegisterCombatLog==nil and A.CombatLog==nil)
        assert(not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
        A.Remove('nameplate9');assert(plate.UnitFrame.alpha==1)
        assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
        ''')

    def test_forever_never_touches_restricted_combat_log(self):
        sys.path.insert(0,str(HERE/'ElmoPlater'))
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            runpy.run_path(str(HERE/'ElmoPlater/test_forever_combat_log.py'))

    def test_forever_displays_secret_health(self):
        sys.path.insert(0,str(HERE/'ElmoPlater'))
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            runpy.run_path(str(HERE/'ElmoPlater/test_secret_health.py'))

    def test_forever_displays_personal_auras_with_protected_fields(self):
        sys.path.insert(0,str(HERE/'ElmoPlater'))
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            runpy.run_path(str(HERE/'ElmoPlater/test_secret_auras.py'))

    def test_forever_delegates_restricted_auras_to_blizzard(self):
        sys.path.insert(0,str(HERE/'ElmoPlater'))
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            runpy.run_path(str(HERE/'ElmoPlater/test_aura_containers.py'))

    def test_forever_cooldowns_and_secret_values(self):
        vm=LuaRuntime(unpack_returned_tuples=True)
        vm.execute((HERE/'ElmoSpellTracker/wow_mock.lua').read_text())
        ns=vm.table();loader=vm.eval('function(s,n,ns)assert(loadstring(s,"@"..n))("ElmoSpellTracker",ns)end')
        addon=STAGE/'ElmoSpellTracker'
        for name in (addon/'ElmoSpellTracker.toc').read_text().splitlines():
            if name.endswith('.lua'):loader((addon/name).read_text(),name,ns)
        vm.globals().A=ns
        vm.execute('''
        GetSpellInfo=nil;GetSpellCooldown=nil;IsUsableSpell=nil
        MOCK.spell(100,'Forever ability');MOCK.start()
        MOCK.cooldown(100,6);MOCK.cast(100);MOCK.advance(.1)
        assert(#A.db.spells==1 and A.UI.icons[1].texture.desaturated)
        assert(A.UI.icons[1].timer:GetText()=='6')
        MOCK.advance(7);assert(not A.UI.icons[1].texture.desaturated)
        MOCK.spells[100].insufficientPower=true
        MOCK.event('UNIT_POWER_UPDATE','player','RAGE');MOCK.advance(.2)
        assert(A.UI.icons[1].texture.desaturated)
        SECRET=setmetatable({}, {__index=function()error('Secret value indexed')end})
        function issecretvalue(v)return rawequal(v,SECRET)end
        C_Spell.GetSpellCooldown=function()return SECRET end
        C_Spell.GetSpellCharges=function()return SECRET end
        C_Spell.GetSpellCooldownDuration=function()return SECRET end
        C_Spell.GetSpellBaseCooldown=function()return SECRET end
        A.UI.Update();assert(A.UI.icons[1].timer:GetText()=='?')
        A.Observe(SECRET);assert(#A.db.spells==1)
        C_Spell.GetSpellInfo=function()return SECRET end
        assert(A.Spells.Info(200)==nil)
        ''')

if __name__=='__main__':unittest.main()
