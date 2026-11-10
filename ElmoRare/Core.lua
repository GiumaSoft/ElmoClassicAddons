local addonName, A = ...
ElmoRare = A
A.version, A.units, A.seen = "1.0.0", {}, {}
local frame, elapsed = CreateFrame("Frame"), 0
local ABSENCE_RESET, MAX_SEEN = 300, 256
_G["BINDING_NAME_CLICK ElmoRareMarkTargetButton:LeftButton"] = "ElmoRare: Skull on current target"

local function checked(ok, ...) if ok then return ... end end
function A.Call(fn, ...)
    if type(fn) == "function" then return checked(pcall(fn, ...)) end
end
function A.Private(value)
    return type(issecretvalue) == "function" and issecretvalue(value) or
        type(canaccessvalue) == "function" and not canaccessvalue(value)
end
function A.Text(value) if not A.Private(value) and type(value) == "string" then return value end end
function A.Number(value)
    if not A.Private(value) and type(value) == "number" and value == value and
        value ~= math.huge and value ~= -math.huge then return value end
end
function A.Bool(value) if not A.Private(value) and type(value) == "boolean" then return value end end
function A.Print(message) DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoRare:|r " .. message) end
function A.Source(unit)
    if unit == "target" then return "Target" end
    if unit == "mouseover" then return "Mouseover" end
    return "Nearby nameplate"
end

function A.Read(unit)
    unit = A.Text(unit)
    if not unit or A.Bool(A.Call(UnitExists, unit)) ~= true then return end
    local classification = A.Text(A.Call(UnitClassification, unit))
    if classification ~= "rare" and classification ~= "rareelite" then return end
    local dead = A.Bool(A.Call(UnitIsDeadOrGhost, unit))
    local controlled = A.Bool(A.Call(UnitPlayerControlled, unit))
    if dead ~= false or controlled ~= false then return end
    local guid = A.Text(A.Call(UnitGUID, unit))
    if not guid or not (guid:match("^Creature%-") or guid:match("^Vehicle%-")) then return end
    local name = A.Text(A.Call(UnitName, unit))
    if not name or name == "" then return end
    return {guid = guid, name = name, level = A.Number(A.Call(UnitLevel, unit)), unit = unit,
        classification = classification, lastSeen = GetTime(),
        npcID = tonumber(guid:match("^[^%-]+%-%d+%-%d+%-%d+%-%d+%-(%d+)%-"))}
end

local function prune(now, makeRoom)
    local count, oldest, oldestTime = 0, nil, math.huge
    for guid, record in pairs(A.seen) do
        if now - record.lastSeen > ABSENCE_RESET then A.seen[guid] = nil
        else
            count = count + 1
            if record.lastSeen < oldestTime then oldest, oldestTime = guid, record.lastSeen end
        end
    end
    if makeRoom and count >= MAX_SEEN and oldest then A.seen[oldest] = nil end
end

function A.Probe(unit)
    if not A.db or not A.db.enabled then return end
    local record = A.Read(unit)
    if not record then return end
    local previous = A.seen[record.guid]
    local fresh = not previous or record.lastSeen - previous.lastSeen > ABSENCE_RESET
    if fresh then prune(record.lastSeen, true) end
    A.seen[record.guid] = record
    if A.last and A.last.guid == record.guid then A.last = record end
    if fresh then
        A.last = record
        if A.db.sound then A.UI.Sound() end
        if A.db.popup then A.UI.Notify(record) end
        A.Print("Rare detected: " .. record.name .. " — " .. A.Source(unit) .. ".")
    end
    return record
end

function A.Scan()
    if not A.db or not A.db.enabled then return end
    prune(GetTime())
    for unit in pairs(A.units) do
        if A.Bool(A.Call(UnitExists, unit)) == false then A.units[unit] = nil
        else A.Probe(unit) end
    end
    A.Probe("target"); A.Probe("mouseover")
end

function A.Discover()
    local plates = A.Call(C_NamePlate and C_NamePlate.GetNamePlates)
    if not A.Private(plates) and type(plates) == "table" and
        (type(canaccesstable) ~= "function" or canaccesstable(plates)) then
        for _, plate in ipairs(plates) do
            if not A.Private(plate) and A.Bool(A.Call(plate.IsForbidden, plate)) == false then
                local unit = A.Text(A.Call(plate.GetUnit, plate)) or A.Text(plate.unitToken)
                if unit and unit:match("^nameplate%d+$") then A.units[unit] = true end
            end
        end
    end
    A.Scan()
end

function A.SetEnabled(enabled)
    local changed = A.db.enabled ~= enabled
    A.db.enabled = enabled == true
    if not A.db.enabled then A.UI.Hide()
    elseif changed then A.seen = {}; A.Discover() end
end

function A.Preview()
    if A.db.sound then A.UI.Sound() end
    A.UI.Notify({name = "Rare alert preview", level = 25, classification = "rareelite", preview = true,
        lastSeen = GetTime()})
end

function A.Command(command)
    command = (command or ""):lower():match("^%s*(.-)%s*$")
    if command == "test" then A.Preview()
    elseif command == "on" or command == "off" then
        A.SetEnabled(command == "on"); A.Print("Detection " .. (A.db.enabled and "enabled." or "disabled."))
    elseif command == "last" then
        if A.last then A.UI.Notify(A.last) else A.Print("No rare detected yet.") end
    elseif command == "status" then
        local count = 0; for _ in pairs(A.units) do count = count + 1 end
        A.Print("Detection: " .. tostring(A.db.enabled) .. "; tracked nameplates: " .. count ..
            "; secure skull key: " .. (A.UI.marker and "ready" or "unavailable/deferred") .. ".")
    elseif command == "" then A.Settings.Open()
    else A.Print("/erare: options. /erare test | on | off | last | status") end
end

local function initialize()
    if A.db then return end
    ElmoRareDB = type(ElmoRareDB) == "table" and ElmoRareDB or {}
    A.db = ElmoRareDB
    for _, key in ipairs({"enabled", "sound", "popup"}) do
        if type(A.db[key]) ~= "boolean" then A.db[key] = true end
    end
    A.UI.Create(); A.UI.CreateMarker(); A.Settings.Register()
    SLASH_ELMORARE1, SLASH_ELMORARE2 = "/erare", "/elmorare"
    SlashCmdList.ELMORARE = A.Command
    A.Discover()
    A.Print("Loaded " .. A.version .. ". /erare: options; /erare test: alert preview.")
end

frame:SetScript("OnEvent", function(_, event, unit)
    if event == "ADDON_LOADED" then
        if unit == addonName then initialize() end
        return
    end
    if not A.db then return end
    if event == "PLAYER_REGEN_ENABLED" then A.UI.CreateMarker()
    elseif event == "PLAYER_ENTERING_WORLD" then A.units = {}; A.UI.Hide(); A.Discover()
    elseif event == "NAME_PLATE_UNIT_ADDED" then
        unit = A.Text(unit)
        if unit and unit:match("^nameplate%d+$") then A.units[unit] = true; A.Probe(unit) end
    elseif event == "NAME_PLATE_UNIT_REMOVED" then
        unit = A.Text(unit); if unit then A.units[unit] = nil end
    elseif event == "PLAYER_TARGET_CHANGED" then A.Probe("target")
    elseif event == "UPDATE_MOUSEOVER_UNIT" then A.Probe("mouseover")
    elseif event == "CVAR_UPDATE" then
        unit = A.Text(unit); if unit and unit:lower():match("^nameplate") then A.Discover() end
    else A.Probe(unit) end
end)
for _, event in ipairs({"ADDON_LOADED", "PLAYER_ENTERING_WORLD", "PLAYER_REGEN_ENABLED",
    "NAME_PLATE_UNIT_ADDED", "NAME_PLATE_UNIT_REMOVED", "PLAYER_TARGET_CHANGED", "UPDATE_MOUSEOVER_UNIT",
    "UNIT_CLASSIFICATION_CHANGED", "UNIT_LEVEL", "UNIT_FLAGS", "CVAR_UPDATE"}) do
    A.Call(frame.RegisterEvent, frame, event)
end
frame:SetScript("OnUpdate", function(_, delta)
    if not A.db then return end
    elapsed = elapsed + delta
    if elapsed >= .5 then elapsed = 0; A.Scan(); A.UI.Tick() end
end)
