from fixture import create_vm

vm, _ = create_vm()
vm.execute(r'''
MOCK.start()
local guid='Creature-0-123-0-1-1234-0000000001'
local mob,plate=MOCK.mob('nameplate1',guid,'Quest beast')
local record=A.units.nameplate1
assert(record.frame.questBag,'Quest loot marker is missing')
assert(record.frame.questKill,'Quest kill marker is missing')
assert(not record.frame.questBag:IsShown(),'Questie is optional')
assert(not record.frame.questKill:IsShown())

local tooltips={lookupByKey={}}
local player={currentQuestlog={}}
Questie={ICON_TYPE_LOOT=2,ICON_TYPE_SLAY=1,
    icons={loot='Interface\\AddOns\\Questie\\Icons\\loot.blp',slay='Interface\\AddOns\\Questie\\Icons\\slay.blp'}}
QuestieLoader={ImportModule=function(_,name)
    return name=='QuestieTooltips' and tooltips or player
end}
local loot={Type='item',Icon=2,Completed=false}
function loot:Update() self.Completed=MOCK.lootComplete==true end
local kill={Type='monster',Icon=1,Completed=false}
tooltips.lookupByKey.m_1234={
    kill={questId=101,objective=kill},
    loot={questId=102,objective=loot},
    starter={questId=103,type='itemFromMonster',name='Available quest'},
}
player.currentQuestlog[101]=101
MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questBag:IsShown(),'An unaccepted loot quest must not count')
assert(record.frame.questKill:IsShown(),'An accepted kill objective must show the knife')
assert(record.frame.questKill.texture==Questie.icons.slay)
player.currentQuestlog[102]=102
MOCK.event('QUEST_ACCEPTED')
assert(record.frame.questBag:IsShown(),'Accepted incomplete item objective must show a bag')
assert(record.frame.questKill:IsShown() and record.frame.questBag.texture==Questie.icons.loot)
local point,relative,relativePoint,x,y=record.frame.questBag:GetPoint()
assert(point=='RIGHT' and relative==record.frame.bar and relativePoint=='LEFT' and x==-4 and y==0)
local bx,by,bw,bh=MOCK.worldRect(record.frame.bar)
local ix,iy,iw,ih=MOCK.worldRect(record.frame.questBag)
assert(iw==16 and ih==16 and ix+iw==bx-4 and math.abs(iy+ih/2-by-bh/2)<.01)
local kx,ky,kw,kh=MOCK.worldRect(record.frame.questKill)
assert(kw==16 and kh==16 and kx+kw==ix-2 and math.abs(ky+kh/2-by-bh/2)<.01,
    'Knife and bag must fit side by side to the left of the health bar')
assert(not record.frame.mouse and not record.frame.bar.mouse)

MOCK.lootComplete=true;MOCK.event('BAG_UPDATE_DELAYED')
assert(not record.frame.questBag:IsShown(),'Completion hides loot even while the kill objective remains')
assert(record.frame.questKill:IsShown())
kx,ky,kw,kh=MOCK.worldRect(record.frame.questKill)
assert(kx+kw==bx-4,'A lone knife must sit next to the bar')
kill.Completed=true;MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questKill:IsShown(),'Completed kills must hide the knife')
kill.Completed=false
MOCK.lootComplete=false;MOCK.event('QUEST_LOG_UPDATE')
assert(record.frame.questBag:IsShown(),'Losing a needed item restores the marker')
player.currentQuestlog[102]=nil;MOCK.event('QUEST_REMOVED')
assert(not record.frame.questBag:IsShown(),'Abandoning removes the marker')

-- A native quest log index, when available, overrides a stale Questie registry.
player.currentQuestlog[102]=102
local active=false
GetQuestLogIndexByID=function(id)return active and id==102 and 1 or 0 end
MOCK.event('QUEST_LOG_UPDATE');assert(not record.frame.questBag:IsShown())
active=true;MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questBag:IsShown())
GetQuestLogIndexByID=nil
C_QuestLog={GetLogIndexForQuestID=function(id)return active and id==102 and 1 or nil end}
active=false;MOCK.event('QUEST_LOG_UPDATE');assert(not record.frame.questBag:IsShown())
active=true;MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questBag:IsShown())

-- Several item objectives may share one mob; completing only one must keep the bag.
tooltips.lookupByKey.m_1234.other={questId=102,objective={Type='item',Icon=2,Completed=false}}
MOCK.lootComplete=true;MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questBag:IsShown())
tooltips.lookupByKey.m_1234.other.objective.Completed=true
MOCK.event('QUEST_LOG_UPDATE');assert(not record.frame.questBag:IsShown())

-- Do not infer loot from unknown/private data or a generic kill/talk objective.
SECRET=setmetatable({}, {__index=function()error('Secret field read')end})
function issecretvalue(v)return rawequal(v,SECRET)end
tooltips.lookupByKey.m_1234={secret=SECRET,unknown={questId=102,objective={Type='item',Completed=SECRET}}}
MOCK.event('QUEST_LOG_UPDATE');assert(not record.frame.questBag:IsShown())
tooltips.lookupByKey.m_1234={unknown={questId=102,objective={Type='item'}}}
MOCK.event('QUEST_LOG_UPDATE');assert(not record.frame.questBag:IsShown())
assert(not A.QuestLoot.GetIcons(SECRET,GetTime()))
assert(not A.QuestLoot.GetIcons('Player-0-123-0-1-1234-0001',GetTime()))

-- Noncombat quest interactions must not turn into kill targets.
tooltips.lookupByKey.m_1234={talk={questId=102,objective={Type='monster',Icon=5,Completed=false}}}
MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questBag:IsShown() and not record.frame.questKill:IsShown())

-- Use Questie's configured assets, including its pfquest theme behavior.
tooltips.lookupByKey.m_1234={loot={questId=102,objective=loot},kill={questId=102,objective=kill}}
MOCK.lootComplete=false
Questie.db={profile={ICON_LOOT=123456,ICON_SLAY='CustomKnife'}}
MOCK.event('QUEST_LOG_UPDATE')
assert(record.frame.questBag.texture==123456 and record.frame.questKill.texture=='CustomKnife')
Questie.db.profile.iconTheme='pfquest';MOCK.advance(.6)
assert(record.frame.questBag.texture==Questie.icons.loot and record.frame.questKill.texture==Questie.icons.slay)
Questie.db=nil

tooltips.lookupByKey.m_1234={loot={questId=102,objective=loot}}
MOCK.lootComplete=false;MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questBag:IsShown())
MOCK.hit('nameplate1');A.Update(false)
bx,by,bw,bh=MOCK.worldRect(record.frame.bar)
ix,iy,iw,ih=MOCK.worldRect(record.frame.questBag)
assert(ix+iw==bx-4 and math.abs(iy+ih/2-by-bh/2)<.01,'Bag must follow priority height')

-- Late Questie updates converge on the existing timer without requiring a new nameplate.
MOCK.lootComplete=true;MOCK.advance(.6)
assert(not record.frame.questBag:IsShown())
MOCK.lootComplete=false;MOCK.advance(.6)
assert(record.frame.questBag:IsShown())
MOCK.remove('nameplate1')
local other=MOCK.mob('nameplate2','Creature-0-123-0-1-9999-0000000002','Other mob',plate)
assert(not A.units.nameplate2.frame.questBag:IsShown(),'Pooled frames must not retain a bag')
assert(not A.units.nameplate2.frame.questKill:IsShown(),'Pooled frames must not retain a knife')
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
''')
print('Quest marker checks passed: kill/loot objectives, progress/abandon, Questie textures, late updates, geometry, pooling and private-data guards. Simulated APIs only.')
