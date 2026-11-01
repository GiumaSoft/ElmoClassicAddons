local _, A = ...
function A.MigrateSettings()
    if type(ElmoPlaterDB) ~= "table" then
        if type(ElmoPlaterDB) ~= "table" and type(ClassicPlaterDB) == "table" then ElmoPlaterDB = ClassicPlaterDB end
        if type(ElmoPlaterDB) ~= "table" and type(ClassicTargetDB) == "table" then ElmoPlaterDB = ClassicTargetDB end
    end
end
_G["ClassicPlater"] = A
_G["ClassicTarget"] = A
