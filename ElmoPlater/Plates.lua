local _, A = ...
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local WHITE = "Interface\\Buttons\\WHITE8X8"

local function text(parent, size)
    local label = parent:CreateFontString(nil, "OVERLAY")
    label:SetFont(FONT, size, "OUTLINE"); label:SetTextColor(1, 1, 1)
    return label
end

local function make(plate)
    local bounds = CreateFrame("Frame", nil, UIParent)
    bounds:EnableMouse(false); bounds:Hide()
    local f = CreateFrame("Frame", nil, UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:EnableMouse(false); f:SetFrameStrata("LOW")
    f:SetBackdrop({bgFile = WHITE, edgeFile = WHITE, edgeSize = 1})
    f:SetBackdropColor(.025, .025, .025, .95); f:SetBackdropBorderColor(.08, .08, .08, 1)
    f.bar = CreateFrame("StatusBar", nil, f); f.bar:EnableMouse(false)
    f.bar:SetPoint("TOPLEFT", 1, -1); f.bar:SetPoint("BOTTOMRIGHT", -1, 1)
    f.bar:SetStatusBarTexture(WHITE)
    f.percent = text(f.bar, 12); f.percent:SetPoint("CENTER")
    f.name = text(f, 10); f.name:SetPoint("BOTTOMLEFT", f, "TOPLEFT", 0, 3)
    f.level = text(f, 10); f.level:SetPoint("BOTTOMRIGHT", f, "TOPRIGHT", 0, 3)
    f.icons = {}; f:Hide()
    return {plate = plate, bounds = bounds, frame = f, auras = {}}
end

local function nativePoints(native)
    local health = native.HealthBarsContainer and native.HealthBarsContainer.healthBar
    local setup, styles = NamePlateSetupOptions, NamePlateConstants and NamePlateConstants.NAME_ANCHOR_STYLES
    local height = setup and A.Number(setup.healthBarHeight)
    if health and native.name and height and styles then
        local inside = setup.unitNameAnchorStyle == styles.InsideHealthBar
        return {
            {point = "TOPLEFT", relativeTo = inside and health or native.name, relativePoint = "TOPLEFT",
                offsetX = inside and -10 or -14, offsetY = inside and height / 2 or 0},
            {point = "BOTTOMRIGHT", relativeTo = health, relativePoint = "BOTTOMRIGHT", offsetX = 10, offsetY = -height / 2},
        }
    end
    return {
        {point = "TOPLEFT", relativeTo = native, relativePoint = "TOPLEFT", offsetX = 0, offsetY = 0},
        {point = "BOTTOMRIGHT", relativeTo = native, relativePoint = "BOTTOMRIGHT", offsetX = 0, offsetY = 0},
    }
end

local function bindClicks(record)
    local plate = record.plate
    if record.clickBound or record.clickFailed or not plate.SetHitTestPoints or
        A.Call(plate.CanChangeHitTestPoints, plate) ~= true then return end
    local ok, err = pcall(plate.SetHitTestPoints, plate, {
        {point = "TOPLEFT", relativeTo = record.frame, relativePoint = "TOPLEFT", offsetX = 0, offsetY = 0},
        {point = "BOTTOMRIGHT", relativeTo = record.frame, relativePoint = "BOTTOMRIGHT", offsetX = 0, offsetY = 0},
    })
    record.clickBound, record.clickFailed = ok, not ok
    if not ok then A.Print("Could not bind this nameplate's click area: " .. tostring(err)) end
end

local function restore(record)
    record.frame:Hide()
    local native = record.native
    if native and A.Call(native.GetParent, native) == record.plate then
        if record.clickBound and A.Call(record.plate.CanChangeHitTestPoints, record.plate) == true then
            A.Call(record.plate.SetHitTestPoints, record.plate, nativePoints(native))
        end
        A.Call(native.SetAlpha, native, record.alpha or 1)
    end
    record.clickBound, record.clickFailed = false, false
    record.native = nil
end

function A.Remove(unit)
    local r = A.units[unit]
    if r then restore(r); r.unit = nil; r.guid = nil; A.units[unit] = nil end
end

function A.Clear()
    for unit in pairs(A.units) do A.Remove(unit) end
    A.attacked = {}
end

function A.Add(unit)
    local guid = UnitGUID(unit)
    if type(guid) ~= "string" or not (guid:match("^Creature%-") or guid:match("^Vehicle%-")) then return end
    local plate = C_NamePlate.GetNamePlateForUnit(unit)
    if not plate or plate:IsForbidden() then return end
    local native = plate.UnitFrame
    local health = native and native.HealthBarsContainer and native.HealthBarsContainer.healthBar
    if not health or native:IsForbidden() then return end
    local record = A.records[plate]
    if not record then record = make(plate); A.records[plate] = record end
    if record.unit and record.unit ~= unit then A.Remove(record.unit) end
    if A.units[unit] and A.units[unit] ~= record then A.Remove(unit) end
    if record.native ~= native then
        restore(record)
        if A.nativeAlpha[native] == nil then A.nativeAlpha[native] = A.Number(A.Call(native.GetAlpha, native)) or 1 end
        record.native, record.alpha = native, A.nativeAlpha[native]
        record.bounds:ClearAllPoints(); record.bounds:SetAllPoints(health)
        record.frame:ClearAllPoints(); record.frame:SetAllPoints(record.bounds)
    end
    if record.guid ~= guid then record.auras = {} end
    record.unit, record.guid = unit, guid; A.units[unit] = record
    native:SetAlpha(0)
    A.Update(true, unit)
end

local function scan(record)
    local auras = {}
    for i = 1, 255 do
        local data
        if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
            data = C_UnitAuras.GetAuraDataByIndex(record.unit, i, "HARMFUL|PLAYER")
        elseif UnitDebuff then
            local name, icon, count, _, duration, expires, source, _, _, id = UnitDebuff(record.unit, i, "PLAYER")
            if name then data = {name = name, icon = icon, applications = count, duration = duration,
                expirationTime = expires, sourceUnit = source, spellId = id} end
        end
        if not data then break end
        local source, expires = data.sourceUnit, A.Number(data.expirationTime) or 0
        if source and (source == "player" or UnitIsUnit(source, "player")) and
            (expires == 0 or expires > GetTime()) then
            auras[#auras + 1] = {name = data.name, id = A.Number(data.spellId), icon = data.icon,
                expires = expires, count = A.Number(data.applications) or 0}
        end
    end
    record.auras = auras
end

local function icon(record, index)
    local f = record.frame.icons[index]
    if f then return f end
    f = CreateFrame("Frame", nil, record.frame, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:EnableMouse(false); f:SetBackdrop({edgeFile = WHITE, edgeSize = 1})
    f:SetBackdropBorderColor(.1, .1, .1, 1)
    f.texture = f:CreateTexture(nil, "ARTWORK"); f.texture:SetPoint("TOPLEFT", 1, -1)
    f.texture:SetPoint("BOTTOMRIGHT", -1, 1); f.texture:SetTexCoord(.07, .93, .07, .93)
    f.timer = text(f, 10); f.timer:SetPoint("CENTER")
    f.count = text(f, 9); f.count:SetPoint("BOTTOMRIGHT")
    record.frame.icons[index] = f
    return f
end

function A.Missing(record)
    if not UnitCanAttack("player", record.unit) then return false end
    local watch = A.db.watchDebuff
    if watch == "" then return #record.auras == 0 end
    local id = tonumber(watch)
    local name = id and A.Call(C_Spell and C_Spell.GetSpellName, id) or watch
    for _, aura in ipairs(record.auras) do
        if (id and aura.id == id) or (type(name) == "string" and type(aura.name) == "string" and
            aura.name:lower() == name:lower()) then return false end
    end
    return true
end

function A.Better(a, b)
    local aCritical, bCritical = a.fraction < .2, b.fraction < .2
    if aCritical ~= bCritical then return aCritical end
    if a.missing ~= b.missing then return a.missing end
    if a.health ~= b.health then return a.health < b.health end
    return a.guid < b.guid
end

function A.LevelColor(level)
    local player = A.Number(UnitLevel("player"))
    if level == -1 then return 1, .1, .1 end
    if not level or level < 1 or not player or player < 1 then return .7, .7, .7 end
    local gap = level - player
    if gap > 5 then return 1, .1, .1 end
    if gap >= 3 then return 1, .5, .25 end
    if gap >= -2 then return 1, 1, 0 end
    local color = A.Call(GetCreatureDifficultyColor, level)
    if type(color) == "table" and A.Number(color.r) and A.Number(color.g) and A.Number(color.b) then
        return color.r, color.g, color.b
    end
    -- Classic Era zero-XP threshold, for clients without the colour helper.
    local gray = player <= 5 and 0 or (player <= 39 and player - 5 - math.floor(player / 10) or
        player - 1 - math.floor(player / 5))
    if level <= gray then return .6, .6, .6 end
    return .25, .75, .25
end

local function render(record, now)
    local unit, f = record.unit, record.frame
    if not unit or UnitGUID(unit) ~= record.guid or not record.plate:IsShown() or UnitIsDeadOrGhost(unit) or
        (C_NamePlateManager and A.Call(C_NamePlateManager.IsNamePlateUnitBehindCamera, unit)) then
        f:Hide(); return false
    end
    -- Rebind safely if Blizzard replaces a pooled unit frame.
    if record.plate.UnitFrame ~= record.native then f:Hide(); return false end
    local scale = A.Number(A.Call(record.plate.GetEffectiveScale, record.plate))
    local uiScale = A.Number(A.Call(UIParent.GetEffectiveScale, UIParent)) or 1
    if scale and scale > 0 then
        f:SetScale(scale / uiScale); record.bounds:SetScale(scale / uiScale)
    end
    f:SetAlpha(A.Number(A.Call(record.plate.GetAlpha, record.plate)) or 1)
    record.native:SetAlpha(0)
    local hp, max = A.Number(UnitHealth(unit)), A.Number(UnitHealthMax(unit))
    record.health = hp and max and max > 0 and math.max(0, hp) or math.huge
    record.fraction = hp and max and max > 0 and math.max(0, math.min(1, hp / max)) or 2
    f.bar:SetMinMaxValues(0, 1); f.bar:SetValue(record.fraction <= 1 and record.fraction or 0)
    f.percent:SetText(record.fraction <= 1 and math.floor(record.fraction * 100 + .5) .. "%" or "?")
    local denied = A.Call(UnitIsTapDenied, unit) == true
    local r, g, b, border = .85, .12, .12, 1
    if denied then r, g, b, border = .55, .55, .55, .025
    elseif not UnitCanAttack("player", unit) then r, g, b, border = .1, .8, .2, .025
    elseif (A.Number(A.Call(UnitReaction, unit, "player")) or 3) >= 4 and
        A.Call(UnitAffectingCombat, unit) ~= true then r, g, b, border = 1, .82, 0, .025 end
    f.bar:SetStatusBarColor(r, g, b)
    record.borderShade = border
    f.name:SetText((UnitName(unit) or "") .. (denied and " [CLAIMED]" or ""))
    local level = A.Number(UnitLevel(unit))
    f.level:SetText(level == -1 and "Lv. ??" or (level and level > 0 and "Lv. " .. level or "Lv. ?"))
    f.level:SetTextColor(A.LevelColor(level))
    record.selected = UnitGUID("target") == record.guid
    for i = #record.auras, 1, -1 do
        if record.auras[i].expires > 0 and record.auras[i].expires <= now then table.remove(record.auras, i) end
    end
    local size, count = A.db.plateAuraSize, #record.auras
    for i, aura in ipairs(record.auras) do
        local child = icon(record, i); child:SetSize(size, size); child:ClearAllPoints()
        local columns = math.min(6, count)
        local rowCount = math.min(columns, count - math.floor((i - 1) / columns) * columns)
        child:SetPoint("BOTTOM", f, "TOP", ((i - 1) % columns - (rowCount - 1) / 2) * (size + 2),
            20 + math.floor((i - 1) / columns) * (size + 2))
        child.texture:SetTexture(aura.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
        child.timer:SetText(aura.expires > 0 and math.ceil(aura.expires - now) or "")
        child.count:SetText(aura.count > 1 and aura.count or ""); child:Show()
    end
    for i = count + 1, #f.icons do f.icons[i]:Hide() end
    record.missing = A.Missing(record)
    f:Show(); return true
end

function A.Update(refreshAuras, changedUnit)
    if not A.ready then return end
    local list, now = {}, GetTime()
    for _, record in pairs(A.units) do
        if refreshAuras and (not changedUnit or changedUnit == record.unit) and
            record.unit and UnitGUID(record.unit) == record.guid then scan(record) end
        if render(record, now) then list[#list + 1] = record end
    end
    table.sort(list, A.Better)
    local firstPriority = true
    for rank, record in ipairs(list) do
        local level = 30 + (#list - rank) * 8
        record.frame:SetFrameLevel(level)
        record.frame.bar:SetFrameLevel(level + 1)
        for _, child in ipairs(record.frame.icons) do child:SetFrameLevel(level + 2) end
        local priority = firstPriority and A.attacked[record.guid] == true and
            UnitCanAttack("player", record.unit) == true
        record.priority = priority
        -- Measure only our UIParent-based bounds. Bound click points follow this owned rectangle.
        local height = A.Number(A.Call(record.bounds.GetHeight, record.bounds)) or 0
        record.frame:ClearAllPoints()
        record.frame:SetPoint("BOTTOMLEFT", record.bounds, "BOTTOMLEFT", 0, 0)
        record.frame:SetPoint("TOPRIGHT", record.bounds, "TOPRIGHT", 0, priority and height or 0)
        local borderSize = (record.selected or priority) and 2 or 1
        if record.borderSize ~= borderSize then
            record.frame:SetBackdrop({bgFile = WHITE, edgeFile = WHITE, edgeSize = borderSize})
            record.frame:SetBackdropColor(.025, .025, .025, .95)
            record.frame.bar:ClearAllPoints()
            record.frame.bar:SetPoint("TOPLEFT", borderSize, -borderSize)
            record.frame.bar:SetPoint("BOTTOMRIGHT", -borderSize, borderSize)
            record.borderSize = borderSize
        end
        local shade = record.borderShade
        record.frame:SetBackdropBorderColor(shade, shade, shade, 1)
        bindClicks(record)
        if priority then firstPriority = false end
    end
end
