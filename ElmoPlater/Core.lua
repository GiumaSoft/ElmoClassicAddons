local addonName, A = ...
ElmoPlater = A
ClassicTarget = A -- Compatibility for existing integrations.
A.version, A.records, A.units, A.attacked = "2.2.1", {}, {}, {}
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
function A.Secret(v)
    return type(issecretvalue) == "function" and issecretvalue(v)
end
function A.Text(v)
    if not A.Secret(v) and type(v) == "string" then return v end
end
function A.Bool(v)
    if not A.Secret(v) and type(v) == "boolean" then return v end
end
function A.CombatLogAvailable()
    local restricted = A.Call(C_CombatLog and C_CombatLog.IsCombatLogRestricted)
    return not A.Secret(restricted) and restricted ~= true and
        type(C_CombatLog and C_CombatLog.GetCurrentEventInfo or CombatLogGetCurrentEventInfo) == "function"
end
function A.RegisterCombatLog()
    if A.CombatLogAvailable() then
        local valid = A.Call(C_EventUtils and C_EventUtils.IsEventValid, "COMBAT_LOG_EVENT_UNFILTERED")
        if A.Bool(valid) ~= false then A.Call(A.frame.RegisterEvent, A.frame, "COMBAT_LOG_EVENT_UNFILTERED") end
    else
        A.Call(A.frame.UnregisterEvent, A.frame, "COMBAT_LOG_EVENT_UNFILTERED")
    end
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
    event, source, dest = A.Text(event), A.Text(source), A.Text(dest)
    if not event or not dest or not (dest:match("^Creature%-") or dest:match("^Vehicle%-")) then return end
    if event == "UNIT_DIED" or event == "UNIT_DESTROYED" then
        A.attacked[dest] = nil; A.Update(false)
    elseif source and source == A.Text(A.Call(UnitGUID,"player")) then
        local damage = event:match("_DAMAGE$") or event:match("_MISSED$") or event == "DAMAGE_SHIELD"
        local debuff = (event == "SPELL_AURA_APPLIED" or event == "SPELL_AURA_REFRESH") and A.Text(select(15, ...)) == "DEBUFF"
        if debuff then
            local id, name = A.Number(select(12, ...)), A.Text(select(13, ...))
            local info = id and A.Spells.Info(id)
            A.Rules.Observe(id, name, info and info.icon)
        end
        if damage or debuff then A.attacked[dest] = true; A.Update(false) end
    end
end

function A.Command(msg)
    local command, value = (msg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    command = command:lower()
    if command == "" or command == "config" or command == "settings" then
        A.Settings.Toggle()
    elseif command == "debuff" then
        if value:lower() == "any" then
            A.db.rules, A.db.watchDebuff = {}, ""
            A.Print("Rules cleared. No priority highlight until you add a rule.")
        else
            local info = A.Spells.Info(tonumber(value) or value)
            if not info or not info.id then A.Print("Unknown spell. Open /eplater and add a spell ID."); return end
            A.db.rules, A.db.watchDebuff = {}, value
            A.Rules.Add(info.id)
            A.Print("Single priority rule: " .. info.name .. ".")
        end
    else
        A.Print("/eplater: Rules Manager. First matching enabled rule wins. Health and debuff rules share the same ordered list; only engaged mobs qualify.")
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
    A.Rules.Initialize()
    A.ready = A.Recover()
    if not A.ready then return end
    A.RegisterCombatLog()
    SLASH_CLASSICPLATER1, SLASH_CLASSICPLATER2 = "/cplater", "/classicplater"
    SLASH_CLASSICPLATER3, SLASH_CLASSICPLATER4 = "/ctarget", "/classictarget"
    SlashCmdList.CLASSICPLATER = A.Command
    SLASH_ELMOPLATER1="/elmoplater"; SLASH_ELMOPLATER2="/eplater"
    SlashCmdList.ELMOPLATER=A.Command
    A.Scan()
    A.Print("Loaded " .. A.version .. ". /eplater: learned debuffs and ordered priority rules.")
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
        elseif event == "PLAYER_ENTERING_WORLD" then A.RegisterCombatLog(); A.Scan()
        elseif event == "COMBAT_LOG_EVENT_UNFILTERED" and A.CombatLogAvailable() then
            A.CombatLog(A.Call(C_CombatLog and C_CombatLog.GetCurrentEventInfo or CombatLogGetCurrentEventInfo))
        elseif event == "CVAR_UPDATE" then
            if A.Text(unit) and unit:lower():match("^nameplate") then
                for _, record in pairs(A.units) do record.clickBound, record.clickFailed = false, false end
            end
        elseif event == "UNIT_AURA" then A.Update(true, unit)
        else A.Update(false) end
    end
end)
for _, event in ipairs({"ADDON_LOADED", "PLAYER_LOGIN", "PLAYER_REGEN_ENABLED", "NAME_PLATE_UNIT_ADDED",
    "NAME_PLATE_UNIT_REMOVED", "UNIT_HEALTH", "UNIT_MAXHEALTH", "UNIT_AURA", "UNIT_FACTION", "UNIT_FLAGS",
    "PLAYER_TARGET_CHANGED", "PLAYER_ENTERING_WORLD", "PLAYER_LEAVING_WORLD", "PLAYER_LOGOUT",
    "CVAR_UPDATE"}) do
    A.Call(A.frame.RegisterEvent, A.frame, event)
end
A.frame:SetScript("OnUpdate", function(_, dt)
    if not A.ready then return end
    elapsed = elapsed + dt
    if elapsed >= .1 then elapsed = 0; A.Update(false) end
end)
