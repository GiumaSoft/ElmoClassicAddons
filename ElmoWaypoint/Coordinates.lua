local _, A = ...
local C = {}
A.Coordinates = C

function C.Place()
    C.panel:ClearAllPoints()
    local position = A.db.coordinatesPosition
    if position then C.panel:SetPoint("CENTER", UIParent, "CENTER", position.x, position.y)
    else C.panel:SetPoint("TOP", UIParent, "TOP", 0, -70) end
end
function C.Center() A.db.coordinatesPosition = nil; C.Place() end
function C.SetVisible(visible) A.db.showCoordinates = visible == true; A.Tick() end
function C.SetLocked(locked) A.db.coordinatesLocked = locked == true; A.Tick() end
function C.Create()
    if C.panel then return end
    local frame = CreateFrame("Frame", "ElmoWaypointCoordinates", UIParent, "BackdropTemplate")
    C.panel = frame
    frame:SetSize(220, 48); frame:SetFrameStrata("MEDIUM")
    frame:SetMovable(true); frame:SetClampedToScreen(true)
    frame:SetBackdrop({bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1})
    frame:SetBackdropColor(.025, .025, .025, .88); frame:SetBackdropBorderColor(.68, .52, .18, .9)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", function(self) if not A.db.coordinatesLocked then self:StartMoving() end end)
    frame:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local x, y = self:GetCenter(); local cx, cy = UIParent:GetCenter()
        if A.Number(x) and A.Number(y) and A.Number(cx) and A.Number(cy) then
            A.db.coordinatesPosition = {x = x - cx, y = y - cy}
        end
        C.Place()
    end)
    frame:SetScript("OnMouseUp", function(_, button) if button == "RightButton" then A.Settings.Open() end end)
    C.zone = frame:CreateFontString(nil, "OVERLAY")
    C.zone:SetFont(STANDARD_TEXT_FONT, 10, "OUTLINE")
    C.zone:SetPoint("TOP", 0, -6); C.zone:SetWidth(204); C.zone:SetWordWrap(false)
    C.zone:SetTextColor(.7, .7, .7)
    C.value = frame:CreateFontString(nil, "OVERLAY")
    C.value:SetFont(STANDARD_TEXT_FONT, 15, "OUTLINE")
    C.value:SetPoint("TOP", 0, -23); C.value:SetWidth(204); C.value:SetWordWrap(false)
    C.value:SetTextColor(1, .82, .15)
    C.Place(); frame:Hide()
end
function C.Update(position)
    C.panel:EnableMouse(not A.db.coordinatesLocked)
    C.panel:SetShown(A.db.showCoordinates)
    if not A.db.showCoordinates then return end
    C.zone:SetText(position and A.MapName(position.mapID) or "Position unavailable")
    C.value:SetText(position and string.format("%.2f, %.2f", position.x * 100, position.y * 100) or "--.--, --.--")
end
