local addonName, A = ...
ElmoBuff = A
A.version = "1.0.2"
A.units = {"player","party1","party2","party3","party4"}
local frame, elapsed = CreateFrame("Frame"), 0
local function checked(ok, ...) if ok then return ... end end
function A.Call(fn, ...) if type(fn)=="function" then return checked(pcall(fn,...)) end end
function A.Private(v)
    return type(issecretvalue)=="function" and issecretvalue(v) or
        type(canaccessvalue)=="function" and not canaccessvalue(v)
end
function A.Text(v) if not A.Private(v) and type(v)=="string" then return v end end
function A.Number(v)
    if not A.Private(v) and type(v)=="number" and v==v and v~=math.huge and v~=-math.huge then return v end
end
function A.Bool(v) if not A.Private(v) and type(v)=="boolean" then return v end end
function A.Table(v)
    if not A.Private(v) and type(v)=="table" and (type(canaccesstable)~="function" or canaccesstable(v)) then return v end
end
function A.Print(text) DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoBuff:|r "..text) end

function A.Auras(unit)
    -- Never probe restricted auras or turn an unknown result into "missing".
    if InCombatLockdown() or A.Bool(A.Call(C_Secrets and C_Secrets.ShouldAurasBeSecret))==true then return end
    local result, complete = {}, true
    local function add(data)
        data=A.Table(data)
        if not data then complete=false;return end
        local name=A.Text(data.name)
        if not name then complete=false;return end
        local source=A.Text(data.sourceUnit)
        result[#result+1]={name=name,id=A.Number(data.spellId),expires=A.Number(data.expirationTime),
            mine=source=="player" or source and A.Bool(A.Call(UnitIsUnit,source,"player"))==true}
    end
    if C_UnitAuras and type(C_UnitAuras.GetUnitAuras)=="function" then
        local ok, raw=pcall(C_UnitAuras.GetUnitAuras,unit,"HELPFUL",255)
        local data=ok and A.Table(raw)
        if not data then return end
        for i=1,math.min(#data,255) do add(data[i]) end
    else
        for i=1,255 do
            if C_UnitAuras and type(C_UnitAuras.GetAuraDataByIndex)=="function" then
                local ok,data=pcall(C_UnitAuras.GetAuraDataByIndex,unit,i,"HELPFUL")
                if not ok or A.Private(data) then return end
                if data==nil then break end
                add(data)
            elseif type(UnitBuff)=="function" then
                local ok,name,_,_,_,_,expires,source,_,_,id=pcall(UnitBuff,unit,i)
                if not ok or A.Private(name) then return end
                if name==nil then break end
                add({name=name,spellId=id,sourceUnit=source,expirationTime=expires})
            else return end
        end
    end
    return result, complete
end

function A.BuffState(f, auras, complete, spell)
    if not auras then return "unknown" end
    local remaining, uncertainConflict
    for _,aura in ipairs(auras) do
        local seconds=aura.expires and aura.expires>0 and math.max(0,aura.expires-GetTime())
        if f.names[aura.name] then
            -- A permanent or unreadable duration is still a positively identified buff.
            if not seconds then return "active" end
            if seconds>0 then
                -- Never replace a group buff, another rank, or another caster's
                -- potentially talent-improved buff just because it expires soon.
                -- Only our exact cast rank is safe to refresh in advance.
                if not aura.mine or not spell or aura.id~=spell.id then return "covered",seconds end
                remaining=math.max(remaining or 0,seconds)
            end
        elseif f.exclusive and (not seconds or seconds>0) then
            for _,other in ipairs(A.Spells.families) do
                if other~=f and other.exclusive==f.exclusive and other.names[aura.name] then
                    -- Some groups conflict only for the same caster. Unknown
                    -- ownership must not enable a potentially destructive cast.
                    if not f.exclusiveByCaster or aura.mine==true then return "covered",seconds end
                    if aura.mine==nil then uncertainConflict=true end
                end
            end
        end
    end
    if uncertainConflict then return "unknown" end
    if remaining then
        if remaining<=A.db.refresh and not complete then return "unknown" end
        return remaining<=A.db.refresh and "refresh" or "active",remaining
    end
    return complete and "missing" or "unknown"
end

local manaClasses={PRIEST=true,MAGE=true,WARLOCK=true,DRUID=true,SHAMAN=true,PALADIN=true,HUNTER=true}
function A.UnitState(unit)
    if A.Bool(A.Call(UnitExists,unit))~=true then return "absent" end
    if A.Bool(A.Call(UnitIsConnected,unit))~=true then return "offline" end
    if A.Bool(A.Call(UnitIsDeadOrGhost,unit))~=false then return "dead" end
    if A.Bool(A.Call(UnitCanAssist,"player",unit))~=true then return "unavailable" end
    return "ready"
end

function A.Update()
    if not A.db or not A.UI.root or InCombatLockdown() then return end
    A.counts={missing=0,refresh=0,unknown=0,covered=0}
    local raid=A.Bool(A.Call(IsInRaid))==true
    for index,unit in ipairs(A.units) do
        local host=A.UI.Host(unit)
        local viable=A.UnitState(unit)
        local hostShown=host and A.UI.Visible(host)
        local show=A.db.enabled and not raid and (unit~="player" or A.db.self) and viable~="absent" and hostShown
        local auras,complete
        if show and viable=="ready" then auras,complete=A.Auras(unit) end
        local _,class=A.Call(UnitClass,unit);class=A.Text(class)
        local visible=0
        for column,b in ipairs(A.UI.groups[index].buttons) do
            local f=A.Spells.active[column]
            local spell=f and A.Spells.ForUnit(f,unit)
            local state,remaining="inactive",nil
            if show and f and spell and A.db.buffs[f.key] and viable=="ready" then
                if f.mana and not manaClasses[class] then state="ineligible"
                else state,remaining=A.BuffState(f,auras,complete,spell) end
            end
            local need=state=="missing" or state=="refresh"
            if state=="unknown" then A.counts.unknown=A.counts.unknown+1 end
            if state=="covered" then A.counts.covered=A.counts.covered+1 end
            if need then A.counts[state]=A.counts[state]+1 end
            if need then
                visible=visible+1
                A.UI.Anchor(b,host,visible)
            end
            local range=spell and A.Spells.Range(spell,unit)
            A.UI.Configure(b,unit,f,spell,need,state,remaining,range)
        end
    end
end

function A.RefreshSpells()
    if InCombatLockdown() then A.pending=true;return end
    A.Spells.Refresh()
    A.Update()
end

function A.Command(command)
    command=(command or ""):lower():match("^%s*(.-)%s*$")
    if command=="on" or command=="off" then
        A.db.enabled=command=="on";A.Update()
    elseif command=="status" then
        local c=A.counts or {}
        A.Print("Missing: "..(c.missing or 0).."; expiring: "..(c.refresh or 0).."; covered: "..(c.covered or 0).."; unreadable: "..(c.unknown or 0)..
            ". Rebuff icons update outside combat.")
    else A.Settings.Open() end
end

local function initialize()
    if A.db then return end
    ElmoBuffDB=type(ElmoBuffDB)=="table" and ElmoBuffDB or {}
    A.db=ElmoBuffDB
    for _,key in ipairs({"enabled","self"}) do if type(A.db[key])~="boolean" then A.db[key]=true end end
    A.db.buffs=type(A.db.buffs)=="table" and A.db.buffs or {}
    A.db.refresh=math.max(0,math.min(600,A.Number(A.db.refresh) or 60))
    A.db.side=A.db.side=="LEFT" and "LEFT" or A.db.side=="ABOVE" and "ABOVE" or "RIGHT"
    A.db.size=math.max(20,math.min(40,A.Number(A.db.size) or 28))
    A.Settings.Register()
    SLASH_ELMOBUFF1,SLASH_ELMOBUFF2="/ebuff","/elmobuff";SlashCmdList.ELMOBUFF=A.Command
    if not InCombatLockdown() then A.Spells.Refresh();A.UI.Create();A.Update() end
    A.Print("Loaded "..A.version..". Missing-buff icons appear beside party members. /ebuff: options.")
end

frame:SetScript("OnEvent",function(_,event,unit)
    if event=="ADDON_LOADED" then if unit==addonName then initialize() end;return end
    if not A.db then return end
    if InCombatLockdown() then
        if event=="SPELLS_CHANGED" or event=="LEARNED_SPELL_IN_TAB" then A.pending=true end
        return
    end
    if not A.UI.root then A.Spells.Refresh();A.UI.Create() end
    if event=="SPELLS_CHANGED" or event=="LEARNED_SPELL_IN_TAB" or event=="PLAYER_REGEN_ENABLED" or event=="PLAYER_ENTERING_WORLD" then
        A.pending=nil;A.Spells.Refresh()
    end
    A.Update()
end)
for _,event in ipairs({"ADDON_LOADED","PLAYER_ENTERING_WORLD","GROUP_ROSTER_UPDATE","UNIT_AURA",
    "UNIT_CONNECTION","UNIT_FLAGS","UNIT_LEVEL","SPELLS_CHANGED","LEARNED_SPELL_IN_TAB",
    "PLAYER_REGEN_ENABLED","PLAYER_REGEN_DISABLED","EDIT_MODE_LAYOUTS_UPDATED","CVAR_UPDATE"}) do
    A.Call(frame.RegisterEvent,frame,event)
end
frame:SetScript("OnUpdate",function(_,delta)
    elapsed=elapsed+delta
    if elapsed>=.5 then elapsed=0;A.Update() end
end)
