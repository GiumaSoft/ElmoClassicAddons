local _, A = ...
local C = {}
A.Conditions = C
C.metrics = {
    {"health_pct", "Target health %"}, {"health", "Target remaining HP"},
    {"player_health", "Player health %"}, {"mana", "Player mana"},
    {"rage", "Player rage"}, {"energy", "Player energy"},
    {"enemies", "Engaged mobs"}, {"missing", "Mobs needing this debuff"},
    {"covered", "Active configured debuffs"}, {"aura", "Own debuff present (1/0)"},
    {"remaining", "Own debuff remaining (sec)"}, {"stacks", "Own debuff stacks"},
    {"cooldown", "Spell cooldown (sec)"}, {"combat", "Player in combat (1/0)"},
}
C.operators = {"<", "<=", ">", ">=", "==", "~="}
local metrics, operators = {}, {}
for _, item in ipairs(C.metrics) do metrics[item[1]] = true end
for _, item in ipairs(C.operators) do operators[item] = true end

function C.Validate(rows)
    if rows == nil then return {} end
    if type(rows) ~= "table" then return nil, "Invalid condition list." end
    local clean, depth = {}, 0
    for i, row in ipairs(rows) do
        if type(row) ~= "table" or not metrics[row.metric] or not operators[row.op] then
            return nil, "Condition " .. i .. ": choose a valid type and operator."
        end
        local value, opens, closes, id = tonumber(row.value), tonumber(row.opens or 0),
            tonumber(row.closes or 0), tonumber(row.spellID or 0)
        if not A.Number(value) or value < 0 or value > 1000000000 then return nil, "Condition " .. i .. ": invalid value." end
        if not A.Number(opens) or not A.Number(closes) or opens % 1 ~= 0 or closes % 1 ~= 0 or
            opens < 0 or closes < 0 or opens > 3 or closes > 3 then return nil, "Use 0–3 parentheses per row." end
        if not A.Number(id) or id % 1 ~= 0 or id < 0 or id > 10000000 then return nil, "Invalid condition spell ID." end
        if i > 1 and row.join ~= "AND" and row.join ~= "OR" then return nil, "Choose AND or OR." end
        depth = depth + opens - closes
        if depth < 0 then return nil, "A closing parenthesis has no opening parenthesis." end
        clean[i] = {metric=row.metric, op=row.op, value=value, opens=opens, closes=closes,
            spellID=id, join=i == 1 and "AND" or row.join}
    end
    if depth ~= 0 then return nil, "Close all open parentheses before saving." end
    return clean
end

local function percent(unit)
    local hp, maximum = A.Number(A.Call(UnitHealth, unit)), A.Number(A.Call(UnitHealthMax, unit))
    if hp and maximum and maximum > 0 then return hp / maximum * 100 end
end
local function metric(row, record, rule, context)
    local key = row.metric
    if key == "health_pct" then return record.fraction <= 1 and record.fraction * 100 or nil end
    if key == "health" then return A.Number(record.health) end
    if key == "player_health" then return percent("player") end
    if key == "enemies" then return context.enemies end
    if key == "missing" then return context.missing end
    if key == "covered" then return record.covered end
    if key == "mana" or key == "rage" or key == "energy" then
        local power = {mana=0, rage=1, energy=3}
        return A.Number(A.Call(UnitPower, "player", power[key]))
    end
    if key == "combat" then
        local value = A.Bool(A.Call(UnitAffectingCombat, "player"))
        if value ~= nil then return value and 1 or 0 end
    elseif key == "cooldown" then
        if row.spellID == 0 and rule.kind ~= "debuff" then return end
        return A.Spells.Remaining(row.spellID > 0 and row.spellID or rule.spellID)
    else
        if row.spellID == 0 and rule.kind ~= "debuff" then return end
        if record.aurasKnown == false then return end
        local auraRule = rule
        if row.spellID > 0 then auraRule = {auraID=row.spellID, spellID=row.spellID} end
        local aura = A.Rules.Aura(record, auraRule)
        if key == "aura" then return aura and 1 or 0 end
        if not aura then return 0 end
        if key == "stacks" then return aura.count end
        if key == "remaining" and aura.expires > 0 then return math.max(0, aura.expires - context.now) end
    end
end
local function compare(value, op, threshold)
    if not A.Number(value) then return false end -- private/unknown data never satisfies a comparison
    if op == "<" then return value < threshold end
    if op == "<=" then return value <= threshold end
    if op == ">" then return value > threshold end
    if op == ">=" then return value >= threshold end
    if op == "==" then return value == threshold end
    if op == "~=" then return value ~= threshold end
    return false
end
local precedence = {OR=1, AND=2}
-- Evaluate validated data, never Lua expressions from saved variables.
function C.Match(rows, record, rule, context)
    if not rows or #rows == 0 then return true end
    local values, ops = {}, {}
    local function reduce()
        local op = table.remove(ops)
        local right, left = table.remove(values), table.remove(values)
        if op == "AND" then values[#values+1] = left and right else values[#values+1] = left or right end
    end
    for i, row in ipairs(rows) do
        if i > 1 then
            while #ops > 0 and ops[#ops] ~= "(" and precedence[ops[#ops]] >= precedence[row.join] do reduce() end
            ops[#ops+1] = row.join
        end
        for _=1,row.opens do ops[#ops+1] = "(" end
        values[#values+1] = compare(metric(row, record, rule, context), row.op, row.value)
        for _=1,row.closes do
            while ops[#ops] ~= "(" do reduce() end
            table.remove(ops)
        end
    end
    while #ops > 0 do reduce() end
    return values[1] == true
end
