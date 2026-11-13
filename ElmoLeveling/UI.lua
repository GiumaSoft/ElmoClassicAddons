local _, A = ...
local U = {}
A.UI = U
local WHITE = "Interface\\Buttons\\WHITE8X8"
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local WIDTH, EXPANDED_WIDTH, HEIGHT = 332, 408, 164

local function label(parent, size, text)
    local f = parent:CreateFontString(nil, "OVERLAY")
    f:SetFont(FONT, size, ""); f:SetTextColor(.93, .91, .84)
    f:SetJustifyH("LEFT"); f:SetText(text or "")
    return f
end
local function panel(kind, name, parent)
    local f = CreateFrame(kind, name, parent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:SetBackdrop({bgFile = WHITE, edgeFile = WHITE, edgeSize = 1})
    f:SetBackdropColor(.025, .025, .025, .94); f:SetBackdropBorderColor(.68, .52, .18, 1)
    return f
end
local function button(parent, text, x, y, width, callback)
    local b = panel("Button", nil, parent)
    b:EnableMouse(true); b:RegisterForClicks("LeftButtonUp")
    b:SetSize(width, 23); b:SetPoint("TOPRIGHT", x, y)
    b.label = label(b, 11, text); b.label:SetPoint("CENTER")
    local highlight = b:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetAllPoints(); highlight:SetColorTexture(1, .82, 0, .12)
    b:SetScript("OnClick", callback)
    return b
end
function U.Number(value)
    local text = string.format("%.0f", math.max(0, value)):reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")
    return text
end
function U.SessionTime(seconds)
    seconds = math.floor(math.max(0, seconds))
    return string.format("%dd %02dh %02dm %02ds", math.floor(seconds / 86400),
        math.floor(seconds / 3600) % 24, math.floor(seconds / 60) % 60, seconds % 60)
end
function U.Clock(seconds)
    seconds = math.floor(math.max(0, seconds))
    local clock = string.format("%02d:%02d:%02d", math.floor(seconds / 3600) % 24, math.floor(seconds / 60) % 60, seconds % 60)
    return (seconds >= 86400 and (math.floor(seconds / 86400) .. "d ") or "") .. clock
end
function U.Money(copper, signed)
    local prefix = signed and (copper > 0 and "+" or copper < 0 and "-" or "") or ""
    copper = math.floor(math.abs(copper))
    return prefix .. "|cffffd100" .. U.Number(math.floor(copper / 10000)) .. "g|r " ..
        "|cffc7c7cf" .. math.floor(copper / 100) % 100 .. "s|r " .. "|cffeda55f" .. copper % 100 .. "c|r"
end
function U.Place()
    local f = U.panel; f:ClearAllPoints()
    if A.db.position then f:SetPoint("TOPLEFT", UIParent, "TOPLEFT", A.db.position.x, A.db.position.y)
    else f:SetPoint("CENTER", UIParent, "CENTER", 0, -130) end
end
function U.ScrollLevels(delta)
    U.levelOffset = math.max(0, math.min(math.max(0, #A.db.levels + 1 - 8), (U.levelOffset or 0) + delta))
    U.RefreshLevels()
end
function U.ToggleLevels() A.db.levelExpanded = not A.db.levelExpanded; U.RefreshLevels() end

function U.RegisterOptions()
    if U.optionsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p = CreateFrame("Frame", nil, UIParent)
    U.optionsPanel = p; p:Hide()
    label(p, 16, "ElmoLeveling"):SetPoint("TOPLEFT", 16, -16)
    label(p, 12, "Elapsed time, earned XP, time per level and equipment upgrades."):SetPoint("TOPLEFT", 16, -48)
    local function check(value, y, change)
        local c = CreateFrame("CheckButton", nil, p, "UICheckButtonTemplate")
        c:SetPoint("TOPLEFT", 16, y); c:SetSize(26, 26)
        label(c, 12, value):SetPoint("LEFT", c, "RIGHT", 4, 0)
        c:SetScript("OnClick", function(self) change(self:GetChecked() == true) end)
        return c
    end
    p.visible = check("Show tracker", -80, A.SetVisible)
    p.locked = check("Lock tracker position", -114, A.SetLocked)
    p.expanded = check("Show time per level", -148, function(value) A.db.levelExpanded = value; U.RefreshLevels() end)
    local function action(value, y, fn)
        local b = CreateFrame("Button", nil, p, "UIPanelButtonTemplate")
        b:SetPoint("TOPLEFT", 16, y); b:SetSize(240, 26); b:SetText(value); b:SetScript("OnClick", fn)
        return b
    end
    p.center = action("Center and show tracker", -196, function() A.Command("center"); p.visible:SetChecked(true) end)
    p.reset = action("Restart session", -234, A.Reset)
    p.clear = action("Clear completed level history", -272, function() A.Levels.ClearHistory(); U.levelOffset = 0; U.RefreshLevels() end)
    label(p, 12, "All online time counts, including idle and out-of-combat time."):SetPoint("TOPLEFT", 16, -324)
    label(p, 12, "Restarting the session preserves time per level and completed levels."):SetPoint("TOPLEFT", 16, -348)
    p:SetScript("OnShow", function()
        p.visible:SetChecked(not A.db.hidden); p.locked:SetChecked(A.db.locked)
        p.expanded:SetChecked(A.db.levelExpanded)
    end)
    U.optionsCategory = Settings.RegisterCanvasLayoutCategory(p, "ElmoLeveling")
    Settings.RegisterAddOnCategory(U.optionsCategory)
end

function U.CreateLevels()
    U.levelOffset, U.levelRows = 0, {}
    U.levelToggle = button(U.panel, "Levels [+]", -10, -3, 100, U.ToggleLevels)
    U.levelToggle:SetFrameLevel(U.anchor:GetFrameLevel() + 1)
    U.levelToggle:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP"); GameTooltip:SetText("Time per level")
        GameTooltip:AddLine("Online time spent advancing from one level to the next, including idle time.", 1, 1, 1, true)
        GameTooltip:AddLine("Click to expand. Times use days, hours, minutes and seconds.", .8, .8, .8, true)
        GameTooltip:AddLine("Partial means time before first observation was unavailable. Past levels cannot be reconstructed.", .8, .8, .8, true)
        GameTooltip:Show()
    end)
    U.levelToggle:SetScript("OnLeave", function() GameTooltip:Hide() end)
    local p = CreateFrame("Frame", nil, U.panel)
    U.levelPanel = p; p:SetSize(EXPANDED_WIDTH, 204); p:SetPoint("TOPLEFT", 0, -HEIGHT - 5)
    local divider = p:CreateTexture(nil, "ARTWORK")
    divider:SetColorTexture(.68, .52, .18, .35); divider:SetPoint("TOPLEFT", 10, 0); divider:SetSize(EXPANDED_WIDTH - 20, 1)
    label(p, 10, "Level"):SetPoint("TOPLEFT", 10, -10)
    label(p, 10, "Time to level"):SetPoint("TOPLEFT", 104, -10)
    local status = label(p, 10, "Status"); status:SetPoint("TOPRIGHT", -10, -10); status:SetJustifyH("RIGHT")
    p:EnableMouseWheel(true); p:SetScript("OnMouseWheel", function(_, delta) U.ScrollLevels(-delta * 3) end)
    for i = 1, 8 do
        local row = CreateFrame("Button", nil, p)
        U.levelRows[i] = row; row:SetSize(EXPANDED_WIDTH - 20, 18); row:SetPoint("TOPLEFT", 10, -26 - (i - 1) * 19)
        local background = row:CreateTexture(nil, "BACKGROUND"); background:SetAllPoints()
        background:SetColorTexture(.45, .36, .18, i % 2 == 0 and .10 or .03)
        row.level = label(row, 11, ""); row.level:SetPoint("LEFT", 0, 0); row.level:SetWidth(88)
        row.duration = label(row, 11, ""); row.duration:SetPoint("LEFT", 94, 0); row.duration:SetWidth(184)
        row.status = label(row, 10, ""); row.status:SetPoint("RIGHT", 0, 0); row.status:SetJustifyH("RIGHT"); row.status:SetWidth(100)
        row:EnableMouseWheel(true); row:SetScript("OnMouseWheel", function(_, delta) U.ScrollLevels(-delta * 3) end)
        row:SetScript("OnEnter", function(self)
            if not self.entry then return end
            GameTooltip:SetOwner(self, "ANCHOR_TOP"); GameTooltip:SetText(self.level:GetText())
            GameTooltip:AddLine(self.status:GetText() .. ": " .. self.duration:GetText(), 1, 1, 1)
            GameTooltip:AddLine(self.entry.complete and "Full observed online time for this level, including idle time." or
                "Only observed time is available; time before tracking began is not invented.", .8, .8, .8, true)
            GameTooltip:Show()
        end)
        row:SetScript("OnLeave", function() GameTooltip:Hide() end)
    end
    U.levelPage = label(p, 9, ""); U.levelPage:SetPoint("TOPLEFT", 10, -185)
    U.levelUp = button(p, "Up", -54, -180, 38, function() U.ScrollLevels(-8) end)
    U.levelDown = button(p, "Down", -10, -180, 38, function() U.ScrollLevels(8) end)
end
function U.RefreshLevels()
    if not U.levelPanel then return end
    local expanded = A.db.levelExpanded
    U.levelToggle.label:SetText(expanded and "Levels [-]" or "Levels [+]")
    U.levelPanel:SetShown(expanded)
    if U.levelExpanded ~= expanded then
        if U.levelExpanded ~= nil or expanded then
            local left, top = U.panel:GetLeft(), U.panel:GetTop()
            U.panel:SetSize(expanded and EXPANDED_WIDTH or WIDTH, expanded and (HEIGHT + 215) or HEIGHT)
            if left and top then
                U.panel:ClearAllPoints(); U.panel:SetPoint("TOPLEFT", UIParent, "TOPLEFT", left - UIParent:GetLeft(), top - UIParent:GetTop())
            end
        end
        U.levelExpanded = expanded
    end
    local state, count = A.db.levelState, #A.db.levels + 1
    U.levelOffset = math.min(U.levelOffset, math.max(0, count - 8))
    for i, row in ipairs(U.levelRows) do
        local index = U.levelOffset + i
        local current = index == 1
        local entry = current and state or A.db.levels[index - 1]
        row.entry = entry; row:SetShown(entry ~= nil)
        if entry then
            local atCap = current and A.last and A.last.maximum == 0
            row.level:SetText(current and (entry.level .. (atCap and "" or (" -> " .. (entry.level + 1)))) or (entry.from .. " -> " .. entry.to))
            local seconds = current and A.Levels.CurrentSeconds() or entry.seconds
            row.duration:SetText(atCap and "--" or (A.IsNumber(seconds) and U.SessionTime(seconds) or "--"))
            row.status:SetText(atCap and "Max level" or (current and (entry.complete and "In progress" or "Partial") or
                (not seconds and "Unavailable" or (entry.complete and "Complete" or "Partial"))))
        end
    end
    U.levelPage:SetText((U.levelOffset + 1) .. "-" .. math.min(count, U.levelOffset + 8) .. " / " .. count .. " (mouse wheel)")
    U.levelUp:SetShown(count > 8); U.levelDown:SetShown(count > 8)
end

function U.Create()
    if U.panel then return end
    local f = panel("Frame", "ElmoLevelingPanel", UIParent)
    U.panel = f; f:SetSize(WIDTH, HEIGHT); f:SetFrameStrata("MEDIUM"); f:SetMovable(true); f:SetClampedToScreen(true); U.Place()
    U.anchor = CreateFrame("Frame", nil, f)
    U.anchor:SetPoint("TOPLEFT", 1, -1); U.anchor:SetSize(WIDTH - 117, 36)
    U.anchor:EnableMouse(true); U.anchor:RegisterForDrag("LeftButton")
    U.anchor:SetScript("OnDragStart", function() if not A.db.locked then f:StartMoving() end end)
    U.anchor:SetScript("OnDragStop", function()
        f:StopMovingOrSizing(); A.db.position = {x = f:GetLeft() - UIParent:GetLeft(), y = f:GetTop() - UIParent:GetTop()}; U.Place()
    end)
    U.anchor:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP"); GameTooltip:SetText("ElmoLeveling")
        GameTooltip:AddLine("Time and XP show actual online time and XP earned since Start/reset.", 1, 1, 1, true)
        GameTooltip:AddLine("All XP sources count. The total does not reset at an hour or day boundary.", .8, .8, .8, true)
        GameTooltip:AddLine("Idle and out-of-combat online time count. Offline time does not.", .8, .8, .8, true)
        GameTooltip:AddLine("The session resumes after reload/login. Restart clears time and XP without clearing level times.", .8, .8, .8, true)
        GameTooltip:AddLine("Bags show vendor sell value. Purple borders retain the class/role upgrade rules.", .8, .8, .8, true)
        GameTooltip:AddLine(A.db.locked and "Click Unlock to move this panel." or "Drag the title to move this panel.", 1, .82, 0, true)
        GameTooltip:Show()
    end)
    U.anchor:SetScript("OnLeave", function() GameTooltip:Hide() end)
    local title = label(U.anchor, 13, "ElmoLeveling"); title:SetPoint("TOPLEFT", 9, -3); title:SetTextColor(1, .82, 0)
    U.character = label(U.anchor, 14, ""); U.character:SetPoint("TOPLEFT", 9, -20); U.character:SetWidth(200); U.character:SetWordWrap(false)
    U.sessionStrip = panel("Frame", nil, f)
    U.sessionStrip:SetPoint("TOPLEFT", 10, -48); U.sessionStrip:SetPoint("TOPRIGHT", -10, -48)
    U.sessionStrip:SetHeight(34); U.sessionStrip:SetBackdropColor(.055, .045, .065, .9)
    U.sessionStrip:SetBackdropBorderColor(.34, .28, .14, .75); U.sessionStrip:EnableMouse(false)
    U.summary = label(U.sessionStrip, 13, "")
    U.summary:SetPoint("TOPLEFT", 8, 0); U.summary:SetPoint("BOTTOMRIGHT", -8, 0)
    U.summary:SetJustifyH("CENTER"); U.summary:SetWordWrap(false)
    local divider = f:CreateTexture(nil, "ARTWORK")
    divider:SetColorTexture(.68, .52, .18, .35); divider:SetPoint("TOPLEFT", 10, -94); divider:SetSize(WIDTH - 20, 1)
    label(f, 11, "Bags (sell value):"):SetPoint("TOPLEFT", 10, -107)
    U.bagValue = label(f, 15, "Loading..."); U.bagValue:SetPoint("TOPRIGHT", -10, -103); U.bagValue:SetWidth(186); U.bagValue:SetJustifyH("RIGHT")
    U.bagStatus = label(f, 9, ""); U.bagStatus:SetPoint("TOPLEFT", 10, -144); U.bagStatus:SetWidth(158)
    U.lock = button(f, "Lock", -88, -136, 69, function() A.SetLocked(not A.db.locked) end)
    U.reset = button(f, "Restart", -12, -136, 69, A.Reset)
    U.CreateLevels()
end
function U.Update()
    if not U.panel then return end
    local level = UnitLevel("player")
    U.character:SetText((A.Text(UnitName("player")) or "Player") .. " lv. " .. math.max(A.IsNumber(level) and level or 0, A.expectedLevel or 0))
    local stats = A.Stats()
    U.summary:SetText("|cffaaa59bTime|r |cffffd100" .. U.Clock(stats.elapsed) ..
        "|r  |cff806b3c·|r  |cffaaa59bXP|r |cffb77aff" .. (A.db.xpGap and "--" or ("+" .. U.Number(stats.totalXP))) .. "|r")
    local bags = A.Bags.state
    if bags then
        U.bagValue:SetText((bags.pending > 0 and ">= " or "") .. U.Money(bags.value))
        U.bagStatus:SetText(bags.pending > 0 and ("Loading: " .. bags.pending) or (bags.stacks .. " stacks / " .. U.Number(bags.items)))
    end
    U.lock.label:SetText(A.db.locked and "Unlock" or "Lock")
    U.panel:SetShown(not A.db.hidden)
    U.RefreshLevels()
end
