-- Explicit Era API/frame fixture. Missing widget methods raise errors.
MOCK={time=100,spells={},messages={},requests={},frames={},shift=false}
local methods={}
local function noop() end
for _,name in ipairs({'SetBackdrop','SetBackdropColor','SetBackdropBorderColor','SetFrameStrata',
    'SetClampedToScreen','SetMovable','EnableMouse','RegisterForClicks','RegisterForDrag','SetTexCoord',
    'SetShadowColor','SetShadowOffset','SetTextInsets','SetAutoFocus','SetNumeric','SetMaxLetters'}) do methods[name]=noop end
function methods:SetSize(w,h) self.width,self.height=w,h end
function methods:SetWidth(v) self.width=v end
function methods:GetWidth() return self.width or 0 end
function methods:GetHeight() return self.height or 0 end
function methods:SetPoint(...) self.point={...} end
function methods:ClearAllPoints() self.point=nil end
function methods:GetLeft()
    if self==UIParent then return 0 end
    if self.mockLeft then return self.mockLeft end
    local p=self.point or {'TOPLEFT',self.parent,'TOPLEFT',0,0}
    local relative=type(p[2])=='table' and p[2] or self.parent
    local relativePoint=type(p[3])=='string' and p[3] or p[1]
    local x=type(p[2])=='number' and p[2] or p[4] or 0
    local offset=relativePoint=='CENTER' and relative:GetWidth()/2 or 0
    return relative:GetLeft()+offset+x
end
function methods:GetTop()
    if self==UIParent then return 900 end
    if self.mockTop then return self.mockTop end
    local p=self.point or {'TOPLEFT',self.parent,'TOPLEFT',0,0}
    local relative=type(p[2])=='table' and p[2] or self.parent
    local relativePoint=type(p[3])=='string' and p[3] or p[1]
    local y=type(p[2])=='number' and p[3] or p[5] or 0
    return relative:GetTop()-(relativePoint=='CENTER' and relative:GetHeight()/2 or 0)+y
end
function methods:SetAllPoints(target) self.allPoints=target or self.parent end
function methods:SetScript(event,fn) self.scripts[event]=fn end
function methods:GetScript(event) return self.scripts[event] end
function methods:RegisterEvent(event) self.events[event]=true end
function methods:RegisterUnitEvent(event,unit) self.events[event]=unit end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:SetShown(value) self.shown=value end
function methods:IsShown() return self.shown end
function methods:SetText(value) self.text=tostring(value) end
function methods:GetText() return self.text or '' end
function methods:SetTextColor(...) self.color={...} end
function methods:SetFont(path,size,flags) self.font,self.fontSize,self.flags=path,size,flags end
function methods:SetJustifyH(value) self.justifyH=value end
function methods:SetJustifyV(value) self.justifyV=value end
function methods:SetColorTexture(...) self.color={...} end
function methods:SetTexture(value) self.texture=value end
function methods:SetVertexColor(...) self.vertex={...} end
function methods:SetDesaturated(value) self.desaturated=value end
function methods:StartMoving() self.moving=true end
function methods:StopMovingOrSizing() self.moving=false end
function methods:HasFocus() return self.focus==true end
function methods:ClearFocus() self.focus=false end
function methods:SetOwner(owner,anchor) self.owner,self.anchor=owner,anchor end
function methods:ClearLines() self.lines={} end
function methods:NumLines() return #(self.lines or {}) end
function methods:AddLine(text) self.lines=self.lines or {};self.lines[#self.lines+1]=text end
function methods:SetSpellByID(id) self.spellID=id;self.lines={MOCK.spells[id].name} end
function methods:CreateTexture() return CreateFrame('Texture',nil,self) end
function methods:CreateFontString() return CreateFrame('FontString',nil,self) end
function CreateFrame(kind,name,parent,template)
    local f=setmetatable({kind=kind,name=name,parent=parent,template=template,shown=true,scripts={},events={}}, {__index=methods})
    MOCK.frames[#MOCK.frames+1]=f
    if name then _G[name]=f end
    return f
end
UIParent=CreateFrame('Frame');UIParent:SetSize(1440,900)
GameTooltip=CreateFrame('GameTooltip');GameTooltip:ClearLines()
BackdropTemplateMixin={};UISpecialFrames={};SlashCmdList={}
DEFAULT_CHAT_FRAME={AddMessage=function(_,message) MOCK.messages[#MOCK.messages+1]=message end}
function GetTime() return MOCK.time end
function IsShiftKeyDown() return MOCK.shift end
C_Spell={};C_SpellBook={}
function MOCK.spell(id,name,base)
    MOCK.spells[id]={name=name or ('Ability '..id),icon=id+10000,base=base or 6000,known=true}
    return MOCK.spells[id]
end
function MOCK.cooldown(id,duration)
    local s=assert(MOCK.spells[id]);s.start,s.duration=MOCK.time,duration;s.gcdOnly=false
end
function MOCK.globalCooldown(id,duration)
    MOCK.gcd={start=MOCK.time,duration=duration or 1.5}
    local s=assert(MOCK.spells[id]);s.start,s.duration=MOCK.gcd.start,MOCK.gcd.duration;s.gcdOnly=true
end
function C_Spell.GetSpellInfo(id)
    local s=MOCK.spells[id]
    if not s or s.cold then return nil end
    return {name=s.name,iconID=s.icon,spellID=id}
end
function C_Spell.RequestLoadSpellData(id) MOCK.requests[id]=(MOCK.requests[id] or 0)+1 end
function C_SpellBook.IsSpellKnown(id) return MOCK.spells[id] and MOCK.spells[id].known or false end
function C_SpellBook.IsSpellInSpellBook(id) return MOCK.spells[id] and MOCK.spells[id].inBook==true or false end
function C_Spell.IsAutoAttackSpell(id) return MOCK.spells[id] and MOCK.spells[id].autoAttack or false end
function C_Spell.IsAutoRepeatSpell(id) return MOCK.spells[id] and MOCK.spells[id].autoRepeat or false end
function C_Spell.IsSpellPassive(id) return MOCK.spells[id] and MOCK.spells[id].passive or false end
function GetSpellBaseCooldown(id) return MOCK.spells[id] and MOCK.spells[id].base end
function C_Spell.GetSpellCooldown(id)
    local s=id==61304 and MOCK.gcd or MOCK.spells[id]
    if not s or s.noCooldownInfo then return nil end
    return {startTime=s.start or 0,duration=s.duration or 0,isEnabled=not s.paused,
        isActive=not s.paused and (s.duration or 0)>0,modRate=s.modRate or 1,
        isOnGCD=s.unreliableGCDFlag or s.gcdOnly or false}
end
local function durationObject(untilTime)
    return {GetRemainingDuration=function() return math.max(0,untilTime-MOCK.time) end}
end
function C_Spell.GetSpellCooldownDuration(id,ignoreGCD)
    assert(ignoreGCD==true,'Cooldown reads must explicitly exclude the GCD')
    local s=MOCK.spells[id]
    if not s or s.noDuration then return nil end
    if s.paused or s.gcdOnly then return durationObject(MOCK.time) end
    return durationObject(s.nativeEnd or ((s.start or 0)+(s.duration or 0)))
end
function C_Spell.GetSpellCharges(id)
    local s=MOCK.spells[id];return s and s.charges
end
function C_Spell.IsSpellUsable(id)
    local s=MOCK.spells[id]
    if not s then return false,false end
    return s.usable~=false and not s.insufficientPower,s.insufficientPower==true
end
function C_Spell.GetSpellChargeDuration(id)
    local s=MOCK.spells[id];local c=s and s.charges
    if c then return durationObject(s.chargeNativeEnd or (c.cooldownStartTime+c.cooldownDuration)) end
end
function MOCK.event(event,...)
    ElmoSpellTracker.frame:GetScript('OnEvent')(ElmoSpellTracker.frame,event,...)
end
function MOCK.cast(id,unit) MOCK.event('UNIT_SPELLCAST_SUCCEEDED',unit or 'player','Cast-1',id) end
function MOCK.advance(seconds)
    for _=1,math.ceil(seconds/.05) do
        MOCK.time=MOCK.time+.05
        local fn=ElmoSpellTracker.frame:GetScript('OnUpdate')
        if fn then fn(ElmoSpellTracker.frame,.05) end
    end
end
function MOCK.start() MOCK.event('ADDON_LOADED','ElmoSpellTracker') end
