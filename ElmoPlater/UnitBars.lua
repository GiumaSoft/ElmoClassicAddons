local _, A = ...
local B = {}
A.UnitBars = B
local WHITE = "Interface\\Buttons\\WHITE8X8"
local casterClasses = {MAGE = true, PRIEST = true, WARLOCK = true, PALADIN = true, SHAMAN = true, DRUID = true}

local function bar(parent, height)
    local f = CreateFrame("Frame", nil, parent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:EnableMouse(false); f:SetHeight(height)
    f:SetBackdrop({bgFile = WHITE, edgeFile = WHITE, edgeSize = 1})
    f:SetBackdropColor(.025, .025, .025, .95); f:SetBackdropBorderColor(.08, .08, .08, 1)
    f.bar = CreateFrame("StatusBar", nil, f); f.bar:EnableMouse(false)
    f.bar:SetPoint("TOPLEFT", 1, -1); f.bar:SetPoint("BOTTOMRIGHT", -1, 1)
    f.bar:SetStatusBarTexture(WHITE)
    f:Hide()
    return f
end

function B.Create(parent)
    parent.mana = bar(parent, 7)
    parent.mana:SetPoint("TOPLEFT", parent, "BOTTOMLEFT", 0, -2)
    parent.mana:SetPoint("TOPRIGHT", parent, "BOTTOMRIGHT", 0, -2)
    parent.mana.bar:SetStatusBarColor(.12, .35, .95)
    local cast = bar(parent, 16)
    parent.cast = cast
    cast.bar:ClearAllPoints()
    cast.bar:SetPoint("TOPLEFT", 18, -1); cast.bar:SetPoint("BOTTOMRIGHT", -1, 1)
    cast.remaining = cast.bar:CreateTexture(nil, "BACKGROUND")
    cast.remaining:SetAllPoints(cast.bar); cast.remaining:Hide()
    cast.icon = cast:CreateTexture(nil, "ARTWORK")
    cast.icon:SetSize(14, 14); cast.icon:SetPoint("LEFT", 1, 0)
    cast.icon:SetTexCoord(.07, .93, .07, .93)
    cast.name = cast.bar:CreateFontString(nil, "OVERLAY")
    cast.name:SetFont(STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF", 9, "OUTLINE")
    cast.name:SetTextColor(1, 1, 1); cast.name:SetJustifyH("LEFT"); cast.name:SetWordWrap(false)
    cast.name:SetPoint("TOPLEFT", 2, 0); cast.name:SetPoint("BOTTOMRIGHT", -2, 0)
    cast:SetScript("OnUpdate", function(self) self.bar:SetValue(GetTime() * 1000) end)
end

function B.Reset(parent)
    parent.mana:Hide(); parent.cast:Hide()
    parent.cast.name:SetText(""); parent.cast.icon:SetTexture(nil)
end

local function mana(record)
    local f, unit = record.frame.mana, record.unit
    local _, class = A.Call(UnitClass, unit)
    class = A.Text(class)
    if not A.db.showMana or A.Bool(A.Call(UnitIsPlayer, unit)) ~= false or
        not (class and casterClasses[class]) or A.Number(A.Call(UnitPowerType, unit)) ~= 0 then
        f:Hide(); return false
    end
    local maximum, current = A.Call(UnitPowerMax, unit, 0), A.Call(UnitPower, unit, 0)
    local max, value = A.Number(maximum), A.Number(current)
    if not (A.Secret(maximum) or max and max > 0) or not (A.Secret(current) or value) then
        f:Hide(); return false
    end
    -- Protected values are display inputs only; never divide or compare them.
    f.bar:SetMinMaxValues(0, maximum); f.bar:SetValue(current)
    f:Show()
    return true
end

local function hasName(name)
    return A.Secret(name) or A.Text(name) ~= nil
end

local function casting(record, now)
    local f, unit = record.frame.cast, record.unit
    if not A.db.showCast then f:Hide(); return end
    local name, _, texture, start, finish, _, _, locked = A.Call(UnitCastingInfo, unit)
    local channel = false
    if not hasName(name) then
        name, _, texture, start, finish, _, locked = A.Call(UnitChannelInfo, unit)
        channel = true
    end
    if not hasName(name) then f:Hide(); return end
    local publicStart, publicFinish = A.Number(start), A.Number(finish)
    if not (A.Secret(start) or publicStart) or not (A.Secret(finish) or publicFinish) or
        publicStart and publicFinish and (publicFinish <= publicStart or publicFinish <= now * 1000) then
        f:Hide(); return
    end
    -- Native min/max/value setters accept protected numbers. All three inputs
    -- use milliseconds; Lua never subtracts, scales or compares private times.
    f.bar:SetMinMaxValues(start, finish)
    f.bar:SetValue(now * 1000)
    f.bar:SetReverseFill(channel)
    local r, g, b = 1, .72, .15
    if A.Bool(locked) == true then r, g, b = .55, .55, .55
    elseif channel then r, g, b = .2, .8, .55 end
    -- Channels empty from the right: native elapsed fill covers the coloured
    -- background, leaving only the remaining portion visible on the left.
    f.remaining:SetShown(channel)
    if channel then
        f.remaining:SetColorTexture(r, g, b, 1)
        f.bar:SetStatusBarColor(.025, .025, .025)
    else f.bar:SetStatusBarColor(r, g, b) end
    f.name:SetText(name)
    if A.Secret(texture) then f.icon:SetTexture(texture)
    else f.icon:SetTexture(A.Number(texture) or A.Text(texture) or "Interface\\Icons\\INV_Misc_QuestionMark") end
    f:Show()
end

function B.Update(record, now)
    local hasMana = mana(record)
    local f = record.frame.cast
    f:ClearAllPoints()
    f:SetPoint("TOPLEFT", record.frame, "BOTTOMLEFT", 0, hasMana and -11 or -2)
    f:SetPoint("TOPRIGHT", record.frame, "BOTTOMRIGHT", 0, hasMana and -11 or -2)
    casting(record, now)
end
