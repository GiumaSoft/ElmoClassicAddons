local _, A = ...
local P = {dirty = true, records = {}, free = {}}
A.Pins = P
local library = LibStub("HereBeDragons-Pins-2.0")

local function hideTooltip(icon)
    if GameTooltip:IsOwned(icon) then GameTooltip:Hide() end
end
local function showTooltip(icon)
    local point = icon.waypoint
    if not point then return end
    GameTooltip:SetOwner(icon, "ANCHOR_CURSOR")
    GameTooltip:SetText("ElmoWaypoint · " .. icon.index, 1, .82, .15)
    if point.title ~= "" then GameTooltip:AddLine(point.title, 1, 1, 1, true) end
    GameTooltip:AddLine(string.format("%s · %.2f, %.2f", A.MapName(point.mapID), point.x * 100, point.y * 100), .7, .7, .7)
    GameTooltip:AddLine("Left-click to navigate", 1, .82, .15)
    GameTooltip:Show()
end
local function circle(icon, size, layer)
    local texture = icon:CreateTexture(nil, layer)
    texture:SetSize(size, size)
    texture:SetPoint("CENTER")
    texture:SetColorTexture(1, 1, 1)
    local mask = icon:CreateMaskTexture()
    mask:SetTexture("Interface\\CHARACTERFRAME\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
    mask:SetAllPoints(texture)
    texture:AddMaskTexture(mask)
    return texture
end
local function createIcon(size)
    local icon = CreateFrame("Button", nil, UIParent)
    icon:SetSize(size, size)
    icon:RegisterForClicks("LeftButtonUp")
    icon.ring = circle(icon, size, "BACKGROUND")
    circle(icon, size - 4, "BORDER"):SetVertexColor(.06, .06, .06)
    icon.number = icon:CreateFontString(nil, "OVERLAY")
    icon.number:SetFont(STANDARD_TEXT_FONT, 10, "OUTLINE")
    icon.number:SetPoint("CENTER")
    icon:SetScript("OnEnter", showTooltip)
    icon:SetScript("OnLeave", hideTooltip)
    icon:SetScript("OnHide", hideTooltip)
    icon:SetScript("OnClick", function(self) A.Select(self.index) end)
    icon:Hide()
    return icon
end
local function unregister(record)
    library:RemoveWorldMapIcon(P, record.world)
    library:RemoveMinimapIcon(P, record.mini)
    for _, icon in ipairs({record.world, record.mini}) do
        icon:Hide(); icon.waypoint = nil
    end
    record.point = nil
end
function P.Refresh()
    if not P.dirty then return end
    P.dirty = false
    for i = #P.records, #A.db.points + 1, -1 do
        local record = table.remove(P.records, i)
        unregister(record)
        P.free[#P.free + 1] = record
    end
    for i, point in ipairs(A.db.points) do
        local record = P.records[i]
        if not record then
            record = table.remove(P.free) or {world = createIcon(22), mini = createIcon(18)}
            P.records[i] = record
        end
        if record.point ~= point then
            unregister(record)
            -- HBD owns map transforms, zoom, rotation and visibility. Each icon
            -- is registered only under our reference, independently of the arrow.
            local world = library:AddWorldMapIconMap(P, record.world, point.mapID, point.x, point.y, HBD_PINS_WORLDMAP_SHOW_WORLD)
            local mini = library:AddMinimapIconMap(P, record.mini, point.mapID, point.x, point.y, true, true)
            if world and mini then record.point = point end
        end
        for _, icon in ipairs({record.world, record.mini}) do
            icon.waypoint, icon.index = point, i
            icon.number:SetText(i)
            if i == A.db.active then icon.ring:SetVertexColor(1, .82, .15)
            else icon.ring:SetVertexColor(.55, .48, .3) end
            if GameTooltip:IsOwned(icon) then showTooltip(icon) end
        end
    end
end
