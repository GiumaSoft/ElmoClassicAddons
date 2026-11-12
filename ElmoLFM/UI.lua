local _, A = ...
local U, Theme = {}, A.Theme
A.UI = U
local frame, scroll, content
local rows = {}

local function label(parent, text, x, y, width, font)
    local f = parent:CreateFontString(nil, "OVERLAY", font or "GameFontHighlightSmall")
    f:SetPoint("TOPLEFT", x, y); f:SetWidth(width); f:SetJustifyH("LEFT"); f:SetText(text)
    return f
end
local function input(parent, x, y, width, numeric)
    local f = CreateFrame("EditBox", nil, parent, "InputBoxTemplate,BackdropTemplate")
    f:SetPoint("TOPLEFT", x, y); f:SetSize(width, 26); f:SetAutoFocus(false)
    f:SetNumeric(numeric == true); f:SetMaxLetters(numeric and 2 or 120)
    Theme.Input(f)
    f:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
    return f
end
local function filtersMatch()
    local query = A.Query(frame.zone:GetText(), frame.minimum:GetText(), frame.maximum:GetText())
    return query and query == A.query
end
local function selectPlayer(row)
    if row.player and A.Contactable(row.player) and not A.queue and not A.search then
        A.selected[row.player.key] = not A.selected[row.player.key] or nil
        U.Refresh()
    end
end
local function getRow(index)
    if rows[index] then return rows[index] end
    local row = CreateFrame("Button", nil, content, "BackdropTemplate")
    row:SetSize(702, 32); row:SetPoint("TOPLEFT", 0, -(index - 1) * 34)
    row.check = CreateFrame("CheckButton", nil, row, "UICheckButtonTemplate")
    row.check:SetSize(24, 24); row.check:SetPoint("LEFT", 2, 0)
    row.name = label(row, "", 34, -9, 172)
    row.level = label(row, "", 216, -9, 32)
    row.class = label(row, "", 258, -9, 86)
    row.zone = label(row, "", 354, -9, 142)
    row.sent = row:CreateTexture(nil, "ARTWORK")
    row.sent:SetSize(20, 20); row.sent:SetPoint("TOPLEFT", 507, -6)
    row.sent:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    row.sent:SetVertexColor(.35, 1, .4, 1)
    row.reply = label(row, "", 540, -9, 154)
    for _, f in ipairs({row.name, row.level, row.class, row.zone, row.reply}) do f:SetWordWrap(false) end
    row:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    row:SetScript("OnClick", function(self, button)
        if button == "RightButton" then
            if self.player then A.InvitePlayer(self.player.name) end
        elseif button == "LeftButton" then selectPlayer(self) end
    end)
    row.check:SetScript("OnClick", function() selectPlayer(row) end)
    local function tooltip()
        local p = row.player
        if not p then return end
        GameTooltip:SetOwner(row, "ANCHOR_RIGHT"); GameTooltip:SetText(p.name, 1, .82, 0)
        GameTooltip:AddLine("Level " .. p.level .. " " .. p.class, 1, 1, 1)
        GameTooltip:AddLine(p.area, .8, .8, .8)
        if p.guild and p.guild ~= "" then GameTooltip:AddLine(p.guild, .6, .85, 1) end
        local contact = A.contacts[p.key]
        if contact then
            GameTooltip:AddLine(contact.state, .75, .75, .75)
            if contact.reply then
                GameTooltip:AddLine("Latest reply:", 1, .82, 0)
                GameTooltip:AddLine(contact.reply, .65, .85, 1, true)
            end
        elseif A.IsMember(p.name) then GameTooltip:AddLine("In your group", .75, .75, .75)
        elseif A.invites[p.key] and GetTime() < A.invites[p.key].expires then
            GameTooltip:AddLine("Invite requested", .75, .75, .75)
        end
        GameTooltip:AddLine("Left-click: select. Right-click: invite to your group.", 1, .82, 0, true)
        GameTooltip:AddLine("Online in WHO results; group availability is confirmed by reply.", .75, .75, .75, true)
        GameTooltip:Show()
    end
    row:SetScript("OnEnter", tooltip); row.check:SetScript("OnEnter", tooltip)
    row:SetScript("OnLeave", function() GameTooltip:Hide() end)
    row.check:SetScript("OnLeave", function() GameTooltip:Hide() end)
    rows[index] = row
    return row
end

function U.Refresh()
    if not frame or not frame:IsShown() then return end
    local query, queryError = A.Query(frame.zone:GetText(), frame.minimum:GetText(), frame.maximum:GetText())
    frame.query:SetText(query and ("/who " .. query) or queryError)
    frame.query:SetTextColor(query and .75 or 1, query and .75 or .35, query and .75 or .35)
    local selected, tickets = 0, 0
    for key, ticket in pairs(A.tickets) do
        local invite = A.invites[key]
        if GetTime() < ticket.expires and not A.IsMember(ticket.name) and
            not (A.contacts[key] and A.contacts[key].reply) and (not invite or GetTime() >= invite.expires) then
            tickets = tickets + 1
        end
    end
    for index, player in ipairs(A.results) do
        local row = getRow(index)
        row.player = player
        local available = A.Contactable(player)
        if not available then A.selected[player.key] = nil end
        local checked = A.selected[player.key] == true
        if checked then selected = selected + 1 end
        Theme.Panel(row, checked and {.17, .14, .07} or {.035, .035, .035}, checked and {.86, .66, .14} or {.15, .13, .08})
        row.check:SetChecked(checked); row.check:SetEnabled(available and not A.queue and not A.search)
        row.name:SetText(player.name); row.name:SetTextColor(available and 1 or .55, available and .86 or .55, available and .6 or .55)
        row.level:SetText(player.level); row.class:SetText(player.class); row.zone:SetText(player.area)
        row.zone:SetTextColor(.8, .8, .8)
        local color = RAID_CLASS_COLORS and RAID_CLASS_COLORS[player.classFile]
        row.class:SetTextColor(color and color.r or .8, color and color.g or .8, color and color.b or .8)
        local contact = A.contacts[player.key]
        row.sent:SetShown(contact ~= nil and contact.sent == true)
        row.reply:SetText(contact and contact.reply and contact.reply:gsub("[\r\n]", " ") or "")
        row.reply:SetTextColor(.65, .85, 1)
        row:Show()
    end
    for index = #A.results + 1, #rows do rows[index]:Hide() end
    content:SetHeight(math.max(1, #A.results * 34))
    frame.search:SetText(A.search and "Waiting..." or "Prepare /who")
    frame.search:SetEnabled(query ~= nil and not A.search and not A.queue)
    frame.import:SetEnabled(query ~= nil and not A.queue)
    frame.selectAll:SetEnabled(#A.results > 0 and not A.search and not A.queue)
    frame.clear:SetEnabled(selected > 0 and not A.queue)
    frame.autoInvite:SetChecked(A.db.autoInvite)
    local message, err = A.Message()
    frame.preview:SetText(message or err)
    frame.preview:SetTextColor(message and .9 or 1, message and .86 or .35, message and .7 or .35)
    frame.counter:SetText(message and (#message .. "/255 bytes") or "Shorten or complete the message before sending.")
    frame.send:SetText(A.queue and "Sending..." or ("Send selected (" .. selected .. ")"))
    frame.send:SetEnabled(not not (selected > 0 and message ~= nil and filtersMatch() and A.resultsAt ~= nil and
        GetTime() - A.resultsAt < 300 and not A.search and not A.queue))
    frame.status:SetText(A.status or "Choose filters, click Prepare /who, then press Enter in chat to run the search.")
    frame.status:SetTextColor(1, A.error and .35 or .86, A.error and .35 or .6)
    frame.summary:SetText(selected .. " selected  ·  " .. #A.results .. " players\n" .. tickets ..
        " awaiting replies  ·  Auto-invite " .. (A.db.autoInvite and "ON" or "OFF"))
end

function U.Center()
    A.db.position = nil
    if frame then frame:ClearAllPoints(); frame:SetPoint("CENTER") end
end
function U.ImportWho()
    if frame then return A.ImportWho(frame.zone:GetText(), frame.minimum:GetText(), frame.maximum:GetText()) end
    return A.ImportWho(A.db.zone, A.db.minimum, A.db.maximum)
end
function U.Create()
    if frame then return end
    frame = CreateFrame("Frame", "ElmoLFMFrame", UIParent, "BackdropTemplate")
    U.frame = frame
    frame:Hide()
    frame:SetSize(760, 716); frame:SetClampedToScreen(true); frame:SetFrameStrata("DIALOG")
    local p = A.db.position
    if type(p) == "table" and A.Text(p.point) and A.Number(p.x) and A.Number(p.y) then
        frame:SetPoint(p.point, UIParent, p.point, p.x, p.y)
    else frame:SetPoint("CENTER") end
    Theme.Panel(frame)
    Theme.Inset(frame, 8, -8, 744, 54)
    Theme.Inset(frame, 12, -186, 736, 234)
    Theme.Inset(frame, 12, -486, 736, 163)
    frame:SetMovable(true); frame:EnableMouse(true); frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", function(self) self:StartMoving() end)
    frame:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local point, _, _, x, y = self:GetPoint()
        A.db.position = {point = point, x = x, y = y}
    end)
    label(frame, "ElmoLFM", 18, -16, 600, "GameFontNormalLarge")
    label(frame, "Local recruitment  ·  Search, select and whisper", 18, -42, 660)
    Theme.Button(frame, "X", 26, 716, -16, function() frame:Hide() end)
    label(frame, "Zone", 18, -76, 330)
    label(frame, "Min level", 490, -76, 62)
    label(frame, "Max level", 564, -76, 62)
    frame.zone, frame.minimum, frame.maximum = input(frame, 18, -98, 326), input(frame, 490, -98, 62, true), input(frame, 564, -98, 62, true)
    frame.zone:SetText(A.db.zone); frame.minimum:SetText(A.db.minimum); frame.maximum:SetText(A.db.maximum)
    Theme.Button(frame, "My zone", 118, 356, -98, function()
        frame.zone:SetText(A.Text(A.Call(GetRealZoneText or GetZoneText)) or "")
    end)
    local function search()
        for _, f in ipairs({frame.zone, frame.minimum, frame.maximum}) do f:ClearFocus() end
        A.Search(frame.zone:GetText(), frame.minimum:GetText(), frame.maximum:GetText())
    end
    frame.search = Theme.Button(frame, "Prepare /who", 102, 638, -98, search); Theme.Accent(frame.search)
    frame.query = input(frame, 18, -132, 722)
    frame.query:SetHeight(20); frame.query:SetMaxLetters(260)
    frame.query:SetScript("OnEditFocusGained", function(self) self:HighlightText() end)
    label(frame, "Select players · Right-click to invite", 18, -162, 360, "GameFontNormal")
    frame.import = Theme.Button(frame, "Import WHO list", 142, 390, -156, U.ImportWho)
    frame.selectAll = Theme.Button(frame, "Select all", 94, 542, -156, function()
        for _, player in ipairs(A.results) do if A.Contactable(player) then A.selected[player.key] = true end end
        U.Refresh()
    end)
    frame.clear = Theme.Button(frame, "Clear", 94, 646, -156, function() A.selected = {}; U.Refresh() end)
    label(frame, "Player", 52, -195, 172); label(frame, "Level", 234, -195, 32)
    label(frame, "Class", 276, -195, 86); label(frame, "Zone", 372, -195, 142)
    label(frame, "Sent", 518, -195, 34); label(frame, "Last reply", 558, -195, 154)
    scroll = CreateFrame("ScrollFrame", nil, frame, "UIPanelScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", 18, -214); scroll:SetSize(702, 200)
    content = CreateFrame("Frame", nil, scroll); content:SetSize(702, 1); scroll:SetScrollChild(content)
    frame.status = label(frame, "", 18, -430, 722); frame.status:SetHeight(36)
    label(frame, "Online matches; availability to join is confirmed by reply.", 18, -468, 722)
    label(frame, "Whisper message", 18, -497, 260, "GameFontNormal")
    frame.autoInvite = CreateFrame("CheckButton", nil, frame, "UICheckButtonTemplate")
    frame.autoInvite:SetSize(26, 26); frame.autoInvite:SetPoint("TOPLEFT", 374, -489)
    label(frame.autoInvite, "Auto-invite replies starting with inv", 30, -8, 330)
    frame.autoInvite:SetScript("OnClick", function(self) A.SetAutoInvite(self:GetChecked()) end)
    frame.message = input(frame, 18, -521, 722)
    frame.message:SetHeight(58); frame.message:SetMultiLine(true); frame.message:SetMaxLetters(255)
    frame.message:SetTextInsets(8, 8, 7, 7); frame.message:SetText(A.db.message)
    frame.message:SetScript("OnTextChanged", function(self) A.db.message = self:GetText(); U.Refresh() end)
    A.Links.Register(frame.message)
    frame.preview = label(frame, "", 18, -588, 722); frame.preview:SetHeight(44)
    frame.counter = label(frame, "", 18, -637, 722)
    frame.send = Theme.Button(frame, "Send selected", 176, 18, -670, function()
        frame.message:ClearFocus()
        if not filtersMatch() then A.Status("Search with these filters before sending.", true); return end
        A.SendSelected()
    end)
    Theme.Accent(frame.send)
    Theme.Button(frame, "Stop recruitment", 176, 206, -670, A.Stop)
    frame.summary = label(frame, "", 402, -665, 338); frame.summary:SetHeight(34)
    for _, edit in ipairs({frame.zone, frame.minimum, frame.maximum}) do
        edit:SetScript("OnTextChanged", U.Refresh); edit:SetScript("OnEnterPressed", search)
    end
    frame:SetScript("OnShow", U.Refresh)
    UISpecialFrames[#UISpecialFrames + 1] = "ElmoLFMFrame"
    U.Refresh()
end
function U.Toggle()
    U.Create()
    frame:SetShown(not frame:IsShown())
end
function U.Open()
    U.Create(); frame:Show(); U.Refresh()
end
