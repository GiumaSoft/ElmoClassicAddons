local addonName, A = ...
local frame, sinceUpdate = CreateFrame("Frame"), 0
A.frame = frame

frame:SetScript("OnEvent", function(_, event, unit, ...)
    if event == "ADDON_LOADED" then
        if unit ~= addonName then if A.db then A.Upgrades.HookBags() end; return end
        A.Init(); A.Sales.Init(); A.Levels.Init(); A.UI.RegisterOptions(); A.Upgrades.HookBags()
        SLASH_ELMOLEVELING1, SLASH_ELMOLEVELING2 = "/elmoleveling", "/elvl"
        SlashCmdList.ELMOLEVELING = A.Command
        return
    end
    if not A.db then return end
    if event == "PLAYER_ENTERING_WORLD" then
        A.Start(); A.Bags.Scan(); A.Upgrades.Invalidate(); A.Upgrades.HookBags()
        A.UI.Create(); A.Sample(); A.UI.Update()
        frame:SetScript("OnUpdate", function(_, elapsed)
            sinceUpdate = sinceUpdate + elapsed
            if sinceUpdate < 1 then return end
            sinceUpdate = sinceUpdate % 1
            A.Sample(); A.Bags.Update(); A.Sales.Update(); A.Upgrades.Update(); A.UI.Update()
        end)
    elseif event == "PLAYER_XP_UPDATE" then
        if unit == "player" then A.Sample(); A.UI.Update() end
    elseif event == "PLAYER_LEVEL_UP" then
        if A.IsNumber(unit) then
            A.expectedLevel = math.max(A.expectedLevel or 0, unit)
            A.Levels.Advance(unit)
        end
        A.Upgrades.Invalidate(); A.UI.Update()
    elseif event == "TIME_PLAYED_MSG" then A.Levels.Played(unit, ...); A.UI.Update()
    elseif event == "ZONE_CHANGED" or event == "ZONE_CHANGED_INDOORS" or event == "ZONE_CHANGED_NEW_AREA" or
        event == "UPDATE_EXHAUSTION" or event == "PLAYER_UPDATE_RESTING" then A.UI.Update()
    elseif event == "BAG_UPDATE_DELAYED" then A.Bags.dirty = true; A.Upgrades.Invalidate()
    elseif event == "MERCHANT_SHOW" then A.Sales.Open(); A.UI.Update()
    elseif event == "MERCHANT_UPDATE" or event == "PLAYER_MONEY" then A.Bags.dirty = true
    elseif event == "MERCHANT_CLOSED" then A.Bags.Scan(); A.Sales.Close(); A.UI.Update()
    elseif event == "GET_ITEM_INFO_RECEIVED" or event == "ITEM_DATA_LOAD_RESULT" then
        A.Bags.ItemLoaded(unit); A.Upgrades.ItemLoaded(unit)
    elseif event == "PLAYER_EQUIPMENT_CHANGED" or event == "CHARACTER_POINTS_CHANGED" or
        event == "PLAYER_TALENT_UPDATE" or event == "TRAIT_CONFIG_UPDATED" or event == "TRAIT_CONFIG_LIST_UPDATED" or
        event == "SPELLS_CHANGED" or event == "SKILL_LINES_CHANGED" or
        event == "GROUP_ROSTER_UPDATE" or event == "PLAYER_ROLES_ASSIGNED" then A.Upgrades.Invalidate()
    elseif event == "PLAYER_LOGOUT" then A.Bags.Update(); A.Sales.Update(); A.Save(); frame:SetScript("OnUpdate", nil) end
end)

for _, event in ipairs({"ADDON_LOADED", "PLAYER_ENTERING_WORLD", "PLAYER_XP_UPDATE", "PLAYER_LEVEL_UP", "TIME_PLAYED_MSG", "PLAYER_LOGOUT",
    "ZONE_CHANGED", "ZONE_CHANGED_INDOORS", "ZONE_CHANGED_NEW_AREA", "UPDATE_EXHAUSTION", "PLAYER_UPDATE_RESTING",
    "BAG_UPDATE_DELAYED", "GET_ITEM_INFO_RECEIVED", "ITEM_DATA_LOAD_RESULT", "PLAYER_EQUIPMENT_CHANGED",
    "CHARACTER_POINTS_CHANGED", "PLAYER_TALENT_UPDATE", "TRAIT_CONFIG_UPDATED", "TRAIT_CONFIG_LIST_UPDATED",
    "SPELLS_CHANGED", "SKILL_LINES_CHANGED", "GROUP_ROSTER_UPDATE", "PLAYER_ROLES_ASSIGNED",
    "MERCHANT_SHOW", "MERCHANT_UPDATE", "MERCHANT_CLOSED", "PLAYER_MONEY"}) do
    A.Compat.Register(frame, event)
end
