local _, A = ...
local M = {}
A.Minimap = M
function M.SetVisible(visible)
    A.db.minimap.hide = visible ~= true
    local icons = LibStub("LibDBIcon-1.0")
    if A.db.minimap.hide then icons:Hide("ElmoWaypoint") else icons:Show("ElmoWaypoint") end
end
function M.Register()
    if M.broker then return end
    M.broker = LibStub("LibDataBroker-1.1"):NewDataObject("ElmoWaypoint", {
        type = "launcher", text = "ElmoWaypoint", icon = "Interface\\Icons\\INV_Misc_Map_01",
        OnClick = function(_, button)
            if button == "RightButton" then A.Settings.Open() else A.SetVisible(not A.db.showArrow) end
        end,
        OnTooltipShow = function(tooltip)
            tooltip:AddLine("ElmoWaypoint", 1, .82, 0)
            tooltip:AddLine("/way x y [note]", 1, 1, 1)
            tooltip:AddLine("/way current [note]: save your position.", 1, 1, 1)
            tooltip:AddLine(#A.db.points .. " saved waypoint(s)", .8, .8, .8)
            tooltip:AddLine("Left click: show/hide arrow.", .6, .85, 1)
            tooltip:AddLine("Right click: options and Reset all waypoints.", .6, .85, 1)
            tooltip:AddLine("Drag to reposition the minimap icon.", .6, .85, 1)
        end,
    })
    LibStub("LibDBIcon-1.0"):Register("ElmoWaypoint", M.broker, A.db.minimap)
end
