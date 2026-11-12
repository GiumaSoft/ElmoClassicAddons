local _, A = ...
local M = {}
A.Minimap = M

function M.SetVisible(visible)
    A.db.minimap.hide = visible ~= true
    local icons = LibStub("LibDBIcon-1.0")
    if A.db.minimap.hide then icons:Hide("ElmoLFM") else icons:Show("ElmoLFM") end
end

function M.Register()
    if M.broker then return end
    local db = A.db
    if type(db.minimap) ~= "table" then db.minimap = {} end
    db.minimap.minimapPos = (A.Number(tonumber(db.minimap.minimapPos)) or 190) % 360
    db.minimap.hide = db.minimap.hide == true
    M.broker = LibStub("LibDataBroker-1.1"):NewDataObject("ElmoLFM", {
        type = "launcher",
        text = "ElmoLFM",
        icon = "Interface\\Icons\\INV_Misc_Spyglass_03",
        OnClick = function(_, button)
            if button == "RightButton" then A.Settings.Open() else A.UI.Toggle() end
        end,
        OnTooltipShow = function(tooltip)
            tooltip:AddLine("ElmoLFM", 1, .82, 0)
            tooltip:AddLine("Find players by zone and level.", 1, 1, 1)
            tooltip:AddLine("Left click: recruitment window.", .6, .85, 1)
            tooltip:AddLine("Right click: options. Drag to reposition.", .6, .85, 1)
        end,
    })
    LibStub("LibDBIcon-1.0"):Register("ElmoLFM", M.broker, db.minimap)
end
