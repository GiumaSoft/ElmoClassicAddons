local _, A = ...
local S = {}
A.Spells = S
-- Training levels are a fallback for clients without GetSpellLevelLearned.
-- A beneficial buff rank may be received ten levels before its training level.
S.catalog = {
    PRIEST = {
        {key="fortitude",id=1243,group=21562,label="Fortitude",levels={1,12,24,36,48,60}},
        {key="spirit",id=14752,group=27681,label="Divine Spirit",levels={30,40,50,60},mana=true},
        {key="shadow",id=976,group=27683,label="Shadow Protection",levels={30,42,56},default=false},
    },
    MAGE = {{key="intellect",id=1459,group=23028,label="Arcane Intellect",levels={1,14,28,42,56},mana=true}},
    DRUID = {
        {key="mark",id=1126,group=21849,label="Mark of the Wild",levels={1,10,20,30,40,50,60}},
        {key="thorns",id=467,label="Thorns",levels={6,14,24,34,44,54},default=false},
    },
    PALADIN = {
        {key="might",id=19740,group=25782,label="Blessing of Might",levels={4,12,22,32,42,52,60}},
        {key="wisdom",id=19742,group=25894,label="Blessing of Wisdom",levels={14,24,34,44,54,60}},
        {key="kings",id=20217,group=25898,label="Blessing of Kings",levels={20}},
    },
}

function S.Info(id)
    local raw = A.Call(C_Spell and C_Spell.GetSpellInfo, id)
    if A.Table(raw) and A.Text(raw.name) then
        return {id=id,name=raw.name,icon=A.Number(raw.iconID)}
    end
    local name, _, icon = A.Call(GetSpellInfo, id)
    if A.Text(name) then return {id=id,name=name,icon=A.Number(icon)} end
end

function S.Refresh()
    if InCombatLockdown() then return end
    local _, class = A.Call(UnitClass, "player")
    A.class = A.Text(class)
    S.families = S.catalog[A.class] or {}
    local byName = {}
    for _, f in ipairs(S.families) do
        f.ranks, f.names = {}, {}
        local info, group = S.Info(f.id), f.group and S.Info(f.group)
        f.name, f.icon = info and info.name or f.label, info and info.icon or "Interface\\Icons\\INV_Misc_QuestionMark"
        f.names[f.name] = true
        if group then f.names[group.name] = true end
        byName[f.name] = f
        if type(A.db.buffs[f.key]) ~= "boolean" then A.db.buffs[f.key] = f.default ~= false end
    end
    local seen = {}
    local function add(id, subtext, level, order)
        id = A.Number(id)
        if not id or seen[id] then return end
        local known = C_SpellBook and C_SpellBook.IsSpellKnown or IsSpellKnown
        if type(known)=="function" and A.Bool(A.Call(known,id))~=true then return end
        local info = S.Info(id)
        local f = info and byName[info.name]
        if not f then return end
        seen[id] = true
        local rank = tonumber((A.Text(subtext) or ""):match("%d+")) or #f.ranks + 1
        level = A.Number(level) or A.Number(A.Call(C_Spell and C_Spell.GetSpellLevelLearned or GetSpellLevelLearned, id))
        if not level or level <= 0 then level = f.levels[rank] end
        f.ranks[#f.ranks+1] = {id=id,name=info.name,icon=info.icon,rank=rank,level=level,order=order}
    end
    local modern = C_SpellBook and C_SpellBook.GetNumSpellBookSkillLines
    local tabs = A.Number(A.Call(modern or GetNumSpellTabs)) or 0
    for tab = 1, math.min(tabs, 30) do
        local offset, count
        if modern then
            local line = A.Table(A.Call(C_SpellBook.GetSpellBookSkillLineInfo, tab))
            if line then offset,count=A.Number(line.itemIndexOffset),A.Number(line.numSpellBookItems) end
        else
            local _, _, o, n = A.Call(GetSpellTabInfo, tab); offset,count=A.Number(o),A.Number(n)
        end
        if offset and count then
            for slot = offset+1, offset+math.min(count, 500) do
                if modern then
                    local bank = Enum and Enum.SpellBookSpellBank and Enum.SpellBookSpellBank.Player or 0
                    local info = A.Table(A.Call(C_SpellBook.GetSpellBookItemInfo, slot, bank))
                    if info and A.Bool(info.isPassive) == false then
                        local _, subtext = A.Call(C_SpellBook.GetSpellBookItemName, slot, bank)
                        add(info.spellID,subtext,A.Call(C_SpellBook.GetSpellBookItemLevelLearned,slot,bank),slot)
                    end
                else
                    local kind, id = A.Call(GetSpellBookItemInfo, slot, BOOKTYPE_SPELL or "spell")
                    if A.Text(kind) == "SPELL" then
                        local _, subtext = A.Call(GetSpellBookItemName, slot, BOOKTYPE_SPELL or "spell")
                        add(id,subtext,nil,slot)
                    end
                end
            end
        end
    end
    for _, f in ipairs(S.families) do
        table.sort(f.ranks,function(a,b) return a.rank<b.rank or a.rank==b.rank and a.order<b.order end)
    end
    if A.class == "PALADIN" then
        local selected
        for _, f in ipairs(S.families) do
            if f.key == A.db.blessing and #f.ranks>0 then selected=f end
        end
        if not selected then
            for _, f in ipairs(S.families) do if #f.ranks>0 then selected=f;break end end
        end
        S.active = selected and {selected} or {}
        if selected then A.db.blessing=selected.key end
    else S.active = S.families end
end

function S.ForUnit(f, unit)
    if #f.ranks == 0 then return end
    local level = A.Number(A.Call(UnitLevel, unit))
    if not level or level < 1 then return f.ranks[1] end
    local chosen
    for _, rank in ipairs(f.ranks) do
        if rank.level and level+10 >= rank.level then chosen=rank end
    end
    return chosen or f.ranks[1]
end

function S.Range(spell, unit)
    if unit == "player" then return true end
    local value = A.Call(C_Spell and C_Spell.IsSpellInRange, spell.id, unit)
    if A.Bool(value) ~= nil then return value end
    value = A.Call(IsSpellInRange, spell.name, unit)
    if A.Private(value) then return end
    if value == 1 or value == true then return true end
    if value == 0 or value == false then return false end
end
