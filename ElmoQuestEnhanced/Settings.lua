local _, A = ...
local options = {
    {key = "reportQuests", default = true, label = "Report completed quests",
        tooltip = "Announce when one of your active quests becomes complete."},
    {key = "reportObjectives", default = true, label = "Report completed objectives",
        tooltip = "Announce each completed objective of quests with multiple objectives."},
    {key = "reportProgress", default = false, label = "Report remaining objectives (kills/items)",
        tooltip = "Announce each increase in quest kill or item counts, including how many remain. A completed-objective report replaces the progress message when both are enabled."},
}

function A.OpenSettings()
    if A.settingsCategory then Settings.OpenToCategory(A.settingsCategory:GetID()) end
end

function A.InitializeSettings()
    if A.db then return end
    if type(ElmoQuestEnhancedDB) ~= "table" then ElmoQuestEnhancedDB = {} end
    A.db = ElmoQuestEnhancedDB
    for _, option in ipairs(options) do
        if type(A.db[option.key]) ~= "boolean" then A.db[option.key] = option.default end
    end
    local category = Settings.RegisterVerticalLayoutCategory("ElmoQuestEnhanced")
    for _, option in ipairs(options) do
        local setting = Settings.RegisterAddOnSetting(category, "ElmoQuestEnhanced_" .. option.key,
            option.key, A.db, Settings.VarType.Boolean, option.label, option.default)
        Settings.CreateCheckbox(category, setting, option.tooltip)
    end
    Settings.RegisterAddOnCategory(category)
    A.settingsCategory = category
    SLASH_ELMOQUESTENHANCED1, SLASH_ELMOQUESTENHANCED2 = "/eqe", "/elmoquestenhanced"
    SlashCmdList.ELMOQUESTENHANCED = A.OpenSettings
end
