local _, A = ...
function A.MigrateSettings()
    if type(ElmoLevelingDB) == "table" then return end
    local forever = A.flavor == "forever"
    local db = forever and ClassicLevelingForeverDB or (not forever and ClassicLevelingDB)
    if type(db) ~= "table" then
        local folder = forever and "ForeverLeveling" or "ClassicXPTracker"
        local variable = forever and "ForeverLevelingTrackerDB" or "ClassicXPTrackerDB"
        local metadata = C_AddOns and C_AddOns.GetAddOnMetadata or GetAddOnMetadata
        local allowed = not forever or A.Call(metadata, folder, "X-ClassicLevelingForever-Legacy") == "1"
        if allowed then
            if type(_G[variable]) ~= "table" then
                local load = C_AddOns and C_AddOns.LoadAddOn or LoadAddOn
                if type(load) == "function" then pcall(load, folder) end
            end
            if type(_G[variable]) == "table" then db = _G[variable]; A.migratedLegacy = true end
        end
    end
    ElmoLevelingDB = type(db) == "table" and db or {}
end
_G.ClassicLeveling = A
_G.ClassicLevelingForever = A
