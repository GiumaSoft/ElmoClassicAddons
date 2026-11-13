local _, A = ...
_G.ElmoLeveling = A
A.version = "2.2.0"
local number = A.IsNumber

local function progress()
    local xp, maximum, level = UnitXP("player"), UnitXPMax("player"), UnitLevel("player")
    if not number(xp) or not number(maximum) or not number(level) or level < 1 then return end
    if maximum > 0 and xp > maximum then return end
    return {xp = xp, maximum = maximum, level = level}
end

function A.Print(message)
    if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoLeveling:|r " .. message) end
end

function A.Init()
    if A.db then return end
    local db = type(ElmoLevelingDB) == "table" and ElmoLevelingDB or {}
    db.xp = number(db.xp) and math.floor(db.xp) or 0
    db.seconds = number(db.seconds) and db.seconds or 0
    db.locked, db.hidden = db.locked == true, db.hidden == true
    db.levelExpanded = db.levelExpanded == true
    db.xpGap = db.xpGap == true or nil
    db.bagBaseline = number(db.bagBaseline) and math.floor(db.bagBaseline) or nil
    if type(db.position) ~= "table" or type(db.position.x) ~= "number" or
        type(db.position.y) ~= "number" or not number(math.abs(db.position.x)) or
        not number(math.abs(db.position.y)) then db.position = nil end
    db.measurementAt = number(db.measurementAt) and math.min(db.measurementAt, db.seconds) or 0
    db.periods = nil
    -- Retired mob records and rate samples are never used by the new counters.
    db.history, db.kills, db.respawns, db.mobExpanded, db.combatSeconds = nil, nil, nil, nil, nil
    ElmoLevelingDB, A.db = db, db
end

function A.Elapsed()
    return A.db.seconds + (A.startedAt and math.max(0, GetTime() - A.startedAt) or 0)
end
function A.SinceStart() return math.max(0, A.Elapsed() - A.db.measurementAt) end

function A.Start()
    if A.startedAt then return end
    A.last, A.expectedLevel = progress(), nil
    A.startedAt = GetTime()
    A.Levels.Start(A.last and A.last.level or UnitLevel("player"))
end

-- Read actual player-bar awards from all sources, including level rollover.
-- No combat log, mob XP messages, averages or medians are involved.
function A.Sample()
    if not A.startedAt then return end
    local current = progress()
    if not current then return end
    local previous = A.last
    if not previous then A.last = current; return end
    local level = math.max(previous.level, current.level)
    if current.maximum == previous.maximum then
        if level > previous.level or (A.expectedLevel or 0) > previous.level then return end
        if current.xp < previous.xp then return end
    elseif previous.maximum > 0 then
        level = math.max(level, previous.level + 1)
    end
    if level > previous.level + 1 then
        -- The intervening XP requirements were not observed. Do not invent an award.
        A.db.xpGap = true
        A.Levels.Advance(level)
        current.level, A.last = level, current
        return
    end
    local gained = current.xp - previous.xp
    if level > previous.level then gained = gained + previous.maximum end
    if gained < 0 then return end
    A.db.xp = A.db.xp + gained
    A.Levels.Advance(level)
    current.level, A.last = level, current
    if level >= (A.expectedLevel or 0) then A.expectedLevel = nil end
end

function A.Stats()
    return {elapsed = A.SinceStart(), totalXP = A.db.xp}
end

function A.Reset()
    A.Sample()
    local now = A.Elapsed()
    A.db.xp, A.db.measurementAt, A.db.xpGap = 0, now, nil
    A.last, A.expectedLevel = progress(), nil
    A.Bags.Reset()
    A.Sales.Reset()
    A.UI.Update()
end

function A.Save()
    if not A.startedAt then return end
    A.Sample()
    A.Levels.Save()
    A.db.seconds = A.Elapsed()
    A.startedAt = nil
end

function A.SetLocked(locked)
    A.db.locked = locked == true
    if A.UI.panel then A.UI.panel:StopMovingOrSizing() end
    A.UI.Update()
end
function A.SetVisible(visible) A.db.hidden = not visible; A.UI.Update() end
function A.Command(text)
    local command = (text or ""):match("^%s*(.-)%s*$"):lower()
    if command == "" then A.SetVisible(A.db.hidden)
    elseif command == "show" then A.SetVisible(true)
    elseif command == "hide" then A.SetVisible(false)
    elseif command == "reset" or command == "start" then A.Reset(); A.Print("Session restarted. Level history preserved.")
    elseif command == "lock" then A.SetLocked(true)
    elseif command == "unlock" then A.SetLocked(false)
    elseif command == "center" then A.db.position = nil; A.SetVisible(true); A.UI.Place()
    elseif command == "options" then A.UI.OpenOptions()
    elseif command == "details" then A.UI.ToggleLevels()
    else
        A.Print("/elvl: show/hide. /elvl start | reset: restart elapsed time and earned XP.")
        A.Print("/elvl lock | unlock | center | details | options. /elmoleveling is also available.")
    end
end
