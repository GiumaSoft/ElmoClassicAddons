local _, A = ...
local E = {offset=0, rows={}}
A.ConditionEditor = E
local U = A.Settings
local label, button, entry = U.Label, U.Button, U.Entry

local function choice(parent, x, y, width, items)
    return A.Dropdown.New(parent,x,y,width,items,nil,E.frame)
end

local function pairsOf(values)
    local result={}
    for _, v in ipairs(values) do result[#result+1]={v,tostring(v)} end
    return result
end
function E.Collect()
    for i,row in ipairs(E.rows) do
        local value=E.draft.conditions[E.offset+i]
        if value then
            for _, key in ipairs({"metric","op","join","opens","closes"}) do value[key]=row[key].value end
            value.value=row.value:GetText(); value.spellID=row.spellID.value
        end
    end
end
function E.Refresh()
    A.Dropdown.Close()
    local count=#E.draft.conditions
    E.offset=math.max(0,math.min(E.offset,math.max(0,count-5)))
    for i,row in ipairs(E.rows) do
        local value=E.draft.conditions[E.offset+i]
        row.frame:SetShown(value~=nil)
        if value then
            row.index=E.offset+i
            row.number:SetText(row.index..".")
            for _,key in ipairs({"metric","op","join","opens","closes"}) do row[key]:SetValue(value[key]) end
            row.value:SetText(value.value); row.spellID:SetValue(value.spellID or 0)
        end
    end
    E.count:SetText(count.." conditions · rows "..(count==0 and 0 or E.offset+1).."–"..math.min(count,E.offset+5))
end
function E.Save()
    E.Collect()
    local rule,err=A.Rules.Validate(E.draft)
    if not rule then E.message:SetText(err); return false end
    A.db.rules[E.index]=rule
    U.selected=E.index; U.Refresh(); A.Update(false)
    E.frame:Hide(); U.Message("Rule and conditions saved.")
    return true
end
function E.Create()
    if E.frame then return end
    local f=CreateFrame("Frame","ElmoPlaterConditions",U.frame,BackdropTemplateMixin and "BackdropTemplate" or nil)
    E.frame=f; f:SetSize(920,450); f:SetPoint("CENTER"); f:SetFrameStrata("FULLSCREEN_DIALOG")
    f:SetBackdrop({bgFile="Interface\\Buttons\\WHITE8X8",edgeFile="Interface\\Buttons\\WHITE8X8",edgeSize=2})
    f:SetBackdropColor(.025,.03,.035,1); f:SetBackdropBorderColor(.72,.54,.18,1); f:EnableMouse(true)
    table.insert(UISpecialFrames,"ElmoPlaterConditions")
    f:SetScript("OnHide",A.Dropdown.Close)
    E.title=label(f,"Conditions",16,-15,16,830)
    button(f,"X",878,-12,27,function() f:Hide() end)
    label(f,"These conditions must also pass the rule limits. Use AND / OR and parentheses; AND is evaluated before OR.",16,-45,11,888)
    label(f,"Choose This rule or another ability in the spell menu. Debuffs must be yours. Unknown data does not pass.",16,-64,11,888)
    for _,item in ipairs({{16,"#"},{46,"Join"},{120,"("},{165,"Condition"},{429,"Operator"},{515,"Value"},{607,"Spell / aura"},{735,")"}}) do
        label(f,item[2],item[1],-95,11,150)
    end
    for i=1,5 do
        local row={}; E.rows[i]=row
        row.frame=CreateFrame("Frame",nil,f); row.frame:SetSize(890,35); row.frame:SetPoint("TOPLEFT",16,-117-(i-1)*38)
        row.number=label(row.frame,"",0,-6,11,24)
        row.join=choice(row.frame,30,0,66,pairsOf({"AND","OR"}))
        row.opens=choice(row.frame,104,0,38,{{0,"—"},{1,"("},{2,"(("},{3,"((("}})
        row.metric=choice(row.frame,149,0,256,A.Conditions.metrics)
        row.op=choice(row.frame,413,0,78,pairsOf(A.Conditions.operators))
        row.value=entry(row.frame,499,0,84)
        row.spellID=choice(row.frame,591,0,118,function()return U.SpellOptions(true,"This rule",row.spellID.value)end)
        row.spellID.menuWidth=330
        row.closes=choice(row.frame,719,0,42,{{0,"—"},{1,")"},{2,"))"},{3,")))"}})
        button(row.frame,"Remove",773,0,102,function()
            E.Collect(); table.remove(E.draft.conditions,row.index); E.Refresh()
        end)
    end
    E.count=label(f,"",16,-312,11,510)
    button(f,"Previous",590,-305,145,function() E.Collect(); E.offset=E.offset-5; E.Refresh() end)
    button(f,"Next",746,-305,145,function() E.Collect(); E.offset=E.offset+5; E.Refresh() end)
    button(f,"Add condition",16,-343,175,function()
        E.Collect()
        local conditions=E.draft.conditions
        conditions[#conditions+1]={metric="health_pct",op=">=",value=0,spellID=0,join="AND",opens=0,closes=0}
        E.offset=math.max(0,#conditions-5); E.Refresh()
    end)
    E.message=label(f,"",16,-382,11,875)
    button(f,"Save conditions",560,-410,175,E.Save)
    button(f,"Cancel",746,-410,145,function() f:Hide() end)
end
function E.Open()
    local rule,err=U.ReadRule()
    if not rule then U.Message(err); return end
    -- Validate returns a fresh copy, so Cancel leaves the saved rule unchanged.
    E.draft,E.index,E.offset=rule,U.selected,0
    E.Create(); E.title:SetText("Rule "..E.index..": "..A.Rules.Name(rule).." — Conditions")
    E.message:SetText(""); E.Refresh(); E.frame:Show()
end
