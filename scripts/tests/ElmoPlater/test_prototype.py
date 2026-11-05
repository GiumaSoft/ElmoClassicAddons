from fixture import create_vm
vm,ns=create_vm()
vm.execute(r"""
MOCK.start();assert(A.ready and A.version=='2.2.4')
local a,pa=MOCK.mob('nameplate1','Creature-a','Murloc Streamrunner')
local b,pb=MOCK.mob('nameplate2','Creature-b','Boar');pb.centerX=950
assert(A.units.nameplate1 and pa.UnitFrame.alpha==0)
local ra,rb=A.units.nameplate1,A.units.nameplate2
a.health=30;b.health=70;MOCK.event('UNIT_HEALTH','nameplate1')
assert(ra.frame.percent:GetText()=='30%')
assert(ra.frame.bar.statusTexture=='Interface\\Buttons\\WHITE8X8')
assert(ra.clickBound and rb.clickBound and MOCK.clickAt(600,316)=='Creature-a')
MOCK.event('PLAYER_TARGET_CHANGED');assert(ra.frame:IsShown())
assert(MOCK.nativeWidth==132 and MOCK.writes==0 and MOCK.insetWrites==0)
MOCK.aura('nameplate1',772,1);MOCK.aura('nameplate1',999,30,'party1');MOCK.aura('nameplate1',888,30,'pet')
MOCK.event('UNIT_AURA','nameplate1');assert(#ra.auras==1)
assert(ra.frame.icons[1]:IsShown() and not ra.frame.icons[1].mouse)
assert(A.db.learnedDebuffs[772] and not A.db.learnedDebuffs[999] and not A.db.learnedDebuffs[888])
local function marked(unit)
 for token,record in pairs(A.units) do
  local priority=token==unit
  assert(record.priority==priority,'Wrong priority: '..token)
  local x,y,w,h=MOCK.worldRect(record.frame)
  local bx,by,bw,bh=MOCK.worldRect(record.bounds)
  assert(x==bx and y==by and w==bw and h==bh*(priority and 4 or 2),'Invalid rectangle: '..token)
  assert(not record.frame.mouse and not record.frame.bar.mouse)
  local nx,ny,nw,nh=MOCK.worldRect(record.frame.name)
  local lx,ly,lw,lh=MOCK.worldRect(record.frame.level)
  assert(nx+nw+6<=lx,'Name and level overlap')
  assert(math.abs((nx+lx+lw)/2-(x+w/2))<.01,'Name and level group is not centered')
  assert(ny>=y+h and ly>=y+h and ny+nh<=y+h+20 and ly+lh<=y+h+20,'Header overlaps bar or debuffs')
  assert(record.frame.name.wordWrap==false and record.frame.level.wordWrap==false)
  for i=1,#record.auras do
   local _,debuffBottom,_,debuffHeight=MOCK.worldRect(record.frame.icons[i])
   assert(debuffBottom>=y+h+20,'Debuff overlaps bar or name/level header')
  end
 end
end
marked(nil)
-- Long names may extend beyond the health rectangle; the level follows the full name.
a.name='Murloc Streamrunner with a very long name';MOCK.event('UNIT_HEALTH','nameplate1')
local nameX,_,nameWidth=MOCK.worldRect(ra.frame.name)
local barX,_,barWidth=MOCK.worldRect(ra.frame)
assert(nameX+nameWidth>barX+barWidth and ra.frame.name:GetText()==a.name)
assert(nameX<barX,'Long header must be able to extend on both sides of the bar')
marked(nil)
MOCK.hit('nameplate1','Player-other');marked(nil)
MOCK.hit('nameplate1');marked('nameplate1')
MOCK.hit('nameplate2');marked('nameplate1')
MOCK.combat=true
assert(MOCK.clickAt(600,330)=='Creature-a');MOCK.event('PLAYER_TARGET_CHANGED');marked('nameplate1')
b.health=19;MOCK.event('UNIT_HEALTH','nameplate2');marked('nameplate2')
assert(rb.frame:GetFrameLevel()>ra.frame:GetFrameLevel())
assert(MOCK.clickAt(950,330)=='Creature-b')
-- Points above the native region remain clipped.
assert(MOCK.clickAt(950,340)==nil)
for i=1,5 do A.Update(false);marked('nameplate2') end
MOCK.nativeHeight=40;A.Update(false);marked('nameplate2')
MOCK.nativeHeight=32;A.Update(false);marked('nameplate2')
-- Debuffs stay above the name/level header for multiple rows and sizes.
for id=1001,1008 do MOCK.aura('nameplate2',id,20) end
MOCK.event('UNIT_AURA','nameplate2');marked('nameplate2')
A.db.plateAuraSize=30;A.Update(false);marked('nameplate2')
b.auras={};MOCK.event('UNIT_AURA','nameplate2');marked('nameplate2')
A.db.plateAuraSize=22
local c,pc=MOCK.mob('nameplate3','Creature-c','Untouched');pc.centerX=1300;c.health=1
marked('nameplate2');assert(not A.attacked[c.guid])
MOCK.remove('nameplate3');assert(pc.UnitFrame.alpha==1)
MOCK.advance(1.2);assert(#ra.auras==0 and not ra.frame.icons[1]:IsShown())
MOCK.combat=false
a.neutral=true;MOCK.event('UNIT_FACTION','nameplate1');assert(ra.frame.bar.statusColor[2]==.82)
a.friendly=true;MOCK.event('UNIT_FACTION','nameplate1');assert(ra.frame.bar.statusColor[2]==.8)
a.friendly=false;a.neutral=false;a.tapDenied=true;MOCK.event('UNIT_FACTION','nameplate1')
assert(ra.frame.name:GetText():find('CLAIMED',1,true) and ra.frame.border[1]==.025)
MOCK.event('PLAYER_REGEN_ENABLED');assert(next(A.attacked)==nil);marked(nil)
local hitWrites=MOCK.hitWrites
MOCK.combat=true;MOCK.event('CVAR_UPDATE','nameplateSize');A.Update(false)
assert(not ra.clickBound and not rb.clickBound and MOCK.hitWrites==hitWrites)
MOCK.combat=false;MOCK.event('PLAYER_REGEN_ENABLED');assert(ra.clickBound and rb.clickBound)
a.dead=true;MOCK.event('UNIT_FLAGS','nameplate1');assert(not ra.frame:IsShown())
local native=pa.UnitFrame;pa.UnitFrame=nil;MOCK.remove('nameplate1');assert(native.alpha==1)
assert(pa.hitPoints[1].relativeTo==native.HealthBarsContainer.healthBar)
MOCK.event('PLAYER_LOGOUT');assert(pb.UnitFrame.alpha==1)
assert(pb.hitPoints[1].relativeTo==pb.UnitFrame.HealthBarsContainer.healthBar)
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
""")
print('Prototype checks passed: native geometry isolation, engaged-only double height, debuffs above bars, targeting containment, own auras, expiry, colours and pooled cleanup. Simulated APIs only.')
