-- Narrow offline WoW mock. Missing UI methods fail instead of silently succeeding.
MOCK={time=100,class="PALADIN",level=15,items={},equipped={},bags={},messages={},requests={},inside=false,
    instanceName="Fixture Dungeon",map=999001,dual=false,locale="enUS",catalogReady=false}
SECRET=setmetatable({},{__index=function() error("secret read") end,
    __tostring=function() error("secret tostring") end,__lt=function() error("secret comparison") end,
    __concat=function() error("secret concat") end})
function issecretvalue(v) return rawequal(v,SECRET) end
local methods={}
local noop=function() end
for _,key in ipairs({"SetMovable","EnableMouse","RegisterForDrag","SetClampedToScreen","SetFrameStrata",
    "SetBackdrop","SetBackdropColor","SetBackdropBorderColor","StartMoving","StopMovingOrSizing",
    "SetJustifyH","SetWordWrap","SetTextColor","SetAllPoints","SetColorTexture","SetOwner"}) do methods[key]=noop end
methods.EnableMouseWheel=noop
function methods:SetSize(w,h) self.width,self.height=w,h end
function methods:SetWidth(w) self.width=w end
function methods:SetHeight(h) self.height=h end
function methods:GetHeight() return self.height or 240 end
function methods:GetWidth() return self.width or 240 end
function methods:SetPoint(...) self.point={...} end
function methods:ClearAllPoints() self.point=nil end
function methods:SetScript(key,fn) self.scripts[key]=fn end
function methods:GetScript(key) return self.scripts[key] end
function methods:SetText(v) self.text=v end
function methods:GetText() return self.text end
function methods:GetStringHeight()
    local visible=(self.text or ''):gsub('|c%x%x%x%x%x%x%x%x',''):gsub('|r','')
    return math.max(1,math.ceil(#visible/math.max(1,math.floor((self.width or 200)/6))))*12
end
function methods:GetCenter() return 300,200 end
function methods:GetLeft()
    if self==UIParent then return 0 end
    local p=self.point
    if p and p[1]=="TOPLEFT" and p[3]=="TOPLEFT" then return p[2]:GetLeft()+p[4] end
    return 300-(self.width or 240)/2
end
function methods:GetTop()
    if self==UIParent then return 800 end
    local p=self.point
    if p and p[1]=="TOPLEFT" and p[3]=="TOPLEFT" then return p[2]:GetTop()+p[5] end
    return 200+(self.height or 240)/2
end
function methods:SetScrollChild(v) self.child=v end
function methods:GetVerticalScroll() return self.scroll or 0 end
function methods:SetVerticalScroll(v) self.scroll=v end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:SetShown(v) self.shown=v end
function methods:IsShown() return self.shown end
function methods:RegisterEvent(e) self.events[e]=true end
function methods:AddLine(s) self.lines=self.lines or {};self.lines[#self.lines+1]=s end
function methods:SetHyperlink(link) self.link=link;self.lines={} end
function methods:CreateFontString(...) return CreateFrame("FontString",nil,self) end
function methods:CreateTexture(...) return CreateFrame("Texture",nil,self) end
function CreateFrame(kind,name,parent,template)
    local f=setmetatable({kind=kind,name=name,parent=parent,template=template,scripts={},events={},shown=true}, {__index=methods})
    if name then _G[name]=f end
    return f
end
UIParent=CreateFrame("Frame");GameTooltip=CreateFrame("GameTooltip")
DEFAULT_CHAT_FRAME={AddMessage=function(_,s) MOCK.messages[#MOCK.messages+1]=s end}
SlashCmdList={};NUM_BAG_SLOTS=4
ITEM_QUALITY_COLORS={[3]={hex="|cff0070dd"}}
DPS_TEMPLATE="(%.1f damage per second)";SHIELD_BLOCK_TEMPLATE="%d Block"
function GetTime() return MOCK.time end
function GetLocale() return MOCK.locale end
function UnitClass() return MOCK.class,MOCK.class,2 end
function UnitLevel() return MOCK.level end
function CanDualWield() return MOCK.dual end
function InCombatLockdown() return MOCK.combat or false end
function IsInInstance() return MOCK.inside,MOCK.instanceType or "party" end
function GetInstanceInfo() return MOCK.instanceName,"party",1,"Normal",5,false,false,MOCK.map end
function GetInventoryItemLink(_,slot) return MOCK.equipped[slot] end
local function idOf(ref)
    if issecretvalue(ref) then return SECRET end
    if type(ref)=="number" then return ref end
    if type(ref)=="string" then return tonumber(ref:match("item:(%d+)")) end
end
function GetInventoryItemID(_,slot) return idOf(MOCK.equipped[slot]) end
local function data(ref)
    local id=idOf(ref)
    if issecretvalue(id) then return nil end
    local item=MOCK.items[ref] or MOCK.items[id]
    if item then return item,id end
    if MOCK.catalogReady and ElmoDungeonLoot and ElmoDungeonLoot.Catalog.items[id] then
        local c=ElmoDungeonLoot.Catalog.items[id]
        return {name=c.name,loc=c.loc,level=c.level,classID=c.classID,subclassID=c.subclassID,
            stats={},dps=(c.classID==2 and 10 or nil),uniqueMax=c.unique and 1},id
    end
end
C_Item={}
function C_Item.GetItemInfoInstant(ref)
    local item,id=data(ref)
    if not item then return idOf(ref) end
    return id,"type","subtype",item.loc,123,item.classID or 4,item.subclassID or 1
end
function C_Item.GetItemInfo(ref)
    local item,id=data(ref)
    if not item or item.cold then return nil end
    local link=item.infoLink or (type(ref)=="string" and ref or "item:"..id)
    return item.name or "Item "..id,link,3,item.itemLevel or 20,item.level or 1,item.itemType or "type",item.itemSubType or "subtype",1,item.loc,123,1,
        item.classID or 4,item.subclassID or 1,1,0,nil,false,""
end
function C_Item.GetItemStats(ref) local item=data(ref);return item and item.stats end
function C_Item.GetItemUniquenessByID(id)
    local item=data(id)
    return item and item.uniqueMax~=nil,nil,item and item.uniqueMax,item and item.category
end
function C_Item.RequestLoadItemDataByID(id) MOCK.requests[id]=(MOCK.requests[id] or 0)+1 end
C_PlayerInfo={}
function C_PlayerInfo.CanUseItem(id)
    local item=data(id)
    if not item then return nil end
    if item.usable~=nil then return item.usable end
    return (item.level or 1)<=MOCK.level
end
C_Container={}
function C_Container.GetContainerNumSlots(bag)
    local n=0;for k in pairs(MOCK.bags[bag] or {}) do n=math.max(n,k) end;return n
end
function C_Container.GetContainerItemInfo(bag,slot)
    local v=(MOCK.bags[bag] or {})[slot]
    if not v then return nil end
    if issecretvalue(v) then return SECRET end
    return {hyperlink=v,itemID=idOf(v),stackCount=1}
end
function C_Container.GetContainerItemLink(bag,slot) return (MOCK.bags[bag] or {})[slot] end
C_TooltipInfo={}
local function tooltipData(item)
    if not item then return nil end
    if item.secretTooltip then return SECRET end
    local lines={}
    for _,s in ipairs(item.lines or {}) do
        lines[#lines+1]=type(s)=="table" and s or {leftText=s}
    end
    if item.dps then lines[#lines+1]={leftText=string.format("(%.1f damage per second)",item.dps)} end
    if item.block then lines[#lines+1]={leftText=item.block.." Block"} end
    return {lines=lines}
end
function C_TooltipInfo.GetHyperlink(ref) return tooltipData(data(ref)) end
function C_TooltipInfo.GetInventoryItem(unit,slot)
    assert(unit=="player")
    local ref=MOCK.equipped[slot]
    local record=MOCK.inventoryTooltips and MOCK.inventoryTooltips[slot]
    if record==false then return nil end
    return tooltipData(record or data(ref))
end
function C_TooltipInfo.GetBagItem(bag,slot)
    local ref=(MOCK.bags[bag] or {})[slot]
    local record=MOCK.bagTooltips and MOCK.bagTooltips[bag] and MOCK.bagTooltips[bag][slot]
    if record==false then return nil end
    return tooltipData(record or data(ref))
end

-- Classic Era's native GameTooltip scanner, including both text columns.
function methods:ClearLines() self.nativeLines={} end
function methods:NumLines() return #(self.nativeLines or {}) end
local function nativeTooltip(frame, record)
    frame.nativeLines=tooltipData(record) and tooltipData(record).lines or {}
    for i,line in ipairs(frame.nativeLines) do
        local left=CreateFrame('FontString');left:SetText(line.leftText)
        local right=CreateFrame('FontString');right:SetText(line.rightText)
        _G[frame.name..'TextLeft'..i]=left
        _G[frame.name..'TextRight'..i]=right
    end
end
local visibleHyperlink=methods.SetHyperlink
function methods:SetHyperlink(ref)
    if self.name=='ElmoDungeonLootScanTooltip' then nativeTooltip(self,data(ref))
    else visibleHyperlink(self,ref) end
end
function methods:SetInventoryItem(unit,slot)
    assert(unit=='player');MOCK.nativeSource='inventory:'..slot
    local record=MOCK.inventoryTooltips and MOCK.inventoryTooltips[slot]
    nativeTooltip(self,record==false and nil or record or data(MOCK.equipped[slot]))
    if record==false then self:ClearLines() end
end
function methods:SetBagItem(bag,slot)
    MOCK.nativeSource='bag:'..bag..':'..slot
    local record=MOCK.bagTooltips and MOCK.bagTooltips[bag] and MOCK.bagTooltips[bag][slot]
    nativeTooltip(self,record==false and nil or record or data((MOCK.bags[bag] or {})[slot]))
    if record==false then self:ClearLines() end
end

function MOCK.advance(seconds)
    for _=1,math.ceil(seconds/.05) do
        MOCK.time=MOCK.time+.05
        local fn=ElmoDungeonLoot.frame:GetScript("OnUpdate")
        if fn then fn(ElmoDungeonLoot.frame,.05) end
    end
end
