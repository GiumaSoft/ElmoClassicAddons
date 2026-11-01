local _, CD = ...
local A = {cache={},cacheCount=0,requested={}}
CD.Items = A
local call, number, text, tab = CD.Call, CD.Number, CD.Text, CD.Table

local statKeys = {
    ITEM_MOD_STRENGTH_SHORT="str",ITEM_MOD_AGILITY_SHORT="agi",ITEM_MOD_STAMINA_SHORT="sta",
    ITEM_MOD_INTELLECT_SHORT="int",ITEM_MOD_SPIRIT_SHORT="spirit",ITEM_MOD_MANA_SHORT="mana",
    ITEM_MOD_HEALTH_SHORT="health",RESISTANCE0_NAME="armor",ITEM_MOD_ARMOR_SHORT="armor",
    RESISTANCE1_NAME="holyRes",RESISTANCE2_NAME="fireRes",RESISTANCE3_NAME="natureRes",
    RESISTANCE4_NAME="frostRes",RESISTANCE5_NAME="shadowRes",RESISTANCE6_NAME="arcaneRes",
    ITEM_MOD_EXTRA_ARMOR_SHORT="armor",ITEM_MOD_ATTACK_POWER_SHORT="ap",
    ITEM_MOD_RANGED_ATTACK_POWER_SHORT="rap",ITEM_MOD_FERAL_ATTACK_POWER_SHORT="feralap",
    ITEM_MOD_SPELL_POWER_SHORT="sp",ITEM_MOD_SPELL_DAMAGE_DONE_SHORT="damage",
    ITEM_MOD_SPELL_HEALING_DONE_SHORT="healing",ITEM_MOD_MANA_REGENERATION_SHORT="mp5",
    ITEM_MOD_POWER_REGEN0_SHORT="mp5",ITEM_MOD_HEALTH_REGEN_SHORT="hp5",
    ITEM_MOD_HEALTH_REGENERATION_SHORT="hp5",ITEM_MOD_CRIT_RATING_SHORT="crit",
    ITEM_MOD_CRIT_MELEE_RATING_SHORT="crit",ITEM_MOD_CRIT_RANGED_RATING_SHORT="crit",
    ITEM_MOD_CRIT_SPELL_RATING_SHORT="spellcrit",ITEM_MOD_HIT_RATING_SHORT="hit",
    ITEM_MOD_HIT_MELEE_RATING_SHORT="hit",ITEM_MOD_HIT_RANGED_RATING_SHORT="hit",
    ITEM_MOD_HIT_SPELL_RATING_SHORT="spellhit",ITEM_MOD_HASTE_RATING_SHORT="haste",
    ITEM_MOD_HASTE_MELEE_RATING_SHORT="haste",ITEM_MOD_HASTE_RANGED_RATING_SHORT="haste",
    ITEM_MOD_HASTE_SPELL_RATING_SHORT="haste",ITEM_MOD_EXPERTISE_RATING_SHORT="expertise",
    ITEM_MOD_DEFENSE_SKILL_RATING_SHORT="defense",ITEM_MOD_DODGE_RATING_SHORT="dodge",
    ITEM_MOD_PARRY_RATING_SHORT="parry",ITEM_MOD_BLOCK_RATING_SHORT="block",
    ITEM_MOD_BLOCK_VALUE_SHORT="blockValue",ITEM_MOD_SPELL_PENETRATION_SHORT="spellpen",
    ITEM_MOD_DAMAGE_PER_SECOND_SHORT="dps",ITEM_MOD_PHYSICAL_DAMAGE_SHORT="weaponDamage",
    ITEM_MOD_FIRE_DAMAGE_SHORT="fire",ITEM_MOD_FROST_DAMAGE_SHORT="frost",
    ITEM_MOD_SHADOW_DAMAGE_SHORT="shadow",ITEM_MOD_ARCANE_DAMAGE_SHORT="arcane",
    ITEM_MOD_NATURE_DAMAGE_SHORT="nature",ITEM_MOD_HOLY_DAMAGE_SHORT="holy",
}
A.StatKeys=statKeys

local function itemAPI(name, fallback)
    return C_Item and C_Item[name] or _G[fallback or name]
end

function A.Reset()
    A.cache, A.requested, A.cacheCount = {}, {}, 0
end

function A.Request(id)
    if not id or A.requested[id] then return end
    A.requested[id] = true
    call(itemAPI("RequestLoadItemDataByID"), id)
end

local function numericToken(value)
    return tonumber((value:gsub(",", ".")))
end

local function templatePattern(format)
    if not text(format) then return nil end
    local pattern = format:gsub("%%[%d%.%$]*[dfs]", "CDNUMBER")
    pattern = pattern:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1")
    return "^" .. pattern:gsub("CDNUMBER", "([%d%.,]+)") .. "$"
end

local primaryStats={Strength="str",Agility="agi",Stamina="sta",Intellect="int",Spirit="spirit"}

local function tooltip(item, location)
    local api=C_TooltipInfo or {}
    local raw
    if location and location.equipmentSlot then
        raw=call(api.GetInventoryItem,"player",location.equipmentSlot,false)
        item.tooltipSource="inventory"
    elseif location and location.bag~=nil then
        raw=call(api.GetBagItem,location.bag,location.slot)
        item.tooltipSource="bag"
    else
        raw=call(api.GetHyperlink,item.link);item.tooltipSource="link"
    end
    local data = tab(raw)
    local lines = data and tab(data.lines)
    if not lines and not CD.IsSecret(raw) then
        data = tab(CD.Compat.ReadTooltip(item.link, location))
        lines = data and tab(data.lines)
    end
    if not lines then return false end
    local dpsPattern = templatePattern(_G.DPS_TEMPLATE)
    local blockPattern = templatePattern(_G.SHIELD_BLOCK_TEMPLATE)
    local damagePattern = templatePattern(_G.DAMAGE_TEMPLATE)
    local english = (text(call(GetLocale)) or "enUS") == "enUS"
    local minimum,maximum,speed,tooltipBlock
    local primary={}
    local classicBonuses={}
    for index = 1, math.min(#lines, 100) do
        local line = tab(lines[index])
        local seen={}
        for _,field in ipairs({"leftText","rightText","text"}) do
            local value = line and text(line[field])
            if value and not seen[value] then
                seen[value]=true
                value = value:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
                local dps = (dpsPattern and value:match(dpsPattern))
                    or (english and value:match("%(([%d%.]+) damage per second%)"))
                if dps then item.dps = numericToken(dps) end
                local low,high
                if damagePattern then low,high=value:match(damagePattern) end
                if not low and english then low,high=value:match("^([%d%.,]+)%s*%-%s*([%d%.,]+) Damage$") end
                if low and high then minimum,maximum=numericToken(low),numericToken(high) end
                local delay=english and value:match("^Speed%s+([%d%.,]+)$")
                if delay then speed=numericToken(delay) end
                local block = blockPattern and value:match(blockPattern)
                    or (english and value:match("^(%d+) Block$"))
                if block then tooltipBlock = numericToken(block) end
                if english then
                    local parsedEquip=false
                    local classicStat,classicAmount=CD.Compat.ReadBonus(value)
                    if classicStat then
                        classicBonuses[classicStat]=(classicBonuses[classicStat] or 0)+classicAmount
                        parsedEquip=true
                    end
                    -- Supplement primary attributes omitted by GetItemStats, using the actual item's tooltip.
                    local amount,name=value:match("^([%+%-]?[%d%.,]+)%s+(%a+)$")
                    local key=primaryStats[name]
                    if key then primary[key]=(primary[key] or 0)+numericToken(amount) end
                    -- Flat school bonuses and flat healing are sometimes omitted from GetItemStats.
                    for school, stat in pairs({Shadow="shadow",Fire="fire",Frost="frost",Nature="nature",
                            Arcane="arcane",Holy="holy"}) do
                        local bonus = value:match("^Equip: %+([%d%.]+) " .. school .. " Spell Damage$")
                        if bonus then item.stats[stat] = math.max(item.stats[stat] or 0, tonumber(bonus));parsedEquip=true end
                    end
                    local power = value:match("^Equip: %+([%d%.]+) Spell Power$")
                    local healing = value:match("^Equip: %+([%d%.]+) Healing$")
                    local damage = value:match("^Equip: %+([%d%.]+) Spell Damage$")
                    if power then item.stats.sp = math.max(item.stats.sp or 0, tonumber(power)) end
                    if healing then item.stats.healing = math.max(item.stats.healing or 0, tonumber(healing)) end
                    if damage then item.stats.damage = math.max(item.stats.damage or 0, tonumber(damage)) end
                    if value:find("^Equip:") and not (parsedEquip or power or healing or damage) then
                        item.effects=true
                        item.effectLines[#item.effectLines+1]=value
                    end
                    if value:find("^Unique") then
                        item.uniqueMax = tonumber(value:match("%((%d+)%)")) or 1
                    end
                    if value:find("^Use:") or value:find("^Chance on hit:") or value:find(" Set:",1,true) then
                        item.effects = true
                        item.effectLines[#item.effectLines+1]=value
                    end
                end
            end
        end
    end
    for stat,amount in pairs(primary) do
        if item.stats[stat]==nil then item.stats[stat]=amount end
    end
    if tooltipBlock then
        item.stats.blockValue=math.max(item.stats.blockValue or 0,tooltipBlock+(classicBonuses.blockValue or 0))
    end
    for stat,amount in pairs(classicBonuses) do
        item.stats[stat]=math.max(item.stats[stat] or 0,amount)
    end
    if not item.dps and minimum and maximum and speed and speed>0 then
        item.dps=(minimum+maximum)/(2*speed)
    end
    -- Match the displayed DPS precision for both the owned copy and the drop.
    -- 20–39 / 2.40 must not lose to the identical weapon displayed as 12.3 DPS.
    if item.dps then item.dps=math.floor(item.dps*10+.5)/10 end
    item.damageMin,item.damageMax,item.weaponSpeed=minimum,maximum,speed
    return true
end

local classIds={WARRIOR=1,PALADIN=2,HUNTER=3,ROGUE=4,PRIEST=5,SHAMAN=7,MAGE=8,WARLOCK=9,DRUID=11}
local armorNames={[0]="Miscellaneous",[1]="Cloth",[2]="Leather",[3]="Mail",[4]="Plate",[6]="Shield",[7]="Libram",[8]="Idol",[9]="Totem"}
local weaponNames={[0]="Axe",[1]="Two-hand axe",[2]="Bow",[3]="Gun",[4]="Mace",[5]="Two-hand mace",[6]="Polearm",[7]="Sword",[8]="Two-hand sword",[10]="Staff",[13]="Fist weapon",[15]="Dagger",[16]="Thrown",[18]="Crossbow",[19]="Wand",[20]="Fishing pole"}

function A.HasMask(mask, id)
    if not mask or mask<=0 then return true end
    return id and math.floor(mask/2^(id-1))%2==1 or false
end

function A.Character()
    local name,class,id=call(UnitClass,"player")
    local _,_,raceId=call(UnitRace,"player")
    return {class=text(class),className=text(name),classID=number(id) or classIds[class],
        raceID=number(raceId),level=number(call(UnitLevel,"player")) or 0,
        faction=text(call(UnitFactionGroup,"player")) or "Alliance"}
end

function A.Eligibility(item)
    local who=A.Character()
    if (item.level or 0)>who.level then return false,"Requires level "..item.level end
    if not A.HasMask(item.classes,who.classID) then return false,"Class restriction" end
    if who.raceID and not A.HasMask(item.races,who.raceID) then return false,"Race restriction" end
    if item.classID==12 then return nil,"Quest item" end
    local usable
    if item.live then usable=CD.Bool(call(C_PlayerInfo and C_PlayerInfo.CanUseItem,item.id)) end
    if usable==true then return true,"Usable" end
    if usable==false then return false,"Requirements not met" end
    return nil,"Check requirements"
end

function A.Read(id)
    local fact=CD.Catalog.items[id]
    if not fact then return {id=id,name="Item #"..tostring(id),stats={},effectLines={},reason="No catalogue data"} end
    local item=CD.Copy(fact)
    item.stats,item.otherStats,item.effectLines=CD.Copy(fact.stats),{},{}
    item.link="item:"..id
    local name,link,quality,itemLevel,level,itemType,subtype,_,loc,icon=call(itemAPI("GetItemInfo"),id)
    local _,_,_,instantLoc,instantIcon,instantClass,instantSub=call(itemAPI("GetItemInfoInstant"),id)
    item.loc=text(loc) or text(instantLoc) or item.loc
    item.icon=number(icon) or number(instantIcon)
    item.classID=number(instantClass) or item.classID
    item.subclassID=number(instantSub) or item.subclassID
    item.live=text(name)~=nil and text(link)~=nil
    item.ready=true -- Base stats are bundled and available even with a cold client cache.
    item.itemType=text(itemType)
    item.itemSubType=text(subtype) or (item.classID==2 and weaponNames[item.subclassID])
        or (item.classID==4 and armorNames[item.subclassID])
    if item.live then
        item.name,item.link=text(name),text(link)
        item.quality=number(quality) or item.quality
        item.itemLevel=number(itemLevel) or item.itemLevel
        item.level=number(level) or item.level
        item.loc=text(loc) or item.loc
        local raw=tab(call(itemAPI("GetItemStats"),item.link))
        if raw then
            item.stats={}
            for key,value in pairs(raw) do
                local stat,amount=text(key) and statKeys[key],number(value)
                if stat and amount then item.stats[stat]=amount
                elseif text(key) and amount and amount~=0 then item.otherStats[key]=amount end
            end
        end
        item.dps=item.stats.dps or item.dps
        tooltip(item)
    end
    item.usable,item.useReason=A.Eligibility(item)
    return item
end

local statOrder={
    {"str","STR"},{"agi","AGI"},{"sta","STA"},{"int","INT"},{"spirit","SPI"},
    {"ap","AP"},{"rap","Ranged AP"},{"feralap","Feral AP"},
    {"sp","Spell power"},{"damage","Spell damage"},{"healing","Healing"},
    {"hit","Hit",true},{"crit","Crit",true},{"spellhit","Spell hit",true},{"spellcrit","Spell crit",true},
    {"defense","Defense"},{"dodge","Dodge",true},{"parry","Parry",true},{"block","Block",true},
    {"blockValue","Block value"},{"mp5","MP5"},{"hp5","HP5"},{"mana","Mana"},{"health","Health"},
    {"shadow","Shadow damage"},{"fire","Fire damage"},{"frost","Frost damage"},
    {"nature","Nature damage"},{"arcane","Arcane damage"},{"holy","Holy damage"},
    {"holyRes","Holy resist"},{"fireRes","Fire resist"},{"natureRes","Nature resist"},
    {"frostRes","Frost resist"},{"shadowRes","Shadow resist"},{"arcaneRes","Arcane resist"},
    {"weaponDamage","Weapon damage"},{"haste","Haste",true},{"expertise","Expertise"},{"spellpen","Spell penetration"},
}
A.StatOrder=statOrder
local function fmt(n) return (string.format("%.2f",n):gsub("%.?0+$","")) end
function A.FormatStats(item)
    local parts,stats={},item.stats or {}
    if item.itemSubType then parts[#parts+1]=item.itemSubType end
    if item.dps then parts[#parts+1]=fmt(item.dps).." DPS" end
    if item.damageMin and item.damageMax then parts[#parts+1]=fmt(item.damageMin).."–"..fmt(item.damageMax).." damage" end
    if item.weaponSpeed then parts[#parts+1]="Speed "..fmt(item.weaponSpeed) end
    if stats.armor and stats.armor~=0 then parts[#parts+1]=fmt(stats.armor).." Armor" end
    for _,s in ipairs(statOrder) do
        local amount=stats[s[1]]
        if amount and amount~=0 then parts[#parts+1]=(amount>0 and "+" or "")..fmt(amount)..(s[3] and "% " or " ")..s[2] end
    end
    local keys={};for key in pairs(item.otherStats or {}) do keys[#keys+1]=key end;table.sort(keys)
    for _,key in ipairs(keys) do
        local amount=item.otherStats[key]
        parts[#parts+1]=(amount>0 and "+" or "")..fmt(amount).." "..(text(_G[key]) or key)
    end
    for _,line in ipairs(item.effectLines or {}) do parts[#parts+1]=line end
    if item.effects and #(item.effectLines or {})==0 then parts[#parts+1]="Additional effects — hover for details" end
    if #parts==0 then
        parts[1]=item.classID==12 and "Quest item" or item.classID==9 and "Recipe" or "No numeric bonuses"
    end
    if not item.live and item.effects then parts[#parts+1]="Live tooltip loading" end
    return table.concat(parts," · ")
end

