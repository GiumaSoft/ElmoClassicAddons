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
    f.header = CreateFrame("Frame", nil, f); f.header:EnableMouse(false)
    f.header:SetPoint("BOTTOM", f, "TOP", 0, 3); f.header:SetHeight(14)
    f.name = text(f.header, 10); f.name:SetPoint("LEFT", f.header, "LEFT", 0, 0)
    f.name:SetHeight(14); f.name:SetJustifyH("LEFT"); f.name:SetWordWrap(false)
    f.level = text(f.header, 10); f.level:SetPoint("LEFT", f.name, "RIGHT", 6, 0)
    f.level:SetHeight(14); f.level:SetJustifyH("LEFT"); f.level:SetWordWrap(false)
    f.icons = {}; f:Hide()
    return {plate = plate, bounds = bounds, frame = f, auras = {}, auraContainer = A.Auras.Create(f)}
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
    if record.auraContainer then record.auraContainer:SetEnabled(false); record.auraContainer:Hide() end
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
    unit = A.Text(unit)
    if not unit then return end
    local guid = A.Text(A.Call(UnitGUID, unit))
    if not guid or not (guid:match("^Creature%-") or guid:match("^Vehicle%-")) then
        A.Remove(unit); return
    end
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
    if record.guid ~= guid then record.auras, record.aurasKnown = {}, false end
    record.unit, record.guid = unit, guid; A.units[unit] = record
    if record.auraContainer then
        record.auraContainer:SetUnit(unit); record.auraContainer:SetEnabled(true); record.auraContainer:Show()
    end
    native:SetAlpha(0)
    A.Update(true, unit)
end

local function scan(record)
    if A.Auras.Restricted() then
        -- The container draws restricted auras. Rule logic must not query them.
        record.auras, record.aurasKnown = {}, false
        return
    end
    local auras, batch = {}, nil
    record.aurasKnown = true
    if C_UnitAuras and C_UnitAuras.GetUnitAuras then
        -- Forever's native nameplates use this API. Indexed aura queries can
        -- be unavailable even when the batch supplies drawable display fields.
        local ok
        ok, batch = pcall(C_UnitAuras.GetUnitAuras, record.unit, "HARMFUL|PLAYER", 255)
        if not ok or A.Secret(batch) or type(batch) ~= "table" or
            (type(canaccesstable) == "function" and not canaccesstable(batch)) then
            record.auras, record.aurasKnown = {}, false
            return
        end
    end
    for i = 1, 255 do
        local data
        if batch then data = batch[i]
        elseif C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
            local ok
            ok, data = pcall(C_UnitAuras.GetAuraDataByIndex, record.unit, i, "HARMFUL|PLAYER")
            if not ok then record.aurasKnown = false; break end
        elseif UnitDebuff then
            local name, icon, count, _, duration, expires, source, _, _, id = UnitDebuff(record.unit, i, "PLAYER")
            if name then data = {name = name, icon = icon, applications = count, duration = duration,
                expirationTime = expires, sourceUnit = source, spellId = id} end
        end
        if A.Secret(data) then record.aurasKnown = false; break end
        if type(data) ~= "table" then break end
        if type(canaccesstable) == "function" and not canaccesstable(data) then record.aurasKnown = false; break end
        local source, expires = A.Text(data.sourceUnit), A.Number(data.expirationTime) or 0
        if A.Secret(data.sourceUnit) or A.Secret(data.spellId) then record.aurasKnown = false end
        -- HARMFUL|PLAYER already filters ownership when the caster is withheld.
        if (not source or source == "player" or A.Bool(A.Call(UnitIsUnit, source, "player")) == true) and
            (expires == 0 or expires > GetTime()) then
            local texture = data.icon
            if not A.Secret(texture) then
                texture = A.Number(texture) or A.Text(texture) or "Interface\\Icons\\INV_Misc_QuestionMark"
            end
            A.Rules.Observe(data.spellId, data.name, data.icon)
            auras[#auras + 1] = {name = A.Text(data.name), id = A.Number(data.spellId), icon = texture,
                expires = expires, count = A.Number(data.applications) or 0}
        end
    end
    record.auras = auras
    -- A visible personal harmful aura is evidence even when the combat log is unavailable.
    if #auras > 0 and A.Bool(A.Call(UnitAffectingCombat, "player")) == true then
        A.attacked[record.guid] = true
    end
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

-- Secondary layering only. The chosen rule target is explicitly placed in front.
function A.Better(a, b)
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
    local guid = unit and A.Text(A.Call(UnitGUID, unit))
    local health, maximum = A.Call(UnitHealth, unit), A.Call(UnitHealthMax, unit)
    local hp, max = A.Number(health), A.Number(maximum)
    local privateHealth = A.Secret(health) or A.Secret(maximum)
    -- Protected health can go directly to display APIs; missing data cannot.
    if not guid or not (A.Secret(health) or hp) or not (A.Secret(maximum) or max) then
        if record.native then A.Call(record.native.SetAlpha, record.native, record.alpha or 1) end
        record.priority = false
        f:ClearAllPoints(); f:SetAllPoints(record.bounds)
        f:Hide(); return false
    end
    if not unit or guid ~= record.guid or not record.plate:IsShown() or A.Bool(A.Call(UnitIsDeadOrGhost, unit)) == true or
        A.Bool(A.Call(C_NamePlateManager and C_NamePlateManager.IsNamePlateUnitBehindCamera, unit)) == true then
        f:Hide(); return false
    end
    -- Rebind safely if Blizzard replaces a pooled unit frame.
    if record.plate.UnitFrame ~= record.native then f:Hide(); return false end
    -- Public personal threat replaces combat-log evidence on restricted clients.
    if not A.attacked[guid] and not A.CombatLogAvailable() and
        A.Bool(A.Call(UnitAffectingCombat, "player")) == true and
        A.Number(A.Call(UnitThreatSituation, "player", unit)) then
        A.attacked[guid] = true
    end
    local scale = A.Number(A.Call(record.plate.GetEffectiveScale, record.plate))
    local uiScale = A.Number(A.Call(UIParent.GetEffectiveScale, UIParent)) or 1
    if scale and scale > 0 then
        f:SetScale(scale / uiScale); record.bounds:SetScale(scale / uiScale)
    end
    f:SetAlpha(A.Number(A.Call(record.plate.GetAlpha, record.plate)) or 1)
    record.native:SetAlpha(0)
    record.health = hp and max and max > 0 and math.max(0, hp) or math.huge
    record.fraction = hp and max and max > 0 and math.max(0, math.min(1, hp / max)) or 2
    record.privateHealth = privateHealth
    if privateHealth then
        f.bar:SetMinMaxValues(0, maximum); f.bar:SetValue(health)
        local curve = CurveConstants and CurveConstants.ScaleTo100
        local percent = curve and A.Call(UnitHealthPercent, unit, true, curve)
        if A.Secret(percent) or A.Number(percent) then
            f.percent:SetFormattedText("%.0f%%", percent)
        else f.percent:SetText("") end
    else
        f.bar:SetMinMaxValues(0, 1); f.bar:SetValue(record.fraction <= 1 and record.fraction or 0)
        f.percent:SetText(record.fraction <= 1 and math.floor(record.fraction * 100 + .5) .. "%" or "?")
    end
    local denied = A.Bool(A.Call(UnitIsTapDenied, unit)) == true
    local r, g, b, border = .85, .12, .12, 1
    if denied then r, g, b, border = .55, .55, .55, .025
    elseif A.Bool(A.Call(UnitCanAttack, "player", unit)) == false then r, g, b, border = .1, .8, .2, .025
    elseif (A.Number(A.Call(UnitReaction, unit, "player")) or 3) >= 4 and
        (not UnitAffectingCombat or A.Bool(A.Call(UnitAffectingCombat, unit)) == false) then
        r, g, b, border = 1, .82, 0, .025
    end
    f.bar:SetStatusBarColor(r, g, b)
    record.borderShade = border
    f.name:SetText((A.Text(A.Call(UnitName, unit)) or "") .. (denied and " [CLAIMED]" or ""))
    local level = A.Number(UnitLevel(unit))
    f.level:SetText(level == -1 and "Lv. ??" or (level and level > 0 and "Lv. " .. level or "Lv. ?"))
    f.level:SetTextColor(A.LevelColor(level))
    -- Measure only our own text; center the complete name/level group, not the bar width.
    local nameWidth = A.Number(A.Call(f.name.GetStringWidth, f.name)) or 0
    local levelWidth = A.Number(A.Call(f.level.GetStringWidth, f.level)) or 0
    f.header:SetWidth(nameWidth + 6 + levelWidth)
    record.selected = A.Text(A.Call(UnitGUID, "target")) == record.guid
    for i = #record.auras, 1, -1 do
        if record.auras[i].expires > 0 and record.auras[i].expires <= now then table.remove(record.auras, i) end
    end
    A.Auras.Update(record)
    local size, count = A.db.plateAuraSize, record.auraContainer and 0 or #record.auras
    for i = 1, count do
        local aura = record.auras[i]
        local child = icon(record, i); child:SetSize(size, size); child:ClearAllPoints()
        local columns = math.min(6, count)
        local rowCount = math.min(columns, count - math.floor((i - 1) / columns) * columns)
        child:SetPoint("BOTTOM", f, "TOP", ((i - 1) % columns - (rowCount - 1) / 2) * (size + 2),
            20 + math.floor((i - 1) / columns) * (size + 2))
        child.texture:SetTexture(aura.icon)
        child.timer:SetText(aura.expires > 0 and math.ceil(aura.expires - now) or "")
        child.count:SetText(aura.count > 1 and aura.count or ""); child:Show()
    end
    for i = count + 1, #f.icons do f.icons[i]:Hide() end
    f:Show(); return true
end

function A.Update(refreshAuras, changedUnit)
    if not A.ready then return end
    local list, now = {}, GetTime()
    A.privateHealthActive = false
    for _, record in pairs(A.units) do
        if refreshAuras and (not changedUnit or changedUnit == record.unit or
            A.Bool(A.Call(UnitIsUnit, changedUnit, record.unit)) == true) and
            record.unit and A.Text(A.Call(UnitGUID, record.unit)) == record.guid then scan(record) end
        if render(record, now) then
            list[#list + 1] = record
            if record.privateHealth then A.privateHealthActive = true end
        end
    end
    table.sort(list, A.Better)
    A.priorityTarget = A.Rules.Choose(list, now)
    for rank, record in ipairs(list) do
        local level = 30 + (#list - rank) * 8
        local priority = record == A.priorityTarget
        if priority then level = 30 + #list * 8 end
        record.frame:SetFrameLevel(level); record.frame.bar:SetFrameLevel(level + 1)
        record.frame.header:SetFrameLevel(level + 2)
        if record.auraContainer then record.auraContainer:SetFrameLevel(level + 2) end
        for _, child in ipairs(record.frame.icons) do child:SetFrameLevel(level + 2) end
        record.priority = priority
        -- Measure only our UIParent-based bounds. Bound click points follow this owned rectangle.
        local height = A.Number(A.Call(record.bounds.GetHeight, record.bounds)) or 0
        record.frame:ClearAllPoints()
        record.frame:SetPoint("BOTTOMLEFT", record.bounds, "BOTTOMLEFT", 0, 0)
        record.frame:SetPoint("TOPRIGHT", record.bounds, "TOPRIGHT", 0, height * (priority and 3 or 1))
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
    end
    if A.Settings then A.Settings.Tick(now) end
end
