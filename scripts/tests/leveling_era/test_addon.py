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
        namespace = self.vm.table()
        namespace.flavor = "classic"
        load = self.vm.eval('function(s, n, ns) assert(loadstring(s, "@" .. n))("ElmoLeveling", ns) end')
        for name in (ADDON / "ElmoLeveling.toc").read_text().splitlines():
            if name.endswith(".lua"):
                load((ADDON / name).read_text(), name, namespace)
        self.vm.globals().A = namespace

    def check(self, code):
        self.vm.execute(code)

    def test_first_start_does_not_count_existing_xp(self):
        self.check("""MOCK.start()
        assert(A.db.xp == 0 and A.Elapsed() == 0)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '0')
        assert(A.UI.panel:IsShown() and ElmoLevelingPanel == A.UI.panel)
        assert(SLASH_CLASSICLEVELING1 == '/clvl' and SlashCmdList.CLASSICLEVELING == A.Command)
        assert(SLASH_CLASSICLEVELING3 == '/cxp' and SLASH_CLASSICLEVELING4 == '/classicxp')""")

    def test_exact_rates_after_one_minute(self):
        self.check("""MOCK.start(); MOCK.advance(60); MOCK.gain(120)
        local xp, seconds, minute, hour = A.Stats()
        assert(xp == 120 and seconds == 60 and minute == 120 and hour == 7200)
        A.UI.Update(true) -- Check exact rate formatting separately from the five-second cadence.
        assert(A.UI.minute:GetText() == '120' and A.UI.hour:GetText() == '120')
        assert(A.UI.averageMinute:GetText() == '120' and A.UI.averageHour:GetText() == '7,200')
        assert(A.UI.total:GetText() == 'Session XP: 120' and A.UI.time:GetText() == 'Combat 0h 0m 0s | Total 0h 1m 0s')""")

    def test_multiple_sources_add_actual_awards(self):
        self.check("""MOCK.maximum = 10000; MOCK.start(); MOCK.advance(600)
        for _, amount in ipairs({100, 250, 25, 200}) do MOCK.gain(amount) end
        local xp, _, minute, hour = A.Stats()
        assert(xp == 575 and minute == 57.5 and hour == 3450)""")

    def test_idle_time_reduces_average(self):
        self.check("""MOCK.start(); MOCK.advance(60); MOCK.gain(100); MOCK.advance(60)
        local xp, seconds, minute, hour = A.Stats()
        assert(xp == 100 and seconds == 120 and minute == 50 and hour == 3000)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '100')
        assert(A.UI.averageHour:GetText() == '3,000')""")

    def test_no_division_by_zero_at_first_award(self):
        self.check("""MOCK.start(); MOCK.gain(20)
        local xp, seconds, minute, hour = A.Stats()
        assert(xp == 20 and seconds == 0 and minute == 0 and hour == 0)
        MOCK.advance(1); assert(select(3, A.Stats()) == 1200)""")

    def test_duplicate_player_events_and_pet_events(self):
        self.check("""MOCK.start(); MOCK.gain(25)
        MOCK.event('PLAYER_XP_UPDATE', 'player'); MOCK.event('PLAYER_XP_UPDATE', 'pet')
        MOCK.event('PLAYER_XP_UPDATE', 'party1'); assert(A.db.xp == 25)""")

    def test_level_up_event_before_xp_bar_changes(self):
        self.check("""MOCK.xp = 380; MOCK.start(); MOCK.advance(60)
        MOCK.event('PLAYER_LEVEL_UP', 2); MOCK.advance(1); assert(A.db.xp == 0)
        MOCK.level, MOCK.xp, MOCK.maximum = 2, 50, 900
        MOCK.event('PLAYER_XP_UPDATE', 'player'); assert(A.db.xp == 70)
        MOCK.advance(1); assert(A.db.xp == 70)""")

    def test_xp_event_before_level_up_event(self):
        self.check("""MOCK.xp = 380; MOCK.start()
        MOCK.level, MOCK.xp, MOCK.maximum = 2, 50, 900
        MOCK.event('PLAYER_XP_UPDATE', 'player'); MOCK.event('PLAYER_LEVEL_UP', 2)
        MOCK.advance(1); assert(A.db.xp == 70)
        MOCK.gain(100); assert(A.db.xp == 170)""")

    def test_rollover_overflow_larger_than_previous_xp(self):
        self.check("""MOCK.xp = 10; MOCK.start()
        MOCK.level, MOCK.xp, MOCK.maximum = 2, 50, 900
        MOCK.event('PLAYER_XP_UPDATE', 'player'); assert(A.db.xp == 440)""")

    def test_new_xp_bar_before_unit_level_changes(self):
        self.check("""MOCK.xp = 380; MOCK.start()
        MOCK.xp, MOCK.maximum = 50, 900; MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 70)
        MOCK.level = 2; MOCK.event('PLAYER_LEVEL_UP', 2); MOCK.advance(1)
        assert(A.db.xp == 70)
        MOCK.gain(30); assert(A.db.xp == 100)""")

    def test_unit_level_changes_before_xp_bar(self):
        self.check("""MOCK.xp = 380; MOCK.start(); MOCK.level = 2
        MOCK.event('PLAYER_LEVEL_UP', 2); MOCK.advance(1); assert(A.db.xp == 0)
        MOCK.xp, MOCK.maximum = 50, 900; MOCK.advance(1); assert(A.db.xp == 70)""")

    def test_multiple_sequential_level_ups(self):
        self.check("""MOCK.xp = 380; MOCK.start()
        MOCK.level, MOCK.xp, MOCK.maximum = 2, 50, 900; MOCK.event('PLAYER_XP_UPDATE', 'player')
        MOCK.gain(800)
        MOCK.level, MOCK.xp, MOCK.maximum = 3, 20, 1400
        MOCK.event('PLAYER_LEVEL_UP', 3); MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 940)""")

    def test_final_level_up_to_level_sixty(self):
        self.check("""MOCK.level, MOCK.xp, MOCK.maximum = 59, 209700, 209800; MOCK.start()
        MOCK.level, MOCK.xp, MOCK.maximum = 60, 0, 0
        MOCK.event('PLAYER_LEVEL_UP', 60); MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 100)
        MOCK.advance(60); assert(select(4, A.Stats()) == 6000)""")

    def test_max_level_character_stays_zero(self):
        self.check("""MOCK.level, MOCK.xp, MOCK.maximum = 60, 0, 0; MOCK.start(); MOCK.advance(300)
        MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 0 and A.UI.hour:GetText() == '0')""")

    def test_zone_change_does_not_reset_or_duplicate(self):
        self.check("""MOCK.start(); MOCK.advance(20); MOCK.gain(20)
        MOCK.event('PLAYER_ENTERING_WORLD', false, false); MOCK.advance(40)
        assert(A.db.xp == 20 and A.Elapsed() == 60)""")

    def test_reset_button_and_following_award(self):
        self.check("""MOCK.start(); MOCK.advance(60); MOCK.gain(100)
        A.UI.reset:GetScript('OnClick')(A.UI.reset)
        assert(A.db.xp == 0 and A.Elapsed() == 0 and A.UI.time:GetText() == 'Combat 0h 0m 0s | Total 0h 0m 0s')
        MOCK.advance(60); MOCK.gain(20); assert(select(3, A.Stats()) == 20)""")

    def test_logout_saves_time_once_and_stops_clock(self):
        self.check("""MOCK.start(); MOCK.advance(90); MOCK.gain(75)
        MOCK.event('PLAYER_LOGOUT'); assert(A.db.seconds == 90 and A.db.xp == 75)
        MOCK.advance(10000); MOCK.event('PLAYER_LOGOUT')
        assert(A.Elapsed() == 90 and A.frame:GetScript('OnUpdate') == nil)""")

    def test_saved_totals_resume_without_offline_xp_or_time(self):
        self.check("""ElmoLevelingDB = {xp = 120, seconds = 60}
        MOCK.time, MOCK.xp, MOCK.maximum = 999999, 350, 10000
        MOCK.start(); MOCK.advance(60); MOCK.gain(60)
        local xp, seconds, minute, hour = A.Stats()
        assert(xp == 180 and seconds == 120 and minute == 90 and hour == 5400)""")

    def test_reload_resume_from_saved_values(self):
        self.check("""MOCK.start(); MOCK.advance(60); MOCK.gain(120); MOCK.event('PLAYER_LOGOUT')""")
        db = self.vm.globals().ElmoLevelingDB
        xp, seconds = db.xp, db.seconds
        self.setUp()  # Fresh Lua/UI runtime, like /reload.
        self.check(f"""ElmoLevelingDB = {{xp = {xp}, seconds = {seconds}}}
        MOCK.start(); MOCK.advance(60); MOCK.gain(60)
        assert(A.db.xp == 180 and A.Elapsed() == 120 and select(4, A.Stats()) == 5400)""")

    def test_hidden_panel_still_tracks_and_reopens(self):
        self.check("""MOCK.start(); A.Command('hide'); assert(not A.UI.panel:IsShown())
        MOCK.advance(60); MOCK.gain(10); MOCK.advance(5); A.Command('')
        assert(A.UI.panel:IsShown() and A.db.xp == 10 and A.UI.minute:GetText() == '10')
        A.Command(''); assert(A.db.hidden); A.Command('show'); assert(A.UI.panel:IsShown())""")

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

    def test_corrupt_saved_data_is_sanitized(self):
        self.check("""ElmoLevelingDB = {xp = -4, seconds = math.huge, hidden = 'yes',
            locked = 1, position = {x = 0/0, y = -270}}
        MOCK.start(); assert(A.db.xp == 0 and A.db.seconds == 0)
        assert(not A.db.hidden and not A.db.locked and A.db.position == nil)""")

    def test_invalid_xp_snapshot_does_not_destroy_baseline(self):
        self.check("""MOCK.start(); MOCK.xp = nil; MOCK.event('PLAYER_XP_UPDATE', 'player')
        MOCK.xp = 100; MOCK.gain(25); assert(A.db.xp == 25)""")

    def test_invalid_temporary_decrease_does_not_create_fake_level_up(self):
        self.check("""MOCK.start(); MOCK.xp = 90; MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 0); MOCK.xp = 110; MOCK.event('PLAYER_XP_UPDATE', 'player')
        assert(A.db.xp == 10)""")

    def test_commands_and_title_tooltip(self):
        self.check("""MOCK.start(); A.Command('  RESET  '); assert(#MOCK.messages == 1)
        A.Command('help'); assert(#MOCK.messages == 3)
        A.UI.anchor:GetScript('OnEnter')(A.UI.anchor)
        assert(GameTooltip.text == 'ElmoLeveling' and GameTooltip:IsShown())
        A.UI.anchor:GetScript('OnLeave')(); assert(not GameTooltip:IsShown())""")

    def test_number_and_long_time_format(self):
        self.check("""assert(A.UI.Number(1234567) == '1,234,567')
        assert(A.UI.Number(999.7) == '1,000' and A.UI.Number(0) == '0')
        assert(A.UI.Time(3661) == '01:01:01' and A.UI.Time(360000) == '100:00:00')""")

    def test_wrong_addon_load_is_ignored(self):
        self.check("""MOCK.event('ADDON_LOADED', 'OtherAddon'); assert(A.db == nil)
        MOCK.start(); MOCK.event('ADDON_LOADED', 'ElmoLeveling'); assert(A.db.xp == 0)""")

    def test_recent_windows_do_not_extrapolate_during_startup(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.gain(100)
        local xp, seconds, avgMinute, avgHour, minute, hour = A.Stats()
        assert(xp == 100 and seconds == 10 and minute == 100 and hour == 100)
        assert(avgMinute == 600 and avgHour == 36000)
        A.UI.Update(true) -- Rate math/formatting, independent of the refresh schedule.
        assert(A.UI.minute:GetText() == '100' and A.UI.hour:GetText() == '100')
        assert(A.UI.averageMinute:GetText() == '600' and A.UI.averageHour:GetText() == '36,000')""")

    def test_award_expires_at_exactly_sixty_seconds(self):
        self.check("""MOCK.start(); MOCK.gain(100); MOCK.advance(59.5)
        local minute, hour = A.RollingXP(); assert(minute == 100 and hour == 100)
        MOCK.advance(.5); minute, hour = A.RollingXP()
        assert(minute == 0 and hour == 100)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '100')""")

    def test_award_expires_at_exactly_one_hour(self):
        self.check("""MOCK.start(); MOCK.gain(100); MOCK.advance(3599.5)
        local minute, hour = A.RollingXP(); assert(minute == 0 and hour == 100)
        MOCK.advance(.5); minute, hour = A.RollingXP()
        assert(minute == 0 and hour == 0 and #A.db.history == 0)
        assert(A.UI.hour:GetText() == '0' and A.UI.averageHour:GetText() == '100')""")

    def test_each_award_ages_out_independently(self):
        self.check("""MOCK.maximum = 10000; MOCK.start(); MOCK.gain(100)
        MOCK.advance(30); MOCK.gain(200); MOCK.advance(30); MOCK.gain(50)
        local minute, hour = A.RollingXP(); assert(minute == 250 and hour == 350)
        MOCK.advance(30); minute, hour = A.RollingXP(); assert(minute == 50 and hour == 350)
        MOCK.advance(3510); minute, hour = A.RollingXP(); assert(minute == 0 and hour == 250)
        MOCK.advance(30); minute, hour = A.RollingXP(); assert(minute == 0 and hour == 50)
        MOCK.advance(30); minute, hour = A.RollingXP(); assert(minute == 0 and hour == 0)
        assert(A.db.xp == 350 and select(4, A.Stats()) > 0)""")

    def test_rolling_windows_refresh_without_new_xp_even_when_hidden(self):
        self.check("""MOCK.start(); MOCK.gain(50); A.Command('hide'); MOCK.advance(60)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '50')
        MOCK.advance(3540); A.Command('show')
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '0')
        assert(A.UI.averageHour:GetText() == '50' and A.UI.panel:IsShown())""")

    def test_level_up_award_enters_both_windows_once(self):
        self.check("""MOCK.xp = 380; MOCK.start(); MOCK.advance(10)
        MOCK.event('PLAYER_LEVEL_UP', 2)
        MOCK.level, MOCK.xp, MOCK.maximum = 2, 50, 900
        MOCK.event('PLAYER_XP_UPDATE', 'player'); MOCK.event('PLAYER_XP_UPDATE', 'player')
        MOCK.advance(1)
        local minute, hour = A.RollingXP(); assert(minute == 70 and hour == 70)
        assert(#A.db.history == 1 and A.db.xp == 70)
        MOCK.advance(59); assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '70')""")

    def test_reset_clears_recent_windows_and_session_averages(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.gain(100)
        A.UI.reset:GetScript('OnClick')(); local minute, hour = A.RollingXP()
        assert(minute == 0 and hour == 0 and #A.db.history == 0 and A.db.xp == 0)
        assert(A.UI.averageMinute:GetText() == '0' and A.UI.averageHour:GetText() == '0')
        MOCK.advance(10); MOCK.gain(25); minute, hour = A.RollingXP()
        assert(minute == 25 and hour == 25 and select(3, A.Stats()) == 150)""")

    def test_version_one_migration_keeps_totals_without_backfilling_windows(self):
        self.check("""ElmoLevelingDB = {xp = 3600, seconds = 7200}
        MOCK.start(); local minute, hour = A.RollingXP(); assert(minute == 0 and hour == 0)
        assert(A.db.xp == 3600 and A.Elapsed() == 7200)
        assert(A.UI.averageMinute:GetText() == '30' and A.UI.averageHour:GetText() == '1,800')
        MOCK.gain(50); minute, hour = A.RollingXP(); assert(minute == 50 and hour == 50)
        assert(A.db.xp == 3650)""")

    def test_recent_history_survives_reload(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.gain(120)
        MOCK.advance(10); MOCK.event('PLAYER_LOGOUT')""")
        db = self.vm.globals().ElmoLevelingDB
        xp, seconds = db.xp, db.seconds
        history = ",".join(f"{{at={award.at},xp={award.xp}}}" for _, award in db.history.items())
        self.setUp()
        self.check(f"""ElmoLevelingDB = {{xp={xp},seconds={seconds},history={{{history}}}}}
        MOCK.time = 999999; MOCK.start(false, true)
        local minute, hour = A.RollingXP(); assert(minute == 120 and hour == 120)
        MOCK.advance(50); minute, hour = A.RollingXP(); assert(minute == 0 and hour == 120)
        assert(A.db.xp == 120 and A.Elapsed() == 70)""")

    def test_relogin_clears_recent_windows_without_resetting_saved_totals(self):
        self.check("""MOCK.start(); MOCK.gain(100); MOCK.advance(10); MOCK.event('PLAYER_LOGOUT')
        MOCK.advance(86400); assert(A.Elapsed() == 10)
        MOCK.event('PLAYER_ENTERING_WORLD', true, false)
        local minute, hour = A.RollingXP(); assert(minute == 0 and hour == 0)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '0')
        assert(A.db.xp == 100 and A.Elapsed() == 10)
        MOCK.gain(50); minute, hour = A.RollingXP(); assert(minute == 50 and hour == 50)
        assert(A.db.xp == 150)""")

    def test_cold_login_clears_saved_recent_awards_and_keeps_session_and_preferences(self):
        self.check("""ElmoLevelingDB = {xp=300,seconds=100,combatSeconds=20,
            history={{at=99,xp=75}},locked=true,bagBaseline=12345}
        MOCK.start(); local minute, hour = A.RollingXP()
        assert(minute == 0 and hour == 0 and #A.db.history == 0)
        assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '0')
        assert(A.db.xp == 300 and A.Elapsed() == 100 and A.CombatElapsed() == 20)
        assert(A.db.locked and A.db.bagBaseline == 12345)""")

    def test_zone_transition_preserves_recent_windows(self):
        self.check("""MOCK.start(); MOCK.advance(5); MOCK.gain(75)
        MOCK.event('PLAYER_ENTERING_WORLD', false, false)
        local minute, hour = A.RollingXP(); assert(minute == 75 and hour == 75)
        assert(A.db.xp == 75)""")

    def test_old_and_invalid_saved_awards_are_discarded_and_valid_awards_sorted(self):
        self.check("""ElmoLevelingDB = {xp=300,seconds=4000,history={
            {at=3990,xp=100},{at=0,xp=500},{at=4001,xp=50},{at=3999,xp=-1},
            {at=3998,xp='20'},{at=0/0,xp=10},{at=3999,xp=math.huge},
            {at=3999,xp=1.5},false,{at=500,xp=200}}}
        MOCK.start(false, true); local minute, hour = A.RollingXP()
        assert(minute == 100 and hour == 300 and #A.db.history == 2)
        assert(A.db.history[1].at == 500 and A.db.history[2].at == 3990)
        MOCK.advance(100); minute, hour = A.RollingXP(); assert(minute == 0 and hour == 100)""")

    def test_awards_at_same_timestamp_are_combined(self):
        self.check("""MOCK.maximum = 10000; MOCK.start()
        MOCK.gain(100); MOCK.gain(50); MOCK.gain(25)
        local minute, hour = A.RollingXP(); assert(minute == 175 and hour == 175)
        assert(#A.db.history == 1 and A.db.history[1].xp == 175)""")

    def test_history_remains_dense_and_bounded_over_long_sessions(self):
        self.check("""MOCK.maximum = 10000; MOCK.start()
        for i = 1, 200 do MOCK.advance(30); MOCK.gain(1) end
        local minute, hour = A.RollingXP(); assert(minute == 2 and hour == 120)
        assert(#A.db.history == 120 and A.db.history[1].at == 2430 and A.db.xp == 200)
        MOCK.advance(3600); assert(#A.db.history == 0)
        MOCK.gain(10); minute, hour = A.RollingXP()
        assert(#A.db.history == 1 and minute == 10 and hour == 10 and A.db.xp == 210)""")

    def test_expired_awards_stay_expired_after_save_and_restart(self):
        self.check("""MOCK.start(); MOCK.gain(100); MOCK.advance(3600); MOCK.event('PLAYER_LOGOUT')
        assert(#A.db.history == 0); MOCK.event('PLAYER_ENTERING_WORLD', true, false)
        local minute, hour = A.RollingXP(); assert(minute == 0 and hour == 0 and A.db.xp == 100)""")

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
        assert(A.Bags.Change() == 0 and A.db.bagBaseline == 20 and A.db.xp == 0 and A.Elapsed() == 0)
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

    def test_first_login_imports_latest_legacy_saved_xp_and_preferences(self):
        self.check("""MOCK.legacyDB = {xp=120,seconds=20,history={{at=10,xp=120}},
            locked=true,hidden=true,position={x=54,y=-270}}
        MOCK.start(); assert(A.migratedLegacy and #MOCK.loadedAddons == 1)
        assert(MOCK.loadedAddons[1] == 'ClassicXPTracker' and ElmoLevelingDB == A.db)
        assert(A.db.xp == 120 and A.Elapsed() == 20 and A.db.locked and A.db.hidden)
        assert(A.db.position.x == 54 and A.db.position.y == -270)
        local minute,hour = A.RollingXP(); assert(minute == 0 and hour == 0)
        assert(ElmoLevelingPanel ~= nil and ClassicXPTrackerPanel == nil)""")

    def test_existing_classicleveling_profile_takes_precedence_over_legacy_data(self):
        self.check("""ElmoLevelingDB = {xp=25,seconds=50}; MOCK.legacyDB = {xp=1000,seconds=100}
        MOCK.start(); assert(A.db.xp == 25 and A.Elapsed() == 50 and #MOCK.loadedAddons == 0)
        assert(not A.migratedLegacy)""")

    def test_already_loaded_legacy_saved_variables_do_not_load_another_addon(self):
        self.check("""ClassicXPTrackerDB = {xp=75,seconds=30}; MOCK.start()
        assert(A.db.xp == 75 and A.Elapsed() == 30 and #MOCK.loadedAddons == 0 and A.migratedLegacy)""")

    def test_missing_or_failed_legacy_loader_does_not_block_fresh_install(self):
        self.check("""MOCK.legacyError = true; MOCK.start()
        assert(A.db.xp == 0 and A.Elapsed() == 0 and not A.migratedLegacy)
        assert(A.UI.panel:IsShown() and A.Bags.state.value == 0)""")

    def test_legacy_loadaddon_fallback_can_import_old_saved_variables(self):
        self.check("""LoadAddOn = C_AddOns.LoadAddOn; C_AddOns = nil
        MOCK.legacyDB = {xp=90,seconds=30}; MOCK.start()
        assert(A.db.xp == 90 and A.migratedLegacy and #MOCK.loadedAddons == 1)""")

    def test_legacy_helper_is_data_only_and_declares_the_old_character_variable(self):
        legacy = Path(__file__).resolve().parents[3] / "scripts/fixtures/ClassicXPTracker"
        toc = (legacy / "ClassicXPTracker.toc").read_text()
        self.assertIn("## LoadOnDemand: 1", toc)
        self.assertIn("## SavedVariablesPerCharacter: ClassicXPTrackerDB", toc)
        self.assertEqual([s for s in toc.splitlines() if s.endswith(".lua")], ["Legacy.lua"])
        self.check("BEFORE_LEGACY_FRAMES = #MOCK.frames")
        self.vm.execute((legacy / "Legacy.lua").read_text())
        self.check("assert(#MOCK.frames == BEFORE_LEGACY_FRAMES and ClassicXPTrackerPanel == nil)")

    def test_renamed_addon_declares_its_own_character_variable_and_one_panel(self):
        toc = (ADDON / "ElmoLeveling.toc").read_text()
        self.assertIn("## Title: ElmoLeveling", toc)
        self.assertIn("## SavedVariablesPerCharacter: ElmoLevelingDB", toc)
        self.check("""MOCK.start(); local panels = 0
        for _, frame in ipairs(MOCK.frames) do
            if frame.name == 'ElmoLevelingPanel' then panels = panels + 1 end
            assert(frame.name ~= 'ClassicXPTrackerPanel')
        end
        assert(panels == 1 and A.version == '1.6.3' and A.UI.panel.height == 195 and A.UI.panel.width == 332)""")

    def test_mob_kill_records_actual_xp_levels_and_one_kill(self):
        self.check("""MOCK.level = 20; MOCK.mob('target','Boar',19); MOCK.start()
        MOCK.death('target'); assert(#A.db.kills == 1 and A.db.kills[1].xp == nil)
        MOCK.chat('Boar',75); local kill = A.db.kills[1]
        assert(kill.name == 'Boar' and kill.mobLevel == 19 and kill.playerLevel == 20 and kill.xp == 75)
        assert(A.Mobs.Rate() == 1 and A.UI.mobToggle.label:GetText() == 'Kills/min: 1 [+]')
        assert(A.UI.mobRows[1].xp:GetText() == '75@20')""")

    def test_kill_that_levels_up_keeps_player_level_before_award(self):
        self.check("""MOCK.level = 20; MOCK.mob('target','Boar',20); MOCK.start(); MOCK.death('target')
        MOCK.level = 21; MOCK.event('PLAYER_LEVEL_UP',21); MOCK.chat('Boar',100)
        assert(A.db.kills[1].playerLevel == 20 and A.db.kills[1].xp == 100)""")

    def test_xp_before_death_and_level_up_still_keeps_earlier_character_level(self):
        self.check("""MOCK.level=20; MOCK.start(); MOCK.chat('Boar',100)
        MOCK.level=21; MOCK.event('PLAYER_LEVEL_UP',21); MOCK.mob('target','Boar',20); MOCK.death('target')
        assert(#A.db.kills == 1 and A.db.kills[1].playerLevel == 20)""")

    def test_quest_and_exploration_messages_do_not_create_mob_kills(self):
        self.check("""COMBATLOG_XPGAIN_QUEST = 'Quest: %s, %d experience.'; MOCK.start()
        MOCK.chatText('You gain 250 experience.'); MOCK.chatText('Quest: Boar, 250 experience.')
        MOCK.chatText('New zone: 120 experience'); MOCK.advance(3)
        assert(#A.db.kills == 0 and A.Mobs.Rate() == 0)""")

    def test_mob_names_with_numbers_and_punctuation_are_parsed_correctly(self):
        self.check("""MOCK.start(); local name,xp = A.Mobs.Parse('Robo-Spy 3000 (Elite) dies, you gain 120 experience.')
        assert(name == 'Robo-Spy 3000 (Elite)' and xp == 120)""")

    def test_rest_and_group_bonus_messages_use_the_total_once(self):
        self.check("""MOCK.start()
        local name,xp = A.Mobs.Parse('Boar dies, you gain 120 experience. (+60 exp Rested bonus)')
        assert(name == 'Boar' and xp == 120)
        name,xp = A.Mobs.Parse('Boar dies, you gain 80 experience. (+10 group bonus)')
        assert(name == 'Boar' and xp == 80)""")

    def test_localized_and_positional_templates_work(self):
        self.check("""COMBATLOG_XPGAIN_FIRSTPERSON = '%2$d points pour %1$s.'; MOCK.start()
        local name,xp = A.Mobs.Parse('1,234 points pour Mr. Smite.')
        assert(name == 'Mr. Smite' and xp == 1234)""")

    def test_pattern_literals_and_color_codes_are_handled(self):
        self.check("""COMBATLOG_XPGAIN_FIRSTPERSON = '[%s] meurt: +%d XP (100%%).'; MOCK.start()
        local name,xp = A.Mobs.Parse('|cffffd100[Boar 7]|r meurt: +42 XP (100%).')
        assert(name == 'Boar 7' and xp == 42)""")

    def test_unknown_and_skull_mob_levels_are_displayed_as_unknown(self):
        self.check("""MOCK.level=10; MOCK.mob('target','Skull Mob',-1); MOCK.start()
        MOCK.death('target'); MOCK.chat('Skull Mob',100)
        assert(A.db.kills[1].mobLevel == nil and A.db.kills[1].playerLevel == 10)
        A.UI.ToggleMobs(); assert(A.UI.mobRows[1].mobLevel:GetText() == '?')""")

    def test_nameplate_level_is_retained_after_nameplate_disappears(self):
        self.check("""local mob=MOCK.mob('nameplate1','Boar',12); MOCK.start()
        MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate1'); MOCK.event('NAME_PLATE_UNIT_REMOVED','nameplate1')
        MOCK.units.nameplate1=nil
        MOCK.combat={MOCK.time,'PARTY_KILL',false,'Player-Test','HunterTest',1,0,mob.guid,mob.name,0,0}
        MOCK.event('COMBAT_LOG_EVENT_UNFILTERED'); MOCK.chat('Boar',55)
        assert(A.db.kills[1].mobLevel == 12)""")

    def test_mouseover_and_party_target_levels_can_be_observed(self):
        self.check("""local a=MOCK.mob('mouseover','Boar',12); local b=MOCK.mob('party1target','Wolf',13)
        MOCK.start(); MOCK.event('UPDATE_MOUSEOVER_UNIT'); MOCK.event('UNIT_TARGET','party1')
        assert(A.Mobs.units[a.guid].mobLevel == 12 and A.Mobs.units[b.guid].mobLevel == 13)""")

    def test_party_kill_unit_died_and_chat_are_one_kill(self):
        self.check("""local mob=MOCK.mob('target','Boar',5); MOCK.start()
        MOCK.death('target'); MOCK.death('target','UNIT_DIED'); MOCK.chat('Boar',30,42,mob.guid)
        MOCK.death('target'); MOCK.chat('Boar',30,42,mob.guid)
        assert(#A.db.kills == 1 and A.Mobs.Rate() == 1 and A.db.kills[1].xp == 30)""")

    def test_same_name_kills_are_matched_in_order(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',10); MOCK.death('target')
        MOCK.mob('target','Boar',11); MOCK.death('target')
        MOCK.chat('Boar',100); MOCK.chat('Boar',110)
        assert(#A.db.kills == 2 and A.Mobs.Rate() == 2)
        assert(A.db.kills[1].mobLevel == 11 and A.db.kills[1].xp == 110)
        assert(A.db.kills[2].mobLevel == 10 and A.db.kills[2].xp == 100)""")

    def test_xp_messages_before_combat_events_are_matched_in_order(self):
        self.check("""MOCK.start(); MOCK.chat('Boar',100); MOCK.chat('Boar',110)
        MOCK.mob('target','Boar',10); MOCK.death('target'); MOCK.mob('target','Boar',11); MOCK.death('target')
        assert(#A.db.kills == 2 and A.db.kills[2].xp == 100 and A.db.kills[1].xp == 110)
        assert(A.Mobs.Rate() == 2)""")

    def test_exact_guid_takes_precedence_over_same_name(self):
        self.check("""MOCK.start(); local a=MOCK.mob('target','Boar',10); MOCK.death('target')
        local b=MOCK.mob('target','Boar',11); MOCK.death('target')
        MOCK.chat('Boar',110,nil,b.guid); MOCK.chat('Boar',100,nil,a.guid)
        assert(A.db.kills[1].xp == 110 and A.db.kills[2].xp == 100)""")

    def test_known_guid_waits_for_matching_kill_instead_of_other_same_name(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',10); MOCK.death('target')
        MOCK.chat('Boar',110,nil,'Creature-special')
        assert(A.db.kills[1].xp == nil and #A.Mobs.pending == 1)
        MOCK.mob('target','Boar',11,'Creature-special'); MOCK.death('target')
        assert(A.db.kills[1].xp == 110 and A.db.kills[2].xp == nil)""")

    def test_xp_only_fallback_records_unobserved_level_as_unknown(self):
        self.check("""MOCK.level=20; MOCK.start(); MOCK.chat('Distant Mob',40); MOCK.advance(2)
        assert(#A.db.kills == 1 and A.db.kills[1].name == 'Distant Mob' and A.db.kills[1].mobLevel == nil)
        assert(A.db.kills[1].xp == 40 and A.db.kills[1].playerLevel == 20 and A.Mobs.Rate() == 1)""")

    def test_late_combat_event_adopts_xp_only_fallback_without_duplicate(self):
        self.check("""MOCK.start(); MOCK.chat('Boar',40); MOCK.advance(2)
        MOCK.mob('target','Boar',10); MOCK.death('target')
        assert(#A.db.kills == 1 and A.Mobs.Rate() == 1 and A.db.kills[1].xp == 40)
        assert(A.db.kills[1].mobLevel == 10)""")

    def test_late_xp_only_fallback_keeps_history_ordered_by_kill_time(self):
        self.check("""MOCK.start(); MOCK.chat('Distant Mob',30); MOCK.advance(1)
        MOCK.mob('target','Newer Mob',10); MOCK.death('target'); MOCK.chat('Newer Mob',50)
        MOCK.advance(1); assert(#A.db.kills == 2 and A.Mobs.Rate() == 2)
        assert(A.db.kills[1].name == 'Newer Mob' and A.db.kills[2].name == 'Distant Mob')""")

    def test_zero_xp_credited_kill_counts_toward_kills_per_minute(self):
        self.check("""MOCK.level=20; MOCK.mob('target','Grey Mob',2); MOCK.start(); MOCK.death('target')
        MOCK.advance(2); assert(#A.db.kills == 1 and A.db.kills[1].xp == 0 and A.Mobs.Rate() == 1)""")

    def test_old_zero_xp_kill_does_not_steal_new_xp_message(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.advance(3)
        MOCK.mob('target','Boar',10); MOCK.death('target'); MOCK.chat('Boar',100)
        assert(A.db.kills[1].xp == 100 and A.db.kills[2].xp == 0)""")

    def test_pet_and_group_kills_are_credited_but_outsiders_are_not(self):
        self.check("""MOCK.mob('pet','Pet',20,'Pet-Hunter'); MOCK.start()
        MOCK.mob('target','Boar',10); MOCK.death('target','PARTY_KILL',0,'Pet-Hunter')
        MOCK.mob('target','Wolf',10); MOCK.death('target','PARTY_KILL',2,'Player-Party')
        MOCK.mob('target','Bear',10); MOCK.death('target','PARTY_KILL',8,'Player-Outsider')
        MOCK.advance(2); assert(#A.db.kills == 2 and A.Mobs.Rate() == 2)""")

    def test_unrelated_unit_deaths_and_player_deaths_do_not_count(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',10); MOCK.death('target','UNIT_DIED',8,'Player-Other')
        MOCK.mob('target','Other Player',20,'Player-Other'); MOCK.death('target')
        MOCK.advance(3); assert(#A.db.kills == 0 and A.Mobs.Rate() == 0)""")

    def test_combat_records_do_not_double_add_to_xp_counters(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.chat('Boar',50)
        assert(A.db.xp == 0); MOCK.gain(50); assert(A.db.xp == 50 and A.db.kills[1].xp == 50)""")

    def test_kill_rate_is_fixed_sixty_second_window_and_expires_without_kills(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.chat('Boar',10)
        assert(A.Mobs.Rate() == 1)
        MOCK.advance(30); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.chat('Boar',10)
        assert(A.Mobs.Rate() == 2); MOCK.advance(30); assert(A.Mobs.Rate() == 1)
        MOCK.advance(30); assert(A.Mobs.Rate() == 0)
        assert(A.UI.mobToggle.label:GetText() == 'Kills/min: 0 [+]' and #A.db.kills == 2)""")

    def test_history_cap_does_not_limit_frequency_count(self):
        self.check("""MOCK.start()
        for i=1,205 do MOCK.mob('target','Boar '..i,1); MOCK.death('target'); MOCK.chat('Boar '..i,10) end
        assert(#A.db.kills == 100 and A.Mobs.Rate() == 205)
        assert(A.db.kills[1].name == 'Boar 205' and A.db.kills[100].name == 'Boar 106')""")

    def test_expand_collapse_and_scroll_preserve_compact_main_panel(self):
        self.check("""MOCK.start(); assert(not A.UI.mobPanel:IsShown() and A.UI.panel.height == 195)
        for i=1,12 do MOCK.mob('target','Boar '..i,i); MOCK.death('target'); MOCK.chat('Boar '..i,i*10) end
        A.UI.mobToggle:GetScript('OnClick')()
        assert(A.db.mobExpanded and A.UI.mobPanel:IsShown() and A.UI.panel.height == 400)
        assert(A.UI.mobRows[1].nameText:GetText() == 'Boar 12' and A.UI.mobRows[1].xp:GetText() == '120@1')
        A.UI.mobPanel:GetScript('OnMouseWheel')(A.UI.mobPanel,-1)
        assert(A.UI.mobOffset == 3 and A.UI.mobRows[1].nameText:GetText() == 'Boar 9')
        A.UI.mobDown:GetScript('OnClick')(); assert(A.UI.mobOffset == 4)
        A.UI.mobUp:GetScript('OnClick')(); assert(A.UI.mobOffset == 0)
        A.UI.mobToggle:GetScript('OnClick')(); assert(not A.db.mobExpanded and A.UI.panel.height == 195)""")

    def test_header_drag_region_leaves_the_mob_toggle_clear(self):
        self.check("""MOCK.start()
        local ax,ay,ar = MOCK.headerBounds(A.UI.anchor)
        local bx,by,br = MOCK.headerBounds(A.UI.mobToggle)
        assert(ar < bx, 'The mouse-enabled title drag frame overlaps the mob toggle')
        assert(A.UI.mobToggle:GetFrameLevel() > A.UI.anchor:GetFrameLevel())""")

    def test_pointer_up_on_mob_button_expands_once_and_right_click_does_not_toggle(self):
        self.check("""MOCK.start(); local b=A.UI.mobToggle
        local x1,y1,x2,y2 = MOCK.headerBounds(b); local x,y=(x1+x2)/2,(y1+y2)/2
        assert(MOCK.headerClick(x,y,'LeftButton',true) == b and not A.db.mobExpanded)
        assert(MOCK.headerClick(x,y,'LeftButton',false) == b and A.db.mobExpanded)
        assert(A.UI.mobPanel:IsShown() and A.UI.panel.height == 400)
        MOCK.headerClick(x,y,'RightButton',false); assert(A.db.mobExpanded)
        MOCK.headerClick(x,y,'LeftButton',false); assert(not A.db.mobExpanded and A.UI.panel.height == 195)
        assert(MOCK.headerClick(20,12,'LeftButton',false) == A.UI.anchor and not A.db.mobExpanded)""")

    def test_expanded_row_tooltip_includes_full_mob_name_xp_and_both_levels(self):
        self.check("""MOCK.level=20; MOCK.start(); MOCK.mob('target','Long mob name for a full tooltip',19)
        MOCK.death('target'); MOCK.chat('Long mob name for a full tooltip',80); A.UI.ToggleMobs()
        local row=A.UI.mobRows[1]; row:GetScript('OnEnter')(row)
        assert(GameTooltip:GetText() == 'Long mob name for a full tooltip')
        assert(GameTooltip.lines[1] == 'Mob level: 19' and GameTooltip.lines[2] == 'XP received: 80')
        assert(GameTooltip.lines[3] == 'Your level at kill: 20')""")

    def test_saved_kill_history_expansion_and_frequency_are_restored(self):
        self.check("""ElmoLevelingDB={seconds=100,mobExpanded=true,
            kills={{name='Boar',mobLevel=10,playerLevel=11,xp=80,at=90}},killTimes={0,40,50,90,101}}
        MOCK.start(); assert(#A.db.kills == 1 and A.Mobs.Rate() == 2)
        assert(A.UI.mobPanel:IsShown() and A.UI.panel.height == 400 and A.UI.mobRows[1].xp:GetText() == '80@11')
        MOCK.advance(10); assert(A.Mobs.Rate() == 1)""")

    def test_reset_clears_kill_log_pending_messages_and_rate(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.chat('Boar',10)
        MOCK.chat('Unmatched',20); A.UI.ToggleMobs(); A.Reset(); MOCK.advance(3)
        assert(#A.db.kills == 0 and #A.Mobs.pending == 0 and A.Mobs.Rate() == 0)
        assert(A.UI.mobEmpty:IsShown() and A.UI.mobOffset == 0)""")

    def test_offline_time_does_not_advance_kill_frequency_window(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target'); MOCK.chat('Boar',10)
        MOCK.advance(10); MOCK.event('PLAYER_LOGOUT'); MOCK.advance(86400)
        assert(A.Mobs.Rate() == 1)
        MOCK.event('PLAYER_ENTERING_WORLD',true,false); MOCK.advance(50); assert(A.Mobs.Rate() == 0)""")

    def test_hidden_panel_keeps_recording_kills_and_rate(self):
        self.check("""MOCK.start(); A.Command('hide'); MOCK.mob('target','Boar',1)
        MOCK.death('target'); MOCK.chat('Boar',10); assert(#A.db.kills == 1 and A.Mobs.Rate() == 1)
        A.Command('show'); assert(A.UI.mobToggle.label:GetText() == 'Kills/min: 1 [+]')""")

    def test_logout_finishes_pending_kill_rows_before_saved_variables_are_written(self):
        self.check("""MOCK.start(); MOCK.mob('target','Grey Mob',1); MOCK.death('target')
        MOCK.chat('Distant Mob',30); MOCK.event('PLAYER_LOGOUT')
        assert(#A.db.kills == 2 and A.db.kills[1].xp == 30 and A.db.kills[2].xp == 0)
        assert(A.db.kills[1].at <= A.db.seconds and A.db.kills[2].at <= A.db.seconds)""")

    def test_legacy_combat_api_fallback_and_missing_combat_data_are_safe(self):
        self.check("""C_CombatLog=nil; MOCK.start(); MOCK.mob('target','Boar',1); MOCK.death('target')
        MOCK.chat('Boar',10); assert(#A.db.kills == 1)
        CombatLogGetCurrentEventInfo=function() error('unavailable') end
        MOCK.event('COMBAT_LOG_EVENT_UNFILTERED'); assert(#A.db.kills == 1)""")

    def test_corrupt_kill_history_and_future_frequency_entries_are_filtered(self):
        self.check("""ElmoLevelingDB={seconds=100,kills={false,
            {name='Bad',playerLevel=0,xp=10,at=90},{name='Bad',playerLevel=10,xp=-1,at=90},
            {name='Good',mobLevel=-1,playerLevel=10,xp=0,at=90}},killTimes={false,-1,0/0,30,40,41,101}}
        MOCK.start(); assert(#A.db.kills == 1 and A.db.kills[1].name == 'Good')
        assert(A.db.kills[1].mobLevel == nil and A.Mobs.Rate() == 1)""")

    def test_kill_time_uses_combat_timestamps_not_xp_message_delay(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',1000); MOCK.advance(2)
        MOCK.death('target',nil,nil,nil,1012.5); MOCK.advance(1); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 12.5)
        assert(A.UI.mobRows[1].killTime:GetText() == '12.5s')
        assert(A.Mobs.Rate() == 1 and A.db.kills[1].xp == 75)""")

    def test_later_attacks_do_not_restart_kill_timer(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',10); MOCK.attack('target','SPELL_DAMAGE',14)
        MOCK.attack('target','RANGE_DAMAGE',18); MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 10)""")

    def test_pet_or_group_first_attack_starts_the_same_timer(self):
        self.check("""MOCK.mob('pet','Pet',8,'Pet-Hunter'); MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',10,0,'Pet-Hunter')
        MOCK.attack('target','RANGE_DAMAGE',12); MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 10)
        MOCK.mob('target','Wolf',8); MOCK.attack('target','SPELL_DAMAGE',30,2,'Player-Party')
        MOCK.attack('target','SWING_DAMAGE',32); MOCK.death('target',nil,nil,nil,35); MOCK.chat('Wolf',50)
        assert(A.db.kills[1].killTime == 5)""")

    def test_unrelated_player_attacks_do_not_start_kill_timer(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',1,8,'Player-Outsider')
        MOCK.attack('target','SWING_DAMAGE',10); MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 10)""")

    def test_missed_first_attack_counts_and_preparatory_casts_do_not(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SPELL_CAST_SUCCESS',1)
        MOCK.attack('target','SWING_MISSED',5,nil,nil,'DODGE')
        MOCK.attack('target','SWING_DAMAGE',8); MOCK.death('target',nil,nil,nil,15); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 10)""")

    def test_ranged_spell_periodic_and_missed_attacks_start_timing(self):
        self.check("""MOCK.start()
        for _,event in ipairs({'RANGE_DAMAGE','RANGE_MISSED','SPELL_DAMAGE','SPELL_MISSED',
            'SPELL_PERIODIC_DAMAGE','SPELL_PERIODIC_MISSED'}) do
            MOCK.mob('target',event,8); MOCK.attack('target',event,10)
            MOCK.death('target',nil,nil,nil,15); MOCK.chat(event,75)
            assert(A.db.kills[1].killTime == 5,event)
        end""")

    def test_each_guid_has_independent_timer_for_same_name_mobs(self):
        self.check("""MOCK.start(); local a=MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',10)
        local b=MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',12)
        MOCK.units.target=a; MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75,nil,a.guid)
        MOCK.units.target=b; MOCK.death('target',nil,nil,nil,25); MOCK.chat('Boar',75,nil,b.guid)
        assert(A.db.kills[1].killTime == 13 and A.db.kills[2].killTime == 10)""")

    def test_true_death_event_updates_provisional_party_kill_time_once(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',10)
        MOCK.death('target','PARTY_KILL',nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 10)
        MOCK.death('target','UNIT_DIED',nil,nil,20.5); assert(A.db.kills[1].killTime == 10.5)
        MOCK.death('target','PARTY_KILL',nil,nil,99); MOCK.death('target','UNIT_DIED',nil,nil,99)
        assert(A.db.kills[1].killTime == 10.5 and #A.db.kills == 1 and A.Mobs.Rate() == 1)""")

    def test_killing_damage_delivered_after_death_can_complete_timing(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == nil)
        MOCK.attack('target','SWING_DAMAGE',10); assert(A.db.kills[1].killTime == 10)
        MOCK.attack('target','SWING_DAMAGE',25); assert(A.db.kills[1].killTime == 10)""")

    def test_one_shot_with_same_timestamp_is_zero_not_unknown(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',20); MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 0 and A.UI.mobRows[1].killTime:GetText() == '0.0s')
        assert(A.UI.mobRows[1].xpPerSecond:GetText() == '--')""")

    def test_unobserved_attack_and_xp_only_rows_have_unknown_duration(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8); MOCK.death('target'); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == nil and A.UI.mobRows[1].killTime:GetText() == '--')
        assert(A.UI.mobRows[1].xpPerSecond:GetText() == '--')
        MOCK.chat('Distant Mob',50); MOCK.advance(2); assert(A.db.kills[1].killTime == nil)""")

    def test_evade_discards_previous_pull_timer(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',1)
        MOCK.attack('target','SWING_MISSED',5,nil,nil,'EVADE')
        MOCK.attack('target','RANGE_DAMAGE',20); MOCK.death('target',nil,nil,nil,25); MOCK.chat('Boar',75)
        assert(A.db.kills[1].killTime == 5)""")

    def test_stale_unfinished_fights_expire_and_full_reset_discards_active_timers(self):
        self.check("""MOCK.start(); local mob=MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',10)
        MOCK.advance(301); assert(A.Mobs.fights[mob.guid] == nil)
        MOCK.attack('target','SWING_DAMAGE',20); A.Reset(); assert(A.Mobs.fights[mob.guid] == nil)
        MOCK.death('target',nil,nil,nil,25); MOCK.chat('Boar',75); assert(A.db.kills[1].killTime == nil)""")

    def test_saved_kill_times_restore_and_invalid_times_stay_unknown(self):
        self.check("""ElmoLevelingDB={seconds=100,mobExpanded=true,kills={
            {name='Boar',mobLevel=8,playerLevel=7,xp=75,at=90,killTime=12.5},
            {name='Wolf',mobLevel=8,playerLevel=7,xp=75,at=89,killTime=0},
            {name='Old',mobLevel=8,playerLevel=7,xp=75,at=88},
            {name='Bad',mobLevel=8,playerLevel=7,xp=75,at=87,killTime=-1}}}
        MOCK.start(); assert(A.db.kills[1].killTime == 12.5 and A.db.kills[2].killTime == 0)
        assert(A.UI.mobRows[1].killTime:GetText() == '12.5s' and A.UI.mobRows[2].killTime:GetText() == '0.0s')
        assert(A.UI.mobRows[1].xpPerSecond:GetText() == '6.0' and A.UI.mobRows[2].xpPerSecond:GetText() == '--')
        assert(A.UI.mobRows[3].killTime:GetText() == '--' and A.db.kills[4].killTime == nil)""")

    def test_clear_button_removes_history_and_preserves_all_other_counters(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.gain(25)
        MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',1)
        MOCK.death('target',nil,nil,nil,5); MOCK.chat('Boar',75); A.UI.ToggleMobs()
        local elapsed,baseline = A.Elapsed(), A.db.bagBaseline
        A.UI.mobClear:GetScript('OnClick')(A.UI.mobClear)
        assert(#A.db.kills == 0 and A.UI.mobEmpty:IsShown() and A.UI.mobOffset == 0)
        assert(A.Mobs.Rate() == 1 and A.db.xp == 25 and A.Elapsed() == elapsed and A.db.bagBaseline == baseline)
        assert(A.db.mobExpanded and A.UI.mobPanel:IsShown() and A.UI.panel.height == 400)""")

    def test_clear_preserves_fight_in_progress_for_future_kill(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',10)
        A.Mobs.ClearHistory(); MOCK.death('target',nil,nil,nil,20); MOCK.chat('Boar',75)
        assert(#A.db.kills == 1 and A.db.kills[1].killTime == 10 and A.Mobs.Rate() == 1)""")

    def test_clear_does_not_restore_removed_row_from_late_guid_events(self):
        self.check("""MOCK.start(); local mob=MOCK.mob('target','Boar',8)
        MOCK.death('target'); A.Mobs.ClearHistory(); MOCK.chat('Boar',75,nil,mob.guid)
        MOCK.death('target','UNIT_DIED'); MOCK.advance(3)
        assert(#A.db.kills == 0 and A.Mobs.Rate() == 1)""")

    def test_clear_discards_pending_history_but_new_same_name_kill_still_records(self):
        self.check("""MOCK.start(); MOCK.chat('Pending Mob',30); A.Mobs.ClearHistory(); MOCK.advance(3)
        assert(#A.db.kills == 0 and #A.Mobs.pending == 0)
        MOCK.mob('target','Boar',8); MOCK.death('target'); MOCK.chat('Boar',75)
        A.Mobs.ClearHistory(); MOCK.chat('Boar',80); MOCK.mob('target','Boar',9); MOCK.death('target')
        assert(#A.db.kills == 1 and A.db.kills[1].xp == 80 and A.db.kills[1].mobLevel == 9)""")

    def test_kill_time_tooltip_and_five_column_row_keep_xp_at_level(self):
        self.check("""MOCK.level=7; MOCK.start(); MOCK.mob('target','Boar',8)
        MOCK.attack('target','SWING_DAMAGE',10); MOCK.death('target',nil,nil,nil,22.5)
        MOCK.chat('Boar',75); A.UI.ToggleMobs(); local row=A.UI.mobRows[1]
        assert(row.nameText:GetText() == 'Boar' and row.mobLevel:GetText() == '8')
        assert(row.xp:GetText() == '75@7' and row.killTime:GetText() == '12.5s')
        assert(row.xpPerSecond:GetText() == '6.0')
        row:GetScript('OnEnter')(row); assert(GameTooltip.lines[4] == 'Kill time: 12.5s')
        assert(GameTooltip.lines[5] == 'XP/s: 6.0')""")

    def test_xp_per_second_updates_from_pending_to_known_and_zero_xp(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',8); MOCK.attack('target','SWING_DAMAGE',10)
        MOCK.death('target',nil,nil,nil,22.5)
        assert(A.UI.mobRows[1].xpPerSecond:GetText() == '--')
        MOCK.chat('Boar',75); assert(A.UI.mobRows[1].xpPerSecond:GetText() == '6.0')
        MOCK.mob('target','Grey Mob',1); MOCK.attack('target','SWING_DAMAGE',30)
        MOCK.death('target',nil,nil,nil,40); MOCK.advance(2)
        assert(A.db.kills[1].xp == 0 and A.UI.mobRows[1].xpPerSecond:GetText() == '0.0')""")

    def test_player_line_uses_real_name_level_and_level_event_before_xp_settles(self):
        self.check("""MOCK.playerName='Osobo'; MOCK.level=5; MOCK.start()
        assert(A.UI.character:GetText() == 'Osobo lv. 5')
        MOCK.event('PLAYER_LEVEL_UP',6); assert(A.UI.character:GetText() == 'Osobo lv. 6')
        MOCK.level=6; MOCK.advance(1); A.Reset()
        assert(A.UI.character:GetText() == 'Osobo lv. 6' and A.UI.panel.height == 195)
        assert(A.UI.character.parent == A.UI.anchor and A.UI.character.width == 145)""")

    def test_old_saved_history_keeps_newest_100_without_changing_counters(self):
        self.check("""ElmoLevelingDB={seconds=200,xp=500,kills={},killTimes={190,195}}
        for i=200,1,-1 do table.insert(ElmoLevelingDB.kills,
            {name='Mob '..i,playerLevel=7,xp=75,at=i,killTime=12.5}) end
        MOCK.start()
        assert(#A.db.kills == 100 and A.db.kills[1].name == 'Mob 200' and A.db.kills[100].name == 'Mob 101')
        assert(A.db.xp == 500 and A.Mobs.Rate() == 2 and A.db.kills[100].killTime == 12.5)
        A.UI.mobClear:GetScript('OnClick')(); assert(A.UI.mobPage:GetText() == '0 / 100')""")

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


    def test_session_idle_only_increases_total(self):
        self.check("""MOCK.start(); MOCK.advance(10)
        assert(A.Elapsed() == 10 and A.CombatElapsed() == 0)
        assert(A.frame.events.PLAYER_REGEN_DISABLED and A.frame.events.PLAYER_REGEN_ENABLED)""")

    def test_session_combines_combat_segments_and_excludes_idle(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.event('PLAYER_REGEN_DISABLED')
        MOCK.advance(20); MOCK.event('PLAYER_REGEN_ENABLED'); MOCK.advance(5)
        MOCK.event('PLAYER_REGEN_DISABLED'); MOCK.advance(7); MOCK.event('PLAYER_REGEN_ENABLED')
        MOCK.advance(3); assert(A.CombatElapsed() == 27 and A.Elapsed() == 45)
        assert(A.db.xp == 0 and A.UI.time:GetText() == 'Combat 0h 0m 27s | Total 0h 0m 45s')""")

    def test_session_duplicate_events_and_zone_changes_do_not_restart_combat(self):
        self.check("""MOCK.start(); MOCK.event('PLAYER_REGEN_DISABLED'); MOCK.advance(5)
        MOCK.event('PLAYER_REGEN_DISABLED'); MOCK.event('PLAYER_ENTERING_WORLD',false,false)
        MOCK.advance(5); MOCK.event('PLAYER_REGEN_ENABLED'); MOCK.event('PLAYER_REGEN_ENABLED')
        MOCK.advance(3); assert(A.CombatElapsed() == 10 and A.Elapsed() == 13)""")

    def test_session_login_during_combat_starts_from_login(self):
        self.check("""MOCK.combat=true; MOCK.start(); MOCK.advance(5)
        assert(A.CombatElapsed() == 5 and A.Elapsed() == 5)""")

    def test_session_logout_saves_combat_and_excludes_offline_time(self):
        self.check("""MOCK.combat=true; MOCK.start(); MOCK.advance(20)
        MOCK.event('PLAYER_LOGOUT'); A.Save()
        assert(A.db.combatSeconds == 20 and A.db.seconds == 20 and A.combatStartedAt == nil)
        MOCK.advance(86400); assert(A.CombatElapsed() == 20 and A.Elapsed() == 20)
        MOCK.event('PLAYER_ENTERING_WORLD',true,false); MOCK.advance(10)
        assert(A.CombatElapsed() == 30 and A.Elapsed() == 30)""")

    def test_session_reset_during_combat_restarts_both_timers(self):
        self.check("""MOCK.combat=true; MOCK.start(); MOCK.advance(20); MOCK.gain(50)
        A.Reset(); assert(A.CombatElapsed() == 0 and A.Elapsed() == 0 and A.db.xp == 0)
        MOCK.advance(5); assert(A.CombatElapsed() == 5 and A.Elapsed() == 5)
        MOCK.event('PLAYER_REGEN_ENABLED'); MOCK.advance(5)
        assert(A.CombatElapsed() == 5 and A.Elapsed() == 10)""")

    def test_session_older_profile_keeps_total_and_starts_combat_at_zero(self):
        self.check("""ElmoLevelingDB={xp=100,seconds=300}; MOCK.start()
        assert(A.Elapsed() == 300 and A.CombatElapsed() == 0 and A.db.xp == 100)""")

    def test_session_saved_combat_cannot_exceed_total(self):
        self.check("""ElmoLevelingDB={seconds=60,combatSeconds=999}; MOCK.start()
        assert(A.CombatElapsed() == 60 and A.db.combatSeconds == 60)""")

    def test_session_hiding_and_clearing_mob_history_preserve_timers(self):
        self.check("""MOCK.start(); MOCK.advance(10); MOCK.event('PLAYER_REGEN_DISABLED')
        A.Command('hide'); MOCK.advance(20); A.Mobs.ClearHistory(); MOCK.advance(5)
        A.Command('show'); assert(A.Elapsed() == 35 and A.CombatElapsed() == 25)
        assert(A.UI.panel:IsShown() and A.UI.time:GetText() == 'Combat 0h 0m 25s | Total 0h 0m 35s')""")

    def test_session_display_and_single_bag_sell_value(self):
        self.check("""ElmoLevelingDB={seconds=8410,combatSeconds=1815}
        MOCK.item(10,230); MOCK.put(0,1,10,1); MOCK.start()
        assert(A.UI.time:GetText() == 'Combat 0h 30m 15s | Total 2h 20m 10s')
        assert(A.UI.bagLabel:GetText() == 'Bags (sell value):' and A.UI.bagChange == nil)
        assert(MOCK.plain(A.UI.bagValue:GetText()) == '0g 2s 30c')
        for _,frame in ipairs(MOCK.frames) do
            assert(frame.text ~= 'Bag change' and frame.text ~= 'Bags (vendor)')
        end""")



    def test_respawn_average_groups_name_across_levels_and_individual_mobs(self):
        self.check("""MOCK.start(); local first=MOCK.mob('target','Boar',2); first.dead=true
        MOCK.chat('Boar',50); MOCK.advance(2); MOCK.advance(18)
        MOCK.mob('target','Boar',20); MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 20 and n == 1)
        MOCK.units.target.dead=true; MOCK.chat('Boar',50); MOCK.advance(2); MOCK.advance(28)
        MOCK.mob('mouseover','Boar',40); MOCK.event('UPDATE_MOUSEOVER_UNIT'); MOCK.advance(5)
        avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 25 and n == 2)
        A.UI.ToggleMobs(); assert(A.UI.mobRows[1].respawn:GetText() == '25s')
        assert(A.UI.mobRows[2].respawn:GetText() == '25s')
        assert(A.UI.panel.width == 408); A.UI.ToggleMobs(); assert(A.UI.panel.width == 332)""")

    def test_respawn_mean_is_published_on_five_second_boundaries(self):
        self.check("""MOCK.start(); local mob=MOCK.mob('target','Boar',2); mob.dead=true
        MOCK.chat('Boar',50); MOCK.advance(2)
        MOCK.mob('target','Boar',8); MOCK.event('PLAYER_TARGET_CHANGED')
        assert(A.Mobs.RespawnAverage('Boar') == nil)
        MOCK.advance(2); assert(A.Mobs.RespawnAverage('Boar') == nil)
        MOCK.advance(1); local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 2 and n == 1)""")

    def test_respawn_repeated_target_mouseover_and_plate_sightings_are_not_new_spawns(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.mob('mouseover','Boar',3).dead=true
        MOCK.chat('Boar',10); MOCK.chat('Boar',10); MOCK.advance(2)
        local fresh=MOCK.mob('target','Boar',8); MOCK.event('PLAYER_TARGET_CHANGED')
        MOCK.units.mouseover=fresh; MOCK.event('UPDATE_MOUSEOVER_UNIT')
        MOCK.units.nameplate1=fresh; MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate1')
        MOCK.advance(10); local avg,n=A.Mobs.RespawnAverage('Boar')
        assert(avg == 2 and n == 1 and #A.Mobs.respawnPending == 1)""")

    def test_respawn_already_observed_living_mob_is_not_a_new_appearance(self):
        self.check("""MOCK.start(); MOCK.mob('mouseover','Boar',9)
        MOCK.mob('target','Boar',2).dead=true; MOCK.chat('Boar',50); MOCK.advance(2)
        MOCK.event('UPDATE_MOUSEOVER_UNIT'); MOCK.advance(5)
        assert(A.Mobs.RespawnAverage('Boar') == nil)
        MOCK.mob('nameplate1','Boar',10); MOCK.event('NAME_PLATE_UNIT_ADDED','nameplate1')
        MOCK.advance(5); local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 7 and n == 1)""")

    def test_respawn_one_appearance_matches_one_pending_kill_in_order(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',10); MOCK.advance(2); MOCK.advance(8)
        MOCK.mob('target','Boar',3).dead=true; MOCK.chat('Boar',10); MOCK.advance(2)
        MOCK.advance(18); MOCK.mob('target','Boar',8); MOCK.event('PLAYER_TARGET_CHANGED')
        MOCK.advance(20); local avg,n=A.Mobs.RespawnAverage('Boar')
        assert(avg == 30 and n == 1 and #A.Mobs.respawnPending == 1)
        MOCK.mob('mouseover','Boar',11); MOCK.event('UPDATE_MOUSEOVER_UNIT'); MOCK.advance(5)
        avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 35 and n == 2)""")

    def test_respawn_dead_sightings_are_excluded_but_dead_to_alive_is_measured(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(2)
        local corpse=MOCK.mob('target','Boar',8); corpse.dead=true
        MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        assert(A.Mobs.RespawnAverage('Boar') == nil)
        corpse.dead=false; MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 7 and n == 1)""")

    def test_respawn_different_names_do_not_match(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(2)
        MOCK.mob('target','Wolf',2); MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        assert(A.Mobs.RespawnAverage('Boar') == nil and A.Mobs.RespawnAverage('Wolf') == nil)
        assert(#A.Mobs.respawnPending == 1)""")

    def test_respawn_zone_change_discards_waiting_samples_but_keeps_measured_averages(self):
        self.check("""ElmoLevelingDB={respawns={{name='Boar',total=60,count=2}}}; MOCK.start()
        MOCK.mob('target','Boar',2).dead=true; MOCK.chat('Boar',50); MOCK.advance(2)
        MOCK.event('ZONE_CHANGED_NEW_AREA'); MOCK.mob('target','Boar',9)
        MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 30 and n == 2)
        assert(#A.Mobs.respawnPending == 0)""")

    def test_respawn_offline_time_does_not_turn_into_an_observed_wait(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(2); MOCK.event('PLAYER_LOGOUT'); MOCK.advance(86400)
        MOCK.mob('target','Boar',20); MOCK.event('PLAYER_ENTERING_WORLD',true,false); MOCK.advance(5)
        assert(A.Mobs.RespawnAverage('Boar') == nil and #A.Mobs.respawnPending == 0)""")

    def test_respawn_logout_saves_a_collected_sample_before_next_refresh(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(2)
        MOCK.mob('target','Boar',8); MOCK.event('PLAYER_TARGET_CHANGED')
        assert(A.Mobs.RespawnAverage('Boar') == nil); MOCK.event('PLAYER_LOGOUT')
        assert(A.db.respawns[1].total == 2 and A.db.respawns[1].count == 1)""")

    def test_respawn_saved_averages_reject_invalid_and_duplicate_records(self):
        self.check("""ElmoLevelingDB={respawns={false,{name='Boar',total=40,count=2},
            {name='Boar',total=999,count=1},{name='',total=10,count=1},
            {name='Wolf',total=-1,count=1},{name='Bear',total=2,count=0},
            {name='Tiger',total=2,count=.5}}}; MOCK.start()
        local avg,n=A.Mobs.RespawnAverage('Boar'); assert(avg == 20 and n == 2 and #A.db.respawns == 1)""")

    def test_respawn_history_and_runtime_caches_are_bounded(self):
        self.check("""ElmoLevelingDB={respawns={}}; for i=1,120 do
            table.insert(ElmoLevelingDB.respawns,{name='Mob '..i,total=i,count=1}) end
        MOCK.start(); assert(#A.db.respawns == 100 and A.Mobs.RespawnAverage('Mob 101') == nil)
        for i=1,110 do MOCK.chat('Boar',10) end; MOCK.advance(2)
        assert(#A.Mobs.respawnPending == 100 and #A.db.kills == 100)
        for i=1,1001 do MOCK.mob('target','Wolf',i%20+1); MOCK.event('PLAYER_TARGET_CHANGED') end
        assert(#A.Mobs.respawnOrder == 1000)""")

    def test_respawn_clear_keeps_averages_but_reset_clears_them(self):
        self.check("""ElmoLevelingDB={respawns={{name='Boar',total=30,count=1}}}; MOCK.start()
        A.Mobs.ClearHistory(); assert(A.Mobs.RespawnAverage('Boar') == 30)
        A.Reset(); assert(A.Mobs.RespawnAverage('Boar') == nil and #A.db.respawns == 0)
        assert(#A.Mobs.respawnPending == 0 and #A.Mobs.respawnOrder == 0)""")

    def test_xp_minute_display_refreshes_every_five_seconds_while_totals_continue(self):
        self.check("""MOCK.start(); MOCK.advance(1); MOCK.gain(100)
        assert(A.UI.total:GetText() == 'Session XP: 100' and A.UI.hour:GetText() == '100')
        assert(A.UI.minute:GetText() == '0' and A.UI.averageMinute:GetText() == '0')
        MOCK.advance(3); assert(A.UI.minute:GetText() == '0')
        MOCK.advance(1); assert(A.UI.minute:GetText() == '100' and A.UI.averageMinute:GetText() == '1,200')""")

    def test_xp_minute_five_second_refresh_keeps_the_sixty_second_window(self):
        self.check("""MOCK.start(); MOCK.advance(1); MOCK.gain(100); MOCK.advance(4)
        assert(A.UI.minute:GetText() == '100'); MOCK.advance(55); MOCK.advance(1)
        assert(A.RollingXP() == 0 and A.UI.minute:GetText() == '100')
        MOCK.advance(4); assert(A.UI.minute:GetText() == '0' and A.UI.hour:GetText() == '100')""")

    def test_xp_minute_reset_is_immediate_between_refreshes(self):
        self.check("""MOCK.start(); MOCK.advance(1); MOCK.gain(100); MOCK.advance(4)
        assert(A.UI.minute:GetText() == '100'); MOCK.advance(1); A.Reset()
        assert(A.UI.minute:GetText() == '0' and A.UI.averageMinute:GetText() == '0')
        MOCK.advance(1); MOCK.gain(20); MOCK.advance(3); assert(A.UI.minute:GetText() == '0')
        MOCK.advance(1); assert(A.UI.minute:GetText() == '20')""")



    def test_respawn_fast_sighting_before_the_xp_row_settles_is_preserved(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(1)
        MOCK.mob('target','Boar',20); MOCK.event('PLAYER_TARGET_CHANGED')
        MOCK.advance(1); assert(#A.db.kills == 1)
        MOCK.advance(3); local avg,n=A.Mobs.RespawnAverage('Boar')
        assert(avg == 1 and n == 1 and #A.Mobs.respawnPending == 0)""")


    def test_respawn_zone_change_also_excludes_a_kill_still_waiting_for_correlation(self):
        self.check("""MOCK.start(); MOCK.mob('target','Boar',2).dead=true
        MOCK.chat('Boar',50); MOCK.advance(1); MOCK.event('ZONE_CHANGED_NEW_AREA')
        MOCK.advance(1); assert(#A.db.kills == 1 and #A.Mobs.respawnPending == 0)
        MOCK.mob('target','Boar',20); MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(5)
        assert(A.Mobs.RespawnAverage('Boar') == nil)""")


if __name__ == "__main__":
    unittest.main()
