local S,U,I=CD.Search,CD.UI,CD.Items
local count=0
local function check(name,fn) fn();count=count+1;print('OK SEARCH '..name) end
local function parse(s) local filter,err=S.Parse(s);assert(filter,err);return filter end
local function matches(item,s) return S.Matches(item,parse(s)) end
local item={name="Sentinel's Gloves",level=20,quality=3,itemLevel=25,dps=12.3,weaponSpeed=2.4,
    classID=4,subclassID=2,loc='INVTYPE_HAND',
    live=true,stats={agi=5,sta=2,armor=40,crit=1.5,str=-2,fireRes=5},otherStats={ITEM_MOD_UNKNOWN_SHORT=7}}

check('Empty searches preserve all loot',function() assert(matches(item,''));assert(matches(item,'  ')) end)
check('Names are literal, case-insensitive and support apostrophes',function()
    assert(matches(item,"sentinel's GLOVES"));assert(not matches(item,'boots'))
    assert(not matches(item,'Gloves.*'))
end)
check('Quoted name fragments and stats work together',function()
    assert(matches(item,'"Sentinel\'s Gloves", agi >= 5'))
    assert(not matches(item,'"Gloves Sentinel"'))
end)
check('Boundary comparisons include exactly five agility',function()
    assert(matches(item,'agi>=5'));assert(not matches(item,'agi>5'))
    assert(matches(item,'agi<=5'));assert(not matches(item,'agi<5'))
    assert(matches(item,'agi=5'));assert(matches(item,'agi==5'))
    assert(matches(item,'agi!=4'));assert(not matches(item,'agi!=5'));assert(matches(item,'agi~=4'))
end)
check('More than two conditions must all match',function()
    assert(matches(item,'agi >= 5, sta >= 2, armor >= 40, req <= 20, quality = 3, ilvl > 24'))
    assert(not matches(item,'agi >= 5, sta >= 2, armor > 40, req <= 20'))
end)
check('Condition count is not capped',function()
    local list={};for i=1,150 do list[i]='agi >= 5' end
    assert(matches(item,table.concat(list,', ')))
end)
check('Whitespace AND ampersands and semicolons combine conditions',function()
    assert(matches(item,'AGI>=5 AND STA>=2 armor=40; crit>=1.5 & req<=20'))
end)
check('All published numeric fields can be filtered',function()
    for _,field in ipairs(S.fields) do
        local fixture={name='Fixture',live=true,stats={},otherStats={}}
        fixture[field.key]=2;fixture.stats[field.key]=2
        assert(matches(fixture,field.key..'>=1'),field.key)
    end
end)
check('Long aliases raw API keys and unrecognized numeric stats',function()
    assert(matches(item,'agility>=5, stamina>=2, armour>=40'))
    assert(matches(item,'ITEM_MOD_AGILITY_SHORT>=5'))
    assert(matches(item,'ITEM_MOD_UNKNOWN_SHORT>=7'))
end)
check('Weapon metadata decimals negative stats percentages and absent stats',function()
    assert(matches(item,'dps>=12.3 speed<2.5 str=-2 crit>=1.5%'))
    assert(matches(item,'int=0'));assert(not matches(item,'int>0'))
end)
check('Cold-cache unbundled effects do not produce a false zero match',function()
    local cold={name='Effect item',live=false,effects=true,stats={agi=5}}
    assert(not matches(cold,'sp=0'));assert(matches(cold,'agi=5'))
    cold.live=true;assert(matches(cold,'sp=0'))
end)
check('Malformed inputs receive actionable errors and are never evaluated',function()
    for _,query in ipairs({'agi >=','agi => 5','agi>=5foo','agi>=5.2.1','agii >= 2','>= 4','"unclosed'}) do
        local filter,err=S.Parse(query);assert(not filter and err,query)
    end
    local filter=S.Parse('agi=5; loadstring("error()")()')
    assert(filter and not S.Matches(item,filter))
end)

MOCK.class,MOCK.faction,MOCK.race,MOCK.level='HUNTER','Alliance',3,20
CD.SelectDungeon('the-deadmines')
check('Search UI filters actual drops and removes empty boss headers',function()
    U.search:SetText('str >= 4, int >= 3, req <= 17')
    local ids,headers={},0
    for _,row in ipairs(U.lootRows) do
        if row:IsShown() then
            if row.item then ids[#ids+1]=row.item.id;assert(S.Matches(row.item,parse(U.search:GetText())))
            else headers=headers+1 end
        end
    end
    assert(#ids==1 and ids[1]==5195);assert(headers==1)
end)
check('No results and invalid expressions have distinct feedback',function()
    U.search:SetText('agi > 1000');assert(U.searchEmpty:IsShown())
    assert(U.searchEmpty:GetText():find('No items',1,true))
    U.search:SetText('agi >=');assert(U.searchEmpty:GetText():find('Fix',1,true))
    assert(U.searchHint:GetText():find('number',1,true))
end)
check('Clear restores rows, scroll and leaves quests unchanged',function()
    local quest=U.questRows[1].quest.id
    U.clearSearch:GetScript('OnClick')()
    assert(U.search:GetText()=='');assert(not U.searchEmpty:IsShown())
    assert(U.questRows[1].quest.id==quest);assert(U.lootScroll:GetVerticalScroll()==0)
end)
check('Native live resistance stats use the same filter field as bundled values',function()
    MOCK.items[5195].stats.RESISTANCE2_NAME=5
    local it=I.Read(5195);assert(it.stats.fireRes==5);assert(matches(it,'fireRes>=5'))
    MOCK.items[5195].stats.RESISTANCE2_NAME=nil
end)
check('Armor types use numeric metadata instead of item-name words',function()
    for subclass,kind in ipairs({'cloth','leather','mail','plate'}) do
        local armor={name='Mailroom Gloves',classID=4,subclassID=subclass,loc='INVTYPE_HAND',stats={}}
        assert(matches(armor,kind));assert(matches(armor,'type='..kind));assert(matches(armor,'armor:'..kind))
        assert(matches(armor,'cloth|leather|mail|plate'))
    end
    assert(not matches({name='Cloth Ring',classID=4,subclassID=0,loc='INVTYPE_FINGER',stats={}},'cloth'))
    assert(not matches({name='Plate Sword',classID=2,subclassID=4,stats={}},'plate'))
end)
check('Slot filters match jewelry and armor even without English slot words in the name',function()
    for keyword,loc in pairs({ring='FINGER',trinket='TRINKET',neck='NECK',head='HEAD',shoulder='SHOULDER',
        back='CLOAK',chest='CHEST',shirt='BODY',wrist='WRIST',hands='HAND',waist='WAIST',legs='LEGS',feet='FEET',
        ranged='RANGED',relic='RELIC',shield='SHIELD',tabard='TABARD',bag='BAG',ammo='AMMO'}) do
        local it={name='Unrelated Name',loc='INVTYPE_'..loc,stats={}}
        assert(matches(it,keyword),keyword);assert(matches(it,'slot:'..keyword),keyword)
    end
end)
check('Alternative types and slots combine with unlimited AND conditions',function()
    assert(matches(item,'cloth|leather, gloves|head, agi >= 5, sta >= 2, req <= 20'))
    assert(matches(item,'type:cloth | leather, slot:head | hands, armor = 40'))
    assert(not matches(item,'mail|plate, hands, agi>=5'))
    assert(not matches(item,'leather, ring|trinket|neck'))
end)
check('Categorical alternatives may include jewelry alongside armor',function()
    local ring={name='Lavishly Jeweled Ring',classID=4,subclassID=0,loc='INVTYPE_FINGER',stats={int=2}}
    assert(matches(ring,'cloth|leather|ring|trinket, int>=2'))
    assert(not matches(ring,'cloth|leather, int>=2'))
end)
check('Common slot aliases and case variants work',function()
    assert(matches(item,'LEATHER, slot = GLOVES, stamina >= 2'))
    assert(matches(item,'hand'));assert(matches(item,'hands'))
    local feet={name='Footwear',loc='INVTYPE_FEET',stats={}}
    assert(matches(feet,'boots'));assert(matches(feet,'slot:feet'))
end)
check('Chest includes robes; mainhand and offhand respect inventory types',function()
    assert(matches({loc='INVTYPE_ROBE',stats={}},'chest'))
    assert(matches({loc='INVTYPE_2HWEAPON',stats={}},'main_hand'))
    assert(not matches({loc='INVTYPE_2HWEAPON',stats={}},'offhand'))
    assert(matches({loc='INVTYPE_WEAPON',stats={}},'mainhand'))
    assert(matches({loc='INVTYPE_WEAPON',stats={}},'off-hand'))
    assert(matches({loc='INVTYPE_HOLDABLE',stats={}},'offhand'))
    assert(not matches({loc='INVTYPE_WEAPONOFFHAND',stats={}},'mainhand'))
end)
check('Quoted slot names remain literal name searches',function()
    assert(matches({name='Ring of Power',loc='INVTYPE_TRINKET',stats={}},'"ring"'))
    assert(not matches({name='Ring of Power',loc='INVTYPE_TRINKET',stats={}},'ring'))
    assert(matches({name='Cloth Cap',classID=4,subclassID=2,stats={}},'"cloth"'))
end)
check('Malformed alternatives report errors and numeric armor comparisons remain valid',function()
    for _,query in ipairs({'cloth|','cloth||leather','slot:unknown','type:plat','ring|unknown'}) do
        local filter,err=S.Parse(query);assert(not filter and err,query)
    end
    assert(matches(item,'armor=40'));assert(matches(item,'armor>=40'))
end)
check('Containers and ammo can be recognized before their native slot label loads',function()
    assert(matches({classID=1,loc='',stats={}},'bag'))
    assert(matches({classID=11,loc='',stats={}},'quiver'))
    assert(matches({classID=6,loc='',stats={}},'ammo'))
end)
check('Instant native slot metadata works when the full item cache is cold',function()
    MOCK.items[5195].cold=true
    local it=I.Read(5195);assert(not it.live);assert(matches(it,'cloth, hands, int>=3'))
    assert(it.icon==123)
    MOCK.items[5195].cold=nil
end)
check('Material and slot searches filter actual visible loot',function()
    U.search:SetText('cloth, hands, int >= 3')
    local ids={}
    for _,row in ipairs(U.lootRows) do
        if row:IsShown() and row.item then ids[#ids+1]=row.item.id end
    end
    assert(#ids==1 and ids[1]==5195)
    U.search:SetText('ring|trinket|neck')
    local count=0
    for _,row in ipairs(U.lootRows) do
        if row:IsShown() and row.item then count=count+1;assert(row.item.loc=='INVTYPE_FINGER' or row.item.loc=='INVTYPE_TRINKET' or row.item.loc=='INVTYPE_NECK') end
    end
    assert(count>0)
    U.clearSearch:GetScript('OnClick')()
end)
print('SEARCH '..count..' parsing, multi-stat and UI checks')
