local _, A = ...
local L = {LIMIT = 100}
A.Levels = L

function L.Init()
    local history = {}
    for _, entry in ipairs(type(A.db.levels) == "table" and A.db.levels or {}) do
        if type(entry) == "table" and A.IsNumber(entry.from) and A.IsNumber(entry.to) and
            entry.from >= 1 and entry.to == entry.from + 1 and #history < L.LIMIT then
            history[#history + 1] = {from = entry.from, to = entry.to,
                seconds = A.IsNumber(entry.seconds) and entry.seconds or nil, complete = entry.complete == true}
        end
    end
    A.db.levels = history
    local state = A.db.levelState
    if type(state) ~= "table" or not A.IsNumber(state.level) or state.level < 1 or state.level % 1 ~= 0 or not A.IsNumber(state.seconds) then
        A.db.levelState = nil
    else
        state.complete = state.complete == true
    end
end

function L.Start(level)
    if not A.IsNumber(level) or level < 1 then return end
    local state = A.db.levelState
    if not state or state.level ~= level then
        state = {level = level, seconds = 0, complete = false}
        A.db.levelState = state
    end
    L.started = A.Elapsed()
    -- The native /played reply can recover this level's full online time even
    -- when the addon was first installed partway through it. Never replace chat handlers.
    if type(RequestTimePlayed) == "function" then
        L.requestLevel = level
        A.Call(RequestTimePlayed)
    end
end

function L.CurrentSeconds()
    local state = A.db.levelState
    return state and state.seconds + (L.started and math.max(0, A.Elapsed() - L.started) or 0) or 0
end

function L.Played(total, seconds)
    local state = A.db.levelState
    if not state or not L.requestLevel then return end
    local requested = L.requestLevel
    L.requestLevel = nil
    if requested ~= state.level or not A.IsNumber(total) or not A.IsNumber(seconds) or seconds > total then return end
    state.seconds, state.complete, L.started = seconds, true, A.Elapsed()
end

function L.Advance(level)
    if not A.IsNumber(level) or level < 1 or level % 1 ~= 0 or level > 200 then return end
    local state = A.db.levelState
    if not state then L.Start(level); return end
    if level <= state.level then return end
    local gap, seconds = level - state.level, L.CurrentSeconds()
    for from = state.level, level - 1 do
        table.insert(A.db.levels, 1, {from = from, to = from + 1,
            seconds = gap == 1 and seconds or nil, complete = gap == 1 and state.complete == true})
    end
    while #A.db.levels > L.LIMIT do table.remove(A.db.levels) end
    A.db.levelState = {level = level, seconds = 0, complete = true}
    L.started = A.Elapsed()
    L.requestLevel = nil
end

function L.Save()
    if A.db.levelState then A.db.levelState.seconds = L.CurrentSeconds() end
    L.started, L.requestLevel = nil, nil
end
function L.ClearHistory() A.db.levels = {} end
