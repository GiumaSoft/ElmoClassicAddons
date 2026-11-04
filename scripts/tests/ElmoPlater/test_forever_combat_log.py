"""Forever must never touch the Blizzard-only combat-log event, even in pcall."""
from fixture import create_vm


def forever_vm(reader=True):
    vm, ns = create_vm()
    vm.execute('''
    function GetBuildInfo() return '1.60.1', '70790', '', 16001 end
    C_CombatLog = {IsCombatLogRestricted = function() return MOCK.combat end}
    C_EventUtils = {IsEventValid = function() return true end}
    local methods = getmetatable(A.frame).__index
    local register, unregister = methods.RegisterEvent, methods.UnregisterEvent
    MOCK.forbiddenCombatLogCalls = 0
    local function forbidden(event)
        if event ~= 'COMBAT_LOG_EVENT_UNFILTERED' then return false end
        MOCK.forbiddenCombatLogCalls = MOCK.forbiddenCombatLogCalls + 1
        -- The engine emits ADDON_ACTION_FORBIDDEN; pcall need not throw.
        return true
    end
    function methods:RegisterEvent(event)
        if not forbidden(event) then return register(self, event) end
    end
    function methods:UnregisterEvent(event)
        if not forbidden(event) then return unregister(self, event) end
    end
    function UnitAffectingCombat() return MOCK.combat end
    function UnitThreatSituation(player, unit)
        assert(player == 'player')
        return MOCK.units[unit] and MOCK.units[unit].threat
    end
    ''')
    if not reader:
        vm.execute('CombatLogGetCurrentEventInfo = nil')
    return vm, ns


# Classic Era keeps its combat-log lifecycle, including later restriction changes.
vm, ns = create_vm()
vm.execute('''
function GetBuildInfo() return '1.15.9', '70576', '', 11509 end
C_CombatLog = C_CombatLog or {}
C_CombatLog.IsCombatLogRestricted = function() return MOCK.logRestricted == true end
MOCK.start()
assert(A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
MOCK.logRestricted = true; A.RegisterCombatLog()
assert(not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
MOCK.logRestricted = false; A.RegisterCombatLog()
assert(A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
''')


for reader in (True, False):
    vm, ns = forever_vm(reader)
    vm.execute('''
    MOCK.start()
    MOCK.event('PLAYER_ENTERING_WORLD')
    MOCK.combat = true
    A.RegisterCombatLog()
    MOCK.combat = false
    MOCK.event('PLAYER_REGEN_ENABLED')
    MOCK.event('PLAYER_ENTERING_WORLD')
    assert(A.ready)
    assert(MOCK.forbiddenCombatLogCalls == 0,
        'Forever attempted a forbidden combat-log registration or removal')
    assert(not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
    ''')

vm, ns = forever_vm()
vm.execute('''
MOCK.start()
local mob, plate = MOCK.mob('nameplate1', 'Creature-threat', 'Engaged enemy')
local other = MOCK.mob('nameplate2', 'Creature-other', 'Untouched enemy')
local record = A.units.nameplate1
mob.health = 15; other.health = 1
mob.threat = 0 -- On our threat list even when another player is tanking.
MOCK.advance(.2)
assert(not A.attacked[mob.guid] and not A.priorityTarget)
MOCK.combat = true
MOCK.advance(.2)
assert(A.attacked[mob.guid] and not A.attacked[other.guid])
assert(A.priorityTarget == record and record.frame:IsShown())
assert(record.frame.percent:GetText() == '15%')
-- Restricted threat must not be compared or used as evidence of engagement.
local secret = {}
function issecretvalue(v) return rawequal(v, secret) end
other.threat = secret
MOCK.advance(.2)
assert(not A.attacked[other.guid] and A.priorityTarget == record)
-- A personal harmful aura remains an allowed fallback if threat is unavailable.
UnitThreatSituation = nil
MOCK.aura('nameplate2', 589, 10)
MOCK.event('UNIT_AURA', 'nameplate2')
assert(A.attacked[other.guid] and #A.units.nameplate2.auras == 1)
MOCK.combat = false; MOCK.event('PLAYER_REGEN_ENABLED')
assert(next(A.attacked) == nil and not A.priorityTarget)
MOCK.event('PLAYER_LOGOUT')
assert(plate.UnitFrame.alpha == 1 and MOCK.forbiddenCombatLogCalls == 0)
''')
print('Forever combat-log checks passed: zero forbidden registrations/removals, public threat and personal-aura fallback, secret values and combat cleanup. Simulated APIs only.')
