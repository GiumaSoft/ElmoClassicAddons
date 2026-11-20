"""Native quest kills only: progress, exact names, localization and Era headers."""
from pathlib import Path
import os

from lupa.lua51 import LuaRuntime


HERE = Path(__file__).resolve().parent
ADDON = Path(os.environ.get("ELMO_TEST_ADDON", HERE.parents[2] / "ElmoLeveling"))


def create_vm():
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute((HERE / "wow_mock.lua").read_text())
    namespace = vm.table()
    vm.globals().A = namespace
    load = vm.eval('function(s, name, ns) assert(loadstring(s, "@" .. name))("ElmoLeveling", ns) end')
    for name in (ADDON / "ElmoLeveling.toc").read_text().splitlines():
        if name.endswith(".lua") and not name.startswith("Libs"):
            load((ADDON / name.replace("\\", "/")).read_text(), name, namespace)
    vm.execute(r'''
local methods = getmetatable(UIParent).__index
local setPoint = methods.SetPoint
function methods:SetPoint(point, relative, ...)
    if type(relative)=='table' and relative.restrictLayout then
        assert(self.template=='DisableUntrustedLayoutScriptsTemplate', 'Restricted aura layout anchor')
    end
    setPoint(self, point, relative, ...)
end
function methods:SetGradient() end
function methods:SetBlendMode() end
function methods:SetParent(parent) self.parent = parent end
function methods:SetAlpha(value) self.alpha = value end
function methods:GetEffectiveAlpha() return (self.alpha or 1) * (self.parent and self.parent:GetEffectiveAlpha() or 1) end
function methods:GetEffectiveScale() return (self.scale or 1) * (self.parent and self.parent:GetEffectiveScale() or 1) end
function methods:GetTop() return self.mockTop or 900 end
function methods:GetWidth() return self.width end
function methods:SetBackdrop(value) self.backdrop = value end
function methods:GetCenter() return self.x, self.y end
function methods:SetRotation(angle) self.rotation = angle end
function methods:IsForbidden() return self.forbidden == true end
function methods:SetMouseMotionEnabled(value) self.mouseMotion = value end
function methods:SetMouseClickEnabled(value) self.mouseClick = value end
function methods:SetAtlas(value) self.atlas = value end
function GameTooltip:SetOwner(owner, anchor) self.owner, self.anchor, self.lines = owner, anchor, {} end
C_Texture = {GetAtlasInfo = function(atlas) if atlas == 'QuestNormal' then return {} end end}
function CreateColor(...) return {...} end
local plates = {}
C_NamePlate = {
    GetNamePlateForUnit = function(unit)
        assert(unit:match('^nameplate%d+$'), 'Mob markers must use nameplate tokens')
        local plate = plates[unit]
        if plate and not plate.listOnly then return plate end
    end,
    GetNamePlates = function()
        local result = {}
        for _, plate in pairs(plates) do result[#result + 1] = plate end
        return result
    end
}
local add = MOCK.mob
function MOCK.mob(unit, guid, name, plate)
    local mob = add(unit, name, 8, guid)
    plate = plate or CreateFrame('Frame', nil, UIParent)
    plate.unitToken = unit
    plates[unit] = plate
    if not plate.listOnly then
        MOCK.event('NAME_PLATE_UNIT_ADDED', unit)
        A.QuestMarkers.Update()
    end
    return mob, plate
end
function MOCK.remove(unit)
    plates[unit], MOCK.units[unit] = nil, nil
    MOCK.event('NAME_PLATE_UNIT_REMOVED', unit)
end
local function marker(anchor, texture)
    for _, frame in ipairs(MOCK.frames) do
        if frame.icon and frame.icon.texture == texture and frame.anchor == anchor then return frame end
    end
end
function MOCK.knife(anchor)
    return marker(anchor, 'Interface\\Icons\\INV_Weapon_ShortBlade_05')
end
function MOCK.bag(anchor)
    return marker(anchor, 'Interface\\Icons\\INV_Misc_Bag_08')
end
function MOCK.questMarker(anchor)
    for _, frame in ipairs(MOCK.frames) do
        if frame.kind == "Frame" and not frame.count and frame.anchor == anchor then return frame end
    end
end
''')
    return vm, namespace


vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
local rows={
    [101]={{text='0/6 Rockjaw Skullthumper slain',type='monster',finished=false,numFulfilled=0,numRequired=6}},
    [102]={{text='Crocolisk Meat: 0/5',type='item',finished=false,numFulfilled=0,numRequired=5}},
    [103]={{text='Guard Thomas spoken to: 0/1',type='monster',finished=false,numFulfilled=0,numRequired=1}},
    [104]={{text='Rockjaw Skullthumper slain: 0/1',type='monster',finished=false,numFulfilled=0,numRequired=1}},
    [105]={{text='Stonejaw Trogg slain: 1/4',type='monster',finished=false,numFulfilled=1,numRequired=4}},
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
C_XMLUtil={GetTemplateInfo=function(name)
    if name=='DisableUntrustedLayoutScriptsTemplate' then return {} end
end}
MOCK.start()
local guid='Creature-0-123-0-1-1234-0000000001'
local mob,plate=MOCK.mob('nameplate1',guid,'Rockjaw Skullthumper')
local knife = assert(MOCK.knife(plate))
assert(knife:IsShown() and knife.count:GetText() == '0/6')
local questMarker=assert(MOCK.questMarker(plate))
assert(questMarker:IsShown() and questMarker.point[2]==plate and questMarker.point[1]=='BOTTOM' and questMarker.point[3]=='TOP')
assert(questMarker.point[4]==0 and not questMarker.mouseEnabled)
local markerTextures = 0
for _, region in ipairs(MOCK.frames) do
    if region.parent==questMarker and region.kind=='Texture' then
        markerTextures = markerTextures + 1
        assert(region.atlas=='QuestNormal' and region.width==32 and region.height==32)
    end
end
assert(markerTextures==1, 'The nameplate marker is only the large quest icon')
plate.alpha=.25; A.QuestMarkers.Update()
assert(questMarker.alpha>=.88,'Keep the marker bright on dimmed plates')
plate.alpha=1; A.QuestMarkers.Update()
A.db.questMobBeam=false; A.QuestMarkers.Update()
assert(knife.icon:IsShown() and not questMarker:IsShown())
A.db.questMobBeam=true; A.db.questMobMarks=false; A.QuestMarkers.Update()
assert(not knife:IsShown() and questMarker:IsShown())
A.db.questMobMarks=true; A.QuestMarkers.Update()
local questieReady=false
C_AddOns.IsAddOnLoaded=function(addon)
    if addon=='Questie' then return questieReady, questieReady end
    return false,false
end
for _, loaded in ipairs({false,true,false}) do
    questieReady=loaded; A.QuestMarkers.Update()
    assert(knife:IsShown() and knife.icon:IsShown() and knife.count:GetText()=='0/6' and questMarker:IsShown())
    assert(knife.point[1]=='LEFT' and knife.point[3]=='RIGHT','Keep the badge on the right with or without Questie')
end
assert(A.db.questMobMarks and A.db.questMobBeam,'Questie must not change the saved options')
local _, secondPlate=MOCK.mob('nameplate6','Creature-second','Rockjaw Skullthumper')
local secondMarker=assert(MOCK.questMarker(secondPlate))
assert(questMarker:IsShown() and secondMarker:IsShown() and questMarker~=secondMarker,'Every matching nameplate gets its own marker')
MOCK.remove('nameplate6')
assert(questMarker:IsShown() and not secondMarker:IsShown(),'Removing one plate hides just its marker')
local _, itemPlate=MOCK.mob('nameplate2','Creature-other','Crocolisk')
assert(not MOCK.knife(itemPlate),'Item drops must not show a knife')
local _, talkPlate=MOCK.mob('nameplate3','Creature-talk','Guard Thomas')
assert(not MOCK.knife(talkPlate),'Talk objectives are not kills')
local _, elderPlate=MOCK.mob('nameplate4','Creature-longer','Elder Rockjaw Skullthumper')
assert(not MOCK.knife(elderPlate),'Names must match exactly, never as substrings')
assert(reads==3,'All plates must share one quest snapshot')

assert(knife.point[1]=='LEFT' and knife.point[2]==plate and knife.point[3]=='RIGHT' and knife.point[4]==8)
assert(not knife.mouseEnabled)
local health=CreateFrame('StatusBar',nil,UIParent)
local upper=CreateFrame('Frame',nil,UIParent)
upper.restrictLayout=true
local display=CreateFrame('Frame',nil,UIParent)
display.scale,display.alpha=.65,.8
local levelBadge=CreateFrame('Frame',nil,display)
levelBadge:SetSize(24,24)
local timerClearance=14
upper.GetTop=function() error('Do not read the secret location of the aura container') end
ElmoPlater={GetHealthAnchor=function(unit,native,guid)
    if unit=='nameplate1' and native==plate and guid==mob.guid then return health,upper,timerClearance,levelBadge end
end}
A.QuestMarkers.Update()
assert(knife.point[2]==levelBadge and knife:IsShown(),'Use the level badge even without Questie')
assert(knife.width==24 and knife.height==24 and knife.backdrop.edgeSize==8,'Match the framed level badge')
assert(knife.icon.width==24*.65 and knife.icon.height==knife.icon.width and knife.icon.point[1]=='CENTER')
assert(knife:GetEffectiveScale()==levelBadge:GetEffectiveScale() and knife:GetEffectiveAlpha()==levelBadge:GetEffectiveAlpha())
display.scale=.8
assert(knife:GetEffectiveScale()==.8,'The knife scales with the level even between marker updates')
assert(questMarker.template=='DisableUntrustedLayoutScriptsTemplate' and questMarker.point[2]==upper and
    questMarker.point[3]=='TOP' and questMarker.point[4]==0 and questMarker.point[5]==20,
    'Anchor to the top of Plater aura rows without reading their geometry')
questieReady=true;timerClearance=20
A.QuestMarkers.Update()
assert(knife.point[1]=='LEFT' and knife.point[2]==levelBadge and knife.point[3]=='RIGHT' and knife.point[4]==8,
    'Keep the badge beside the level when Questie is loaded')
assert(knife.icon:IsShown() and knife.count:GetText()=='0/6' and questMarker.point[5]==26)
questieReady=false
ElmoPlater=nil
local native=CreateFrame('Frame',nil,plate)
plate.UnitFrame=native
native.healthBar=health
health.mockTop=105
native.name=native:CreateFontString(); native.name.mockTop=117
native.AurasFrame=CreateFrame('Frame',nil,native)
local debuffs=CreateFrame('Frame',nil,native.AurasFrame)
native.AurasFrame.DebuffListFrame=debuffs
debuffs.mockTop,debuffs.scale=80,2
A.QuestMarkers.Update()
assert(knife.point[2]==health and knife.point[1]=='LEFT','Fall back to the right of the native health bar')
assert(knife:GetParent()==UIParent and knife:GetEffectiveScale()==1,'Release ElmoPlater scale when its display goes away')
assert(questMarker.point[2]==health and questMarker.point[4]==0 and questMarker.point[5]==61,
    'Clear a scaled native aura row while keeping the horizontal center on the bar')
debuffs:Hide(); A.QuestMarkers.Update()
assert(questMarker.point[5]==18,'The marker drops to just above the name when the auras disappear')
plate.UnitFrame=nil; A.QuestMarkers.Update()
assert(reads==3,'Repeated rendering must reuse the snapshot')
active[4]=105; MOCK.event('QUEST_ACCEPTED')
local _, troggPlate=MOCK.mob('nameplate6','Creature-trogg','Stonejaw Trogg')
local otherMarker=assert(MOCK.questMarker(troggPlate))
assert(questMarker:IsShown() and otherMarker:IsShown(),'An unwatched quest also gets a marker')
active[4]=nil; MOCK.event('QUEST_REMOVED')
assert(questMarker:IsShown() and not otherMarker:IsShown())
MOCK.remove('nameplate6')
rows[101][1].finished=true
MOCK.event('QUEST_LOG_UPDATE')
assert(not knife:IsShown(),'Completing an objective must hide it immediately')
assert(not questMarker:IsShown(),'Completing the quest objective also hides the mob marker')
rows[101][1].finished=false;rows[101][1].numFulfilled=6
MOCK.event('QUEST_LOG_UPDATE')
assert(not knife:IsShown(),'Complete public counts override a stale finished flag')
rows[101][1].numFulfilled=0;rows[101][1].text='6/6 Rockjaw Skullthumper slain'
MOCK.event('QUEST_LOG_UPDATE')
assert(not knife:IsShown(),'Completed text also overrides stale counts')
rows[101][1].text='Rockjaw Skullthumper slain: 0/6'
MOCK.event('QUEST_LOG_UPDATE');assert(knife:IsShown())
completed[101]=true
MOCK.event('QUEST_AUTOCOMPLETE');assert(not knife:IsShown())
completed[101]=false
-- Two quests can require the same creature; finishing only one must keep it.
active[4]=104;rows[101][1].finished=true
MOCK.event('QUEST_ACCEPTED');assert(knife:IsShown())
active[4]=nil
MOCK.event('QUEST_REMOVED');assert(not knife:IsShown())
active[1]=104
MOCK.event('QUEST_ACCEPTED');assert(knife:IsShown())
active[1]=nil
MOCK.event('QUEST_TURNED_IN');assert(not knife:IsShown())
-- GetInfo stops at the first absent entry, as the real API does.
active={101,102,103};rows[101][1].finished=false
MOCK.event('QUEST_LOG_UPDATE');assert(knife:IsShown())
rows[101]=nil
MOCK.advance(.6);assert(not knife:IsShown(),'Unavailable objective data must hide stale markers')
rows[101]={{text='0/6 Rockjaw Skullthumper slain',type='monster',finished=false}}
MOCK.advance(.6);assert(knife:IsShown(),'Late data must retry without a new nameplate')
-- The slash command must apply immediately and persist without polling quests.
SlashCmdList.ELMOLEVELING('questkills off')
assert(A.db.questMobMarks==false and ElmoLevelingDB.questMobMarks==false)
assert(not knife:IsShown(),'Disabling must hide existing knives immediately')
local disabledReads=reads
MOCK.event('QUEST_LOG_UPDATE');MOCK.advance(1)
assert(reads==disabledReads,'Disabled markers must not poll the quest log')
SlashCmdList.ELMOLEVELING('questkills')
SlashCmdList.ELMOLEVELING('questkills invalid')
assert(A.db.questMobMarks==false and reads==disabledReads,'Status and invalid input must preserve the setting')
rows[101][1].finished=true
SlashCmdList.ELMOLEVELING('QUESTKILLS ON')
assert(A.db.questMobMarks==true and not knife:IsShown(),'Enabling must refresh current progress')
rows[101][1].finished=false
SlashCmdList.ELMOLEVELING('questkills off');SlashCmdList.ELMOLEVELING('questkills on')
assert(knife:IsShown(),'Enabling must restore an eligible knife immediately')
MOCK.remove('nameplate1')
MOCK.mob('nameplate5','Creature-pooled','Other mob',plate)
assert(not MOCK.knife(plate),'Pooled frames must not retain a knife')
assert(not knife:IsShown())
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
    assert((A.QuestKills.GetObjective(guid,name,GetTime())~=nil)==expected,wording)
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
assert(not A.QuestKills.GetObjective('Player-native','Rockjaw Skullthumper',GetTime()))
assert(A.QuestKills.GetObjective('Vehicle-native','Rockjaw Skullthumper',GetTime()))
QUEST_MONSTERS_KILLED=nil;A.QuestKills.Invalidate()
assert(not A.QuestKills.GetObjective(guid,'Rockjaw Skullthumper',GetTime()),'Missing localization must not guess')
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
local _, wolfPlate=MOCK.mob('nameplate1','Creature-wolf','Wolf')
local _, boarPlate=MOCK.mob('nameplate2','Creature-boar','Boar')
local knife=assert(MOCK.knife(wolfPlate))
assert(knife:IsShown() and MOCK.knife(boarPlate):IsShown())
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
    return A.QuestKills.GetObjective(guid,'Wolf',GetTime())~=nil
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
assert(not A.QuestKills.GetObjective(secret,'Wolf',GetTime()))
assert(not A.QuestKills.GetObjective(guid,secret,GetTime()))
''')

vm, _ = create_vm()
vm.execute(r'''
ElmoLevelingDB={questMobMarks=false,questCompass=false}
local reads=0
C_QuestLog={GetInfo=function()reads=reads+1 end}
MOCK.start()
local _, plate=MOCK.mob('nameplate1','Creature-wolf','Wolf')
MOCK.advance(1)
assert(not A.db.questMobMarks and not A.db.questMobBeam and not A.db.questArrow,
    'A saved disabled group setting must transfer to its new standalone controls')
assert(not MOCK.knife(plate) and reads==0)
''')
print('Native kill marker checks passed: centered markers above auras, Questie badge placement, all matching plates and unwatched quests, localization and pooling. Simulated APIs only.')

vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
Enum={TooltipDataLineType={QuestTitle=17,QuestObjective=8}}
local item={type='item',finished=false,text='Eldarath Relic: 6/12',numFulfilled=6,numRequired=12}
local kill={type='monster',finished=false,text='Spitelash Siren slain: 2/8',numFulfilled=2,numRequired=8}
local active, needsKill, done, reads=true,false,false,0
C_QuestLog={
    GetInfo=function(i)
        if i==1 and active then return {questID=88809} end
        if i==2 and active and needsKill then return {questID=101} end
    end,
    GetQuestObjectives=function(id) return id==88809 and {item} or {kill} end,
    IsComplete=function(id) return id==88809 and done end,
}
local title={type=17,id=88809,leftText='Preserving Eldarath'}
local objective={type=8,leftText='6/12 Eldarath Relic',numFulfilled=6,numRequired=12,completed=false}
local lines={title,objective}
C_TooltipInfo={GetUnit=function(unit)
    assert(unit:match('^nameplate%d+$'),'Quest item lookup must be independent of the target')
    reads=reads+1
    if unit=='nameplate1' then return {lines=lines} end
end}
MOCK.start()
local mob, plate=MOCK.mob('nameplate1','Creature-siren','Spitelash Siren')
local bag=assert(MOCK.bag(plate))
local questMarker=assert(MOCK.questMarker(plate))
assert(bag:IsShown() and bag.point[4]==8 and bag.count:GetText()=='6/12' and questMarker:IsShown() and not MOCK.knife(plate))
local restrictedAura=CreateFrame('Frame',nil,UIParent)
restrictedAura.restrictLayout=true
local display=CreateFrame('Frame',nil,UIParent)
display.scale=.8
local badge=CreateFrame('Frame',nil,display)
badge:SetSize(26,26)
ElmoPlater={GetHealthAnchor=function(unit, native)
    if unit=='nameplate1' then return native, restrictedAura, 14, badge end
end}
A.QuestMarkers.Update()
assert(questMarker:IsShown() and questMarker.point[2]==plate and questMarker.point[5]==68,
    'Fall back to the health bar if Blizzard rejects the aura anchor')
assert(bag.width==26 and bag.height==26 and bag.backdrop.edgeSize==8,'Frame size follows the level badge')
assert(bag.point[1]=='LEFT' and bag.point[2]==badge and bag.point[3]=='RIGHT','Put the bag immediately after the level')
assert(bag:GetEffectiveScale()==badge:GetEffectiveScale(),'The bag inherits the nameplate scale')
display.scale=.55
assert(bag:GetEffectiveScale()==.55,'The bag scales with the level even between marker updates')
badge:SetSize(32,32); A.QuestMarkers.Update()
assert(bag.width==32 and bag.height==32,'Resize existing bag markers when the badge changes')
assert(bag.icon.width==32*.65 and bag.icon.height==bag.icon.width and bag.icon.point[1]=='CENTER')
ElmoPlater=nil
A.QuestMarkers.Update()
local count=reads
A.QuestMarkers.Update()
assert(reads==count,'Reuse the tooltip lookup between quest snapshots')
local _, unrelated=MOCK.mob('nameplate2','Creature-other','Spitelash Siren')
assert(not MOCK.bag(unrelated) and not MOCK.questMarker(unrelated),
    'A similarly named mob needs its own native association')

needsKill=true; MOCK.event('QUEST_ACCEPTED')
local knife=assert(MOCK.knife(plate))
assert(knife:IsShown() and bag:IsShown() and bag.point[2]==knife and questMarker:IsShown(),
    'Keep both badges and one overhead marker on dual-purpose mobs')

objective.completed=true
MOCK.advance(.6)
assert(not bag:IsShown() and questMarker:IsShown() and knife:IsShown(),
    'Completed tooltip rows hide the bag even before the quest log updates')
objective.completed=false
needsKill=false; MOCK.event('QUEST_REMOVED')
assert(not knife:IsShown() and bag:IsShown() and questMarker:IsShown())

local function check(expected)
    MOCK.event('QUEST_LOG_UPDATE')
    assert(bag:IsShown()==expected and questMarker:IsShown()==expected)
end
local private={}
function issecretvalue(value) return rawequal(value,private) end
objective.leftText=private; check(false)
objective.leftText='6/12 Eldarath Relic'; check(true)
title.id=private; check(false)
title.id=88809
lines={title,{type=17,id=99999},objective}; check(false)
lines={title,objective}
objective.leftText='6/12 Other Relic'; check(false)
objective.leftText='6/12 Eldarath Relic'
item.type='object'; check(false)
item.type='item'
item.numFulfilled=12; check(false)
item.numFulfilled=6; check(true)
done=true; check(false)
done=false
active=false; check(false)
active=true; check(true)

A.db.questMobMarks=false; A.QuestMarkers.Update()
assert(not bag:IsShown() and questMarker:IsShown(),'With only the marker enabled, item objectives still qualify')
A.db.questMobMarks=true; A.QuestMarkers.Update()
assert(bag:IsShown() and questMarker:IsShown())
A.db.questMobBeam=false; A.QuestMarkers.Update()
assert(bag:IsShown() and not questMarker:IsShown())
A.db.questMobBeam=true; A.QuestMarkers.Update()
assert(bag:IsShown() and questMarker:IsShown())

MOCK.remove('nameplate1')
assert(not bag:IsShown() and not questMarker:IsShown())
lines={}
MOCK.mob('nameplate1','Creature-siren','Spitelash Siren',plate)
assert(not MOCK.bag(plate) and not MOCK.questMarker(plate),'A reused token must retest its tooltip')
''')
print('Native item marker checks passed: exact quest and objective association, independent options, completion, protected fields and token reuse.')

vm, _ = create_vm()
vm.execute(r'''
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
C_QuestLog={GetInfo=function(i) if i==1 then return {questID=101} end end,
    GetQuestObjectives=function() return {{text='Wolf slain: 0/3',type='monster',finished=false}} end}
local restricted={}
function issecretvalue(value) return rawequal(value, restricted) end
local readGUID, readName = UnitGUID, UnitName
function UnitGUID(unit)
    assert(unit~='target')
    if unit=='nameplate1' then return restricted end
    return readGUID(unit)
end
function UnitName(unit)
    assert(unit~='target')
    if unit=='nameplate1' then return restricted end
    return readName(unit)
end
local isPlayer, controlled = false, false
function UnitCanAttack(_, unit) return unit=='nameplate1' end
function UnitIsPlayer() return isPlayer end
function UnitPlayerControlled() return controlled end
MOCK.start()
local plate = CreateFrame('Frame', nil, UIParent)
plate.listOnly = true
plate.UnitFrame = CreateFrame('Frame', nil, plate)
plate.UnitFrame.name = plate.UnitFrame:CreateFontString()
plate.UnitFrame.name:SetText('Wolf')
MOCK.mob('nameplate1','Creature-wolf','Wolf',plate)
assert(not MOCK.questMarker(plate))
MOCK.advance(.6)
local questMarker=assert(MOCK.questMarker(plate))
assert(questMarker:IsShown(), 'An untargeted plate in the live list must get a marker without an add event')
isPlayer=true; A.QuestMarkers.Update()
assert(not questMarker:IsShown(), 'Never classify a player by a matching name')
isPlayer=false; controlled=true; A.QuestMarkers.Update()
assert(not questMarker:IsShown(), 'Never classify a player-controlled nameplate by name alone')
controlled=false; plate.UnitFrame.name:SetText(restricted); A.QuestMarkers.Update()
assert(not questMarker:IsShown(), 'Do not interpret a private name')
plate.UnitFrame.name:SetText('Wolf'); A.QuestMarkers.Update()
assert(questMarker:IsShown())
plate.unitToken='nameplate2'; A.QuestMarkers.Update()
assert(not questMarker:IsShown(), 'Do not reuse cached plates after Blizzard reassigns the token')
''')

vm, _ = create_vm()
vm.execute(r'''
local tracked, done, clamped, facing, otherTrack = 101, false, false, 0, false
local playerMap, publishedPins, nativePoint = nil, true, false
QUEST_MONSTERS_KILLED='%s slain: %d/%d'
local rows={
    [101]={{text='Wolf slain: 2/6',type='monster',finished=false}},
    [102]={{text='Boar slain: 0/4',type='monster',finished=false}},
}
local projection = CreateFrame('Frame', nil, UIParent)
projection.x, projection.y, projection.scale = 200, 90, .8
function CreateVector2D(x, y) return {GetXY=function() return x,y end} end
function GetPlayerFacing() return facing end
C_Map = {
    GetBestMapForUnit=function() return playerMap end,
    GetPlayerMapPosition=function(map, unit) assert(map==1 and unit=='player'); return CreateVector2D(.4,.5) end,
    GetWorldPosFromMapPos=function(map, vector)
        local x,y=vector:GetXY(); return map, CreateVector2D(x*1000,y*1000)
    end,
    SetUserWaypoint=function() error('Quest guidance must not move the native waypoint') end,
}
C_QuestLog = {
    GetInfo=function(i) if i<=2 then return {questID=100+i} end end,
    GetQuestObjectives=function(id) return rows[id] end,
    GetQuestsOnMap=function() if publishedPins then return {{questID=101,x=.6,y=.5},{questID=102,x=.5,y=.7}} end end,
    GetNumQuestWatches=function() return 1 end,
    GetQuestIDForQuestWatchIndex=function() return 102 end,
    GetNextWaypoint=function(id) if id==102 then return 1,.7,.5 end end,
    GetTitleForQuestID=function(id) return 'Quest '..id end,
    IsOnQuest=function() return true end,
    IsComplete=function(id) return id==101 and done end,
}
Enum = {SuperTrackingType={Quest=0}, NavigationState={InRange=2}}
C_SuperTrack = {
    GetSuperTrackedQuestID=function() return tracked end,
    IsSuperTrackingQuest=function() return true end,
    GetHighestPrioritySuperTrackingType=function() return otherTrack and 1 or 0 end,
    IsSuperTrackingUserWaypoint=function() return otherTrack end,
}
C_Navigation = {
    GetNextWaypointForMap=function() if nativePoint then return .7,.5 end end,
    HasValidScreenPosition=function() return true end,
    WasClampedToScreen=function() return clamped end,
    GetTargetState=function() return 2 end,
    GetDistance=function() return 243 end,
    GetFrame=function() return projection end,
}
MOCK.start(); MOCK.advance(.1)
local compass = ElmoLevelingQuestCompass
assert(compass:IsShown() and compass.band:IsShown() and compass.directions[1]:IsShown())
assert(not compass.arrow:IsShown(), 'The missing map must hide directions to quests, not the compass')
playerMap=1; MOCK.advance(.1)
local beam = ElmoLevelingQuestBeacon
assert(compass:IsShown() and beam:IsShown() and not compass.mouseEnabled and not beam.mouseEnabled)
assert(compass.title:GetText()=='Quest 101  ·  200 yd' and math.abs(compass.arrow.rotation)<.01)
assert(beam.title:GetText()=='Quest 101' and beam.distance:GetText()=='243 yd')
assert(beam.point[4]==160 and beam.point[5]==72)
local pin=compass.pins[1]
assert(pin:IsShown() and pin.icon.atlas=='QuestNormal' and pin.mouseMotion and pin.mouseClick==false)
pin:GetScript('OnEnter')(pin)
assert(GameTooltip:IsShown() and GameTooltip:GetText()=='Quest 101' and GameTooltip.lines[1]=='Wolf  2/6')
assert(GameTooltip.lines[2]=='Quest 102' and GameTooltip.lines[3]=='Boar  0/4')
pin:GetScript('OnLeave')(pin); assert(not GameTooltip:IsShown())
publishedPins=false; nativePoint=true; MOCK.event('QUEST_POI_UPDATE'); MOCK.advance(.1)
assert(compass.arrow:IsShown() and compass.title:GetText()=='Quest 101  ·  300 yd')
otherTrack=true; MOCK.event('SUPER_TRACKING_CHANGED'); MOCK.advance(.1)
assert(compass.band:IsShown() and not compass.arrow:IsShown(), 'A manual waypoint cannot provide the quest arrow')
otherTrack=false; nativePoint=false; publishedPins=true; MOCK.event('SUPER_TRACKING_CHANGED'); MOCK.advance(.1)
facing=math.pi/2; MOCK.advance(.1)
assert(math.abs(compass.arrow.rotation+math.pi/2)<.01)
clamped=true; MOCK.advance(.1); assert(not beam:IsShown() and compass:IsShown())
clamped=false; otherTrack=true; MOCK.advance(.1); assert(not beam:IsShown())
otherTrack=false; MOCK.advance(.1); assert(beam:IsShown())
done=true; MOCK.event('QUEST_LOG_UPDATE'); MOCK.advance(.1)
assert(not beam:IsShown() and compass.title:GetText():match('Quest 102'))
local inside
C_Minimap = {IsInsideQuestBlob=function(id) return id==inside end}
inside=102; MOCK.advance(.1)
assert(compass.band:IsShown() and not compass.arrow:IsShown())
inside=nil; MOCK.advance(.1)
assert(compass.arrow:IsShown() and compass.title:GetText():match('Quest 102'))

ElmoWaypointDB = {points={
    {mapID=1,x=.401,y=.5,title='Camp'},
    {mapID=2,x=.9,y=.5,title='Other continent'},
}, active=2, showArrow=false, showCoordinates=true, coordinatesLocked=true,
    coordinatesPosition={x=-200,y=100}, minimap={hide=true,minimapPos=45}}
MOCK.event('ADDON_LOADED','ElmoWaypoint')
local waypoints=A.Waypoints
assert(A.db.waypoints==waypoints.db and #waypoints.db.points==2 and waypoints.Current().title=='Other continent')
assert(waypoints.db.importedElmoWaypoint and waypoints.db.coordinatesLocked and waypoints.db.coordinatesPosition.x==-200)
assert(waypoints.db.minimap.hide and waypoints.db.minimap.minimapPos==45)
assert(not waypoints.Active() and #ElmoWaypointDB.points==2)
MOCK.event('PLAYER_LOGIN')
assert(SLASH_ELMOWAYPOINT1=='/way')
SlashCmdList.ELMOWAYPOINT('resume')
assert(compass.title:GetText():find('Different continent',1,true) and not compass.arrow:IsShown())
inside=102
SlashCmdList.ELMOWAYPOINT('60 50 Meeting point')
assert(compass.arrow:IsShown() and compass.title:GetText()=='Meeting point  ·  200 yd' and #waypoints.db.points==3)
assert(not ElmoWaypointArrow and not beam:IsShown())
SlashCmdList.ELMOWAYPOINT('pause')
assert(not compass.arrow:IsShown() and #waypoints.db.points==3)
inside=nil; MOCK.advance(.1)
assert(compass.title:GetText():match('Quest 102'))
SlashCmdList.ELMOWAYPOINT('next')
assert(compass.title:GetText()=='Camp  ·  Arrived' and not compass.arrow:IsShown())
MOCK.advance(1.3)
assert(not waypoints.Active() and waypoints.Current().title=='Camp' and #waypoints.db.points==3)
assert(compass.arrow:IsShown() and compass.title:GetText():match('Quest 102'))
SlashCmdList.ELMOWAYPOINT('remove')
MOCK.event('ADDON_LOADED','ElmoWaypoint')
assert(#waypoints.db.points==2 and #ElmoWaypointDB.points==2, 'Removing a migrated point must survive repeat import')
waypoints.Select(2)
assert(compass.title:GetText()=='Meeting point  ·  200 yd')
waypoints.ClearSelection()
assert(not waypoints.Current() and #waypoints.db.points==2)
assert(compass.arrow:IsShown() and compass.title:GetText():match('Quest 102'))
A.db.questCompass=false; A.QuestNavigation.Update()
assert(compass:IsShown() and not compass.band:IsShown() and compass.arrow:IsShown())
A.db.questCompass=true; A.db.questArrow=false; A.QuestNavigation.Update()
assert(compass:IsShown() and compass.band:IsShown() and not compass.arrow:IsShown())
A.db.questCompass=false; A.QuestNavigation.Update(); assert(not compass:IsShown())
MOCK.event('PLAYER_LEAVING_WORLD'); assert(not beam:IsShown())
''')
print('Quest navigation checks passed: relative heading, grouped hover tooltips, projection scale, completed quests and waypoint ownership.')
