local _, A = ...
local S = {}
A.Settings = S

function S.Register()
    if S.panel then return end
    local panel = CreateFrame("Frame", nil, UIParent)
    S.panel = panel; panel:Hide()
    local function label(text, y)
        local f = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        f:SetPoint("TOPLEFT", 16, y); f:SetWidth(540); f:SetJustifyH("LEFT"); f:SetText(text)
        return f
    end
    label("ElmoLFM", -16)
    label("Find online players by zone and level. Select candidates and send them your whisper message.", -52)
    local open = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    open:SetPoint("TOPLEFT", 16, -104); open:SetSize(220, 28); open:SetText("Open recruitment window")
    open:SetScript("OnClick", function()
        if SettingsPanel and HideUIPanel then HideUIPanel(SettingsPanel) end
        A.UI.Open()
    end)
    local auto = CreateFrame("CheckButton", nil, panel, "UICheckButtonTemplate")
    auto:SetPoint("TOPLEFT", 16, -150); auto:SetSize(26, 26)
    local caption = auto:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    caption:SetPoint("LEFT", auto, "RIGHT", 4, 0); caption:SetText("Auto-invite contacted players who reply inv")
    auto:SetScript("OnClick", function(self) A.SetAutoInvite(self:GetChecked()) end)
    local stop = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    local minimap = CreateFrame("CheckButton", nil, panel, "UICheckButtonTemplate")
    minimap:SetPoint("TOPLEFT", 16, -194); minimap:SetSize(26, 26)
    local minimapCaption = minimap:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    minimapCaption:SetPoint("LEFT", minimap, "RIGHT", 4, 0); minimapCaption:SetText("Show minimap button")
    minimap:SetScript("OnClick", function(self) A.Minimap.SetVisible(self:GetChecked()) end)
    stop:SetPoint("TOPLEFT", 16, -250); stop:SetSize(220, 28); stop:SetText("Stop recruitment")
    stop:SetScript("OnClick", A.Stop)
    local center = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    center:SetPoint("TOPLEFT", 252, -250); center:SetSize(180, 28); center:SetText("Center window")
    center:SetScript("OnClick", A.UI.Center)
    label("Prepare /who fills chat; press Enter to run it. Native WHO updates fill the open window. Import WHO list reads cached results without another search. Replies allow auto-invites for 10 minutes.", -306)
    label("Closing the window leaves the current recruitment running. Use Stop recruitment or /elfm stop to end whispers and reply invitations.", -380)
    label("The list mirrors Blizzard WHO, including other zones. Zone/level fields prepare the query. Focus Whisper message and Shift-click a quest to insert its link.", -450)
    panel:SetScript("OnShow", function()
        auto:SetChecked(A.db.autoInvite); minimap:SetChecked(not A.db.minimap.hide)
    end)
    if Settings and Settings.RegisterCanvasLayoutCategory then
        S.category = Settings.RegisterCanvasLayoutCategory(panel, "ElmoLFM")
        Settings.RegisterAddOnCategory(S.category)
    elseif InterfaceOptions_AddCategory then
        panel.name = "ElmoLFM"; InterfaceOptions_AddCategory(panel)
    end
end
function S.Open()
    if S.category and Settings and Settings.OpenToCategory then Settings.OpenToCategory(S.category:GetID())
    elseif InterfaceOptionsFrame_OpenToCategory then InterfaceOptionsFrame_OpenToCategory(S.panel) end
end
