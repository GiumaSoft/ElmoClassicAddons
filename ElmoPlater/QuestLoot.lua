local _, A = ...
local Q, cache = {}, {}
A.QuestLoot = Q

local function publicTable(value)
    if not A.Secret(value) and type(value) == "table" and
        not (issecrettable and issecrettable(value)) then return value end
end

local function activeQuest(id, player)
    if not id then return false end
    local reader = C_QuestLog and C_QuestLog.GetLogIndexForQuestID or GetQuestLogIndexByID
    if type(reader) == "function" then
        local index = A.Number(A.Call(reader, id))
        return index and index > 0
    end
    local log = player and publicTable(player.currentQuestlog)
    return log and not A.Secret(log[id]) and log[id] ~= nil and log[id] ~= false
end

local function needed(npc)
    local loader = publicTable(QuestieLoader)
    if not loader then return false end
    local tooltips = publicTable(A.Call(loader.ImportModule, loader, "QuestieTooltips"))
    local registry = tooltips and publicTable(tooltips.lookupByKey)
    local entries = registry and publicTable(registry["m_" .. npc])
    if not entries then return false end
    local player = publicTable(A.Call(loader.ImportModule, loader, "QuestiePlayer"))
    local lootIcon = Questie and A.Number(Questie.ICON_TYPE_LOOT)
    local slayIcon = Questie and A.Number(Questie.ICON_TYPE_SLAY)
    local loot, slay = false, false
    for _, entry in pairs(entries) do
        entry = publicTable(entry)
        local objective = entry and publicTable(entry.objective)
        if objective and activeQuest(A.Number(entry.questId), player) then
            -- Questie owns progress and updates it through its quest-log cache.
            if A.Bool(objective.IsSourceItem) ~= true and A.Bool(objective.IsRequiredSourceItem) ~= true then
                A.Call(objective.Update, objective)
            end
            if A.Bool(objective.Completed) == false then
                local icon, kind = A.Number(objective.Icon), A.Text(objective.Type)
                if (lootIcon and icon == lootIcon) or (not icon and kind == "item") then loot = true end
                if (slayIcon and icon == slayIcon) or (not icon and kind == "monster") then slay = true end
                if loot and slay then break end
            end
        end
    end
    return loot, slay
end

local function texture(kind, setting)
    local questie = publicTable(Questie)
    local icons = questie and publicTable(questie.icons)
    local db = questie and publicTable(questie.db)
    local profile = db and publicTable(db.profile)
    local custom = profile and A.Text(profile.iconTheme) ~= "pfquest" and profile[setting]
    local default = icons and icons[kind]
    return A.Number(custom) or A.Text(custom) or A.Number(default) or A.Text(default) or
        ("Interface\\AddOns\\Questie\\Icons\\" .. kind .. ".blp")
end

function Q.Invalidate()
    cache = {}
end

function Q.GetIcons(guid, now)
    guid = A.Text(guid)
    if not guid or not (guid:match("^Creature%-") or guid:match("^Vehicle%-")) then return end
    local npc = guid:match("^%w+%-%d+%-%d+%-%d+%-%d+%-(%d+)%-")
    if not npc then return end
    now = now or GetTime()
    local found = cache[npc]
    if not found or now >= found.expires then
        local loot, slay = needed(npc)
        found = {loot = loot, slay = slay, expires = now + .5}
        cache[npc] = found
    end
    return found.loot and texture("loot", "ICON_LOOT") or nil,
        found.slay and texture("slay", "ICON_SLAY") or nil
end
