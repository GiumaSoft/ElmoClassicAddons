"""Real Lua 5.1 addon tests with explicit Era spell APIs and native-frame fixtures."""
from pathlib import Path
import unittest
import os
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).parent
ADDON = Path(os.environ.get('ELMO_TEST_ADDON', Path(__file__).resolve().parents[3] / "ElmoSpellTracker"))

class CooldownTests(unittest.TestCase):
    def setUp(self):
        self.vm=LuaRuntime(unpack_returned_tuples=True)
        self.vm.execute((HERE/'wow_mock.lua').read_text())
        ns=self.vm.table()
        load=self.vm.eval('function(s,n,ns) assert(loadstring(s,"@"..n))("ElmoSpellTracker",ns) end')
        for name in (ADDON/'ElmoSpellTracker.toc').read_text().splitlines():
            if name.endswith('.lua'): load((ADDON/name).read_text(),name,ns)
        self.vm.globals().A=ns

    def check(self,code): self.vm.execute(code)

    def test_default_and_registration(self):
        self.check("""MOCK.start();assert(A.db.maxSkills==10 and #A.db.spells==0)
        assert(A.frame.events.UNIT_SPELLCAST_SUCCEEDED=='player')
        assert(SlashCmdList.ELMOSPELLTRACKER==A.Command)
        assert(SLASH_ELMOSPELLTRACKER2=='/est' and SlashCmdList.CLASSICSPELLSTRACKER==nil)""")

    def test_first_cast_grey_icon_with_centered_timer(self):
        self.check("""MOCK.spell(100,'Arcane Shot');MOCK.start();MOCK.cooldown(100,6);MOCK.cast(100);MOCK.advance(.1)
        assert(#A.db.spells==1 and A.db.spells[1]==100)
        local b=A.UI.icons[1];assert(b.texture.desaturated and b.timer:GetText()=='6')
        assert(b.timer.allPoints==b and b.timer.justifyH=='CENTER' and b.timer.justifyV=='MIDDLE')""")

    def test_expiry_restores_original_colour_and_keeps_icon(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,2);MOCK.cast(100);MOCK.advance(.2)
        MOCK.advance(2.1);local b=A.UI.icons[1];assert(b:IsShown() and not b.texture.desaturated)
        assert(b.texture.vertex[1]==1 and not b.timer:IsShown() and b.timer:GetText()=='')
        assert(#A.db.spells==1 and A.frame:GetScript('OnUpdate')==nil)""")

    def test_new_abilities_append_to_right_without_moving_first_icon(self):
        self.check("""MOCK.spell(100);MOCK.spell(101);MOCK.start()
        MOCK.cooldown(100,8);MOCK.cast(100);MOCK.advance(.1);local x=A.UI.icons[1]:GetLeft()
        MOCK.cooldown(101,8);MOCK.cast(101);MOCK.advance(.1)
        assert(A.db.spells[1]==100 and A.db.spells[2]==101)
        assert(A.UI.icons[1]:GetLeft()==x and A.UI.icons[2]:GetLeft()>x)""")

    def test_repeated_cast_does_not_reorder_or_duplicate(self):
        self.check("""for i=100,102 do MOCK.spell(i) end;MOCK.start()
        for _,i in ipairs({100,101,100,102}) do MOCK.cooldown(i,6);MOCK.cast(i);MOCK.advance(.15) end
        assert(#A.db.spells==3 and A.db.spells[1]==100 and A.db.spells[2]==101 and A.db.spells[3]==102)""")

    def test_ranks_share_one_slot(self):
        self.check("""MOCK.spell(100,'Arcane Shot');MOCK.spell(101,'Arcane Shot');MOCK.spell(102,'Multi-Shot')
        MOCK.start();for _,i in ipairs({100,102,101}) do MOCK.cooldown(i,10);MOCK.cast(i);MOCK.advance(.1) end
        assert(#A.db.spells==2 and A.db.spells[1]==101 and A.db.spells[2]==102)
        assert(A.UI.icons[1].spellID==101)""")

    def test_pending_spell_data_preserves_first_use_order(self):
        self.check("""MOCK.spell(100).cold=true;MOCK.spell(101);MOCK.start()
        MOCK.cast(100);MOCK.advance(.1);MOCK.cooldown(101,10);MOCK.cast(101);MOCK.advance(.1)
        MOCK.spells[100].cold=false;MOCK.cooldown(100,10);MOCK.event('SPELL_DATA_LOAD_RESULT',100,true);MOCK.advance(.1)
        assert(A.db.spells[1]==100 and A.db.spells[2]==101);assert(MOCK.requests[100]==1)""")

    def test_late_first_cast_wins_a_full_single_slot(self):
        self.check("""MOCK.spell(100).cold=true;MOCK.spell(101);MOCK.start();A.SetMaxSkills(1)
        MOCK.cast(100);MOCK.advance(.1);MOCK.cooldown(101,6);MOCK.cast(101);MOCK.advance(.1)
        MOCK.spells[100].cold=false;MOCK.cooldown(100,6);MOCK.advance(.1)
        assert(#A.db.spells==1 and A.db.spells[1]==100)""")

    def test_gcd_only_spell_is_not_learned(self):
        self.check("""MOCK.spell(100,'Serpent Sting',0);MOCK.start();MOCK.globalCooldown(100)
        MOCK.cast(100);MOCK.advance(5.2);assert(#A.db.spells==0 and not next(A.pending))
        assert(A.frame:GetScript('OnUpdate')==nil)""")

    def test_gcd_does_not_grey_a_ready_tracked_spell(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,1);MOCK.cast(100);MOCK.advance(1.2)
        MOCK.globalCooldown(100);MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(not A.UI.icons[1].texture.desaturated and not A.UI.icons[1].timer:IsShown())""")

    def test_deferred_cooldown_without_base_metadata(self):
        self.check("""MOCK.spell(100,'Cooldown spell',0);GetSpellBaseCooldown=nil;MOCK.start()
        MOCK.globalCooldown(100);MOCK.cast(100);MOCK.advance(.1);assert(#A.db.spells==0)
        MOCK.cooldown(100,6);MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(#A.db.spells==1 and A.UI.icons[1].texture.desaturated)""")

    def test_known_base_cooldown_adds_before_the_server_update(self):
        self.check("""MOCK.spell(100,'Raptor Strike',6000);MOCK.start();MOCK.globalCooldown(100)
        MOCK.cast(100);MOCK.advance(.1);assert(#A.db.spells==1 and not A.UI.icons[1].texture.desaturated)
        MOCK.advance(3);MOCK.cooldown(100,6);MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(A.UI.icons[1].texture.desaturated)""")

    def test_native_duration_is_authoritative_and_ignores_stale_gcd_flag(self):
        self.check("""local s=MOCK.spell(100);MOCK.start();MOCK.cooldown(100,30)
        s.modRate=2;s.nativeEnd=MOCK.time+7;s.unreliableGCDFlag=true
        MOCK.cast(100);MOCK.advance(.1);assert(A.UI.icons[1].timer:GetText()=='7')""")

    def test_cooldown_reset_immediately_restores_colour(self):
        self.check("""local s=MOCK.spell(100);MOCK.start();MOCK.cooldown(100,180);MOCK.cast(100);MOCK.advance(.1)
        s.start=0;s.duration=0;MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(not A.UI.icons[1].texture.desaturated and A.UI.icons[1].remaining==0)""")

    def test_cooldowns_on_hold_are_learned_without_fake_countdown(self):
        self.check("""local s=MOCK.spell(100,'Stealth',0);s.paused=true;MOCK.start();MOCK.cast(100);MOCK.advance(.1)
        assert(#A.db.spells==1 and A.UI.icons[1].remaining==0)
        s.paused=false;MOCK.cooldown(100,10);MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(A.UI.icons[1].texture.desaturated and A.UI.icons[1].timer:GetText()=='10')""")

    def test_pet_other_players_and_failed_casts_do_not_add_skills(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,30)
        MOCK.cast(100,'pet');MOCK.cast(100,'party1');MOCK.event('UNIT_SPELLCAST_FAILED','player','Cast-1',100)
        MOCK.advance(.1);assert(#A.db.spells==0)""")

    def test_autoattacks_passives_and_item_spells_are_excluded(self):
        self.check("""MOCK.spell(100,'Auto Shot').autoRepeat=true
        MOCK.spell(101,'Attack').autoAttack=true;MOCK.spell(102,'Passive').passive=true
        MOCK.spell(103,'Healing Potion').known=false
        MOCK.start();for i=100,103 do MOCK.cooldown(i,60);MOCK.cast(i) end
        MOCK.advance(.1);assert(#A.db.spells==0)""")

    def test_spellbook_override_can_be_tracked(self):
        self.check("""local s=MOCK.spell(100);s.known=false;s.inBook=true;MOCK.start()
        MOCK.cooldown(100,10);MOCK.cast(100);MOCK.advance(.1);assert(#A.db.spells==1)""")

    def test_bar_capacity_default_ten_and_hard_cap_twelve(self):
        self.check("""for i=100,112 do MOCK.spell(i) end;MOCK.start()
        for i=100,110 do MOCK.cooldown(i,10);MOCK.cast(i);MOCK.advance(.1) end
        assert(#A.db.spells==10 and not A.UI.icons[11]:IsShown())
        local notices=#MOCK.messages;MOCK.cast(110);MOCK.advance(.1);assert(#MOCK.messages==notices)
        assert(A.SetMaxSkills(12));for i=110,112 do MOCK.cooldown(i,10);MOCK.cast(i);MOCK.advance(.1) end
        assert(#A.db.spells==12 and A.UI.icons[12]:IsShown())""")

    def test_limit_validation_and_slash_parameter(self):
        self.check("""MOCK.start();for _,value in ipairs({'0','13','1.5','foo','-2',''}) do assert(not A.SetMaxSkills(value)) end
        assert(A.db.maxSkills==10);A.Command('max 1');assert(A.db.maxSkills==1)
        A.Command('max 12');assert(A.db.maxSkills==12);A.Command('max 0');assert(A.db.maxSkills==12)""")

    def test_shrinking_keeps_saved_icons_and_growing_restores_them(self):
        self.check("""for i=100,102 do MOCK.spell(i) end;MOCK.start()
        for i=100,102 do MOCK.cooldown(i,10);MOCK.cast(i);MOCK.advance(.1) end
        A.SetMaxSkills(1);MOCK.advance(.1);assert(#A.db.spells==3 and not A.UI.icons[2]:IsShown())
        A.SetMaxSkills(3);MOCK.advance(.1);assert(A.UI.icons[3].spellID==102 and A.UI.icons[3]:IsShown())""")

    def test_saved_list_is_read_from_native_state_on_reload(self):
        self.check("""MOCK.spell(100);MOCK.spell(101)
        ElmoSpellTrackerDB={maxSkills=2,spells={100,101},position={x=123,y=-200},locked=true}
        MOCK.cooldown(100,30);MOCK.start();MOCK.advance(.1)
        assert(#A.db.spells==2 and A.UI.icons[1].texture.desaturated and not A.UI.icons[2].texture.desaturated)
        assert(A.UI.bar.point[1]=='TOPLEFT' and A.UI.bar.point[4]==123 and A.UI.bar.point[5]==-200)
        assert(not A.UI.handle:IsShown())""")

    def test_invalid_saved_variables_are_sanitized(self):
        self.check("""MOCK.spell(100,'Same');MOCK.spell(101,'Same')
        ElmoSpellTrackerDB={maxSkills=100,spells={100,100,'oops',-1,101},locked='true'}
        MOCK.start();assert(A.db.maxSkills==10 and #A.db.spells==1 and not A.db.locked)""")

    def test_remove_frees_a_slot_and_relearning_adds_to_right(self):
        self.check("""MOCK.spell(100);MOCK.spell(101);MOCK.start();A.SetMaxSkills(1)
        MOCK.cooldown(100,10);MOCK.cast(100);MOCK.advance(.1);assert(A.Remove(1))
        MOCK.cooldown(101,10);MOCK.cast(101);MOCK.advance(.1);assert(A.db.spells[1]==101)
        A.SetMaxSkills(2);MOCK.cast(100);MOCK.advance(.1);assert(A.db.spells[2]==100)""")

    def test_shift_right_click_removes_only_when_unlocked(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,6);MOCK.cast(100);MOCK.advance(.1)
        MOCK.shift=true;A.SetLocked(true);A.UI.icons[1]:GetScript('OnClick')();assert(#A.db.spells==1)
        A.SetLocked(false);A.UI.icons[1]:GetScript('OnClick')();assert(#A.db.spells==0)""")

    def test_clear_does_not_relearn_spells_until_used(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,10);MOCK.cast(100);MOCK.advance(.1)
        A.Clear();MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.2);assert(#A.db.spells==0)
        MOCK.cast(100);MOCK.advance(.1);assert(#A.db.spells==1)""")

    def test_drag_saves_top_left_anchor(self):
        self.check("""MOCK.start();local b=A.UI.bar
        A.UI.handle:GetScript('OnDragStart')();assert(b.moving)
        b.mockLeft=120;b.mockTop=700;A.UI.handle:GetScript('OnDragStop')()
        assert(not b.moving and A.db.position.x==120 and A.db.position.y==-200 and b.point[1]=='TOPLEFT')""")

    def test_settings_accept_limit_and_report_invalid_input(self):
        self.check("""MOCK.start();A.Command('');local f=A.UI.settings;assert(f:IsShown())
        f.limit:SetText('12');f.limit:GetScript('OnEnterPressed')();assert(A.db.maxSkills==12)
        f.limit:SetText('13');f.limit:GetScript('OnEnterPressed')();assert(A.db.maxSkills==12)
        assert(f.status:GetText():find('1 to 12',1,true))""")

    def test_tooltip_uses_native_spell_id(self):
        self.check("""MOCK.spell(100);MOCK.start();MOCK.cooldown(100,6);MOCK.cast(100);MOCK.advance(.1)
        A.UI.icons[1]:GetScript('OnEnter')(A.UI.icons[1]);assert(GameTooltip.spellID==100 and GameTooltip:IsShown())
        A.UI.icons[1]:GetScript('OnLeave')();assert(not GameTooltip:IsShown())""")

    def test_native_charge_recharge_and_available_charge(self):
        self.check("""local s=MOCK.spell(100);s.charges={currentCharges=0,maxCharges=2,cooldownStartTime=100,cooldownDuration=20}
        s.chargeNativeEnd=107;MOCK.start();MOCK.cast(100);MOCK.advance(.1)
        assert(A.UI.icons[1].timer:GetText()=='7' and A.UI.icons[1].texture.desaturated)
        s.charges.currentCharges=1;MOCK.event('SPELL_UPDATE_CHARGES');MOCK.advance(.1)
        assert(not A.UI.icons[1].texture.desaturated and not A.UI.icons[1].timer:IsShown())""")

    def test_legacy_spell_apis_fallback(self):
        self.check("""local s=MOCK.spell(100);C_Spell=nil;C_SpellBook=nil
        function GetSpellInfo(id) local s=MOCK.spells[id];if s then return s.name,'Rank 1',s.icon end end
        function IsSpellKnown(id) return MOCK.spells[id]~=nil end
        function GetSpellCooldown(id) local s=id==61304 and MOCK.gcd or MOCK.spells[id];if s then return s.start or 0,s.duration or 0,1 end end
        MOCK.start();MOCK.cooldown(100,6);MOCK.cast(100);MOCK.advance(.1)
        assert(#A.db.spells==1 and A.UI.icons[1].timer:GetText()=='6')
        MOCK.advance(7);MOCK.globalCooldown(100);MOCK.event('SPELL_UPDATE_COOLDOWN');MOCK.advance(.1)
        assert(not A.UI.icons[1].texture.desaturated)""")

    def test_unreadable_cooldown_is_not_reported_as_ready(self):
        self.check("""local s=MOCK.spell(100);s.noDuration=true;s.noCooldownInfo=true
        ElmoSpellTrackerDB={spells={100}};MOCK.start();MOCK.advance(.1)
        assert(A.UI.icons[1].timer:GetText()=='?' and A.UI.icons[1].texture.desaturated)""")

    def test_countdown_format_boundaries(self):
        self.check("""assert(A.UI.FormatTime(.2)=='1');assert(A.UI.FormatTime(59.1)=='1:00')
        assert(A.UI.FormatTime(65)=='1:05');assert(A.UI.FormatTime(600)=='10:00');assert(A.UI.FormatTime(3600)=='1h')""")

    def test_resource_gain_and_loss_refresh_an_idle_bar(self):
        for power in ('MANA','ENERGY','RAGE'):
            with self.subTest(power=power):
                self.setUp()
                self.check("""local s=MOCK.spell(100);ElmoSpellTrackerDB={spells={100}}
                s.insufficientPower=true;MOCK.start();MOCK.advance(.2)
                local b=A.UI.icons[1]
                assert(b.texture.desaturated and b.texture.vertex[1]==.65)
                assert(not b.timer:IsShown() and A.frame:GetScript('OnUpdate')==nil)
                s.insufficientPower=false;MOCK.event('UNIT_POWER_UPDATE','player','"""+power+"""');MOCK.advance(.2)
                assert(not b.texture.desaturated and b.texture.vertex[1]==1)
                s.insufficientPower=true;MOCK.event('SPELL_UPDATE_USABLE');MOCK.advance(.2)
                assert(b.texture.desaturated and not b.timer:IsShown())""")

    def test_cooldown_expiry_stays_grey_when_resource_is_missing(self):
        self.check("""local s=MOCK.spell(100);MOCK.start();MOCK.cooldown(100,1)
        MOCK.cast(100);MOCK.advance(.2);s.insufficientPower=true;MOCK.advance(1.2)
        local b=A.UI.icons[1];assert(b.texture.desaturated and not b.timer:IsShown())
        s.insufficientPower=false;MOCK.event('UNIT_POWER_UPDATE','player','RAGE');MOCK.advance(.2)
        assert(not b.texture.desaturated)""")

    def test_resource_gain_does_not_override_an_active_cooldown(self):
        self.check("""local s=MOCK.spell(100);s.insufficientPower=true
        MOCK.start();MOCK.cooldown(100,30);MOCK.cast(100);MOCK.advance(.2)
        s.insufficientPower=false;MOCK.event('UNIT_POWER_UPDATE','player','MANA');MOCK.advance(.2)
        assert(A.UI.icons[1].texture.desaturated and A.UI.icons[1].timer:IsShown())""")

    def test_non_resource_unusable_does_not_grey_a_ready_spell(self):
        self.check("""local s=MOCK.spell(100);s.usable=false
        ElmoSpellTrackerDB={spells={100}};MOCK.start();MOCK.advance(.2)
        assert(not A.UI.icons[1].texture.desaturated)""")

    def test_legacy_resource_api(self):
        self.check("""local s=MOCK.spell(100);C_Spell.IsSpellUsable=nil
        function IsUsableSpell(id) return false,MOCK.spells[id].insufficientPower==true end
        s.insufficientPower=true;ElmoSpellTrackerDB={spells={100}};MOCK.start();MOCK.advance(.2)
        assert(A.UI.icons[1].texture.desaturated)
        s.insufficientPower=false;MOCK.event('UNIT_DISPLAYPOWER','player');MOCK.advance(.2)
        assert(not A.UI.icons[1].texture.desaturated)""")

    def test_current_profile_is_preserved_and_old_settings_are_not_imported(self):
        self.check("""MOCK.spell(100)
        ClassicCooldownTrackerDB={spells={100},maxSkills=2}
        ElmoSpellTrackerDB={spells={100},maxSkills=4,position={x=75,y=-90},locked=true}
        local current=ElmoSpellTrackerDB;local old=ClassicCooldownTrackerDB
        MOCK.start();MOCK.advance(.2)
        assert(A.db==current and A.db.maxSkills==4 and A.db.spells[1]==100 and A.db.locked)
        assert(A.UI.bar.name=='ElmoSpellTrackerBar' and A.UI.bar.point[4]==75)
        assert(ClassicCooldownTrackerDB==old and ClassicCooldownTracker==nil)
        assert(SLASH_CLASSICSPELLSTRACKER1==nil and SLASH_ELMOSPELLTRACKER2=='/est')""")

    def test_only_player_power_events_wake_an_idle_bar(self):
        self.check("""MOCK.start();MOCK.advance(.2)
        assert(A.frame.events.UNIT_POWER_UPDATE=='player')
        MOCK.event('UNIT_POWER_UPDATE','party1','MANA');assert(A.frame:GetScript('OnUpdate')==nil)
        MOCK.event('UNIT_MAXPOWER','player','MANA');assert(A.frame:GetScript('OnUpdate')~=nil)""")

if __name__=='__main__':unittest.main(verbosity=2)
