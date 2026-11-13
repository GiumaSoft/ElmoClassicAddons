local _, A = ...
local S = {}
A.Settings = S
function S.Register()
    if S.panel then return end
    local p = CreateFrame("Frame", nil, UIParent); S.panel = p; p:Hide()
    local function label(text, y)
        local f = p:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        f:SetPoint("TOPLEFT", 16, y); f:SetWidth(530); f:SetJustifyH("LEFT"); f:SetText(text)
        return f
    end
    label("ElmoWaypoint", -16)
    label("/way x y [note] adds a waypoint. /way current [note] saves your current position. Hover circular pins for notes; left-click to navigate.", -52)
    local function check(key, text, y, callback)
        local c = CreateFrame("CheckButton", nil, p, "UICheckButtonTemplate")
        p[key] = c; c:SetSize(26, 26); c:SetPoint("TOPLEFT", 16, y)
        local caption = c:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        caption:SetPoint("LEFT", c, "RIGHT", 4, 0); caption:SetText(text)
        c:SetScript("OnClick", function(self) callback(self:GetChecked() == true) end)
    end
    check("showArrow", "Show waypoint arrow", -100, A.SetVisible)
    check("locked", "Lock arrow position (click-through)", -132, A.SetLocked)
    check("showCoordinates", "Show current coordinates", -164, A.Coordinates.SetVisible)
    check("coordinatesLocked", "Lock coordinates position (click-through)", -196, A.Coordinates.SetLocked)
    check("minimap", "Show minimap launcher (waypoint pins stay visible)", -228, function(visible) A.Minimap.SetVisible(visible) end)
    local function button(key, text, x, y, callback)
        local b = CreateFrame("Button", nil, p, "UIPanelButtonTemplate")
        p[key] = b; b:SetSize(220, 28); b:SetPoint("TOPLEFT", x, y); b:SetText(text); b:SetScript("OnClick", callback)
    end
    button("next", "Next waypoint", 16, -282, A.Next)
    button("remove", "Remove current waypoint", 252, -282, A.RemoveCurrent)
    button("reset", "Reset all waypoints", 16, -324, A.Reset)
    button("center", "Reset arrow position", 252, -324, A.Center)
    button("coordinatesCenter", "Reset coordinates position", 16, -366, A.Coordinates.Center)
    S.status = label("", -420)
    label("Drag the coordinates frame to move it; right-click for options. The minimap launcher toggles the arrow with left-click and opens options with right-click.", -452)
    label("Waypoints remain after arrival, reload and logout. Use Next, Remove or Reset to manage them. Missing position data pauses the arrow and coordinate display.", -510)
    p:SetScript("OnShow", S.Refresh)
    if Settings and Settings.RegisterCanvasLayoutCategory then
        S.category = Settings.RegisterCanvasLayoutCategory(p, "ElmoWaypoint"); Settings.RegisterAddOnCategory(S.category)
    elseif InterfaceOptions_AddCategory then p.name = "ElmoWaypoint"; InterfaceOptions_AddCategory(p) end
end
function S.Refresh()
    local p = S.panel
    if not p or not p:IsShown() then return end
    p.showArrow:SetChecked(A.db.showArrow); p.locked:SetChecked(A.db.locked); p.minimap:SetChecked(not A.db.minimap.hide)
    p.showCoordinates:SetChecked(A.db.showCoordinates); p.coordinatesLocked:SetChecked(A.db.coordinatesLocked)
    p.next:SetEnabled(#A.db.points > 1); p.remove:SetEnabled(A.Current() ~= nil); p.reset:SetEnabled(#A.db.points > 0)
    local point = A.Current()
    S.status:SetText(#A.db.points .. " saved waypoint(s)" .. (point and (" · " .. A.MapName(point.mapID)) or ""))
end
function S.Open()
    if S.category and Settings and Settings.OpenToCategory then Settings.OpenToCategory(S.category:GetID())
    elseif InterfaceOptionsFrame_OpenToCategory then InterfaceOptionsFrame_OpenToCategory(S.panel)
    else A.Print("/ewp reset | next | remove | show | hide | center") end
end
