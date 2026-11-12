local addonName, A = ...
ElmoPlater = A
A.version, A.records, A.units = "2.4.0", {}, {}
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
function A.Print(text)
    DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoPlater:|r " .. text)
end

function A.Scan()
    for _, plate in ipairs(C_NamePlate.GetNamePlates()) do
        if not plate:IsForbidden() then
            local unit = A.Call(plate.GetUnit, plate) or plate.unitToken
            if unit then A.Add(unit) end
        end
    end
end

function A.AuraStatus()
    local lines = {}
    local function report(line) lines[#lines + 1] = line; A.Print(line) end
    local function describe(value)
        if A.Secret(value) then return "private" end
        if type(value) ~= "table" then return type(value) end
        return "table (icon=" .. (A.Secret(value.icon) and "private" or type(value.icon)) ..
            ", caster=" .. (A.Secret(value.sourceUnit) and "private" or A.Text(value.sourceUnit) or "nil") ..
            ", spell=" .. (A.Secret(value.spellId) and "private" or tostring(A.Number(value.spellId))) .. ")"
    end
    report("Last UNIT_AURA: " .. (A.lastAuraUnit or "none"))
    report("Aura display: " .. (A.Auras.available and "Blizzard container" or "legacy icons"))
    local units = {"target"}
    for unit, record in pairs(A.units) do
        local shown = 0
        for _, child in ipairs(record.frame.icons) do if child:IsShown() then shown = shown + 1 end end
        report(unit .. ": stored=" .. #record.auras .. ", known=" .. tostring(record.aurasKnown) ..
            ", icons=" .. shown .. ", visible=" .. tostring(record.frame:IsShown()) ..
            ", container=" .. tostring(record.auraContainer ~= nil))
        if A.Bool(A.Call(UnitIsUnit, unit, "target")) == true then units[#units + 1] = unit end
    end
    if A.Auras.available or A.Auras.Restricted() then
        report("Blizzard aura display or restricted data: direct queries skipped.")
        A.db.auraDiagnostic = lines
        return
    end
    for _, unit in ipairs(units) do
        for _, filter in ipairs({"HARMFUL|PLAYER", "HARMFUL"}) do
            local indexed = "unavailable"
            if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
                local ok, data = pcall(C_UnitAuras.GetAuraDataByIndex, unit, 1, filter)
                indexed = ok and describe(data) or "error: " .. (A.Text(data) or "private")
            end
            local batch = "unavailable"
            if C_UnitAuras and C_UnitAuras.GetUnitAuras then
                local ok, data = pcall(C_UnitAuras.GetUnitAuras, unit, filter, 255)
                if not ok then batch = "error: " .. (A.Text(data) or "private")
                elseif A.Secret(data) then batch = "private"
                elseif type(data) == "table" then batch = #data .. "; first=" .. describe(data[1])
                else batch = type(data) end
            end
            report(unit .. " " .. filter .. ": indexed=" .. indexed .. "; batch=" .. batch)
        end
    end
    A.db.auraDiagnostic = lines
end

function A.Command(msg)
    local command, value = (msg or ""):match("^%s*(%S*)%s*(.-)%s*$")
    command = command:lower()
    if command == "" or command == "config" or command == "settings" then
        A.Settings.Open()
    elseif command == "auras" then
        A.AuraStatus()
    elseif command == "questkills" then
        value = value:lower()
        if value == "on" or value == "off" then
            A.db.questKills = value == "on"
            A.QuestKills.Invalidate()
        elseif value ~= "" then
            A.Print("Usage: /eplater questkills on|off")
            return
        end
        A.Print("Quest kill marker: " .. (A.db.questKills and "enabled" or "disabled") ..
            ". /eplater questkills on|off")
        A.Update(false)
        return
    elseif command == "status" then
        local visible, custom, private = 0, 0, 0
        for _, record in pairs(A.units) do
            custom = custom + 1
            if record.frame:IsShown() then visible = visible + 1 end
            if record.privateHealth then private = private + 1 end
        end
        A.Print("Ready: " .. tostring(A.ready) .. "; native plates: " .. #C_NamePlate.GetNamePlates() ..
            "; tracked: " .. custom .. "; custom visible: " .. visible .. "; private health: " .. private)
        for _, plate in ipairs(C_NamePlate.GetNamePlates()) do
            if not plate:IsForbidden() then
                local unit = A.Text(A.Call(plate.GetUnit, plate)) or A.Text(plate.unitToken)
                if unit then
                    local guid, hp = A.Call(UnitGUID, unit), A.Call(UnitHealth, unit)
                    local native = plate.UnitFrame
                    local healthBar = native and native.HealthBarsContainer and native.HealthBarsContainer.healthBar
                    A.Print(unit .. ": GUID " .. (A.Secret(guid) and "private" or A.Text(guid) and "readable" or "missing") ..
                        "; HP " .. (A.Secret(hp) and "private" or A.Number(hp) and "readable" or "missing") ..
                        "; native health bar: " .. tostring(healthBar ~= nil))
                end
            end
        end
    else
        A.Print("/eplater: options. /eplater questkills on|off: quest knife. /eplater status | auras: diagnostics.")
    end
    A.Update(true)
end

function A.Initialize()
    if A.ready then return end
    if type(ElmoPlaterDB) ~= "table" then
        ElmoPlaterDB = {}
    end
    A.db = ElmoPlaterDB
    -- Retire settings used only by the removed priority engine.
    A.db.rules, A.db.ruleSchema, A.db.watchDebuff, A.db.learnedDebuffs = nil, nil, nil, nil
    A.db.plateAuraSize = math.max(14, math.min(36, A.Number(A.db.plateAuraSize) or 22))
    A.db.questKills = A.db.questKills ~= false
    A.db.showMana = A.db.showMana ~= false
    A.db.showCast = A.db.showCast ~= false
    A.Settings.RegisterOptions()
    A.Auras.Initialize()
    A.ready = not InCombatLockdown()
    if not A.ready then return end
    SLASH_ELMOPLATER1="/elmoplater"; SLASH_ELMOPLATER2="/eplater"
    SlashCmdList.ELMOPLATER=A.Command
    A.Scan()
    A.Print("Loaded " .. A.version .. ". /eplater: nameplate options.")
end

local elapsed = 0
A.frame:SetScript("OnEvent", function(_, event, unit)
    if event == "ADDON_LOADED" then
        if unit == addonName and IsLoggedIn() then A.Initialize() end
    elseif event == "PLAYER_LOGIN" then A.Initialize()
    elseif event == "PLAYER_REGEN_ENABLED" then A.Initialize(); A.Update(true)
    elseif A.ready then
        if event == "NAME_PLATE_UNIT_ADDED" then A.Add(unit)
        elseif event == "NAME_PLATE_UNIT_REMOVED" then A.Remove(unit)
        elseif event == "PLAYER_LOGOUT" or event == "PLAYER_LEAVING_WORLD" then A.Clear()
        elseif event == "PLAYER_ENTERING_WORLD" then A.QuestKills.Invalidate(true); A.Scan()
        elseif event == "CVAR_UPDATE" then
            if A.Text(unit) and unit:lower():match("^nameplate") then
                for _, record in pairs(A.units) do record.clickBound, record.clickFailed = false, false end
            end
        elseif event == "UNIT_AURA" then A.lastAuraUnit = A.Text(unit); A.Update(true, unit)
        elseif event == "PLAYER_TARGET_CHANGED" then A.Update(true, "target")
        elseif event == "PLAYER_REGEN_DISABLED" then A.Update(true)
        elseif event == "QUEST_LOG_UPDATE" or event == "QUEST_ACCEPTED" or event == "QUEST_REMOVED" or
            event == "QUEST_TURNED_IN" or event == "QUEST_AUTOCOMPLETE" or event == "QUEST_DATA_LOAD_RESULT" then
            if A.QuestKills.Invalidate(event ~= "QUEST_LOG_UPDATE" and event ~= "QUEST_DATA_LOAD_RESULT") then
                A.Update(false)
            end
        else A.Update(false) end
    end
end)
for _, event in ipairs({"ADDON_LOADED", "PLAYER_LOGIN", "PLAYER_REGEN_ENABLED", "PLAYER_REGEN_DISABLED", "NAME_PLATE_UNIT_ADDED",
    "NAME_PLATE_UNIT_REMOVED", "UNIT_HEALTH", "UNIT_MAXHEALTH", "UNIT_AURA", "UNIT_FACTION", "UNIT_FLAGS",
    "UNIT_POWER_UPDATE", "UNIT_POWER_FREQUENT", "UNIT_MAXPOWER", "UNIT_DISPLAYPOWER",
    "UNIT_SPELLCAST_START", "UNIT_SPELLCAST_STOP", "UNIT_SPELLCAST_FAILED", "UNIT_SPELLCAST_FAILED_QUIET",
    "UNIT_SPELLCAST_INTERRUPTED", "UNIT_SPELLCAST_DELAYED", "UNIT_SPELLCAST_CHANNEL_START",
    "UNIT_SPELLCAST_CHANNEL_UPDATE", "UNIT_SPELLCAST_CHANNEL_STOP",
    "UNIT_SPELLCAST_INTERRUPTIBLE", "UNIT_SPELLCAST_NOT_INTERRUPTIBLE",
    "PLAYER_TARGET_CHANGED", "PLAYER_ENTERING_WORLD", "PLAYER_LEAVING_WORLD", "PLAYER_LOGOUT",
    "CVAR_UPDATE", "QUEST_LOG_UPDATE", "QUEST_ACCEPTED", "QUEST_REMOVED", "QUEST_TURNED_IN",
    "QUEST_AUTOCOMPLETE", "QUEST_DATA_LOAD_RESULT"}) do
    A.Call(A.frame.RegisterEvent, A.frame, event)
end
A.frame:SetScript("OnUpdate", function(_, dt)
    if not A.ready then return end
    elapsed = elapsed + dt
    if elapsed >= .1 then elapsed = 0; A.Update(false) end
end)
