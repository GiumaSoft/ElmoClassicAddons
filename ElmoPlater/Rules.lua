local _, A = ...
local R = {}
A.Rules = R
R.kinds = {{"debuff","Missing debuff"},{"health_below","Health below threshold"},{"lowest_health","Lowest health (attacked mobs)"}}

local function integer(value, minimum, maximum)
    value = tonumber(value)
    return A.Number(value) and value % 1 == 0 and value >= minimum and value <= maximum and value
end
function R.New(kind)
    return {kind=kind,spellID=0,auraID=0,enabled=true,aoe=false,minEnemies=1,minMissing=1,
        minHealth=0,maxHealth=100,threshold=20,refresh=0,preferCovered=false,conditions={}}
end
function R.Validate(rule)
    local kind=rule.kind or "debuff" -- v1 saved rules only described debuffs
    if kind~="debuff" and kind~="health_below" and kind~="lowest_health" then return nil,"Choose a valid rule type." end
    local result={kind=kind}
    for key,bounds in pairs({minEnemies={1,40},minMissing={1,40},minHealth={0,100},maxHealth={0,100}}) do
        result[key]=integer(rule[key],bounds[1],bounds[2])
        if not result[key] then return nil,key..": enter a whole number from "..bounds[1].." to "..bounds[2] end
    end
    result.threshold=integer(rule.threshold or 20,0,100)
    if not result.threshold then return nil,"Health threshold must be 0–100%." end
    result.spellID,result.auraID=0,0
    if kind=="debuff" then
        result.spellID,result.auraID=integer(rule.spellID,1,10000000),integer(rule.auraID,0,10000000)
        if not result.spellID or not result.auraID then return nil,"Choose an ability and a debuff." end
    end
    result.refresh=tonumber(rule.refresh)
    if not A.Number(result.refresh) or result.refresh<0 or result.refresh>60 then return nil,"Refresh threshold must be 0–60 seconds." end
    if result.minHealth>result.maxHealth then return nil,"Minimum health must not exceed maximum health." end
    result.enabled,result.aoe,result.preferCovered=rule.enabled==true,rule.aoe==true,rule.preferCovered==true
    local err
    result.conditions,err=A.Conditions.Validate(rule.conditions)
    if not result.conditions then return nil,err end
    return result
end
function R.Initialize()
    A.db.learnedDebuffs=type(A.db.learnedDebuffs)=="table" and A.db.learnedDebuffs or {}
    local rules={}
    for _,rule in ipairs(type(A.db.rules)=="table" and A.db.rules or {}) do
        if type(rule)=="table" then local clean=R.Validate(rule);if clean then rules[#rules+1]=clean end end
    end
    A.db.rules=rules
    if A.db.ruleSchema~=2 then
        if A.db.ruleSchema~=1 and #rules==0 and A.db.watchDebuff~="" then
            local info=A.Spells.Info(A.db.watchDebuff)
            if info and info.id then R.Add(info.id) end
        end
        -- Replace the former implicit priorities with ordinary, editable rules once.
        table.insert(rules,1,R.New("health_below"))
        rules[#rules+1]=R.New("lowest_health")
        A.db.ruleSchema=2
    end
end
function R.Observe(id,name,icon)
    id,name,icon=A.Number(id),A.Text(name),A.Number(icon)
    if not id or id<=0 or id%1~=0 or not name then return end
    local old=A.db.learnedDebuffs[id]
    if type(old)=="table" and old.name==name and old.icon==icon then return end
    A.db.learnedDebuffs[id]={id=id,name=name,icon=icon}
    if A.Settings then A.Settings.dirty=true end
end
function R.Add(value)
    local rule
    if value=="health_below" or value=="lowest_health" then rule=R.New(value)
    else
        local id=integer(value,1,10000000)
        if not id then return nil,"Choose a rule from the New rule menu." end
        local info=A.Spells.Info(id)
        if not info and not A.db.learnedDebuffs[id] then return nil,"Spell data is loading. Try again." end
        rule=R.New("debuff");rule.spellID,rule.auraID,rule.preferCovered=id,id,true
    end
    A.db.rules[#A.db.rules+1]=rule
    return #A.db.rules
end
function R.Move(index,direction)
    local other=index+direction
    if not A.db.rules[index] or not A.db.rules[other] then return index end
    A.db.rules[index],A.db.rules[other]=A.db.rules[other],A.db.rules[index]
    return other
end
function R.Name(rule)
    if rule.kind=="health_below" then return "Health < "..rule.threshold.."%" end
    if rule.kind=="lowest_health" then return "Lowest health (attacked mobs)" end
    local id=rule.auraID>0 and rule.auraID or rule.spellID
    local observed=A.db.learnedDebuffs[id]
    local info=A.Spells.Info(id)
    return info and info.name or type(observed)=="table" and A.Text(observed.name) or "Spell #"..id
end
function R.Aura(record,rule)
    local name=R.Name(rule)
    for _,aura in ipairs(record.auras) do
        if rule.auraID>0 and aura.id==rule.auraID or name and A.Text(aura.name) and aura.name:lower()==name:lower() then return aura end
    end
end
function R.Missing(record,rule,now)
    if record.aurasKnown==false then return false end
    local aura=R.Aura(record,rule)
    if not aura then return true end
    return rule.refresh>0 and aura.expires>0 and aura.expires-now<=rule.refresh
end
local function lowest(a,b)
    return not b or a.health<b.health or a.health==b.health and a.guid<b.guid
end
-- Every priority is represented by a saved rule. No critical-health gate or HP fallback.
function R.Choose(list,now)
    local engaged={}
    for _,record in ipairs(list) do
        record.suggestedRule,record.covered=nil,0
        if A.attacked[record.guid] and A.Number(record.health) and record.fraction<=1 and
            A.Bool(A.Call(UnitCanAttack,"player",record.unit))==true then
            engaged[#engaged+1]=record
            local seen={}
            for _,rule in ipairs(A.db.rules) do
                local aura=rule.enabled and rule.kind=="debuff" and R.Aura(record,rule)
                if aura then
                    local key=aura.id or aura.name
                    if key and not seen[key] then record.covered=record.covered+1;seen[key]=true end
                end
            end
        end
    end
    for index,rule in ipairs(A.db.rules) do
        local debuff=rule.kind=="debuff"
        if rule.enabled and #engaged>=rule.minEnemies and (not debuff or A.Spells.Ready(rule.spellID)) then
            local missing
            if debuff then
                missing=0
                for _,record in ipairs(engaged) do if R.Missing(record,rule,now) then missing=missing+1 end end
            end
            if not debuff or missing>=rule.minMissing then
                local context={enemies=#engaged,missing=missing,now=now}
                local best
                for _,record in ipairs(engaged) do
                    local hp=record.fraction*100
                    local applies=not debuff or R.Missing(record,rule,now)
                    if rule.kind=="health_below" then applies=hp<rule.threshold end
                    if applies and hp>=rule.minHealth and hp<=rule.maxHealth and
                        A.Conditions.Match(rule.conditions,record,rule,context) then
                        if not best or (debuff and rule.preferCovered and record.covered>best.covered) or
                            (not debuff or not rule.preferCovered or record.covered==best.covered) and lowest(record,best) then best=record end
                    end
                end
                if best then best.suggestedRule=index;return best,index end
            end
        end
    end
end
