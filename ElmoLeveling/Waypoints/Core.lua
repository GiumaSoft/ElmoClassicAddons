local _, addon = ...
local A = {LIMIT = 50, Call = addon.Call, Text = addon.Text, Print = addon.Print, Private = addon.IsSecret, IsNumber = addon.IsNumber}
addon.Waypoints = A

function A.Number(value)
    if not A.Private(value) and type(value) == "number" and value == value and math.abs(value) < math.huge then return value end
end
local function coordinate(value)
    if A.Text(value) then value = tonumber((value:gsub(",", "."))) end
    value = A.Number(value)
    if value and value >= 0 and value <= 100 then return value / 100 end
end
local function title(value)
    return (A.Text(value) or ""):gsub("[%c|]", ""):match("^%s*(.-)%s*$"):sub(1, 255)
end
local function normalize(db, selectLast)
    local points, selected = {}, nil
    local active = A.Number(db.active)
    for index, point in ipairs(type(db.points) == "table" and db.points or {}) do
        if type(point) == "table" and A.IsNumber(point.mapID) and point.mapID > 0 and point.mapID % 1 == 0 and
            A.IsNumber(point.x) and point.x <= 1 and A.IsNumber(point.y) and point.y <= 1 then
            points[#points + 1] = {mapID = point.mapID, x = point.x, y = point.y, title = title(point.title)}
            if index == active then selected = #points end
            if #points == A.LIMIT then break end
        end
    end
    if selectLast and not selected and #points > 0 then selected = #points end
    db.points, db.active = points, selected
    db.showArrow = db.showArrow ~= false and selected ~= nil
    db.locked = db.locked ~= false
    db.showCoordinates, db.coordinatesLocked = db.showCoordinates ~= false, db.coordinatesLocked == true
    for _, key in ipairs({"position", "coordinatesPosition"}) do
        local position = db[key]
        if type(position) ~= "table" or not A.Number(position.x) or not A.Number(position.y) then db[key] = nil end
    end
    if type(db.minimap) ~= "table" then db.minimap = {} end
    db.minimap.minimapPos = (A.Number(db.minimap.minimapPos) or 210) % 360
    db.minimap.hide = db.minimap.hide == true
    return db
end

function A.Init()
    local saved = addon.db.waypoints
    A.db = normalize(type(saved) == "table" and saved or {})
    addon.db.waypoints = A.db
end

function A.Import(legacy)
    if not A.db or A.db.importedElmoWaypoint or type(legacy) ~= "table" then return end
    local points = normalize({points = legacy.points, active = legacy.active, showArrow = legacy.showArrow}, true)
    -- Keep the current selection and settings if the integrated waypoint list is already in use.
    if #A.db.points == 0 then
        A.db.points, A.db.active, A.db.showArrow = points.points, points.active, points.showArrow
        A.db.showCoordinates = legacy.showCoordinates ~= false
        A.db.coordinatesLocked = legacy.coordinatesLocked == true
        if type(legacy.coordinatesPosition) == "table" then
            local x, y = A.Number(legacy.coordinatesPosition.x), A.Number(legacy.coordinatesPosition.y)
            if x and y then A.db.coordinatesPosition = {x = x, y = y} end
        end
        if type(legacy.minimap) == "table" then
            A.db.minimap.hide = legacy.minimap.hide == true
            A.db.minimap.minimapPos = (A.Number(legacy.minimap.minimapPos) or 210) % 360
        end
    else
        for _, point in ipairs(points.points) do
            if #A.db.points >= A.LIMIT then break end
            local duplicate
            for _, saved in ipairs(A.db.points) do
                if saved.mapID == point.mapID and saved.x == point.x and saved.y == point.y then duplicate = true; break end
            end
            if not duplicate then A.db.points[#A.db.points + 1] = point end
        end
    end
    A.db.importedElmoWaypoint = true
    A.Pins.dirty = true
    if A.Coordinates.panel then A.Coordinates.Place() end
    A.Minimap.Refresh()
end

function A.Current() return A.db.points[A.db.active] end
function A.Active() return A.db.showArrow and A.Current() or nil end
function A.Arrival(distance)
    if not A.arrivedAt and (not distance or distance > 8) then return end
    local now = GetTime()
    A.arrivedAt = A.arrivedAt or now + 1.25
    if now < A.arrivedAt then return true end
    A.db.showArrow, A.arrivedAt = false, nil
end

function A.PlayerPosition(map)
    map = map or A.Call(C_Map and C_Map.GetBestMapForUnit, "player")
    if not A.IsNumber(map) or map <= 0 or map % 1 ~= 0 then return end
    local vector = A.Call(C_Map and C_Map.GetPlayerMapPosition, map, "player")
    if A.Private(vector) or (type(vector) ~= "table" and type(vector) ~= "userdata") then return end
    local x, y = A.Call(function() return vector:GetXY() end)
    if A.IsNumber(x) and x <= 1 and A.IsNumber(y) and y <= 1 then
        return {mapID = map, x = x, y = y, vector = vector}
    end
end
function A.MapName(mapID)
    local info = A.Call(C_Map and C_Map.GetMapInfo, mapID)
    if not A.Private(info) and type(info) == "table" then return A.Text(info.name) or ("Map " .. mapID) end
    return "Map " .. mapID
end
local function save(map, x, y, label)
    local index
    for i, point in ipairs(A.db.points) do
        if point.mapID == map and point.x == x and point.y == y then index = i; break end
    end
    if not index then
        if #A.db.points >= A.LIMIT then A.Print("Waypoint limit reached. Remove a waypoint or reset the list."); return false end
        index = #A.db.points + 1
        A.db.points[index] = {mapID = map, x = x, y = y, title = title(label)}
    elseif title(label) ~= "" then A.db.points[index].title = title(label) end
    A.Select(index)
    A.Print(string.format("Waypoint %d: %s (%.2f, %.2f).", index, A.MapName(map), x * 100, y * 100))
    return true
end
function A.Add(x, y, label)
    x, y = coordinate(x), coordinate(y)
    if not x or not y then A.Print("Use /way x y [note], with coordinates from 0 to 100."); return false end
    local map = A.Number(A.Call(C_Map and C_Map.GetBestMapForUnit, "player"))
    if not map or map <= 0 or map % 1 ~= 0 then A.Print("Your current map is unavailable. Try again when the map is ready."); return false end
    return save(map, x, y, label)
end
function A.AddCurrent(note)
    local position = A.PlayerPosition()
    if not position then A.Print("Your current coordinates are unavailable. No waypoint added."); return false end
    return save(position.mapID, position.x, position.y, note)
end
function A.Select(index)
    if not A.db.points[index] then return end
    A.db.active, A.db.showArrow, A.arrivedAt = index, true, nil
    A.Pins.dirty = true
    A.Tick()
end
function A.Next()
    if #A.db.points > 0 then A.Select((A.db.active or 0) % #A.db.points + 1) end
end
function A.ClearSelection()
    A.db.active = nil
    A.Pins.dirty = true
    A.SetVisible(false)
end
function A.RemoveCurrent()
    if not A.Current() then return end
    table.remove(A.db.points, A.db.active)
    if #A.db.points == 0 then A.ClearSelection(); return end
    A.db.active = math.min(A.db.active, #A.db.points)
    A.Pins.dirty = true
    A.SetVisible(false)
end
function A.Reset()
    A.db.points = {}
    A.ClearSelection()
    A.Print("All waypoints cleared.")
end
function A.SetVisible(visible)
    A.db.showArrow, A.arrivedAt = visible == true and A.Current() ~= nil, nil
    A.Tick()
end
function A.SetLocked(locked) A.db.locked = locked == true; A.Tick() end
function A.Center()
    A.db.position = nil
    addon.QuestNavigation.Place()
end
function A.Update(position)
    A.Pins.Refresh()
    A.Coordinates.Update(position)
    A.Settings.Refresh()
end
function A.Tick()
    if A.inWorld then addon.QuestNavigation.Update() end
    A.Settings.Refresh()
end
function A.Command(text)
    text = (A.Text(text) or ""):match("^%s*(.-)%s*$")
    local command = text:lower()
    if command == "" or command == "options" then A.Settings.Open()
    elseif command == "reset" or command == "clear" then A.Reset()
    elseif command == "next" then A.Next()
    elseif command == "remove" then A.RemoveCurrent()
    elseif command == "show" or command == "resume" then A.SetVisible(true)
    elseif command == "hide" or command == "pause" then A.SetVisible(false)
    elseif command == "lock" or command == "unlock" then A.SetLocked(command == "lock")
    elseif command == "center" then A.Center()
    elseif command == "current" or command:match("^current%s") then A.AddCurrent(text:match("^%S+%s+(.+)$"))
    elseif command == "coords show" or command == "coords hide" then A.Coordinates.SetVisible(command == "coords show")
    elseif command == "coords lock" or command == "coords unlock" then A.Coordinates.SetLocked(command == "coords lock")
    elseif command == "coords center" then A.Coordinates.Center()
    elseif command == "minimap show" or command == "minimap hide" then A.Minimap.SetVisible(command == "minimap show")
    else
        local x, y, label = text:match("^(%S+)%s+(%S+)%s*(.-)$")
        if x and y then A.Add(x, y, label)
        else A.Print("/way x y [note] | current [note]. /ewp reset | next | remove | resume | pause | lock | unlock | center. /ewp coords show | hide | lock | unlock | center.") end
    end
end
function A.RegisterCommands()
    -- Flush earlier registrations through Blizzard's own importer, then add our
    -- aliases normally. Other addons retain their handlers and alternative names.
    A.Call(ChatFrameUtil and ChatFrameUtil.ImportAllListsToHash or ChatFrame_ImportAllListsToHash)
    SLASH_ELMOWAYPOINT1, SLASH_ELMOWAYPOINT2, SLASH_ELMOWAYPOINT3 = "/way", "/ewp", "/elmowaypoint"
    SlashCmdList.ELMOWAYPOINT = A.Command
end
