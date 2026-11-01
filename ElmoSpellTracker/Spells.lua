local _,A=...
local S={requested={}}
A.Spells=S
local call,num,txt,bool=A.Call,A.Number,A.Text,A.Bool
local GCD=61304

function S.Request(id)
    if not S.requested[id] then
        S.requested[id]=true
        call(C_Spell and C_Spell.RequestLoadSpellData,id)
    end
end

function S.Info(id)
    local info=call(C_Spell and C_Spell.GetSpellInfo,id)
    if not A.Secret(info) and type(info)=="table" and txt(info.name) then
        return {id=id,name=info.name,icon=num(info.iconID) or num(info.originalIconID)}
    end
    local name,_,icon=call(GetSpellInfo,id)
    if txt(name) then return {id=id,name=name,icon=num(icon)} end
    S.Request(id)
end

function S.Known(id)
    local seen=false
    for _,fn in ipairs({C_SpellBook and C_SpellBook.IsSpellKnown or false,
        C_SpellBook and C_SpellBook.IsSpellInSpellBook or false,
        IsPlayerSpell or false,IsSpellKnown or false}) do
        local value=bool(call(fn,id))
        if value==true then return true end
        if value==false then seen=true end
    end
    if seen then return false end
end

function S.Excluded(id)
    if id==GCD or S.Known(id)==false then return true end
    for _,fn in ipairs({C_Spell and C_Spell.IsAutoAttackSpell or IsAutoAttackSpell or false,
        C_Spell and C_Spell.IsAutoRepeatSpell or IsAutoRepeatSpell or false,
        C_Spell and C_Spell.IsSpellPassive or IsPassiveSpell or false}) do
        if bool(call(fn,id))==true then return true end
    end
    return false
end

function S.InsufficientPower(id)
    local _, missing = call(C_Spell and C_Spell.IsSpellUsable, id)
    if bool(missing) == nil then _, missing = call(IsUsableSpell, id) end
    return bool(missing) == true
end

local function cooldown(id)
    local info=call(C_Spell and C_Spell.GetSpellCooldown,id)
    if not A.Secret(info) and type(info)=="table" then
        return {start=num(info.startTime),duration=num(info.duration),enabled=bool(info.isEnabled),active=bool(info.isActive)}
    end
    local start,duration,enabled=call(GetSpellCooldown,id)
    if num(start) and num(duration) then
        return {start=start,duration=duration,enabled=not A.Secret(enabled) and enabled~=0 and enabled~=false}
    end
end

local function charges(id)
    local info=call(C_Spell and C_Spell.GetSpellCharges,id)
    if not A.Secret(info) and type(info)=="table" then
        return {current=num(info.currentCharges),max=num(info.maxCharges),
            start=num(info.cooldownStartTime),duration=num(info.cooldownDuration)}
    end
    local current,max,start,duration=call(GetSpellCharges,id)
    if num(max) then return {current=num(current),max=max,start=num(start),duration=num(duration)} end
end

local function remaining(object)
    if not A.Secret(object) and object then return num(call(object.GetRemainingDuration,object)) end
end

local function gcdOnly(info)
    local global=cooldown(GCD)
    if not info.start or not info.duration or not global or not global.start or not global.duration then
        return info.duration and info.duration<=1.5
    end
    if global.duration>0 and math.abs(info.duration-global.duration)<.05
        and math.abs(info.start-global.start)<.1 then return true end
    return false
end

function S.Status(id)
    local info=cooldown(id)
    local charge=charges(id)
    local base=num(call(C_Spell and C_Spell.GetSpellBaseCooldown or GetSpellBaseCooldown,id))
    local hasBase=base and base>0 or false
    if charge and charge.max and charge.max>0 and charge.current then
        if charge.current>0 then return {remaining=0,hasCooldown=true,charges=charge.current} end
        local value=remaining(call(C_Spell and C_Spell.GetSpellChargeDuration,id))
        if not value and charge.start and charge.duration then value=charge.start+charge.duration-A.Now() end
        return {remaining=value and math.max(0,value),hasCooldown=true,charges=0}
    end
    -- Era 1.15.9 exposes an authoritative remaining duration excluding the GCD.
    -- Do not trust isOnGCD outside a SPELL_UPDATE_COOLDOWN callback.
    local value=remaining(call(C_Spell and C_Spell.GetSpellCooldownDuration,id,true))
    if info and info.enabled==false then
        return {remaining=0,hasCooldown=true,paused=true}
    end
    if value then
        value=math.max(0,value)
        return {remaining=value,hasCooldown=hasBase or value>0}
    end
    if not info or not info.start or not info.duration then return {hasCooldown=hasBase} end
    if info.duration<=0 or info.active==false then return {remaining=0,hasCooldown=hasBase} end
    if gcdOnly(info) then return {remaining=0,hasCooldown=hasBase} end
    value=math.max(0,info.start+info.duration-A.Now())
    return {remaining=value,hasCooldown=hasBase or value>0}
end

function S.Eligible(id)
    if S.Excluded(id) then return false end
    local info=S.Info(id)
    if not info then return nil end
    local status=S.Status(id)
    if status.hasCooldown then return true,info end
    -- The cooldown can arrive after UNIT_SPELLCAST_SUCCEEDED. Keep the cast pending.
    return nil,info
end
