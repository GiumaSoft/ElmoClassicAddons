local addonName, A = ...
ElmoLFM = A
A.version = "1.0.8"
A.results, A.selected, A.contacts, A.tickets, A.invites = {}, {}, {}, {}, {}
A.WHO_TIMEOUT, A.CONTACT_DELAY, A.REPLY_WINDOW = 120, 300, 600
local frame, elapsed = CreateFrame("Frame"), 0
local DEFAULT_MESSAGE = "Hi! Looking for players in {zone} (levels {min}-{max}). Reply inv if you'd like to join."

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
local function checked(ok, ...) if ok then return ... end end
function A.Call(fn, ...) if type(fn) == "function" then return checked(pcall(fn, ...)) end end
local function trim(text) return text:match("^%s*(.-)%s*$") end
local function whoAPI(name, legacy) return C_FriendList and C_FriendList[name] or _G[legacy or name] end
function A.Print(text) DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoLFM:|r " .. text) end
function A.Refresh() if A.UI then A.UI.Refresh() end end
function A.Status(text, error)
    A.status, A.error = text, error == true
    A.Refresh()
end

function A.NameKey(name)
    name = A.Text(name)
    if not name or name == "" or name:find("[%c|]") then return end
    local player, realm = name:match("^([^%-]+)%-(.+)$")
    if not player then player, realm = name, A.Text(A.Call(GetNormalizedRealmName)) or A.Text(A.Call(GetRealmName)) end
    return player:lower() .. (realm and ("-" .. realm:lower():gsub("%s", "")) or "")
end
function A.IsMember(name)
    local ownName, realm = A.Call(UnitFullName or UnitName, "player")
    ownName, realm = A.Text(ownName), A.Text(realm)
    if ownName and A.NameKey(name) == A.NameKey(ownName .. (realm and realm ~= "" and ("-" .. realm) or "")) then return true end
    local raid = A.Call(UnitInRaid, name)
    return A.Bool(A.Call(UnitInParty, name)) == true or A.Bool(raid) == true or
        (A.Number(raid) ~= nil and raid > 0)
end
function A.FreeSlots()
    local count = A.Number(A.Call(GetNumGroupMembers))
    if not count then return 0 end
    count = math.max(1, count)
    for key, invite in pairs(A.invites) do
        if GetTime() >= invite.expires or A.IsMember(invite.name) then A.invites[key] = nil
        else count = count + 1 end
    end
    return math.max(0, (A.Bool(A.Call(IsInRaid)) and 40 or 5) - count)
end
function A.CanInvite()
    if A.FreeSlots() == 0 then return false, "The group is full or its remaining invitations are pending." end
    if C_PartyInfo and type(C_PartyInfo.CanInvite) == "function" then
        if A.Bool(A.Call(C_PartyInfo.CanInvite)) ~= true then return false, "You do not have permission to invite." end
    elseif A.Bool(A.Call(IsInGroup)) and A.Bool(A.Call(UnitIsGroupLeader, "player")) ~= true and
        not (A.Bool(A.Call(IsInRaid)) and A.Bool(A.Call(UnitIsGroupAssistant, "player"))) then
        return false, "You do not have permission to invite."
    end
    return true
end
function A.InvitePlayer(name)
    name = A.Text(name)
    local key = A.NameKey(name)
    if not key then A.Status("Choose a valid player to invite.", true); return false end
    if A.IsMember(name) then
        A.tickets[key], A.invites[key] = nil, nil
        A.Status(name .. " is already in your group."); return false
    end
    A.FreeSlots()
    if A.invites[key] then A.Status("An invitation to " .. name .. " is already pending."); return false end
    local allowed, reason = A.CanInvite()
    if not allowed then A.Status(reason, true); return false end
    local invite = C_PartyInfo and C_PartyInfo.InviteUnit or InviteUnit
    local ok, error = pcall(invite, name)
    if not ok or error == false then
        A.Status("Could not invite " .. name .. ": " .. (A.Text(error) or "blocked by the client."), true)
        return false
    end
    A.invites[key] = {name = name, expires = GetTime() + 60}
    local contact = A.contacts[key]
    if contact then contact.state = "Invite requested" end
    A.Status("Invite requested for " .. name .. ".")
    return true
end
function A.Contactable(player)
    if A.IsMember(player.name) then return false end
    local contact = A.contacts[player.key]
    return not contact or GetTime() - contact.time >= A.CONTACT_DELAY
end
function A.ReleaseWho()
    local visible = A.Bool(A.Call(WhoFrame and WhoFrame.IsShown, WhoFrame)) or
        A.Bool(A.Call(LFGWhoListFrame and LFGWhoListFrame.IsShown, LFGWhoListFrame)) or false
    A.Call(whoAPI("SetWhoToUi", "SetWhoToUI"), visible)
end

function A.Query(zone, low, high)
    zone = trim(A.Text(zone) or "")
    low, high = tonumber(low), tonumber(high)
    if zone == "" or zone:find('["%c|]') then return nil, "Enter a zone without quotes, links or line breaks." end
    if not A.Number(low) or not A.Number(high) or low % 1 ~= 0 or high % 1 ~= 0 or low < 1 or high > 60 or low > high then
        return nil, "Choose a level range between 1 and 60, with minimum no greater than maximum."
    end
    local query = (WHO_TAG_ZONE or "z-") .. '"' .. zone .. '" ' .. low .. "-" .. high
    if #query > 255 then return nil, "The zone name is too long." end
    return query, nil, zone, low, high
end
function A.Search(zone, low, high)
    local query, err, clean, minimum, maximum = A.Query(zone, low, high)
    if err then A.Status(err, true); return false end
    if A.search or A.queue then A.Status("Finish or stop the current search or whisper batch first.", true); return false end
    if A.query and A.query ~= query then A.tickets = {} end
    A.db.zone, A.db.minimum, A.db.maximum = clean, minimum, maximum
    A.query = query
    A.results, A.selected, A.resultsAt = {}, {}, nil
    A.search = {zone = clean, low = minimum, high = maximum, expires = GetTime() + A.WHO_TIMEOUT}
    A.Call(whoAPI("SetWhoToUi", "SetWhoToUI"), true)
    A.Status("Press Enter in chat to run /who. Or copy the command above into chat; Stop cancels waiting.")
    -- Preparing chat text does not execute the restricted WHO action.
    -- The player's next Enter key invokes Blizzard's own slash-command handler.
    A.Call(ChatFrameUtil and ChatFrameUtil.OpenChat or ChatFrame_OpenChat, "/who " .. query)
    return true
end
local function whoInfo(index)
    if C_FriendList and C_FriendList.GetWhoInfo then return C_FriendList.GetWhoInfo(index) end
    local name, guild, level, race, class, area, filename = GetWhoInfo(index)
    if name then return {fullName = name, fullGuildName = guild, level = level, raceStr = race,
        classStr = class, area = area, filename = filename} end
end
function A.ImportWho(zone, low, high)
    local query, err, clean, minimum, maximum = A.Query(zone, low, high)
    if err then A.Status(err, true); return false end
    if A.queue then A.Status("Finish or stop the whisper batch before importing WHO results.", true); return false end
    local count, total = A.Call(whoAPI("GetNumWhoResults"))
    count, total = A.Number(count), A.Number(total)
    if not count then A.Status("The client did not expose a readable WHO count. Run a native /who first.", true); return false end
    local results, seen = {}, {}
    local skipped = {unreadable = 0, duplicate = 0}
    for index = 1, math.min(50, count) do
        local info = A.Call(whoInfo, index)
        if not A.Private(info) and type(info) == "table" and
            (type(canaccesstable) ~= "function" or canaccesstable(info)) then
            local name, level, area = A.Text(info.fullName), A.Number(info.level), A.Text(info.area)
            local key = A.NameKey(name)
            if key and level and area then
                if seen[key] then skipped.duplicate = skipped.duplicate + 1
                else
                    seen[key] = true
                    results[#results + 1] = {name = name, key = key, level = level, area = area,
                        class = A.Text(info.classStr) or "?", classFile = A.Text(info.filename), guild = A.Text(info.fullGuildName)}
                end
            else skipped.unreadable = skipped.unreadable + 1 end
        else skipped.unreadable = skipped.unreadable + 1 end
    end
    if A.query and A.query ~= query then A.tickets = {} end
    A.db.zone, A.db.minimum, A.db.maximum = clean, minimum, maximum
    A.query, A.selected, A.whoSkipped = query, {}, skipped
    if A.search then A.search = nil; A.ReleaseWho() end
    A.results, A.resultsAt, A.returned, A.total = results, GetTime(), count, total or count
    A.Status("Showing " .. #results .. " of " .. count .. " Blizzard WHO players, including other zones.\n" ..
        "Excluded: " .. skipped.unreadable .. " unreadable, " .. skipped.duplicate .. " duplicates." ..
        ((count >= 50 or A.total > count) and "\nWHO limit reached; narrow the native search." or ""))
    return true
end
function A.ReceiveWho()
    local search = A.search
    if not search then return end
    search.received = true
    if GetTime() >= search.expires then A.Tick(); return end
    return A.ImportWho(search.zone, search.low, search.high)
end

function A.Message()
    local message = A.db.message:gsub("%{zone%}", function() return A.db.zone end)
        :gsub("%{min%}", tostring(A.db.minimum)):gsub("%{max%}", tostring(A.db.maximum))
    message = trim(message:gsub("[\r\n]+", " "))
    if message == "" then return nil, "Write a whisper message first." end
    if #message > 255 then return nil, "The whisper exceeds 255 bytes. Shorten the message." end
    return message
end
function A.SendSelected()
    if A.queue or A.search then A.Status("Finish or stop the current search or whisper batch first.", true); return false end
    if not A.resultsAt or GetTime() - A.resultsAt >= 300 then A.Status("Search again to refresh the player list.", true); return false end
    local message, err = A.Message()
    if err then A.Status(err, true); return false end
    if A.FreeSlots() == 0 then A.Status("The group is full or its invitations are pending.", true); return false end
    if A.db.autoInvite then
        local allowed, reason = A.CanInvite()
        if not allowed then A.Status(reason, true); return false end
    end
    local players = {}
    for _, player in ipairs(A.results) do
        if A.selected[player.key] and A.Contactable(player) then players[#players + 1] = player end
    end
    if #players == 0 then A.Status("Select at least one player who has not been contacted in the last 5 minutes.", true); return false end
    A.queue = {players = players, message = message, next = 1, at = GetTime()}
    A.Tick()
    return true
end
function A.SetAutoInvite(enabled)
    A.db.autoInvite = enabled == true
    if not A.db.autoInvite then A.tickets = {} end
    A.Refresh()
end
function A.HandleWhisper(message, sender)
    message, sender = A.Text(message), A.Text(sender)
    if not message or not sender then return end
    local key = A.NameKey(sender)
    local contact = key and A.contacts[key]
    if contact then
        contact.reply, contact.replyTime, contact.sent = message, GetTime(), true
        if contact.state == "Whisper requested" then contact.state = "Whisper sent" end
        A.Refresh()
    end
    if not A.db.autoInvite then return end
    local command = message:lower():match("^%s*(%a+)")
    if command ~= "inv" and command ~= "invite" then return end
    local ticket = key and A.tickets[key]
    if not ticket or GetTime() >= ticket.expires then return end
    return A.InvitePlayer(ticket.name)
end
function A.Stop()
    if A.search then A.search = nil; A.ReleaseWho() end
    A.queue, A.tickets = nil, {}
    A.Status("Recruitment stopped. Existing invitations can still be accepted.")
end
function A.Tick()
    local now = GetTime()
    if A.search and now >= A.search.expires then
        local received = A.search.received
        A.search = nil; A.ReleaseWho()
        A.Status(received and "WHO replied, but the client did not expose readable results." or
            "No WHO results received. Prepare /who again and press Enter in chat to run it.", true)
    end
    for key, ticket in pairs(A.tickets) do if now >= ticket.expires then A.tickets[key] = nil end end
    local queue = A.queue
    if not queue or now < queue.at then return end
    if A.FreeSlots() == 0 then A.Stop(); A.Status("The group is full; recruitment stopped."); return end
    if A.db.autoInvite then
        local allowed, reason = A.CanInvite()
        if not allowed then A.Stop(); A.Status(reason, true); return end
    end
    local player = queue.players[queue.next]
    if A.Contactable(player) then
        local send = C_ChatInfo and C_ChatInfo.SendChatMessage or SendChatMessage
        local previous = A.contacts[player.key]
        A.contacts[player.key] = {name = player.name, time = now, message = queue.message, state = "Whisper requested"}
        local ok, reason = pcall(send, queue.message, "WHISPER", nil, player.name)
        if not ok or reason == false then
            A.contacts[player.key] = previous
            A.queue = nil; A.Status("Could not whisper " .. player.name .. ": " .. (A.Text(reason) or "blocked by the client. Retry with Send selected."), true); return
        end
        if A.db.autoInvite then A.tickets[player.key] = {name = player.name, expires = now + A.REPLY_WINDOW} end
        A.selected[player.key] = nil
    end
    queue.next, queue.at = queue.next + 1, now + 1
    if queue.next > #queue.players then
        A.queue = nil; A.Status("Whisper batch finished." .. (A.db.autoInvite and " Interested players can reply inv." or ""))
    else A.Status("Sending whispers: " .. (queue.next - 1) .. "/" .. #queue.players .. ".") end
end
function A.Command(command)
    command = trim(command or ""):lower()
    if command == "stop" then A.Stop(); A.Print(A.status)
    elseif command == "minimap" or command == "minimap show" then A.Minimap.SetVisible(true)
    elseif command == "minimap hide" then A.Minimap.SetVisible(false)
    elseif command == "options" then A.Settings.Open()
    elseif command == "import" then A.UI.Open(); A.UI.ImportWho(); A.Print(A.status)
    elseif command == "status" then
        A.Print("v" .. A.version .. " | " .. (A.query or "No query") .. " | " .. #A.results .. " rows\n" ..
            (A.status or "Ready. No active recruitment."))
    elseif command == "" then A.UI.Toggle()
    else A.Print("/elfm: recruitment window. /elfm import | stop | options | status | minimap show|hide") end
end
function A.Initialize()
    if A.db then return end
    local db = type(ElmoLFMDB) == "table" and ElmoLFMDB or {}
    local level = math.max(1, math.min(60, A.Number(A.Call(UnitLevel, "player")) or 1))
    db.zone = A.Text(db.zone) or A.Text(A.Call(GetRealZoneText or GetZoneText)) or ""
    db.minimum = math.max(1, math.min(60, math.floor(A.Number(tonumber(db.minimum)) or math.max(1, level - 2))))
    db.maximum = math.max(db.minimum, math.min(60, math.floor(A.Number(tonumber(db.maximum)) or math.min(60, level + 2))))
    db.message, db.autoInvite = A.Text(db.message) or DEFAULT_MESSAGE, db.autoInvite ~= false
    ElmoLFMDB, A.db = db, db
    SLASH_ELMOLFM1, SLASH_ELMOLFM2 = "/elfm", "/elmolfm"
    SlashCmdList.ELMOLFM = A.Command
    A.Minimap.Register()
    A.Settings.Register()
end
frame:SetScript("OnEvent", function(_, event, ...)
    if event == "ADDON_LOADED" then if ... == addonName then A.Initialize() end; return end
    if not A.db then return end
    if event == "ADDON_ACTION_BLOCKED" or event == "ADDON_ACTION_FORBIDDEN" then
        local source, action = ...
        source, action = A.Text(source), A.Text(action)
        if A.search and (source == addonName or action and action:find("SendWho", 1, true)) then
            A.search = nil
            A.ReleaseWho()
            A.Status("Native WHO was blocked (" .. (source or addonName) .. "). Reload, prepare /who and run it from chat.", true)
        end
    elseif event == "WHO_LIST_UPDATE" then
        if A.search then A.ReceiveWho()
        elseif not A.queue and A.UI.frame and A.UI.frame:IsShown() then A.UI.ImportWho() end
    elseif event == "CHAT_MSG_WHISPER" then A.HandleWhisper(...)
    elseif event == "CHAT_MSG_WHISPER_INFORM" then
        local message, name = ...
        local key = A.NameKey(name)
        local contact = key and A.contacts[key]
        if contact and A.Text(message) == contact.message then
            contact.sent = true
            if contact.state == "Whisper requested" then contact.state = "Whisper sent" end
        end
    elseif event == "GROUP_ROSTER_UPDATE" then
        for key, ticket in pairs(A.tickets) do
            if A.IsMember(ticket.name) then A.tickets[key], A.invites[key] = nil, nil end
        end
        if A.FreeSlots() == 0 and A.queue then A.Stop() end
    end
    A.Refresh()
end)
for _, event in ipairs({"ADDON_LOADED", "WHO_LIST_UPDATE", "CHAT_MSG_WHISPER", "CHAT_MSG_WHISPER_INFORM",
    "GROUP_ROSTER_UPDATE", "ADDON_ACTION_BLOCKED", "ADDON_ACTION_FORBIDDEN"}) do frame:RegisterEvent(event) end
frame:SetScript("OnUpdate", function(_, dt)
    if not A.db then return end
    elapsed = elapsed + dt
    if elapsed >= .2 then elapsed = 0; A.Tick(); A.Refresh() end
end)
