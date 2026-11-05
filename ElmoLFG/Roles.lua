local _, A = ...

local order = { "Tank", "Healer", "DPS" }
local capacity = { Tank = 1, Healer = 1, DPS = 3 }
local labels = { Tank = "Tank", Healer = "Heal", DPS = "Dps" }
local aliases = { tank = "Tank", heal = "Healer", healer = "Healer", dps = "DPS", damager = "DPS", damage = "DPS" }
local pureDPS = { MAGE = true, ROGUE = true, HUNTER = true, WARLOCK = true }
A.memberRoles, A.pendingRoles = {}, {}

function A.CanonicalRole(role)
    return type(role) == "string" and aliases[role:lower()] or nil
end

function A.RoleLabel(role) return labels[role] or "Unknown" end

function A.SetPlayerRole(role)
    A.db.playerRole = A.CanonicalRole(role)
    A.db.roles = A.db.playerRole and { [A.db.playerRole] = true } or {}
end

function A.NameKey(name)
    local player, realm = name:match("^([^%-]+)%-(.+)$")
    if not player then
        player = name
        realm = (GetNormalizedRealmName and GetNormalizedRealmName()) or (GetRealmName and GetRealmName())
    end
    return player:lower() .. (realm and ("-" .. realm:lower():gsub("%s", "")) or "")
end

local function FullName(unit)
    local name, realm
    if UnitFullName then name, realm = UnitFullName(unit) else name, realm = UnitName(unit) end
    if not name then return end
    return realm and realm ~= "" and (name .. "-" .. realm) or name
end

function A.IsSelf(name)
    local me = FullName("player")
    return me and A.NameKey(name) == A.NameKey(me)
end

function A.HasSelectedDungeon()
    for _, dungeon in ipairs(A.AvailableDungeons()) do
        if A.db.selected["d:" .. dungeon.id] then return true end
    end
    return false
end

function A.RecruitmentTarget()
    return A.HasSelectedDungeon() and math.min(5, A.db.stopAtPlayers) or A.db.stopAtPlayers
end

function A.GroupRoster()
    local roster, seen = {}, {}
    local playerGUID = UnitGUID and UnitGUID("player")
    local function add(unit)
        local name = FullName(unit)
        if not name then return end
        local guid = UnitGUID and UnitGUID(unit)
        local nameKey = A.NameKey(name)
        local key = guid or nameKey
        if seen[key] then return end
        seen[key] = true
        roster[#roster + 1] = { unit = unit, name = name, nameKey = nameKey, key = key,
            isPlayer = unit == "player" or (guid and guid == playerGUID) or false }
    end
    add("player")
    if IsInRaid() then
        for i = 1, GetNumGroupMembers() do add("raid" .. i) end
    elseif IsInGroup() then
        for i = 1, math.min(4, GetNumGroupMembers() - 1) do add("party" .. i) end
    end
    return roster
end

local function MemberRole(member)
    if member.isPlayer and A.db.playerRole then return A.db.playerRole end
    if A.memberRoles[member.key] then return A.memberRoles[member.key] end
    if UnitGroupRolesAssigned then
        local ok, role = pcall(UnitGroupRolesAssigned, member.unit)
        if ok and A.CanonicalRole(role) then return A.CanonicalRole(role) end
    end
    local _, class = UnitClass(member.unit)
    if pureDPS[class] then return "DPS" end
end

function A.SyncGroupRoles()
    local roster, present, joined = A.GroupRoster(), {}, {}
    for _, member in ipairs(roster) do
        present[member.key], joined[member.nameKey] = true, true
        local pending = A.pendingRoles[member.nameKey]
        if pending then
            A.memberRoles[member.key] = pending.role
            A.pendingRoles[member.nameKey] = nil
        end
    end
    -- A loading roster is not proof that a member has left.
    if #roster == A.GroupSize() then
        for key in pairs(A.memberRoles) do if not present[key] then A.memberRoles[key] = nil end end
    end
    for key, pending in pairs(A.pendingRoles) do
        if not joined[key] and GetTime() - pending.time >= 120 then A.pendingRoles[key] = nil end
    end
    for _, member in ipairs(roster) do member.role = MemberRole(member) end
    return roster
end

function A.SetMemberRole(key, role)
    role = A.CanonicalRole(role)
    for _, member in ipairs(A.GroupRoster()) do
        if member.key == key then
            if member.isPlayer then A.SetPlayerRole(role) else A.memberRoles[key] = role end
            return true
        end
    end
    return false
end

function A.RecordMemberRole(name, role)
    local key = A.NameKey(name)
    for _, member in ipairs(A.GroupRoster()) do
        if member.nameKey == key then return A.SetMemberRole(member.key, role) end
    end
    return false
end

function A.GroupComposition()
    local roster = A.SyncGroupRoles()
    local result = { roster = roster, have = { Tank = 0, Healer = 0, DPS = 0 }, missing = {},
        unknown = math.max(0, A.GroupSize() - #roster), free = math.max(0, 5 - A.GroupSize()) }
    for _, member in ipairs(roster) do
        if member.role then result.have[member.role] = result.have[member.role] + 1
        else result.unknown = result.unknown + 1 end
    end
    for _, role in ipairs(order) do result.missing[role] = math.max(0, capacity[role] - result.have[role]) end
    return result
end

function A.DungeonRoleText(separator)
    local group = A.GroupComposition()
    if group.unknown > 0 then return group.free .. " slots (assign group roles)" end
    local parts, count = {}, 0
    for _, role in ipairs(order) do
        local missing = group.missing[role]
        count = count + missing
        if missing > 0 then parts[#parts + 1] = missing .. " " .. labels[role] end
    end
    if count ~= group.free then return group.free .. " slots (check group roles)" end
    return #parts > 0 and table.concat(parts, separator or "/") or "0 slots"
end

function A.WhisperRole(message)
    local found
    for word in A.Normalize(message):gmatch("%S+") do
        local role = aliases[word]
        if role then
            if found and found ~= role then return nil, "specify one role: inv tank, inv heal or inv dps." end
            found = role
        end
    end
    return found, "whisper inv tank, inv heal or inv dps to join a dungeon."
end

function A.CanInviteRole(role, sender)
    local group = A.GroupComposition()
    local reserved, total = 0, 0
    local senderKey = A.NameKey(sender)
    for key, pending in pairs(A.pendingRoles) do
        if key ~= senderKey then
            total = total + 1
            if pending.role == role then reserved = reserved + 1 end
        end
    end
    if A.GroupSize() + total >= A.RecruitmentTarget() then return false, "the remaining places have pending invitations." end
    if group.missing[role] <= reserved then return false, "no open " .. A.RoleLabel(role) .. " place." end
    return true
end
