local addonName, A = ...
ElmoWaypoint = A
A.version, A.LIMIT = "1.2.0", 50
local frame, elapsed = CreateFrame("Frame"), 0
A.frame = frame

function A.Private(value)
    return type(issecretvalue) == "function" and issecretvalue(value) or
        type(canaccessvalue) == "function" and not canaccessvalue(value)
end
function A.Number(value)
    if not A.Private(value) and type(value) == "number" and value == value and
        value ~= math.huge and value ~= -math.huge then return value end
end
function A.Text(value) if not A.Private(value) and type(value) == "string" then return value end end
function A.Call(fn, ...)
    if type(fn) ~= "function" then return end
    local ok, a, b, c = pcall(fn, ...)
    if ok then return a, b, c end
end
function A.Print(text) DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoWaypoint:|r " .. text) end
local function coordinate(value)
    if A.Text(value) then value = tonumber((value:gsub(",", "."))) end
    value = A.Number(value)
    if value and value >= 0 and value <= 100 then return value / 100 end
end
local function title(value)
    return (A.Text(value) or ""):gsub("[%c|]", ""):match("^%s*(.-)%s*$"):sub(1, 255)
end
function A.Init()
    if A.db then return end
    local db = type(ElmoWaypointDB) == "table" and ElmoWaypointDB or {}
    local points = {}
    for _, point in ipairs(type(db.points) == "table" and db.points or {}) do
        if type(point) == "table" and A.Number(point.mapID) and point.mapID > 0 and point.mapID % 1 == 0 and
            A.Number(point.x) and point.x >= 0 and point.x <= 1 and A.Number(point.y) and point.y >= 0 and point.y <= 1 and #points < A.LIMIT then
            points[#points + 1] = {mapID = point.mapID, x = point.x, y = point.y, title = title(point.title)}
        end
    end
    db.points = points
    db.active = math.max(1, math.min(#points, math.floor(A.Number(db.active) or #points)))
    db.showArrow, db.locked = db.showArrow ~= false, db.locked == true
    db.showCoordinates, db.coordinatesLocked = db.showCoordinates ~= false, db.coordinatesLocked == true
    for _, key in ipairs({"position", "coordinatesPosition"}) do
        if type(db[key]) ~= "table" or not A.Number(db[key].x) or not A.Number(db[key].y) then db[key] = nil end
    end
    if type(db.minimap) ~= "table" then db.minimap = {} end
    db.minimap.minimapPos = (A.Number(db.minimap.minimapPos) or 210) % 360
    db.minimap.hide = db.minimap.hide == true
    ElmoWaypointDB, A.db = db, db
end
function A.Current() return A.db.points[A.db.active] end
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
    A.db.active, A.db.showArrow = index, true
    A.Pins.dirty = true
    A.Tick()
end
function A.Next()
    if #A.db.points > 0 then A.db.active = A.db.active % #A.db.points + 1 end
    A.Pins.dirty = true; A.Tick()
end
function A.RemoveCurrent()
    if A.Current() then table.remove(A.db.points, A.db.active) end
    A.db.active = math.max(1, math.min(A.db.active, #A.db.points))
    A.Pins.dirty = true; A.Tick()
end
function A.Reset()
    A.db.points, A.db.active = {}, 1
    A.Pins.dirty = true; A.Tick(); A.Print("All ElmoWaypoint waypoints cleared.")
end
function A.SetVisible(visible) A.db.showArrow = visible == true; A.Tick() end
function A.SetLocked(locked) A.db.locked = locked == true; A.Tick() end
function A.Center() A.db.position = nil; A.UI.Place() end
function A.Tick()
    if not A.db or not A.UI.panel then return end
    A.Pins.Refresh()
    local point = A.Current()
    local position = (A.db.showCoordinates or point and A.db.showArrow) and A.PlayerPosition() or nil
    local state = point and A.db.showArrow and A.Navigation(point, position) or nil
    A.state = state
    A.UI.Update(point, state)
    A.Coordinates.Update(position)
    if A.Settings.Refresh then A.Settings.Refresh() end
end
function A.Command(text)
    text = (A.Text(text) or ""):match("^%s*(.-)%s*$")
    local command = text:lower()
    if command == "" or command == "options" then A.Settings.Open()
    elseif command == "reset" or command == "clear" then A.Reset()
    elseif command == "next" then A.Next()
    elseif command == "remove" then A.RemoveCurrent()
    elseif command == "show" or command == "hide" then A.SetVisible(command == "show")
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
        else A.Print("/way x y [note] | current [note]. /ewp reset | next | remove | show | hide | lock | unlock | center. /ewp coords show | hide | lock | unlock | center.") end
    end
end
function A.RegisterCommands()
    -- Flush earlier registrations through Blizzard's own importer, then add our
    -- aliases normally. Other addons retain their handlers and alternative names.
    A.Call(ChatFrameUtil and ChatFrameUtil.ImportAllListsToHash or ChatFrame_ImportAllListsToHash)
    SLASH_ELMOWAYPOINT1, SLASH_ELMOWAYPOINT2, SLASH_ELMOWAYPOINT3 = "/way", "/ewp", "/elmowaypoint"
    SlashCmdList.ELMOWAYPOINT = A.Command
end
frame:SetScript("OnEvent", function(_, event, name)
    if event == "ADDON_LOADED" and name == addonName then
        A.Init(); A.UI.Create(); A.Coordinates.Create(); A.Settings.Register()
    elseif event == "PLAYER_LOGIN" and A.db then
        A.RegisterCommands(); A.Minimap.Register(); A.ready = true; A.Tick()
    elseif A.ready then A.Pins.dirty = true; A.Tick() end
end)
for _, event in ipairs({"ADDON_LOADED", "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "ZONE_CHANGED_NEW_AREA"}) do frame:RegisterEvent(event) end
frame:SetScript("OnUpdate", function(_, dt)
    if not A.ready then return end
    elapsed = elapsed + dt
    if elapsed < .05 then return end
    elapsed = elapsed % .05
    A.Tick()
end)
