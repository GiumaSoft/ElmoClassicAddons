local addonName,A=...
local f=CreateFrame("Frame")
A.frame=f
A.pending,A.orders,A.fullNotices={},{},{}
local sequence=0

local function wake()
    if not f:GetScript("OnUpdate") then
        f:SetScript("OnUpdate",function(_,elapsed) A.Tick(elapsed) end)
    end
end

function A.Refresh()
    if not A.db then return end
    A.UI.Layout()
    wake()
end

local function find(id,name)
    for i,known in ipairs(A.db.spells) do
        if known==id then return i end
        local info=A.Spells.Info(known)
        if info and name and info.name==name then return i end
    end
end

function A.AddSpell(id,info,order)
    local index=find(id,info.name)
    if index then
        local old=A.db.spells[index]
        local firstUse=A.orders[old] or order
        if old~=id then A.orders[old]=nil end
        A.orders[id]=firstUse
        A.db.spells[index]=id
        A.Refresh()
        return true
    end
    local spells=A.db.spells
    if #spells>=A.db.maxSkills then
        -- Delayed spell data must not displace the first-used ability with a later cast.
        local last=spells[#spells]
        if #spells>A.db.maxSkills or order>=(A.orders[last] or 0) then
            if not A.fullNotices[id] then
                A.fullNotices[id]=true
                A.Print("Bar full. "..(A.db.maxSkills<A.HARD_LIMIT and "Use /est max 12, or " or "")..
                    "Shift-right-click an icon while unlocked to free a slot.")
            end
            return false
        end
        A.orders[last]=nil;table.remove(spells)
    end
    A.orders[id]=order
    local at=#spells+1
    for i,known in ipairs(spells) do if (A.orders[known] or 0)>order then at=i;break end end
    table.insert(spells,at,id)
    A.Refresh()
    return true
end

function A.Observe(id)
    id=A.Number(id)
    if not A.db or not id or id<=0 or id%1~=0 or A.Spells.Excluded(id) then return end
    if not A.pending[id] then
        sequence=sequence+1
        A.pending[id]={order=sequence,expires=A.Now()+5}
    else A.pending[id].expires=A.Now()+5 end
    wake()
end

function A.ProcessPending()
    local pending={}
    for id,cast in pairs(A.pending) do pending[#pending+1]={id=id,cast=cast} end
    table.sort(pending,function(a,b) return a.cast.order<b.cast.order end)
    for _,entry in ipairs(pending) do
        local id,cast=entry.id,entry.cast
        local eligible,info=A.Spells.Eligible(id)
        if eligible then A.pending[id]=nil;A.AddSpell(id,info,cast.order)
        elseif eligible==false or A.Now()>=cast.expires then A.pending[id]=nil end
    end
end

function A.Tick(elapsed)
    A.elapsed=(A.elapsed or 0)+elapsed
    if A.elapsed<.1 then return end
    A.elapsed=0
    A.ProcessPending()
    local active=A.UI.Update()
    if not active and not next(A.pending) then f:SetScript("OnUpdate",nil) end
end

function A.SetMaxSkills(value)
    value=tonumber(value)
    if not value or value%1~=0 or value<1 or value>A.HARD_LIMIT then return false,"Enter a whole number from 1 to 12." end
    A.db.maxSkills=value
    A.fullNotices={}
    A.Refresh()
    return true,"Maximum skills: "..value.."."
end

function A.SetLocked(locked)
    A.db.locked=locked==true
    A.Refresh()
end

function A.Remove(index)
    index=tonumber(index)
    local id=index and A.db.spells[index]
    if not id then return false end
    table.remove(A.db.spells,index);A.orders[id]=nil;A.pending[id]=nil;A.fullNotices={}
    A.Refresh()
    return true
end

function A.Clear()
    A.db.spells={};A.pending={};A.orders={};A.fullNotices={}
    A.Refresh()
end

function A.Command(command)
    local name,value=(command or ""):match("^%s*(%S*)%s*(.-)%s*$")
    name=name:lower()
    if name=="max" or name=="limit" then
        local ok,message=A.SetMaxSkills(value);A.Print(message);return ok
    elseif name=="lock" then A.SetLocked(true)
    elseif name=="unlock" then A.SetLocked(false)
    elseif name=="reset" then A.Clear();A.Print("Tracked abilities cleared. They will be added again when used.")
    elseif name=="remove" then
        if not A.Remove(value) then A.Print("Use /est remove <icon number>.") end
    elseif name=="help" then
        A.Print("/est: settings · /est max 1–12 · /est lock · /est unlock · /est remove <number> · /est reset")
    elseif name=="" then A.UI.Settings()
    else A.Print("Unknown command. /est help") end
end

function A.Initialize()
    if A.db then return end
    if type(ElmoSpellTrackerDB)~="table" then
        ElmoSpellTrackerDB={}
    end
    A.db=ElmoSpellTrackerDB
    local limit=tonumber(A.db.maxSkills)
    A.db.maxSkills=limit and limit%1==0 and limit>=1 and limit<=A.HARD_LIMIT and limit or A.DEFAULT_LIMIT
    A.db.locked=A.db.locked==true
    local saved=type(A.db.spells)=="table" and A.db.spells or {}
    A.db.spells={}
    local seen,names={},{}
    for _,id in ipairs(saved) do
        id=A.Number(id)
        if id and id>0 and id%1==0 and not seen[id] and #A.db.spells<A.HARD_LIMIT then
            local info=A.Spells.Info(id)
            if not info or not names[info.name] then
                A.db.spells[#A.db.spells+1]=id
                sequence=sequence+1;A.orders[id]=sequence;seen[id]=true
                if info then names[info.name]=true end
            end
        end
    end
    A.UI.Create()
    A.UI.RegisterOptions()
    SLASH_ELMOSPELLTRACKER1="/elmospelltracker"; SLASH_ELMOSPELLTRACKER2="/est"
    SlashCmdList.ELMOSPELLTRACKER=A.Command
    A.Refresh()
end

f:SetScript("OnEvent",function(_,event,...)
    if event=="ADDON_LOADED" then if (...)==addonName then A.Initialize() end;return end
    if event=="PLAYER_LOGIN" then A.Initialize();A.Refresh();return end
    if not A.db then return end
    if event=="UNIT_SPELLCAST_SUCCEEDED" then
        local unit,_,id=...
        if A.Text(unit)=="player" then A.Observe(id) end
    elseif event=="SPELL_DATA_LOAD_RESULT" or event=="SPELLS_CHANGED" or event=="PLAYER_ENTERING_WORLD" then
        A.Refresh()
    elseif event=="UNIT_POWER_UPDATE" or event=="UNIT_MAXPOWER" or event=="UNIT_DISPLAYPOWER" then
        if (...)=="player" then wake() end
    else wake() end
end)
f:RegisterEvent("ADDON_LOADED")
f:RegisterEvent("PLAYER_LOGIN")
f:RegisterEvent("PLAYER_ENTERING_WORLD")
f:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED","player")
for _,event in ipairs({"UNIT_POWER_UPDATE","UNIT_MAXPOWER","UNIT_DISPLAYPOWER"}) do
    f:RegisterUnitEvent(event,"player")
end
for _,event in ipairs({"SPELL_UPDATE_COOLDOWN","SPELL_UPDATE_CHARGES","SPELL_UPDATE_USABLE","SPELLS_CHANGED","SPELL_DATA_LOAD_RESULT"}) do
    A.Call(f.RegisterEvent,f,event)
end
