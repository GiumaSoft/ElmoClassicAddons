local _, A = ...
local Q = {}
A.QuestKills = Q
local wanted, targetsByQuest, expires, scanning = {}, {}, 0, false
local itemsByQuest, itemMatches = {}, {}
local legacyLog, legacySignature

local function publicTable(value)
    if not A.IsSecret(value) and type(value) == "table" and
        not (issecrettable and issecrettable(value)) then return value end
end

local function number(value)
    if A.IsNumber(value) then return value end
end
local function boolean(value)
    if not A.IsSecret(value) and type(value) == "boolean" then return value end
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

local function objectiveLabel(value)
    local text = clean(value)
    if not text then return end
    text = text:gsub("：", ":")
    local done, total, label = text:match("^(%d+)%s*/%s*(%d+)%s+(.+)$")
    if not label then label, done, total = text:match("^(.-)%s*:?%s*(%d+)%s*/%s*(%d+)$") end
    return clean(label or text), tonumber(done), tonumber(total)
end

local function objectiveProgress(row)
    if boolean(row.finished) ~= false or A.IsSecret(row.numFulfilled) or A.IsSecret(row.numRequired) then return end
    local label, done, total = objectiveLabel(row.text)
    if not label or label == "" then return end
    -- Either public source may already know that this objective is complete.
    if total and (total <= 0 or done >= total) then return end
    local fulfilled, required = number(row.numFulfilled) or done, number(row.numRequired) or total
    if not fulfilled or not required or required <= 0 or fulfilled < 0 or fulfilled >= required then return end
    return label, fulfilled, required
end

local function visibleSignature()
    local count, total = A.Call(GetNumQuestLogEntries)
    local parts, collapsed = {tostring(number(total) or 0)}, false
    for i = 1, number(count) or 0 do
        local title, _, _, header, closed, complete, _, id = A.Call(GetQuestLogTitle, i)
        parts[#parts + 1] = (A.Text(title) or "") .. ":" .. tostring(number(id) or 0) .. ":" ..
            tostring(boolean(closed) == true) .. ":" .. tostring(not A.IsSecret(complete) and tonumber(complete) or 0)
        if boolean(header) and boolean(closed) then collapsed = true end
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
            local id = number(info.questID)
            if id and id > 0 and not A.IsSecret(info.isHeader) and boolean(info.isHeader) ~= true and
                not A.IsSecret(info.isComplete) and not A.IsSecret(info.isFailed) then
                result[id] = boolean(info.isComplete) == true or boolean(info.isFailed) == true
            end
        end
        return result
    end
    local signature, collapsed = visibleSignature()
    if signature == legacySignature then return legacyLog end
    -- Era omits collapsed children. Cache their IDs and restore the user's
    -- headers and selection before returning. Our own quest events are ignored.
    if collapsed and A.Call(InCombatLockdown) == true then return legacyLog or result end
    local headers, ordinal, selection = {}, 0, number(A.Call(GetQuestLogSelection))
    for i = 1, number(A.Call(GetNumQuestLogEntries)) or 0 do
        local _, _, _, header, closed = A.Call(GetQuestLogTitle, i)
        if boolean(header) then ordinal = ordinal + 1; headers[ordinal] = boolean(closed) == true end
    end
    if collapsed then A.Call(ExpandQuestHeader, 0) end
    local restore = {}; ordinal = 0
    for i = 1, number(A.Call(GetNumQuestLogEntries)) or 0 do
        local _, _, _, header, _, complete, _, id = A.Call(GetQuestLogTitle, i)
        if boolean(header) then
            ordinal = ordinal + 1
            if collapsed and headers[ordinal] then restore[#restore + 1] = i end
        else
            complete = not A.IsSecret(complete) and tonumber(complete)
            id = number(id)
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
    local names, targets, items, pattern = {}, {}, {}, killPattern()
    for id, completed in pairs(questLog()) do
        local complete = A.Call(C_QuestLog and C_QuestLog.IsComplete or IsQuestComplete, id)
        if not completed and not A.IsSecret(complete) and boolean(complete) ~= true then
            local rows = publicTable(A.Call(C_QuestLog and C_QuestLog.GetQuestObjectives, id))
            if rows then
                for _, row in ipairs(rows) do
                    row = publicTable(row)
                    if row then
                        local kind = A.Text(row.type)
                        local label, done, total
                        if kind == "item" or (kind == "monster" and pattern) then
                            label, done, total = objectiveProgress(row)
                        end
                        if label and kind == "item" then
                            local list = items[id] or {}
                            items[id] = list
                            list[label:lower()] = {name = label, done = done, total = total, questID = id}
                        end
                        local name = label and kind == "monster" and clean(label:match(pattern))
                        if name then
                            local key = name:lower()
                            local objective = {name = name, done = done, total = total, questID = id}
                            local list = targets[id] or {}
                            list[#list + 1] = objective
                            targets[id] = list
                            local previous = names[key]
                            if not previous or total - done > previous.total - previous.done or
                                (total - done == previous.total - previous.done and id < previous.questID) then
                                names[key] = objective
                            end
                        end
                    end
                end
            end
        end
    end
    wanted, targetsByQuest, itemsByQuest, itemMatches = names, targets, items, {}
    expires, scanning = now + .5, false
end

function Q.Invalidate(structural)
    if scanning then return false end
    expires = 0
    if structural then legacyLog, legacySignature = nil, nil end
    return true
end

function Q.FindByName(name, now)
    name = clean(name)
    if not name or name == "" then return end
    now = now or GetTime()
    if not scanning and now >= expires then refresh(now) end
    return wanted[name:lower()]
end

function Q.IsCreatureGUID(guid)
    guid = A.Text(guid)
    return guid and (guid:match("^Creature%-") or guid:match("^Vehicle%-")) ~= nil
end

function Q.GetObjective(guid, name, now)
    if Q.IsCreatureGUID(guid) then return Q.FindByName(name, now) end
end

function Q.ForgetUnit(unit)
    itemMatches[unit] = nil
end

local function itemObjectiveFor(unit)
    local types = Enum and Enum.TooltipDataLineType
    if not (types and types.QuestTitle and types.QuestObjective) then return end
    local data = publicTable(A.Call(C_TooltipInfo and C_TooltipInfo.GetUnit, unit))
    local lines = data and publicTable(data.lines)
    if not lines then return end
    local items
    for _, row in ipairs(lines) do
        local line = publicTable(row)
        local kind = line and number(line.type)
        if not kind then
            items = nil
        elseif kind == types.QuestTitle then
            items = itemsByQuest[number(line.id)]
        elseif items and kind == types.QuestObjective and boolean(line.completed) == false and
            not A.IsSecret(line.numFulfilled) and not A.IsSecret(line.numRequired) then
            local label, done, total = objectiveLabel(line.leftText)
            local objective = label and items[label:lower()]
            local reportedDone = number(line.numFulfilled) or done
            local reportedTotal = number(line.numRequired) or total
            if objective and reportedTotal == objective.total and reportedDone and reportedDone < reportedTotal then
                return objective
            end
        end
    end
end

function Q.GetItemObjective(unit, guid, now)
    if not (C_TooltipInfo and C_TooltipInfo.GetUnit) then return end
    if not scanning and now >= expires then refresh(now) end
    if not next(itemsByQuest) then return end
    local match = itemMatches[unit]
    if match and match.guid == guid then return match.objective end
    local objective = itemObjectiveFor(unit)
    itemMatches[unit] = {guid = guid, objective = objective}
    return objective
end

function Q.TargetsForQuest(questID)
    local now = GetTime()
    if not scanning and now >= expires then refresh(now) end
    return targetsByQuest[questID]
end
