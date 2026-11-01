local _,CD=...
local Q={}
CD.Quests=Q
local call=CD.Call

local function intersects(a,b)
    for id=1,53 do
        if CD.Items.HasMask(a,id) and CD.Items.HasMask(b,id) then return true end
    end
    return false
end

function Q.ForCharacter(quest,who)
    who=who or CD.Items.Character()
    if quest.faction and quest.faction~=who.faction then return false end
    local faction=CD.QuestCatalog.factionMasks and CD.QuestCatalog.factionMasks[who.faction]
        or (who.faction=="Horde" and 178 or 77)
    if quest.races and quest.races>0 and not intersects(quest.races,faction) then return false end
    if not CD.Items.HasMask(quest.classes,who.classID) then return false end
    if who.raceID and not CD.Items.HasMask(quest.races,who.raceID) then return false end
    return true
end

function Q.Get(id)
    local catalog,who=CD.QuestCatalog,CD.Items.Character()
    local class=catalog.classes and catalog.classes[who.faction..":"..tostring(who.classID)]
    if class and class[id] then return class[id] end
    if who.faction=="Horde" and catalog.horde and catalog.horde[id] then return catalog.horde[id] end
    return catalog.quests[id]
end

function Q.List(dungeon)
    local result={}
    local who=CD.Items.Character()
    for _,id in ipairs(dungeon.quests or {}) do
        local quest=Q.Get(id)
        if quest and Q.ForCharacter(quest,who) then result[#result+1]=quest end
    end
    return result
end

function Q.Completed(id)
    return CD.Bool(call(C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted or IsQuestFlaggedCompleted,id))==true
end

function Q.InLog(id)
    local api=C_QuestLog and C_QuestLog.GetLogIndexForQuestID or GetQuestLogIndexByID
    if api then
        local index=CD.Number(call(api,id))
        if index and index>0 then return true end
    end
    local count=CD.Number(call(C_QuestLog and C_QuestLog.GetNumQuestLogEntries or GetNumQuestLogEntries)) or 0
    for i=1,count do
        local info=CD.Table(call(C_QuestLog and C_QuestLog.GetInfo,i))
        if info then
            if CD.Bool(info.isHeader)~=true and CD.Number(info.questID)==id then return true end
        else
            local _,_,_,_,header,_,_,questId=call(GetQuestLogTitle,i)
            if CD.Bool(header)~=true and CD.Number(questId)==id then return true end
        end
    end
    return false
end

function Q.State(quest)
    if Q.Completed(quest.id) and not quest.repeatable then return "Completed","green" end
    if Q.InLog(quest.id) then return "In quest log","blue" end
    local who=CD.Items.Character()
    if who.level<quest.minLevel then return "Requires level "..quest.minLevel,"red" end
    if quest.maxLevel and quest.maxLevel>0 and who.level>quest.maxLevel then return "Above maximum level","red" end
    for _,id in ipairs(quest.previousAll or {}) do
        if not Q.Completed(id) then return "Prerequisites incomplete","amber" end
    end
    local any,done=false,false
    for _,id in ipairs(quest.previousAny or {}) do
        local prior=Q.Get(id)
        if not prior or Q.ForCharacter(prior,who) then any=true;done=done or Q.Completed(id) end
    end
    if any and not done then return "Prerequisites incomplete","amber" end
    if quest.activeParent and quest.activeParent>0 and not Q.InLog(quest.activeParent) then
        return "Parent quest must be active","amber"
    end
    if #(quest.skill or {})>0 or #(quest.minRep or {})>0 or #(quest.maxRep or {})>0 then
        return "Check skill / reputation requirements","amber"
    end
    for _,id in ipairs(quest.exclusive or {}) do
        if Q.Completed(id) then return "Alternative quest completed","muted" end
    end
    return quest.repeatable and "Repeatable · check quest giver" or "Check quest giver","ink2"
end

function Q.ZoneName(area)
    local map=CD.QuestCatalog.areaMaps[area]
    local info=map and call(C_Map and C_Map.GetMapInfo,map)
    return info and info.name or CD.QuestCatalog.areaNames[area] or "Area #"..area
end

function Q.GiverLines(quest)
    local lines={}
    for _,giver in ipairs(quest.givers or {}) do
        local kind=giver.kind=="item" and "Starts from item: " or giver.kind=="object" and "Quest object: " or "Quest giver: "
        lines[#lines+1]=kind..giver.name
        for i,loc in ipairs(giver.locations or {}) do
            if i<=3 then
                lines[#lines+1]=(loc.source and loc.source.." · " or "")..Q.LocationText(loc)
            end
        end
        if #(giver.locations or {})>3 then lines[#lines+1]="Additional spawn locations in tooltip" end
        if #(giver.locations or {})==0 then
            lines[#lines+1]=giver.kind=="item" and "Dropped item — exact location not recorded" or "Coordinates not recorded"
        end
    end
    if #lines==0 then lines[1]="Automatic / scripted start — no quest giver recorded" end
    return lines
end

function Q.LocationText(loc)
    if loc.map then
        local info=CD.Table(call(C_Map and C_Map.GetMapInfo,loc.map))
        local name=info and CD.Text(info.name) or CD.QuestCatalog.mapNames[loc.map] or "Map #"..loc.map
        return name..(loc.x and loc.y and string.format(" (%.1f, %.1f)",loc.x,loc.y) or " (coordinates not recorded)")
    end
    return Q.ZoneName(loc.zone)..(loc.x and loc.y and string.format(" (%.1f, %.1f)",loc.x,loc.y)
        or " (coordinates not recorded)")
end

-- Preserve AND/OR semantics and show each earlier step, including its own giver.
function Q.Prerequisites(quest)
    local result,path={},{}
    local function visit(current,depth,relation)
        if depth>20 or path[current.id] then return end
        path[current.id]=true
        local groups={{current.previousAll,"Complete all"},{current.previousAny,"Complete one"}}
        for _,group in ipairs(groups) do
            local valid={}
            for _,id in ipairs(group[1] or {}) do
                local prior=Q.Get(id)
                if prior and Q.ForCharacter(prior) then valid[#valid+1]=prior end
            end
            for _,prior in ipairs(valid) do
                result[#result+1]={quest=prior,depth=depth,relation=#valid>1 and group[2] or "Previous step"}
                visit(prior,depth+1,group[2])
            end
        end
        local parent=Q.Get(current.activeParent or 0)
        if parent and Q.ForCharacter(parent) then
            result[#result+1]={quest=parent,depth=depth,relation="Must be active"}
            visit(parent,depth+1,"Must be active")
        end
        path[current.id]=nil
    end
    visit(quest,0)
    return result
end

function Q.Link(quest)
    return string.format("|cffffff00|Hquest:%d:%d|h[%s]|h|r",quest.id,quest.level,quest.name)
end
