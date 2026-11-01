local addonName,CD=...
local f=CreateFrame("Frame")
CD.frame=f
local function initialize()
    if CD.db then return end
    CD.MigrateSettings()
    ElmoDungeonLootDB=CD.Table(ElmoDungeonLootDB) or {}
    CD.db=ElmoDungeonLootDB
    if CD.db.journalVersion~=2 then CD.db.position=nil;CD.db.journalVersion=2 end
    if not CD.Catalog.dungeons[CD.db.lastDungeon or ""] then CD.db.lastDungeon="the-deadmines" end
    -- Obsolete 1.x score settings are ignored. No equipped items or bags are scanned.
    SLASH_CLASSICDUNGEON1="/cdungeon"
    SLASH_CLASSICDUNGEON2="/classicdungeon"
    SLASH_CLASSICDUNGEON3="/cdl"
    SlashCmdList.CLASSICDUNGEON=function(command)
        command=(command or ""):lower():match("^%s*(.-)%s*$")
        if command=="reset" then
            CD.db.position=nil
            if CD.UI.frame then CD.UI.frame:ClearAllPoints();CD.UI.frame:SetPoint("CENTER") end
            CD.UI.Show();CD.QueueItems();return
        elseif command=="help" then
            CD.Print("/cdungeon — open the dungeon journal. /cdungeon reset — center the window.")
            return
        end
        CD.UI.Create()
        if CD.UI.frame:IsShown() then CD.UI.frame:Hide() else CD.UI.Show();CD.QueueItems() end
    end
    SLASH_ELMODUNGEONLOOT1="/elmodungeonloot"; SLASH_ELMODUNGEONLOOT2="/edl"
    SlashCmdList.ELMODUNGEONLOOT=SlashCmdList.CLASSICDUNGEON
end

function CD.SelectDungeon(id)
    if not CD.Catalog.dungeons[id] then return false end
    CD.db.lastDungeon=id
    CD.UI.Render(true);CD.QueueItems()
    return true
end

-- Warm only the selected dungeon's client cache, in bounded batches.
function CD.QueueItems()
    local dungeon=CD.db and CD.Catalog.dungeons[CD.db.lastDungeon]
    if not dungeon then return end
    local ids,seen={},{}
    for _,groups in ipairs({dungeon.bosses,dungeon.sharedLoot or {}}) do
        for _,group in ipairs(groups) do
            for _,entry in ipairs(group.loot) do
                if not seen[entry.id] then ids[#ids+1]=entry.id;seen[entry.id]=true end
            end
        end
    end
    CD.queue,CD.queueIndex,CD.queueElapsed=ids,1,0
    f:SetScript("OnUpdate",function(_,elapsed)
        CD.queueElapsed=CD.queueElapsed+elapsed
        if CD.queueElapsed<.05 then return end
        CD.queueElapsed=0
        for _=1,6 do
            local id=CD.queue[CD.queueIndex]
            if not id then CD.queue=nil;break end
            CD.Items.Request(id);CD.queueIndex=CD.queueIndex+1
        end
        if not CD.queue then f:SetScript("OnUpdate",nil) end
    end)
end

local refreshPending=false
local function refresh()
    refreshPending=false
    if CD.UI.frame and CD.UI.frame:IsShown() then CD.UI.Render() end
end
f:SetScript("OnEvent",function(_,event,...)
    if event=="ADDON_LOADED" then
        if (...)==addonName then initialize() end
        return
    end
    if event=="PLAYER_LOGIN" then initialize();return end
    if not CD.db or not CD.UI.frame or not CD.UI.frame:IsShown() then return end
    if event=="GET_ITEM_INFO_RECEIVED" or event=="ITEM_DATA_LOAD_RESULT" then
        if not CD.Items.requested[(...)] then return end
    end
    if not refreshPending then
        refreshPending=true
        if C_Timer and C_Timer.After then C_Timer.After(.25,refresh) else refresh() end
    end
end)
for _,event in ipairs({"ADDON_LOADED","PLAYER_LOGIN","QUEST_LOG_UPDATE","QUEST_TURNED_IN",
    "PLAYER_LEVEL_UP","SKILL_LINES_CHANGED","SPELLS_CHANGED","GET_ITEM_INFO_RECEIVED","ITEM_DATA_LOAD_RESULT"}) do
    CD.Call(f.RegisterEvent,f,event)
end
