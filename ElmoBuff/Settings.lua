local _,A=...
local S={}
A.Settings=S
local function label(parent,value,x,y,width,size)
    local t=parent:CreateFontString(nil,"OVERLAY")
    t:SetFont(STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF",size or 12,"")
    t:SetPoint("TOPLEFT",x,y);t:SetWidth(width or 520);t:SetJustifyH("LEFT");t:SetText(value)
    return t
end
local function button(parent,value,x,y,width,fn)
    local b=CreateFrame("Button",nil,parent,"UIPanelButtonTemplate")
    b:SetPoint("TOPLEFT",x,y);b:SetSize(width,26);b:SetText(value);b:SetScript("OnClick",fn);return b
end
local function change(fn)
    if InCombatLockdown() then A.Print("Change buff settings after combat.");S.Refresh();return end
    fn();A.RefreshSpells();S.Refresh()
end
function S.Refresh()
    local p=S.panel;if not p then return end
    p.enabled:SetChecked(A.db.enabled);p.self:SetChecked(A.db.self)
    p.refresh:SetText(tostring(A.db.refresh))
    p.side:SetText("Side: "..A.db.side:lower());p.size:SetText("Icon size: "..A.db.size)
    local families=A.Spells.families or {}
    for i,b in ipairs(p.buffs) do
        local f=families[i];b:SetShown(f~=nil and A.class~="PALADIN")
        if f then b.caption:SetText(f.name);b:SetChecked(A.db.buffs[f.key]) end
    end
    p.blessing:SetShown(A.class=="PALADIN")
    p.blessing:SetText(A.Spells.active and A.Spells.active[1] and A.Spells.active[1].name or "No blessing learned")
end
function S.Register()
    if S.category or not (Settings and Settings.RegisterCanvasLayoutCategory) then return end
    local p=CreateFrame("Frame",nil,UIParent);p:Hide();S.panel=p;p.buffs={}
    label(p,"ElmoBuff",16,-16,520,16)
    label(p,"Missing-buff icons beside party members. Click an icon to buff that member.",16,-54)
    local function check(key,text,y)
        local b=CreateFrame("CheckButton",nil,p,"UICheckButtonTemplate")
        b:SetPoint("TOPLEFT",16,y);b:SetSize(26,26)
        b.caption=label(b,text,0,0,490);b.caption:ClearAllPoints();b.caption:SetPoint("LEFT",b,"RIGHT",4,0)
        b:SetScript("OnClick",function(self)change(function()A.db[key]=self:GetChecked()==true end)end)
        return b
    end
    p.enabled=check("enabled","Show rebuff icons",-82)
    p.self=check("self","Include your player frame",-120)
    label(p,"Tracked buffs",16,-172)
    for i=1,3 do
        local b=check("unused","",-198-(i-1)*35);p.buffs[i]=b
        b:SetScript("OnClick",function(self)
            local f=A.Spells.families[i]
            if f then change(function()A.db.buffs[f.key]=self:GetChecked()==true end)end
        end)
    end
    p.blessing=button(p,"Blessing",16,-202,310,function()
        change(function()
            local list=A.Spells.families or {};local selected=0
            for i,f in ipairs(list) do if f.key==A.db.blessing then selected=i end end
            for n=1,#list do
                local f=list[(selected+n-1)%#list+1]
                if #f.ranks>0 then A.db.blessing=f.key;break end
            end
        end)
    end)
    label(p,"Refresh when less than",16,-326,220)
    p.refresh=CreateFrame("EditBox",nil,p,"InputBoxTemplate")
    p.refresh:SetPoint("TOPLEFT",240,-318);p.refresh:SetSize(55,26);p.refresh:SetAutoFocus(false)
    p.refresh:SetNumeric(true);p.refresh:SetMaxLetters(3)
    label(p,"seconds remain (0 = missing only)",308,-326,250)
    p.apply=button(p,"Apply",16,-360,80,function()
        local value=tonumber(p.refresh:GetText())
        if value and value>=0 and value<=600 and value%1==0 then change(function()A.db.refresh=value end)
        else S.Refresh() end
    end)
    p.side=button(p,"Side",110,-360,150,function()
        change(function()A.db.side=({RIGHT="LEFT",LEFT="ABOVE",ABOVE="RIGHT"})[A.db.side]end)
    end)
    p.size=button(p,"Icon size",274,-360,150,function()
        change(function()A.db.size=A.db.size>=40 and 20 or math.min(40,A.db.size+4) end)
    end)
    label(p,"Icons disappear after the buff is confirmed. Failed casts stay visible. Rebuffs are hidden and disabled during combat; raids and pets are excluded.",16,-416,530)
    p:SetScript("OnShow",function()A.RefreshSpells();S.Refresh()end)
    S.category=Settings.RegisterCanvasLayoutCategory(p,"ElmoBuff");Settings.RegisterAddOnCategory(S.category)
end
function S.Open()
    if S.category then Settings.OpenToCategory(S.category:GetID())
    else A.Print("/ebuff on | off | status") end
end
