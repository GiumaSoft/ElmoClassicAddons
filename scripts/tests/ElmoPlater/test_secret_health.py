"""Protected health remains drawable after the priority engine is removed."""
from fixture import create_vm

vm, ns = create_vm()
vm.execute('''
function GetBuildInfo() return '1.60.1', '70790', '', 16001 end
MOCK.start()
local mob, plate = MOCK.mob('nameplate1', 'Creature-secret-health', 'Young Wolf')
local record = A.units.nameplate1
local publicHealth, publicMax = UnitHealth, UnitHealthMax
local hp, maximum, percent = {}, {}, {}
function issecretvalue(v)
    return rawequal(v, hp) or rawequal(v, maximum) or rawequal(v, percent)
end
function UnitHealth(unit)
    if unit == 'nameplate1' then return hp end
    return publicHealth(unit)
end
function UnitHealthMax(unit)
    if unit == 'nameplate1' then return maximum end
    return publicMax(unit)
end
CurveConstants = {ScaleTo100 = {}}
function UnitHealthPercent(unit, predicted, curve)
    assert(unit == 'nameplate1' and predicted == true and curve == CurveConstants.ScaleTo100)
    return percent
end
local methods = getmetatable(record.frame.percent).__index
function methods:SetFormattedText(format, value)
    assert(format == '%.0f%%' and rawequal(value, percent))
    self.formattedValue = value
end
A.Update(false)
assert(record.frame:IsShown() and plate.UnitFrame.alpha == 0,
    'Protected health must not disable the custom nameplate')
assert(rawequal(record.frame.bar.value, hp) and rawequal(record.frame.bar.maximum, maximum))
assert(rawequal(record.frame.percent.formattedValue, percent))
assert(A.Rules == nil and A.priorityTarget == nil)
-- Missing percent support still leaves the health bar visible.
UnitHealthPercent = nil
A.Update(false)
assert(record.frame:IsShown() and record.frame.percent:GetText() == '')
-- Return to ordinary numeric health without leaving the bar on the old range.
UnitHealth, UnitHealthMax = publicHealth, publicMax
mob.health = 15
A.Update(false)
assert(record.frame.bar.maximum == 1 and record.frame.bar.value == .15)
assert(record.frame.percent:GetText() == '15%' and A.priorityTarget == nil)
-- Missing health is different from a protected value: restore Blizzard's artwork.
UnitHealth = function() return nil end
A.Update(false)
assert(not record.frame:IsShown() and plate.UnitFrame.alpha == 1)
MOCK.event('PLAYER_LOGOUT')
''')
print('Secret-health checks passed: opaque values forwarded only to display APIs, percentage formatting, numeric recovery without priority machinery. Simulated APIs only.')
