local _,A=...
local U={icons={}}
A.UI=U
local SIZE,GAP,LEFT=44,5,20
local WHITE="Interface\\Buttons\\WHITE8X8"
local BODY=STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local gold={.68,.52,.18}

local function panel(kind,name,parent)
    local f=CreateFrame(kind,name,parent,BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:SetBackdrop({bgFile=WHITE,edgeFile=WHITE,edgeSize=1})
    f:SetBackdropColor(.025,.025,.025,.90);f:SetBackdropBorderColor(unpack(gold))
    return f
end
local function label(parent,size,value)
    local t=parent:CreateFontString(nil,"OVERLAY")
    t:SetFont(BODY,size,"");t:SetTextColor(.93,.91,.84)
    t:SetJustifyH("LEFT");t:SetJustifyV("TOP");t:SetText(value or "")
    return t
end
local function button(parent,value,w,x,y,fn)
    local b=panel("Button",nil,parent);b:SetSize(w,25);b:SetPoint("TOPLEFT",x,y)
    local t=label(b,12,value);t:SetPoint("CENTER");t:SetJustifyH("CENTER");t:SetJustifyV("MIDDLE")
    b.label=t
    local glow=b:CreateTexture(nil,"HIGHLIGHT");glow:SetAllPoints();glow:SetColorTexture(1,.82,0,.12)
    b:SetScript("OnClick",fn)
    return b
end

function U.FormatTime(remaining)
    local seconds=math.max(1,math.ceil(remaining))
    if seconds>=3600 then return math.floor(seconds/3600).."h" end
    if seconds>=60 then return string.format("%d:%02d",math.floor(seconds/60),seconds%60) end
    return tostring(seconds)
end

local function icon(index)
    local b=panel("Button",nil,U.bar)
    b:SetSize(SIZE,SIZE);b:SetPoint("TOPLEFT",LEFT+(index-1)*(SIZE+GAP),-4)
    b:RegisterForClicks("RightButtonUp")
    b.texture=b:CreateTexture(nil,"ARTWORK");b.texture:SetPoint("TOPLEFT",2,-2);b.texture:SetPoint("BOTTOMRIGHT",-2,2)
    b.texture:SetTexCoord(.07,.93,.07,.93)
    b.timer=label(b,18,"");b.timer:ClearAllPoints();b.timer:SetAllPoints();b.timer:SetJustifyH("CENTER");b.timer:SetJustifyV("MIDDLE")
    b.timer:SetFont(BODY,18,"OUTLINE");b.timer:SetShadowColor(0,0,0,1);b.timer:SetShadowOffset(1,-1)
    b:SetScript("OnEnter",function(self)
        if not self.spellID then return end
        GameTooltip:SetOwner(self,"ANCHOR_TOP")
        GameTooltip:ClearLines()
        local ok=pcall(GameTooltip.SetSpellByID,GameTooltip,self.spellID)
        if not ok or GameTooltip:NumLines()==0 then
            local info=A.Spells.Info(self.spellID)
            GameTooltip:SetText(info and info.name or "Loading ability…")
        end
        GameTooltip:AddLine("Right-click: settings",.55,.78,1)
        if not A.db.locked then GameTooltip:AddLine("Shift-right-click: remove this ability",.8,.8,.8) end
        GameTooltip:Show()
    end)
    b:SetScript("OnLeave",function() GameTooltip:Hide() end)
    b:SetScript("OnClick",function()
        if IsShiftKeyDown() and not A.db.locked then A.Remove(index) else U.Settings() end
    end)
    return b
end

function U.Create()
    if U.bar then return end
    local bar=CreateFrame("Frame","ElmoSpellTrackerBar",UIParent)
    U.bar=bar
    bar:SetFrameStrata("MEDIUM");bar:SetClampedToScreen(true);bar:SetMovable(true)
    local p=A.db.position
    if type(p)=="table" and A.Number(p.x) and A.Number(p.y) then
        bar:SetPoint("TOPLEFT",UIParent,"TOPLEFT",p.x,p.y)
    else bar:SetPoint("TOPLEFT",UIParent,"CENTER",-210,-180) end
    local handle=panel("Button",nil,bar);U.handle=handle
    handle:SetPoint("TOPLEFT",0,-4);handle:SetSize(14,SIZE)
    local dots=label(handle,12,":");dots:SetPoint("CENTER")
    handle:RegisterForDrag("LeftButton")
    handle:SetScript("OnDragStart",function() if not A.db.locked then bar:StartMoving() end end)
    handle:SetScript("OnDragStop",function()
        bar:StopMovingOrSizing()
        local x,y=bar:GetLeft()-UIParent:GetLeft(),bar:GetTop()-UIParent:GetTop()
        A.db.position={x=x,y=y}
        bar:ClearAllPoints();bar:SetPoint("TOPLEFT",UIParent,"TOPLEFT",x,y)
    end)
    handle:SetScript("OnClick",function() U.Settings() end)
    handle:SetScript("OnEnter",function(self)
        GameTooltip:SetOwner(self,"ANCHOR_TOP");GameTooltip:SetText("ElmoSpellTracker")
        GameTooltip:AddLine("Drag this handle to move the bar. Click for settings.",1,1,1,true);GameTooltip:Show()
    end)
    handle:SetScript("OnLeave",function() GameTooltip:Hide() end)
    for i=1,A.HARD_LIMIT do U.icons[i]=icon(i) end
end

function U.Layout()
    if not U.bar then return end
    local count=math.min(#A.db.spells,A.db.maxSkills)
    U.bar:SetSize(count>0 and (LEFT+count*SIZE+(count-1)*GAP+4) or 14,SIZE+8)
    U.bar:SetShown(count>0 or not A.db.locked)
    U.handle:SetShown(not A.db.locked)
    for i,b in ipairs(U.icons) do
        b.spellID=i<=count and A.db.spells[i] or nil
        b:SetShown(b.spellID~=nil)
        if b.spellID then
            local info=A.Spells.Info(b.spellID)
            b.texture:SetTexture(info and info.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
        end
    end
    if U.settings then U.RefreshSettings() end
end

function U.Update()
    local active=false
    for _,b in ipairs(U.icons) do
        if b.spellID and b:IsShown() then
            local state=A.Spells.Status(b.spellID)
            local remaining=state.remaining
            local cooling=remaining and remaining>0
            local grey=cooling or remaining==nil or A.Spells.InsufficientPower(b.spellID)
            b.remaining=remaining
            b.texture:SetDesaturated(grey)
            local shade=grey and .65 or 1
            b.texture:SetVertexColor(shade,shade,shade)
            if cooling then
                local value=U.FormatTime(remaining)
                b.timer:SetFont(BODY,#value>4 and 14 or 18,"OUTLINE")
                b.timer:SetText(value);b.timer:Show();active=true
            elseif remaining==nil then b.timer:SetText("?");b.timer:Show()
            else b.timer:SetText("");b.timer:Hide() end
        end
    end
    return active
end

function U.RefreshSettings()
    local f=U.settings
    if not f then return end
    if not f.limit:HasFocus() then f.limit:SetText(tostring(A.db.maxSkills)) end
    f.lock.label:SetText(A.db.locked and "Unlock bar" or "Lock bar")
    f.count:SetText(math.min(#A.db.spells,A.db.maxSkills).." / "..A.db.maxSkills.." visible · "..#A.db.spells.." saved")
end

function U.Settings()
    if not U.settings then
        local f=panel("Frame","ElmoSpellTrackerSettings",UIParent);U.settings=f
        f:SetSize(390,270);f:SetPoint("CENTER");f:SetFrameStrata("DIALOG");f:SetClampedToScreen(true)
        f:EnableMouse(true)
        local title=label(f,16,"ElmoSpellTracker");title:SetPoint("TOPLEFT",17,-17);title:SetTextColor(1,.82,0)
        button(f,"X",25,350,-11,function() f:Hide() end)
        local description=label(f,11,"Used abilities are added from left to right.\nGrey: on cooldown or insufficient mana, energy or rage.\nThe timer shows cooldown only.")
        description:SetPoint("TOPLEFT",18,-49)
        local t=label(f,12,"Maximum skills (1–12)");t:SetPoint("TOPLEFT",18,-94)
        local input=panel("EditBox",nil,f);f.limit=input
        input:SetPoint("TOPLEFT",187,-88);input:SetSize(45,27);input:SetFont(BODY,13,"")
        input:SetTextInsets(8,5,0,0);input:SetAutoFocus(false);input:SetNumeric(true);input:SetMaxLetters(2)
        f.status=label(f,11,"");f.status:SetPoint("TOPLEFT",18,-127);f.status:SetWidth(350)
        local function apply()
            local ok,message=A.SetMaxSkills(input:GetText())
            f.status:SetText(message);f.status:SetTextColor(ok and .6 or 1,ok and .9 or .3,.3)
            if ok then input:ClearFocus() end
        end
        button(f,"Apply",65,244,-89,apply)
        input:SetScript("OnEnterPressed",apply)
        input:SetScript("OnEscapePressed",function() input:ClearFocus();U.RefreshSettings() end)
        f.lock=button(f,"Lock bar",135,18,-157,function() A.SetLocked(not A.db.locked) end)
        button(f,"Clear tracked skills",174,165,-157,function() A.Clear();f.status:SetText("Skills will be added again when used.") end)
        f.count=label(f,11,"");f.count:SetPoint("TOPLEFT",18,-198)
        local help=label(f,10,"Drag the bar handle to move it. Shift-right-click an icon\nwhile unlocked to remove it. /cst max 10 sets the limit.")
        help:SetPoint("TOPLEFT",18,-222)
        table.insert(UISpecialFrames,"ElmoSpellTrackerSettings")
    end
    U.RefreshSettings();U.settings:Show()
end

function U.RegisterOptions()
    if U.optionsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p=CreateFrame("Frame",nil,UIParent);U.optionsPanel=p;p:Hide()
    local title=label(p,16,"ElmoSpellTracker");title:SetPoint("TOPLEFT",16,-16)
    local description=label(p,12,"Tracked abilities, bar capacity and position locking.")
    description:SetPoint("TOPLEFT",16,-48)
    p.locked=CreateFrame("CheckButton",nil,p,"UICheckButtonTemplate")
    p.locked:SetPoint("TOPLEFT",16,-80);p.locked:SetSize(26,26)
    local caption=label(p.locked,12,"Lock bar position and prevent mouse removal")
    caption:SetPoint("LEFT",p.locked,"RIGHT",4,0)
    p.locked:SetScript("OnClick",function(self)A.SetLocked(self:GetChecked()==true)end)
    local capacity=label(p,12,"Maximum skills (1–12)");capacity:SetPoint("TOPLEFT",16,-132)
    p.limit=CreateFrame("EditBox",nil,p,"InputBoxTemplate")
    p.limit:SetPoint("TOPLEFT",242,-123);p.limit:SetSize(56,26)
    p.limit:SetAutoFocus(false);p.limit:SetNumeric(true);p.limit:SetMaxLetters(2)
    p.status=label(p,11,"");p.status:SetPoint("TOPLEFT",16,-164);p.status:SetWidth(530)
    local function apply()
        local ok,message=A.SetMaxSkills(p.limit:GetText())
        p.status:SetText(message);p.limit:SetText(tostring(A.db.maxSkills));p.limit:ClearFocus()
    end
    p.apply=button(p,"Apply",70,310,-123,apply)
    p.limit:SetScript("OnEnterPressed",apply)
    p.limit:SetScript("OnEscapePressed",function(self)self:SetText(tostring(A.db.maxSkills));self:ClearFocus()end)
    local removal=label(p,12,"Remove saved ability number");removal:SetPoint("TOPLEFT",16,-207)
    p.removeIndex=CreateFrame("EditBox",nil,p,"InputBoxTemplate")
    p.removeIndex:SetPoint("TOPLEFT",242,-198);p.removeIndex:SetSize(56,26)
    p.removeIndex:SetAutoFocus(false);p.removeIndex:SetNumeric(true);p.removeIndex:SetMaxLetters(2)
    p.remove=button(p,"Remove",90,310,-198,function()
        local removed=A.Remove(p.removeIndex:GetText())
        p.status:SetText(removed and "Ability removed." or "Enter an existing saved ability number.")
        p.removeIndex:ClearFocus()
    end)
    p.clear=button(p,"Clear tracked skills",240,16,-250,function()
        A.Clear();p.status:SetText("Skills will be added again when used.")
    end)
    p.open=button(p,"Open bar settings",240,16,-292,function()
        if SettingsPanel and HideUIPanel then HideUIPanel(SettingsPanel) end
        U.Settings()
    end)
    p:SetScript("OnShow",function()
        p.locked:SetChecked(A.db.locked);p.limit:SetText(tostring(A.db.maxSkills));p.status:SetText("")
    end)
    U.optionsCategory=Settings.RegisterCanvasLayoutCategory(p,"ElmoSpellTracker")
    Settings.RegisterAddOnCategory(U.optionsCategory)
end
