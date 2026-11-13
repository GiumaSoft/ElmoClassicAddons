"""Execute the installed addon in Lua 5.1 with explicit Classic Era fixtures."""
from pathlib import Path
import os
import unittest

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).parent
ADDON = Path(os.environ.get("ELMO_TEST_ADDON", str(Path(__file__).resolve().parents[3] / "ElmoLeveling")))


class LevelingTests(unittest.TestCase):
    def setUp(self):
        self.vm = LuaRuntime(unpack_returned_tuples=True)
        self.vm.execute((HERE / "wow_mock.lua").read_text())
        if self._testMethodName.startswith("test_forever_"):
            self.vm.execute("MOCK.forever()")
        namespace = self.vm.table()
        namespace.flavor = "forever"
        load = self.vm.eval('function(s, n, ns) assert(loadstring(s, "@" .. n))("ElmoLeveling", ns) end')
        for name in (ADDON / "ElmoLeveling.toc").read_text().splitlines():
            if name.endswith(".lua"):
                load((ADDON / name).read_text(), name, namespace)
        self.vm.globals().A = namespace


    def check(self, code):
        self.vm.execute(code)


    def test_lock_prevents_drag_and_unlock_button_restores_it(self):
        self.check("""MOCK.start(); A.Command('lock')
        A.UI.anchor:GetScript('OnDragStart')(); assert(not A.UI.panel.moving)
        assert(A.UI.lock.label:GetText() == 'Unlock')
        A.UI.lock:GetScript('OnClick')(); A.UI.anchor:GetScript('OnDragStart')()
        assert(A.UI.panel.moving and A.UI.lock.label:GetText() == 'Lock')""")


    def test_drag_saves_top_left_position_and_center_recovers(self):
        self.check("""MOCK.start(); A.UI.panel.mockLeft, A.UI.panel.mockTop = 123, 456
        A.UI.anchor:GetScript('OnDragStop')()
        assert(A.db.position.x == 123 and A.db.position.y == -444)
        assert(A.UI.panel.point[1] == 'TOPLEFT' and A.UI.panel.point[4] == 123)
        A.Command('hide'); A.Command('center')
        assert(A.db.position == nil and A.UI.panel.point[1] == 'CENTER' and A.UI.panel:IsShown())""")


    def test_saved_preferences_are_restored(self):
        self.check("""ElmoLevelingDB = {locked = true, hidden = true, position = {x = 54, y = -270}}
        MOCK.start(); assert(A.db.locked and not A.UI.panel:IsShown())
        assert(A.UI.panel.point[4] == 54 and A.UI.panel.point[5] == -270)""")


    def test_invalid_xp_snapshot_does_not_destroy_baseline(self):
        self.check("""MOCK.start(); MOCK.xp = nil; MOCK.event('PLAYER_XP_UPDATE', 'player')
        MOCK.xp = 100; MOCK.gain(25); assert(A.db.xp == 25)""")


    def test_bag_value_multiplies_unit_sell_price_by_stack_quantity(self):
        self.check("""MOCK.item(10, 123); MOCK.item(20, 10000); MOCK.item(30, 1)
        MOCK.put(0, 1, 10, 2); MOCK.put(1, 1, 20, 1); MOCK.put(4, 1, 30, 200)
        MOCK.start(); local b = A.Bags.state
        assert(b.value == 10446 and b.stacks == 3 and b.items == 203 and b.pending == 0)
        assert(MOCK.plain(A.UI.bagValue:GetText()) == '1g 4s 46c')
        assert(A.db.bagBaseline == 10446 and A.Bags.Change() == 0)""")


    def test_only_carried_bags_are_included(self):
        self.check("""MOCK.item(10, 100); MOCK.put(0, 1, 10, 1)
        MOCK.put(-1, 1, 10, 20); MOCK.put(5, 1, 10, 20); MOCK.put(-2, 1, 10, 20)
        MOCK.start(); assert(A.Bags.state.value == 100 and MOCK.scanCalls == 5)""")


    def test_existing_bags_form_baseline_and_new_items_raise_bag_change(self):
        self.check("""MOCK.item(10, 10); local stack = MOCK.put(0, 1, 10, 2)
        MOCK.start(); assert(A.Bags.Change() == 0)
        stack.stackCount = 5; MOCK.bagChange()
        assert(A.Bags.state.value == 50 and A.Bags.Change() == 30)
        assert(MOCK.plain(A.UI.bagValue:GetText()) == '0g 0s 50c' and A.UI.bagChange == nil)""")


    def test_consuming_or_selling_items_lowers_current_bag_value(self):
        self.check("""MOCK.item(10, 10); MOCK.put(0, 1, 10, 2); MOCK.start()
        MOCK.bags[0][1] = nil; MOCK.bagChange()
        assert(A.Bags.state.value == 0 and A.Bags.Change() == -20)
        assert(MOCK.plain(A.UI.bagValue:GetText()) == '0g 0s 0c' and A.UI.bagChange == nil)""")


    def test_sorting_and_splitting_stacks_preserve_total_and_change(self):
        self.check("""MOCK.item(10, 12); MOCK.put(0, 1, 10, 10); MOCK.start()
        MOCK.bags[0][1] = nil; MOCK.put(1, 1, 10, 4); MOCK.put(4, 1, 10, 6)
        MOCK.bagChange(); assert(A.Bags.state.value == 120 and A.Bags.Change() == 0)
        assert(A.Bags.state.stacks == 2 and A.Bags.state.items == 10)""")


    def test_exact_item_links_keep_variant_prices_separate(self):
        self.check("""MOCK.item(10, 100, {link='item:10:variantA'})
        MOCK.item(10, 150, {link='item:10:variantB'})
        MOCK.put(0, 1, 10, 2, {hyperlink='item:10:variantA'})
        MOCK.put(0, 2, 10, 3, {hyperlink='item:10:variantB'})
        MOCK.start(); assert(A.Bags.state.value == 650)""")


    def test_unsellable_items_are_zero_even_without_loaded_item_data(self):
        self.check("""MOCK.put(0, 1, 99, 5, {hasNoValue=true}); MOCK.start()
        assert(A.Bags.state.value == 0 and A.Bags.state.pending == 0)
        assert(A.Bags.state.items == 5 and MOCK.requests[99] == nil)
        assert(A.db.bagBaseline == 0)""")


    def test_known_zero_sell_price_is_not_treated_as_unknown(self):
        self.check("""MOCK.item(10, 0); MOCK.put(0, 1, 10, 1); MOCK.start()
        assert(A.Bags.state.pending == 0 and A.Bags.state.value == 0 and MOCK.requests[10] == nil)""")


    def test_initial_cold_item_data_waits_before_setting_baseline(self):
        self.check("""MOCK.item(10, 50); local item = MOCK.item(20, 100, {cold=true})
        MOCK.put(0, 1, 10, 1); MOCK.put(0, 2, 20, 2); MOCK.start()
        assert(A.Bags.state.value == 50 and A.Bags.state.pending == 1)
        assert(A.db.bagBaseline == nil and A.Bags.Change() == nil)
        assert(A.UI.bagValue:GetText():sub(1,3) == '>= ' and A.UI.bagChange == nil)
        item.cold = false; MOCK.event('ITEM_DATA_LOAD_RESULT', 20, true); MOCK.advance(1)
        assert(A.Bags.state.value == 250 and A.db.bagBaseline == 250 and A.Bags.Change() == 0)""")


    def test_new_cold_items_count_as_gain_after_prices_resolve(self):
        self.check("""MOCK.start(); local item = MOCK.item(20, 100, {cold=true})
        MOCK.put(0, 1, 20, 2); MOCK.bagChange()
        assert(A.db.bagBaseline == 0 and A.Bags.Change() == nil)
        item.cold = false; MOCK.event('GET_ITEM_INFO_RECEIVED', 20, true); MOCK.advance(1)
        assert(A.Bags.Change() == 200 and A.Bags.state.pending == 0)""")


    def test_failed_item_data_requests_stay_pending_and_retry_at_most_every_five_seconds(self):
        self.check("""MOCK.item(20, 100, {cold=true}); MOCK.put(0, 1, 20, 2); MOCK.start()
        assert(MOCK.requests[20] == 1)
        for i=1,4 do MOCK.event('GET_ITEM_INFO_RECEIVED', 20, false); MOCK.advance(1) end
        assert(MOCK.requests[20] == 1 and A.Bags.state.pending == 1 and A.db.bagBaseline == nil)
        MOCK.advance(1); assert(MOCK.requests[20] == 2 and A.Bags.Change() == nil)""")


    def test_slot_with_known_id_but_missing_info_does_not_look_empty(self):
        self.check("""MOCK.item(10, 50); local stack = MOCK.put(0, 1, 10, 1, {missingInfo=true})
        MOCK.start(); assert(A.Bags.state.pending == 1 and A.db.bagBaseline == nil)
        stack.missingInfo = false; MOCK.event('ITEM_DATA_LOAD_RESULT', 10, true); MOCK.advance(1)
        assert(A.Bags.state.value == 50 and A.db.bagBaseline == 50 and A.Bags.Change() == 0)""")


    def test_unavailable_backpack_does_not_establish_zero_baseline(self):
        self.check("""MOCK.slots[0] = 0; MOCK.start()
        assert(A.db.bagBaseline == nil and A.Bags.state.pending == 1)
        MOCK.slots[0] = 16; MOCK.item(10, 50); MOCK.put(0, 1, 10, 1); MOCK.bagChange()
        assert(A.db.bagBaseline == 50 and A.Bags.Change() == 0)""")


    def test_invalid_quantity_waits_for_valid_stack_data(self):
        self.check("""MOCK.item(10, 50); local stack = MOCK.put(0, 1, 10, 0)
        MOCK.start(); assert(A.Bags.state.pending == 1 and A.db.bagBaseline == nil)
        stack.stackCount = 3; MOCK.bagChange()
        assert(A.Bags.state.value == 150 and A.db.bagBaseline == 150)""")


    def test_invalid_price_is_not_counted_as_zero(self):
        self.check("""local item = MOCK.item(10, -50); MOCK.put(0, 1, 10, 1); MOCK.start()
        assert(A.Bags.state.pending == 1 and A.db.bagBaseline == nil)
        item.price = 50; MOCK.advance(1); assert(A.Bags.state.value == 50 and A.db.bagBaseline == 50)""")


    def test_bag_scans_coalesce_and_do_not_run_during_unchanged_idle_time(self):
        self.check("""MOCK.start(); assert(MOCK.scanCalls == 5)
        MOCK.advance(60); assert(MOCK.scanCalls == 5)
        MOCK.event('GET_ITEM_INFO_RECEIVED', 999, true); MOCK.advance(1); assert(MOCK.scanCalls == 5)
        for i=1,30 do MOCK.event('BAG_UPDATE_DELAYED') end
        MOCK.advance(1); assert(MOCK.scanCalls == 10)""")


    def test_bag_tracking_continues_while_panel_is_hidden(self):
        self.check("""MOCK.start(); A.Command('hide'); MOCK.item(10, 200); MOCK.put(0, 1, 10, 1)
        MOCK.bagChange(); assert(not A.UI.panel:IsShown() and A.Bags.Change() == 200)
        A.Command('show'); assert(MOCK.plain(A.UI.bagValue:GetText()) == '0g 2s 0c')""")


    def test_reset_updates_bag_baseline_and_clears_xp_at_the_same_time(self):
        self.check("""MOCK.item(10, 5); local stack = MOCK.put(0, 1, 10, 1); MOCK.start()
        MOCK.advance(60); MOCK.gain(25); stack.stackCount = 4; MOCK.bagChange()
        assert(A.Bags.Change() == 15 and A.db.xp == 25)
        A.UI.reset:GetScript('OnClick')()
        assert(A.Bags.Change() == 0 and A.db.bagBaseline == 20 and A.db.xp == 0 and A.SinceStart() == 0)
        stack.stackCount = 5; MOCK.bagChange(); assert(A.Bags.Change() == 5)""")


    def test_reset_while_prices_are_pending_waits_for_complete_baseline(self):
        self.check("""MOCK.start(); local item = MOCK.item(10, 50, {cold=true}); MOCK.put(0, 1, 10, 1)
        MOCK.bagChange(); A.Reset(); assert(A.db.bagBaseline == nil and A.Bags.Change() == nil)
        item.cold = false; MOCK.advance(1); assert(A.db.bagBaseline == 50 and A.Bags.Change() == 0)""")


    def test_saved_bag_baseline_survives_login_and_zone_changes(self):
        self.check("""ElmoLevelingDB = {bagBaseline=100}; MOCK.item(10, 200); MOCK.put(0, 1, 10, 1)
        MOCK.start(); assert(A.Bags.Change() == 100)
        MOCK.event('PLAYER_ENTERING_WORLD', false, false); assert(A.Bags.Change() == 100)
        MOCK.event('PLAYER_LOGOUT'); assert(ElmoLevelingDB.bagBaseline == 100)""")


    def test_zero_baseline_is_restored_instead_of_being_replaced(self):
        self.check("""ElmoLevelingDB = {bagBaseline=0}; MOCK.item(10, 200); MOCK.put(0, 1, 10, 1)
        MOCK.start(); assert(A.db.bagBaseline == 0 and A.Bags.Change() == 200)""")


    def test_coin_formatting_preserves_gold_silver_and_copper(self):
        self.check("""assert(MOCK.plain(A.UI.Money(123456)) == '12g 34s 56c')
        assert(MOCK.plain(A.UI.Money(-10001,true)) == '-1g 0s 1c')
        assert(MOCK.plain(A.UI.Money(0,true)) == '0g 0s 0c')
        assert(MOCK.plain(A.UI.Money(10000,true)) == '+1g 0s 0c')""")


    def test_missing_container_api_waits_without_creating_false_baseline(self):
        self.check("""C_Container = nil; MOCK.start()
        assert(A.Bags.state.pending == 1 and A.db.bagBaseline == nil and A.UI.bagChange == nil)""")


    def test_legacy_item_info_fallback_retains_correct_unit_prices(self):
        self.check("""MOCK.item(10, 75); MOCK.put(0,1,10,2)
        GetItemInfo = C_Item.GetItemInfo; C_Item = nil; MOCK.start()
        assert(A.Bags.state.value == 150 and A.Bags.state.pending == 0)""")


    def test_hunter_prefers_useful_stats_over_item_level_and_rarity(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=2},{itemLevel=20})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=4},{itemLevel=10})
        MOCK.gear(30,'INVTYPE_CHEST',{ITEM_MOD_INTELLECT_SHORT=5},{itemLevel=99,quality=4})
        MOCK.equipped[5]='item:10'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:20').upgrade)
        assert(not A.Upgrades.Evaluate('item:30').upgrade)
        assert(not A.Upgrades.Evaluate('item:10').upgrade)""")


    def test_unusable_and_above_level_items_never_get_borders(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=50},{unusable=true})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=50},{required=10})
        MOCK.put(0,1,10,1); MOCK.put(0,2,20,1); MOCK.start()
        local container,buttons=MOCK.nativeBag(0,2)
        assert(not buttons[1].ElmoLevelingUpgrade and not buttons[2].ElmoLevelingUpgrade)
        MOCK.level=10; MOCK.event('PLAYER_LEVEL_UP',10); MOCK.advance(1)
        assert(buttons[2].ElmoLevelingUpgrade and not buttons[1].ElmoLevelingUpgrade)""")


    def test_empty_armor_slot_is_an_upgrade_but_cosmetics_and_bags_are_not(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{}, {armor=30})
        MOCK.gear(20,'INVTYPE_BODY',{ITEM_MOD_AGILITY_SHORT=99})
        MOCK.gear(30,'INVTYPE_TABARD',{ITEM_MOD_AGILITY_SHORT=99})
        MOCK.gear(40,'INVTYPE_BAG',{ITEM_MOD_AGILITY_SHORT=99}); MOCK.item(50,999)
        MOCK.start(); assert(A.Upgrades.Evaluate('item:10').upgrade)
        for _,id in ipairs({20,30,40,50}) do assert(not A.Upgrades.Evaluate('item:'..id).upgrade) end""")


    def test_ring_replaces_weaker_of_two_and_nonunique_copy_can_fill_other_slot(self):
        self.check("""MOCK.gear(10,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.gear(20,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=1})
        MOCK.gear(30,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=3})
        MOCK.equipped[11]='item:10'; MOCK.equipped[12]='item:20'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:30').upgrade and A.Upgrades.Evaluate('item:30').slot == 12)
        assert(A.Upgrades.Evaluate('item:10').upgrade and A.Upgrades.Evaluate('item:10').slot == 12)""")


    def test_unique_ring_cannot_duplicate_but_can_replace_same_category(self):
        self.check("""MOCK.gear(10,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=5},{unique=true})
        MOCK.gear(20,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=1})
        MOCK.equipped[11]='item:10'; MOCK.equipped[12]='item:20'; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:10').upgrade)
        MOCK.gear(30,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=8},{category=42,limit=1})
        MOCK.gear(40,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=7},{category=42,limit=1})
        MOCK.equipped[11]='item:40'; MOCK.event('PLAYER_EQUIPMENT_CHANGED',11)
        assert(A.Upgrades.Evaluate('item:30').upgrade and A.Upgrades.Evaluate('item:30').slot == 11)""")


    def test_nonunique_native_zero_category_does_not_act_like_unique(self):
        self.check("""MOCK.gear(10,'INVTYPE_TRINKET',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.equipped[13]='item:10'; C_Item.GetItemUniqueness=function() return 0,0 end
        MOCK.start(); assert(A.Upgrades.Evaluate('item:10').upgrade)""")


    def test_unique_category_counts_other_slots_and_honors_limit(self):
        self.check("""MOCK.gear(10,'INVTYPE_TRINKET',{ITEM_MOD_AGILITY_SHORT=9},{category=7,limit=1})
        MOCK.gear(20,'INVTYPE_FINGER',{ITEM_MOD_AGILITY_SHORT=1},{category=7,limit=1})
        MOCK.equipped[11]='item:20'; MOCK.start(); assert(not A.Upgrades.Evaluate('item:10').upgrade)
        MOCK.items['item:10'].limit=2; MOCK.event('PLAYER_EQUIPMENT_CHANGED',11)
        assert(A.Upgrades.Evaluate('item:10').upgrade)""")


    def test_hunter_ranged_weapon_upgrade_depends_on_dps(self):
        self.check("""MOCK.gear(10,'INVTYPE_RANGED',{}, {dps=5,subclassID=2})
        MOCK.gear(20,'INVTYPE_RANGEDRIGHT',{}, {dps=7,subclassID=3})
        MOCK.gear(30,'INVTYPE_RANGED',{ITEM_MOD_AGILITY_SHORT=1},{dps=4,subclassID=2})
        MOCK.equipped[18]='item:10'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:20').upgrade and not A.Upgrades.Evaluate('item:30').upgrade)""")


    def test_hunter_melee_weapon_is_compared_as_stat_stick(self):
        self.check("""MOCK.gear(10,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=5},{dps=2})
        MOCK.gear(20,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=2},{dps=50})
        MOCK.gear(30,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=6},{dps=1})
        MOCK.equipped[16]='item:10'; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:20').upgrade and A.Upgrades.Evaluate('item:30').upgrade)""")


    def test_two_handed_weapon_accounts_for_lost_offhand_stats(self):
        self.check("""MOCK.gear(10,'INVTYPE_WEAPON',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.gear(20,'INVTYPE_WEAPONOFFHAND',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.gear(30,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=8})
        MOCK.gear(40,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=11})
        MOCK.equipped[16]='item:10'; MOCK.equipped[17]='item:20'; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:30').upgrade and A.Upgrades.Evaluate('item:40').upgrade)""")


    def test_offhand_cannot_be_added_while_using_two_hander_or_before_dual_wield(self):
        self.check("""MOCK.gear(10,'INVTYPE_2HWEAPON',{})
        MOCK.gear(20,'INVTYPE_WEAPONOFFHAND',{ITEM_MOD_AGILITY_SHORT=10})
        MOCK.equipped[16]='item:10'; MOCK.dualWield=true; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:20').upgrade)
        MOCK.equipped[16]=nil; MOCK.dualWield=false; MOCK.event('PLAYER_EQUIPMENT_CHANGED',16)
        assert(not A.Upgrades.Evaluate('item:20').upgrade)
        MOCK.dualWield=true; MOCK.event('SPELLS_CHANGED'); assert(A.Upgrades.Evaluate('item:20').upgrade)""")


    def test_generic_one_hander_can_upgrade_offhand_after_dual_wield_is_trained(self):
        self.check("""MOCK.gear(10,'INVTYPE_WEAPON',{ITEM_MOD_AGILITY_SHORT=10})
        MOCK.gear(20,'INVTYPE_WEAPON',{ITEM_MOD_AGILITY_SHORT=3})
        MOCK.equipped[16]='item:10'; MOCK.start(); assert(not A.Upgrades.Evaluate('item:20').upgrade)
        MOCK.dualWield=true; MOCK.event('SPELLS_CHANGED')
        local verdict=A.Upgrades.Evaluate('item:20'); assert(verdict.upgrade and verdict.slot == 17)""")


    def test_warrior_weapon_dps_loss_can_outweigh_more_stats(self):
        self.check("""MOCK.class='WARRIOR'
        MOCK.gear(10,'INVTYPE_2HWEAPON',{}, {dps=10})
        MOCK.gear(20,'INVTYPE_2HWEAPON',{ITEM_MOD_STRENGTH_SHORT=2},{dps=5})
        MOCK.gear(30,'INVTYPE_2HWEAPON',{}, {dps=11})
        MOCK.equipped[16]='item:10'; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:20').upgrade and A.Upgrades.Evaluate('item:30').upgrade)""")


    def test_feral_does_not_score_weapon_base_dps(self):
        self.check("""MOCK.class='DRUID'; MOCK.talents={0,10,0}
        MOCK.gear(10,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=5},{dps=2})
        MOCK.gear(20,'INVTYPE_2HWEAPON',{ITEM_MOD_AGILITY_SHORT=2},{dps=50})
        MOCK.equipped[16]='item:10'; MOCK.start()
        assert(not A.Upgrades.Evaluate('item:20').upgrade and A.Upgrades.Profile().name == 'Druid feral')""")


    def test_talent_change_reweights_existing_bag_borders(self):
        self.check("""MOCK.class='PALADIN'; MOCK.talents={0,0,10}
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_STRENGTH_SHORT=5})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_INTELLECT_SHORT=5})
        MOCK.equipped[5]='item:10'; MOCK.put(0,1,20,1); MOCK.start()
        local _,buttons=MOCK.nativeBag(0,1); assert(not buttons[1].ElmoLevelingUpgrade)
        MOCK.talents={10,0,0}; MOCK.event('CHARACTER_POINTS_CHANGED',-1); MOCK.advance(1)
        assert(buttons[1].ElmoLevelingUpgrade and A.Upgrades.Profile().name == 'Healing')""")


    def test_protection_profile_prefers_stamina_and_armor(self):
        self.check("""MOCK.class='WARRIOR'; MOCK.talents={0,0,10}
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_STRENGTH_SHORT=5})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_STAMINA_SHORT=5},{armor=30})
        MOCK.equipped[5]='item:10'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:20').upgrade and A.Upgrades.Profile().name == 'Protection')""")


    def test_flat_tooltip_bonuses_are_counted_once_alongside_native_stats(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_RANGED_ATTACK_POWER_SHORT=10},
            {tooltip={'Equip: Increases ranged attack power by 10.','+3 Agility'}})
        MOCK.start(); local item=A.Upgrades.Read('item:10')
        assert(item.stats.rap == 10 and item.stats.agi == 3 and A.Upgrades.Score(item,5) == 16)""")


    def test_healing_bonus_can_make_a_healer_upgrade(self):
        self.check("""MOCK.class='PRIEST'; MOCK.talents={0,10,0}
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_INTELLECT_SHORT=5})
        MOCK.gear(20,'INVTYPE_CHEST',{}, {tooltip={'Equip: Increases healing done by spells and effects by up to 8.'}})
        MOCK.equipped[5]='item:10'; MOCK.start(); assert(A.Upgrades.Evaluate('item:20').upgrade)""")


    def test_cold_equipped_item_prevents_false_upgrade_then_item_load_rechecks(self):
        self.check("""local current=MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=10},{cold=true})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.equipped[5]='item:10'; MOCK.put(0,1,20,1); MOCK.start()
        local _,buttons=MOCK.nativeBag(0,1)
        assert(not buttons[1].ElmoLevelingUpgrade and MOCK.requests[10] == 1)
        MOCK.advance(1); assert(MOCK.requests[10] == 1)
        current.cold=false; MOCK.event('GET_ITEM_INFO_RECEIVED',10,true); MOCK.advance(1)
        assert(not buttons[1].ElmoLevelingUpgrade)
        current.stats.ITEM_MOD_AGILITY_SHORT=1; MOCK.event('PLAYER_EQUIPMENT_CHANGED',5); MOCK.advance(1)
        assert(buttons[1].ElmoLevelingUpgrade)""")


    def test_missing_weapon_dps_is_pending_and_never_zero_equipped_baseline(self):
        self.check("""local current=MOCK.gear(10,'INVTYPE_RANGED',{}, {tooltipCold=true})
        MOCK.gear(20,'INVTYPE_RANGED',{}, {dps=5}); MOCK.equipped[18]='item:10'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:20') == nil and MOCK.requests[10] == 1)
        current.tooltipCold=false; current.dps=10; MOCK.event('ITEM_DATA_LOAD_RESULT',10,true)
        assert(not A.Upgrades.Evaluate('item:20').upgrade)""")


    def test_random_suffix_item_links_are_scored_separately(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=1},{link='item:10:agi'})
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_INTELLECT_SHORT=1},{link='item:10:int'})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=2})
        MOCK.equipped[5]='item:10:agi'; MOCK.start()
        assert(A.Upgrades.Evaluate('item:20').upgrade and not A.Upgrades.Evaluate('item:10:int').upgrade)""")


    def test_native_border_tracks_actual_slot_and_is_mouse_transparent(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=1})
        MOCK.put(0,2,10,1); MOCK.start()
        local container,buttons=MOCK.nativeBag(0,2)
        buttons[1]:SetID(2); buttons[2]:SetID(1); ContainerFrame_Update(container)
        local border=buttons[1].ElmoLevelingUpgradeBorder
        assert(border:IsShown() and not border.mouseEnabled and border.parent == buttons[1])
        assert(not buttons[2].ElmoLevelingUpgrade and buttons[1].ElmoLevelingUpgrade)
        MOCK.bags[0][2]=nil; MOCK.bagChange(); assert(not border:IsShown())""")


    def test_upgrades_keep_working_when_meter_is_hidden(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=2})
        MOCK.put(0,1,10,1); MOCK.start(); A.Command('hide')
        local _,buttons=MOCK.nativeBag(0,1)
        assert(not A.UI.panel:IsShown() and buttons[1].ElmoLevelingUpgradeBorder:IsShown())""")


    def test_betterbags_fast_draw_rebind_clear_and_bank_do_not_leave_stale_border(self):
        self.check("""MOCK.betterBags()
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5}); MOCK.item(20,0); MOCK.start()
        local item=MOCK.betterItem('item:10',0); local b=item.button; local border=b.ElmoLevelingUpgradeBorder
        assert(A.Upgrades.betterHooked and border:IsShown())
        item.currentData.itemInfo.itemLink='item:20'; item:FinishItemDraw(); assert(not border:IsShown())
        item.currentData.itemInfo.itemLink='item:10'; item:FinishItemDraw(); assert(border:IsShown())
        item:ResetVisuals(); assert(not border:IsShown() and A.Upgrades.buttons[b] == nil)
        item.currentData.bagid=-1; item:FinishItemDraw(); assert(not border:IsShown())
        item.currentData.bagid=5; item:FinishItemDraw(); assert(not border:IsShown())
        item.currentData.bagid=4; item:FinishItemDraw(); assert(border:IsShown())
        item.currentData.isItemEmpty=true; item:FinishItemDraw(); assert(not border:IsShown())""")


    def test_betterbags_can_load_later_and_hooks_are_not_duplicated(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5}); MOCK.start()
        assert(not A.Upgrades.betterHooked); MOCK.betterBags(); MOCK.event('ADDON_LOADED','BetterBags')
        assert(A.Upgrades.betterHooked)
        local item=MOCK.betterItem('item:10',0); local border=item.button.ElmoLevelingUpgradeBorder
        local frames=#MOCK.frames; MOCK.event('ADDON_LOADED','AnotherAddon'); item:FinishItemDraw()
        assert(#MOCK.frames == frames and item.button.ElmoLevelingUpgradeBorder == border)""")


    def test_native_bank_slots_are_not_read_or_highlighted(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5}); MOCK.start()
        local _,buttons=MOCK.nativeBag(5,1)
        assert(not buttons[1].ElmoLevelingUpgrade and not buttons[1].ElmoLevelingUpgradeBorder)""")


    def test_forever_betterbags_bag_selector_is_not_an_item_slot(self):
        self.check("""MOCK.class='PRIEST'; MOCK.betterBags(); MOCK.start()
        -- BetterBags creates its bag selector with no parent or container ID.
        local selector=CreateFrame('Button','BetterBagsBagButtonTest',nil,'ItemButtonTemplate')
        SetItemButtonQuality(selector,2)
        assert(A.Upgrades.buttons[selector] == nil)
        -- A previously tracked or detached button must not abort the repaint.
        A.Upgrades.buttons[selector]={container=nil}
        MOCK.gear(10,'INVTYPE_RANGEDRIGHT',{}, {subclassID=19,dps=10.4})
        local wand=MOCK.betterItem('item:10',0)
        assert(wand.button.ElmoLevelingUpgradeBorder:IsShown())
        MOCK.equipped[18]='item:10'; MOCK.event('PLAYER_EQUIPMENT_CHANGED',18)
        MOCK.advance(1)
        assert(not wand.button.ElmoLevelingUpgradeBorder:IsShown())
        assert(not wand.button.ElmoLevelingUpgrade)""")


    def test_forever_native_item_losing_its_slot_does_not_break_other_borders(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.put(0,1,10,1); MOCK.start()
        local _,buttons=MOCK.nativeBag(0,1)
        local b=buttons[1]; assert(b.ElmoLevelingUpgradeBorder:IsShown())
        b.GetBagID=function() end; b:SetID(0)
        A.Upgrades.buttons[b]={container=nil}
        MOCK.bagChange()
        assert(not b.ElmoLevelingUpgradeBorder:IsShown())""")


    def test_forever_border_updates_when_equipment_settles_after_its_event(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=10})
        MOCK.put(0,1,10,1); MOCK.start()
        local _,buttons=MOCK.nativeBag(0,1); MOCK.advance(1)
        local border=buttons[1].ElmoLevelingUpgradeBorder; assert(border:IsShown())
        MOCK.event('PLAYER_EQUIPMENT_CHANGED',5); MOCK.advance(1)
        MOCK.equipped[5]='item:20'; MOCK.advance(1)
        assert(not border:IsShown() and not buttons[1].ElmoLevelingUpgrade)
        MOCK.equipped[5]=nil; MOCK.advance(1); assert(border:IsShown())""")


    def test_forever_border_updates_when_level_settles_after_level_up(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5},{required=2})
        MOCK.put(0,1,10,1); MOCK.start()
        local _,buttons=MOCK.nativeBag(0,1); MOCK.advance(1)
        assert(not buttons[1].ElmoLevelingUpgrade)
        MOCK.event('PLAYER_LEVEL_UP',2); MOCK.advance(1)
        MOCK.level=2; MOCK.advance(1)
        assert(buttons[1].ElmoLevelingUpgradeBorder:IsShown())""")


    def test_forever_betterbags_border_updates_after_delayed_equipment_change(self):
        self.check("""MOCK.betterBags()
        MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.gear(20,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=10}); MOCK.start()
        local item=MOCK.betterItem('item:10',0); MOCK.advance(1)
        local border=item.button.ElmoLevelingUpgradeBorder; assert(border:IsShown())
        MOCK.event('PLAYER_EQUIPMENT_CHANGED',5); MOCK.advance(1)
        MOCK.equipped[5]='item:20'; MOCK.advance(1)
        assert(not border:IsShown() and not item.button.ElmoLevelingUpgrade)""")


    def test_missing_usability_api_keeps_uncertain_equipment_unmarked(self):
        self.check("""MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=5}); MOCK.start()
        C_PlayerInfo=nil; assert(not A.Upgrades.Evaluate('item:10').upgrade)""")


    def test_assigned_group_role_takes_precedence_over_talent_profile(self):
        self.check("""MOCK.class='PALADIN'; MOCK.talents={0,0,10}; MOCK.start()
        assert(A.Upgrades.Profile().name == 'Paladin damage')
        MOCK.role='HEALER'; MOCK.event('PLAYER_ROLES_ASSIGNED'); assert(A.Upgrades.Profile().name == 'Healing')
        MOCK.role='TANK'; MOCK.event('GROUP_ROSTER_UPDATE'); assert(A.Upgrades.Profile().name == 'Protection')
        MOCK.role='DAMAGER'; MOCK.event('PLAYER_ROLES_ASSIGNED'); assert(A.Upgrades.Profile().name == 'Paladin damage')""")


    def test_druid_assigned_tank_still_ignores_base_weapon_dps(self):
        self.check("""MOCK.class='DRUID'; MOCK.role='TANK'; MOCK.talents={0,10,0}
        MOCK.gear(10,'INVTYPE_2HWEAPON',{ITEM_MOD_STAMINA_SHORT=5},{dps=2})
        MOCK.gear(20,'INVTYPE_2HWEAPON',{ITEM_MOD_STAMINA_SHORT=2},{dps=50})
        MOCK.equipped[16]='item:10'; MOCK.start()
        assert(A.Upgrades.Profile().name == 'Druid tank' and not A.Upgrades.Evaluate('item:20').upgrade)""")


    def test_fishing_poles_are_not_combat_upgrades(self):
        self.check("""MOCK.class='WARRIOR'
        MOCK.gear(10,'INVTYPE_2HWEAPON',{ITEM_MOD_STRENGTH_SHORT=99},{dps=100,subclassID=20})
        MOCK.start(); assert(not A.Upgrades.Evaluate('item:10').upgrade)""")


    def test_legacy_three_value_talent_points_remain_supported(self):
        self.check("""MOCK.class='PALADIN'; MOCK.talents={10,0,0}
        GetTalentTabInfo=function(index) return 'Tree '..index,100,MOCK.talents[index],'Background' end
        MOCK.start(); assert(A.Upgrades.Profile().name == 'Healing')""")


    def test_namespaced_talent_api_is_used_without_global_wrapper(self):
        self.check("""MOCK.class='PALADIN'; GetTalentTabInfo=nil
        C_SpecializationInfo={GetSpecializationInfo=function(index)
            return index,'Tree '..index,'Description',100,'NONE',0,index==2 and 10 or 0 end}
        MOCK.start(); assert(A.Upgrades.Profile().name == 'Protection')""")


    def test_forever_native_bag_border_uses_button_bag_in_combined_bags(self):
        self.check("""MOCK.forever(); MOCK.gear(10,'INVTYPE_CHEST',{ITEM_MOD_AGILITY_SHORT=3})
        MOCK.put(2,1,10,1); MOCK.start()
        local parent=CreateFrame('Frame',nil,UIParent); parent:SetID(0)
        local button=CreateFrame('Button',nil,parent); button:SetID(1); button.bagID=2
        SetItemButtonQuality(button,2,'item:10')
        assert(button.ElmoLevelingUpgradeBorder:IsShown() and not button.ElmoLevelingUpgradeBorder.mouseEnabled)
        button.bagID=5; SetItemButtonQuality(button,2,'item:10')
        assert(not button.ElmoLevelingUpgradeBorder:IsShown())""")


    def test_forever_item_tooltip_reader_and_spellbook_handle_ranged_dps_and_dual_wield(self):
        self.check("""MOCK.forever(); MOCK.gear(10,'INVTYPE_RANGED',{}, {dps=5})
        MOCK.gear(20,'INVTYPE_RANGED',{}, {dps=7}); MOCK.equipped[18]='item:10'
        MOCK.gear(30,'INVTYPE_WEAPONOFFHAND',{ITEM_MOD_AGILITY_SHORT=5})
        MOCK.start(); assert(A.Upgrades.Evaluate('item:20').upgrade)
        assert(not A.Upgrades.Evaluate('item:30').upgrade)
        MOCK.dualWield=true; MOCK.event('SPELLS_CHANGED'); assert(A.Upgrades.Evaluate('item:30').upgrade)
        assert(A.Compat.tooltip == nil, 'Native C_TooltipInfo should not need a hidden GameTooltip')""")


    def test_forever_trait_ranks_choose_role_and_refresh_after_config_update(self):
        self.check("""MOCK.forever(); MOCK.class='PALADIN'; MOCK.traits({0,0,10}); MOCK.start()
        assert(A.Upgrades.Profile().name == 'Paladin damage')
        MOCK.traits({10,0,0}); MOCK.event('TRAIT_CONFIG_UPDATED',100)
        assert(A.Upgrades.Profile().name == 'Healing')
        MOCK.traits({0,10,0}); MOCK.event('TRAIT_CONFIG_UPDATED',100)
        assert(A.Upgrades.Profile().name == 'Protection')""")


    def test_forever_trait_node_with_unknown_new_spell_cannot_receive_old_branch_rank(self):
        self.check("""MOCK.forever(); MOCK.class='PALADIN'; MOCK.traits({1,10,0},true)
        MOCK.start(); assert(A.Upgrades.Profile().name == 'Healing')""")







    def test_single_line_shows_actual_time_and_xp_including_idle(self):
        self.check("""MOCK.start();MOCK.advance(60);MOCK.gain(100)
        local s=A.Stats();assert(s.totalXP==100 and s.elapsed==60)
        assert(MOCK.plain(A.UI.summary:GetText())=='Time 00:01:00  ·  XP +100')
        MOCK.advance(1800);s=A.Stats();assert(s.totalXP==100 and s.elapsed==1860)
        assert(A.UI.hour==nil and A.UI.day==nil and A.UI.averageHour==nil and A.Mobs==nil)
        assert(A.UI.panel.height==164 and A.db.periods==nil)""")

    def test_session_continues_across_hour_and_day_boundaries_without_resets(self):
        self.check("""MOCK.start();MOCK.gain(75);MOCK.advance(3600);MOCK.gain(25)
        local s=A.Stats();assert(s.totalXP==100 and s.elapsed==3600)
        MOCK.advance(86400);s=A.Stats();assert(s.totalXP==100 and s.elapsed==90000)
        assert(MOCK.plain(A.UI.summary:GetText())=='Time 1d 01:00:00  ·  XP +100')
        MOCK.gain(40);assert(A.Stats().totalXP==140 and A.TickPeriods==nil)""")

    def test_existing_session_totals_and_explicit_start_are_preserved(self):
        self.check("""ElmoLevelingDB={xp=12450,seconds=3600,measurementAt=1200,
            periods={hour={xp=20,start=3500}}}
        MOCK.start();local s=A.Stats();assert(s.totalXP==12450 and s.elapsed==2400)
        assert(A.db.periods==nil and MOCK.plain(A.UI.summary:GetText())=='Time 00:40:00  ·  XP +12,450')
        A.Command('start');assert(A.Stats().totalXP==0 and A.Stats().elapsed==0)
        assert(MOCK.plain(A.UI.summary:GetText())=='Time 00:00:00  ·  XP +0')""")

    def test_restart_preserves_current_level_clock_and_completed_history(self):
        self.check("""MOCK.start();MOCK.event('TIME_PLAYED_MSG',5000,1000);MOCK.advance(10)
        MOCK.level,MOCK.xp,MOCK.maximum=2,10,900
        MOCK.event('PLAYER_LEVEL_UP',2);MOCK.event('PLAYER_XP_UPDATE','player')
        MOCK.advance(40);local seconds=A.Levels.CurrentSeconds();assert(#A.db.levels==1)
        A.Reset();local s=A.Stats()
        assert(s.totalXP==0 and s.elapsed==0 and #A.db.levels==1)
        assert(A.Levels.CurrentSeconds()==seconds and A.db.levels[1].seconds==1010)
        MOCK.advance(20);MOCK.gain(30);assert(A.Stats().totalXP==30 and A.Levels.CurrentSeconds()==60)""")

    def test_session_survives_logout_and_excludes_offline_time(self):
        self.check("""MOCK.start();MOCK.advance(1200);MOCK.gain(50);MOCK.event('PLAYER_LOGOUT')
        assert(A.db.seconds==1200 and A.frame:GetScript('OnUpdate')==nil)
        MOCK.advance(100000);MOCK.event('PLAYER_ENTERING_WORLD',true,false)
        assert(A.Stats().totalXP==50 and A.Stats().elapsed==1200)
        MOCK.advance(2400);assert(A.Stats().elapsed==3600 and A.Stats().totalXP==50)""")

    def test_fresh_lua_reload_restores_session_and_level_state(self):
        self.check("""MOCK.start();MOCK.event('TIME_PLAYED_MSG',5000,800)
        MOCK.advance(1200);MOCK.gain(50);MOCK.event('PLAYER_LOGOUT')""")
        def unpack(value):
            return {key:unpack(item) for key,item in value.items()} if hasattr(value,'items') else value
        saved=unpack(self.vm.globals().ElmoLevelingDB)
        self.setUp()
        self.vm.globals().ElmoLevelingDB=self.vm.table_from(saved,recursive=True)
        self.check("""MOCK.time=100000;MOCK.xp=150;MOCK.start(false,true)
        assert(A.Stats().totalXP==50 and A.Stats().elapsed==1200)
        assert(A.Levels.CurrentSeconds()==2000)
        MOCK.advance(2400);assert(A.Stats().totalXP==50 and A.Stats().elapsed==3600)
        assert(A.Levels.CurrentSeconds()==4400)""")

    def test_zone_events_do_not_restart_session_or_repeat_played_requests(self):
        self.check("""MOCK.start();MOCK.advance(120);MOCK.gain(20)
        MOCK.event('PLAYER_ENTERING_WORLD',false,false);MOCK.advance(30)
        assert(A.Stats().totalXP==20 and A.Stats().elapsed==150 and MOCK.playedRequests==1)""")

    def test_level_transition_uses_native_full_played_time_and_all_idle(self):
        self.check("""MOCK.level=38;MOCK.start();MOCK.event('TIME_PLAYED_MSG',200000,90000)
        MOCK.advance(3661);MOCK.level,MOCK.xp,MOCK.maximum=39,20,900
        MOCK.event('PLAYER_LEVEL_UP',39);MOCK.event('PLAYER_XP_UPDATE','player')
        local e=A.db.levels[1];assert(e.from==38 and e.to==39 and e.seconds==93661 and e.complete)
        assert(A.UI.SessionTime(e.seconds)=='1d 02h 01m 01s' and A.Levels.CurrentSeconds()==0)
        A.UI.ToggleLevels();assert(A.UI.levelPanel:IsShown())
        assert(A.UI.levelRows[2].duration:GetText()=='1d 02h 01m 01s')
        assert(A.UI.levelRows[2].status:GetText()=='Complete')""")

    def test_missing_native_played_time_marks_only_first_interval_partial(self):
        self.check("""RequestTimePlayed=nil;MOCK.start();MOCK.advance(60)
        MOCK.level,MOCK.xp,MOCK.maximum=2,20,900
        MOCK.event('PLAYER_LEVEL_UP',2);MOCK.event('PLAYER_XP_UPDATE','player')
        assert(A.db.levels[1].seconds==60 and not A.db.levels[1].complete)
        MOCK.advance(90);MOCK.level,MOCK.xp,MOCK.maximum=3,10,1400
        MOCK.event('PLAYER_LEVEL_UP',3);MOCK.event('PLAYER_XP_UPDATE','player')
        assert(A.db.levels[1].seconds==90 and A.db.levels[1].complete)
        assert(A.UI.levelRows[3].status:GetText()=='Partial')""")

    def test_delayed_played_reply_for_previous_level_is_ignored(self):
        self.check("""MOCK.start();MOCK.advance(10);MOCK.event('PLAYER_LEVEL_UP',2)
        MOCK.event('TIME_PLAYED_MSG',100000,90000)
        assert(A.db.levelState.level==2 and A.Levels.CurrentSeconds()==0)
        assert(A.db.levels[1].seconds==10 and not A.db.levels[1].complete)""")

    def test_duplicate_level_events_and_xp_events_record_one_transition(self):
        self.check("""MOCK.start();MOCK.event('TIME_PLAYED_MSG',10000,1000);MOCK.advance(30)
        MOCK.event('PLAYER_LEVEL_UP',2);MOCK.event('PLAYER_LEVEL_UP',2)
        assert(A.db.xp==0 and #A.db.levels==1)
        MOCK.level,MOCK.xp,MOCK.maximum=2,20,900
        MOCK.event('PLAYER_XP_UPDATE','player');MOCK.event('PLAYER_XP_UPDATE','player')
        assert(A.db.xp==320 and #A.db.levels==1 and A.db.levels[1].seconds==1030)""")

    def test_xp_bar_can_settle_before_native_level_without_double_counting(self):
        self.check("""MOCK.start();MOCK.xp,MOCK.maximum=20,900
        MOCK.event('PLAYER_XP_UPDATE','player');assert(A.db.xp==320 and #A.db.levels==1)
        MOCK.event('PLAYER_LEVEL_UP',2);MOCK.level=2;MOCK.advance(1)
        assert(A.db.xp==320 and #A.db.levels==1)""")

    def test_final_level_and_max_level_display(self):
        self.check("""MOCK.level,MOCK.xp,MOCK.maximum=59,209700,209800;MOCK.start()
        MOCK.event('TIME_PLAYED_MSG',500000,20000);MOCK.advance(10)
        MOCK.level,MOCK.xp,MOCK.maximum=60,0,0
        MOCK.event('PLAYER_LEVEL_UP',60);MOCK.event('PLAYER_XP_UPDATE','player')
        assert(A.db.xp==100 and #A.db.levels==1 and A.db.levels[1].seconds==20010)
        assert(A.UI.levelRows[1].status:GetText()=='Max level')
        MOCK.advance(3600);assert(A.Stats().totalXP==100)""")

    def test_hidden_meter_continues_tracking_without_mob_events(self):
        self.check("""MOCK.start();A.Command('hide');MOCK.advance(80);MOCK.gain(30)
        assert(A.Stats().totalXP==30 and not A.UI.panel:IsShown())
        for _,event in ipairs({'COMBAT_LOG_EVENT_UNFILTERED','CHAT_MSG_COMBAT_XP_GAIN','PLAYER_TARGET_CHANGED',
            'UPDATE_MOUSEOVER_UNIT','NAME_PLATE_UNIT_ADDED','UNIT_HEALTH','PLAYER_REGEN_DISABLED'})do
            assert(not A.frame.events[event])
        end
        A.Command('show');assert(MOCK.plain(A.UI.summary:GetText()):find('XP +30',1,true))""")

    def test_retired_samples_do_not_change_the_saved_session(self):
        self.check("""ElmoLevelingDB={xp=37,seconds=20,history={{at=10,xp=500}},kills={{}},respawns={{}},
            periods={hour={start=math.huge,xp=200},day={start=10,xp=-4}},levelState={level='bad'}}
        MOCK.start();local s=A.Stats();assert(s.totalXP==37 and s.elapsed==20)
        assert(A.db.xp==37 and A.db.kills==nil and A.db.history==nil and A.db.respawns==nil)
        assert(A.db.levelState.level==1 and not A.db.levelState.complete)""")

    def test_invalid_or_secret_snapshots_and_played_values_do_not_create_awards(self):
        self.check("""local secret={};issecretvalue=function(v)return v==secret end
        MOCK.start();MOCK.xp=secret;MOCK.event('PLAYER_XP_UPDATE','player')
        MOCK.event('TIME_PLAYED_MSG',secret,secret);assert(A.db.xp==0)
        MOCK.xp=90;MOCK.event('PLAYER_XP_UPDATE','player');assert(A.db.xp==0)
        MOCK.xp=125;MOCK.event('PLAYER_XP_UPDATE','player');assert(A.db.xp==25)""")

    def test_level_gap_is_unknown_instead_of_invented_xp_or_individual_times(self):
        self.check("""MOCK.start();MOCK.advance(60);MOCK.level,MOCK.xp,MOCK.maximum=3,20,1400
        MOCK.event('PLAYER_LEVEL_UP',3);MOCK.event('PLAYER_XP_UPDATE','player')
        assert(A.db.xpGap and A.db.xp==0 and #A.db.levels==2)
        assert(A.db.levels[1].seconds==nil and MOCK.plain(A.UI.summary:GetText()):find('XP --',1,true))
        assert(A.UI.levelRows[2].status:GetText()=='Unavailable')
        A.Reset();assert(not A.db.xpGap and #A.db.levels==2 and MOCK.plain(A.UI.summary:GetText()):find('XP +0',1,true))""")

    def test_level_history_scrolling_clear_and_xp_restart_are_independent(self):
        self.check("""MOCK.start();for level=2,15 do MOCK.advance(10);A.Levels.Advance(level) end
        A.UI.Update();A.UI.ToggleLevels();A.UI.ScrollLevels(8)
        assert(A.UI.levelOffset==7 and A.UI.levelRows[1].entry.from==8)
        local seconds=A.Levels.CurrentSeconds();A.Levels.ClearHistory();A.UI.RefreshLevels()
        assert(A.UI.levelOffset==0 and A.Levels.CurrentSeconds()==seconds and #A.db.levels==0)
        A.UI.ToggleLevels();assert(not A.UI.levelPanel:IsShown() and A.UI.panel.width==332)""")

    def test_full_weighted_score_examples_and_threshold(self):
        self.check("""MOCK.start();local u=A.Upgrades
        local hunter={classID=4,stats={agi=5,sta=3,armor=100}}
        assert(math.abs(u.Score(hunter,5)-12.8)<0.00001)
        MOCK.class='PRIEST';MOCK.talents={10,0,0};u.Invalidate()
        local priest={classID=4,stats={int=10,spirit=5,spell=12,healing=20}}
        assert(math.abs(u.Score(priest,5)-43.6)<0.00001)
        MOCK.talents={0,0,10};u.Invalidate();assert(math.abs(u.Score(priest,5)-24.5)<0.00001)""")


if __name__ == "__main__":
    unittest.main()
