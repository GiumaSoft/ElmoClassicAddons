local _, A = ...
local U = {}
A.UI = U
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local function label(parent, text, size, x, y, width)
    local f = parent:CreateFontString(nil, "OVERLAY")
    f:SetFont(FONT, size, "OUTLINE"); f:SetPoint("TOPLEFT", x, y); f:SetWidth(width)
    f:SetTextColor(.93, .91, .84); f:SetJustifyH("CENTER"); f:SetWordWrap(false); f:SetText(text)
    return f
end
function U.Place()
    local f = U.panel; f:ClearAllPoints()
    local p = A.db.position
    if p then f:SetPoint("CENTER", UIParent, "CENTER", p.x, p.y)
    else f:SetPoint("TOP", UIParent, "TOP", 0, -130) end
end
function U.Create()
    if U.panel then return end
    local f = CreateFrame("Frame", "ElmoWaypointArrow", UIParent, "BackdropTemplate")
    U.panel = f; f:SetSize(200, 148); f:SetFrameStrata("MEDIUM"); f:SetMovable(true); f:SetClampedToScreen(true)
    f:SetBackdrop({bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1})
    f:SetBackdropColor(.025, .025, .025, .88); f:SetBackdropBorderColor(.68, .52, .18, .9)
    f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", function(self) if not A.db.locked then self:StartMoving() end end)
    f:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local x, y = self:GetCenter(); local cx, cy = UIParent:GetCenter()
        if A.Number(x) and A.Number(y) and A.Number(cx) and A.Number(cy) then A.db.position = {x = x - cx, y = y - cy} end
        U.Place()
    end)
    f:SetScript("OnMouseUp", function(_, button) if button == "RightButton" then A.Settings.Open() end end)
    U.title = label(f, "ElmoWaypoint", 12, 8, -7, 150); U.title:SetTextColor(1, .82, 0)
    U.count = label(f, "", 10, 160, -8, 32)
    U.arrow = CreateFrame("Frame", nil, f); U.arrow:SetSize(60, 60); U.arrow:SetPoint("TOP", 0, -27); U.arrow:EnableMouse(false)
    U.lines = {}
    for i = 1, 3 do
        local back = U.arrow:CreateLine(nil, "ARTWORK", nil, 0)
        back:SetThickness(8); back:SetColorTexture(.12, .08, .025, 1)
        local front = U.arrow:CreateLine(nil, "ARTWORK", nil, 1)
        front:SetThickness(4); front:SetColorTexture(1, .82, .15, 1)
        U.lines[i] = {back = back, front = front}
    end
    U.distance = label(f, "", 13, 8, -90, 184)
    U.target = label(f, "", 11, 8, -110, 184)
    U.coordinates = label(f, "", 10, 8, -128, 184); U.coordinates:SetTextColor(.65, .65, .65)
    U.Place(); f:Hide()
end
function U.Direction(angle, arrived)
    local c, s = math.cos(angle), math.sin(angle)
    local function rotate(x, y) return x * c - y * s, x * s + y * c end
    for i, segment in ipairs({{0, -22, 0, 24}, {0, 24, -15, 7}, {0, 24, 15, 7}}) do
        local sx, sy = rotate(segment[1], segment[2]); local ex, ey = rotate(segment[3], segment[4])
        local pair = U.lines[i]
        for _, line in ipairs({pair.back, pair.front}) do
            line:SetStartPoint("CENTER", U.arrow, sx, sy); line:SetEndPoint("CENTER", U.arrow, ex, ey)
        end
        if arrived then pair.front:SetColorTexture(.35, 1, .45, 1)
        else pair.front:SetColorTexture(1, .82, .15, 1) end
    end
end
function U.Update(point, state)
    U.panel:EnableMouse(not A.db.locked)
    if not point or not A.db.showArrow then U.panel:Hide(); return end
    U.panel:Show()
    U.count:SetText(A.db.active .. "/" .. #A.db.points)
    U.target:SetText(point.title ~= "" and point.title or A.MapName(point.mapID))
    U.coordinates:SetText(string.format("%.2f, %.2f · %s", point.x * 100, point.y * 100, A.MapName(point.mapID)))
    U.arrow:SetShown(state and state.angle ~= nil)
    if state and state.angle then U.Direction(state.angle, state.arrived) end
    if state and state.status then U.distance:SetText(state.status)
    elseif state and state.distance then U.distance:SetText((state.arrived and "Arrived · " or "") .. math.floor(state.distance + .5) .. " yd")
    else U.distance:SetText("Position unavailable") end
end
