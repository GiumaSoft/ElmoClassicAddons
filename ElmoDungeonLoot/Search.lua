local _,CD=...
local S={}
CD.Search=S
local aliases,fields={},{}
local function add(key,label,...)
    aliases[key:lower()]=key
    fields[#fields+1]={key=key,label=label}
    for _,alias in ipairs({...}) do aliases[alias]=key end
end
for _,stat in ipairs(CD.Items.StatOrder) do add(stat[1],stat[2]) end
for raw,key in pairs(CD.Items.StatKeys) do aliases[raw:lower()]=key end
add("armor","Armor","armour")
for key,canonical in pairs({strength="str",agility="agi",stamina="sta",intellect="int",spi="spirit",
    attackpower="ap",rangedap="rap",rangedattackpower="rap",feralattackpower="feralap",
    spellpower="sp",spelldamage="damage",heal="healing",spell_hit="spellhit",spell_crit="spellcrit",
    blockchance="block",block_value="blockValue",fire_res="fireRes",frost_res="frostRes",
    nature_res="natureRes",shadow_res="shadowRes",arcane_res="arcaneRes",holy_res="holyRes"}) do aliases[key]=canonical end
add("dps","Weapon DPS")
add("weaponSpeed","Weapon speed","speed")
add("damageMin","Minimum weapon damage","mindmg","min_damage")
add("damageMax","Maximum weapon damage","maxdmg","max_damage")
add("level","Required level","req","reqlevel","req_level","lvl")
add("itemLevel","Item level","ilvl","ilevel")
add("quality","Item quality")
S.fields=fields
local top={dps=true,weaponSpeed=true,damageMin=true,damageMax=true,level=true,itemLevel=true,quality=true}
local basic={str=true,agi=true,sta=true,int=true,spirit=true,armor=true,mana=true,health=true,
    fireRes=true,frostRes=true,natureRes=true,shadowRes=true,arcaneRes=true,holyRes=true,blockValue=true}
local operations={
    [">="]=function(a,b) return a>=b end,[">"]=function(a,b) return a>b end,
    ["<="]=function(a,b) return a<=b end,["<"]=function(a,b) return a<b end,
    ["="]=function(a,b) return a==b end,["=="]=function(a,b) return a==b end,
    ["!="]=function(a,b) return a~=b end,["~="]=function(a,b) return a~=b end,
}

local armorTypes={cloth=1,leather=2,mail=3,plate=4}
local slots={
    head={"HEAD"},neck={"NECK"},shoulder={"SHOULDER"},back={"CLOAK"},
    chest={"CHEST","ROBE"},shirt={"BODY"},wrist={"WRIST"},hands={"HAND"},
    waist={"WAIST"},legs={"LEGS"},feet={"FEET"},ring={"FINGER"},trinket={"TRINKET"},
    mainhand={"WEAPON","WEAPONMAINHAND","2HWEAPON"},
    offhand={"WEAPON","WEAPONOFFHAND","SHIELD","HOLDABLE"},
    ranged={"RANGED","RANGEDRIGHT","THROWN","RELIC"},relic={"RELIC"},
    shield={"SHIELD"},twohand={"2HWEAPON"},bag={"BAG","QUIVER"},ammo={"AMMO"},tabard={"TABARD"},
}
local slotOrder={"head","neck","shoulder","back","chest","shirt","wrist","hands","waist","legs","feet",
    "ring","trinket","mainhand","offhand","ranged","relic","shield","twohand","bag","ammo","tabard"}
local slotAliases={helm="head",helmet="head",necklace="neck",shoulders="shoulder",cloak="back",cape="back",
    robe="chest",robes="chest",body="shirt",wrists="wrist",bracer="wrist",bracers="wrist",hand="hands",gloves="hands",
    belt="waist",pants="legs",boots="feet",rings="ring",finger="ring",fingers="ring",trinkets="trinket",
    mh="mainhand",oh="offhand",twohanded="twohand",bags="bag",quiver="bag"}
local function category(word,field)
    word=word:lower():gsub("[_%-]","")
    if field~="slot" and armorTypes[word] then return {kind="armor",value=word} end
    local slot=slotAliases[word] or word
    if field~="armor" and slots[slot] then return {kind="slot",value=slot} end
end

-- A clause may contain any number of categorical alternatives joined by |.
-- Separate clauses (including numeric ones) still use AND.
local function readCategories(rest)
    local original,group,field=rest,{},nil
    while true do
        local prefix,separator,tail=rest:match("^([%a_]+)%s*([:=])%s*(.*)")
        local explicit=false
        if prefix then
            local key=prefix:lower()
            if key=="type" or key=="slot" or ((key=="armor" or key=="armour") and separator==":") then
                field=key=="slot" and "slot" or "armor"
                rest=tail;explicit=true
            end
        end
        local word=rest:match("^([%a_][%w_%-]*)")
        local value=word and category(word,field)
        local suffix=word and rest:sub(#word+1) or rest
        local boundary=suffix:sub(1,1)
        if not value or (boundary~="" and not boundary:match("[%s,;&|]")) then
            if #group>0 or explicit then
                return nil,original,"Unknown "..(field or "armor type or slot")..". Click ? for supported values.",true
            end
            return nil,original,nil,false
        end
        group[#group+1]=value
        local afterPipe=suffix:match("^%s*|%s*(.*)")
        if afterPipe==nil then return group,suffix,nil,true end
        rest=afterPipe
    end
end

local function matchesCategory(item,choice)
    if choice.kind=="armor" then return item.classID==4 and item.subclassID==armorTypes[choice.value] end
    local loc=item.loc or ""
    for _,suffix in ipairs(slots[choice.value]) do
        if loc=="INVTYPE_"..suffix then return true end
    end
    -- Container/ammo types are also reliable before their native slot label loads.
    return choice.value=="bag" and (item.classID==1 or item.classID==11)
        or choice.value=="ammo" and item.classID==6 or false
end

function S.Parse(query)
    local result={names={},conditions={},categories={},active=false}
    query=(query or ""):match("^%s*(.-)%s*$")
    local rest=query
    while rest~="" do
        rest=rest:gsub("^[%s,;&]+","")
        local conjunction=rest:match("^([Aa][Nn][Dd])%f[%W]")
        if conjunction then rest=rest:sub(#conjunction+1):gsub("^%s+","") end
        if rest=="" then break end
        result.active=true
        if rest:sub(1,1)=='"' then
            local last=rest:find('"',2,true)
            if not last then return nil,"Close the quoted item name with a double quote." end
            local phrase=rest:sub(2,last-1):lower()
            if phrase~="" then result.names[#result.names+1]=phrase end
            rest=rest:sub(last+1)
        else
            local choices,tail,categoryError,handled=readCategories(rest)
            local key,op=rest:match("^([%a_][%w_]*)%s*([<>!=~]+)")
            if categoryError then return nil,categoryError
            elseif handled then
                result.categories[#result.categories+1]=choices;rest=tail
            elseif key then
                local canonical=aliases[key:lower()]
                if not canonical and key:upper():match("^ITEM_MOD_[A-Z_0-9]+$") then canonical=key:upper() end
                if not canonical then return nil,"Unknown stat: "..key:sub(1,24)..". Click ? for supported stats." end
                if not operations[op] then return nil,"Use >, >=, <, <=, = or != for comparisons." end
                local prefix=rest:match("^[%a_][%w_]*%s*[<>!=~]+%s*")
                local tail=rest:sub(#prefix+1)
                local value=tail:match("^([+-]?%d*%.?%d+)")
                if not value then return nil,"Enter a number after "..key.." "..op.."." end
                local used=#value
                if tail:sub(used+1,used+1)=="%" then used=used+1 end
                local nextChar=tail:sub(used+1,used+1)
                if nextChar~="" and not nextChar:match("[%s,;&]") then
                    return nil,"Separate conditions with a comma, a space or AND. Use a decimal point." end
                local n=tonumber(value)
                if not CD.Number(n) then return nil,"Enter a finite number." end
                result.conditions[#result.conditions+1]={key=canonical,op=op,value=n}
                rest=tail:sub(used+1)
            else
                if rest:sub(1,1):match("[<>!=~]") then return nil,"Enter a stat before the comparison." end
                local name=rest:match('^([^%s,;&]+)')
                if not name then return nil,"Invalid search expression." end
                if name:find("|",1,true) then return nil,"Use | between armor types or slots; quote literal names." end
                result.names[#result.names+1]=name:lower();rest=rest:sub(#name+1)
            end
        end
    end
    return result
end

function S.Matches(item,filter)
    if not filter then return false end
    local name=(item.name or ""):lower()
    for _,part in ipairs(filter.names) do
        if not name:find(part,1,true) then return false end
    end
    for _,group in ipairs(filter.categories or {}) do
        local found=false
        for _,choice in ipairs(group) do
            if matchesCategory(item,choice) then found=true;break end
        end
        if not found then return false end
    end
    for _,condition in ipairs(filter.conditions) do
        local key=condition.key
        local value=top[key] and item[key] or (item.stats or {})[key] or (item.otherStats or {})[key]
        if value==nil then
            -- A cold cache cannot establish an unbundled Equip bonus. Re-evaluate
            -- when the selected dungeon's live item-data request completes.
            if not item.live and item.effects and not basic[key] and not top[key] then return false end
            value=0
        end
        if not operations[condition.op](value,condition.value) then return false end
    end
    return true
end

function S.HelpLines()
    local lines={"Names, armor types, slots and any number of stat conditions can be combined.",
        "All conditions must match (AND). Separate with commas, spaces or AND.",
        "Armor types: cloth · leather · mail · plate",
        "Slots: "..table.concat(slotOrder," · "),
        "Use | for alternatives: cloth|leather, head|chest, sta >= 5",
        "Explicit fields: type:mail, slot:ring|trinket · Quote literal names: \"ring\"",
        "Operators: >  >=  <  <=  =  !=  · Decimals: 2.5 · Percentages: crit >= 1%",
        "Stats and their search names:"}
    local group={}
    for _,field in ipairs(fields) do
        group[#group+1]=field.key.." ("..field.label..")"
        if #group==3 then lines[#lines+1]=table.concat(group," · ");group={} end
    end
    if #group>0 then lines[#lines+1]=table.concat(group," · ") end
    return lines
end
