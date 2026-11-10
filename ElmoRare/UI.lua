local _, A = ...
local U = {}
A.UI = U
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"

local function label(parent, size, point, x, y, width)
    local text = parent:CreateFontString(nil, "OVERLAY")
    text:SetFont(FONT, size, "OUTLINE"); text:SetTextColor(1, 1, 1)
    text:SetPoint(point, x, y); text:SetWidth(width); text:SetJustifyH("LEFT")
    return text
end

function U.Sound()
    return A.Call(PlaySound, SOUNDKIT and SOUNDKIT.RAID_WARNING or 8959, "Master")
end

function U.Position()
    U.banner:ClearAllPoints()
    local p = A.db.position
    if type(p) == "table" and A.Text(p.point) and A.Text(p.relativePoint) and A.Number(p.x) and A.Number(p.y) then
        U.banner:SetPoint(p.point, UIParent, p.relativePoint, p.x, p.y)
    else U.banner:SetPoint("TOP", UIParent, "TOP", 0, -120) end
end

function U.Tooltip()
    local r = U.record
    if not r then return end
    local tip = U.tooltip
    tip:SetOwner(U.banner, "ANCHOR_RIGHT"); tip:ClearLines()
    tip:AddLine(r.name, 1, .82, 0)
    local rank = r.classification == "rareelite" and "Rare elite" or "Rare"
    tip:AddLine(rank .. " — Level " .. (r.level and r.level > 0 and r.level or "??"), 1, 1, 1)
    if r.preview then tip:AddLine("Preview only", .7, .7, .7)
    else
        tip:AddLine("Source: " .. A.Source(r.unit), .7, .7, .7)
        tip:AddLine("Last detected " .. math.max(0, math.floor(GetTime() - r.lastSeen)) .. "s ago", .7, .7, .7)
        if r.npcID then tip:AddLine("NPC ID: " .. r.npcID, .7, .7, .7) end
    end
    tip:AddLine("Target the rare, then press your ElmoRare skull key.", 1, 1, 1, true)
    tip:AddLine("Drag to move. Right-click to dismiss.", .7, .7, .7)
    tip:Show()
end

function U.Create()
    if U.banner then return end
    local f = CreateFrame("Frame", "ElmoRareAlert", UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    U.banner = f
    f:SetSize(350, 88); f:SetFrameStrata("HIGH"); f:SetClampedToScreen(true)
    f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
    f:SetBackdrop({bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1})
    f:SetBackdropColor(.025, .025, .025, .94); f:SetBackdropBorderColor(.85, .65, .15, 1)
    local icon = f:CreateTexture(nil, "ARTWORK")
    icon:SetTexture("Interface\\Icons\\INV_Misc_Spyglass_03"); icon:SetSize(36, 36); icon:SetPoint("TOPLEFT", 10, -14)
    U.title = label(f, 12, "TOPLEFT", 56, -10, 282); U.title:SetTextColor(1, .82, 0)
    U.name = label(f, 15, "TOPLEFT", 56, -30, 282)
    U.name:SetWordWrap(false); U.name:SetHeight(20)
    U.detail = label(f, 11, "TOPLEFT", 56, -58, 282)
    U.tooltip = CreateFrame("GameTooltip", "ElmoRareTooltip", UIParent, "GameTooltipTemplate")
    f:SetScript("OnEnter", U.Tooltip); f:SetScript("OnLeave", function() U.tooltip:Hide() end)
    f:SetScript("OnHide", function() U.tooltip:Hide() end)
    f:SetScript("OnMouseUp", function(_, button) if button == "RightButton" then U.Hide() end end)
    f:SetScript("OnDragStart", f.StartMoving)
    f:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local point, _, relativePoint, x, y = self:GetPoint()
        if A.Text(point) and A.Text(relativePoint) and A.Number(x) and A.Number(y) then
            A.db.position = {point = point, relativePoint = relativePoint, x = x, y = y}
        end
    end)
    U.Position(); f:Hide()
end

function U.Notify(record)
    U.record, U.expires = record, GetTime() + 12
    U.title:SetText(record.preview and "ElmoRare — preview" or "ElmoRare — rare detected")
    U.name:SetText(record.name)
    local level = record.level and record.level > 0 and record.level or "??"
    U.detail:SetText("Level " .. level .. " / " .. (record.classification == "rareelite" and "Rare elite" or "Rare") .. " / Hover for details")
    U.banner:Show()
end
function U.Hide() if U.banner then U.banner:Hide() end end
function U.Tick() if U.expires and GetTime() >= U.expires then U.Hide(); U.expires = nil end end

function U.CreateMarker()
    if U.marker or InCombatLockdown() then return end
    if not (SECURE_ACTIONS and type(SECURE_ACTIONS.raidtarget) == "function") then return end
    -- Standalone, static and separate from the dynamic alert. No unit-token
    -- rebinding, native handler replacement or automatic :Click() invocation.
    local b = CreateFrame("Button", "ElmoRareMarkTargetButton", UIParent, "SecureActionButtonTemplate")
    b:SetSize(1, 1); b:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", -10, -10); b:EnableMouse(false)
    b:RegisterForClicks("AnyDown", "AnyUp")
    b:SetAttribute("type", "raidtarget"); b:SetAttribute("unit", "target")
    b:SetAttribute("marker", 8); b:SetAttribute("action", "set"); b:SetAttribute("useOnKeyDown", true)
    U.marker = b
end
