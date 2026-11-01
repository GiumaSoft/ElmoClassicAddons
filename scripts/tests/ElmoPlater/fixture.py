from pathlib import Path
import os
from lupa.lua51 import LuaRuntime
ROOT = Path(__file__).resolve().parents[3]

def create_vm():
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute((Path(__file__).parent/'wow_mock.lua').read_text())
    vm.execute('''
    local sample=CreateFrame('Frame');local methods=getmetatable(sample).__index
    local oldAlpha=methods.SetAlpha
    function methods:SetAlpha(v)
     if self.nativeArtwork then self.alpha=v else oldAlpha(self,v) end
    end
    function methods:GetAlpha()return self.alpha or 1 end
    function methods:SetScale(v)self.scale=v end
    function methods:GetEffectiveScale()return (self.scale or 1)*(self.parent and self.parent:GetEffectiveScale() or 1)end
    -- Only the guarded hit-test API may write native frames. Other native writes and all measurements remain forbidden.
    local oldHitPoints=methods.SetHitTestPoints
    function methods:SetHitTestPoints(points)
     assert(self:CanChangeHitTestPoints(), 'Click binding outside an allowed tick')
     local fixture=MOCK.inFixture;MOCK.inFixture=true
     local ok,err=pcall(oldHitPoints,self,points);MOCK.inFixture=fixture
     assert(ok,err);MOCK.hitWrites=(MOCK.hitWrites or 0)+1
    end
    NamePlateSetupOptions={healthBarHeight=12,unitNameAnchorStyle=1}
    NamePlateConstants={NAME_ANCHOR_STYLES={InsideHealthBar=1}}
    function CombatLogGetCurrentEventInfo()return unpack(MOCK.logEvent)end
    function MOCK.log(event,guid,name,source,spellID,kind)
     MOCK.logEvent={MOCK.time,event,false,source or UnitGUID('player'),'Source',0,0,guid,name,0,0,spellID or 772,'Spell',1,kind or 'DEBUFF'}
     MOCK.event('COMBAT_LOG_EVENT_UNFILTERED')
    end
    local oldMob=MOCK.mob
    function MOCK.mob(...)
     local d,p=oldMob(...);MOCK.inFixture=true
     local n=p.UnitFrame;n.HealthBarsContainer=CreateFrame('Frame',nil,n)
     n.HealthBarsContainer.healthBar=CreateFrame('StatusBar',nil,n.HealthBarsContainer)
     n.HealthBarsContainer.healthBar:SetPoint('BOTTOMLEFT',n,'BOTTOMLEFT',0,8)
     n.HealthBarsContainer.healthBar:SetPoint('BOTTOMRIGHT',n,'BOTTOMRIGHT',0,8)
     n.HealthBarsContainer.healthBar:SetHeight(12)
     n.name=n:CreateFontString(nil,'OVERLAY');n.name:SetAllPoints(n)
     MOCK.inFixture=false;MOCK.allowPlate=p;MOCK.event('NAME_PLATE_UNIT_ADDED',p.unitToken);MOCK.allowPlate=nil
     return d,p
    end
    ''')
    ns=vm.table()
    load=vm.eval('function(s,n,ns) assert(loadstring(s,"@"..n))("ElmoPlater",ns)end')
    if os.environ.get('ELMO_TEST_FOREVER'):
        vm.execute("""
        local getter=CombatLogGetCurrentEventInfo
        C_CombatLog={IsCombatLogRestricted=function()return MOCK.logRestricted==true end,GetCurrentEventInfo=getter}
        CombatLogGetCurrentEventInfo=nil
        C_EventUtils={IsEventValid=function(event)return not MOCK.invalidEvents or not MOCK.invalidEvents[event] end}
        """)
    addon=Path(os.environ.get('ELMO_TEST_ADDON',ROOT/'ElmoPlater'))
    for name in (addon/'ElmoPlater.toc').read_text().splitlines():
        if name.endswith('.lua'): load((addon/name).read_text(),name,ns)
    vm.globals().A=ns
    return vm,ns
