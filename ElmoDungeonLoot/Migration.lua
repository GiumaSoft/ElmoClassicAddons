local _, A = ...
function A.MigrateSettings()
    if type(ElmoDungeonLootDB) ~= "table" then
        if type(ElmoDungeonLootDB) ~= "table" and type(ClassicDungeonDB) == "table" then ElmoDungeonLootDB = ClassicDungeonDB end
    end
end
_G["ClassicDungeon"] = A
