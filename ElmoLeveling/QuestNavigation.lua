local _, A = ...
local N = {}
A.QuestNavigation = N

local WIDTH, HALF_ANGLE = 456, math.pi / 2
local WHITE = "Interface\\Buttons\\WHITE8X8"
local MEDIA = "Interface\\AddOns\\ElmoLeveling\\Media\\"
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local GOLD = {1, .81, .34}
local directions = {"N", "NW", "W", "SW", "S", "SE", "E", "NE"}
local refreshed, tracked, destinations, active = 0, nil, {}, {}
local compass, beacon

local function number(value)
    if not A.IsSecret(value) and type(value) == "number" and value == value and math.abs(value) < math.huge then
        return value
    end
end

local function equals(value, expected)
    return not A.IsSecret(value) and value == expected
end

local function trackingQuest(id)
    if not (id and C_SuperTrack) then return false end
    if not equals(A.Call(C_SuperTrack.GetSuperTrackedQuestID), id) or
        not equals(A.Call(C_SuperTrack.IsSuperTrackingQuest), true) or
        equals(A.Call(C_SuperTrack.IsSuperTrackingUserWaypoint), true) then return false end
    local types = Enum and Enum.SuperTrackingType
    return not (types and types.Quest and C_SuperTrack.GetHighestPrioritySuperTrackingType) or
        equals(A.Call(C_SuperTrack.GetHighestPrioritySuperTrackingType), types.Quest)
end

local function publicTable(value)
    if not A.IsSecret(value) and type(value) == "table" and not (issecrettable and issecrettable(value)) then return value end
end

local function world(map, position)
    if A.IsSecret(position) or not position then return end
    local instance, vector = A.Call(C_Map and C_Map.GetWorldPosFromMapPos, map, position)
    if not A.IsNumber(instance) or A.IsSecret(vector) or not vector then return end
    local north, west = A.Call(function() return vector:GetXY() end)
    return instance, number(north), number(west)
end

local function destination(map, x, y, id)
    if not A.IsNumber(map) or map <= 0 or not A.IsNumber(x) or x > 1 or not A.IsNumber(y) or y > 1 or
        (id and x == 0 and y == 0) then return end
    local instance, north, west = world(map, A.Call(CreateVector2D, x, y))
    if north and west then return {id = id, instance = instance, north = north, west = west} end
end

local function refresh(map)
    tracked = A.Call(C_SuperTrack and C_SuperTrack.GetSuperTrackedQuestID)
    if not A.IsNumber(tracked) or tracked <= 0 then tracked = nil end
    destinations, active = {}, {}
    if not C_QuestLog then tracked = nil; return end
    local function add(id)
        if not A.IsNumber(id) or id <= 0 or active[id] then return end
        local done = A.Call(C_QuestLog.IsComplete, id)
        local accepted = A.Call(C_QuestLog.IsOnQuest, id)
        if A.IsSecret(done) or A.IsSecret(accepted) or done == true or accepted == false then return end
        active[id] = A.Text(A.Call(C_QuestLog.GetTitleForQuestID, id)) or "Tracked quest"
    end
    add(tracked)
    local watches = A.Call(C_QuestLog.GetNumQuestWatches)
    if A.IsNumber(watches) then
        for i = 1, math.min(watches, 50) do add(A.Call(C_QuestLog.GetQuestIDForQuestWatchIndex, i)) end
    end
    if tracked and not active[tracked] then tracked = nil end
    if not (map and (A.db.questCompass or A.db.questArrow) and next(active)) then return end
    local onMap = {}
    local pins = publicTable(A.Call(C_QuestLog.GetQuestsOnMap, map))
    for _, pin in ipairs(pins or {}) do
        if publicTable(pin) and A.IsNumber(pin.questID) and active[pin.questID] then onMap[pin.questID] = pin end
    end
    for id in pairs(active) do
        local nextMap, x, y = A.Call(C_QuestLog.GetNextWaypoint, id)
        local point = destination(nextMap, x, y, id)
        if not point then
            x, y = A.Call(C_QuestLog.GetNextWaypointForMap, id, map)
            point = destination(map, x, y, id)
        end
        local pin = onMap[id]
        if not point and pin then point = destination(map, pin.x, pin.y, id) end
        if not point and id == tracked and trackingQuest(id) then
            x, y = A.Call(C_Navigation and C_Navigation.GetNextWaypointForMap, map)
            point = destination(map, x, y, id)
        end
        if point then destinations[#destinations + 1] = point end
    end
end

local function label(parent, size, color)
    local text = parent:CreateFontString(nil, "OVERLAY")
    text:SetFont(FONT, size, "OUTLINE")
    text:SetTextColor(unpack(color))
    return text
end

local function hidePinTooltip(pin)
    if GameTooltip and GameTooltip:IsOwned(pin) then GameTooltip:Hide() end
end

local function showPinTooltip(pin)
    if not GameTooltip or not pin.quests then return end
    GameTooltip:SetOwner(pin, "ANCHOR_CURSOR")
    for i, id in ipairs(pin.quests) do
        local title = active[id] or "Tracked quest"
        if i == 1 then GameTooltip:SetText(title)
        else GameTooltip:AddLine(title, 1, .81, .34, true) end
        local targets = A.QuestKills.TargetsForQuest(id)
        if targets then
            for _, objective in ipairs(targets) do
                GameTooltip:AddLine(objective.name .. "  " .. objective.done .. "/" .. objective.total, .92, .91, .85, true)
            end
        end
    end
    GameTooltip:Show()
end

local function createPin(band)
    local pin = CreateFrame("Frame", nil, band)
    pin:SetSize(16, 16)
    pin.icon = A.QuestMarkers.CreateQuestBang(pin, 14)
    pin.icon:SetPoint("CENTER")
    pin:SetScript("OnEnter", showPinTooltip)
    pin:SetScript("OnLeave", hidePinTooltip)
    pin:SetScript("OnHide", hidePinTooltip)
    pin:EnableMouse(false)
    if pin.SetMouseMotionEnabled then pin:SetMouseMotionEnabled(true)
    else pin:EnableMouse(true) end
    if pin.SetMouseClickEnabled then pin:SetMouseClickEnabled(false) end
    return pin
end

function N.Place()
    if not compass then return end
    compass:ClearAllPoints()
    local position = A.Waypoints.db.position
    if position then compass:SetPoint("CENTER", UIParent, "CENTER", position.x, position.y)
    else compass:SetPoint("TOP", UIParent, "TOP", 0, -24) end
end

local function createCompass()
    local frame = CreateFrame("Frame", "ElmoLevelingQuestCompass", UIParent)
    frame:SetSize(WIDTH, 32)
    frame:SetMovable(true)
    frame:SetClampedToScreen(true)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", function(self)
        if not A.Waypoints.db.locked then self:StartMoving() end
    end)
    frame:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local x, y = self:GetCenter()
        local cx, cy = UIParent:GetCenter()
        if number(x) and number(y) and number(cx) and number(cy) then
            A.Waypoints.db.position = {x = x - cx, y = y - cy}
        end
        N.Place()
    end)
    local band = CreateFrame("Frame", nil, frame)
    band:SetAllPoints(); band:EnableMouse(false)
    frame.band = band
    local backdrop = band:CreateTexture(nil, "BACKGROUND")
    backdrop:SetAllPoints(); backdrop:SetColorTexture(.07, .055, .085, .8)
    local tick = band:CreateTexture(nil, "ARTWORK")
    tick:SetSize(2, 6); tick:SetPoint("BOTTOM"); tick:SetColorTexture(.86, .66, .28, 1)
    frame.headingUnavailable = label(band, 11, GOLD)
    frame.headingUnavailable:SetPoint("CENTER")
    frame.headingUnavailable:SetText("Heading unavailable")
    frame.directions, frame.pins = {}, {}
    for index, name in ipairs(directions) do
        local text = label(band, 11, GOLD)
        text:SetText(name); frame.directions[index] = text
    end
    for index = 1, 5 do frame.pins[index] = createPin(band) end
    local arrow = frame:CreateTexture(nil, "ARTWORK")
    arrow:SetSize(54, 54)
    arrow:SetTexture(MEDIA .. "QuestArrow.tga")
    frame.arrow = arrow
    frame.title = label(frame, 12, GOLD)
    frame.title:SetPoint("TOP", arrow, "BOTTOM", 0, 2)
    frame:Hide()
    return frame
end

local function relative(angle, facing)
    return (angle - facing + math.pi) % (2 * math.pi) - math.pi
end

local function drawPins(points)
    local groups = {}
    for _, point in ipairs(points) do
        if math.abs(point.angle) <= HALF_ANGLE and point.distance > 8 then
            local x = -point.angle / HALF_ANGLE * (WIDTH / 2 - 14)
            local group
            for _, candidate in ipairs(groups) do
                if math.abs(x - candidate.x) < 16 then group = candidate; break end
            end
            if not group and #groups < #compass.pins then
                group = {x = x, primary = point == points[1], quests = {}}
                groups[#groups + 1] = group
            end
            if group then group.quests[#group.quests + 1] = point.id end
        end
    end
    for i, pin in ipairs(compass.pins) do
        local group = groups[i]
        if group then
            pin.quests = group.quests
            local key = table.concat(pin.quests, ":")
            if pin.key ~= key and GameTooltip and GameTooltip:IsOwned(pin) then showPinTooltip(pin) end
            pin.key = key
            local tint = group.primary and 1 or .83
            pin.icon:SetVertexColor(tint, tint, tint)
            pin:ClearAllPoints()
            pin:SetPoint("CENTER", compass.band, "CENTER", group.x, -8)
            pin:Show()
        else
            pin.quests, pin.key = nil, nil
            pin:Hide()
        end
    end
end

local function drawCompass(position)
    local W = A.Waypoints
    local manual = W.Active()
    local showBand = A.db.questCompass
    if not (showBand or A.db.questArrow) then return end

    local facing = number(A.Call(GetPlayerFacing))
    local points, instance, north, west = {}
    if position and (#destinations > 0 or manual) then
        instance, north, west = world(position.mapID, position.vector)
    end
    local function measure(point)
        if not north or not west or point.instance ~= instance then return end
        local dn, dw = point.north - north, point.west - west
        point.distance = math.sqrt(dn * dn + dw * dw)
        point.angle = facing and relative(math.atan2(dw, dn), facing) or nil
        return point
    end
    if facing then
        for _, point in ipairs(destinations) do
            if measure(point) then points[#points + 1] = point end
        end
    end
    table.sort(points, function(a, b)
        if a.id == tracked then return b.id ~= tracked end
        if b.id == tracked then return false end
        if a.distance == b.distance then return a.id < b.id end
        return a.distance < b.distance
    end)
    local direction, caption
    if A.db.questArrow and manual then
        local point = destination(manual.mapID, manual.x, manual.y)
        local geometry = point and measure(point)
        local name = manual.title ~= "" and manual.title or ("Waypoint " .. W.db.active)
        if W.Arrival(geometry and geometry.distance) then
            caption = name .. "  ·  Arrived"
        elseif W.Active() then
            if geometry and geometry.angle then
                direction = geometry.angle
                caption = name .. "  ·  " .. math.floor(geometry.distance + .5) .. " yd"
            elseif not point or not north or not west then
                caption = name .. "  ·  Position unavailable"
            elseif point.instance ~= instance then
                caption = name .. "  ·  Different continent"
            else
                caption = name .. "  ·  Heading unavailable"
            end
        end
    end
    if A.db.questArrow and not W.Active() then
        local primary = points[1]
        if primary and (not tracked or primary.id == tracked) and
            not equals(A.Call(C_Minimap and C_Minimap.IsInsideQuestBlob, primary.id), true) then
            caption = active[primary.id] .. "  ·  " .. math.floor(primary.distance + .5) .. " yd"
            if primary.distance > 8 then direction = primary.angle end
        end
    end
    if not (showBand or caption) then return end
    if not compass then
        compass = createCompass()
        N.Place()
    end
    compass:EnableMouse(not W.db.locked)
    compass.band:SetShown(showBand)
    if compass.bandAnchored ~= showBand then
        compass.arrow:ClearAllPoints()
        compass.arrow:SetPoint("TOP", compass, showBand and "BOTTOM" or "TOP", 0, -3)
        compass.bandAnchored = showBand
    end
    local function place(text, angle, y)
        text:ClearAllPoints()
        text:SetPoint("CENTER", compass, "CENTER", -angle / HALF_ANGLE * (WIDTH / 2 - 14), y)
        text:Show()
    end
    if showBand then
        compass.headingUnavailable:SetShown(facing == nil)
        for index, text in ipairs(compass.directions) do
            local angle = facing and relative((index - 1) * math.pi / 4, facing)
            if angle and math.abs(angle) <= HALF_ANGLE then place(text, angle, 7) else text:Hide() end
        end
        drawPins(points)
    else
        for _, pin in ipairs(compass.pins) do hidePinTooltip(pin) end
    end
    compass.arrow:SetShown(direction ~= nil)
    compass.title:SetShown(caption ~= nil)
    if direction then compass.arrow:SetRotation(direction) end
    if caption then compass.title:SetText(caption) end
    compass:Show()
    return true
end

local function drawBeacon()
    if not (A.db.questBeam and C_Navigation and trackingQuest(tracked)) then return end
    if not equals(A.Call(C_Navigation.HasValidScreenPosition), true) or
        not equals(A.Call(C_Navigation.WasClampedToScreen), false) then return end
    local states = Enum and Enum.NavigationState
    if states and not equals(A.Call(C_Navigation.GetTargetState), states.InRange) then return end
    if A.Call(IsInInstance) or A.Call(UnitOnTaxi, "player") then return end
    local anchor = A.Call(C_Navigation.GetFrame)
    if A.IsSecret(anchor) or not anchor or equals(A.Call(anchor.IsForbidden, anchor), true) then return end
    local x, y = A.Call(anchor.GetCenter, anchor)
    local scale, base = number(A.Call(anchor.GetEffectiveScale, anchor)), number(A.Call(UIParent.GetEffectiveScale, UIParent))
    if not (number(x) and number(y) and scale and scale > 0 and base and base > 0) then return end
    local distance = number(A.Call(C_Navigation.GetDistance))
    beacon = beacon or A.QuestMarkers.CreateBeacon("ElmoLevelingQuestBeacon")
    beacon:ClearAllPoints()
    beacon:SetPoint("CENTER", UIParent, "BOTTOMLEFT", x * scale / base, y * scale / base)
    beacon.title:SetText(active[tracked])
    beacon.distance:SetText(distance and tostring(math.floor(distance + .5)) .. " yd" or "")
    beacon:Show()
    return true
end

function N.Invalidate()
    refreshed = 0
end

function N.Hide()
    if compass then
        for _, pin in ipairs(compass.pins) do hidePinTooltip(pin) end
        compass:Hide()
    end
    if beacon then beacon:Hide() end
end

function N.Update()
    local W = A.Waypoints
    local map = A.Call(C_Map and C_Map.GetBestMapForUnit, "player")
    if not A.IsNumber(map) or map <= 0 then map = nil end
    local now = GetTime()
    if now >= refreshed or map ~= N.map then
        refresh(map)
        N.map, refreshed = map, now + 1
    end
    local position
    if map and (W.db.showCoordinates or A.db.questCompass or A.db.questArrow) then
        position = W.PlayerPosition(map)
    end
    if not drawCompass(position) and compass then compass:Hide() end
    if (A.db.questArrow and W.Active() or not drawBeacon()) and beacon then beacon:Hide() end
    W.Update(position)
end
