"""Mana and casting display through public or opaque native API fixtures."""
import unittest
from fixture import create_vm


API = r'''
local methods = getmetatable(A.frame).__index
local text = methods.SetText
local secrets = {}
function MOCK.secret()
    local value = setmetatable({}, {
        __index=function()error('Private value indexed')end,
        __tostring=function()error('Private value converted to text')end,
        __add=function()error('Private arithmetic')end,
        __sub=function()error('Private arithmetic')end,
        __div=function()error('Private arithmetic')end,
        __lt=function()error('Private comparison')end,
        __le=function()error('Private comparison')end})
    secrets[value] = true
    return value
end
function issecretvalue(value) return secrets[value] == true end
function methods:SetText(value)
    if issecretvalue(value) then self.opaqueText=value else text(self,value) end
end
function UnitPowerType(unit) return MOCK.units[unit] and MOCK.units[unit].powerType or 0 end
function UnitPower(unit, power)
    assert(power==0);return MOCK.units[unit] and MOCK.units[unit].mana or 0
end
function UnitPowerMax(unit, power)
    assert(power==0);return MOCK.units[unit] and MOCK.units[unit].maxMana or 0
end
local function active(unit,channel)
    local cast=MOCK.units[unit] and MOCK.units[unit].cast
    if cast and cast.channel==channel and cast.expires>GetTime() then return cast end
end
function UnitCastingInfo(unit)
    local c=active(unit,false)
    if c then return c.name,c.name,c.icon,c.start,c.finish,false,'cast',c.locked,100,c.barID end
end
function UnitChannelInfo(unit)
    local c=active(unit,true)
    if c then return c.name,c.name,c.icon,c.start,c.finish,false,c.locked,100,false,0,c.barID end
end
function UnitCastingDuration() error('No duration binding is needed') end
function UnitChannelDuration() error('No duration binding is needed') end
function MOCK.castUnit(unit,channel,seconds)
    local c={name=channel and 'Drain Life' or 'Fireball',icon=135812,
        start=GetTime()*1000,finish=(GetTime()+seconds)*1000,expires=GetTime()+seconds,
        channel=channel,locked=false,barID=1}
    MOCK.units[unit].cast=c
    return c
end
function MOCK.legacyBars()
    UnitCastingDuration,UnitChannelDuration=nil,nil
end
MOCK.start()
'''


class UnitBarsTests(unittest.TestCase):
    def setUp(self):
        self.vm, _ = create_vm()
        self.vm.execute(API)

    def check(self, code):
        self.vm.execute(code)

    def test_mana_filters_and_power_events_include_zero_mana(self):
        self.check("""
        local mob=MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        assert(A.db.showMana and A.db.showCast and not f.mana:IsShown() and not f.cast:IsShown())
        mob.maxMana,mob.mana=1000,750;MOCK.event('UNIT_MAXPOWER','nameplate1')
        assert(f.mana:IsShown() and f.mana.bar.maximum==1000 and f.mana.bar.value==750)
        mob.mana=0;MOCK.event('UNIT_POWER_UPDATE','nameplate1')
        assert(f.mana:IsShown() and f.mana.bar.value==0)
        mob.powerType=1;MOCK.event('UNIT_DISPLAYPOWER','nameplate1');assert(not f.mana:IsShown())
        mob.powerType=0;mob.maxMana=0;A.Update(false);assert(not f.mana:IsShown())
        mob.maxMana=1000;UnitPower=function()return nil end
        A.Update(false);assert(not f.mana:IsShown() and f:IsShown())
        """)

    def test_private_mana_values_are_forwarded_without_arithmetic(self):
        self.check("""
        local mob=MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        mob.mana,mob.maxMana=MOCK.secret(),MOCK.secret()
        MOCK.combat=true;MOCK.event('UNIT_POWER_FREQUENT','nameplate1')
        assert(f.mana:IsShown() and rawequal(f.mana.bar.value,mob.mana))
        assert(rawequal(f.mana.bar.maximum,mob.maxMana) and f.mana.bar.minimum==0)
        mob.powerType=MOCK.secret();A.Update(false)
        assert(not f.mana:IsShown() and f:IsShown())
        """)

    def test_native_cast_and_channel_ranges_icons_names_and_directions(self):
        self.check("""
        MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        local c=MOCK.castUnit('nameplate1',false,3);MOCK.event('UNIT_SPELLCAST_START','nameplate1')
        assert(f.cast:IsShown() and f.cast.name:GetText()=='Fireball' and f.cast.icon.texture==135812)
        assert(f.cast.bar.minimum==c.start and f.cast.bar.maximum==c.finish and not f.cast.bar.reverseFill)
        assert(f.cast.bar.value==GetTime()*1000 and not f.cast.remaining:IsShown())
        MOCK.time=MOCK.time+.03;f.cast:GetScript('OnUpdate')(f.cast,.03)
        assert(f.cast.bar.value==GetTime()*1000)
        c=MOCK.castUnit('nameplate1',true,5);MOCK.event('UNIT_SPELLCAST_CHANNEL_START','nameplate1')
        assert(f.cast.name:GetText()=='Drain Life' and f.cast.bar.maximum==c.finish)
        assert(f.cast.bar.reverseFill and f.cast.remaining:IsShown())
        MOCK.units.nameplate1.cast=nil;MOCK.event('UNIT_SPELLCAST_CHANNEL_STOP','nameplate1')
        assert(not f.cast:IsShown())
        """)

    def test_private_cast_fields_only_reach_native_display_methods(self):
        self.check("""
        MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        local c=MOCK.castUnit('nameplate1',false,3)
        c.name,c.icon,c.start,c.finish,c.locked=MOCK.secret(),MOCK.secret(),MOCK.secret(),MOCK.secret(),MOCK.secret()
        MOCK.combat=true;MOCK.event('UNIT_SPELLCAST_START','nameplate1',MOCK.secret(),MOCK.secret())
        assert(f.cast:IsShown() and rawequal(f.cast.name.opaqueText,c.name))
        assert(rawequal(f.cast.icon.texture,c.icon))
        assert(rawequal(f.cast.bar.minimum,c.start) and rawequal(f.cast.bar.maximum,c.finish))
        assert(f.cast.bar.value==GetTime()*1000)
        c.channel=true;MOCK.event('UNIT_SPELLCAST_CHANNEL_START','nameplate1')
        assert(f.cast:IsShown() and f.cast.bar.reverseFill and f.cast.remaining:IsShown())
        MOCK.advance(4);assert(not f.cast:IsShown())
        """)

    def test_legacy_cast_and_channel_progress_delays_and_interruptions(self):
        self.check("""
        MOCK.legacyBars();MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        local c=MOCK.castUnit('nameplate1',false,4);A.Update(false)
        MOCK.advance(1);assert(f.cast:IsShown() and math.abs(f.cast.bar.value-c.start-1000)<100)
        assert(f.cast.bar.minimum==c.start and f.cast.bar.maximum==c.finish)
        c.finish=c.finish+1000;c.expires=c.expires+1
        MOCK.event('UNIT_SPELLCAST_DELAYED','nameplate1');assert(f.cast.bar.maximum==c.finish)
        c=MOCK.castUnit('nameplate1',true,4);MOCK.advance(1)
        assert(math.abs(c.finish-f.cast.bar.value-3000)<100 and f.cast.bar.reverseFill)
        c.locked=true;MOCK.event('UNIT_SPELLCAST_NOT_INTERRUPTIBLE','nameplate1')
        assert(f.cast.remaining.color[1]==.55)
        MOCK.units.nameplate1.cast=nil;MOCK.event('UNIT_SPELLCAST_INTERRUPTED','nameplate1')
        assert(not f.cast:IsShown())
        c=MOCK.castUnit('nameplate1',false,1);MOCK.advance(2);assert(not f.cast:IsShown())
        """)

    def test_missing_timing_hides_cast_without_affecting_health_and_recovers(self):
        self.check("""
        MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        local c=MOCK.castUnit('nameplate1',false,4)
        c.start,c.finish=nil,nil
        MOCK.event('UNIT_SPELLCAST_START','nameplate1')
        assert(not f.cast:IsShown() and f:IsShown())
        c.start,c.finish=MOCK.secret(),MOCK.secret();A.Update(false);assert(f.cast:IsShown())
        MOCK.legacyBars();A.Update(false);assert(f.cast:IsShown() and f:IsShown())
        c.start,c.finish=GetTime()*1000,(GetTime()+4)*1000;A.Update(false)
        assert(f.cast:IsShown() and f.cast.bar.minimum==c.start and f.cast.bar.maximum==c.finish)
        """)

    def test_new_bars_do_not_resize_health_or_capture_clicks_and_cast_closes_mana_gap(self):
        self.check("""
        local mob=MOCK.mob('nameplate1');local record=A.units.nameplate1;local f=record.frame
        local x,y,w,h=MOCK.worldRect(f)
        mob.mana,mob.maxMana=500,1000;MOCK.castUnit('nameplate1',false,4);A.Update(false)
        local mx,my,mw,mh=MOCK.worldRect(f.mana)
        local cx,cy,cw,ch=MOCK.worldRect(f.cast)
        assert(mx==x and mw==w and mh==7 and my+mh==y-2)
        assert(cx==x and cw==w and ch==16 and cy+ch<my)
        assert(not f.mana.mouse and not f.mana.bar.mouse and not f.cast.mouse and not f.cast.bar.mouse)
        local currentX,currentY,currentW,currentH=MOCK.worldRect(f)
        assert(x==currentX and y==currentY and w==currentW and h==currentH)
        assert(record.plate.hitPoints[1].relativeTo==f and record.plate.hitPoints[2].relativeTo==f)
        assert(MOCK.clickAt(cx+cw/2,cy+ch/2)==nil)
        mob.maxMana=0;A.Update(false)
        local _,newY,_,newH=MOCK.worldRect(f.cast);assert(newY+newH==y-2)
        assert(MOCK.foreignWrites==0 and MOCK.restrictedReads==0 and MOCK.hookAttempts==0)
        """)

    def test_pool_cleanup_does_not_keep_old_mana_or_cast(self):
        self.check("""
        local mob,plate=MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        mob.mana,mob.maxMana=500,1000;MOCK.castUnit('nameplate1',false,20);A.Update(false)
        assert(f.mana:IsShown() and f.cast:IsShown())
        MOCK.remove('nameplate1')
        assert(not f.mana:IsShown() and not f.cast:IsShown() and f.cast.name:GetText()=='')
        MOCK.mob('nameplate2','Creature-new','New Mob',plate)
        assert(A.units.nameplate2.frame==f and f:IsShown())
        assert(not f.mana:IsShown() and not f.cast:IsShown() and f.cast.icon.texture==nil)
        """)

    def test_disabled_preferences_persist_and_can_be_reenabled(self):
        self.check("""
        local mob=MOCK.mob('nameplate1');local f=A.units.nameplate1.frame
        mob.mana,mob.maxMana=500,1000;MOCK.castUnit('nameplate1',false,20)
        A.db.showMana,A.db.showCast=false,false;A.Update(false);A.Initialize()
        assert(not f.mana:IsShown() and not f.cast:IsShown() and not A.db.showMana and not A.db.showCast)
        A.db.showMana,A.db.showCast=true,true;A.Update(false)
        assert(f.mana:IsShown() and f.cast:IsShown())
        """)


if __name__ == "__main__":
    unittest.main()
