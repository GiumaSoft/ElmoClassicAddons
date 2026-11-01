local count=0
local function check(name,fn) fn();count=count+1;print('OK '..name) end
local function eq(a,b) assert(a==b,tostring(a)..' ~= '..tostring(b)) end
local function contains(s,part) assert(s:find(part,1,true),s..' does not contain '..part) end
local U,Q,I=CD.UI,CD.Quests,CD.Items
MOCK.level,MOCK.class,MOCK.race,MOCK.faction=20,'HUNTER',3,'Alliance'
CD.frame:GetScript('OnEvent')(CD.frame,'ADDON_LOADED','ElmoDungeonLoot')

check('Version and Era-only catalogue',function()
    assert(CD.version:match('^2%.'));eq(#CD.Catalog.order,26)
    assert(not CD.Compare and not CD.Profiles)
    assert(CD.Catalog.dungeons['the-deadmines'])
    for _,d in pairs(CD.Catalog.dungeons) do
        for _,g in ipairs(d.bosses) do
            assert(g.kind~='trash')
            for _,drop in ipairs(g.loot) do assert(CD.Catalog.items[drop.id]) end
        end
    end
end)
check('Cold-cache stats are present immediately',function()
    local it=I.Read(5195)
    eq(it.name,'Gold-flecked Gloves');eq(it.stats.armor,22);eq(it.stats.str,4);eq(it.stats.int,3)
    assert(not it.live);eq(it.usable,nil)
    contains(I.FormatStats(it),'22 Armor');contains(I.FormatStats(it),'+4 STR')
end)
check('Cold-cache weapon data includes DPS and speed',function()
    local it=I.Read(7230)
    assert(it.dps>0 and it.weaponSpeed>0 and it.damageMin>0)
    contains(I.FormatStats(it),'DPS');contains(I.FormatStats(it),'Speed')
end)
check('Eligibility reports required level and class before native API',function()
    local it=I.Read(7230);it.level=60
    local ok,why=I.Eligibility(it);eq(ok,false);contains(why,'60')
    it.level=1;it.classes=2 -- Paladin
    ok,why=I.Eligibility(it);eq(ok,false);contains(why,'Class')
end)
check('Live item tooltip and API stats replace bundled values',function()
    MOCK.items[5195]={name='Gold-flecked Gloves',loc='INVTYPE_HAND',level=17,classID=4,subclassID=1,
        stats={RESISTANCE0_NAME=22,ITEM_MOD_STRENGTH_SHORT=4,ITEM_MOD_INTELLECT_SHORT=3},
        lines={'Gold-flecked Gloves','22 Armor','+4 Strength','+3 Intellect'},usable=true}
    local it=I.Read(5195);assert(it.live);eq(it.usable,true);eq(it.stats.str,4)
end)
check('Quest drops and recipes are retained',function()
    local d=CD.Catalog.dungeons['the-deadmines'];local letter,parrot=false,false
    for _,g in ipairs(d.bosses) do for _,it in ipairs(g.loot) do
        if it.id==2874 then letter=true;eq(g.name,'Edwin VanCleef') end
        if it.id==8490 then parrot=true;eq(g.name,'Cookie') end
    end end
    assert(letter and parrot)
    local recipe=false
    for _,it in pairs(CD.Catalog.items) do if it.classID==9 then recipe=true end end
    assert(recipe)
end)
check('Boss levels are sourced and shared loot is separated',function()
    local d=CD.Catalog.dungeons['the-deadmines']
    eq(d.bosses[1].name,"Rhahk'Zor");eq(d.bosses[1].minLevel,19)
    for _,g in ipairs(d.sharedLoot) do eq(g.kind,'trash') end
    eq(#CD.Catalog.dungeons['the-stockade'].bosses,6)
    eq(#CD.Catalog.dungeons['ragefire-chasm'].bosses,4)
end)
check('Dungeon quests exclude ordinary material turn-ins and world starters',function()
    for _,d in pairs(CD.Catalog.dungeons) do
        for _,id in ipairs(d.quests) do assert(id~=7791 and id~=635) end
    end
    local ids={};for _,id in ipairs(CD.Catalog.dungeons['the-deadmines'].quests) do ids[id]=true end
    assert(ids[166] and ids[214] and ids[1654])
end)
check('Faction, race and class quest restrictions',function()
    local q={races=178,classes=0}
    eq(Q.ForCharacter(q),false);MOCK.faction,MOCK.race='Horde',2;eq(Q.ForCharacter(q),true)
    q.classes=2;eq(Q.ForCharacter(q),false)
    MOCK.faction,MOCK.race='Alliance',3
    local qs=Q.List(CD.Catalog.dungeons['the-deadmines'])
    for _,quest in ipairs(qs) do assert(quest.id~=1654) end -- Paladin-only
end)
check('All transitive Defias steps and coordinates are available',function()
    local quest=CD.QuestCatalog.quests[166]
    local chain=Q.Prerequisites(quest);assert(#chain>=5)
    local seen={};for _,step in ipairs(chain) do seen[step.quest.id]=true;assert(#step.quest.givers>0) end
    assert(seen[65] and seen[132])
    local lines=table.concat(Q.GiverLines(quest),' ')
    contains(lines,'Gryan Stoutmantle');contains(lines,'Westfall');contains(lines,'56.')
end)
check('Completed and active quest state',function()
    MOCK.completed={[166]=true};eq(Q.State(CD.QuestCatalog.quests[166]),'Completed')
    MOCK.completed={};MOCK.log={[166]=true};eq(Q.State(CD.QuestCatalog.quests[166]),'In quest log')
    MOCK.log={};contains(Q.State(CD.QuestCatalog.quests[166]),'Prerequisites')
end)
check('Legacy quest-log lookup finds quests under collapsed headers',function()
    local modern=C_QuestLog.GetLogIndexForQuestID
    C_QuestLog.GetLogIndexForQuestID=nil
    GetQuestLogIndexByID=function(id) return id==166 and 5 or 0 end
    assert(Q.InLog(166));assert(not Q.InLog(999999))
    C_QuestLog.GetLogIndexForQuestID=modern;GetQuestLogIndexByID=nil
end)
check('Missing coordinates are explicit and never formatted as invented zeros',function()
    contains(Q.LocationText({zone=1581}),'coordinates not recorded')
    contains(Q.LocationText({zone=40,x=56.7,y=47.4}),'56.7, 47.4')
    for _,quest in pairs(CD.QuestCatalog.quests) do
        for _,giver in ipairs(quest.givers) do
            for _,loc in ipairs(giver.locations) do
                if loc.x then assert(loc.x>=0 and loc.x<=100 and loc.y>=0 and loc.y<=100) end
            end
        end
        Q.GiverLines(quest)
    end
end)
check('AND and OR prerequisite states remain distinct',function()
    local q={id=999991,minLevel=1,previousAll={65,132},previousAny={},exclusive={}}
    MOCK.completed={[65]=true};contains(Q.State(q),'incomplete')
    q.previousAll={};q.previousAny={65,132};assert(not Q.State(q):find('incomplete',1,true))
    MOCK.completed={}
end)
check('No gear or bags are scanned by the journal',function()
    GetInventoryItemID=function() error('Unexpected inventory scan') end
    GetInventoryItemLink=function() error('Unexpected inventory scan') end
    C_Container.GetContainerNumSlots=function() error('Unexpected bag scan') end
    U.Show();assert(U.frame:IsShown())
end)
check('Dropdown contains every dungeon and selects one',function()
    eq(#U.options,#CD.Catalog.order)
    U.dropdown:GetScript('OnClick')();assert(U.menu:IsShown())
    local option=U.options[2];option:GetScript('OnClick')();eq(CD.db.lastDungeon,option.dungeonID)
    assert(not U.menu:IsShown());eq(U.dropdown.label:GetText(),CD.Catalog.dungeons[option.dungeonID].name)
    CD.SelectDungeon('the-deadmines')
end)
check('All loot is visible, irrespective of the obsolete upgrade filter',function()
    CD.db.onlyUpgrades=true;U.RenderLoot(true)
    local expected,actual=0,0
    local d=CD.Catalog.dungeons[CD.db.lastDungeon]
    for _,groups in ipairs({d.bosses,d.sharedLoot}) do for _,g in ipairs(groups) do expected=expected+#g.loot end end
    for _,row in ipairs(U.lootRows) do if row:IsShown() and row.item then actual=actual+1 end end
    eq(actual,expected)
end)
check('Tooltip uses the actual item hyperlink on hover and hides on leave',function()
    local row
    for _,r in ipairs(U.lootRows) do if r.item and r.item.id==5195 then row=r end end
    assert(row);row:GetScript('OnEnter')(row)
    eq(GameTooltip.link,row.item.link);eq(GameTooltip.owner,row);assert(GameTooltip:IsShown())
    row:GetScript('OnLeave')(row);assert(not GameTooltip:IsShown())
end)
check('Shift-click inserts item and quest links',function()
    MOCK.shift=true
    local row=U.lootRows[2];row:GetScript('OnClick')(row);eq(MOCK.inserted,row.item.link)
    row=U.questRows[1];row:GetScript('OnClick')(row);contains(MOCK.inserted,'|Hquest:')
    MOCK.shift=false
end)
check('Quest chain expansion includes earlier givers',function()
    local row
    for _,r in ipairs(U.questRows) do if r.quest and r.quest.id==166 then row=r end end
    assert(row);local old=row:GetHeight();row:GetScript('OnClick')(row)
    assert(U.expanded[166]);assert(row:GetHeight()>old);contains(row.chain:GetText(),'Quest giver:')
end)
check('Long loot rows do not overlap and scrollbars clamp',function()
    local total=0
    for _,r in ipairs(U.lootRows) do
        if r:IsShown() then eq(-(r.point[5] or r.point[3]),total);total=total+r:GetHeight() end
    end
    assert(U.lootScroll.child:GetHeight()>=total)
    U.lootScroll:Scroll(1e9);eq(U.lootScroll:GetVerticalScroll(),U.lootScroll.child:GetHeight()-U.lootScroll:GetHeight())
    U.lootScroll:GetScript('OnMouseWheel')(U.lootScroll,1e6);eq(U.lootScroll:GetVerticalScroll(),0)
    U.questScroll:Scroll(1e9);assert(U.questScroll:GetVerticalScroll()>0)
end)
check('Request loading is bounded and does not mutate gameplay',function()
    I.Reset();MOCK.requests={};CD.QueueItems();MOCK.advance(.05)
    local requests=0;for _ in pairs(MOCK.requests) do requests=requests+1 end
    assert(requests<=6 and requests>0)
    MOCK.advance(10);eq(CD.queue,nil);eq(CD.frame:GetScript('OnUpdate'),nil)
end)
check('All classes and factions browse every dungeon without missing rows',function()
    local runs=0
    for _,faction in ipairs({'Alliance','Horde'}) do
        MOCK.faction=faction;MOCK.race=faction=='Horde' and 2 or 3
        for _,class in ipairs({'WARRIOR','PALADIN','HUNTER','ROGUE','PRIEST','SHAMAN','MAGE','WARLOCK','DRUID'}) do
            MOCK.class=class
            for _,id in ipairs(CD.Catalog.order) do
                CD.SelectDungeon(id);assert(#Q.List(CD.Catalog.dungeons[id])>=0)
                for _,row in ipairs(U.lootRows) do
                    if row:IsShown() and row.item then assert(row.stats:GetText()~='');assert(row:GetHeight()>=40) end
                end
                runs=runs+1
            end
        end
    end
    eq(runs,468);print('JOURNAL '..runs..' complete class/faction/dungeon renders')
end)
print('JOURNAL '..count..' behavior, data and UI checks')
