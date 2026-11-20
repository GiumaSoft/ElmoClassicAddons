local _, A = ...
local M = {units = {}}
A.QuestMarkers = M

local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local KNIFE = "Interface\\Icons\\INV_Weapon_ShortBlade_05"
local BAG = "Interface\\Icons\\INV_Misc_Bag_08"
local MOB_MARKER_SIZE = 32
local killMarks, itemMarks = {texture = KNIFE}, {texture = BAG}
local badgePool, mobMarkers, markerPool = {}, {}, {}
local nextScan = 0

function M.CreateQuestBang(parent, size)
    local glyph = parent:CreateTexture(nil, "OVERLAY")
    glyph:SetSize(size, size)
    local atlas = "QuestNormal"
    if not (A.Call(C_Texture and C_Texture.GetAtlasInfo, atlas) and glyph.SetAtlas and
        pcall(glyph.SetAtlas, glyph, atlas, false)) then
        glyph:SetTexture("Interface\\GossipFrame\\AvailableQuestIcon")
    end
    return glyph
end

function M.CreateBeacon(name)
    local frame = CreateFrame("Frame", name, UIParent)
    frame:SetSize(1, 1)
    frame:EnableMouse(false)
    local art = frame:CreateTexture(nil, "ARTWORK")
    art:SetTexture("Interface\\AddOns\\ElmoLeveling\\Media\\QuestBeacon.tga")
    art:SetSize(72, 152)
    -- Offset the full texture so the center of its ground ring is the anchor.
    art:SetPoint("CENTER", frame, "CENTER", 0, 57)
    local symbol = M.CreateQuestBang(frame, 22)
    symbol:SetPoint("CENTER", frame, "CENTER", 0, 114)
    frame.title = frame:CreateFontString(nil, "OVERLAY")
    frame.title:SetFont(FONT, 12, "OUTLINE")
    frame.title:SetTextColor(1, .85, .53)
    frame.title:SetPoint("BOTTOM", frame, "CENTER", 0, 132)
    frame.distance = frame:CreateFontString(nil, "OVERLAY")
    frame.distance:SetFont(FONT, 11, "OUTLINE")
    frame.distance:SetTextColor(.80, .91, 1)
    frame.distance:SetPoint("TOP", frame, "CENTER", 0, -12)
    frame:Hide()
    return frame
end

local function createMobMarker()
    -- Blizzard aura containers only accept dependents with layout scripts disabled.
    local layoutTemplate = "DisableUntrustedLayoutScriptsTemplate"
    local hasTemplate = A.Call(C_XMLUtil and C_XMLUtil.GetTemplateInfo, layoutTemplate)
    local frame = CreateFrame("Frame", nil, UIParent, hasTemplate and layoutTemplate or nil)
    frame:SetSize(MOB_MARKER_SIZE, MOB_MARKER_SIZE)
    frame:EnableMouse(false)
    M.CreateQuestBang(frame, MOB_MARKER_SIZE):SetPoint("CENTER")
    frame:Hide()
    return frame
end

local function createProgressBadge()
    local mark = CreateFrame("Frame", nil, UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    mark:SetFrameStrata("LOW")
    mark:EnableMouse(false)
    mark:SetBackdrop({bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
        edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 8,
        insets = {left = 2, right = 2, top = 2, bottom = 2}})
    mark:SetBackdropColor(.025, .025, .025, .95)
    mark:SetBackdropBorderColor(.47, .36, .14, 1)
    local icon = mark:CreateTexture(nil, "ARTWORK")
    icon:SetPoint("CENTER", mark, "CENTER")
    icon:SetTexCoord(.07, .93, .07, .93)
    local count = mark:CreateFontString(nil, "OVERLAY")
    count:SetFont(FONT, 10, "OUTLINE")
    count:SetPoint("TOP", mark, "BOTTOM", 0, -1)
    mark.icon, mark.count = icon, count
    mark:Hide()
    return mark
end

local function usable(frame)
    return not A.IsSecret(frame) and frame and A.Call(frame.IsForbidden, frame) ~= true
end

local function healthAnchor(unit, plate, guid)
    local anchor, upper, clearance, levelBadge = A.Call(ElmoPlater and ElmoPlater.GetHealthAnchor, unit, plate, guid)
    if usable(anchor) then
        return anchor, usable(upper) and upper or anchor, clearance, usable(levelBadge) and levelBadge or nil
    end
    local native = plate.UnitFrame
    if usable(native) then
        local health = native.HealthBarsContainer and native.HealthBarsContainer.healthBar or native.healthBar
        if usable(health) and A.Call(health.IsShown, health) ~= false then return health end
    end
    return plate
end

local function shown(frame)
    if not usable(frame) then return false end
    local value = A.Call(frame.IsShown, frame)
    return not A.IsSecret(value) and value == true
end

local function screenTop(frame)
    if not shown(frame) then return 0 end
    local top = A.Call(frame.GetTop, frame)
    local scale = A.Call(frame.GetEffectiveScale, frame)
    if A.IsNumber(top) and A.IsNumber(scale) then return top * scale end
end

local function nativeClearance(plate, anchor)
    local native = plate.UnitFrame
    local barTop = screenTop(anchor)
    local uiScale = A.Call(UIParent.GetEffectiveScale, UIParent)
    if not usable(native) or not barTop or barTop == 0 or not A.IsNumber(uiScale) or uiScale == 0 then return 22 end
    local auraFallback = barTop + 72 * uiScale
    local nameTop = screenTop(native.name) or barTop + 22 * uiScale
    local top = math.max(barTop, nameTop, screenTop(native.BuffFrame) or auraFallback)
    local auras = native.AurasFrame
    if shown(auras) then
        top = math.max(top, screenTop(auras.DebuffListFrame) or auraFallback,
            screenTop(auras.BuffListFrame) or auraFallback, screenTop(auras.CrowdControlListFrame) or auraFallback,
            screenTop(auras.LossOfControlFrame) or auraFallback)
    end
    -- Keep X on the bar even when Blizzard lays its aura lists out from one side.
    return (top - barTop) / uiScale
end

local function releaseProgressBadge(marks, unit)
    local mark = marks[unit]
    if not mark then return end
    mark:Hide()
    mark:ClearAllPoints()
    mark:SetParent(UIParent)
    mark.anchor = nil
    marks[unit] = nil
    badgePool[#badgePool + 1] = mark
end

function M.Remove(unit)
    if not A.Text(unit) then return end
    M.units[unit] = nil
    A.QuestKills.ForgetUnit(unit)
    local marker = mobMarkers[unit]
    if marker then
        marker:Hide(); marker:ClearAllPoints()
        marker.anchor, marker.offset = nil, nil
        mobMarkers[unit] = nil
        markerPool[#markerPool + 1] = marker
    end
    releaseProgressBadge(itemMarks, unit)
    releaseProgressBadge(killMarks, unit)
end

function M.Clear()
    for unit in pairs(M.units) do M.Remove(unit) end
    nextScan = 0
end

function M.Add(unit, plate)
    unit = A.Text(unit)
    if unit and unit:match("^nameplate%d+$") then
        if not plate then A.QuestKills.ForgetUnit(unit) end
        M.units[unit] = plate or M.units[unit] or true
    end
end

local function plateUnit(plate)
    return A.Text(A.Call(plate.GetUnit, plate)) or A.Text(plate.namePlateUnitToken) or
        A.Text(plate.unitToken) or (usable(plate.UnitFrame) and A.Text(plate.UnitFrame.unit))
end

function M.Scan()
    nextScan = GetTime() + .5
    local plates = A.Call(C_NamePlate and C_NamePlate.GetNamePlates)
    if A.IsSecret(plates) or type(plates) ~= "table" or (issecrettable and issecrettable(plates)) then return end
    for _, plate in ipairs(plates) do
        if usable(plate) then M.Add(plateUnit(plate), plate) end
    end
end

local function mobObjectives(unit, now)
    local plate = A.Call(C_NamePlate and C_NamePlate.GetNamePlateForUnit, unit)
    if not usable(plate) then
        local listed = M.units[unit]
        if listed ~= true and usable(listed) and plateUnit(listed) == unit then plate = listed end
    end
    if not usable(plate) or not A.Call(plate.IsShown, plate) then return end
    local alpha = A.Call(plate.GetEffectiveAlpha or plate.GetAlpha, plate)
    if A.IsNumber(alpha) and alpha <= 0 then return end
    local dead = A.Call(UnitIsDeadOrGhost or UnitIsDead, unit)
    local attack = A.Call(UnitCanAttack, "player", unit)
    local behind = A.Call(C_NamePlateManager and C_NamePlateManager.IsNamePlateUnitBehindCamera, unit)
    if (not A.IsSecret(dead) and dead) or (not A.IsSecret(attack) and attack == false) or
        (not A.IsSecret(behind) and behind) then return end
    local guid = A.Text(A.Call(UnitGUID, unit))
    if guid == "" then guid = nil end
    if guid then
        if not A.QuestKills.IsCreatureGUID(guid) then return end
    elseif not A.IsSecret(attack) and attack == true then
        local player = A.Call(UnitIsPlayer, unit)
        local controlled = A.Call(UnitPlayerControlled, unit)
        if A.IsSecret(player) or player ~= false or A.IsSecret(controlled) or controlled ~= false then return end
    else
        return
    end
    local name = A.Text(A.Call(UnitName, unit))
    if not name or name == "" then
        local native = plate.UnitFrame
        local label = usable(native) and native.name
        if usable(label) then name = A.Text(A.Call(label.GetText, label)) end
    end
    local kill = A.QuestKills.FindByName(name, now)
    local item = A.QuestKills.GetItemObjective(unit, guid, now)
    if not kill and not item then return end
    return plate, guid, kill, item, A.IsNumber(alpha) and math.min(alpha, 1) or 1
end

local function renderProgressBadge(marks, unit, anchor, objective, alpha, size, parent)
    local mark = marks[unit]
    if not anchor or not objective then
        if mark then mark:Hide() end
        return
    end
    if not mark then
        mark = table.remove(badgePool) or createProgressBadge()
        mark.icon:SetTexture(marks.texture)
        marks[unit] = mark
    end
    if mark:GetParent() ~= parent then mark:SetParent(parent) end
    if mark.size ~= size then
        mark:SetSize(size, size)
        local iconSize = size * .65
        mark.icon:SetSize(iconSize, iconSize)
        mark.size = size
    end
    if mark.anchor ~= anchor then
        mark:ClearAllPoints()
        if not pcall(mark.SetPoint, mark, "LEFT", anchor, "RIGHT", 8, 0) then
            mark.anchor = nil
            mark:Hide()
            return
        end
        mark.anchor = anchor
    end
    mark:SetAlpha(parent == UIParent and alpha or 1)
    mark.count:SetText(objective.done .. "/" .. objective.total)
    mark:Show()
    return mark
end

local function renderMobMarker(unit, anchor, clearance, alpha, bar)
    local marker = mobMarkers[unit]
    if not marker then
        marker = table.remove(markerPool) or createMobMarker()
        mobMarkers[unit] = marker
    end
    local offset = clearance + 6
    if marker.anchor ~= anchor or marker.offset ~= offset then
        marker:ClearAllPoints()
        local anchored = pcall(marker.SetPoint, marker, "BOTTOM", anchor, "TOP", 0, offset)
        if not anchored and anchor ~= bar then
            marker:ClearAllPoints()
            -- Reserve room for the name, an aura row and its countdown.
            anchored = pcall(marker.SetPoint, marker, "BOTTOM", bar, "TOP", 0, 26 + clearance * 3)
        end
        if not anchored then
            marker.anchor = nil
            return
        end
        marker.anchor, marker.offset = anchor, offset
    end
    marker:SetAlpha(math.max(.88, alpha))
    marker:Show()
    return true
end

function M.Update()
    local now = GetTime()
    local showProgress, showMarker = A.db.questMobMarks, A.db.questMobBeam
    if (showProgress or showMarker) and now >= nextScan then M.Scan() end
    for unit in pairs(M.units) do
        local plate, guid, kill, item, alpha
        if showProgress or showMarker then plate, guid, kill, item, alpha = mobObjectives(unit, now) end
        local anchor, upper, clearance, levelBadge
        if plate then anchor, upper, clearance, levelBadge = healthAnchor(unit, plate, guid) end
        local badgeAnchor = showProgress and (levelBadge or anchor)
        local size, parent
        if badgeAnchor and levelBadge then
            size = A.Call(levelBadge.GetWidth, levelBadge)
            parent = A.Call(levelBadge.GetParent, levelBadge)
        end
        if not A.IsNumber(size) or size == 0 then size = 18 end
        if not usable(parent) then parent = UIParent end
        local knife = renderProgressBadge(killMarks, unit, badgeAnchor, kill, alpha, size, parent)
        renderProgressBadge(itemMarks, unit, knife or badgeAnchor, item, alpha, size, parent)
        local markerShown
        if showMarker and anchor then
            if not upper then clearance = nativeClearance(plate, anchor) end
            markerShown = renderMobMarker(unit, upper or anchor, A.IsNumber(clearance) and clearance or 48, alpha, anchor)
        end
        if not markerShown and mobMarkers[unit] then mobMarkers[unit]:Hide() end
    end
end
