from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[3]
ADDON = Path(os.environ.get('ELMO_TEST_ADDON', ROOT / "ElmoPlater"))
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
ns=vm.table();load=vm.eval('function(s,n,ns) assert(loadstring(s,"@"..n))("ElmoPlater",ns)end')
if os.environ.get('ELMO_TEST_FOREVER'):
    vm.execute('''
    local getter=CombatLogGetCurrentEventInfo
    C_CombatLog={IsCombatLogRestricted=function()return MOCK.logRestricted==true end,
        GetCurrentEventInfo=getter}
    CombatLogGetCurrentEventInfo=nil
    C_EventUtils={IsEventValid=function(event)return not MOCK.invalidEvents or not MOCK.invalidEvents[event] end}
    ''')
for name in ['Migration.lua','Core.lua','Plates.lua']:load((ADDON/name).read_text(),name,ns)
vm.globals().A=ns
vm.execute('''
MOCK.start();assert(A.ready and A.version=='2.0.7')
local a,pa=MOCK.mob('nameplate1','Creature-a','Wolf')
local b,pb=MOCK.mob('nameplate2','Creature-b','Boar');pb.centerX=950
assert(A.units.nameplate1 and A.units.nameplate2 and pa.UnitFrame.alpha==0)
a.health=20;b.health=70;MOCK.event('UNIT_HEALTH','nameplate1')
assert(A.units.nameplate1.frame:GetFrameLevel()>A.units.nameplate2.frame:GetFrameLevel())
assert(A.units.nameplate1.frame.percent:GetText()=='20%')
assert(A.units.nameplate1.frame.bar.statusTexture=='Interface\\\\Buttons\\\\WHITE8X8')
assert(A.units.nameplate1.clickBound and A.units.nameplate2.clickBound)
assert(MOCK.clickAt(600,316)=='Creature-a')
MOCK.event('PLAYER_TARGET_CHANGED');assert(A.units.nameplate1.frame:IsShown())
assert(MOCK.nativeWidth==132 and MOCK.writes==0 and MOCK.insetWrites==0)
MOCK.aura('nameplate1',772,1);MOCK.aura('nameplate1',999,30,'party1');MOCK.aura('nameplate1',888,30,'pet')
MOCK.event('UNIT_AURA','nameplate1');assert(#A.units.nameplate1.auras==1)
assert(A.units.nameplate1.frame.icons[1]:IsShown() and not A.units.nameplate1.frame.icons[1].mouse)
MOCK.units.target=nil;MOCK.event('PLAYER_TARGET_CHANGED')
b.health=20;MOCK.event('UNIT_HEALTH','nameplate2')
assert(A.units.nameplate2.missing and not A.units.nameplate1.missing)
assert(A.units.nameplate2.frame:GetFrameLevel()>A.units.nameplate1.frame:GetFrameLevel())
local c,pc=MOCK.mob('nameplate3','Creature-c','Bear');pc.centerX=1300;c.health=90
local function above(first,second)
 assert(A.units[first].frame:GetFrameLevel()>A.units[second].frame:GetFrameLevel())
end
local function marked(unit)
 for token,record in pairs(A.units) do
  local priority=token==unit
  assert(record.priority==priority, 'Wrong priority: '..token)
  local x,y,w,h=MOCK.worldRect(record.frame)
  local bx,by,bw,bh=MOCK.worldRect(record.bounds)
  assert(x==bx and y==by and w==bw, 'Priority rectangle moved sideways or downward: '..token)
  assert(h==bh*(priority and 2 or 1), 'Wrong rectangle height: '..token)
  assert(not record.frame.mouse and not record.frame.bar.mouse)
 end
end
-- Only our attacked mobs qualify; nearby mobs and attacks by others never enlarge a bar.
marked(nil)
MOCK.hit('nameplate1','SWING_DAMAGE','Player-other');marked(nil)
MOCK.hit('nameplate1');marked('nameplate1')
MOCK.hit('nameplate2');marked('nameplate2')
c.health=1;MOCK.event('UNIT_HEALTH','nameplate3');marked('nameplate2')
assert(not A.attacked[c.guid])
MOCK.hit('nameplate3');marked('nameplate3')
c.health=90;MOCK.event('UNIT_HEALTH','nameplate3');marked('nameplate2')
-- Missing-debuff ties use actual remaining HP, independently of GUID and percentage.
b.health=80;c.health=40;MOCK.event('UNIT_HEALTH','nameplate2')
above('nameplate3','nameplate2');marked('nameplate3')
b.health=30;c.maxHealth=200;MOCK.event('UNIT_HEALTH','nameplate3')
above('nameplate2','nameplate3');marked('nameplate2')
b.health=15;c.health=20;MOCK.event('UNIT_HEALTH','nameplate2')
above('nameplate2','nameplate3');marked('nameplate2')
b.health=20;c.health=90;c.maxHealth=100;MOCK.event('UNIT_HEALTH','nameplate3')
MOCK.combat=true
-- Critical health wins over missing debuffs; exactly 20% is not critical.
a.health=19.9;MOCK.event('UNIT_HEALTH','nameplate1')
above('nameplate1','nameplate2');above('nameplate2','nameplate3');marked('nameplate1')
a.health=20;MOCK.event('UNIT_HEALTH','nameplate1')
above('nameplate2','nameplate3');above('nameplate3','nameplate1');marked('nameplate2')
-- Within the critical group, missing debuffs win even over a lower health percentage.
a.health=1;b.health=19;MOCK.event('UNIT_HEALTH','nameplate2')
above('nameplate2','nameplate1');above('nameplate1','nameplate3');marked('nameplate2')
b.health=20;MOCK.event('UNIT_HEALTH','nameplate2')
above('nameplate1','nameplate2');above('nameplate2','nameplate3');marked('nameplate1')
a.health=20;MOCK.event('UNIT_HEALTH','nameplate1')
-- Selection participates in the same ordering and does not override any rule.
MOCK.units.target=c;MOCK.event('PLAYER_TARGET_CHANGED')
above('nameplate2','nameplate3');above('nameplate3','nameplate1')
marked('nameplate2')
-- The added upper half targets the correct mob during combat; it shrinks when priority moves.
assert(MOCK.clickAt(900,330)=='Creature-b');MOCK.event('PLAYER_TARGET_CHANGED')
marked('nameplate2')
assert(A.units.nameplate2.selected and MOCK.clickAt(900,330)=='Creature-b')
MOCK.units.target=c;MOCK.event('PLAYER_TARGET_CHANGED')
a.health=10;MOCK.event('UNIT_HEALTH','nameplate1')
above('nameplate1','nameplate2');above('nameplate2','nameplate3')
marked('nameplate1')
MOCK.units.target=b;MOCK.event('PLAYER_TARGET_CHANGED')
above('nameplate1','nameplate2');above('nameplate2','nameplate3')
marked('nameplate1')
MOCK.units.target=a;MOCK.event('PLAYER_TARGET_CHANGED')
marked('nameplate1');assert(A.units.nameplate1.selected and A.units.nameplate1.priority)
MOCK.units.target=nil;MOCK.event('PLAYER_TARGET_CHANGED')
above('nameplate1','nameplate2');above('nameplate2','nameplate3')
marked('nameplate1')
-- Crossing below 20% immediately updates both layering and the marker.
c.health=1;MOCK.event('UNIT_HEALTH','nameplate3')
above('nameplate3','nameplate1');above('nameplate1','nameplate2');marked('nameplate3')
-- Repeated updates never compound the doubled height; native size changes still propagate.
for i=1,5 do A.Update(false);marked('nameplate3') end
MOCK.nativeHeight=40;A.Update(false);marked('nameplate3')
MOCK.nativeHeight=32;A.Update(false);marked('nameplate3')
local d,pd=MOCK.mob('nameplate4','Creature-d','Unattacked');pd.centerX=200;d.health=1
assert(A.units.nameplate4.clickBound);marked('nameplate3')
MOCK.remove('nameplate4')
MOCK.log('UNIT_DIED',c.guid,c.name,'Creature-enemy');marked('nameplate1')
assert(not A.attacked[c.guid])
MOCK.combat=false
MOCK.remove('nameplate3');assert(pc.UnitFrame.alpha==1)
MOCK.advance(1.2);assert(#A.units.nameplate1.auras==0 and not A.units.nameplate1.frame.icons[1]:IsShown())
marked('nameplate1')
A.Command('debuff Rend');assert(A.db.watchDebuff=='Rend')
local aura=MOCK.aura('nameplate1',6546,15);aura.name='Rend';MOCK.event('UNIT_AURA','nameplate1')
assert(not A.units.nameplate1.missing)
a.neutral=true;MOCK.event('UNIT_FACTION','nameplate1');assert(A.units.nameplate1.frame.bar.statusColor[2]==.82)
a.friendly=true;MOCK.event('UNIT_FACTION','nameplate1');assert(A.units.nameplate1.frame.bar.statusColor[2]==.8)
a.friendly=false;a.tapDenied=true;MOCK.event('UNIT_FACTION','nameplate1')
assert(A.units.nameplate1.frame.name:GetText():find('CLAIMED',1,true))
MOCK.event('PLAYER_REGEN_ENABLED');assert(next(A.attacked)==nil);marked(nil)
local hitWrites=MOCK.hitWrites
MOCK.combat=true;MOCK.event('CVAR_UPDATE','nameplateSize');A.Update(false)
assert(not A.units.nameplate1.clickBound and not A.units.nameplate2.clickBound)
assert(MOCK.hitWrites==hitWrites, 'Hit-test API called in a blocked combat tick')
MOCK.combat=false;MOCK.event('PLAYER_REGEN_ENABLED')
assert(A.units.nameplate1.clickBound and A.units.nameplate2.clickBound)
a.dead=true;MOCK.event('UNIT_FLAGS','nameplate1');assert(not A.units.nameplate1.frame:IsShown())
local native=pa.UnitFrame;pa.UnitFrame=nil;MOCK.remove('nameplate1');assert(native.alpha==1)
assert(pa.hitPoints[1].relativeTo==native.HealthBarsContainer.healthBar)
MOCK.event('PLAYER_LOGOUT');assert(pb.UnitFrame.alpha==1)
assert(pb.hitPoints[1].relativeTo==pb.UnitFrame.HealthBarsContainer.healthBar)
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
''')
print('Lua 5.1 prototype smoke checks passed: attacked-only enlargement, solid health texture, guarded native click binding, added upper-half clicks in combat, priority and size changes, exact 20% boundary, combat-end cleanup, own debuffs, colours, expiry and pooled-frame cleanup. Simulated APIs only; native clipping is modeled.')
