"""Dual-client package checks plus modern/restricted API regressions. No live input."""
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STAGE=ROOT/'.build'/'forever'

def load_dungeon():
    vm=LuaRuntime(unpack_returned_tuples=True)
    for name in ['wow_mock.lua','journal_mock.lua']:vm.execute((HERE/'dungeon'/name).read_text())
    vm.execute('''
    GetNumQuestLogEntries=nil;GetQuestLogTitle=nil;GetQuestLogIndexByID=nil
    C_QuestLog={GetNumQuestLogEntries=function()return 1 end,
        GetInfo=function(i)return {questID=96393,isHeader=false}end,
        IsQuestFlaggedCompleted=function(id)return id==96391 end}
    C_Map={GetMapInfo=function(id)return {name=id==1426 and 'Dun Morogh' or 'Map '..id}end}
    C_TooltipInfo={GetHyperlink=function()return {lines={{leftText='Equip: +18 Spell Power'}}}end}
    ''')
    ns=vm.table();loader=vm.eval('function(s,n,ns)assert(loadstring(s,"@"..n))("ElmoDungeonLoot",ns)end')
    addon=STAGE/'ElmoDungeonLoot'
    for name in (addon/'ElmoDungeonLoot.toc').read_text().splitlines():
        if name.endswith('.lua'):loader((addon/name).read_text(),name,ns)
    vm.globals().CD=ns
    vm.execute("CD.frame:GetScript('OnEvent')(CD.frame,'ADDON_LOADED','ElmoDungeonLoot')")
    return vm

class ForeverTests(unittest.TestCase):
    def test_all_packages_and_versions(self):
        for client,interface in [('classic',11509),('forever',16001)]:
            for name,version in [('ElmoLeveling','1.6.3'),('ElmoPlater','2.0.7'),('ElmoDungeonLoot','2.2.0'),('ElmoSpellTracker','1.0.2')]:
                path=ROOT/'.build'/client/name
                toc=(path/(name+'.toc')).read_text()
                self.assertIn('## Interface: '+str(interface),toc)
                self.assertIn('## Version: '+version,toc)
                vm=LuaRuntime()
                compile=vm.eval('function(s,n)assert(loadstring(s,n))end')
                for file in path.rglob('*.lua'):compile(file.read_text(),str(file))

    def test_forever_catalog_and_cold_cache_stats(self):
        vm=load_dungeon()
        vm.execute('''
        assert(#CD.Catalog.order==35 and CD.Catalog.meta.client=='forever')
        local item=CD.Items.Read(270256)
        assert(item.name=="Durgen's Crescent Axe" and item.stats.str==4 and item.dps==12.3)
        assert(item.weaponSpeed==2.4 and item.loc=='INVTYPE_WEAPONMAINHAND')
        assert(CD.Search.Matches(item,CD.Search.Parse('axe, str >= 4, dps >= 12, req <= 13')))
        assert(not CD.Search.Matches(item,CD.Search.Parse('str >= 5')))
        assert(CD.Catalog.dungeons['hall-of-thanes'] and CD.Catalog.dungeons['city-of-dalaran'])
        assert(CD.Items.Read(271095).stats.sp==18)
        for _,d in pairs(CD.Catalog.dungeons)do
            for _,group in ipairs(d.bosses)do
                assert(group.kind~='quest' and group.kind~='trash')
                for _,drop in ipairs(group.loot)do assert(CD.Catalog.items[drop.id])end
            end
        end
        ''')

    def test_modern_quest_log_and_chains(self):
        vm=load_dungeon()
        vm.execute('''
        local Q=CD.Quests
        assert(Q.InLog(96393) and not Q.InLog(214))
        local q=Q.Get(96393)
        assert(q.previousAny[1]==96391 and Q.Get(96391))
        assert(#Q.Prerequisites(q)>0)
        assert(Q.State(q)=='In quest log')
        assert(Q.GiverLines(q)[2]:find('Dun Morogh',1,true))
        assert(Q.GiverLines(q)[2]:find('64.9, 58.5',1,true))
        assert(Q.ForCharacter(q,{faction='Horde',raceID=2,classID=1})==false)
        assert(Q.ForCharacter({races=4294967296,classes=0},{faction='Alliance',raceID=33,classID=1}))
        ''')

    def test_forever_all_dungeons_classes_and_factions_render(self):
        vm=load_dungeon()
        vm.execute('''
        CD.UI.Create()
        for _,faction in ipairs({'Alliance','Horde'})do
            MOCK.faction=faction;MOCK.race=faction=='Alliance' and 3 or 2
            for _,class in ipairs({'WARRIOR','PALADIN','HUNTER','ROGUE','PRIEST','SHAMAN','MAGE','WARLOCK','DRUID'})do
                MOCK.class=class
                for _,slug in ipairs(CD.Catalog.order)do
                    CD.db.lastDungeon=slug;CD.UI.Render(true)
                    for _,q in ipairs(CD.Quests.List(CD.Catalog.dungeons[slug]))do
                        CD.Quests.State(q);CD.Quests.GiverLines(q);CD.Quests.Prerequisites(q)
                    end
                end
            end
        end
        ''')

    def test_forever_item_tooltip_search_and_nil_return_positions(self):
        vm=load_dungeon()
        vm.execute('''
        local a,b,c,d=CD.Call(function()return nil,nil,nil,7 end)
        assert(a==nil and b==nil and c==nil and d==7)
        MOCK.items[271095]={name='Fang of Magmatus',loc='INVTYPE_WEAPONMAINHAND',level=13,
            classID=2,subclassID=15,stats={ITEM_MOD_INTELLECT_SHORT=4},usable=true}
        local item=CD.Items.Read(271095)
        assert(item.live and item.stats.sp==18 and item.stats.int==4)
        CD.UI.Create();CD.db.lastDungeon='hall-of-thanes';CD.UI.Render(true)
        CD.db.lastDungeon='blackmaw-hold';CD.UI.Render(true)
        assert(CD.UI.searchEmpty:GetText()=='No drop table recorded for this dungeon.')
        ''')

    def test_forever_nameplates_and_restricted_fallback(self):
        with patch.dict(os.environ,{'ELMO_TEST_ADDON':str(STAGE/'ElmoPlater'),'ELMO_TEST_FOREVER':'1'}):
            state=runpy.run_path(str(HERE/'ElmoPlater/test_prototype.py'))
        vm=state['vm']
        vm.execute('''
        MOCK.event('PLAYER_ENTERING_WORLD')
        local mob,plate=MOCK.mob('nameplate9','Creature-forever','Forever enemy')
        local record=A.units.nameplate9
        assert(record and record.frame:IsShown() and plate.UnitFrame.alpha==0)
        SECRET=setmetatable({}, {__index=function()error('Secret value indexed')end})
        function issecretvalue(v)return rawequal(v,SECRET)end
        local health,guid=UnitHealth,UnitGUID
        UnitHealth=function(unit)if unit=='nameplate9' then return SECRET end;return health(unit)end
        A.Update(false)
        assert(not record.frame:IsShown() and plate.UnitFrame.alpha==1)
        UnitHealth=health;A.Update(false)
        assert(record.frame:IsShown() and plate.UnitFrame.alpha==0)
        UnitGUID=function(unit)if unit=='nameplate9' then return SECRET end;return guid(unit)end
        A.Update(false);assert(not record.frame:IsShown() and plate.UnitFrame.alpha==1)
        UnitGUID=guid
        local aura=C_UnitAuras.GetAuraDataByIndex
        C_UnitAuras.GetAuraDataByIndex=function()return SECRET end
        A.Update(true);assert(not record.missing and not record.aurasKnown)
        C_UnitAuras.GetAuraDataByIndex=aura
        MOCK.logRestricted=true;A.RegisterCombatLog()
        assert(not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
        MOCK.logRestricted=false;A.RegisterCombatLog()
        assert(A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
        MOCK.logRestricted=true;A.CombatLog(1,SECRET,false,SECRET,nil,nil,nil,SECRET)
        A.Remove('nameplate9');assert(plate.UnitFrame.alpha==1)
        assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
        ''')

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
