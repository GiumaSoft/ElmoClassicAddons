"""Reproduce Forever's denial of raw aura access and verify display delegation."""
from fixture import create_vm

vm, ns = create_vm()
vm.execute('''
function GetBuildInfo() return '1.60.1', '70790', '', 16001 end
C_XMLUtil = {GetTemplateInfo=function(name)
    assert(name == 'CustomAuraContainerTemplate'); return {}
end}
C_Secrets = {ShouldAurasBeSecret=function() return MOCK.secretAuras == true end}
C_StringUtil = {CreateNumericRuleFormatter=function()
    return {AddBreakpoint=function() end}
end}
AnchorUtil = {FlowDirection={Right=1, Up=2}}
AuraContainerSortMethod = {Default=0}
AuraContainerSortDirection = {Normal=0}
MOCK.containers, MOCK.blockedQueries = {}, 0
local create = CreateFrame
local methods = getmetatable(UIParent).__index
local containerMethods = {}
function containerMethods:SetEnabled(enabled) self.enabled = enabled end
function containerMethods:SetUnit(unit) assert(type(unit)=='string'); self.unit = unit end
function containerMethods:SetFlowLayoutAnchorPoint(point) assert(point=='BOTTOMLEFT') end
function containerMethods:SetFlowLayoutGrowthDirection(x,y) assert(x==1 and y==2) end
function containerMethods:SetFlowLayoutMaximumLineSize(width) assert(width==142) end
function containerMethods:AddAuraGroup(key, filter, options)
    assert(key=='personal' and filter=='HARMFUL|PLAYER')
    assert(options.sortMethod==0 and options.sortDirection==0 and options.maxFrameCount==math.huge)
    assert(options.layout.elementWidth==22 and options.layout.elementHeight==22)
    self.filter = filter
    local button = create('AuraButton',nil,self)
    setmetatable(button,{__index=function(frame,key)
        assert(not rawget(frame,'adopted') or not MOCK.secretAuras,
            'Addon accessed an adopted aura button during restricted combat')
        if key=='SetIcon' then return function(_,texture) assert(texture.kind=='Texture'); MOCK.iconBound=true end end
        if key=='SetDurationText' or key=='SetApplicationCount' then
            return function(_,label) assert(label.kind=='FontString') end
        end
        return methods[key]
    end})
    options.initializeFrame(button)
    button.adopted = true
end
function CreateFrame(kind,name,parent,template)
    if kind~='AuraContainer' then return create(kind,name,parent,template) end
    assert(template=='CustomAuraContainerTemplate')
    local frame = create(kind,name,parent,template)
    setmetatable(frame,{__index=function(_,key) return containerMethods[key] or methods[key] end})
    MOCK.containers[#MOCK.containers+1] = frame
    return frame
end
local indexed = C_UnitAuras.GetAuraDataByIndex
local function denyWhenRestricted()
    if MOCK.secretAuras then
        MOCK.blockedQueries = MOCK.blockedQueries + 1
        error("Auras cannot be accessed when secret while tainted by 'ElmoPlater'")
    end
end
function C_UnitAuras.GetAuraDataByIndex(...)
    denyWhenRestricted(); return indexed(...)
end
function C_UnitAuras.GetUnitAuras(unit, filter)
    denyWhenRestricted(); assert(filter=='HARMFUL|PLAYER'); return MOCK.units[unit].auras
end

MOCK.start()
assert(A.Auras.available)
local mob, plate = MOCK.mob('nameplate2', 'Creature-restricted-aura', 'Enemy')
local record = A.units.nameplate2
local container = record.auraContainer
assert(container and container.enabled and container.unit=='nameplate2' and container:IsShown())
assert(container.parent==record.frame and MOCK.iconBound)
assert(container.points[1][1]=='BOTTOM' and container.points[1][3]=='TOP')
MOCK.units.target = mob
MOCK.aura('nameplate2',589,10)
MOCK.event('UNIT_AURA','target')
assert(#record.auras==1 and A.db.learnedDebuffs[589])
assert(#record.frame.icons==0, 'The legacy display must not duplicate the native container')

MOCK.secretAuras, MOCK.combat = true, true
MOCK.event('PLAYER_REGEN_DISABLED')
assert(not record.aurasKnown and #record.auras==0)
MOCK.event('UNIT_AURA','nameplate2'); MOCK.event('UNIT_AURA','target')
MOCK.event('PLAYER_TARGET_CHANGED'); MOCK.advance(.3)
assert(record.frame:IsShown() and container.enabled and container.unit=='nameplate2')
assert(MOCK.blockedQueries==0, 'No forbidden raw aura query may be attempted')
-- Size/layer changes must affect only the public container, never its adopted buttons.
A.db.plateAuraSize=36; A.Update(false)
assert(container.scale==36/22 and container.frameLevel==record.frame.frameLevel+2)
A.Command('auras')
assert(MOCK.blockedQueries==0)
assert(A.db.auraDiagnostic[2]=='Aura display: Blizzard container')
assert(A.db.auraDiagnostic[#A.db.auraDiagnostic]:find('direct queries skipped',1,true))
-- Pooling disables the former unit and rebinds the same container to the new token.
MOCK.remove('nameplate2'); assert(not container.enabled and not container:IsShown() and not record.frame:IsShown())
local other = MOCK.mob('nameplate3','Creature-new-aura','Other',plate)
assert(A.units.nameplate3.auraContainer==container and container.unit=='nameplate3' and container.enabled)
assert(container:IsShown())
assert(#MOCK.containers==1 and MOCK.blockedQueries==0)
MOCK.secretAuras, MOCK.combat = false, false
MOCK.aura('nameplate3',772,5)
MOCK.event('PLAYER_REGEN_ENABLED')
assert(A.units.nameplate3.aurasKnown and #A.units.nameplate3.auras==1)
MOCK.event('PLAYER_LOGOUT'); assert(not container.enabled and plate.UnitFrame.alpha==1)
''')
print('Aura-container checks passed: no forbidden raw queries, native personal-filter/icon/timer bindings, no duplicate icons, public-only scaling/layering, pooling and recovery. Simulated APIs only.')
