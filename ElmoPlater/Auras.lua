local _, A = ...
local R = {}
A.Auras = R
local SIZE = 22
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"

function R.Initialize()
    R.available = A.Call(C_XMLUtil and C_XMLUtil.GetTemplateInfo, "CustomAuraContainerTemplate") ~= nil
    if R.available then
        R.timerFormatter = C_StringUtil.CreateNumericRuleFormatter()
        R.timerFormatter:AddBreakpoint({threshold = 0, step = 1, format = "%d"})
    end
end

function R.Restricted()
    return A.Bool(A.Call(C_Secrets and C_Secrets.ShouldAurasBeSecret)) == true
end

local function label(button, size, ...)
    local text = button:CreateFontString(nil, "OVERLAY")
    text:SetFont(FONT, size, "OUTLINE"); text:SetTextColor(1, 1, 1)
    text:SetPoint(...)
    return text
end

local function initializeButton(button)
    -- Blizzard adopts these display elements after this callback returns.
    -- Never inspect or change the individual buttons after initialization.
    button:SetSize(SIZE, SIZE); button:EnableMouse(false)
    local texture = button:CreateTexture(nil, "ARTWORK")
    texture:SetPoint("TOPLEFT", 1, -1); texture:SetPoint("BOTTOMRIGHT", -1, 1)
    texture:SetTexCoord(.07, .93, .07, .93)
    button:SetIcon(texture)
    button:SetDurationText(label(button, 12, "BOTTOM", button, "TOP", 0, 2), {textFormatter = R.timerFormatter})
    button:SetApplicationCount(label(button, 9, "BOTTOMRIGHT"))
end

function R.Create(parent)
    if not R.available then return end
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")
    container:EnableMouse(false); container:SetSize(1, 1)
    container:SetPoint("BOTTOM", parent, "TOP", 0, 20)
    container:SetFlowLayoutAnchorPoint("BOTTOMLEFT")
    container:SetFlowLayoutGrowthDirection(AnchorUtil.FlowDirection.Right, AnchorUtil.FlowDirection.Up)
    container:SetFlowLayoutMaximumLineSize(6 * (SIZE + 2) - 2)
    container:AddAuraGroup("personal", "HARMFUL|PLAYER", {
        initializeFrame = initializeButton,
        maxFrameCount = math.huge,
        sortMethod = AuraContainerSortMethod.Default,
        sortDirection = AuraContainerSortDirection.Normal,
        layout = {elementWidth = SIZE, elementHeight = SIZE, elementSpacing = 2, lineSpacing = 16},
    })
    container:SetEnabled(false); container:Hide()
    return container
end

function R.Update(record)
    local container = record.auraContainer
    if container and record.auraSize ~= A.db.plateAuraSize then
        -- Scale the public container; its adopted children can be inaccessible.
        container:SetScale(A.db.plateAuraSize / SIZE)
        record.auraSize = A.db.plateAuraSize
    end
end
