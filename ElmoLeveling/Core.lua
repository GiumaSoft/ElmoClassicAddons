local addonName, A = ...
local frame = CreateFrame("Frame")
A.frame = frame
local sinceUpdate = 0

frame:SetScript("OnEvent", function(_, event, unit, ...)
    if event == "ADDON_LOADED" then
        if unit ~= addonName then
            if A.db then A.Upgrades.HookBags() end
            return
        end
        A.Init()
        A.Mobs.Init()
        A.UI.RegisterOptions()
        A.Upgrades.HookBags()
        SLASH_CLASSICLEVELINGFOREVER1 = "/clf"
        SLASH_CLASSICLEVELINGFOREVER2 = "/classiclevelingforever"
        SLASH_CLASSICLEVELINGFOREVER3 = "/flvl"
        SLASH_CLASSICLEVELINGFOREVER4 = "/fl"
        SLASH_CLASSICLEVELINGFOREVER5 = "/foreverleveling"
        SlashCmdList.CLASSICLEVELINGFOREVER = A.Command
        SLASH_ELMOLEVELING1="/elmoleveling"
        SLASH_ELMOLEVELING2="/elvl"
        SlashCmdList.ELMOLEVELING=A.Command
        SLASH_CLASSICLEVELING1="/clvl"; SLASH_CLASSICLEVELING2="/classicleveling"
        SLASH_CLASSICLEVELING3="/cxp"; SLASH_CLASSICLEVELING4="/classicxp"
        SlashCmdList.CLASSICLEVELING=A.Command
        return
    end
    if not A.db then return end
    if event == "PLAYER_ENTERING_WORLD" then
        local initialLogin = unit == true and select(1, ...) ~= true
        if initialLogin then A.db.history = {} end
        A.Start()
        A.Mobs.ResetRespawnObservations()
        A.Bags.Scan()
        A.Upgrades.Invalidate()
        A.Upgrades.HookBags()
        A.Mobs.Scan()
        A.UI.Create()
        A.Sample()
        A.UI.Update(initialLogin)
        frame:SetScript("OnUpdate", function(_, elapsed)
            sinceUpdate = sinceUpdate + elapsed
            if sinceUpdate < 1 then return end
            sinceUpdate = sinceUpdate % 1
            A.Sample()
            A.Bags.Update()
            A.Upgrades.Update()
            A.Mobs.Tick()
            A.UI.Update()
        end)
    elseif event == "ZONE_CHANGED_NEW_AREA" then
        A.Mobs.ResetRespawnObservations()
        A.Mobs.Scan()
    elseif event == "PLAYER_REGEN_DISABLED" or event == "PLAYER_REGEN_ENABLED" then
        A.SetCombat(event == "PLAYER_REGEN_DISABLED")
        A.Mobs.Scan()
        A.UI.Update()
    elseif event == "PLAYER_XP_UPDATE" then
        if unit ~= "player" then return end
        A.Sample()
        A.UI.Update()
    elseif event == "PLAYER_LEVEL_UP" then
        if type(unit) == "number" then A.expectedLevel = math.max(A.expectedLevel or 0, unit) end
        A.Upgrades.Invalidate()
        A.UI.Update()
        -- The next update reads the settled XP bar, not the pre-level-up values.
    elseif event == "BAG_UPDATE_DELAYED" then A.Bags.dirty = true; A.Upgrades.Invalidate()
    elseif event == "GET_ITEM_INFO_RECEIVED" or event == "ITEM_DATA_LOAD_RESULT" then
        A.Bags.ItemLoaded(unit)
        A.Upgrades.ItemLoaded(unit)
    elseif event == "PLAYER_EQUIPMENT_CHANGED" or event == "CHARACTER_POINTS_CHANGED" or
        event == "PLAYER_TALENT_UPDATE" or event == "TRAIT_CONFIG_UPDATED" or event == "TRAIT_CONFIG_LIST_UPDATED" or event == "SPELLS_CHANGED" or event == "SKILL_LINES_CHANGED" or
        event == "GROUP_ROSTER_UPDATE" or event == "PLAYER_ROLES_ASSIGNED" then A.Upgrades.Invalidate()
    elseif event == "CHAT_MSG_COMBAT_XP_GAIN" then
        local args = {...}
        if A.Mobs.XP(unit, args[10], args[11]) then A.UI.Update() end
    elseif event == "COMBAT_LOG_EVENT_UNFILTERED" then
        if A.Mobs.Combat() then A.UI.Update() end
    elseif event == "PLAYER_TARGET_CHANGED" then A.Mobs.Observe("target")
    elseif event == "UPDATE_MOUSEOVER_UNIT" then A.Mobs.Observe("mouseover")
    elseif event == "UNIT_TARGET" then
        unit = A.Text(unit)
        if unit then
            A.Mobs.Observe(unit)
            A.Mobs.Observe(unit == "player" and "target" or unit .. "target")
        end
    elseif event == "NAME_PLATE_UNIT_ADDED" then
        A.Mobs.plates[unit] = true; A.Mobs.Observe(unit)
    elseif event == "NAME_PLATE_UNIT_REMOVED" then A.Mobs.Observe(unit); A.Mobs.plates[unit] = nil
    elseif event == "UNIT_FLAGS" or event == "UNIT_HEALTH" or event == "UNIT_THREAT_LIST_UPDATE" or
        event == "UNIT_THREAT_SITUATION_UPDATE" then
        unit = A.Text(unit)
        if unit == "player" or unit == "pet" then A.Mobs.Scan()
        elseif unit then A.Mobs.Observe(unit) end
    elseif event == "PLAYER_LOGOUT" then
        A.Mobs.Tick(true)
        A.Save()
        frame:SetScript("OnUpdate", nil)
    end
end)

for _, event in ipairs({"ADDON_LOADED", "PLAYER_ENTERING_WORLD", "PLAYER_XP_UPDATE", "PLAYER_LEVEL_UP", "PLAYER_LOGOUT",
    "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED",
    "ZONE_CHANGED_NEW_AREA",
    "BAG_UPDATE_DELAYED", "GET_ITEM_INFO_RECEIVED", "ITEM_DATA_LOAD_RESULT", "CHAT_MSG_COMBAT_XP_GAIN",
    "COMBAT_LOG_EVENT_UNFILTERED", "PLAYER_TARGET_CHANGED", "UPDATE_MOUSEOVER_UNIT", "UNIT_TARGET",
    "UNIT_FLAGS", "UNIT_HEALTH", "UNIT_THREAT_LIST_UPDATE", "UNIT_THREAT_SITUATION_UPDATE",
    "NAME_PLATE_UNIT_ADDED", "NAME_PLATE_UNIT_REMOVED", "PLAYER_EQUIPMENT_CHANGED",
    "CHARACTER_POINTS_CHANGED", "PLAYER_TALENT_UPDATE", "TRAIT_CONFIG_UPDATED", "TRAIT_CONFIG_LIST_UPDATED", "SPELLS_CHANGED", "SKILL_LINES_CHANGED", "GROUP_ROSTER_UPDATE"}) do
    A.Compat.Register(frame, event)
end
A.Compat.Register(frame, "PLAYER_ROLES_ASSIGNED")
