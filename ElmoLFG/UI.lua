local addonName, A = ...
local Theme = A.Theme
local frame, scroll, content, search, preview, note, channelMenu, sendButton, status, meta, selectedCount
local startButton, stopButton, autoStatus, announcerPrompt, intervalInput, targetInput
local resetTextButton, customMessageLabel, updatingCustomMessage
local composerError
local roleButtons, tabButtons, rows = {}, {}, {}
local groupRolesFrame, groupRoleRows, RefreshGroupRoles = nil, {}, nil
local tab, refreshPending, elapsed = "quests", false, 0

local function Label(parent, text, x, y, font)
    local label = parent:CreateFontString(nil, "OVERLAY", font or "GameFontNormal")
    label:SetPoint("TOPLEFT", x, y)
    label:SetText(text)
    label:SetShadowColor(0, 0, 0, 1)
    label:SetShadowOffset(1, -1)
    return label
end

local function Button(parent, text, width, x, y, action)
    return Theme.Button(parent, text, width, x, y, action)
end

local function SetStatus(text, error)
    status:SetText(text or "")
    status:SetTextColor(error and 1 or 0.7, error and 0.35 or 0.85, error and 0.25 or 0.7)
end

local function RefreshComposer()
    local message, err, chatBytes = A.BuildMessage()
    if preview:GetText() ~= message then preview:SetText(message) end
    local text = A.GetAnnouncementText()
    if note:GetText() ~= text then
        updatingCustomMessage = true
        note:SetText(text)
        updatingCustomMessage = false
    end
    local custom = A.IsCustomAnnouncement()
    customMessageLabel:SetText(custom and "Custom message · Edited" or "Custom message (optional)")
    resetTextButton:SetEnabled(custom)
    selectedCount:SetText(#A.SelectedActivities() .. " activities selected · " .. (chatBytes or 0) .. "/255 bytes")
    local destination = A.GetDestination()
    UIDropDownMenu_SetText(channelMenu, destination and destination.label or "Choose a channel")
    for role, button in pairs(roleButtons) do button:SetChecked(A.db.playerRole == role) end
    frame.roleLabel:SetText("Your dungeon role")
    local remaining = A.CooldownRemaining()
    sendButton:SetText(remaining > 0 and ("Wait " .. remaining .. "s") or "Post announce")
    sendButton:SetEnabled(not err and destination ~= nil and remaining == 0)
    frame.editButton:SetEnabled(not err and destination ~= nil)
    startButton:SetEnabled(not A.announcing and not err and destination ~= nil)
    stopButton:SetEnabled(A.announcing)
    if not intervalInput:HasFocus() then intervalInput:SetText(tostring(A.db.announcementInterval)) end
    if not targetInput:HasFocus() then targetInput:SetText(tostring(A.db.stopAtPlayers)) end
    frame.autoJoin:SetChecked(A.db.autoJoin)
    local autoInvite = A.db.autoJoin and "ON" or "OFF"
    if not A.announcing then
        autoStatus:SetText("Stopped · Auto-invite: OFF")
    elseif A.announcementPending then
        autoStatus:SetText("Ready · Click Post announce · Auto-invite: " .. autoInvite)
    else
        local remaining = math.max(0, math.ceil(A.nextAnnouncement - GetTime()))
        local public = destination and (destination.type == "CHANNEL" or destination.type == "SAY" or destination.type == "YELL")
        autoStatus:SetText((public and "Next reminder in " or "Next post in ") .. remaining .. "s · Auto-invite: " .. autoInvite)
    end
    autoStatus:SetText(autoStatus:GetText() .. "\n" .. A.GroupSize() .. "/" .. A.RecruitmentTarget() .. " players")
    if groupRolesFrame and groupRolesFrame:IsShown() then RefreshGroupRoles() end
    if err then SetStatus(err, true)
    elseif composerError and status:GetText() == composerError then SetStatus("") end
    composerError = err
end

RefreshGroupRoles = function()
    local group = A.GroupComposition()
    for i, row in ipairs(groupRoleRows) do
        local member = group.roster[i]
        row:SetShown(member ~= nil)
        if member then
            row.member = member
            row.name:SetText((member.isPlayer and "You" or member.name) .. " · " .. A.RoleLabel(member.role))
            for role, button in pairs(row.buttons) do
                if member.role == role then button:LockHighlight() else button:UnlockHighlight() end
            end
        end
    end
    groupRolesFrame.summary:SetText("Open: " .. A.DungeonRoleText())
end

local function OpenGroupRoles()
    if not groupRolesFrame then
        local f = CreateFrame("Frame", "ElmoLFGGroupRoles", UIParent, "BackdropTemplate")
        groupRolesFrame = f
        f:SetSize(490, 308)
        f:SetScale(frame:GetScale())
        f:SetPoint("CENTER", frame, "CENTER")
        f:SetFrameStrata("FULLSCREEN_DIALOG")
        f:SetClampedToScreen(true)
        f:EnableMouse(true)
        Theme.Panel(f)
        Label(f, "Dungeon group roles", 16, -16, "GameFontNormalLarge")
        Label(f, "1 Tank · 1 Heal · 3 Dps. Invites and assigned roles update automatically.", 16, -43, "GameFontHighlightSmall")
        Button(f, "×", 24, 453, -11, function() f:Hide() end):SetHeight(24)
        table.insert(UISpecialFrames, "ElmoLFGGroupRoles")
        for i = 1, 5 do
            local row = CreateFrame("Frame", nil, f)
            row:SetSize(458, 32)
            row:SetPoint("TOPLEFT", 16, -68 - (i - 1) * 36)
            row.name = Label(row, "", 0, -8, "GameFontHighlightSmall")
            row.name:SetWidth(196)
            row.name:SetWordWrap(false)
            row.buttons = {}
            for j, entry in ipairs({ { "Tank", "Tank" }, { "Healer", "Heal" }, { "DPS", "Dps" }, { "Auto", "Auto" } }) do
                local role = entry[1]
                row.buttons[role] = Button(row, entry[2], 58, 202 + (j - 1) * 64, 0, function()
                    if row.member then A.SetMemberRole(row.member.key, role) end
                    SetStatus("")
                    RefreshComposer()
                end)
            end
            groupRoleRows[i] = row
        end
        f.summary = Label(f, "", 16, -260, "GameFontHighlightSmall")
        Label(f, "Unknown roles: choose above. Auto clears the assignment and uses client data.", 16, -283, "GameFontDisableSmall")
    end
    RefreshGroupRoles()
    groupRolesFrame:Show()
end

local function RowTooltip(row)
    if not row.data then return end
    GameTooltip:SetOwner(row, "ANCHOR_RIGHT")
    local item = row.data
    if tab == "board" then
        GameTooltip:AddLine(item.sender, 1, 0.82, 0)
        GameTooltip:AddLine(item.text, 1, 1, 1, true)
        GameTooltip:AddLine("Click to prepare a whisper.", 0.6, 0.85, 1)
    elseif tab == "quests" then
        if item.link then
            GameTooltip:SetHyperlink(item.link)
        else
            GameTooltip:AddLine(item.name, 1, 0.82, 0)
            GameTooltip:AddLine(item.zone, 1, 1, 1)
        end
    else
        GameTooltip:AddLine(item.name, 1, 0.82, 0)
        GameTooltip:AddLine("Minimum entry level: " .. item.min .. ". Recommended: " .. item.low .. "–" .. item.high .. ".", 1, 1, 1)
        if item.note then GameTooltip:AddLine(item.note, 0.8, 0.8, 0.8, true) end
    end
    GameTooltip:Show()
end

local function ClickRow(row)
    if tab == "board" then
        local roles = A.RoleText()
        local class = UnitClass("player")
        A.OpenChat("/w " .. row.data.sender .. " Hi! " .. UnitLevel("player") .. " " .. class .. (roles ~= "" and (" " .. roles) or "") .. " here, still looking?")
    else
        local key = row.data.key or ("d:" .. row.data.id)
        A.db.selected[key] = not A.db.selected[key] or nil
        A.RefreshList()
        SetStatus("")
        RefreshComposer()
    end
end

local function GetRow(index)
    if rows[index] then return rows[index] end
    local row = CreateFrame("Button", nil, content)
    row:SetHighlightTexture("Interface\\Buttons\\WHITE8X8")
    row:GetHighlightTexture():SetVertexColor(1, 0.82, 0, 0.08)
    row.check = CreateFrame("CheckButton", nil, row, "UICheckButtonTemplate")
    row.check:SetSize(26, 26)
    row.check:SetPoint("TOPLEFT", 0, -3)
    row.check:SetScript("OnClick", function() ClickRow(row) end)
    row.title = Label(row, "", 32, -3, "GameFontHighlight")
    row.title:SetJustifyH("LEFT")
    row.title:SetWordWrap(false)
    row.detail = Label(row, "", 32, -19, "GameFontHighlightSmall")
    row.detail:SetJustifyH("LEFT")
    row.detail:SetTextColor(0.65, 0.65, 0.65)
    row.reply = Button(row, "Whisper", 74, 0, 0, function() ClickRow(row) end)
    row.reply:ClearAllPoints()
    row.reply:SetPoint("TOPRIGHT", -4, -12)
    row:SetScript("OnClick", ClickRow)
    row:SetScript("OnEnter", RowTooltip)
    row:SetScript("OnLeave", function() GameTooltip:Hide() end)
    row.check:SetScript("OnEnter", function() RowTooltip(row) end)
    row.check:SetScript("OnLeave", function() GameTooltip:Hide() end)
    rows[index] = row
    return row
end

function A.RefreshList()
    if not frame then return end
    local items = tab == "quests" and A.quests or (tab == "dungeons" and A.AvailableDungeons() or A.VisibleMessages())
    local query, shown = A.Normalize(search:GetText()), 0
    local board = tab == "board"
    local height = board and 62 or 38
    local width = scroll:GetWidth()
    content:SetWidth(width)
    for _, item in ipairs(items) do
        local haystack = board and (item.sender .. " " .. item.text) or (item.name .. " " .. (item.zone or ""))
        if tab == "dungeons" then haystack = haystack .. " " .. table.concat(item.aliases, " ") end
        if query == "" or A.Normalize(haystack):find(query, 1, true) then
            shown = shown + 1
            local row = GetRow(shown)
            row.data = item
            row:ClearAllPoints()
            row:SetPoint("TOPLEFT", 0, -(shown - 1) * height)
            row:SetSize(width, height)
            row.check:SetShown(not board)
            row.reply:SetShown(board)
            row.title:ClearAllPoints()
            row.title:SetPoint("TOPLEFT", board and 6 or 32, -3)
            row.title:SetWidth(width - (board and 100 or 42))
            row.detail:ClearAllPoints()
            row.detail:SetPoint("TOPLEFT", board and 6 or 32, -20)
            row.detail:SetWidth(width - (board and 100 or 42))
            row.detail:SetHeight(board and 36 or 16)
            row.detail:SetWordWrap(board)
            if board then
                row.title:SetText(item.sender .. " · " .. (item.channel or "Chat") .. " · " .. math.floor((GetTime() - item.time) / 60) .. "m")
                row.title:SetTextColor(1, 0.82, 0)
                row.detail:SetText(item.text)
            else
                local key = item.key or ("d:" .. item.id)
                row.check:SetChecked(A.db.selected[key])
                if tab == "quests" then
                    local difficulty = C_PlayerInfo and C_PlayerInfo.GetContentDifficultyQuestForPlayer and GetDifficultyColor and
                        GetDifficultyColor(C_PlayerInfo.GetContentDifficultyQuestForPlayer(item.id)) or GetQuestDifficultyColor(item.level)
                    local r, g, b = difficulty.r, difficulty.g, difficulty.b
                    if QuestDifficultyColors and difficulty == QuestDifficultyColors.trivial then r, g, b = 0.75, 0.75, 0.75 end
                    local levelText = string.format("|cff%02x%02x%02x[%s]|r",
                        math.floor(r * 255 + 0.5), math.floor(g * 255 + 0.5), math.floor(b * 255 + 0.5), A.QuestLevel(item))
                    row.title:SetText(levelText .. " " .. item.name)
                    row.title:SetTextColor(item.complete == 1 and 0.3 or 1, 1, item.complete == 1 and 0.3 or 1)
                    row.detail:SetText(item.zone .. (item.tag and (" · " .. item.tag) or "") .. (item.complete == 1 and " · Ready to turn in" or (item.complete == -1 and " · Failed" or "")))
                else
                    row.title:SetText(item.name)
                    row.title:SetTextColor(1, UnitLevel("player") < item.low and 0.65 or 1, UnitLevel("player") < item.low and 0.3 or 1)
                    row.detail:SetText("Entry " .. item.min .. "+ · Recommended " .. item.low .. "–" .. item.high .. (item.note and " · Details in tooltip" or ""))
                end
            end
            row:Show()
        end
    end
    for i = shown + 1, #rows do rows[i]:Hide() end
    content:SetHeight(math.max(scroll:GetHeight(), shown * height))
    scroll:SetVerticalScroll(math.min(scroll:GetVerticalScroll(), math.max(0, shown * height - scroll:GetHeight())))
    frame.empty:SetShown(shown == 0)
    frame.empty:SetText(board and "No matching announcements received in the last 5 minutes.\nListening to your joined channels. Use Join LFG to add LookingForGroup."
        or (tab == "quests" and "No matching active quests in your quest log." or "No matching dungeons available at your level."))
    meta:SetText(tab == "quests" and (#A.quests .. " active quests") or
        (tab == "dungeons" and (#items .. "/" .. #A.dungeons .. " dungeons · Level " .. UnitLevel("player")) or (shown .. " announcements · Last 5 minutes")))
    frame.onlySelected:SetShown(board)
    frame.onlySelected:SetChecked(A.db.selectedOnly)
    for key, button in pairs(tabButtons) do
        if key == tab then button:LockHighlight() else button:UnlockHighlight() end
    end
end

local function SelectDefaultChannel()
    local options = A.ChannelOptions()
    for _, option in ipairs(options) do
        if option.key:lower():gsub("%s", ""):find("lookingforgroup", 1, true) then
            if not A.db.channel or A.waitForLFG then A.db.channel = option.key end
            A.waitForLFG = false
            return
        end
    end
    if not A.db.channel then A.db.channel = options[1].key end
end

function A.Refresh(force)
    if not A.db then return end
    A.ReadQuests(force)
    SelectDefaultChannel()
    if frame and frame:IsShown() then
        A.RefreshList()
        RefreshComposer()
    end
end

local function RefreshAnnouncerPrompt()
    if not announcerPrompt then return end
    announcerPrompt:SetShown(A.announcing and A.announcementPending and not frame:IsShown())
    if A.announcementPending then
        local destination = A.GetDestination()
        local join = A.HasSelectedDungeon() and "Autojoin ON: inv tank / inv heal / inv dps" or "Whisper inv: autojoin ON"
        if not A.db.autoJoin then join = "Autojoin OFF · Invite players manually" end
        announcerPrompt.detail:SetText((destination and destination.label or "Choose a channel") .. "\n" .. join)
    end
end

local function ShowAnnouncementResult(ok, result)
    A.RefreshList()
    RefreshComposer()
    RefreshAnnouncerPrompt()
    SetStatus(result, not ok)
    if not ok and not frame:IsShown() then print("|cffffd100ElmoLFG|r " .. result) end
end

local function PostAnnouncement()
    local ok, result = A.SendAnnouncement()
    if not ok and A.announcing then A.StopAnnouncing() end
    ShowAnnouncementResult(ok, result)
end

local function StopAnnouncing()
    A.StopAnnouncing()
    ShowAnnouncementResult(true, "Announcing stopped. Auto-invite is off.")
end

local function CreateWindow()
    frame = CreateFrame("Frame", "ElmoLFGFrame", UIParent, "BackdropTemplate")
    frame:SetSize(780, 730)
    frame:SetScale(math.min(1, (UIParent:GetWidth() - 30) / 780, (UIParent:GetHeight() - 30) / 730))
    Theme.Panel(frame)
    Theme.Inset(frame, 8, -8, 764, 50)
    Theme.Inset(frame, 16, -131, 748, 242)
    Theme.Inset(frame, 16, -413, 748, 188)
    Theme.Inset(frame, 16, -604, 748, 70)
    frame:SetFrameStrata("DIALOG")
    frame:SetClampedToScreen(true)
    frame:SetMovable(true)
    frame:EnableMouse(true)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", frame.StartMoving)
    frame:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local point, _, relativePoint, x, y = self:GetPoint()
        A.db.position = { point, relativePoint, x, y }
    end)
    if A.db.position then
        local p = A.db.position
        frame:SetPoint(p[1], UIParent, p[2], p[3], p[4])
    else frame:SetPoint("CENTER") end
    table.insert(UISpecialFrames, "ElmoLFGFrame")
    local close = Button(frame, "×", 24, 744, -15, function() frame:Hide() end)
    close:SetHeight(24)
    Label(frame, "ElmoLFG", 22, -16, "GameFontNormalLarge")
    Label(frame, "Quests and dungeons", 22, -39, "GameFontHighlightSmall")
    for i, entry in ipairs({ { "quests", "Active Quests" }, { "dungeons", "Available Dungeons" }, { "board", "LFG Board" } }) do
        local key = entry[1]
        tabButtons[key] = Button(frame, entry[2], 190, 22 + (i - 1) * 198, -69, function()
            tab = key
            search:SetText("")
            scroll:SetVerticalScroll(0)
            A.Refresh(true)
        end)
    end
    meta = Label(frame, "", 24, -108, "GameFontHighlightSmall")
    search = CreateFrame("EditBox", nil, frame, "InputBoxTemplate,BackdropTemplate")
    Theme.Input(search)
    search:SetSize(250, 22)
    search:SetPoint("TOPRIGHT", -38, -102)
    search:SetAutoFocus(false)
    search:SetMaxLetters(80)
    search:SetScript("OnTextChanged", function() A.RefreshList() end)
    search:SetScript("OnEscapePressed", search.ClearFocus)
    search:SetScript("OnEnterPressed", search.ClearFocus)
    search:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        GameTooltip:SetText("Filter by name, zone or dungeon abbreviation.")
        GameTooltip:Show()
    end)
    search:SetScript("OnLeave", function() GameTooltip:Hide() end)
    Label(frame, "Filter", 427, -108, "GameFontHighlightSmall")
    scroll = CreateFrame("ScrollFrame", nil, frame, "UIPanelScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", 23, -139)
    scroll:SetSize(711, 225)
    content = CreateFrame("Frame", nil, scroll)
    content:SetSize(711, 225)
    scroll:SetScrollChild(content)
    frame.empty = Label(frame, "", 40, -213, "GameFontDisable")
    frame.empty:SetWidth(690)
    frame.empty:SetJustifyH("CENTER")
    Button(frame, "Clear selection", 148, 22, -379, function()
        wipe(A.db.selected)
        SetStatus("")
        A.RefreshList()
        RefreshComposer()
    end)
    selectedCount = Label(frame, "", 185, -385, "GameFontHighlightSmall")
    frame.onlySelected = CreateFrame("CheckButton", nil, frame, "UICheckButtonTemplate")
    frame.onlySelected:SetPoint("TOPLEFT", 22, -119)
    frame.onlySelected:SetSize(22, 22)
    Label(frame.onlySelected, "Selected activities only", 24, -5, "GameFontHighlightSmall")
    frame.onlySelected:SetScript("OnClick", function(self) A.db.selectedOnly = self:GetChecked() or nil; A.RefreshList() end)

    Label(frame, "Announcement preview · Automatic", 23, -425)
    resetTextButton=Button(frame,"Reset text",115,255,-417,function()
        A.ResetAnnouncementText();SetStatus("");RefreshComposer()
    end)
    resetTextButton:SetScript("OnEnter",function(self)
        GameTooltip:SetOwner(self,"ANCHOR_TOP")
        GameTooltip:SetText("Reset custom message")
        GameTooltip:AddLine("Restores the default whisper instructions. Activities, quest slots and missing roles always update automatically.",1,1,1,true)
        GameTooltip:Show()
    end)
    resetTextButton:SetScript("OnLeave",function() GameTooltip:Hide() end)
    Label(frame, "LFM · Find members", 24, -457, "GameFontHighlightSmall")
    Button(frame, "Group roles", 168, 198, -449, OpenGroupRoles)
    frame.roleLabel = Label(frame, "Your role", 395, -429, "GameFontHighlightSmall")
    for i, role in ipairs({ "Tank", "Healer", "DPS" }) do
        local check = CreateFrame("CheckButton", nil, frame, "UICheckButtonTemplate")
        check:SetSize(26, 26)
        check:SetPoint("TOPLEFT", 390 + (i - 1) * 104, -450)
        Label(check, role, 27, -7, "GameFontHighlightSmall")
        check:SetScript("OnClick", function(self) A.SetPlayerRole(self:GetChecked() and role or nil); SetStatus(""); RefreshComposer() end)
        roleButtons[role] = check
    end
    Label(frame, "Channel", 24, -488, "GameFontHighlightSmall")
    channelMenu = CreateFrame("Frame", "ElmoLFGChannelMenu", frame, "UIDropDownMenuTemplate")
    channelMenu:SetPoint("TOPLEFT", 5, -503)
    UIDropDownMenu_SetWidth(channelMenu, 202)
    UIDropDownMenu_Initialize(channelMenu, function()
        for _, option in ipairs(A.ChannelOptions()) do
            local info = UIDropDownMenu_CreateInfo()
            info.text, info.checked = option.label, option.key == A.db.channel
            info.func = function() A.db.channel = option.key; SetStatus(""); RefreshComposer() end
            UIDropDownMenu_AddButton(info)
        end
    end)
    Button(frame, "Join LFG", 110, 243, -505, function()
        A.waitForLFG = true
        JoinChannelByName("LookingForGroup")
        SelectDefaultChannel()
        SetStatus("Requested to join LookingForGroup.")
        RefreshComposer()
    end)
    customMessageLabel = Label(frame, "Custom message (optional)", 379, -488, "GameFontHighlightSmall")
    note = CreateFrame("EditBox", "ElmoLFGCustomMessage", frame, "InputBoxTemplate,BackdropTemplate")
    Theme.Input(note)
    note:SetSize(355, 24)
    note:SetPoint("TOPLEFT", 382, -506)
    note:SetAutoFocus(false)
    note:SetMaxLetters(255)
    note:SetText(A.GetAnnouncementText())
    note:SetScript("OnTextChanged", function(self)
        if updatingCustomMessage then return end
        A.SetAnnouncementText(self:GetText())
        SetStatus("")
        RefreshComposer()
    end)
    note:SetScript("OnEscapePressed", note.ClearFocus)
    note:SetScript("OnEnterPressed", note.ClearFocus)
    local previewPanel = CreateFrame("Frame", "ElmoLFGAnnouncementPreview", frame, "BackdropTemplate")
    previewPanel:SetPoint("TOPLEFT", 24, -546)
    previewPanel:SetSize(710, 51)
    Theme.Panel(previewPanel, { 0.025, 0.025, 0.025 }, { 0.30, 0.24, 0.11 })
    preview = Label(previewPanel, "", 8, -6, "GameFontHighlightSmall")
    preview:SetSize(694, 39)
    preview:SetJustifyH("LEFT")
    preview:SetJustifyV("TOP")
    preview:SetWordWrap(true)
    previewPanel.text = preview
    Label(frame, "Interval", 24, -617, "GameFontHighlightSmall")
    intervalInput = CreateFrame("EditBox", nil, frame, "InputBoxTemplate,BackdropTemplate")
    Theme.Input(intervalInput)
    intervalInput:SetSize(56, 24)
    intervalInput:SetPoint("TOPLEFT", 82, -611)
    intervalInput:SetAutoFocus(false)
    intervalInput:SetNumeric(true)
    intervalInput:SetMaxLetters(3)
    intervalInput:SetText(tostring(A.db.announcementInterval))
    local function ApplyInterval()
        local seconds = intervalInput:GetNumber()
        if seconds == A.db.announcementInterval then return true end
        local ok, err = A.SetAnnouncementInterval(seconds)
        if not ok then intervalInput:SetText(tostring(A.db.announcementInterval)) end
        SetStatus(err, not ok)
        RefreshComposer()
        RefreshAnnouncerPrompt()
        return ok
    end
    intervalInput:SetScript("OnEnterPressed", function(self) ApplyInterval(); self:ClearFocus() end)
    intervalInput:SetScript("OnEditFocusLost", ApplyInterval)
    intervalInput:SetScript("OnEscapePressed", function(self)
        self:SetText(tostring(A.db.announcementInterval))
        self:ClearFocus()
    end)
    Label(frame, "s (30–300)", 148, -617, "GameFontHighlightSmall")
    Label(frame, "Stop at", 234, -617, "GameFontHighlightSmall")
    targetInput = CreateFrame("EditBox", nil, frame, "InputBoxTemplate,BackdropTemplate")
    Theme.Input(targetInput)
    targetInput:SetSize(48, 24)
    targetInput:SetPoint("TOPLEFT", 290, -611)
    targetInput:SetAutoFocus(false)
    targetInput:SetNumeric(true)
    targetInput:SetMaxLetters(2)
    targetInput:SetText(tostring(A.db.stopAtPlayers))
    local function ApplyTarget()
        local players = targetInput:GetNumber()
        if players == A.db.stopAtPlayers then return true end
        local ok, result = A.SetPlayerTarget(players)
        if not ok then targetInput:SetText(tostring(A.db.stopAtPlayers)) end
        SetStatus(result, not ok)
        RefreshComposer()
        RefreshAnnouncerPrompt()
        return ok
    end
    targetInput:SetScript("OnEnterPressed", function(self) ApplyTarget(); self:ClearFocus() end)
    targetInput:SetScript("OnEditFocusLost", ApplyTarget)
    targetInput:SetScript("OnEscapePressed", function(self)
        self:SetText(tostring(A.db.stopAtPlayers))
        self:ClearFocus()
    end)
    targetInput:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        GameTooltip:SetText("Stop at this group size")
        GameTooltip:AddLine("Includes your character. Announcements and auto-invites stop when this many players have joined.", 1, 1, 1, true)
        GameTooltip:AddLine("Quest groups: 2–40 players; above 5 requires a raid. Dungeon recruitment stops at 5.", 1, 0.82, 0, true)
        GameTooltip:Show()
    end)
    targetInput:SetScript("OnLeave", function() GameTooltip:Hide() end)
    Label(frame, "players", 348, -617, "GameFontHighlightSmall")
    autoStatus = Label(frame, "", 430, -614, "GameFontHighlightSmall")
    autoStatus:SetWidth(302)
    autoStatus:SetJustifyH("LEFT")
    frame.autoJoin = CreateFrame("CheckButton", "ElmoLFGAutojoin", frame, "UICheckButtonTemplate")
    frame.autoJoin:SetSize(26, 26)
    frame.autoJoin:SetPoint("TOPLEFT", 24, -640)
    Label(frame.autoJoin, "Autojoin", 27, -7, "GameFontHighlightSmall")
    frame.autoJoin:SetScript("OnClick", function(self)
        A.db.autoJoin = self:GetChecked() == true
        SetStatus(A.db.autoJoin and "Autojoin enabled while announcing." or "Autojoin disabled.")
        RefreshComposer()
        RefreshAnnouncerPrompt()
    end)
    frame.autoJoin:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        GameTooltip:SetText("Autojoin")
        GameTooltip:AddLine("Automatically invite players who whisper inv while announcing.", 1, 1, 1, true)
        GameTooltip:AddLine("Dungeon requests also need an available role: tank, heal or dps.", .8, .8, .8, true)
        GameTooltip:Show()
    end)
    frame.autoJoin:SetScript("OnLeave", function() GameTooltip:Hide() end)
    status = Label(frame, "", 150, -645, "GameFontHighlightSmall")
    status:SetWidth(584)
    status:SetJustifyH("LEFT")
    startButton = Button(frame, "Start announcing", 168, 22, -683, function()
        if not ApplyInterval() or not ApplyTarget() then return end
        intervalInput:ClearFocus()
        targetInput:ClearFocus()
        local ok, result = A.StartAnnouncing()
        ShowAnnouncementResult(ok, result)
    end)
    Theme.Accent(startButton)
    startButton:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        GameTooltip:SetText("Start announcing")
        GameTooltip:AddLine("Post now, then repeat at the interval you entered (30–300 seconds).", 1, 1, 1, true)
        GameTooltip:AddLine("Public channels need a click for each repeated post. A Post announce button appears when ready.", 1, 0.82, 0, true)
        GameTooltip:AddLine(A.db.autoJoin and "Quests: whisper inv. Dungeons: inv tank, inv heal or inv dps, for an open role."
            or "Autojoin is off. Invite players manually.", 0.6, 0.85, 1, true)
        GameTooltip:Show()
    end)
    startButton:SetScript("OnLeave", function() GameTooltip:Hide() end)
    stopButton = Button(frame, "Stop announcing", 168, 198, -683, StopAnnouncing)
    frame.editButton = Button(frame, "Edit in chat", 155, 407, -683, function()
        local ok, result = A.EditAnnouncement()
        SetStatus(result, not ok)
    end)
    sendButton = Button(frame, "Post announce", 172, 570, -683, PostAnnouncement)
    Theme.Accent(sendButton)
    frame:SetScript("OnShow", function() SetStatus(""); A.Refresh(true); RefreshAnnouncerPrompt() end)
    frame:SetScript("OnHide", function()
        note:ClearFocus()
        search:ClearFocus()
        intervalInput:ClearFocus()
        targetInput:ClearFocus()
        GameTooltip:Hide()
        if groupRolesFrame then groupRolesFrame:Hide() end
        RefreshAnnouncerPrompt()
    end)
    frame:SetScript("OnUpdate", function(_, delta)
        elapsed = elapsed + delta
        if elapsed >= 1 then
            elapsed = 0
            RefreshComposer()
            if tab == "board" then A.RefreshList() end
        end
    end)
    frame:Hide()

    announcerPrompt = CreateFrame("Frame", "ElmoLFGAnnouncementPrompt", UIParent, "BackdropTemplate")
    announcerPrompt:SetSize(420, 140)
    announcerPrompt:SetScale(frame:GetScale())
    announcerPrompt:SetPoint("BOTTOM", UIParent, "BOTTOM", 0, 180)
    announcerPrompt:SetFrameStrata("DIALOG")
    announcerPrompt:SetClampedToScreen(true)
    Theme.Panel(announcerPrompt)
    Label(announcerPrompt, "ElmoLFG · Announcement ready", 18, -18)
    announcerPrompt.detail = Label(announcerPrompt, "", 18, -43, "GameFontHighlightSmall")
    announcerPrompt.detail:SetWidth(384)
    announcerPrompt.detail:SetJustifyH("LEFT")
    local post = Button(announcerPrompt, "Post announce", 184, 18, -96, PostAnnouncement)
    Theme.Accent(post)
    post:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        local message = A.BuildMessage()
        GameTooltip:AddLine(message, 1, 1, 1, true)
        GameTooltip:Show()
    end)
    post:SetScript("OnLeave", function() GameTooltip:Hide() end)
    Button(announcerPrompt, "Stop announcing", 184, 218, -96, StopAnnouncing)
    announcerPrompt:Hide()
end

local function CreateMinimapButton()
    local broker = LibStub("LibDataBroker-1.1"):NewDataObject("ElmoLFG", {
        type = "launcher",
        text = "ElmoLFG",
        icon = "Interface\\Icons\\INV_Misc_GroupNeedMore",
        OnClick = function() A.Toggle() end,
        OnTooltipShow = function(tooltip)
            tooltip:AddLine("ElmoLFG")
            tooltip:AddLine("Active quests, dungeons and the LFG board.", 1, 1, 1)
            tooltip:AddLine("Click to open · /elmolfg", 0.6, 0.85, 1)
            tooltip:AddLine("Drag to move around the minimap.", 0.6, 0.85, 1)
        end,
    })
    LibStub("LibDBIcon-1.0"):Register("ElmoLFG", broker, A.db.minimap)
end

function A.Toggle()
    frame:SetShown(not frame:IsShown())
end

function A.Show()
    frame:Show()
end

local function RegisterOptions()
    if A.optionsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p=CreateFrame("Frame",nil,UIParent);A.optionsPanel=p;p:Hide()
    Label(p,"ElmoLFG",16,-16,"GameFontNormalLarge")
    local description=Label(p,"Active quests, dungeons, channels, roles and recruitment settings.",16,-48,"GameFontHighlight")
    description:SetWidth(530);description:SetJustifyH("LEFT")
    p.autoJoin=CreateFrame("CheckButton",nil,p,"UICheckButtonTemplate")
    p.autoJoin:SetPoint("TOPLEFT",16,-80);p.autoJoin:SetSize(26,26)
    Label(p.autoJoin,"Autojoin while announcing",30,-7,"GameFontHighlight")
    p.autoJoin:SetScript("OnClick",function(self)
        A.db.autoJoin=self:GetChecked()==true;RefreshComposer();RefreshAnnouncerPrompt()
    end)
    p.open=Button(p,"Open complete LFG settings",280,16,-130,function()
        if SettingsPanel and HideUIPanel then HideUIPanel(SettingsPanel) end
        A.Show()
    end)
    local help=Label(p,"Choose activities, announcement channels and text, interval, group size and roles in the LFG window. Opening it does not start recruitment.",16,-178,"GameFontHighlightSmall")
    help:SetWidth(530);help:SetJustifyH("LEFT")
    p:SetScript("OnShow",function()p.autoJoin:SetChecked(A.db.autoJoin)end)
    A.optionsCategory=Settings.RegisterCanvasLayoutCategory(p,"ElmoLFG")
    Settings.RegisterAddOnCategory(A.optionsCategory)
end

local events = CreateFrame("Frame")
events:RegisterEvent("ADDON_LOADED")
events:SetScript("OnEvent", function(_, event, ...)
    if event == "ADDON_LOADED" then
        if ... ~= addonName then return end
        A.InitializeDB()
        CreateWindow()
        CreateMinimapButton()
        RegisterOptions()
        for _, name in ipairs({ "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "QUEST_LOG_UPDATE", "QUEST_ACCEPTED", "QUEST_REMOVED", "QUEST_TURNED_IN", "QUEST_AUTOCOMPLETE", "QUEST_DATA_LOAD_RESULT", "PLAYER_LEVEL_UP", "CHANNEL_UI_UPDATE", "GROUP_ROSTER_UPDATE", "PLAYER_GUILD_UPDATE", "CHAT_MSG_CHANNEL", "CHAT_MSG_SAY", "CHAT_MSG_YELL", "CHAT_MSG_GUILD", "CHAT_MSG_WHISPER" }) do events:RegisterEvent(name) end
        pcall(events.RegisterEvent, events, "PLAYER_ROLES_ASSIGNED")
        C_Timer.NewTicker(1, function()
            -- Quest data can finish loading after the final log event.
            if frame:IsShown() or not A.questReady then A.Refresh(false) end
            local ok, result = A.TickAnnouncing()
            if ok ~= nil then ShowAnnouncementResult(ok, result) end
        end)
        SLASH_ELMOLFG1, SLASH_ELMOLFG2 = "/elmolfg", "/elfg"
        SlashCmdList.ELMOLFG = function(command)
            if command:lower() == "diag" then
                A.Refresh(true)
                local _, build, _, interface = GetBuildInfo()
                local version = (C_AddOns and C_AddOns.GetAddOnMetadata and C_AddOns.GetAddOnMetadata(addonName, "Version")) or "1.4.4"
                print("ElmoLFG " .. version .. " · build " .. build .. " · interface " .. interface .. " · " .. #A.quests .. " quests · " .. #A.AvailableDungeons() .. "/" .. #A.dungeons .. " dungeons")
            else A.Toggle() end
        end
        print("|cffffd100ElmoLFG|r ready. Open with |cff80c0ff/elmolfg|r or the minimap button.")
        if IsLoggedIn() then A.Refresh(true) end
        return
    end
    if event == "CHAT_MSG_WHISPER" then
        local message, sender = ...
        local ok, result = A.HandleWhisper(message, sender)
        if ok ~= nil then
            SetStatus(result, not ok)
            if not frame:IsShown() then print("|cffffd100ElmoLFG|r " .. result) end
        end
        RefreshComposer()
        return
    end
    if event == "GROUP_ROSTER_UPDATE" then
        A.SyncGroupRoles()
        local stopped, result = A.CheckGroupTarget()
        if stopped then ShowAnnouncementResult(true, result) end
    end
    if event:sub(1, 9) == "CHAT_MSG_" then
        local message, sender, _, channel, _, _, _, number, name = ...
        A.ReceiveMessage(message, sender, name or channel or event:sub(10))
        if frame:IsShown() and tab == "board" then A.RefreshList() end
        return
    end
    if refreshPending then return end
    refreshPending = true
    C_Timer.After(0.15, function()
        refreshPending = false
        A.Refresh(event ~= "QUEST_LOG_UPDATE")
    end)
end)
