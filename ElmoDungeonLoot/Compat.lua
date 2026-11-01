local _, CD = ...
local C = {}
CD.Compat = C

-- Era has no C_TooltipInfo readers. Scan the actual inventory/bag slot so an
-- owned random suffix, enchant or charge is never replaced with a generic link.
function C.ReadTooltip(link, location)
    if not C.tooltip then
        C.tooltip = CreateFrame("GameTooltip", "ElmoDungeonLootScanTooltip", UIParent, "GameTooltipTemplate")
    end
    local tip = C.tooltip
    tip:SetOwner(UIParent, "ANCHOR_NONE")
    tip:ClearLines()
    local ok
    if location and location.equipmentSlot then
        ok = pcall(tip.SetInventoryItem, tip, "player", location.equipmentSlot)
    elseif location and location.bag ~= nil then
        ok = pcall(tip.SetBagItem, tip, location.bag, location.slot)
    else
        ok = pcall(tip.SetHyperlink, tip, link)
    end
    local lines = {}
    if ok then
        for index = 1, math.min(tip:NumLines() or 0, 100) do
            local left = _G["ElmoDungeonLootScanTooltipTextLeft" .. index]
            local right = _G["ElmoDungeonLootScanTooltipTextRight" .. index]
            lines[#lines + 1] = {leftText=left and left:GetText(), rightText=right and right:GetText()}
        end
    end
    tip:Hide()
    if #lines > 0 then return {lines=lines} end
end

-- Classic bonuses are often Equip spells omitted by GetItemStats. Values are
-- percentages/skill points on Era, not the combat ratings of later expansions.
local bonuses = {
    {"ap", "^Equip: Increases attack power by (%d+)%.$"},
    {"rap", "^Equip: Increases ranged attack power by (%d+)%.$"},
    {"ap", "^Equip: %+(%d+) Attack Power%.$"},
    {"rap", "^Equip: %+(%d+) Ranged Attack Power%.$"},
    {"feralap", "^Equip: Increases attack power by (%d+) in Cat, Bear, and Dire Bear forms only%.$"},
    {"crit", "^Equip: Improves your chance to get a critical strike by ([%d%.]+)%%%.$"},
    {"spellcrit", "^Equip: Improves your chance to get a critical strike with spells by ([%d%.]+)%%%.$"},
    {"hit", "^Equip: Improves your chance to hit by ([%d%.]+)%%%.$"},
    {"spellhit", "^Equip: Improves your chance to hit with spells by ([%d%.]+)%%%.$"},
    {"sp", "^Equip: Increases damage and healing done by magical spells and effects by up to (%d+)%.$"},
    {"healing", "^Equip: Increases healing done by spells and effects by up to (%d+)%.$"},
    {"mp5", "^Equip: Restores (%d+) mana per 5 sec%.$"},
    {"hp5", "^Equip: Restores (%d+) health every 5 sec%.$"},
    {"defense", "^Equip: Increases defense by (%d+)%.$"},
    {"dodge", "^Equip: Increases your chance to dodge an attack by ([%d%.]+)%%%.$"},
    {"parry", "^Equip: Increases your chance to parry an attack by ([%d%.]+)%%%.$"},
    {"block", "^Equip: Increases your chance to block attacks with a shield by ([%d%.]+)%%%.$"},
    {"blockValue", "^Equip: Increases the block value of your shield by (%d+)%.$"},
}
for name, stat in pairs({Shadow="shadow",Fire="fire",Frost="frost",Nature="nature",Arcane="arcane",Holy="holy"}) do
    bonuses[#bonuses+1] = {stat, "^Equip: Increases damage done by " .. name .. " spells and effects by up to (%d+)%.$"}
end

function C.ReadBonus(value)
    for _, bonus in ipairs(bonuses) do
        local amount = value:match(bonus[2])
        if amount then return bonus[1], tonumber(amount) end
    end
end
