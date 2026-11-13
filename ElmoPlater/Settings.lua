local _, A = ...
local U = {}
A.Settings = U
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"

local function label(parent, value, x, y, size, width)
    local f = parent:CreateFontString(nil,"OVERLAY")
    f:SetFont(FONT,size or 12,""); f:SetTextColor(.94,.92,.85); f:SetJustifyH("LEFT")
    f:SetPoint("TOPLEFT",x,y); f:SetWidth(width or 320); f:SetText(value)
    return f
end
function U.RegisterOptions()
    if U.optionsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p=CreateFrame("Frame",nil,UIParent);U.optionsPanel=p;p:Hide()
    label(p,"ElmoPlater",16,-16,16,530)
    label(p,"Health, mana, casting, personal debuffs and quest kill markers.",16,-48,12,530)
    p.questKills=CreateFrame("CheckButton",nil,p,"UICheckButtonTemplate")
    p.questKills:SetPoint("TOPLEFT",16,-80);p.questKills:SetSize(26,26)
    local caption=label(p.questKills,"Show quest kill knife",0,0,12,460)
    caption:ClearAllPoints();caption:SetPoint("LEFT",p.questKills,"RIGHT",4,0)
    p.questKills:SetScript("OnClick",function(self)
        A.db.questKills=self:GetChecked()==true;A.QuestKills.Invalidate();A.Update(false)
    end)
    label(p,"Debuff icon size (14–36)",16,-132,12,250)
    p.auraSize=CreateFrame("EditBox",nil,p,"InputBoxTemplate")
    p.auraSize:SetPoint("TOPLEFT",266,-123);p.auraSize:SetSize(56,26)
    p.auraSize:SetAutoFocus(false);p.auraSize:SetNumeric(true);p.auraSize:SetMaxLetters(2)
    local function apply()
        local value=tonumber(p.auraSize:GetText())
        if value and value%1==0 and value>=14 and value<=36 then A.db.plateAuraSize=value;A.Update(true) end
        p.auraSize:SetText(tostring(A.db.plateAuraSize));p.auraSize:ClearFocus()
    end
    p.apply=CreateFrame("Button",nil,p,"UIPanelButtonTemplate")
    p.apply:SetPoint("TOPLEFT",334,-123);p.apply:SetSize(70,26);p.apply:SetText("Apply")
    p.apply:SetScript("OnClick",apply);p.auraSize:SetScript("OnEnterPressed",apply)
    p.auraSize:SetScript("OnEscapePressed",function(self)self:SetText(tostring(A.db.plateAuraSize));self:ClearFocus()end)
    local function toggle(key, caption, y)
        local check=CreateFrame("CheckButton",nil,p,"UICheckButtonTemplate")
        p[key]=check;check:SetPoint("TOPLEFT",16,y);check:SetSize(26,26)
        local text=label(check,caption,0,0,12,460)
        text:ClearAllPoints();text:SetPoint("LEFT",check,"RIGHT",4,0)
        check:SetScript("OnClick",function(self)A.db[key]=self:GetChecked()==true;A.Update(false)end)
    end
    toggle("showMana","Show caster NPC mana bar",-176)
    toggle("showCast","Show mob cast bar",-214)
    p:SetScript("OnShow",function()
        p.questKills:SetChecked(A.db.questKills);p.auraSize:SetText(tostring(A.db.plateAuraSize))
        p.showMana:SetChecked(A.db.showMana);p.showCast:SetChecked(A.db.showCast)
    end)
    U.optionsCategory=Settings.RegisterCanvasLayoutCategory(p,"ElmoPlater")
    Settings.RegisterAddOnCategory(U.optionsCategory)
end

function U.Open()
    if U.optionsCategory then Settings.OpenToCategory(U.optionsCategory:GetID()) end
end
