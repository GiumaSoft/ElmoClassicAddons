local _, A = ...
local S = {}
A.Spells = S
local call, number, text, bool = A.Call, A.Number, A.Text, A.Bool

function S.Info(id)
    local info = call(C_Spell and C_Spell.GetSpellInfo, id)
    if not A.Secret(info) and type(info) == "table" and text(info.name) then
        return {id=number(info.spellID) or number(id), name=info.name, icon=number(info.iconID)}
    end
    local name, _, icon, _, _, _, spellID = call(GetSpellInfo, id)
    if text(name) then return {id=number(spellID) or number(id), name=name, icon=number(icon)} end
    call(C_Spell and C_Spell.RequestLoadSpellData, id)
end

local function known(id)
    local seen = false
    for _, fn in ipairs({C_SpellBook and C_SpellBook.IsSpellKnown or false,
        C_SpellBook and C_SpellBook.IsSpellInSpellBook or false, IsPlayerSpell or false, IsSpellKnown or false}) do
        local result = bool(call(fn, id))
        if result == true then return true end
        if result == false then seen = true end
    end
    if seen then return false end
end

local function cooldown(id)
    local info = call(C_Spell and C_Spell.GetSpellCooldown, id)
    if not A.Secret(info) and type(info) == "table" then
        return number(info.startTime), number(info.duration), bool(info.isEnabled)
    end
    local start, duration, enabled = call(GetSpellCooldown, id)
    if number(start) and number(duration) and not A.Secret(enabled) then
        return start, duration, enabled ~= 0 and enabled ~= false
    end
end

function S.Remaining(id)
    local start, duration, enabled = cooldown(id)
    if enabled == false then return end
    local object = call(C_Spell and C_Spell.GetSpellCooldownDuration, id, true)
    if not A.Secret(object) and object then
        local remaining = number(call(object.GetRemainingDuration, object))
        if remaining then return math.max(0, remaining) end
    end
    if not start or not duration then return end
    if duration <= 0 then return 0 end
    local globalStart, globalDuration = cooldown(61304)
    if globalStart and globalDuration and globalDuration > 0 and
        math.abs(start - globalStart) < .1 and math.abs(duration - globalDuration) < .05 then return 0 end
    return math.max(0, start + duration - GetTime())
end

function S.Ready(id)
    if known(id) == false then return false, "Spell not learned" end
    local usable, missing = call(C_Spell and C_Spell.IsSpellUsable or IsUsableSpell, id)
    usable, missing = bool(usable), bool(missing)
    if missing == true then return false, "Not enough mana / energy / rage" end
    if usable ~= true or missing == nil then return false, "Spell unavailable" end
    local charge = call(C_Spell and C_Spell.GetSpellCharges, id)
    if A.Secret(charge) then return false, "Charge data unavailable" end
    if type(charge) == "table" then
        local current, maximum = number(charge.currentCharges), number(charge.maxCharges)
        if not current or not maximum then return false, "Charge data unavailable" end
        if maximum and maximum > 0 then
            return current and current > 0 or false, current and current > 0 and "Ready" or "Recharging"
        end
    end
    local _, _, enabled = cooldown(id)
    if enabled == false then return false, "Cooldown on hold" end
    local remaining = S.Remaining(id)
    if not remaining then return false, "Cooldown data unavailable" end
    return remaining <= 0, remaining <= 0 and "Ready" or "On cooldown"
end

-- Options are built on panel open, not during combat priority evaluation.
function S.Book()
    local result, seen = {}, {}
    local function add(id)
        id=number(id)
        if not id or seen[id] then return end
        local info=S.Info(id)
        if info then result[#result+1]=info; seen[id]=true end
    end
    local modern=C_SpellBook and C_SpellBook.GetNumSpellBookSkillLines
    local tabs=number(call(modern or GetNumSpellTabs)) or 0
    for tab=1,math.min(tabs,50) do
        local offset,count
        if modern then
            local line=call(C_SpellBook.GetSpellBookSkillLineInfo,tab)
            if not A.Secret(line) and type(line)=="table" then offset,count=number(line.itemIndexOffset),number(line.numSpellBookItems) end
        else
            local _,_,o,n=call(GetSpellTabInfo,tab);offset,count=number(o),number(n)
        end
        if offset and count then
            for slot=offset+1,offset+math.min(count,500) do
                if modern then
                    local bank=Enum and Enum.SpellBookSpellBank and Enum.SpellBookSpellBank.Player or 0
                    local info=call(C_SpellBook.GetSpellBookItemInfo,slot,bank)
                    if not A.Secret(info) and type(info)=="table" and bool(info.isPassive)==false then add(info.spellID) end
                else
                    local kind,id=call(GetSpellBookItemInfo,slot,BOOKTYPE_SPELL or "spell")
                    if text(kind)=="SPELL" and bool(call(IsPassiveSpell,slot,BOOKTYPE_SPELL or "spell"))~=true then add(id) end
                end
            end
        end
    end
    return result
end
