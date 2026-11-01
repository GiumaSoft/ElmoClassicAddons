local _, A = ...
local C = {}
A.Compat = C

function A.IsSecret(value)
    return type(issecretvalue) == "function" and issecretvalue(value)
end
function A.IsNumber(value)
    return not A.IsSecret(value) and type(value) == "number" and value == value and value >= 0 and value < math.huge
end
function A.Text(value)
    return not A.IsSecret(value) and type(value) == "string" and value or nil
end
function A.Call(fn, ...)
    if type(fn) ~= "function" then return end
    local ok, a, b, c, d, e, f, g, h, i, j = pcall(fn, ...)
    if ok then return a, b, c, d, e, f, g, h, i, j end
end

function C.CombatAvailable()
    local get = C_CombatLog and C_CombatLog.GetCurrentEventInfo or CombatLogGetCurrentEventInfo
    if type(get) ~= "function" then return false end
    local restricted = A.Call(C_CombatLog and C_CombatLog.IsCombatLogRestricted)
    return not A.IsSecret(restricted) and restricted ~= true
end

function C.Register(frame, event)
    if event == "COMBAT_LOG_EVENT_UNFILTERED" and not C.CombatAvailable() then return false end
    local valid = A.Call(C_EventUtils and C_EventUtils.IsEventValid, event)
    if valid == false then return false end
    return pcall(frame.RegisterEvent, frame, event)
end

-- Forever uses a C_Traits class tree, not Classic's three talent tabs.
-- Match the live definition's spell rather than assuming old node IDs survived.
function C.TalentTree(class)
    local fact = A.TalentBranches and A.TalentBranches[class]
    if not fact or not C_Traits or type(C_Traits.GetTreeNodes) ~= "function" then return end
    local config = A.Call(C_Traits.GetConfigIDByTreeID, fact.tree)
    if not A.IsNumber(config) or config <= 0 then
        config = A.Call(C_ClassTalents and C_ClassTalents.GetActiveConfigID)
        if not A.IsNumber(config) or config <= 0 then return end
        local info = A.Call(C_Traits.GetConfigInfo, config)
        local holds = false
        for _, id in ipairs(type(info) == "table" and info.treeIDs or {}) do
            if id == fact.tree then holds = true end
        end
        if not holds then return end
    end
    local nodes = A.Call(C_Traits.GetTreeNodes, fact.tree)
    if type(nodes) ~= "table" or A.IsSecret(nodes) then return end
    local points = {0, 0, 0}
    for _, id in ipairs(nodes) do
        local node = A.Call(C_Traits.GetNodeInfo, config, id)
        if type(node) == "table" and not A.IsSecret(node) then
            local rank = node.activeRank or node.ranksPurchased or 0
            local entry = node.activeEntry and node.activeEntry.entryID
            local info = entry and A.Call(C_Traits.GetEntryInfo, config, entry)
            local definition = type(info) == "table" and A.Call(C_Traits.GetDefinitionInfo, info.definitionID)
            local spell = type(definition) == "table" and definition.spellID
            local branch = A.IsNumber(spell) and fact.spells[spell]
            if branch and A.IsNumber(rank) then points[branch] = points[branch] + rank end
        end
    end
    local best, most = 0, 0
    for branch, value in ipairs(points) do if value > most then best, most = branch, value end end
    return best
end

function C.ItemTooltip(link)
    if C_TooltipInfo and type(C_TooltipInfo.GetHyperlink) == "function" then
        local data = A.Call(C_TooltipInfo.GetHyperlink, link)
        if not A.IsSecret(data) and type(data) == "table" then return data end
        return
    end
    if not C.tooltip then C.tooltip = CreateFrame("GameTooltip", "ElmoLevelingScanTooltip", UIParent, "GameTooltipTemplate") end
    local tip = C.tooltip
    tip:SetOwner(UIParent, "ANCHOR_NONE"); tip:ClearLines()
    local ok = pcall(tip.SetHyperlink, tip, link)
    local lines = {}
    if ok then
        for i = 1, math.min(tip:NumLines() or 0, 100) do
            local left, right = _G["ElmoLevelingScanTooltipTextLeft" .. i], _G["ElmoLevelingScanTooltipTextRight" .. i]
            lines[#lines + 1] = {leftText = left and left:GetText(), rightText = right and right:GetText()}
        end
    end
    tip:Hide()
    return {lines = lines}
end
