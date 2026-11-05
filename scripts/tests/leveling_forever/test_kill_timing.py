"""Restricted-client kill timing from public unit observations; no live input."""
import unittest
from test_addon import ADDON, HERE
from lupa.lua51 import LuaRuntime


class ObservedKillTimingTests(unittest.TestCase):
    def setUp(self):
        self.vm = LuaRuntime(unpack_returned_tuples=True)
        self.vm.execute((HERE / 'wow_mock.lua').read_text())
        self.vm.execute('''
        MOCK.forever()
        function GetBuildInfo()return '1.60.1','70790','',16001 end
        function UnitAffectingCombat(unit)
            if unit=='player' then return MOCK.playerCombat==true end
            return MOCK.units[unit] and MOCK.units[unit].combat or false
        end
        function UnitThreatSituation(member,unit)
            local mob=MOCK.units[unit]
            return mob and mob.threat and mob.threat[member]
        end
        function MOCK.engage(unit,member,status)
            local mob=assert(MOCK.units[unit]);mob.combat=true;MOCK.playerCombat=true
            mob.threat=mob.threat or {};mob.threat[member or 'player']=status or 0
            MOCK.event('UNIT_THREAT_LIST_UPDATE',unit)
        end
        function MOCK.publicDeath(unit)
            local mob=assert(MOCK.units[unit]);mob.dead=true;mob.combat=false;mob.threat={}
            MOCK.event('UNIT_FLAGS',unit)
        end
        ''')
        ns = self.vm.table();ns.flavor = 'forever'
        load = self.vm.eval('function(s,n,ns)assert(loadstring(s,"@"..n))("ElmoLeveling",ns)end')
        for name in (ADDON / 'ElmoLeveling.toc').read_text().splitlines():
            if name.endswith('.lua'):load((ADDON / name).read_text(), name, ns)
        self.vm.globals().A = ns
        self.vm.execute('MOCK.start()')

    def check(self, code):
        self.vm.execute(code)

    def test_public_death_stops_timer_before_delayed_xp_and_populates_ui(self):
        self.check('''
        MOCK.mob('target','Boar',8);MOCK.engage('target')
        MOCK.advance(12.5);MOCK.publicDeath('target');MOCK.advance(1)
        MOCK.chat('Boar',75);MOCK.advance(2)
        local kill=A.db.kills[1]
        assert(kill.killTime==12.5 and kill.killTimeEstimated)
        assert(A.UI.mobRows[1].killTime:GetText()=='~12.5s')
        assert(A.UI.mobRows[1].xpPerSecond:GetText()=='~6.0')
        assert(#A.db.kills==1 and A.Mobs.Rate()==1 and not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
        ''')

    def test_looking_at_a_mob_does_not_start_timing_and_switching_targets_keeps_it(self):
        self.check('''
        local mob=MOCK.mob('target','Boar',8);MOCK.event('PLAYER_TARGET_CHANGED');MOCK.advance(20)
        MOCK.engage('target');MOCK.advance(4)
        MOCK.units.nameplate1=mob;MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate1')
        MOCK.units.target=nil;MOCK.event('PLAYER_TARGET_CHANGED');MOCK.advance(6)
        MOCK.publicDeath('nameplate1');MOCK.chat('Boar',50,nil,mob.guid);MOCK.advance(2)
        assert(A.db.kills[1].killTime==10)
        ''')

    def test_same_name_mobs_keep_independent_guid_timers(self):
        self.check('''
        local a=MOCK.mob('nameplate1','Boar',8);MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate1')
        MOCK.engage('nameplate1');MOCK.advance(2)
        local b=MOCK.mob('nameplate2','Boar',9);MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate2')
        MOCK.engage('nameplate2','pet');MOCK.advance(3)
        MOCK.publicDeath('nameplate1');MOCK.chat('Boar',50,nil,a.guid);MOCK.advance(4)
        MOCK.publicDeath('nameplate2');MOCK.chat('Boar',60,nil,b.guid);MOCK.advance(2)
        assert(#A.db.kills==2 and A.db.kills[1].killTime==7 and A.db.kills[2].killTime==5)
        ''')

    def test_group_threat_is_accepted_but_unrelated_combat_is_not(self):
        self.check('''
        local mob=MOCK.mob('target','Wolf',9);mob.combat=true
        MOCK.event('UNIT_FLAGS','target');MOCK.advance(20)
        MOCK.engage('target','party1');MOCK.advance(5);MOCK.publicDeath('target')
        MOCK.chat('Wolf',50,nil,mob.guid);MOCK.advance(2)
        assert(A.db.kills[1].killTime==5)
        ''')

    def test_xp_with_guid_can_close_a_timer_after_unit_disappears(self):
        self.check('''
        local mob=MOCK.mob('target','Wolf',9);MOCK.engage('target');MOCK.advance(5)
        MOCK.units.target=nil;MOCK.event('PLAYER_TARGET_CHANGED')
        MOCK.chat('Wolf',50,nil,mob.guid);MOCK.advance(2)
        assert(A.db.kills[1].killTime==5 and A.db.kills[1].killTimeEstimated)
        ''')

    def test_ambiguous_name_only_xp_does_not_choose_one_of_two_corpses(self):
        self.check('''
        MOCK.mob('target','Boar',8);MOCK.engage('target')
        MOCK.mob('mouseover','Boar',8);MOCK.engage('mouseover');MOCK.advance(5)
        MOCK.publicDeath('target');MOCK.publicDeath('mouseover')
        MOCK.chat('Boar',50);MOCK.advance(2)
        assert(#A.db.kills==1 and A.db.kills[1].killTime==nil)
        ''')

    def test_evade_and_repull_reset_only_that_mobs_observed_timer(self):
        self.check('''
        MOCK.mob('target','Boar',8);MOCK.engage('target');MOCK.advance(10)
        MOCK.units.target.combat=false;MOCK.event('UNIT_FLAGS','target');MOCK.advance(20)
        MOCK.engage('target');MOCK.advance(4);MOCK.publicDeath('target')
        MOCK.chat('Boar',50);MOCK.advance(2)
        assert(A.db.kills[1].killTime==4)
        ''')

    def test_private_threat_does_not_start_a_timer(self):
        self.check('''
        local secret=setmetatable({}, {__index=function()error('Private data read')end,
            __lt=function()error('Private comparison')end})
        issecretvalue=function(v)return rawequal(v,secret)end
        local mob=MOCK.mob('target','Boar',8);mob.combat=true;mob.threat={player=secret}
        MOCK.event('UNIT_FLAGS','target');MOCK.advance(5);MOCK.publicDeath('target')
        MOCK.chat('Boar',50,nil,mob.guid);MOCK.advance(2)
        assert(A.db.kills[1].killTime==nil)
        ''')

    def test_zone_and_reset_discard_observed_pull_times(self):
        self.check('''
        MOCK.mob('target','Boar',8);MOCK.engage('target');MOCK.advance(5)
        MOCK.units.target.combat=false;MOCK.event('ZONE_CHANGED_NEW_AREA');MOCK.advance(2)
        MOCK.publicDeath('target');MOCK.chat('Boar',50);MOCK.advance(2)
        assert(A.db.kills[1].killTime==nil)
        MOCK.mob('target','Wolf',8);MOCK.engage('target');MOCK.advance(5)
        MOCK.units.target.combat=false;A.Reset();MOCK.publicDeath('target')
        MOCK.chat('Wolf',50);MOCK.advance(2);assert(A.db.kills[1].killTime==nil)
        ''')

    def test_public_mob_target_can_start_timing_when_threat_is_private(self):
        self.check('''
        local secret={};issecretvalue=function(v)return rawequal(v,secret)end
        local mob=MOCK.mob('target','Boar',8);mob.combat=true;mob.threat={player=secret}
        function UnitIsUnit(unit,member)return unit=='targettarget' and member=='player' end
        MOCK.event('UNIT_TARGET','target');MOCK.advance(5);MOCK.publicDeath('target')
        MOCK.chat('Boar',50,nil,mob.guid);MOCK.advance(2)
        assert(A.db.kills[1].killTime==5 and A.db.kills[1].killTimeEstimated)
        ''')

    def test_saved_estimates_keep_their_marker_after_reload(self):
        self.check('''
        A.db.seconds=20;A.db.kills={{name='Boar',playerLevel=7,xp=75,at=15,killTime=12.5,killTimeEstimated=true}}
        A.Mobs.Init();A.UI.ToggleMobs()
        assert(A.db.kills[1].killTimeEstimated and A.UI.mobRows[1].killTime:GetText()=='~12.5s')
        ''')

    def test_forever_does_not_use_combat_log_even_when_restriction_flag_is_false(self):
        self.check('''
        local calls=0
        C_CombatLog={IsCombatLogRestricted=function()return false end,
            GetCurrentEventInfo=function()calls=calls+1;error('Forbidden combat log')end}
        CombatLogGetCurrentEventInfo=C_CombatLog.GetCurrentEventInfo
        assert(not A.Compat.CombatAvailable())
        assert(not A.Compat.Register(A.frame,'COMBAT_LOG_EVENT_UNFILTERED'))
        MOCK.event('COMBAT_LOG_EVENT_UNFILTERED');assert(calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
