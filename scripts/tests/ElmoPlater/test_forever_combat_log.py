"""Neither client needs combat logs, threat, spell readiness or depth management."""
from fixture import create_vm

for interface in (11509, 16001):
    vm, ns = create_vm()
    vm.execute(f"function GetBuildInfo()return 'test','1','',{interface} end")
    vm.execute('''
    local methods=getmetatable(A.frame).__index
    local register,unregister=methods.RegisterEvent,methods.UnregisterEvent
    function methods:RegisterEvent(event)
        assert(event~='COMBAT_LOG_EVENT_UNFILTERED','Unnecessary combat-log registration')
        return register(self,event)
    end
    function methods:UnregisterEvent(event)
        assert(event~='COMBAT_LOG_EVENT_UNFILTERED','Unnecessary combat-log removal')
        return unregister(self,event)
    end
    function methods:SetFrameLevel()error('No explicit depth management is needed')end
    for _,name in ipairs({'UnitThreatSituation','IsPlayerSpell','IsSpellKnown','IsUsableSpell',
        'GetSpellCooldown','CombatLogGetCurrentEventInfo'})do
        _G[name]=function()error('Retired priority dependency '..name)end
    end
    C_CombatLog=setmetatable({},{__index=function()error('Combat-log API accessed')end})
    C_SpellBook=setmetatable({},{__index=function()error('Spellbook API accessed')end})
    MOCK.start()
    local mob,plate=MOCK.mob('nameplate1','Creature-cleanup','Enemy')
    local record=A.units.nameplate1
    for _,event in ipairs({'PLAYER_ENTERING_WORLD','PLAYER_REGEN_DISABLED','UNIT_HEALTH',
        'PLAYER_TARGET_CHANGED','UNIT_AURA','PLAYER_REGEN_ENABLED'})do
        MOCK.combat=event=='PLAYER_REGEN_DISABLED'
        mob.health=15;MOCK.event(event,'nameplate1');MOCK.advance(.3)
        assert(record.frame:IsShown()and record.frame.percent:GetText()=='15%')
    end
    assert(A.Rules==nil and A.Conditions==nil and A.Spells==nil and A.attacked==nil)
    assert(A.priorityTarget==nil and A.SetHealthTest==nil and record.healthLayer==nil)
    assert(A.RegisterCombatLog==nil and A.CombatLog==nil)
    assert(not A.frame.events.COMBAT_LOG_EVENT_UNFILTERED)
    MOCK.event('PLAYER_LOGOUT');assert(plate.UnitFrame.alpha==1)
    ''')
print('Reduced-runtime checks passed on both clients: zero combat-log, spellbook, threat or explicit frame-depth operations. Simulated APIs only.')
