local _, A = ...
local S = {}
A.Settings = S

local function label(parent, text, y, size)
    local t = parent:CreateFontString(nil, "OVERLAY")
    t:SetFont(STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF", size or 12, "")
    t:SetPoint("TOPLEFT", 16, y); t:SetWidth(530); t:SetJustifyH("LEFT"); t:SetText(text)
    return t
end

function S.Register()
    if S.category or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p = CreateFrame("Frame", nil, UIParent); p:Hide(); S.panel = p
    label(p, "ElmoRare", -16, 16)
    label(p, "Rare alerts from nearby nameplates, your target and mouseover.", -52)
    for i, option in ipairs({{"enabled", "Enable rare detection"}, {"sound", "Play alert sound"},
        {"popup", "Show rare alert with hover tooltip"}}) do
        local key = option[1]
        local b = CreateFrame("CheckButton", nil, p, "UICheckButtonTemplate")
        p[key] = b; b:SetSize(26, 26); b:SetPoint("TOPLEFT", 16, -84 - (i - 1) * 42)
        local t = label(b, option[2], 0)
        t:ClearAllPoints(); t:SetPoint("LEFT", b, "RIGHT", 4, 0)
        b:SetScript("OnClick", function(self)
            if key == "enabled" then A.SetEnabled(self:GetChecked() == true)
            else
                A.db[key] = self:GetChecked() == true
                if key == "popup" and not A.db.popup then A.UI.Hide() end
            end
        end)
    end
    local test = CreateFrame("Button", nil, p, "UIPanelButtonTemplate")
    p.test = test; test:SetSize(180, 26); test:SetPoint("TOPLEFT", 16, -224); test:SetText("Preview rare alert")
    test:SetScript("OnClick", function()
        if SettingsPanel and HideUIPanel then HideUIPanel(SettingsPanel) end
        A.Preview()
    end)
    local reset = CreateFrame("Button", nil, p, "UIPanelButtonTemplate")
    p.reset = reset; reset:SetSize(180, 26); reset:SetPoint("TOPLEFT", 210, -224); reset:SetText("Reset alert position")
    reset:SetScript("OnClick", function() A.db.position = nil; A.UI.Position() end)
    label(p, "Enable enemy nameplates outside combat for nearby detection. Range is controlled by WoW; this is not a zone-wide radar.", -278)
    label(p, "Key Bindings: search ElmoRare and assign 'Skull on current target'. Target the rare yourself, then press the key. Group marking permissions apply.", -334)
    label(p, "Each spawn alerts once while observed. It can alert again after five minutes without being observed. /erare last shows the last sighting.", -402)
    p:SetScript("OnShow", function()
        for _, key in ipairs({"enabled", "sound", "popup"}) do p[key]:SetChecked(A.db[key]) end
    end)
    S.category = Settings.RegisterCanvasLayoutCategory(p, "ElmoRare")
    Settings.RegisterAddOnCategory(S.category)
end

function S.Open()
    if S.category then Settings.OpenToCategory(S.category:GetID())
    else A.Print("/erare test | on | off | last | status") end
end
