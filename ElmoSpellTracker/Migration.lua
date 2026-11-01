local _, A = ...
function A.MigrateSettings()
    if type(ElmoSpellTrackerDB) ~= "table" then
        if type(ElmoSpellTrackerDB) ~= "table" and type(ClassicSpellsTrackerDB) == "table" then ElmoSpellTrackerDB = ClassicSpellsTrackerDB end
        if type(ElmoSpellTrackerDB) ~= "table" and type(ClassicCooldownTrackerDB) == "table" then ElmoSpellTrackerDB = ClassicCooldownTrackerDB end
    end
end
_G["ClassicSpellsTracker"] = A
_G["ClassicCooldownTracker"] = A
