local addonName, A = ...
ElmoPlater = A
ClassicTarget = A -- Compatibility for existing integrations.
A.version, A.records, A.units, A.attacked = "2.0.7", {}, {}, {}
A.nativeAlpha = setmetatable({}, {__mode = "k"})
A.frame = CreateFrame("Frame")

local function checked(ok, ...)
    if ok then return ... end
end
function A.Call(fn, ...)
    if type(fn) == "function" then return checked(pcall(fn, ...)) end
end
function A.Number(v)
    if type(issecretvalue) == "function" and issecretvalue(v) then return end
    if type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge then return v end
end
function A.Print(text)
    DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoPlater:|r " .. text)
end

-- One-time recovery of global overrides left by the former icon-bar build.
-- Normal operation never changes global native dimensions or stacking bounds.
function A.Recover()
    if InCombatLockdown() then return false end
    local saved = A.db.nativeClickRestoreSize
    if type(saved) == "table" and C_NamePlate and C_NamePlate.GetNamePlateSize and C_NamePlate.SetNamePlateSize then
        local w, h = C_NamePlate.GetNamePlateSize()
        if A.Number(w) and A.Number(h) and w > 2048 and h > 2048 and
            A.Number(saved.width) and A.Number(saved.height) and saved.width > 0 and saved.width < 2048 and
            saved.height > 0 and saved.height < 2048 then
            C_NamePlate.SetNamePlateSize(saved.width, saved.height)
        end
        w, h = C_NamePlate.GetNamePlateSize()
        if not A.Number(w) or not A.Number(h) or w > 2048 or h > 2048 then return false end
        A.db.nativeClickRestoreSize = nil
    end
    local insets = A.db.nativeClickRestoreInsets
    if type(insets) == "table" and #insets == 4 and C_NamePlateManager and Enum and Enum.NamePlateType then
        local a, b, c, d = C_NamePlateManager.GetNamePlateHitTestInsets(Enum.NamePlateType.Friendly)
        if A.Number(a) and A.Number(b) and A.Number(c) and A.Number(d) and
            a > 2048 and b > 2048 and c > 2048 and d > 2048 then
            C_NamePlateManager.SetNamePlateHitTestInsets(Enum.NamePlateType.Friendly, unpack(insets))
        end
        A.db.nativeClickRestoreInsets = nil
    end
    if type(A.db.originalNativeDebuffs) == "boolean" and C_CVar and C_CVar.SetCVarBitfield then
        A.Call(C_CVar.SetCVarBitfield, "nameplateEnemyNpcAuraDisplay", 2, A.db.originalNativeDebuffs)
        A.db.originalNativeDebuffs = nil
    end
    A.db.barClicks = nil
    return true
end

function A.Scan()
    for _, plate in ipairs(C_NamePlate.GetNamePlates()) do
        if not plate:IsForbidden() then
            local unit = A.Call(plate.GetUnit, plate) or plate.unitToken
            if unit then A.Add(unit) end
        end
    end
end

function A.CombatLog(...)
    local _, event, _, source, _, _, _, dest = ...
    if type(dest) ~= "string" or not (dest:match("^Creature%-") or dest:match("^Vehicle%-")) then return end
    if event == "UNIT_DIED" or event == "UNIT_DESTROYED" then
        A.attacked[dest] = nil; A.Update(false)
    elseif source == UnitGUID("player") then
        local damage = event:match("_DAMAGE$") or event:match("_MISSED$") or event == "DAMAGE_SHIELD"
        local debuff = (event == "SPELL_AURA_APPLIED" or event == "SPELL_AURA_REFRESH") and select(15, ...) == "DEBUFF"
        if damage or debuff then A.attacked[dest] = true; A.Update(false) end
    end
end

function A.Command(msg)
    local command, value = (msg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    if command:lower() == "debuff" then
        A.db.watchDebuff = value:lower() == "any" and "" or value
        A.Print(A.db.watchDebuff == "" and "Missing-debuff priority: no personal debuff." or
            "Missing-debuff priority: " .. A.db.watchDebuff .. ".")
    else
        A.Print("v" .. A.version .. " prototype. All mobs: health < 20%, missing debuff, then lowest remaining HP. " ..
            "The first mob you attacked has double height, including your selected target. /ctarget debuff Rend; /ctarget debuff any.")
    end
    A.Update(true)
end

function A.Initialize()
    A.MigrateSettings()
    if A.ready then return end
    if type(ElmoPlaterDB) ~= "table" then
        ElmoPlaterDB = type(ClassicTargetDB) == "table" and ClassicTargetDB or {}
    end
    ClassicTargetDB = ElmoPlaterDB
    A.db = ElmoPlaterDB
    A.db.watchDebuff = type(A.db.watchDebuff) == "string" and A.db.watchDebuff or ""
    A.db.plateAuraSize = math.max(14, math.min(36, A.Number(A.db.plateAuraSize) or 22))
    A.ready = A.Recover()
    if not A.ready then return end
    SLASH_CLASSICPLATER1, SLASH_CLASSICPLATER2 = "/cplater", "/classicplater"
    SLASH_CLASSICPLATER3, SLASH_CLASSICPLATER4 = "/ctarget", "/classictarget"
    SlashCmdList.CLASSICPLATER = A.Command
    SLASH_ELMOPLATER1="/elmoplater"; SLASH_ELMOPLATER2="/eplater"
    SlashCmdList.ELMOPLATER=A.Command
    A.Scan()
    A.Print("Loaded " .. A.version .. " prototype: priority: health < 20%, missing debuff, then lowest remaining HP.")
end

local elapsed = 0
A.frame:SetScript("OnEvent", function(_, event, unit)
    if event == "ADDON_LOADED" then
        if unit == addonName and IsLoggedIn() then A.Initialize() end
    elseif event == "PLAYER_LOGIN" then A.Initialize()
    elseif event == "PLAYER_REGEN_ENABLED" then A.attacked = {}; A.Initialize(); A.Update(false)
    elseif A.ready then
        if event == "NAME_PLATE_UNIT_ADDED" then A.Add(unit)
        elseif event == "NAME_PLATE_UNIT_REMOVED" then A.Remove(unit)
        elseif event == "PLAYER_LOGOUT" or event == "PLAYER_LEAVING_WORLD" then A.Clear()
        elseif event == "PLAYER_ENTERING_WORLD" then A.Scan()
        elseif event == "COMBAT_LOG_EVENT_UNFILTERED" then A.CombatLog(CombatLogGetCurrentEventInfo())
        elseif event == "CVAR_UPDATE" then
            if type(unit) == "string" and unit:lower():match("^nameplate") then
                for _, record in pairs(A.units) do record.clickBound, record.clickFailed = false, false end
            end
        elseif event == "UNIT_AURA" then A.Update(true, unit)
        else A.Update(false) end
    end
end)
for _, event in ipairs({"ADDON_LOADED", "PLAYER_LOGIN", "PLAYER_REGEN_ENABLED", "NAME_PLATE_UNIT_ADDED",
    "NAME_PLATE_UNIT_REMOVED", "UNIT_HEALTH", "UNIT_MAXHEALTH", "UNIT_AURA", "UNIT_FACTION", "UNIT_FLAGS",
    "PLAYER_TARGET_CHANGED", "PLAYER_ENTERING_WORLD", "PLAYER_LEAVING_WORLD", "PLAYER_LOGOUT",
    "COMBAT_LOG_EVENT_UNFILTERED", "CVAR_UPDATE"}) do
    A.frame:RegisterEvent(event)
end
A.frame:SetScript("OnUpdate", function(_, dt)
    if not A.ready then return end
    elapsed = elapsed + dt
    if elapsed >= .1 then elapsed = 0; A.Update(false) end
end)
