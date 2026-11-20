local _, addon = ...
local A = addon.Waypoints
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
    label("Waypoints", -16)
    label("/way x y [note] adds a waypoint. /way current [note] saves your current position. Hover circular pins for notes; left-click to navigate.", -52)
    local function check(key, text, y, callback)
        local c = CreateFrame("CheckButton", nil, p, "UICheckButtonTemplate")
        p[key] = c; c:SetSize(26, 26); c:SetPoint("TOPLEFT", 16, y)
        local caption = c:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        caption:SetPoint("LEFT", c, "RIGHT", 4, 0); caption:SetText(text)
        c:SetScript("OnClick", function(self) callback(self:GetChecked() == true) end)
    end
    check("showArrow", "Follow selected waypoint", -100, A.SetVisible)
    check("locked", "Lock compass position (click-through)", -132, A.SetLocked)
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
    button("center", "Reset compass position", 252, -324, A.Center)
    button("coordinatesCenter", "Reset coordinates position", 16, -366, A.Coordinates.Center)
    S.status = label("", -420)
    p:SetScript("OnShow", S.Refresh)
    if addon.UI.optionsCategory and Settings and Settings.RegisterCanvasLayoutSubcategory then
        S.category = Settings.RegisterCanvasLayoutSubcategory(addon.UI.optionsCategory, p, "Waypoints")
    elseif InterfaceOptions_AddCategory then
        p.name, p.parent = "Waypoints", "ElmoLeveling"
        InterfaceOptions_AddCategory(p)
    end
end
function S.Refresh()
    local p = S.panel
    if not p or not p:IsShown() then return end
    local point = A.Current()
    p.showArrow:SetEnabled(point ~= nil)
    p.showArrow:SetChecked(A.db.showArrow); p.locked:SetChecked(A.db.locked); p.minimap:SetChecked(not A.db.minimap.hide)
    p.showCoordinates:SetChecked(A.db.showCoordinates); p.coordinatesLocked:SetChecked(A.db.coordinatesLocked)
    local count = #A.db.points
    p.next:SetEnabled(count > 1 or count == 1 and not point)
    p.remove:SetEnabled(point ~= nil)
    p.reset:SetEnabled(count > 0)
    S.status:SetText(#A.db.points .. " saved waypoint(s)" .. (point and (" · " .. A.MapName(point.mapID)) or ""))
end
function S.Open()
    if S.category and Settings and Settings.OpenToCategory then Settings.OpenToCategory(S.category:GetID())
    elseif InterfaceOptionsFrame_OpenToCategory then InterfaceOptionsFrame_OpenToCategory(S.panel)
    else A.Print("/ewp reset | next | remove | resume | pause | center") end
end
