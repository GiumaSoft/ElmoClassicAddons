local _, A = ...
local U = {ruleOffset=0, selected=1, rows={}, fields={}, book={}}
A.Settings = U
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local WHITE = "Interface\\Buttons\\WHITE8X8"

local function panel(kind, parent)
    local f = CreateFrame(kind, nil, parent, BackdropTemplateMixin and "BackdropTemplate" or nil)
    f:SetBackdrop({bgFile=WHITE, edgeFile=WHITE, edgeSize=1})
    f:SetBackdropColor(.035,.04,.045,.98); f:SetBackdropBorderColor(.6,.46,.18,1)
    return f
end
local function label(parent, value, x, y, size, width)
    local f = parent:CreateFontString(nil,"OVERLAY")
    f:SetFont(FONT,size or 12,""); f:SetTextColor(.94,.92,.85); f:SetJustifyH("LEFT")
    f:SetPoint("TOPLEFT",x,y); f:SetWidth(width or 320); f:SetText(value)
    return f
end
local function button(parent, value, x, y, width, fn)
    local b = panel("Button",parent); b:SetPoint("TOPLEFT",x,y); b:SetSize(width,25)
    b.label = label(b,value,6,-6,11,width-12)
    b:SetScript("OnClick",fn)
    return b
end
local function entry(parent, x, y, width)
    local f = panel("EditBox",parent); f:SetPoint("TOPLEFT",x,y); f:SetSize(width or 64,23)
    f:SetFont(FONT,12,""); f:SetAutoFocus(false); f:SetTextInsets(5,5,0,0); f:SetMaxLetters(10)
    f:SetScript("OnEscapePressed",function(self) self:ClearFocus() end)
    f:SetScript("OnEnterPressed",function(self) self:ClearFocus() end)
    return f
end
local function message(value) if U.message then U.message:SetText(value or "") end end
U.Panel, U.Label, U.Button, U.Entry, U.Message = panel, label, button, entry, message

-- Learned personal auras populate the debuff picker; the spellbook supplies cast spells.
-- Retain existing selections even when their rank is no longer in the spellbook.
function U.SpellOptions(casts, defaultLabel, extraID)
    local found, sorted, result = {}, {}, {}
    local function add(id,name)
        id=A.Number(id)
        if not id or id<=0 or found[id] then return end
        local info=A.Spells.Info(id)
        found[id]={id,info and info.name or A.Text(name) or "Spell #"..id}
        sorted[#sorted+1]=found[id]
    end
    for _, item in pairs(A.db.learnedDebuffs) do
        if type(item)=="table" then add(item.id,item.name) end
    end
    if casts then for _,info in ipairs(U.book) do add(info.id,info.name) end end
    add(extraID)
    for _,rule in ipairs(A.db.rules) do add(rule.spellID); if rule.auraID>0 then add(rule.auraID) end end
    table.sort(sorted,function(a,b)return a[2]==b[2] and a[1]<b[1] or a[2]<b[2] end)
    if defaultLabel then result[1]={0,defaultLabel} end
    for i,item in ipairs(sorted) do
        local duplicate=(sorted[i-1] and sorted[i-1][2]==item[2]) or (sorted[i+1] and sorted[i+1][2]==item[2])
        result[#result+1]={item[1],item[2]..(duplicate and " (#"..item[1]..")" or "")}
    end
    return result
end
local function numbers(minimum,maximum,current,suffix)
    local result={}
    for value=minimum,maximum do result[#result+1]={value,tostring(value)..(suffix or "")} end
    if A.Number(current) and (current<minimum or current>maximum or current%1~=0) then
        result[#result+1]={current,tostring(current)..(suffix or "")}
    end
    return result
end
local function refreshOptions()
    local values={0,1,2,3,4,5,8,10,15,20,30,60}
    local current=U.fields.refresh and U.fields.refresh.value
    local found=false
    for _,v in ipairs(values) do if v==current then found=true end end
    if A.Number(current) and not found then values[#values+1]=current;table.sort(values) end
    local result={}
    for _,v in ipairs(values) do result[#result+1]={v,v==0 and "Only when missing" or "Refresh at "..v.." seconds remaining"} end
    return result
end
function U.NewOptions()
    local result={{"health_below","Health below threshold (20%)"},{"lowest_health","Lowest health (attacked mobs)"}}
    for _,item in ipairs(U.SpellOptions(false)) do result[#result+1]={item[1],"Missing debuff: "..item[2]} end
    return result
end
function U.LayoutEditor()
    local kind=U.fields.kind.value
    local debuff=kind=="debuff"
    local y=-109
    for _,group in ipairs(U.groups) do
        local show=not group.kind or group.kind==kind
        group.label:SetShown(show);group.field:SetShown(show)
        if show then
            group.label:ClearAllPoints();group.label:SetPoint("TOPLEFT",350,y-5)
            group.field:ClearAllPoints();group.field:SetPoint("TOPLEFT",550,y)
            if group.key=="minEnemies" then
                U.missingLabel:ClearAllPoints();U.missingLabel:SetPoint("TOPLEFT",662,y-5)
                U.fields.minMissing:ClearAllPoints();U.fields.minMissing:SetPoint("TOPLEFT",802,y)
            elseif group.key=="minHealth" then
                U.rangeTo:ClearAllPoints();U.rangeTo:SetPoint("TOPLEFT",714,y-5)
                U.fields.maxHealth:ClearAllPoints();U.fields.maxHealth:SetPoint("TOPLEFT",750,y)
            end
            y=y-42
        end
    end
    U.missingLabel:SetShown(debuff);U.fields.minMissing:SetShown(debuff)
end
function U.LoadRule()
    local rule=A.db.rules[U.selected]
    U.ruleTitle:SetText(rule and ("Rule "..U.selected..": "..A.Rules.Name(rule)) or "Add your first rule")
    for key,field in pairs(U.fields) do
        local value
        if rule then value=rule[key] end
        field:SetValue(value)
    end
    U.conditionsButton.label:SetText("Conditions ("..(rule and #(rule.conditions or {}) or 0)..")…")
    U.LayoutEditor()
end
function U.Lists()
    local count=#A.db.rules
    U.ruleOffset=math.max(0,math.min(U.ruleOffset,math.max(0,count-9)))
    for i,row in ipairs(U.rows) do
        local index=U.ruleOffset+i;local rule=A.db.rules[index]
        row.index=index;row:SetShown(rule~=nil)
        if rule then
            row.label:SetText(index..". "..(rule.enabled and "" or "[OFF] ")..A.Rules.Name(rule)..(rule.kind=="debuff" and rule.aoe and " [AoE]" or ""))
            row:SetBackdropBorderColor(unpack(index==U.selected and {1,.82,.2,1} or {.35,.3,.2,1}))
        end
    end
    U.ruleCount:SetText(count.." rules · first match wins")
    U.emptyList:SetShown(count==0)
    U.addSpell:SetValue(U.addSpell.value)
    U.dirty=false
end
function U.Refresh()
    if not U.frame then return end
    U.Lists();U.LoadRule()
end
function U.Add(id)
    id=id or U.addSpell.value
    if not id or id==0 then message("Choose a health or debuff rule from the New rule menu, then click + Add rule."); return end
    local index,err=A.Rules.Add(id)
    if not index then message(err);return end
    U.selected=index;U.ruleOffset=math.max(0,index-9)
    U.Refresh();A.Update(false);message("Rule "..index.." added. Use + Add rule again for another rule.")
end
function U.Duplicate()
    local old=A.db.rules[U.selected]
    if not old then message("Select a rule to duplicate.");return end
    local copy,err=A.Rules.Validate(old)
    if not copy then message(err);return end
    A.db.rules[#A.db.rules+1]=copy
    U.selected=#A.db.rules;U.ruleOffset=math.max(0,U.selected-9)
    U.Refresh();A.Update(false);message("Rule duplicated at the bottom of the list.")
end
function U.Move(direction)
    U.selected=A.Rules.Move(U.selected,direction);U.ruleOffset=math.max(0,U.selected-9)
    A.Dropdown.Close();U.Refresh();A.Update(false)
end
function U.Remove()
    if A.db.rules[U.selected] then table.remove(A.db.rules,U.selected) end
    U.selected=math.max(1,math.min(U.selected,#A.db.rules))
    A.Dropdown.Close();U.Refresh();A.Update(false)
end
function U.ReadRule()
    local old=A.db.rules[U.selected]
    if not old then return nil,"Add or select a rule first." end
    local values={conditions=old.conditions}
    for key,field in pairs(U.fields) do values[key]=field.value end
    return A.Rules.Validate(values)
end
function U.Save()
    local rule,err=U.ReadRule()
    if not rule then message(err);return end
    A.db.rules[U.selected]=rule
    U.Refresh();A.Update(false);message("Rule saved. Evaluation follows the list from top to bottom.")
end
function U.Tick(now)
    if not U.frame or not U.frame:IsShown() then return end
    if U.dirty then U.Lists() end
    if U.statusAt and now-U.statusAt<.5 then return end
    U.statusAt=now
    local chosen=A.priorityTarget
    local matched=chosen and A.db.rules[chosen.suggestedRule]
    U.status:SetText(matched and ("Priority: "..(A.Text(A.Call(UnitName,chosen.unit)) or "Mob")..
        " · Rule "..chosen.suggestedRule..": "..A.Rules.Name(matched))
        or (A.privateHealthActive and "Health is private: health-based priority is unavailable."
        or "Priority: no matching rule for an engaged mob"))
    if U.fields.kind.value=="debuff" then
        local id=U.fields.spellID.value
        local reason
        if id and id>0 then local ready;ready,reason=A.Spells.Ready(id) end
        U.readiness:SetText("Selected spell: "..(reason or "Choose an ability"))
    else U.readiness:SetText(A.privateHealthActive and "Health rules require readable health values."
        or "Health rules do not require an ability, resources or cooldown checks.") end
end
function U.Create()
    if U.frame then return end
    local f=CreateFrame("Frame","ElmoPlaterSettings",UIParent,BackdropTemplateMixin and "BackdropTemplate" or nil)
    U.frame=f;f:SetSize(960,650);f:SetPoint("CENTER");f:SetFrameStrata("DIALOG")
    f:SetBackdrop({bgFile=WHITE,edgeFile=WHITE,edgeSize=2})
    f:SetBackdropColor(.025,.03,.035,.98);f:SetBackdropBorderColor(.72,.54,.18,1)
    f:SetClampedToScreen(true);f:EnableMouse(true);f:SetMovable(true);f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart",function(self)self:StartMoving()end)
    f:SetScript("OnDragStop",function(self)self:StopMovingOrSizing()end)
    f:SetScript("OnHide",function()A.Dropdown.Close();if A.ConditionEditor.frame then A.ConditionEditor.frame:Hide() end end)
    local w,h=A.Number(A.Call(UIParent.GetWidth,UIParent)),A.Number(A.Call(UIParent.GetHeight,UIParent))
    if w and h then f:SetScale(math.min(1,(w-24)/960,(h-24)/650)) end
    UISpecialFrames=UISpecialFrames or {};table.insert(UISpecialFrames,"ElmoPlaterSettings")
    label(f,"ElmoPlater "..A.version.." — Rules Manager",18,-15,17,840)
    button(f,"X",918,-12,27,function()f:Hide()end)
    label(f,"Rules run top to bottom. The first matching enabled rule wins. Only mobs you attacked qualify.",18,-43,11,924)
    label(f,"New rule — health or missing debuff",18,-78,12,306)
    U.addSpell=A.Dropdown.New(f,18,-102,306,U.NewOptions)
    U.addSpell:SetValue(nil)
    U.addButton=button(f,"+ Add rule",18,-136,146,function()U.Add()end)
    U.duplicateButton=button(f,"Duplicate",178,-136,146,U.Duplicate)
    for i=1,9 do
        U.rows[i]=button(f,"",18,-178-(i-1)*32,306,function(self)
            A.Dropdown.Close();U.selected=self.index;U.Refresh();message("")
        end)
    end
    U.emptyList=label(f,"No rules yet. Choose a health or debuff rule above and click + Add rule. Without matching rules there is no priority highlight.",28,-195,12,280)
    U.ruleCount=label(f,"",18,-476,11,306)
    button(f,"Previous",18,-501,146,function()U.ruleOffset=U.ruleOffset-9;U.Lists()end)
    button(f,"Next",178,-501,146,function()U.ruleOffset=U.ruleOffset+9;U.Lists()end)
    button(f,"Move up",18,-536,96,function()U.Move(-1)end)
    button(f,"Move down",123,-536,96,function()U.Move(1)end)
    button(f,"Remove",228,-536,96,U.Remove)
    label(f,"Health rules need readable HP. Debuffs appear after you apply them. + Add rule appends a new entry.",18,-577,11,306)
    U.ruleTitle=label(f,"",350,-78,14,590)
    U.groups={}
    local function field(key,title,items,kind,width)
        local caption=label(f,title,350,-109,11,195)
        local control=A.Dropdown.New(f,550,-109,width or 390,items)
        U.fields[key]=control
        U.groups[#U.groups+1]={key=key,label=caption,field=control,kind=kind}
        return control
    end
    field("kind","Rule type",A.Rules.kinds).changed=function()U.LayoutEditor()end
    field("enabled","Rule status",{{true,"Enabled"},{false,"Disabled"}})
    field("threshold","Health strictly below",function()return numbers(0,100,nil,"%")end,"health_below")
    field("auraID","Debuff to track",function()return U.SpellOptions(false,"Same as cast spell")end,"debuff")
    field("spellID","Ability to cast",function()return U.SpellOptions(true)end,"debuff")
    field("aoe","Application",{{false,"Single target"},{true,"Area effect (AoE)"}},"debuff")
    field("refresh","Apply / refresh",refreshOptions,"debuff")
    field("preferCovered","Choose matching mob",{{true,"Already partly covered, then lowest HP"},{false,"Lowest remaining HP"}},"debuff")
    field("minEnemies","Minimum engaged mobs",function()return numbers(1,40)end,nil,90)
    U.missingLabel=label(f,"Minimum missing",662,-109,11,130)
    U.fields.minMissing=A.Dropdown.New(f,802,-109,138,function()return numbers(1,40)end)
    field("minHealth","Target health range",function()return numbers(0,100,U.fields.minHealth.value,"%")end,nil,150)
    U.rangeTo=label(f,"to",714,-109,11,28)
    U.fields.maxHealth=A.Dropdown.New(f,750,-109,190,function()return numbers(0,100,U.fields.maxHealth.value,"%")end)
    U.conditionsButton=button(f,"Conditions (0)…",350,-494,280,function()A.ConditionEditor.Open()end)
    U.saveButton=button(f,"Save rule",650,-494,290,U.Save)
    U.readiness=label(f,"",350,-534,11,590)
    label(f,"Health and debuff priorities follow this list only. Use Conditions for extra criteria. Cooldown and resource checks apply to debuff rules.",350,-563,11,590)
    U.message=label(f,"",18,-626,11,924)
    U.status=label(f,"",350,-602,11,590)
    f:Hide()
end
function U.Toggle()
    U.Create()
    if U.frame:IsShown() then U.frame:Hide();return end
    U.book=A.Spells.Book();U.Refresh();U.frame:Show();U.Tick(GetTime())
end
