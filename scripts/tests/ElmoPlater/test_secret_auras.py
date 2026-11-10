"""Filtered personal auras must remain drawable when their display fields are protected."""
from fixture import create_vm

vm, ns = create_vm()
vm.execute('''
function GetBuildInfo() return '1.60.1', '70790', '', 16001 end
MOCK.start()
local mob, plate = MOCK.mob('nameplate1', 'Creature-aura', 'Enemy')
local record = A.units.nameplate1
local secretSource, secretIcon, secretSpell, secretExpiry, secretCount = {}, {}, {}, {}, {}
function issecretvalue(v)
    return rawequal(v, secretSource) or rawequal(v, secretIcon) or rawequal(v, secretSpell)
        or rawequal(v, secretExpiry) or rawequal(v, secretCount)
end
-- The API has already applied HARMFUL|PLAYER; sourceUnit is optional/private.
local personal = MOCK.aura('nameplate1', 589, 10)
personal.sourceUnit = secretSource
MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 1 and record.frame.icons[1]:IsShown(),
    'A protected caster must not discard an aura returned by the personal filter')
personal.sourceUnit = nil
MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 1 and record.frame.icons[1].texture.texture == 589)
-- Texture APIs may receive the protected icon directly.
personal.sourceUnit = secretSource; personal.icon = secretIcon
personal.spellId = secretSpell; personal.expirationTime = secretExpiry; personal.applications = secretCount
MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 1 and record.frame.icons[1]:IsShown())
assert(rawequal(record.frame.icons[1].texture.texture, secretIcon),
    'Protected icons must reach SetTexture without numeric coercion or boolean tests')
assert(not record.aurasKnown)
assert(A.db.learnedDebuffs==nil)
-- Readable non-player casters are still rejected, including pets.
personal.sourceUnit = 'party1'; MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 0 and not record.frame.icons[1]:IsShown())
personal.sourceUnit = 'pet'; MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 0)
-- Ordinary personal debuffs retain readable countdowns and stacks.
personal.sourceUnit = 'player'; personal.icon = 'Interface\\\\Icons\\\\Spell_Shadow_ShadowWordPain'
personal.spellId = 589; personal.expirationTime = MOCK.time + 5; personal.applications = 3
MOCK.event('UNIT_AURA', 'nameplate1')
assert(record.frame.icons[1].texture.texture == personal.icon)
assert(record.frame.icons[1].timer:GetText() == '5' and record.frame.icons[1].count:GetText() == '3')
assert(record.aurasKnown and A.db.learnedDebuffs==nil)
-- The removal event hides a protected aura without comparing its expiration time.
personal.expirationTime = secretExpiry
MOCK.event('UNIT_AURA', 'nameplate1')
mob.auras = {}; MOCK.event('UNIT_AURA', 'nameplate1')
assert(#record.auras == 0 and not record.frame.icons[1]:IsShown())
MOCK.event('PLAYER_LOGOUT'); assert(plate.UnitFrame.alpha == 1)
''')
vm.execute('''
local mob = MOCK.mob('nameplate2', 'Creature-batch-aura', 'Enemy')
local record = A.units.nameplate2
MOCK.units.target = mob
local personal = MOCK.aura('nameplate2', 589, 10)
-- This build uses the batch API for nameplates; the old indexed API may fail.
local indexedCalls = 0
function C_UnitAuras.GetAuraDataByIndex()
    indexedCalls = indexedCalls + 1; error('Indexed aura access unavailable')
end
function C_UnitAuras.GetUnitAuras(unit, filter)
    assert(filter == 'HARMFUL|PLAYER')
    return MOCK.units[unit].auras
end
MOCK.event('UNIT_AURA', 'target')
assert(#record.auras == 1 and record.frame.icons[1]:IsShown(),
    'A target aura event must update its nameplate through the batch API')
assert(indexedCalls == 0)
mob.auras = {}; MOCK.event('UNIT_AURA', 'target')
assert(record.aurasKnown and #record.auras == 0 and not record.frame.icons[1]:IsShown())
assert(indexedCalls == 0, 'An empty batch is authoritative, not an API failure')
MOCK.aura('nameplate2', 589, 10)
MOCK.event('PLAYER_TARGET_CHANGED')
assert(#record.auras == 1, 'Target changes must refresh an existing aura')
function C_UnitAuras.GetUnitAuras() error('Aura access unavailable') end
MOCK.event('UNIT_AURA', 'target')
assert(not record.aurasKnown and #record.auras == 0)
assert(not record.frame.icons[1]:IsShown() and indexedCalls == 0)
''')
print('Protected-aura checks passed: filtered private/missing caster, opaque/string icon display, no aura learning, caster exclusions, countdown/stacks and removal. Simulated APIs only.')
