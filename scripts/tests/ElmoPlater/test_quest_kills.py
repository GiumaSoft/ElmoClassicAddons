"""Native quest kills only: progress, exact names, localization and Era headers."""
from fixture import create_vm

vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
local rows={
    [101]={{text='0/6 Rockjaw Skullthumper slain',type='monster',finished=false,numFulfilled=0,numRequired=6}},
    [102]={{text='Crocolisk Meat: 0/5',type='item',finished=false,numFulfilled=0,numRequired=5}},
    [103]={{text='Guard Thomas spoken to: 0/1',type='monster',finished=false,numFulfilled=0,numRequired=1}},
    [104]={{text='Rockjaw Skullthumper slain: 0/1',type='monster',finished=false,numFulfilled=0,numRequired=1}},
}
local active={101,102,103}
local completed={}
local reads=0
C_QuestLog={
    GetInfo=function(i)
        if i==1 then return {isHeader=true,isCollapsed=true,title='Dun Morogh'} end
        local id=active[i-1]
        if id then return {isHeader=false,questID=id,title='Quest '..id} end
    end,
    GetQuestObjectives=function(id)reads=reads+1;return rows[id] end,
    IsComplete=function(id)return completed[id]==true end,
}
GetNumQuestLogEntries=function()error('Modern API must not expand or read legacy headers')end
QuestieLoader=setmetatable({}, {__index=function()error('Questie must not be read')end})
Questie=setmetatable({}, {__index=function()error('Questie must not be read')end})
MOCK.start()
local guid='Creature-0-123-0-1-1234-0000000001'
local mob,plate=MOCK.mob('nameplate1',guid,'Rockjaw Skullthumper')
local record=A.units.nameplate1
assert(record.frame.questBag==nil,'The bag must no longer be created')
assert(record.frame.questKill:IsShown(),'An unfinished native kill must show a knife without Questie')
assert(record.frame.questKill.texture=='Interface\\Icons\\INV_Weapon_ShortBlade_05')
local other=MOCK.mob('nameplate2','Creature-other','Crocolisk')
assert(not A.units.nameplate2.frame.questKill:IsShown(),'Item drops must not show a knife')
other=MOCK.mob('nameplate3','Creature-talk','Guard Thomas')
assert(not A.units.nameplate3.frame.questKill:IsShown(),'Talk objectives are not kills')
other=MOCK.mob('nameplate4','Creature-longer','Elder Rockjaw Skullthumper')
assert(not A.units.nameplate4.frame.questKill:IsShown(),'Names must match exactly, never as substrings')
assert(reads==3,'All plates must share one quest snapshot')

local function geometry()
    local bx,by,bw,bh=MOCK.worldRect(record.frame.bar)
    local ix,iy,iw,ih=MOCK.worldRect(record.frame.questKill)
    assert(iw==16 and ih==16 and ix+iw==bx-4 and math.abs(iy+ih/2-by-bh/2)<.01)
    assert(not record.frame.mouse and not record.frame.bar.mouse)
end
geometry()
A.Update(false);geometry()
assert(reads==3,'Repeated rendering must reuse the snapshot')
rows[101][1].finished=true
MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questKill:IsShown(),'Completing an objective must hide it immediately')
rows[101][1].finished=false;rows[101][1].numFulfilled=6
MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questKill:IsShown(),'Complete public counts override a stale finished flag')
rows[101][1].numFulfilled=0;rows[101][1].text='6/6 Rockjaw Skullthumper slain'
MOCK.event('QUEST_LOG_UPDATE')
assert(not record.frame.questKill:IsShown(),'Completed text also overrides stale counts')
rows[101][1].text='Rockjaw Skullthumper slain: 0/6'
MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questKill:IsShown())
completed[101]=true
MOCK.event('QUEST_AUTOCOMPLETE');assert(not record.frame.questKill:IsShown())
completed[101]=false
-- Two quests can require the same creature; finishing only one must keep it.
active[4]=104;rows[101][1].finished=true
MOCK.event('QUEST_ACCEPTED');assert(record.frame.questKill:IsShown())
active[4]=nil
MOCK.event('QUEST_REMOVED');assert(not record.frame.questKill:IsShown())
active[1]=104
MOCK.event('QUEST_ACCEPTED');assert(record.frame.questKill:IsShown())
active[1]=nil
MOCK.event('QUEST_TURNED_IN');assert(not record.frame.questKill:IsShown())
-- GetInfo stops at the first absent entry, as the real API does.
active={101,102,103};rows[101][1].finished=false
MOCK.event('QUEST_LOG_UPDATE');assert(record.frame.questKill:IsShown())
rows[101]=nil
MOCK.advance(.6);assert(not record.frame.questKill:IsShown(),'Unavailable objective data must hide stale markers')
rows[101]={{text='0/6 Rockjaw Skullthumper slain',type='monster',finished=false}}
MOCK.advance(.6);assert(record.frame.questKill:IsShown(),'Late data must retry without a new nameplate')
-- The slash command must apply immediately and persist without polling quests.
SlashCmdList.ELMOPLATER('questkills off')
assert(A.db.questKills==false and ElmoPlaterDB.questKills==false)
assert(not record.frame.questKill:IsShown(),'Disabling must hide existing knives immediately')
local disabledReads=reads
MOCK.event('QUEST_LOG_UPDATE');MOCK.advance(1)
assert(reads==disabledReads,'Disabled markers must not poll the quest log')
SlashCmdList.ELMOPLATER('questkills')
SlashCmdList.ELMOPLATER('questkills invalid')
assert(A.db.questKills==false and reads==disabledReads,'Status and invalid input must preserve the setting')
rows[101][1].finished=true
SlashCmdList.ELMOPLATER('QUESTKILLS ON')
assert(A.db.questKills==true and not record.frame.questKill:IsShown(),'Enabling must refresh current progress')
rows[101][1].finished=false
SlashCmdList.ELMOPLATER('questkills off');SlashCmdList.ELMOPLATER('questkills on')
assert(record.frame.questKill:IsShown(),'Enabling must restore an eligible knife immediately')
MOCK.remove('nameplate1')
MOCK.mob('nameplate5','Creature-pooled','Other mob',plate)
assert(not A.units.nameplate5.frame.questKill:IsShown(),'Pooled frames must not retain a knife')
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
''')

vm, _ = create_vm()
vm.execute(r'''
local row={type='monster',finished=false,numFulfilled=0,numRequired=3}
C_QuestLog={GetInfo=function(i)if i==1 then return {questID=101,isHeader=false} end end,
    GetQuestObjectives=function()return {row}end}
local guid='Creature-native'
local function check(format,wording,name,expected)
    QUEST_MONSTERS_KILLED=format;row.text=wording
    A.QuestKills.Invalidate(true)
    assert((A.QuestKills.GetTexture(guid,name,GetTime())~=nil)==expected,wording)
end
check('%s slain: %d/%d','Rockjaw Skullthumper slain: 0/3','Rockjaw Skullthumper',true)
check('%s slain: %d/%d','0/3 Rockjaw Skullthumper slain','Rockjaw Skullthumper',true)
check('%d/%d %s slain','Rockjaw Skullthumper slain: 0/3','Rockjaw Skullthumper',true)
check('%2$d/%3$d %1$s slain','0/3 Rockjaw Skullthumper slain','Rockjaw Skullthumper',true)
check('%s uccisi: %d/%d','0/3 Lupo uccisi','Lupo',true)
check('%s slain: %d/%d',"Mug'lash (Elite) slain: 0/3","Mug'lash (Elite)",true)
check('%s slain: %d/%d','|cffff0000Rockjaw Skullthumper|r slain: 0/3','Rockjaw Skullthumper',true)
check('%s slain: %d/%d','Rockjaw Skullthumper slain','Rockjaw Skullthumper',true)
check('%s slain: %d/%d','Rockjaw Skullthumper slain: 0/3','rockjaw skullthumper',true)
check('%s slain: %d/%d','Troggs slain: 0/3','Rockjaw Skullthumper',false)
check('%s slain: %d/%d','Rockjaw Skullthumper spoken to: 0/3','Rockjaw Skullthumper',false)
check('%s slain: %d/%d','0/0 Rockjaw Skullthumper slain','Rockjaw Skullthumper',false)
check('%s slain: %d/%d','3/3 Rockjaw Skullthumper slain','Rockjaw Skullthumper',false)
check('%s slain: %d/%d','0/3 Rockjaw Skullthumper slain','Rockjaw Skullthumper',true)
assert(not A.QuestKills.GetTexture('Player-native','Rockjaw Skullthumper',GetTime()))
assert(A.QuestKills.GetTexture('Vehicle-native','Rockjaw Skullthumper',GetTime()))
QUEST_MONSTERS_KILLED=nil;A.QuestKills.Invalidate()
assert(not A.QuestKills.GetTexture(guid,'Rockjaw Skullthumper',GetTime()),'Missing localization must not guess')
''')

vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
local headers={{name='Elwynn',closed=true,quests={101}},{name='Dun Morogh',closed=false,quests={102}}}
local rows={
    [101]={{text='Wolf slain: 0/3',type='monster',finished=false,numFulfilled=0,numRequired=3}},
    [102]={{text='Boar slain: 0/3',type='monster',finished=false,numFulfilled=0,numRequired=3}},
}
local selected,expansions,collapses=3,0,0
local function log()
    local result={}
    for _,header in ipairs(headers) do
        result[#result+1]={header=header}
        if not header.closed then for _,id in ipairs(header.quests) do result[#result+1]={id=id} end end
    end
    return result
end
function GetNumQuestLogEntries()return #log(),2 end
function GetQuestLogTitle(index)
    local info=log()[index]
    if info.header then return info.header.name,nil,nil,true,info.header.closed,nil,nil,0 end
    return 'Quest '..info.id,nil,nil,false,false,nil,nil,info.id
end
function GetQuestLogSelection()return selected end
function SelectQuestLogEntry(index)selected=index end
function ExpandQuestHeader(index)
    assert(index==0);expansions=expansions+1
    for _,header in ipairs(headers)do header.closed=false end
    selected=1;MOCK.event('QUEST_LOG_UPDATE')
end
function CollapseQuestHeader(index)
    local header=assert(log()[index].header)
    collapses=collapses+1;header.closed=true;MOCK.event('QUEST_LOG_UPDATE')
end
C_QuestLog={GetQuestObjectives=function(id)return rows[id]end}
MOCK.start()
MOCK.mob('nameplate1','Creature-wolf','Wolf')
MOCK.mob('nameplate2','Creature-boar','Boar')
local knife=A.units.nameplate1.frame.questKill
assert(knife:IsShown() and A.units.nameplate2.frame.questKill:IsShown())
assert(headers[1].closed and not headers[2].closed and selected==3,'Preserve header state and selection')
assert(expansions==1 and collapses==1,'Reentrant quest events must not repeat the expansion')
rows[101][1].finished=true;MOCK.event('QUEST_LOG_UPDATE')
assert(not knife:IsShown() and expansions==1,'Progress must refresh by ID without opening headers again')
rows[101][1].finished=false;MOCK.advance(.6)
assert(knife:IsShown() and expansions==1,'Periodic retries must reuse hidden quest IDs')
headers[1].quests={103};rows[103]={{text='Bear slain: 0/2',type='monster',finished=false}}
MOCK.event('QUEST_REMOVED')
assert(not knife:IsShown() and expansions==2,'A hidden quest replacement must invalidate IDs')
headers[1].quests={101};MOCK.event('QUEST_ACCEPTED');assert(knife:IsShown())
assert(headers[1].closed and not headers[2].closed and selected==3)
MOCK.event('PLAYER_ENTERING_WORLD')
assert(headers[1].closed and not headers[2].closed and selected==3)
''')

vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
local secret=setmetatable({}, {__index=function()error('Private field read')end,
    __tostring=function()error('Private conversion')end,__eq=function()error('Private comparison')end})
function issecretvalue(value)return rawequal(value,secret)end
local private={}
function issecrettable(value)return rawequal(value,private)end
local row={type='monster',finished=false,text='Wolf slain: 0/2',numFulfilled=0,numRequired=2}
local info={questID=101,isHeader=false}
local rows={row}
local completion=false
C_QuestLog={GetInfo=function(i)if i==1 then return info end end,
    GetQuestObjectives=function()return rows end,IsComplete=function()return completion end}
local guid='Creature-wolf'
local function shown()
    A.QuestKills.Invalidate(true)
    return A.QuestKills.GetTexture(guid,'Wolf',GetTime())~=nil
end
assert(shown())
for _,key in ipairs({'type','text','finished','numFulfilled','numRequired'})do
    local old=row[key];row[key]=secret;assert(not shown(),key);row[key]=old
end
local old=rows;rows=secret;assert(not shown());rows=private;assert(not shown());rows=old
rows={secret};assert(not shown());rows=old
info.questID=secret;assert(not shown());info.questID=101
for _,key in ipairs({'isHeader','isComplete','isFailed'})do
    local old=info[key];info[key]=secret;assert(not shown(),key);info[key]=old
end
completion=secret;assert(not shown());completion=false
row.finished=nil;assert(not shown());row.finished=false
C_QuestLog.GetQuestObjectives=function()error('Unavailable API')end
assert(not shown(),'API failures must hide markers')
assert(not A.QuestKills.GetTexture(secret,'Wolf',GetTime()))
assert(not A.QuestKills.GetTexture(guid,secret,GetTime()))
''')

vm, _ = create_vm()
vm.execute(r'''
ElmoPlaterDB={questKills=false}
local reads=0
C_QuestLog={GetInfo=function()reads=reads+1 end}
MOCK.start()
MOCK.mob('nameplate1','Creature-wolf','Wolf')
MOCK.advance(1)
assert(A.db.questKills==false,'A saved disabled setting must survive initialization')
assert(not A.units.nameplate1.frame.questKill:IsShown() and reads==0)
''')
print('Native kill marker checks passed: no Questie or bags, progress, exact names, localized layouts, shared cache, Era headers, pooling, private-data guards and persistent enable/disable commands. Simulated APIs only.')
