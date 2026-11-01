local _, A = ...
local D = {}
A.Dropdown = D
local U = A.Settings
local PAGE = 10

function D.Close()
    if D.popup then D.popup:Hide() end
    D.owner = nil
end
local function itemsFor(field)
    return type(field.items) == "function" and field.items() or field.items
end
function D.Render()
    local popup, owner = D.popup, D.owner
    local items = itemsFor(owner)
    D.offset = math.max(0, math.min(D.offset, math.max(0, #items-PAGE)))
    local count = math.min(PAGE, #items-D.offset)
    local width = math.max(240, owner.menuWidth or owner.width)
    popup:SetSize(width, count*27+40)
    popup.rows = popup.rows or {}
    for i=1,PAGE do
        local row = popup.rows[i]
        if not row then
            row=U.Button(popup,"",3,-3-(i-1)*27,width-6,function(self)
                local field, item = D.owner, self.item
                if not field or not item then return end
                field:SetValue(item[1]); D.Close()
                if field.changed then field.changed(field, item[1]) end
            end)
            popup.rows[i]=row
        end
        local item=items[D.offset+i]
        row.item=item; row:SetWidth(width-6); row.label:SetWidth(width-18)
        row:SetShown(i<=count)
        if i<=count then
            row.label:SetText((item[1]==owner.value and "* " or "")..item[2])
        end
    end
    popup.previous:ClearAllPoints(); popup.previous:SetPoint("TOPLEFT",3,-count*27-7)
    popup.next:ClearAllPoints(); popup.next:SetPoint("TOPRIGHT",-3,-count*27-7)
    popup.previous.label:SetText(D.offset>0 and "< Previous" or "First page")
    popup.next.label:SetText(D.offset+count<#items and "Next >" or "Last page")
end
function D.Open(owner)
    if D.owner==owner and D.popup:IsShown() then D.Close(); return end
    D.Close()
    if #itemsFor(owner)==0 then U.Message("No debuffs observed yet. Apply a debuff once, then open this menu again."); return end
    local root=owner.root or U.frame
    if not D.popup then
        local p=U.Panel("Frame",root); D.popup=p
        p:SetFrameStrata("FULLSCREEN_DIALOG"); p:SetClampedToScreen(true); p:EnableMouse(true)
        p.previous=U.Button(p,"Previous",3,-3,110,function() D.offset=D.offset-PAGE; D.Render() end)
        p.next=U.Button(p,"Next",120,-3,110,function() D.offset=D.offset+PAGE; D.Render() end)
    end
    local p=D.popup
    p:Hide(); p:SetParent(root); p:SetFrameLevel(root:GetFrameLevel()+50)
    p:ClearAllPoints(); p:SetPoint("TOPLEFT",owner,"BOTTOMLEFT",0,-2)
    D.owner=owner; D.offset=0
    for i,item in ipairs(itemsFor(owner)) do if item[1]==owner.value then D.offset=math.floor((i-1)/PAGE)*PAGE; break end end
    D.Render(); p:Show()
end
function D.New(parent,x,y,width,items,changed,root)
    local b=U.Button(parent,"Choose…",x,y,width,function(self) D.Open(self) end)
    b.width,b.items,b.changed,b.root=width,items,changed,root
    b.label:SetWidth(width-30)
    b.arrow=U.Label(b,"v",width-18,-6,11,12)
    function b:SetValue(value)
        self.value=value
        for _, item in ipairs(itemsFor(self)) do
            if item[1]==value then self.label:SetText(item[2]); return end
        end
        self.label:SetText("Choose…")
    end
    return b
end
