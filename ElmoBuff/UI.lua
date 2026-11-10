local _,A=...
local U={groups={}}
A.UI=U
local WHITE="Interface\\Buttons\\WHITE8X8"
local FONT=STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local BRONZE={.47,.36,.14}

local function usable(frame)
    return frame and not A.Private(frame) and A.Bool(A.Call(frame.IsForbidden,frame))==false
end
function U.Visible(frame)
    return A.Bool(A.Call(frame.IsVisible or frame.IsShown,frame))==true
end
function U.Host(unit)
    -- Read native frame identities/visibility only. Never reparent, resize,
    -- measure, hook or otherwise change another addon's or Blizzard's frames.
    if CompactPartyFrame and A.Table(CompactPartyFrame.memberUnitFrames) then
        for _,f in ipairs(CompactPartyFrame.memberUnitFrames) do
            if usable(f) and A.Text(f.unit)==unit and U.Visible(f) then return f end
        end
    end
    if unit=="player" then return usable(PlayerFrame) and PlayerFrame end
    local index=tonumber(unit:match("^party(%d+)$"))
    if not index then return end
    local f=PartyFrame and A.Call(PartyFrame.GetPartyMemberFrame,PartyFrame,index)
        or PartyFrame and PartyFrame["MemberFrame"..index] or _G["PartyMemberFrame"..index]
    if usable(f) then return f end
end

function U.Anchor(b,host,index)
    b:ClearAllPoints()
    local step=A.db.size+5
    if A.db.side=="LEFT" then b:SetPoint("RIGHT",host,"LEFT",-7-(index-1)*step,0)
    elseif A.db.side=="ABOVE" then b:SetPoint("BOTTOMLEFT",host,"TOPLEFT",(index-1)*step,5)
    else b:SetPoint("LEFT",host,"RIGHT",7+(index-1)*step,0) end
end

local function tooltip(b)
    if not b.family then return end
    local tip=U.tooltip
    tip:SetOwner(b,"ANCHOR_RIGHT");tip:ClearLines()
    tip:AddLine(b.family.name,1,.82,0)
    tip:AddLine(A.Text(A.Call(UnitName,b.unit)) or b.unit,.94,.92,.86)
    tip:AddLine(b.state=="refresh" and "Expiring soon" or "Missing buff",1,.65,.2)
    if b.remaining then tip:AddLine("Remaining: "..math.ceil(b.remaining).." seconds",.75,.75,.7) end
    if b.range==false then tip:AddLine("Out of range — move closer and click again.",1,.35,.3,true)
    else tip:AddLine("Click to cast this buff on this member.",.94,.92,.86,true) end
    tip:AddLine("Disappears when the buff is confirmed. Rebuffs are available outside combat.",.6,.6,.55,true)
    tip:Show()
end

function U.Create()
    if U.root or InCombatLockdown() then return end
    if type(RegisterStateDriver)~="function" then A.Print("Secure state drivers are unavailable.");return end
    U.root=CreateFrame("Frame","ElmoBuffIcons",UIParent,"SecureHandlerStateTemplate")
    U.root:SetSize(1,1);U.root:SetPoint("TOPLEFT",UIParent,"TOPLEFT",0,0)
    -- The engine hides the protected click surfaces during combat/raids.
    RegisterStateDriver(U.root,"visibility","[combat] hide; [group:raid] hide; show")
    U.tooltip=CreateFrame("GameTooltip","ElmoBuffTooltip",UIParent,"GameTooltipTemplate")
    for row,unit in ipairs(A.units) do
        local group={buttons={}};U.groups[row]=group
        for column=1,3 do
            local b=CreateFrame("Button",nil,U.root,"SecureActionButtonTemplate,SecureHandlerStateTemplate,BackdropTemplate")
            group.buttons[column]=b;b.unit=unit
            b:SetSize(A.db.size,A.db.size);b:SetFrameStrata("MEDIUM")
            b:SetBackdrop({bgFile=WHITE,edgeFile=WHITE,edgeSize=1})
            b:SetBackdropColor(.035,.033,.028,.96);b:SetBackdropBorderColor(unpack(BRONZE))
            b:SetAttribute("unit",unit);b:SetAttribute("useOnKeyDown",true)
            b:RegisterForClicks("AnyDown","AnyUp")
            b:SetAttribute("_onstate-combat",[[
                if newstate=="1" then self:SetAttribute("type",nil)
                else self:SetAttribute("type",self:GetAttribute("elmo-castable") and "spell" or nil) end
            ]])
            RegisterStateDriver(b,"combat","[combat] 1; 0")
            b.icon=b:CreateTexture(nil,"ARTWORK");b.icon:SetPoint("TOPLEFT",3,-3);b.icon:SetPoint("BOTTOMRIGHT",-3,3)
            b.icon:SetTexCoord(.08,.92,.08,.92)
            local glow=b:CreateTexture(nil,"HIGHLIGHT");glow:SetAllPoints();glow:SetColorTexture(1,.82,.25,.18)
            b.label=b:CreateFontString(nil,"OVERLAY");b.label:SetFont(FONT,10,"OUTLINE")
            b.label:SetPoint("BOTTOM",0,-1);b.label:SetTextColor(1,.86,.5)
            b:SetScript("OnEnter",tooltip);b:SetScript("OnLeave",function()U.tooltip:Hide()end)
            b:SetScript("OnHide",function()if U.tooltip:GetOwner()==b then U.tooltip:Hide()end end)
            -- Do not replace the template's OnClick or simulate a click.
            b:Hide()
        end
    end
end

function U.Configure(b,unit,f,spell,need,state,remaining,range)
    if InCombatLockdown() then return end
    b.unit,b.family,b.state,b.remaining,b.range=unit,f,state,remaining,range
    b:SetSize(A.db.size,A.db.size)
    b:SetAttribute("spell",spell and spell.id or nil)
    b:SetAttribute("elmo-castable",need and range~=false or false)
    b:SetAttribute("type",need and range~=false and "spell" or nil)
    if need then
        b.icon:SetTexture(spell.icon or f.icon);b.icon:SetDesaturated(range==false)
        if range==false then b:SetBackdropBorderColor(.75,.24,.18,1);b.label:SetText("!")
        elseif state=="refresh" then
            b:SetBackdropBorderColor(.9,.65,.22,1);b.label:SetText(remaining and math.ceil(remaining).."s" or "")
        else b:SetBackdropBorderColor(.68,.52,.18,1);b.label:SetText("") end
        b:Show()
    else b:Hide() end
end
