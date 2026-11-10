local _, A = ...
local Q = {}
A.QuestKills = Q
local KNIFE = "Interface\\Icons\\INV_Weapon_ShortBlade_05"
local wanted, expires, scanning = {}, 0, false
local legacyLog, legacySignature

local function publicTable(value)
    if not A.Secret(value) and type(value) == "table" and
        not (issecrettable and issecrettable(value)) then return value end
end

local function clean(value)
    value = A.Text(value)
    if not value then return end
    return value:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
        :gsub("|H.-|h(.-)|h", "%1"):gsub("%s+", " "):match("^%s*(.-)%s*$")
end

local function escape(value)
    return (value:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1"))
end

local function killPattern()
    local format = clean(QUEST_MONSTERS_KILLED)
    if not format then return end
    -- Use Blizzard's localized kill wording, with either Classic's suffix or
    -- Forever's prefix counters. Positional format tokens are also supported.
    format = format:gsub("%%%d+%$", "%%"):gsub("：", ":")
    local label, counters = format:gsub("%%d%s*/%s*%%d", "")
    if counters ~= 1 then return end
    label = label:gsub("^[%s:]+", ""):gsub("[%s:]+$", "")
    local first, last = label:find("%%s")
    if not first or label:find("%%s", last + 1) then return end
    local before, after = label:sub(1, first - 1), label:sub(last + 1)
    if before:find("%%") or after:find("%%") or before .. after == "" then return end
    return "^" .. escape(before) .. "(.+)" .. escape(after) .. "$"
end

local function killName(row, pattern)
    if not pattern or A.Text(row.type) ~= "monster" or A.Bool(row.finished) ~= false or
        A.Secret(row.numFulfilled) or A.Secret(row.numRequired) then return end
    local text = clean(row.text)
    if not text then return end
    text = text:gsub("：", ":")
    local done, total, label = text:match("^(%d+)%s*/%s*(%d+)%s+(.+)$")
    if not label then label, done, total = text:match("^(.-)%s*:?%s*(%d+)%s*/%s*(%d+)$") end
    done, total = tonumber(done), tonumber(total)
    -- Either public source may already know that this objective is complete.
    if total and (total <= 0 or done >= total) then return end
    local fulfilled, required = A.Number(row.numFulfilled) or done, A.Number(row.numRequired) or total
    if not fulfilled or not required or required <= 0 or fulfilled < 0 or fulfilled >= required then return end
    local name = clean((label or text):match(pattern))
    if name and name ~= "" then return name:lower() end
end

local function visibleSignature()
    local count, total = A.Call(GetNumQuestLogEntries)
    local parts, collapsed = {tostring(A.Number(total) or 0)}, false
    for i = 1, A.Number(count) or 0 do
        local title, _, _, header, closed, complete, _, id = A.Call(GetQuestLogTitle, i)
        parts[#parts + 1] = (A.Text(title) or "") .. ":" .. tostring(A.Number(id) or 0) .. ":" ..
            tostring(A.Bool(closed) == true) .. ":" .. tostring(A.Number(complete) or 0)
        if A.Bool(header) and A.Bool(closed) then collapsed = true end
    end
    return table.concat(parts, "\n"), collapsed
end

local function questLog()
    local result = {}
    if C_QuestLog and type(C_QuestLog.GetInfo) == "function" then
        -- Modern indices include children of collapsed headers.
        for i = 1, 1000 do
            local info = publicTable(A.Call(C_QuestLog.GetInfo, i))
            if not info then break end
            local id = A.Number(info.questID)
            if id and id > 0 and not A.Secret(info.isHeader) and A.Bool(info.isHeader) ~= true and
                not A.Secret(info.isComplete) and not A.Secret(info.isFailed) then
                result[id] = A.Bool(info.isComplete) == true or A.Bool(info.isFailed) == true
            end
        end
        return result
    end
    local signature, collapsed = visibleSignature()
    if signature == legacySignature then return legacyLog end
    -- Era omits collapsed children. Cache their IDs and restore the user's
    -- headers and selection before returning. Our own quest events are ignored.
    local headers, ordinal, selection = {}, 0, A.Number(A.Call(GetQuestLogSelection))
    for i = 1, A.Number(A.Call(GetNumQuestLogEntries)) or 0 do
        local _, _, _, header, closed = A.Call(GetQuestLogTitle, i)
        if A.Bool(header) then ordinal = ordinal + 1; headers[ordinal] = A.Bool(closed) == true end
    end
    if collapsed then A.Call(ExpandQuestHeader, 0) end
    local restore = {}; ordinal = 0
    for i = 1, A.Number(A.Call(GetNumQuestLogEntries)) or 0 do
        local _, _, _, header, _, complete, _, id = A.Call(GetQuestLogTitle, i)
        if A.Bool(header) then
            ordinal = ordinal + 1
            if collapsed and headers[ordinal] then restore[#restore + 1] = i end
        else
            id, complete = A.Number(id), A.Number(complete)
            if id and id > 0 then result[id] = complete == 1 or complete == -1 end
        end
    end
    for i = #restore, 1, -1 do A.Call(CollapseQuestHeader, restore[i]) end
    if collapsed and selection and selection > 0 then A.Call(SelectQuestLogEntry, selection) end
    legacySignature, legacyLog = visibleSignature(), result
    return result
end

local function refresh(now)
    scanning = true
    local names, pattern = {}, killPattern()
    for id, completed in pairs(questLog()) do
        local complete = A.Call(C_QuestLog and C_QuestLog.IsComplete or IsQuestComplete, id)
        if not completed and not A.Secret(complete) and A.Bool(complete) ~= true then
            local rows = publicTable(A.Call(C_QuestLog and C_QuestLog.GetQuestObjectives, id))
            if rows then
                for _, row in ipairs(rows) do
                    row = publicTable(row)
                    local name = row and killName(row, pattern)
                    if name then names[name] = true end
                end
            end
        end
    end
    wanted, expires, scanning = names, now + .5, false
end

function Q.Invalidate(structural)
    if scanning then return false end
    expires = 0
    if structural then legacyLog, legacySignature = nil, nil end
    return true
end

function Q.GetTexture(guid, name, now)
    if A.db and A.db.questKills == false then return end
    guid, name = A.Text(guid), clean(name)
    if not guid or not name or not (guid:match("^Creature%-") or guid:match("^Vehicle%-")) then return end
    now = now or GetTime()
    if not scanning and now >= expires then refresh(now) end
    if wanted[name:lower()] then return KNIFE end
end
