-- Strict fixture: only frame methods and native APIs used by this addon exist.
MOCK = {time = 100, xp = 100, maximum = 400, level = 1, frames = {}, messages = {},
    bags = {}, slots = {[0] = 16}, items = {}, requests = {}, loadedAddons = {}, scanCalls = 0,
    units = {}, mobSerial = 0, chatSerial = 0, class = "HUNTER", talents = {}, equipped = {}}
local methods = {}
local function noop() end
for _, name in ipairs({"SetBackdrop", "SetBackdropColor", "SetBackdropBorderColor", "SetFrameStrata",
    "SetClampedToScreen", "SetMovable", "RegisterForDrag", "SetFont", "SetJustifyH",
    "SetColorTexture", "SetTextColor", "SetWordWrap", "EnableMouseWheel"}) do methods[name] = noop end
function methods:SetSize(w, h) self.width, self.height = w, h end
function methods:SetWidth(w) self.width = w end
function methods:SetHeight(h) self.height = h end
function methods:SetPoint(...)
    self.point = {...}; self.points = self.points or {}; self.points[self.point[1]] = self.point
end
function methods:ClearAllPoints() self.point = nil; self.points = {} end
function methods:EnableMouse(enabled) self.mouseEnabled = enabled end
function methods:RegisterForClicks(...)
    self.clicks = {}; for _, event in ipairs({...}) do self.clicks[event] = true end
end
function methods:GetFrameLevel() return self.frameLevel or (self.parent and self.parent:GetFrameLevel() + 1 or 0) end
function methods:GetID() return self.id or 0 end
function methods:SetID(value) self.id = value end
function methods:GetName() return self.name end
function methods:GetParent() return self.parent end
function methods:GetBagID() return self.bagID or (self.parent and self.parent:GetID()) end
function methods:SetFrameLevel(value) self.frameLevel = value end
function methods:SetAllPoints(target) self.allPoints = target or self.parent end
function methods:GetLeft() return self.mockLeft or 0 end
function methods:GetTop() return self.mockTop or 900 end
function methods:SetScript(event, fn) self.scripts[event] = fn end
function methods:GetScript(event) return self.scripts[event] end
function methods:RegisterEvent(event) self.events[event] = true end
function methods:SetText(value) self.text = tostring(value) end
function methods:GetText() return self.text or "" end
function methods:SetShown(value) self.shown = value end
function methods:Show() self.shown = true end
function methods:Hide() self.shown = false end
function methods:IsShown() return self.shown end
function methods:StartMoving() self.moving = true end
function methods:StopMovingOrSizing() self.moving = false end
function methods:SetOwner(owner, anchor) self.owner, self.anchor = owner, anchor end
function methods:AddLine(text) self.lines = self.lines or {}; table.insert(self.lines, text) end
function methods:CreateFontString() return CreateFrame("FontString", nil, self) end
function methods:CreateTexture() return CreateFrame("Texture", nil, self) end
function CreateFrame(kind, name, parent, template)
    local frame = setmetatable({kind = kind, name = name, parent = parent, template = template,
        shown = true, scripts = {}, events = {}, mouseEnabled = kind == 'Button',
        clicks = kind == 'Button' and {LeftButtonUp=true} or {}}, {__index = methods})
    table.insert(MOCK.frames, frame)
    if name then _G[name] = frame end
    return frame
end
UIParent = CreateFrame("Frame")
GameTooltip = CreateFrame("GameTooltip")
BackdropTemplateMixin = {}
SlashCmdList = {}
DEFAULT_CHAT_FRAME = {AddMessage = function(_, message) table.insert(MOCK.messages, message) end}
function GetTime() return MOCK.time end
function UnitAffectingCombat(unit) assert(unit == "player"); return MOCK.combat == true end
function UnitXP(unit) assert(unit == "player"); return MOCK.xp end
function UnitXPMax(unit) assert(unit == "player"); return MOCK.maximum end
function UnitLevel(unit) return unit == "player" and MOCK.level or (MOCK.units[unit] and MOCK.units[unit].level or 0) end
function UnitGUID(unit)
    if unit == "player" then return "Player-Test" end
    return MOCK.units[unit] and MOCK.units[unit].guid
end
function UnitName(unit)
    if unit == "player" then return MOCK.playerName or "HunterTest" end
    return MOCK.units[unit] and MOCK.units[unit].name
end
function UnitClass(unit) assert(unit == 'player'); return MOCK.class, MOCK.class end
function UnitGroupRolesAssigned(unit) assert(unit == 'player'); return MOCK.role or 'NONE' end
function GetTalentTabInfo(index) return index, 'Tree '..index, 'Description', 100, MOCK.talents[index] or 0, 'Background' end
function GetInventoryItemLink(unit, slot) assert(unit == 'player'); return MOCK.equipped[slot] end
function IsPlayerSpell(id) assert(id == 674); return MOCK.dualWield == true end
function hooksecurefunc(target, key, fn)
    if type(target) == 'string' then target, key, fn = _G, target, key end
    local original = assert(target[key]); assert(type(original) == 'function')
    target[key] = function(...)
        local values = {original(...)}; fn(...); return unpack(values)
    end
end
function ContainerFrame_Update() end
function UnitIsDead(unit) return MOCK.units[unit] and MOCK.units[unit].dead == true end
function MOCK.event(event, ...)
    local frame = ElmoLeveling.frame
    frame:GetScript("OnEvent")(frame, event, ...)
end
function MOCK.start(initialLogin, reloadingUi)
    if initialLogin == nil then initialLogin = true end
    MOCK.event("ADDON_LOADED", "ElmoLeveling")
    MOCK.event("PLAYER_ENTERING_WORLD", initialLogin, reloadingUi == true)
end
function MOCK.advance(seconds)
    MOCK.time = MOCK.time + seconds
    local frame = ElmoLeveling.frame
    local fn = frame:GetScript("OnUpdate")
    if fn then fn(frame, seconds) end
end
function MOCK.gain(amount)
    MOCK.xp = MOCK.xp + amount
    MOCK.event("PLAYER_XP_UPDATE", "player")
end

C_AddOns = {}
function C_AddOns.GetAddOnMetadata(name, field)
    if name == 'ForeverLeveling' and field == 'X-ClassicLevelingForever-Legacy' and not MOCK.foreignLegacy then return '1' end
end
function C_AddOns.LoadAddOn(name)
    table.insert(MOCK.loadedAddons, name)
    if MOCK.legacyError then error("Legacy loader unavailable") end
    if name == "ForeverLeveling" then
        if MOCK.oldTrackerDB then ForeverLevelingTrackerDB = MOCK.oldTrackerDB end
        if MOCK.oldPlannerDB then ForeverLevelingDB = MOCK.oldPlannerDB end
        return MOCK.oldTrackerDB ~= nil or MOCK.oldPlannerDB ~= nil
    end
    return false, "MISSING"
end

function MOCK.item(id, sellPrice, options)
    local item = options or {}
    item.id, item.price = id, sellPrice
    item.name = item.name or ("Item " .. id)
    MOCK.items[item.link or ("item:" .. id)] = item
    return item
end

function MOCK.put(bag, slot, id, count, options)
    local info = options or {}
    info.itemID, info.stackCount = id, count
    info.hyperlink = info.hyperlink or ("item:" .. id)
    MOCK.bags[bag] = MOCK.bags[bag] or {}
    MOCK.bags[bag][slot] = info
    MOCK.slots[bag] = math.max(MOCK.slots[bag] or 0, slot)
    return info
end

function MOCK.bagChange()
    MOCK.event("BAG_UPDATE_DELAYED")
    MOCK.advance(1)
end

C_Container = {}
function C_Container.GetContainerNumSlots(bag)
    assert(bag >= 0 and bag <= 4, "Only the backpack and carried bags may be scanned")
    MOCK.scanCalls = MOCK.scanCalls + 1
    return MOCK.slots[bag] or 0
end
function C_Container.GetContainerItemInfo(bag, slot)
    local info = MOCK.bags[bag] and MOCK.bags[bag][slot]
    if info and not info.missingInfo then return info end
end
function C_Container.GetContainerItemID(bag, slot)
    local info = MOCK.bags[bag] and MOCK.bags[bag][slot]
    return info and info.itemID
end

C_Item = {}
function C_Item.GetItemInfo(link)
    local item = MOCK.items[link]
    if not item or item.cold then return end
    return item.name, link, item.quality or 0, item.itemLevel or 1, item.required or 1,
        "Miscellaneous", "Junk", 200, item.equipLoc or "", 1000, item.price, item.classID or 4, item.subclassID or 0
end
function C_Item.RequestLoadItemDataByID(id)
    assert(type(id) == "number" and id > 0 and id % 1 == 0)
    MOCK.requests[id] = (MOCK.requests[id] or 0) + 1
end
function C_Item.GetItemStats(link)
    local item = MOCK.items[link]
    if item and not item.statsCold then return item.stats or {} end
end
function C_Item.IsEquippableItem(link)
    local item = MOCK.items[link]; return item and item.equipLoc ~= nil and item.equippable ~= false
end
local function itemByID(id)
    for _, item in pairs(MOCK.items) do if item.id == id then return item end end
end
C_PlayerInfo = {CanUseItem = function(id)
    local item = itemByID(id)
    return item ~= nil and not item.unusable and (item.required or 1) <= MOCK.level
end}
function C_Item.GetItemUniqueness(link)
    local item = MOCK.items[link]
    if item and item.category then return item.category, item.limit or 1 end
end
function C_Item.GetItemUniquenessByID(id)
    local item = itemByID(id)
    if item then return item.unique == true, nil, item.limit, item.category end
end
DPS_TEMPLATE = '(%.1f damage per second)'
ARMOR_TEMPLATE = '%d Armor'
function methods:ClearLines()
    for i = 1, self.tooltipCount or 0 do
        for _, side in ipairs({'Left','Right'}) do
            local region = _G[self.name..'Text'..side..i]; if region then region:SetText('') end
        end
    end
    self.tooltipCount = 0
end
function methods:SetHyperlink(link)
    local item = MOCK.items[link]; if not item or item.tooltipCold then return end
    local lines = {item.name}
    for _, line in ipairs(item.tooltip or {}) do table.insert(lines,line) end
    if item.dps then table.insert(lines,string.format(DPS_TEMPLATE,item.dps)) end
    if item.armor then table.insert(lines,string.format(ARMOR_TEMPLATE,item.armor)) end
    self.tooltipCount = #lines
    for i, line in ipairs(lines) do
        local name = self.name..'TextLeft'..i
        local region = _G[name] or CreateFrame('FontString',name,self); region:SetText(line)
    end
end
function methods:NumLines() return self.tooltipCount or 0 end

function MOCK.gear(id, location, stats, options)
    local item = options or {}; item.equipLoc, item.stats = location, stats or {}
    if item.classID == nil then
        item.classID = (location:find('WEAPON') or location:find('RANGED') or location == 'INVTYPE_THROWN') and 2 or 4
    end
    return MOCK.item(id, 10, item)
end
function MOCK.nativeBag(bag, size)
    local container = CreateFrame('Frame','TestContainer'..bag,UIParent)
    container:SetID(bag); container.size = size
    local buttons = {}
    for i=1,size do
        buttons[i] = CreateFrame('Button',container.name..'Item'..i,container)
        buttons[i]:SetID(i)
    end
    ContainerFrame_Update(container)
    return container, buttons
end
function MOCK.betterBags()
    local proto = {FinishItemDraw=function() end, ResetVisuals=function() end}
    local addon = {GetModule=function(_,name) if name == 'ItemFrame' then return {itemProto=proto} end end}
    LibStub = function(name)
        assert(name == 'AceAddon-3.0')
        return {GetAddon=function(_,name) if name == 'BetterBags' then return addon end end}
    end
    MOCK.better = proto
end
function MOCK.betterItem(link, bag)
    local item = {button=CreateFrame('Button',nil,UIParent),currentData={bagid=bag or 0,itemInfo={itemLink=link}}}
    setmetatable(item,{__index=MOCK.better}); item:FinishItemDraw()
    return item
end

-- The shipping Forever surface: no readable combat log or Classic globals.
function MOCK.forever()
    C_CombatLog = {IsCombatLogRestricted=function() return true end}
    CombatLogGetCurrentEventInfo = nil
    GetTalentTabInfo, IsPlayerSpell = nil, nil
    C_SpellBook = {IsSpellKnown=function(id) assert(id==674); return MOCK.dualWield == true end}
    C_EventUtils = {IsEventValid=function(event) return event ~= 'CHARACTER_POINTS_CHANGED' end}
    SetItemButtonQuality = function() end
    C_TooltipInfo = {GetHyperlink=function(link)
        local item = MOCK.items[link]
        if not item or item.cold or item.tooltipCold then return end
        local lines = {{leftText=item.name}}
        for _, line in ipairs(item.tooltip or {}) do lines[#lines+1]={leftText=line} end
        if item.dps then lines[#lines+1]={leftText=string.format(DPS_TEMPLATE,item.dps)} end
        if item.armor then lines[#lines+1]={leftText=string.format(ARMOR_TEMPLATE,item.armor)} end
        return {lines=lines}
    end}
end

function MOCK.traits(points, unknownSpell)
    local fact = A.TalentBranches[MOCK.class]
    local spellByBranch = {}
    for spell, branch in pairs(fact.spells) do spellByBranch[branch] = spellByBranch[branch] or spell end
    C_Traits = {
        GetConfigIDByTreeID=function(tree) assert(tree==fact.tree); return 100 end,
        GetTreeNodes=function(tree) assert(tree==fact.tree); return {1,2,3} end,
        GetNodeInfo=function(config,id) assert(config==100); return {activeRank=points[id] or 0,activeEntry={entryID=id}} end,
        GetEntryInfo=function(config,id) assert(config==100); return {definitionID=id} end,
        GetDefinitionInfo=function(id) return {spellID=unknownSpell and id==2 and 999999999 or spellByBranch[id]} end,
    }
end

function MOCK.plain(text)
    return (text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))
end

COMBATLOG_XPGAIN_FIRSTPERSON = "%s dies, you gain %d experience."
COMBATLOG_XPGAIN_FIRSTPERSON_GROUP = "%s dies, you gain %d experience. (+%d group bonus)"
COMBATLOG_XPGAIN_FIRSTPERSON_UNNAMED = "You gain %d experience."
COMBATLOG_XPGAIN_EXHAUSTION1 = "%s dies, you gain %d experience. (%s exp %s bonus)"

C_CombatLog = {GetCurrentEventInfo = function() return unpack(MOCK.combat or {}) end}
CombatLogGetCurrentEventInfo = C_CombatLog.GetCurrentEventInfo

function MOCK.mob(unit, name, mobLevel, guid)
    MOCK.mobSerial = MOCK.mobSerial + 1
    local mob = {name = name, level = mobLevel, guid = guid or ("Creature-" .. MOCK.mobSerial), dead = false}
    MOCK.units[unit] = mob
    return mob
end
function MOCK.death(unit, event, flags, source, stamp)
    local mob = assert(MOCK.units[unit]); mob.dead = true
    MOCK.combat = {stamp or MOCK.time, event or "PARTY_KILL", false, source or "Player-Test", "HunterTest", flags or 1, 0,
        mob.guid, mob.name, 0, 0}
    MOCK.event("COMBAT_LOG_EVENT_UNFILTERED")
end
function MOCK.attack(unit, event, stamp, flags, source, miss)
    local mob = assert(MOCK.units[unit])
    event = event or "SWING_DAMAGE"
    MOCK.combat = {stamp or MOCK.time, event, false, source or "Player-Test", "HunterTest", flags or 1, 0,
        mob.guid, mob.name, 0, 0}
    if event == "SWING_MISSED" then MOCK.combat[12] = miss or "MISS"
    elseif event:match("_MISSED$") then
        MOCK.combat[12],MOCK.combat[13],MOCK.combat[14],MOCK.combat[15] = 123,"Spell",1,miss or "MISS"
    else MOCK.combat[12],MOCK.combat[13],MOCK.combat[14],MOCK.combat[15] = 123,"Spell",1,10 end
    MOCK.event("COMBAT_LOG_EVENT_UNFILTERED")
end
function MOCK.chatText(message, lineID, guid)
    MOCK.chatSerial = MOCK.chatSerial + 1
    MOCK.event("CHAT_MSG_COMBAT_XP_GAIN", message, "", "", "", "", "", 0, 0, "", 0,
        lineID or MOCK.chatSerial, guid or "", 0, false, false, false, false)
end
function MOCK.chat(name, xp, lineID, guid)
    MOCK.chatText(string.format(COMBATLOG_XPGAIN_FIRSTPERSON, name, xp), lineID, guid)
end

-- Header-local pointer routing, including the title drag region. Directly
-- invoking OnClick would miss overlapping mouse-enabled frames.
function MOCK.headerBounds(frame)
    local points, width = frame.points, ElmoLeveling.UI.panel.width
    local left, right = points.TOPLEFT, points.TOPRIGHT
    local x1 = left and left[2] or (width + right[2] - frame.width)
    local x2 = right and width + right[2] or (x1 + frame.width)
    local y1 = -(left or right)[3]
    return x1, y1, x2, y1 + frame.height
end
function MOCK.headerClick(x, y, button, down)
    local receiver
    if not ElmoLeveling.UI.panel:IsShown() then return end
    for _, frame in ipairs({ElmoLeveling.UI.anchor, ElmoLeveling.UI.mobToggle}) do
        local x1,y1,x2,y2 = MOCK.headerBounds(frame)
        if frame.mouseEnabled and frame:IsShown() and x >= x1 and x <= x2 and y >= y1 and y <= y2 and
            (not receiver or frame:GetFrameLevel() >= receiver:GetFrameLevel()) then receiver = frame end
    end
    if receiver then
        local event = (button or 'LeftButton') .. (down and 'Down' or 'Up')
        local callback = receiver:GetScript('OnClick')
        if receiver.clicks[event] and callback then callback(receiver,button or 'LeftButton',down or false) end
    end
    return receiver
end
