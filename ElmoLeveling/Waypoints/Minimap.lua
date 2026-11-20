local _, addon = ...
local A = addon.Waypoints
local M = {}
A.Minimap = M
local NAME = "ElmoLeveling"
local icons = LibStub and LibStub("LibDBIcon-1.0", true)
local broker = LibStub and LibStub("LibDataBroker-1.1", true)

function M.Refresh()
    if M.broker then icons:Refresh(NAME, A.db.minimap) end
end

function M.SetVisible(visible)
    A.db.minimap.hide = visible ~= true
    M.Refresh()
    A.Settings.Refresh()
end

function M.Register()
    if M.broker or not (broker and icons) then return end
    M.broker = broker:NewDataObject(NAME, {
        type = "launcher", text = NAME, icon = "Interface\\Icons\\INV_Misc_Map_01",
        OnClick = function(_, button)
            if button == "RightButton" then
                A.ClearSelection()
            elseif button == "LeftButton" then
                A.SetVisible(not A.db.showArrow)
            end
        end,
        OnTooltipShow = function(tooltip)
            tooltip:AddLine(NAME, 1, .82, 0)
            tooltip:AddLine("/way x y [note]", 1, 1, 1)
            tooltip:AddLine("/way current [note]: save your position.", 1, 1, 1)
            tooltip:AddLine(#A.db.points .. " saved waypoint(s)", .8, .8, .8)
            tooltip:AddLine("Left click: pause or resume the selected waypoint.", .6, .85, 1)
            tooltip:AddLine("Right click: clear the destination.", .6, .85, 1)
            tooltip:AddLine("Drag to reposition the minimap icon.", .6, .85, 1)
        end,
    })
    icons:Register(NAME, M.broker, A.db.minimap)
end
