local _, A = ...

A.quests = {}
A.messages = {}
A.cooldown = 30
A.messageLifetime = 300
A.announcing = false
A.recentInvites = {}

function A.InitializeDB()
    if type(ElmoLFGDB) ~= "table" then ElmoLFGDB = {} end
    A.db = ElmoLFGDB
    A.db.selected = A.db.selected or {}
    A.db.roles = A.db.roles or { DPS = true }
    A.db.mode = A.db.mode == "LFM" and "LFM" or "LFG"
    A.db.note = type(A.db.note) == "string" and A.db.note or ""
    if type(A.db.customMessage) ~= "string" then A.db.customMessage = nil end
    A.db.minimap = A.db.minimap or { minimapPos = 225 }
    A.db.autoJoin = A.db.autoJoin ~= false
    local interval = tonumber(A.db.announcementInterval)
    A.db.announcementInterval = interval and interval >= 30 and interval <= 300 and interval % 1 == 0 and interval or 30
    local target = tonumber(A.db.stopAtPlayers)
    A.db.stopAtPlayers = target and target >= 2 and target <= 40 and target % 1 == 0 and target or 5
    if not A.db.recruitmentRoles then
        local selected, count = nil, 0
        if A.db.mode ~= "LFM" then
            for _, role in ipairs({ "Tank", "Healer", "DPS" }) do
                if A.db.roles[role] then selected, count = role, count + 1 end
            end
        end
        A.db.playerRole = count == 1 and selected or nil
        A.db.recruitmentRoles = true
    end
    A.SetPlayerRole(A.db.playerRole)
end

function A.Normalize(text)
    text = text:gsub("|H.-|h(.-)|h", "%1"):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    return (text:lower():gsub("[%p%c]", " "):gsub("%s+", " "):gsub("^ ", ""):gsub(" $", ""))
end

local function Contains(text, term)
    -- Plain matching with word boundaries prevents ST matching 'stockades', etc.
    return (" " .. text .. " "):find(" " .. A.Normalize(term) .. " ", 1, true) ~= nil
end

local function QuestSignature()
    local count, total = GetNumQuestLogEntries()
    local parts = { tostring(total) }
    for i = 1, count do
        local title, level, _, header, collapsed, complete, _, id = GetQuestLogTitle(i)
        parts[#parts + 1] = table.concat({ title or "", tostring(level), tostring(header), tostring(collapsed), tostring(complete), tostring(id) }, ":")
    end
    return table.concat(parts, "\n")
end

local function StoreQuests(quests, expected, signature)
    A.questReady = #quests == expected
    if not A.questReady then return A.quests end -- Wait for a complete journal snapshot.
    local available, active = {}, {}
    for _, quest in ipairs(quests) do
        if quest.complete ~= 1 then
            available[#available + 1] = quest
            active[quest.key] = true
        end
    end
    A.quests, A.questSignature = available, signature
    for key in pairs(A.db.selected) do
        if key:sub(1, 2) == "q:" and not active[key] then A.db.selected[key] = nil end
    end
    return available
end

function A.ReadQuests(force)
    if C_QuestLog and C_QuestLog.GetInfo then
        -- Forever exposes all log entries, including collapsed headers, through
        -- GetInfo. Do not expand headers or change the selected quest here.
        local quests, present, zone, index = {}, {}, "", 1
        while true do
            local info = C_QuestLog.GetInfo(index)
            if not info then break end
            if info.isHeader then
                zone = info.title or ""
            elseif info.questID and info.questID > 0 then
                if not info.title then A.questReady = false; return A.quests end
                local id, complete = info.questID
                if C_QuestLog.IsFailed(id) then complete = -1
                elseif C_QuestLog.IsComplete(id) then complete = 1 end
                local tag = C_QuestLog.GetQuestTagInfo(id)
                quests[#quests + 1] = {
                    id = id, key = "q:" .. id, name = info.title, level = info.level or 0,
                    tag = tag and tag.tagName, complete = complete, zone = zone,
                    link = (C_QuestLog.GetQuestLink or GetQuestLink)(id),
                }
                present[id] = true
            end
            index = index + 1
        end
        -- The modern aggregate count can disagree with the enumerated log.
        -- Keep an old snapshot only if a missing entry is still in the log.
        if C_QuestLog.GetLogIndexForQuestID then
            for _, quest in ipairs(A.quests) do
                local logIndex = not present[quest.id] and C_QuestLog.GetLogIndexForQuestID(quest.id)
                if logIndex and logIndex > 0 then A.questReady = false; return A.quests end
            end
        end
        return StoreQuests(quests, #quests)
    end
    local signature = QuestSignature()
    if not force and signature == A.questSignature then return A.quests end

    -- Classic's log hides children of collapsed headers. Expand temporarily and
    -- restore the same header states and selection before returning to the UI.
    local collapsed, ordinal, hasCollapsed = {}, 0, false
    local selection = GetQuestLogSelection()
    for i = 1, GetNumQuestLogEntries() do
        local _, _, _, header, closed = GetQuestLogTitle(i)
        if header then
            ordinal = ordinal + 1
            collapsed[ordinal] = closed
            hasCollapsed = hasCollapsed or closed
        end
    end
    if hasCollapsed then ExpandQuestHeader(0) end

    local quests, restore, zone = {}, {}, ""
    local count, expected = GetNumQuestLogEntries()
    ordinal = 0
    for i = 1, count do
        local title, level, tag, header, _, complete, _, id = GetQuestLogTitle(i)
        if header then
            ordinal = ordinal + 1
            zone = title or ""
            if collapsed[ordinal] then restore[#restore + 1] = i end
        elseif title and id and id > 0 then
            quests[#quests + 1] = {
                id = id, key = "q:" .. id, name = title, level = level or 0,
                tag = tag, complete = complete, zone = zone, link = GetQuestLink(id),
            }
        end
    end
    for i = #restore, 1, -1 do CollapseQuestHeader(restore[i]) end
    if hasCollapsed and selection and selection > 0 then SelectQuestLogEntry(selection) end

    -- Ignore events caused by our own expansion/restoration.
    return StoreQuests(quests, expected, QuestSignature())
end

function A.AvailableDungeons()
    local available, level = {}, UnitLevel("player")
    for _, dungeon in ipairs(A.dungeons) do
        if level >= dungeon.min then available[#available + 1] = dungeon end
    end
    return available
end

local function QuestChatLink(quest)
    -- Questie's Shift-click hook sends this ID-bearing bracket format. Its
    -- incoming chat filter turns it into the clickable questie: hyperlink.
    -- Sending a native quest: hyperlink on this Era client loses the link.
    if Questie and Questie.started then
        return "[[" .. quest.level .. "] " .. quest.name .. " (" .. quest.id .. ")]", true
    end
    return quest.link, false
end

function A.SelectedActivities()
    local activities = {}
    for _, quest in ipairs(A.quests) do
        if A.db.selected[quest.key] then
            local chatLink, questieLink = QuestChatLink(quest)
            activities[#activities + 1] = {
                kind = "quest",
                label = quest.name, link = quest.link, chatLink = chatLink,
                questID = quest.id, questieLink = questieLink,
            }
        end
    end
    for _, dungeon in ipairs(A.AvailableDungeons()) do
        if A.db.selected["d:" .. dungeon.id] then activities[#activities + 1] = { kind = "dungeon", label = dungeon.name } end
    end
    return activities
end

function A.RoleText()
    local roles = {}
    for _, role in ipairs({ "Tank", "Healer", "DPS" }) do
        if A.db.roles[role] then roles[#roles + 1] = role end
    end
    return table.concat(roles, "/")
end

function A.GetAnnouncementText()
    if A.db.customMessage ~= nil then return A.db.customMessage end
    -- Preserve an older saved note until the user edits or resets the new tail.
    local note = A.db.note:gsub("[\r\n]", " "):gsub("%s+", " "):match("^%s*(.-)%s*$")
    local hint = A.HasSelectedDungeon() and "- /w me inv role (tank, heal, dps)" or "- /w me inv"
    if A.db.autoJoin then hint = hint .. (A.HasSelectedDungeon() and "(autojoin)" or " (autojoin)") end
    return (note ~= "" and ("- " .. note .. " ") or "") .. hint
end

function A.SetAnnouncementText(text)
    A.db.customMessage = type(text) == "string" and text or ""
    A.db.note = ""
end

function A.ResetAnnouncementText()
    A.db.customMessage, A.db.note = nil, ""
end

function A.IsCustomAnnouncement()
    return A.db.customMessage ~= nil or A.db.note:find("%S") ~= nil
end

function A.BuildGeneratedMessage(forChat)
    local activities = A.SelectedActivities()
    if #activities == 0 then return "", "Select at least one quest or dungeon." end
    local names, chatNames, dungeons = {}, {}, {}
    for _, activity in ipairs(activities) do
        if activity.questID then
            if not activity.chatLink or (not activity.questieLink and not activity.chatLink:find("|Hquest:" .. activity.questID .. ":", 1, true)) then
                return "", "Quest link unavailable: " .. activity.label .. ". Please try again."
            end
            names[#names + 1] = activity.link or activity.chatLink
            chatNames[#chatNames + 1] = activity.chatLink
        else
            dungeons[#dungeons + 1] = activity.label
        end
    end
    local sections, chatSections = {}, {}
    if #names > 0 then
        local total = IsInRaid() and 40 or 5
        local prefix = "Quest " .. math.max(0, total - A.GroupSize()) .. "/" .. total .. ": "
        sections[#sections + 1] = prefix .. table.concat(names, "")
        chatSections[#chatSections + 1] = prefix .. table.concat(chatNames, "")
    end
    if #dungeons > 0 then
        local section = table.concat(dungeons, ", ") .. " need " .. A.DungeonRoleText(" | ")
        sections[#sections + 1] = section
        chatSections[#chatSections + 1] = section
    end
    local chatMessage = "LFM " .. table.concat(chatSections, "; ")
    local message = forChat and chatMessage or ("LFM " .. table.concat(sections, "; "))
    return message, nil, #chatMessage, chatMessage
end

function A.BuildMessage(forChat)
    local prefix, err, _, chatPrefix = A.BuildGeneratedMessage(forChat)
    if err then return prefix, err end
    local display = A.GetAnnouncementText():gsub("[\r\n]", " "):gsub("%s+", " "):match("^%s*(.-)%s*$")
    local questLinks = {}
    for _, activity in ipairs(A.SelectedActivities()) do
        if activity.questID and activity.questieLink then questLinks[activity.questID] = activity.chatLink end
    end
    local function replace(full,id) return questLinks[tonumber(id)] or full end
    local wire = display:gsub("(|c%x%x%x%x%x%x%x%x|Hquest:(%d+):[^|]*|h.-|h|r)", replace)
        :gsub("(|Hquest:(%d+):[^|]*|h.-|h)", replace)
    local chatMessage = chatPrefix .. (wire ~= "" and (" " .. wire) or "")
    local message = forChat and chatMessage or (prefix .. (display ~= "" and (" " .. display) or ""))
    if #chatMessage > 255 then
        return message, "Over 255 bytes: select fewer activities or shorten the custom message.", #chatMessage
    end
    return message, nil, #chatMessage
end

function A.ChannelOptions()
    local options, channels = {}, { GetChannelList() }
    for i = 1, #channels, 3 do
        local id, name, disabled = channels[i], channels[i + 1], channels[i + 2]
        if id and name and not disabled then
            options[#options + 1] = { key = "channel:" .. name, label = id .. ". " .. name, type = "CHANNEL", id = id }
        end
    end
    if IsInGuild() then options[#options + 1] = { key = "GUILD", label = "Guild", type = "GUILD" } end
    if IsInGroup() and not IsInRaid() then options[#options + 1] = { key = "PARTY", label = "Party", type = "PARTY" } end
    options[#options + 1] = { key = "SAY", label = "Local (/say)", type = "SAY" }
    options[#options + 1] = { key = "YELL", label = "Yell (/yell)", type = "YELL" }
    return options
end

function A.GetDestination()
    for _, option in ipairs(A.ChannelOptions()) do
        if option.key == A.db.channel then return option end
    end
end

function A.CooldownRemaining()
    return math.max(0, math.ceil(A.cooldown - (GetTime() - (A.lastSent or -A.cooldown))))
end

function A.PrepareMessage()
    A.ReadQuests(true)
    for key, selected in pairs(A.db.selected) do
        if selected and key:sub(1, 2) == "q:" and not A.questReady then return nil, "Quest log is updating. Please try again in a moment." end
    end
    local message, err = A.BuildMessage(true)
    if err then return nil, err end
    local destination = A.GetDestination()
    if not destination then return nil, "Choose an available channel." end
    return message, nil, destination
end

function A.SendAnnouncement()
    local message, err, destination = A.PrepareMessage()
    if err then return false, err end
    if A.CooldownRemaining() > 0 then return false, "Wait " .. A.CooldownRemaining() .. " seconds before posting again." end
    local send = C_ChatInfo and C_ChatInfo.SendChatMessage or SendChatMessage
    local ok, reason = pcall(send, message, destination.type, nil, destination.id and tostring(destination.id))
    if not ok then return false, "Could not send: " .. tostring(reason) end
    A.lastSent = GetTime()
    if A.announcing then
        A.nextAnnouncement = A.lastSent + A.db.announcementInterval
        A.announcementPending = false
    end
    return true, "Announcement sent to " .. destination.label .. "."
end

function A.StartAnnouncing()
    if A.GroupSize() >= A.RecruitmentTarget() then
        return false, "The group already has " .. A.GroupSize() .. " players. Choose a higher stop target."
    end
    local _, err = A.PrepareMessage()
    if err then return false, err end
    if A.CooldownRemaining() == 0 then
        local ok, result = A.SendAnnouncement()
        if not ok then return false, result end
    end
    A.announcing = true
    A.announcementChannel = A.db.channel
    A.announcementPending = false
    A.nextAnnouncement = math.max(GetTime(), (A.lastSent or GetTime()) + A.db.announcementInterval)
    if not A.db.autoJoin then return true, "Announcing started. Autojoin is off." end
    return true, A.HasSelectedDungeon() and "Announcing started. Whisper inv tank, inv heal or inv dps to join."
        or "Announcing started. Whispers containing 'inv' will trigger a group invite."
end

function A.StopAnnouncing()
    A.announcing = false
    A.announcementPending = false
    A.nextAnnouncement = nil
    A.announcementChannel = nil
end

function A.SetAnnouncementInterval(seconds)
    seconds = tonumber(seconds)
    if not seconds or seconds < 30 or seconds > 300 or seconds % 1 ~= 0 then
        return false, "Enter a whole number from 30 to 300 seconds."
    end
    A.db.announcementInterval = seconds
    if A.announcing then
        A.nextAnnouncement = math.max(GetTime(), (A.lastSent or GetTime()) + A.db.announcementInterval)
        A.announcementPending = false
    end
    return true
end

function A.GroupSize()
    return math.max(1, GetNumGroupMembers())
end

function A.CheckGroupTarget()
    if A.announcing and A.GroupSize() >= A.RecruitmentTarget() then
        local size, target = A.GroupSize(), A.RecruitmentTarget()
        A.StopAnnouncing()
        return true, "Target reached (" .. size .. "/" .. target .. " players). Announcing and auto-invite stopped."
    end
end

function A.SetPlayerTarget(players)
    players = tonumber(players)
    if not players or players < 2 or players > 40 or players % 1 ~= 0 then
        return false, "Enter a whole number from 2 to 40 players, including yourself."
    end
    A.db.stopAtPlayers = players
    local _, result = A.CheckGroupTarget()
    return true, result
end

function A.TickAnnouncing()
    if not A.announcing then return end
    local stopped, result = A.CheckGroupTarget()
    if stopped then return true, result end
    if A.db.channel ~= A.announcementChannel then
        A.StopAnnouncing()
        return false, "Announcing stopped: the selected channel changed."
    end
    if GetTime() < A.nextAnnouncement then return end
    if A.announcementPending then
        local _, err = A.BuildMessage()
        if err or not A.GetDestination() then
            A.StopAnnouncing()
            return false, "Announcing stopped: " .. (err or "the channel is unavailable.")
        end
        return
    end
    local _, err, destination = A.PrepareMessage()
    if err then
        A.StopAnnouncing()
        return false, "Announcing stopped: " .. err
    end
    -- Public chat requires a real hardware event. A timer can only prepare the
    -- next post there; the user clicks Post announce to publish it.
    if destination.type == "CHANNEL" or destination.type == "SAY" or destination.type == "YELL" then
        A.announcementPending = true
        return true, "Announcement ready. Click Post announce to publish."
    end
    local ok, result = A.SendAnnouncement()
    if not ok then A.StopAnnouncing() end
    return ok, result
end

function A.HandleWhisper(message, sender)
    if not A.announcing or not message or not sender or not message:lower():find("inv", 1, true) then return end
    local stopped, result = A.CheckGroupTarget()
    if stopped then return true, result end
    if A.IsSelf(sender) then return end
    local dungeon, role, roleError = A.HasSelectedDungeon(), A.WhisperRole(message)
    if UnitInParty(sender) or UnitInRaid(sender) then
        if dungeon and role then
            A.RecordMemberRole(sender, role)
            return true, sender .. " is assigned as " .. A.RoleLabel(role) .. "."
        end
        return
    end
    if not A.db.autoJoin then return end
    if IsInGroup() and not UnitIsGroupLeader("player") and not (IsInRaid() and UnitIsGroupAssistant("player")) then
        return false, "Cannot invite " .. sender .. ": you do not have permission to invite."
    end
    if GetNumGroupMembers() >= (IsInRaid() and 40 or 5) then
        return false, "Cannot invite " .. sender .. ": the group is full."
    end
    if dungeon then
        if not role then return false, "Cannot invite " .. sender .. ": " .. roleError end
        local available, err = A.CanInviteRole(role, sender)
        if not available then return false, "Cannot invite " .. sender .. ": " .. err end
    end
    local senderKey = A.NameKey(sender)
    if A.recentInvites[senderKey] and GetTime() - A.recentInvites[senderKey] < 15 then
        local pending = A.pendingRoles[senderKey]
        if dungeon and pending and pending.role ~= role then
            pending.role = role
            return true, sender .. " is assigned as " .. A.RoleLabel(role) .. " for the pending invitation."
        end
        return
    end
    local invite = C_PartyInfo and C_PartyInfo.InviteUnit or InviteUnit
    local ok, reason = pcall(invite, sender)
    if not ok then return false, "Could not invite " .. sender .. ": " .. tostring(reason) end
    A.recentInvites[senderKey] = GetTime()
    if dungeon then A.pendingRoles[senderKey] = { role = role, time = GetTime() } end
    return true, "Invite requested for " .. sender .. (role and (" (" .. A.RoleLabel(role) .. ")") or "") .. "."
end

function A.OpenChat(text)
    if ChatFrameUtil and ChatFrameUtil.OpenChat then ChatFrameUtil.OpenChat(text) else ChatFrame_OpenChat(text) end
end

function A.EditAnnouncement()
    local message, err, destination = A.PrepareMessage()
    if err then return false, err end
    local command = destination.id and tostring(destination.id) or ({ SAY = "s", YELL = "y", GUILD = "g", PARTY = "p" })[destination.type]
    A.OpenChat("/" .. command .. " " .. message)
    return true, "Text opened in chat. Press Enter to post."
end

function A.MatchActivities(message, selectedOnly)
    local normalized, matches = A.Normalize(message), {}
    for _, quest in ipairs(A.quests) do
        if (not selectedOnly or A.db.selected[quest.key]) and
            (message:find("|Hquest:" .. quest.id .. ":", 1, true) or Contains(normalized, quest.name)) then
            matches[#matches + 1] = quest.name
        end
    end
    for _, dungeon in ipairs(A.AvailableDungeons()) do
        if not selectedOnly or A.db.selected["d:" .. dungeon.id] then
            local found = Contains(normalized, dungeon.name)
            for _, alias in ipairs(dungeon.aliases) do found = found or Contains(normalized, alias) end
            if found then matches[#matches + 1] = dungeon.name end
        end
    end
    return matches
end

function A.ReceiveMessage(message, sender, channel)
    if not message or not sender or Ambiguate(sender, "short") == UnitName("player") then return end
    local text = A.Normalize(message)
    local recruiting = text:find("%f[%a]lf[gm]%f[%A]") or text:find("%f[%a]lf%d+m%f[%A]")
        or text:find("looking for", 1, true) or text:find("%f[%a]lf%f[%A]")
        or text:find("cerco", 1, true) or text:find("cercasi", 1, true) or text:find("anyone", 1, true)
    if not recruiting or #A.MatchActivities(message) == 0 then return end
    for i = #A.messages, 1, -1 do
        if A.messages[i].sender == sender and A.messages[i].normalized == text then table.remove(A.messages, i) end
    end
    table.insert(A.messages, 1, { text = message, normalized = text, sender = sender, channel = channel, time = GetTime() })
    while #A.messages > 80 do table.remove(A.messages) end
end

function A.VisibleMessages()
    local messages = {}
    for i = #A.messages, 1, -1 do
        if GetTime() - A.messages[i].time > A.messageLifetime then table.remove(A.messages, i) end
    end
    for _, entry in ipairs(A.messages) do
        if #A.MatchActivities(entry.text, A.db.selectedOnly) > 0 then messages[#messages + 1] = entry end
    end
    return messages
end
