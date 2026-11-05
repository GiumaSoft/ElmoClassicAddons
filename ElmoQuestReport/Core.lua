local _, A = ...
ElmoQuestReport = A
local states, legacyLog, legacySignature = {}, nil, nil
local accepted = {}
local frame, elapsed, scanning = CreateFrame("Frame"), 0, false
local ready = IsLoggedIn and IsLoggedIn() or false
A.frame = frame

local function secret(value)
    return issecretvalue and issecretvalue(value)
end
local function text(value)
    if not secret(value) and type(value) == "string" and value ~= "" then return value end
    return nil
end
local function number(value)
    if not secret(value) and type(value) == "number" and value >= 0 and value < math.huge then return value end
    return nil
end
local function boolean(value)
    if not secret(value) and type(value) == "boolean" then return value end
    return nil
end
local function publicTable(value)
    if not secret(value) and type(value) == "table" and not (issecrettable and issecrettable(value)) then return value end
end
local function call(fn, ...)
    if type(fn) ~= "function" then return end
    local ok, a, b, c, d, e, f, g, h = pcall(fn, ...)
    if ok then return a, b, c, d, e, f, g, h end
end

local function channel()
    if boolean(call(IsInGroup, LE_PARTY_CATEGORY_INSTANCE or 2)) then return "INSTANCE_CHAT" end
    if boolean(call(IsInRaid)) then return "RAID" end
    if boolean(call(IsInGroup)) then return "PARTY" end
end

local function announce(message)
    local destination = channel()
    if not destination then return true end -- Consume solo progress without replaying it on group join.
    message = message:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
        :gsub("|H.-|h(.-)|h", "%1"):gsub("[\r\n]", " ")
    local limit = 255
    while message:byte(limit + 1) and message:byte(limit + 1) >= 128 and message:byte(limit + 1) < 192 do limit = limit - 1 end
    local send = C_ChatInfo and C_ChatInfo.SendChatMessage or SendChatMessage
    if type(send) ~= "function" then return false end
    return pcall(send, message:sub(1, limit), destination)
end

local function visibleSignature()
    local count, total = call(GetNumQuestLogEntries)
    local parts, collapsed = {tostring(number(total))}, false
    for i = 1, number(count) or 0 do
        local title, _, _, header, closed, complete, _, id = call(GetQuestLogTitle, i)
        parts[#parts + 1] = (text(title) or "") .. ":" .. tostring(number(id)) .. ":" ..
            tostring(boolean(closed)) .. ":" .. tostring(number(complete))
        if boolean(header) and boolean(closed) then collapsed = true end
    end
    return table.concat(parts, "\n"), collapsed
end

local function questLog()
    local result = {}
    if C_QuestLog and type(C_QuestLog.GetInfo) == "function" then
        for i = 1, 1000 do
            local info = publicTable(call(C_QuestLog.GetInfo, i))
            if not info then break end
            local id = number(info.questID)
            if id and id > 0 and boolean(info.isHeader) ~= true then result[id] = {title = text(info.title)} end
        end
        return result
    end
    local signature, collapsed = visibleSignature()
    if signature == legacySignature then return legacyLog end
    -- Era hides collapsed children. Restore headers and selection before returning.
    local headers, ordinal, selection = {}, 0, call(GetQuestLogSelection)
    for i = 1, number(call(GetNumQuestLogEntries)) or 0 do
        local _, _, _, header, closed = call(GetQuestLogTitle, i)
        if boolean(header) then ordinal = ordinal + 1; headers[ordinal] = boolean(closed) == true end
    end
    if collapsed then call(ExpandQuestHeader, 0) end
    local restore = {}; ordinal = 0
    for i = 1, number(call(GetNumQuestLogEntries)) or 0 do
        local title, _, _, header, _, complete, _, id = call(GetQuestLogTitle, i)
        if boolean(header) then
            ordinal = ordinal + 1
            if headers[ordinal] then restore[#restore + 1] = i end
        elseif number(id) and id > 0 then result[id] = {title = text(title), complete = number(complete) == 1} end
    end
    for i = #restore, 1, -1 do call(CollapseQuestHeader, restore[i]) end
    if collapsed and number(selection) and selection > 0 then call(SelectQuestLogEntry, selection) end
    legacySignature, legacyLog = visibleSignature(), result
    return result
end

local function snapshot(id, info)
    if not info.title then return end
    local rows = publicTable(call(C_QuestLog and C_QuestLog.GetQuestObjectives, id))
    if not rows then return end
    local complete = boolean(call(C_QuestLog and C_QuestLog.IsComplete or IsQuestComplete, id))
    if complete == nil then complete = info.complete end
    if complete == nil then return end
    local objectives, count, allDone = {}, 0, true
    for i, row in ipairs(rows) do
        row = publicTable(row)
        if not row then return end
        local wording, finished = text(row.text), boolean(row.finished)
        if not secret(row.text) and row.text == "" then -- Native empty rows are not objectives.
        elseif not wording or not text(row.type) or finished == nil then return
        else
            objectives[i] = {text = wording, done = finished}
            count = count + 1; allDone = allDone and finished
        end
    end
    if complete and count > 0 and not allDone then return end -- Wait for consistent native rows.
    return {title = info.title, complete = complete, objectives = objectives, count = count, slots = #rows}
end

local function update(id, quest)
    local state = states[id]
    if not state then
        local newlyAccepted = accepted[id] == true
        state = {incomplete = newlyAccepted or not quest.complete, reported = not newlyAccepted and quest.complete,
            objectives = {}, count = quest.count}
        for i, row in pairs(quest.objectives) do
            state.objectives[i] = {incomplete = newlyAccepted or not row.done, reported = not newlyAccepted and row.done}
        end
        states[id] = state -- First observation is a baseline, including after login/reload.
        accepted[id] = nil
        if not newlyAccepted then return end
    end
    state.count = math.max(state.count, quest.count)
    for i = 1, quest.slots do
        local row = quest.objectives[i]
        if row then
            local previous = state.objectives[i] or {incomplete = not row.done, reported = row.done}
            if not row.done then previous.incomplete = true end
            if state.count > 1 and row.done and previous.incomplete and not previous.reported then
                previous.reported = announce("[ElmoQuestReport] Objective complete: " .. row.text .. " (" .. quest.title .. ")")
            end
            state.objectives[i] = previous
        end
    end
    if not quest.complete then state.incomplete = true end
    if quest.complete and state.incomplete and not state.reported then
        state.reported = announce("[ElmoQuestReport] Quest complete: " .. quest.title)
    end
end

function A.Scan()
    if not ready or scanning then return end
    scanning = true
    for id, info in pairs(questLog() or {}) do
        local quest = snapshot(id, info)
        if quest then update(id, quest) end
    end
    scanning = false
end

frame:SetScript("OnEvent", function(_, event, id, second)
    if event == "PLAYER_LOGIN" or event == "PLAYER_ENTERING_WORLD" then ready = true
    elseif event == "PLAYER_LEAVING_WORLD" then ready = false; return
    elseif event == "QUEST_REMOVED" or event == "QUEST_TURNED_IN" then
        id = number(id); if id then states[id], accepted[id] = nil, nil end
        legacySignature = nil
    elseif event == "QUEST_ACCEPTED" then
        id = number(second) or number(id); if id then states[id], accepted[id] = nil, true end
        legacySignature = nil
    elseif event == "UNIT_QUEST_LOG_CHANGED" and text(id) ~= "player" then return end
    elapsed = .5
end)
frame:SetScript("OnUpdate", function(_, dt)
    if not ready then return end
    elapsed = elapsed + dt
    if elapsed >= .5 then elapsed = 0; A.Scan() end
end)
for _, event in ipairs({"PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "PLAYER_LEAVING_WORLD", "QUEST_LOG_UPDATE",
    "QUEST_ACCEPTED", "QUEST_REMOVED", "QUEST_TURNED_IN", "QUEST_WATCH_UPDATE", "QUEST_AUTOCOMPLETE",
    "QUEST_DATA_LOAD_RESULT", "UNIT_QUEST_LOG_CHANGED", "QUEST_LOG_CRITERIA_UPDATE", "CRITERIA_UPDATE"}) do
    pcall(frame.RegisterEvent, frame, event)
end
