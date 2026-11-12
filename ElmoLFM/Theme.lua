local _, A = ...
local Theme = {}
A.Theme = Theme

-- Inspired by the dark glass and bronze palette of the installed Talents Forever.
-- All artwork here uses the Era client's own textures and fonts.
local WHITE = "Interface\\Buttons\\WHITE8X8"
local BRONZE = { 0.47, 0.36, 0.14 }
local PANEL = { 0.07, 0.07, 0.07 }

function Theme.Panel(frame, color, border, alpha)
    color, border = color or PANEL, border or BRONZE
    frame:SetBackdrop({ bgFile = WHITE, edgeFile = WHITE, edgeSize = 1 })
    frame:SetBackdropColor(color[1], color[2], color[3], alpha or 0.97)
    frame:SetBackdropBorderColor(border[1], border[2], border[3], 1)
end

function Theme.Inset(parent, x, y, width, height)
    local background = parent:CreateTexture(nil, "BACKGROUND", nil, 0)
    background:SetPoint("TOPLEFT", x, y)
    background:SetSize(width, height)
    background:SetColorTexture(0.025, 0.025, 0.025, 0.6)
    for _, edge in ipairs({ { 0, 0, width, 1 }, { 0, -height + 1, width, 1 }, { 0, 0, 1, height }, { width - 1, 0, 1, height } }) do
        local line = parent:CreateTexture(nil, "BACKGROUND", nil, 1)
        line:SetPoint("TOPLEFT", x + edge[1], y + edge[2])
        line:SetSize(edge[3], edge[4])
        line:SetColorTexture(0.30, 0.24, 0.11, 0.65)
    end
end

function Theme.Button(parent, text, width, x, y, action)
    local button = CreateFrame("Button", nil, parent, "BackdropTemplate")
    button:SetSize(width, 24)
    button:SetPoint("TOPLEFT", x, y)
    Theme.Panel(button)
    local label = button:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    label:SetPoint("CENTER")
    label:SetShadowColor(0, 0, 0, 0.8)
    label:SetShadowOffset(1, -1)
    button:SetFontString(label)
    button:SetText(text)
    button:SetHighlightTexture(WHITE)
    button:GetHighlightTexture():SetVertexColor(1, 0.86, 0.42, 0.14)

    function button:Paint(pressed)
        if not self:IsEnabled() then
            self:SetBackdropColor(0.10, 0.10, 0.10, 1)
            self:SetBackdropBorderColor(0.23, 0.23, 0.23, 1)
            label:SetTextColor(0.42, 0.42, 0.42)
        elseif self.primary then
            self:SetBackdropColor(pressed and 0.65 or 0.86, pressed and 0.47 or 0.66, 0.14, 1)
            self:SetBackdropBorderColor(1, 0.86, 0.42, 1)
            label:SetTextColor(0.09, 0.07, 0.025)
            label:SetShadowOffset(0, 0)
        else
            self:SetBackdropColor(pressed and 0.075 or 0.15, pressed and 0.07 or 0.14, pressed and 0.062 or 0.125, 1)
            self:SetBackdropBorderColor(BRONZE[1], BRONZE[2], BRONZE[3], 1)
            label:SetTextColor(1, 0.86, 0.60)
        end
    end
    button:SetScript("OnEnable", function(self) self:Paint() end)
    button:SetScript("OnDisable", function(self) self:Paint() end)
    button:SetScript("OnMouseDown", function(self) self:Paint(true) end)
    button:SetScript("OnMouseUp", function(self) self:Paint() end)
    button:SetScript("OnClick", action)
    button:Paint()
    return button
end

function Theme.Accent(button)
    button.primary = true
    button:Paint()
end

function Theme.Input(input)
    for _, part in ipairs({ input.Left, input.Middle, input.Right }) do part:Hide() end
    Theme.Panel(input, { 0.03, 0.03, 0.03 }, { 0.36, 0.29, 0.12 })
    input:SetTextInsets(8, 8, 0, 0)
    input:SetFontObject("GameFontHighlightSmall")
    input:HookScript("OnEditFocusGained", function(self) self:SetBackdropBorderColor(1, 0.82, 0, 1) end)
    input:HookScript("OnEditFocusLost", function(self) self:SetBackdropBorderColor(0.36, 0.29, 0.12, 1) end)
end
