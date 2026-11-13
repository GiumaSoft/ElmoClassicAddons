"""Actual ElmoWaypoint Lua 5.1 with native map, heading and minimap fixtures."""
from pathlib import Path
import os
import unittest
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).parent
ADDON=Path(os.environ.get('ELMO_TEST_ADDON',HERE.resolve().parents[2]/'ElmoWaypoint'))

class WaypointTests(unittest.TestCase):
    legacy=False

    def setUp(self):
        self.vm=LuaRuntime(unpack_returned_tuples=True)
        self.vm.execute((HERE.parent/'ElmoLFM/wow_mock.lua').read_text())
        self.vm.execute((HERE/'wow_mock.lua').read_text())
        if self.legacy:self.vm.execute('MOCK.legacyWaypoint()')
        else:self.vm.execute('WOW_PROJECT_ID=WOW_PROJECT_CAMELOT;C_Minimap={GetViewRadius=function()return MOCK.radius or 233.333333333 end}')
        namespace=self.vm.table()
        load=self.vm.eval('function(source,name,ns)assert(loadstring(source,"@"..name))("ElmoWaypoint",ns)end')
        for name in (ADDON/'ElmoWaypoint.toc').read_text().splitlines():
            if name.endswith('.lua'):load((ADDON/name.replace('\\','/')).read_text(),name,namespace)
        self.vm.globals().A=namespace

    def check(self,source):self.vm.execute(source)

    def test_standalone_start_registers_real_broker_and_native_options(self):
        self.check("""MOCK.start();assert(A.version=='1.2.0' and A.ready and not A.UI.panel:IsShown())
        assert(ElmoWaypointDB==A.db and #A.db.points==0 and not A.db.minimap.hide)
        assert(LibStub('LibDBIcon-1.0'):IsRegistered('ElmoWaypoint'))
        assert(A.Minimap.broker==LibStub('LibDataBroker-1.1'):GetDataObjectByName('ElmoWaypoint'))
        assert(SLASH_ELMOWAYPOINT1=='/way' and SLASH_ELMOWAYPOINT2=='/ewp')
        assert(#MOCK.sent==0 and #MOCK.invited==0 and #MOCK.requests==0)""")

    def test_way_adds_current_player_zone_and_optional_label(self):
        self.check("""MOCK.start();MOCK.runSlash('/way','60 40 Meet here')
        local p=A.Current();assert(p.mapID==1 and p.x==.6 and p.y==.4 and p.title=='Meet here')
        assert(#A.db.points==1 and A.UI.panel:IsShown() and A.UI.target:GetText()=='Meet here')
        assert(A.UI.coordinates:GetText():find('60.00, 40.00',1,true))
        assert(p.mapID~=WorldMapFrame:GetMapID())""")

    def test_decimal_commas_and_coordinate_edges(self):
        self.check("""MOCK.start();MOCK.runSlash('/way','60,25 40,75 Decimal')
        assert(A.Current().x==.6025 and A.Current().y==.4075)
        assert(A.Add('0','100') and A.Current().x==0 and A.Current().y==1)
        assert(A.Add('100','0') and A.Current().x==1 and A.Current().y==0)""")

    def test_invalid_input_and_unknown_player_map_do_not_modify_existing_waypoint(self):
        self.check("""MOCK.start();assert(A.Add(60,40));local current=A.Current()
        for _,pair in ipairs({{-1,50},{101,50},{'nan',50},{50,'inf'},{50,nil},{math.huge,20}})do
            assert(not A.Add(pair[1],pair[2]))
        end
        MOCK.map=nil;assert(not A.Add(20,30));assert(A.Current()==current and #A.db.points==1)
        MOCK.runSlash('/way','bad');assert(A.Current()==current)""")

    def test_duplicate_coordinates_reselect_without_growing_the_list(self):
        self.check("""MOCK.start();A.Add(60,40,'First');A.Add(70,40,'Second');A.Add(60,40,'Updated')
        assert(#A.db.points==2 and A.db.active==1 and A.Current().title=='Updated')
        A.Add(60,40);assert(A.Current().title=='Updated')""")

    def test_multiple_waypoints_next_remove_and_reset_are_local(self):
        self.check("""MOCK.start();A.Add(60,40);A.Add(70,40);assert(A.db.active==2)
        A.Next();assert(A.db.active==1);A.RemoveCurrent()
        assert(#A.db.points==1 and A.Current().x==.7)
        A.Reset();assert(#A.db.points==0 and A.db.active==1 and not A.UI.panel:IsShown())
        A.Next();A.RemoveCurrent();assert(#A.db.points==0)
        assert(#MOCK.sent==0 and #MOCK.requests==0 and #MOCK.invited==0)""")

    def test_actual_map_scale_is_used_for_distance(self):
        self.check("""MOCK.start();A.Add(50,40);assert(math.abs(A.state.distance-200)<.00001)
        A.Add(60,50);assert(math.abs(A.state.distance-100)<.00001)
        A.Add(60,40);assert(math.abs(A.state.distance-math.sqrt(50000))<.00001)""")

    def test_cardinal_directions_and_drawn_line_endpoints(self):
        self.check("""MOCK.start()
        for _,test in ipairs({{50,40,0,0,24},{60,50,-math.pi/2,24,0},
            {50,60,-math.pi,0,-24},{40,50,math.pi/2,-24,0}})do
            A.Add(test[1],test[2]);assert(math.abs(A.state.angle-test[3])<.00001)
            local tip=A.UI.lines[1].front.finish
            assert(math.abs(tip[3]-test[4])<.00001 and math.abs(tip[4]-test[5])<.00001)
        end""")

    def test_arrow_accounts_for_player_heading_and_wraps_at_full_turn(self):
        self.check("""MOCK.start();A.Add(60,50);MOCK.facing=3*math.pi/2;A.Tick()
        assert(math.abs(A.state.angle)<.00001)
        MOCK.facing=math.pi/2;A.Tick();assert(math.abs(math.abs(A.state.angle)-math.pi)<.00001)
        MOCK.facing=2*math.pi;A.Tick();assert(math.abs(A.state.angle+math.pi/2)<.00001)""")

    def test_cross_zone_coordinates_keep_the_destination_map(self):
        self.check("""MOCK.start();MOCK.map=2;A.Add(50,50,'Other zone');MOCK.map=1
        MOCK.fire('ZONE_CHANGED_NEW_AREA')
        assert(A.Current().mapID==2 and math.abs(A.state.distance-2000)<.00001)
        assert(math.abs(A.state.angle+math.pi/2)<.00001)
        MOCK.map=2;MOCK.fire('PLAYER_ENTERING_WORLD');assert(A.state.arrived)""")

    def test_different_continents_pause_direction_and_recover(self):
        self.check("""MOCK.start();A.Add(60,40);MOCK.map=3;A.Tick()
        assert(A.state.status=='Different continent' and not A.UI.arrow:IsShown())
        assert(A.UI.panel:IsShown() and #A.db.points==1)
        MOCK.map=1;A.Tick();assert(A.UI.arrow:IsShown() and A.state.distance)""")

    def test_missing_or_restricted_position_and_facing_are_not_reconstructed(self):
        self.check("""MOCK.start();A.Add(60,40);MOCK.noPosition=true;A.Tick()
        assert(A.state.status=='Position unavailable' and not A.UI.arrow:IsShown())
        MOCK.noPosition=false;MOCK.secretPosition=MOCK.secret();A.Tick();assert(not A.UI.arrow:IsShown())
        MOCK.secretPosition=nil;MOCK.secretWorld=MOCK.secret();A.Tick();assert(not A.UI.arrow:IsShown())
        MOCK.secretWorld=nil;MOCK.facing=MOCK.secret();A.Tick()
        assert(A.state.status=='Facing unavailable' and not A.UI.arrow:IsShown())
        MOCK.facing=0;A.Tick();assert(A.UI.arrow:IsShown())""")

    def test_missing_map_conversion_or_vector_factory_pauses_without_errors(self):
        self.check("""MOCK.start();A.Add(60,40);C_Map.GetWorldPosFromMapPos=nil;A.Tick()
        assert(A.state.status=='Position unavailable')
        CreateVector2D=nil;A.Tick();assert(not A.UI.arrow:IsShown() and #A.db.points==1)
        C_Map=nil;A.Tick();assert(A.state.status=='Position unavailable')""")

    def test_arrival_is_green_and_waypoint_remains_until_removed(self):
        self.check("""MOCK.start();A.Add(50.5,50);assert(A.state.arrived and #A.db.points==1)
        assert(A.UI.lines[1].front.color[2]==1 and A.UI.distance:GetText()=='Arrived · 5 yd')
        MOCK.px=.4;A.Tick();assert(not A.state.arrived and #A.db.points==1)
        assert(A.UI.lines[1].front.color[2]==.82)""")

    def test_hidden_displays_do_not_query_position_and_adding_reopens_arrow(self):
        self.check("""MOCK.start();A.Add(60,40);A.SetVisible(false);A.Coordinates.SetVisible(false);local reads=MOCK.mapReads
        MOCK.advance(10);assert(MOCK.mapReads==reads and not A.UI.panel:IsShown())
        assert(#A.db.points==1);A.Add(70,40);assert(A.UI.panel:IsShown() and #A.db.points==2)""")

    def test_current_command_saves_exact_player_position_note_and_both_pins(self):
        self.check("""MOCK.start();MOCK.px,MOCK.py=.523456789,.417654321
        MOCK.browse(3);MOCK.runSlash('/way','current Meeting place')
        local point=A.Current()
        assert(point.mapID==1 and point.x==MOCK.px and point.y==MOCK.py and point.title=='Meeting place')
        MOCK.browse(1);MOCK.advance(.1)
        assert(A.Pins.records[1].world:IsShown() and A.Pins.records[1].mini:IsShown())
        assert(A.state.arrived);MOCK.runSlash('/way','CURRENT');assert(#A.db.points==1)
        assert(A.Current().title=='Meeting place')""")

    def test_current_position_failure_does_not_reuse_stale_coordinates(self):
        self.check("""MOCK.start();A.Command('current Saved');local saved=A.Current()
        MOCK.noPosition=true;A.Command('current');assert(#A.db.points==1 and A.Current()==saved)
        assert(MOCK.printed:find('No waypoint added',1,true))
        MOCK.noPosition=false;MOCK.secretPosition=MOCK.secret();assert(not A.AddCurrent())
        MOCK.secretPosition=nil;MOCK.px=MOCK.secret();assert(not A.AddCurrent())
        MOCK.px=1.01;assert(not A.AddCurrent());MOCK.px=.5
        MOCK.map=nil;assert(not A.AddCurrent());assert(#A.db.points==1 and A.Current()==saved)""")

    def test_coordinate_display_updates_without_waypoints_and_with_hidden_arrow(self):
        self.check("""MOCK.start();assert(A.Coordinates.panel:IsShown() and #A.db.points==0)
        assert(A.Coordinates.value:GetText()=='50.00, 50.00' and A.Coordinates.zone:GetText()=='Duskwood')
        MOCK.px,MOCK.py=.625,.3875;MOCK.advance(.1)
        assert(A.Coordinates.value:GetText()=='62.50, 38.75')
        A.Command('current');A.Command('hide');MOCK.map=2;MOCK.advance(.1)
        assert(not A.UI.panel:IsShown() and A.Coordinates.panel:IsShown())
        assert(A.Coordinates.zone:GetText()=='Elwynn Forest')
        MOCK.noPosition=true;A.Tick();assert(A.Coordinates.value:GetText()=='--.--, --.--')
        MOCK.noPosition=false;MOCK.secretPosition=MOCK.secret();A.Tick()
        assert(A.Coordinates.zone:GetText()=='Position unavailable')
        MOCK.secretPosition=nil;A.Tick();assert(A.Coordinates.value:GetText()=='62.50, 38.75')""")

    def test_coordinate_frame_has_independent_drag_lock_visibility_and_reset(self):
        self.check("""MOCK.start();A.Command('current');A.Settings.panel:Show()
        local panel=A.Coordinates.panel
        panel.centerX,panel.centerY=360,280;panel.scripts.OnDragStop(panel)
        assert(A.db.coordinatesPosition.x==260 and A.db.coordinatesPosition.y==180 and not A.db.position)
        MOCK.click(A.Settings.panel.coordinatesLocked)
        assert(A.db.coordinatesLocked and not panel.EnableMouseArgs[1] and not A.db.locked)
        A.Command('coords unlock');assert(not A.db.coordinatesLocked and panel.EnableMouseArgs[1])
        MOCK.click(A.Settings.panel.showCoordinates);assert(not panel:IsShown() and A.UI.panel:IsShown())
        A.Command('coords show');assert(panel:IsShown())
        MOCK.click(A.Settings.panel.coordinatesCenter);assert(not A.db.coordinatesPosition and panel.point[1]=='TOP')
        assert(#A.db.points==1)""")

    def test_saved_coordinates_preferences_restore_and_invalid_positions_reset(self):
        self.check("""ElmoWaypointDB={coordinatesPosition={x=260,y=-120},showCoordinates=false,coordinatesLocked=true}
        MOCK.start();assert(not A.Coordinates.panel:IsShown() and not A.Coordinates.panel.EnableMouseArgs[1])
        assert(A.Coordinates.panel.point[4]==260 and A.Coordinates.panel.point[5]==-120)
        A.Command('coords show');assert(A.Coordinates.panel:IsShown())""")
        self.setUp()
        self.check("""ElmoWaypointDB={coordinatesPosition={x=math.huge,y=0}}
        MOCK.start();assert(not A.db.coordinatesPosition and A.Coordinates.panel:IsShown())""")

    def test_real_minimap_button_toggles_arrow_and_opens_reset_options(self):
        self.check("""MOCK.start();A.Add(60,40)
        local button=LibStub('LibDBIcon-1.0'):GetMinimapButton('ElmoWaypoint')
        button.scripts.OnClick(button,'LeftButton');assert(not A.db.showArrow)
        button.scripts.OnClick(button,'LeftButton');assert(A.db.showArrow)
        button.scripts.OnClick(button,'RightButton')
        assert(MOCK.openCategory==123 or MOCK.openLegacy==A.Settings.panel)
        A.Settings.panel:Show();MOCK.click(A.Settings.panel.reset)
        assert(#A.db.points==0 and not A.UI.panel:IsShown())""")

    def test_minimap_visibility_and_location_are_saved(self):
        self.check("""ElmoWaypointDB={minimap={hide=true,minimapPos=750}}
        MOCK.start();assert(A.db.minimap.hide and A.db.minimap.minimapPos==30)
        local button=LibStub('LibDBIcon-1.0'):GetMinimapButton('ElmoWaypoint')
        assert(not button:IsShown());A.Command('minimap show');assert(button:IsShown())
        A.Command('minimap hide');assert(not button:IsShown())""")

    def test_settings_apply_lock_visibility_and_center_without_resetting_points(self):
        self.check("""MOCK.start();A.Add(60,40);local p=A.Settings.panel;p:Show()
        MOCK.click(p.locked);assert(A.db.locked and not A.UI.panel.EnableMouseArgs[1])
        MOCK.click(p.showArrow);assert(not A.db.showArrow and #A.db.points==1)
        MOCK.click(p.showArrow);assert(A.db.showArrow)
        A.UI.panel.centerX,A.UI.panel.centerY=140,180
        A.SetLocked(false);A.UI.panel.scripts.OnDragStop(A.UI.panel)
        assert(A.db.position.x==40 and A.db.position.y==80)
        MOCK.click(p.center);assert(A.db.position==nil and #A.db.points==1)""")

    def test_saved_waypoints_restore_current_selection_and_ignore_corrupt_rows(self):
        self.check("""ElmoWaypointDB={points={{mapID=1,x=.6,y=.4,title='First'},
            {mapID=1,x=.7,y=.4,title='Second'},{mapID=0,x=.5,y=.5},{mapID=1,x=2,y=.5}},
            active=2,showArrow=true,locked=true,position={x=12,y=34}}
        MOCK.start();assert(#A.db.points==2 and A.Current().title=='Second' and A.db.locked)
        assert(A.UI.panel.point[4]==12 and A.UI.panel.point[5]==34 and A.UI.panel:IsShown())""")

    def test_fresh_lua_reload_restores_coordinates_and_visibility(self):
        self.check("""MOCK.start();A.Add(60,40,'Saved');A.SetVisible(false)
        A.db.coordinatesPosition={x=260,y=-120};A.Coordinates.Place();A.Command('coords lock');A.Command('coords hide')""")
        def unpack(value):
            return {k:unpack(v) for k,v in value.items()} if hasattr(value,'items') else value
        saved=unpack(self.vm.globals().ElmoWaypointDB)
        self.setUp();self.vm.globals().ElmoWaypointDB=self.vm.table_from(saved,recursive=True)
        self.check("""MOCK.start();assert(#A.db.points==1 and A.Current().title=='Saved')
        assert(not A.UI.panel:IsShown());A.Command('show');assert(A.UI.panel:IsShown())
        assert(not A.Coordinates.panel:IsShown() and A.db.coordinatesLocked and not A.Coordinates.panel.EnableMouseArgs[1])
        assert(A.Coordinates.panel.point[4]==260 and A.Coordinates.panel.point[5]==-120)""")

    def test_point_limit_and_reset_are_bounded(self):
        self.check("""MOCK.start();for i=1,50 do assert(A.Add(i,40))end
        assert(not A.Add(51,40) and #A.db.points==50)
        A.Reset();assert(A.Add(51,40) and #A.db.points==1)""")

    def test_circular_pins_use_actual_world_map_projection_and_parent_maps(self):
        self.check("""MOCK.start();A.Add(60,40,'Meeting place');MOCK.browse(1)
        local icon=A.Pins.records[1].world
        assert(icon:IsShown() and #WorldMapFrame.pins==1 and icon.ring.mask)
        assert(icon.ring.mask.texture=='Interface\\\\CHARACTERFRAME\\\\TempPortraitAlphaMask')
        local pos=icon:GetParent().position
        assert(math.abs(pos[1]-.6)<.00001 and math.abs(pos[2]-.4)<.00001)
        MOCK.browse(4);pos=icon:GetParent().position
        assert(icon:IsShown() and math.abs(pos[1]-.53)<.00001 and math.abs(pos[2]-.36)<.00001)
        MOCK.browse(3);assert(not icon:IsShown())""")

    def test_minimap_pin_tracks_location_zoom_rotation_and_zone(self):
        self.check("""MOCK.start();A.Add(51,50,'East');MOCK.advance(.1)
        local icon=A.Pins.records[1].mini
        assert(icon:IsShown() and icon:GetParent()==Minimap and icon.point[4]>0 and math.abs(icon.point[5])<.00001)
        local before=icon.point[4]
        MOCK.radius=120;Minimap:SetZoom(3);MOCK.fire('MINIMAP_UPDATE_ZOOM');MOCK.advance(.1)
        assert(icon.point[4]>before)
        MOCK.facing=math.pi/2;MOCK.cvars.rotateMinimap='1';MOCK.fire('CVAR_UPDATE','rotateMinimap','1');MOCK.advance(.1)
        assert(math.abs(icon.point[4])<.00001 and icon.point[5]<0)
        MOCK.map=3;MOCK.fire('ZONE_CHANGED_NEW_AREA');MOCK.advance(1.1);assert(not icon:IsShown())
        MOCK.map=1;MOCK.fire('ZONE_CHANGED_NEW_AREA');MOCK.advance(1.1);assert(icon:IsShown())""")

    def test_far_minimap_waypoint_stays_on_the_edge(self):
        self.check("""MOCK.start();A.Add(90,90);MOCK.advance(.1)
        local icon=A.Pins.records[1].mini
        assert(icon:IsShown() and LibStub('HereBeDragons-Pins-2.0'):IsMinimapIconOnEdge(icon))
        assert(math.sqrt(icon.point[4]^2+icon.point[5]^2)<=72.00001)""")

    def test_both_pin_tooltips_show_the_whole_note_near_cursor(self):
        self.check("""MOCK.start();local note=string.rep('Long note ',15)..'END'
        MOCK.runSlash('/way','60 40 '..note);assert(A.Current().title==note)
        for _,icon in ipairs({A.Pins.records[1].world,A.Pins.records[1].mini})do
            icon.scripts.OnEnter(icon)
            assert(GameTooltip:IsOwned(icon) and GameTooltip.anchor=='ANCHOR_CURSOR')
            assert(GameTooltip.lines[1]==note and GameTooltip.lines[2]:find('Duskwood',1,true))
            icon.scripts.OnLeave(icon);assert(not GameTooltip:IsShown())
        end""")

    def test_empty_note_has_a_useful_tooltip_and_unrelated_tooltip_is_untouched(self):
        self.check("""MOCK.start();A.Add(60,40);local icon=A.Pins.records[1].mini
        icon.scripts.OnEnter(icon);assert(GameTooltip.lines[1]:find('60.00, 40.00',1,true))
        GameTooltip:SetOwner(UIParent,'ANCHOR_CURSOR');GameTooltip:Show()
        icon.scripts.OnLeave(icon);assert(GameTooltip:IsShown())""")

    def test_hiding_arrow_or_launcher_keeps_pins_and_click_selects_saved_point(self):
        self.check("""MOCK.start();A.Add(60,40,'First');A.Add(70,40,'Second');MOCK.browse(1);MOCK.advance(.1)
        A.Command('hide');A.Command('minimap hide')
        local record=A.Pins.records[1]
        assert(record.world:IsShown() and record.mini:IsShown() and not A.UI.panel:IsShown())
        MOCK.click(record.world);assert(A.db.active==1 and A.db.showArrow and A.UI.panel:IsShown())
        A.Command('hide');MOCK.click(A.Pins.records[2].mini)
        assert(A.db.active==2 and A.Current().title=='Second' and A.db.showArrow)
        assert(record.world.ring.vertex[1]==.55 and A.Pins.records[2].world.ring.vertex[1]==1)""")

    def test_duplicate_note_updates_tooltip_and_delete_reindexes_without_stale_pins(self):
        self.check("""MOCK.start();A.Add(60,40,'Old');A.Add(70,40,'Keep');MOCK.browse(1)
        A.Add(60,40,'New note');assert(#WorldMapFrame.pins==2)
        local icon=A.Pins.records[1].world;icon.scripts.OnEnter(icon)
        A.Add(60,40,'Edited while hovering');assert(GameTooltip.lines[1]=='Edited while hovering')
        A.RemoveCurrent();assert(#A.Pins.records==1 and #WorldMapFrame.pins==1)
        assert(A.Pins.records[1].world.index==1 and A.Pins.records[1].world.waypoint.title=='Keep')
        A.Pins.records[1].world.scripts.OnEnter(A.Pins.records[1].world)
        assert(GameTooltip.lines[1]=='Keep')""")

    def test_reset_unregisters_only_our_pins_and_reuses_frames(self):
        self.check("""MOCK.start();A.Add(60,40);MOCK.browse(1);MOCK.advance(.1)
        local library=LibStub('HereBeDragons-Pins-2.0');local other={}
        local mini,world=CreateFrame('Frame'),CreateFrame('Frame')
        library:AddMinimapIconMap(other,mini,1,.5,.5,true,true)
        library:AddWorldMapIconMap(other,world,1,.5,.5)
        local record=A.Pins.records[1];record.world.scripts.OnEnter(record.world)
        A.Reset();assert(not GameTooltip:IsShown() and #WorldMapFrame.pins==1)
        assert(library.minimapPins[mini] and library.worldmapPins[world])
        assert(not library.minimapPins[record.mini] and not library.worldmapPins[record.world])
        A.Add(65,40);assert(A.Pins.records[1]==record and #A.Pins.free==0)""")

    def test_saved_notes_and_pins_restore_with_arrow_hidden(self):
        self.check("""ElmoWaypointDB={points={{mapID=1,x=.6,y=.4,title='Persisted note'}},showArrow=false}
        MOCK.start();MOCK.browse(1);MOCK.advance(.1)
        local record=A.Pins.records[1]
        assert(not A.UI.panel:IsShown() and record.world:IsShown() and record.mini:IsShown())
        record.mini.scripts.OnEnter(record.mini);assert(GameTooltip.lines[1]=='Persisted note')""")

    def test_normal_registration_gives_way_to_elmo_and_retains_tomtom_aliases(self):
        self.check("""SLASH_TOMTOM_WAY1,SLASH_TOMTOM_WAY2='/way','/tway'
        local original=function(text)MOCK.tomtomText=text end
        SlashCmdList.TOMTOM_WAY=original
        MOCK.start();MOCK.runSlash('/way','60 40 Elmo')
        assert(A.Current().title=='Elmo' and not MOCK.tomtomText)
        MOCK.runSlash('/tway','55 66 TomTom');assert(MOCK.tomtomText=='55 66 TomTom')
        assert(SlashCmdList.TOMTOM_WAY==original)""")

    def test_commands_do_not_depend_on_the_background_chat_importer(self):
        self.check("""ChatFrameUtil=nil;ChatFrame_ImportAllListsToHash=nil
        MOCK.start();SlashCmdList.ELMOWAYPOINT('60 40')
        assert(#A.db.points==1 and A.Current().x==.6)
        A.Command('  RESET  ');assert(#A.db.points==0)""")

    def test_reset_leaves_native_and_other_addon_waypoints_untouched(self):
        self.check("""MOCK.start();A.Add(60,40)
        TomTomDB={waypoints={123}}
        C_Map.ClearUserWaypoint=function()error('Native waypoint must remain untouched')end
        TomTom={RemoveAllWaypoints=function()error('TomTom points must remain untouched')end}
        A.Reset();assert(#A.db.points==0 and TomTomDB.waypoints[1]==123)""")

    def test_update_interval_does_not_run_before_login(self):
        self.check("""MOCK.advance(10);assert(not A.db and MOCK.mapReads==0)
        MOCK.start();A.Add(60,40);local reads=MOCK.mapReads
        MOCK.advance(.01);assert(MOCK.mapReads==reads)
        MOCK.advance(.05);assert(MOCK.mapReads>reads)""")

class LegacyWaypointTests(WaypointTests):
    legacy=True

if __name__=='__main__':unittest.main()
