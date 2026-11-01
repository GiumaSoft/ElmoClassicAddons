-- Explicit Lua 5.1 fixture. Native targeting is modeled from physical rectangles,
-- not from ElmoPlater's GUID-to-icon records. This is not a live engine test.
MOCK = {time = 1000, frames = {}, units = {}, plates = {}, messages = {}, combat = false,
    restrictedReads = 0, foreignWrites = 0, hookAttempts = 0,
    nativeWidth = 132, nativeHeight = 32, writes = 0, insetWrites = 0,
    insets = {[0] = {1, 2, 3, 4}, [1] = {0, 0, 0, 0}},
    cvars = {nameplateShowEnemies = true, nameplateShowFriends = false, nameplateShowOffscreen = false}}
local methods = {}
local function foreign(frame)
    if not frame then return false end
    return frame.native or frame.isPlater or frame.nativeArtwork
end
local function measurement(frame)
    if foreign(frame) or (frame.parent and foreign(frame.parent)) then
        MOCK.restrictedReads = MOCK.restrictedReads + 1
        error("Action[FrameMeasurement] failed because[Can't measure restricted regions]")
    end
end
local function mutation(frame)
    if foreign(frame) and not MOCK.inFixture and not MOCK.barClickTest then
        MOCK.foreignWrites = MOCK.foreignWrites + 1
        error('ElmoPlater must not mutate native or Plater frames')
    end
end
local fractions = {TOPLEFT = {0,1}, TOP = {.5,1}, TOPRIGHT = {1,1}, LEFT = {0,.5},
    CENTER = {.5,.5}, RIGHT = {1,.5}, BOTTOMLEFT = {0,0}, BOTTOM = {.5,0}, BOTTOMRIGHT = {1,0}}
local function noop() end
for _, name in ipairs({'SetClampedToScreen', 'SetMovable', 'RegisterForClicks', 'RegisterForDrag',
    'SetAutoFocus', 'SetNumeric', 'SetMaxLetters', 'SetJustifyH', 'SetJustifyV', 'SetTextInsets', 'SetFont'}) do methods[name] = noop end
function methods:SetBackdrop(v) self.backdrop = v end
function methods:SetFont(path,size,flags) self.font,self.fontSize,self.fontFlags=path,size,flags end
function methods:SetAlpha(value) mutation(self); self.alpha=value end
function methods:GetEffectiveAlpha()
    return (self.alpha or 1)*(self.parent and self.parent:GetEffectiveAlpha() or 1)
end
function methods:SetBackdropColor(...) self.background = {...} end
function methods:SetBackdropBorderColor(...) self.border = {...} end
function methods:EnableMouse(v) mutation(self); self.mouse = v end
function methods:SetFrameStrata(v) self.strata = v end
function methods:SetFrameLevel(v) self.frameLevel = v end
function methods:GetFrameLevel() return self.frameLevel or 1 end
function methods:SetClipsChildren(v) self.clips = v end
function methods:SetSize(w,h) mutation(self); self.width,self.height = w,h end
function methods:SetWidth(v) self.width = v end
function methods:SetHeight(v) self.height = v end
function methods:GetParent() return self.parent end
function methods:SetParent(parent) mutation(self); self.parent = parent end
function methods:IsForbidden() return self.forbidden == true end
function methods:SetPoint(point, relative, relativePoint, x, y)
    mutation(self)
    if type(relative) == 'number' then x,y,relative,relativePoint = relative,relativePoint,self.parent,point
    elseif relative == nil then relative,relativePoint = self.parent,point
    elseif type(relativePoint) == 'number' then x,y,relativePoint = relativePoint,x,point end
    relativePoint = relativePoint or point
    local p = {point, relative, relativePoint, x or 0, y or 0}
    for i, existing in ipairs(self.points) do if existing[1] == point then self.points[i] = p; return end end
    self.points[#self.points + 1] = p
end
function methods:ClearAllPoints() mutation(self); self.points = {} end
function methods:GetNumPoints() measurement(self); return #self.points end
function methods:GetPoint(i) measurement(self); return unpack(self.points[i or 1] or {}) end
function methods:SetAllPoints(frame)
    self:ClearAllPoints(); frame = frame or self.parent
    self:SetPoint('TOPLEFT', frame, 'TOPLEFT', 0, 0)
    self:SetPoint('BOTTOMRIGHT', frame, 'BOTTOMRIGHT', 0, 0)
end
local function rect(frame, visiting)
    if frame == UIParent then return 0,0,1440,900 end
    if frame.native then return (frame.centerX or 600) - MOCK.nativeWidth/2, frame.bottom or 300, MOCK.nativeWidth, MOCK.nativeHeight end
    visiting = visiting or {}; assert(not visiting[frame], 'Cyclic frame anchors'); visiting[frame] = true
    local equations = {}
    for _, p in ipairs(frame.points) do
        local rx,ry,rw,rh = rect(p[2] or frame.parent, visiting)
        local own,rel = assert(fractions[p[1]]),assert(fractions[p[3]])
        equations[#equations+1] = {own[1],own[2],rx+rw*rel[1]+p[4],ry+rh*rel[2]+p[5]}
    end
    local x,y,w,h = 0,0,frame.width or 0,frame.height or 0
    if #equations > 0 then
        local a = equations[1]
        for i=2,#equations do
            local b=equations[i]
            if a[1] ~= b[1] then w=(a[3]-b[3])/(a[1]-b[1]) end
            if a[2] ~= b[2] then h=(a[4]-b[4])/(a[2]-b[2]) end
        end
        x,y=a[3]-a[1]*w,a[4]-a[2]*h
    end
    visiting[frame]=nil
    return x,y,w,h
end
function methods:GetRect() measurement(self); return rect(self) end
function MOCK.worldRect(frame) return rect(frame) end
function methods:SetStatusBarTexture(value) self.statusTexture=value end
function methods:SetStatusBarColor(...) self.statusColor={...} end
function methods:SetMinMaxValues(low,high) self.minimum,self.maximum=low,high end
function methods:SetValue(value) self.value=value end
function methods:GetLeft() local x=self:GetRect(); return x end
function methods:GetTop() local _,y,_,h=self:GetRect(); return y+h end
function methods:GetWidth() local _,_,w=self:GetRect(); return w end
function methods:GetHeight() local _,_,_,h=self:GetRect(); return h end
function methods:SetScript(event,fn) self.scripts[event]=fn end
function methods:GetScript(event) return self.scripts[event] end
function methods:RegisterEvent(event) self.events[event]=true end
function methods:UnregisterEvent(event) self.events[event]=nil end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:SetShown(v) self.shown=v end
function methods:IsShown() return self.shown end
function methods:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
function methods:SetText(v)
    self.text=tostring(v or '')
    if self.scripts.OnTextChanged then self.scripts.OnTextChanged(self,false) end
end
function methods:SetChecked(v) self.checked=v==true end
function methods:GetChecked() return self.checked==true end
function methods:GetText() return self.text or '' end
function methods:SetTextColor(...) self.color={...} end
function methods:SetColorTexture(...) self.color={...} end
function methods:SetTexture(v) self.texture=v end
function methods:SetTexCoord(...) self.texCoord={...} end
function methods:SetVertexColor(...) self.vertex={...} end
function methods:SetDesaturated(v) self.desaturated=v end
function methods:StartMoving() self.moving=true end
function methods:StopMovingOrSizing() self.moving=false end
function methods:ClearFocus() self.focus=false end
function methods:SetOwner(owner,anchor) self.owner,self.anchor=owner,anchor end
function methods:ClearLines() self.lines={} end
function methods:AddLine(line) self.lines=self.lines or {}; self.lines[#self.lines+1]=line end
function methods:CreateTexture() return CreateFrame('Texture',nil,self) end
function methods:CreateFontString() return CreateFrame('FontString',nil,self) end
function CreateFrame(kind,name,parent,template)
    local f=setmetatable({kind=kind,name=name,parent=parent,template=template,shown=true,
        scripts={},events={},points={},mouse=kind=='Button'}, {__index=methods})
    MOCK.frames[#MOCK.frames+1]=f; if name then _G[name]=f end; return f
end
UIParent=CreateFrame('Frame'); UIParent:SetSize(1440,900)
GameTooltip=CreateFrame('GameTooltip',nil,UIParent)
BackdropTemplateMixin={}; SlashCmdList={}; Enum={NamePlateType={Friendly=0,Enemy=1}}
DEFAULT_CHAT_FRAME={AddMessage=function(_,m) MOCK.messages[#MOCK.messages+1]=m end}
function GetTime() return MOCK.time end
function IsLoggedIn() return false end
function InCombatLockdown() return MOCK.combat end
local function data(unit) return MOCK.units[unit] end
function UnitGUID(unit) return data(unit) and data(unit).guid end
function UnitName(unit) return data(unit) and data(unit).name end
function UnitLevel(unit) return data(unit) and data(unit).level end
function UnitHealth(unit) return data(unit) and data(unit).health or 0 end
function UnitHealthMax(unit) return data(unit) and data(unit).maxHealth or 0 end
function UnitExists(unit) return data(unit) ~= nil end
function UnitIsDeadOrGhost(unit) return data(unit) and data(unit).dead == true end
function UnitCanAttack(_,unit) return data(unit) and not data(unit).friendly end
function UnitReaction(unit) return data(unit) and (data(unit).friendly and 5 or data(unit).neutral and 4 or 2) end
function UnitIsTapDenied(unit) return data(unit) and data(unit).tapDenied==true or false end
function UnitSelectionColor(unit)
    if data(unit) and data(unit).neutral then return 1,1,0 end
    return .8,.12,.12
end
function UnitIsUnit(a,b) return UnitGUID(a) ~= nil and UnitGUID(a)==UnitGUID(b) end
function GetRaidTargetIndex(unit) return data(unit) and data(unit).mark end
function SetPortraitTexture(texture,unit) texture:SetTexture('portrait:'..assert(UnitGUID(unit))) end
function issecretvalue() return false end
C_CVar={GetCVarBool=function(key) return MOCK.cvars[key] == true end}
MOCK.nativeDebuffs=true
function C_CVar.GetCVarBitfield(name,index)
    assert(name=='nameplateEnemyNpcAuraDisplay' and index==2);return MOCK.nativeDebuffs
end
function C_CVar.SetCVarBitfield(name,index,value)
    assert(name=='nameplateEnemyNpcAuraDisplay' and index==2 and type(value)=='boolean')
    MOCK.nativeDebuffs=value
end
C_AddOns={IsAddOnLoaded=function(name) return name=='Plater' and MOCK.platerLoaded==true end,
    DisableAddOn=function(name)
        assert(name=='Plater');MOCK.platerDisableRequests=(MOCK.platerDisableRequests or 0)+1
        MOCK.platerDisabled=true
    end}
C_UnitAuras={GetAuraDataByIndex=function(unit,index,filter)
    assert(filter=='HARMFUL|PLAYER'); return data(unit) and (data(unit).auras or {})[index]
end}
function UnitDebuff(unit,index,filter)
    assert(filter=='PLAYER'); local a=data(unit) and (data(unit).auras or {})[index]
    if a then return a.name,a.icon,a.applications,nil,a.duration,a.expirationTime,a.sourceUnit,false,false,a.spellId end
end
C_NamePlate={}
function C_NamePlate.GetNamePlateForUnit(unit) return MOCK.plates[unit] end
function C_NamePlate.GetNamePlates()
    local list={}; for _,p in pairs(MOCK.plates) do if p:IsShown() then list[#list+1]=p end end; return list
end
function C_NamePlate.GetNamePlateSize() return MOCK.nativeWidth,MOCK.nativeHeight end
function C_NamePlate.SetNamePlateSize(w,h)
    if not MOCK.barClickTest then
        MOCK.foreignWrites=MOCK.foreignWrites+1
        error('Native size writes require the explicit click test')
    end
    MOCK.nativeSizeAttempts=(MOCK.nativeSizeAttempts or 0)+1
    if MOCK.throwNativeSize and w>=2048 then error('Native client rejected size') end
    MOCK.setNativeSize(w,h)
end
function MOCK.setNativeSize(w,h)
    assert(not MOCK.combat,'Protected global size change during combat')
    MOCK.writes=MOCK.writes+1
    if not MOCK.refuseSize then
        local rounding = MOCK.sizeRounding or 0
        MOCK.nativeWidth,MOCK.nativeHeight=math.min(w,MOCK.sizeLimit or math.huge)+rounding,
            math.min(h,MOCK.sizeLimit or math.huge)+rounding
    end
end
C_NamePlateManager={}
function C_NamePlateManager.GetNamePlateHitTestInsets(kind) return unpack(MOCK.insets[kind]) end
function C_NamePlateManager.SetNamePlateHitTestInsets(kind,...)
    if not MOCK.barClickTest then
        MOCK.foreignWrites=MOCK.foreignWrites+1
        error('Native inset writes require the explicit click test')
    end
    assert(not MOCK.combat,'Protected native insets changed in combat')
    MOCK.insetWrites=MOCK.insetWrites+1;MOCK.insets[kind]={...}
    for i,value in ipairs(MOCK.insets[kind]) do MOCK.insets[kind][i]=value+(MOCK.insetRounding or 0) end
end
function C_NamePlateManager.IsNamePlateUnitBehindCamera(unit) return data(unit) and data(unit).behind==true end
function methods:GetUnit() return self.unitToken end
function methods:CanChangeHitTestPoints() return not MOCK.combat or MOCK.allowPlate==self end
function methods:GetHitTestPoints() measurement(self); return self.hitPoints end
function methods:ClearAllHitTestPoints()
    mutation(self);assert(self:CanChangeHitTestPoints(),'Native hit-test clear outside allowed tick')
    self.hitPoints={};MOCK.hitClears=(MOCK.hitClears or 0)+1
end
function methods:SetHitTestPoints(bindings)
    mutation(self)
    assert(self:CanChangeHitTestPoints(),'Native hit-test change outside allowed assignment tick')
    self.hitPoints={}; for _,p in ipairs(bindings) do
        self.hitPoints[#self.hitPoints+1]={point=p.point,relativeTo=p.relativeTo,relativePoint=p.relativePoint,
            offsetX=p.offsetX,offsetY=p.offsetY}
    end
end
function methods:SetAllHitTestPoints(frame)
    self:SetHitTestPoints({{point='TOPLEFT',relativeTo=frame,relativePoint='TOPLEFT',offsetX=0,offsetY=0},
        {point='BOTTOMRIGHT',relativeTo=frame,relativePoint='BOTTOMRIGHT',offsetX=0,offsetY=0}})
end
function methods:SetStackingBoundsFrame(frame) mutation(self); assert(frame,'Nil stacking bounds'); self.stacking=frame end
function hooksecurefunc(object,key,hook)
    MOCK.hookAttempts=MOCK.hookAttempts+1
    error('ElmoPlater must not hook Blizzard or Plater')
end
NamePlateDriverFrame={UpdateNamePlateSize=function() end}
MOCK.units.player={guid='Player-1',name='Warrior',level=10,health=200,maxHealth=200}
MOCK.units.pet={guid='Pet-1',name='Pet'}
function MOCK.event(event,...)
    local f=ElmoPlater.frame; if f.events[event] then f:GetScript('OnEvent')(f,event,...) end
end
function MOCK.start() MOCK.event('ADDON_LOADED','ElmoPlater'); MOCK.event('PLAYER_LOGIN') end
function MOCK.advance(seconds)
    for _=1,math.ceil(seconds/.05) do
        MOCK.time=MOCK.time+.05
        local f=ElmoPlater.frame; local fn=f:GetScript('OnUpdate'); if fn then fn(f,.05) end
    end
end
function MOCK.mob(unit,guid,name,plate)
    MOCK.inFixture=true
    local d={guid=guid or ('Creature-'..unit),name=name or 'Forest Wolf',level=10,health=100,maxHealth=100,auras={}}
    MOCK.units[unit]=d
    plate=plate or CreateFrame('NamePlate',nil,UIParent); plate.native=true; plate.unitToken=unit; plate:Show()
    -- Native unit-frame pooling resets both artwork anchors and native hit points.
    plate.UnitFrame=CreateFrame('Frame',nil,plate); plate.UnitFrame.nativeArtwork=true; plate.UnitFrame:SetAllPoints(plate)
    plate.hitPoints={{point='TOPLEFT',relativeTo=plate.UnitFrame,relativePoint='TOPLEFT',offsetX=0,offsetY=0},
        {point='BOTTOMRIGHT',relativeTo=plate.UnitFrame,relativePoint='BOTTOMRIGHT',offsetX=0,offsetY=0}}
    MOCK.inFixture=false
    MOCK.plates[unit]=plate; MOCK.allowPlate=plate; MOCK.event('NAME_PLATE_UNIT_ADDED',unit); MOCK.allowPlate=nil
    return d,plate
end
function MOCK.remove(unit)
    local plate=MOCK.plates[unit]; MOCK.event('NAME_PLATE_UNIT_REMOVED',unit)
    MOCK.units[unit]=nil; MOCK.plates[unit]=nil; if plate then plate:Hide() end
    return plate
end
function MOCK.aura(unit,id,seconds,source,count)
    local d=assert(data(unit)); local a={name='Debuff '..id,spellId=id,icon=id,auraInstanceID=id+1000,
        sourceUnit=source or 'player',duration=seconds,expirationTime=seconds>0 and MOCK.time+seconds or 0,
        applications=count or 1}; d.auras[#d.auras+1]=a; return a
end
function MOCK.log(event,guid,name,source,spellID,kind)
    ElmoPlater.CombatLog(MOCK.time,event,false,source or UnitGUID('player'),'Source',0,0,guid,name,0,0,
        spellID or 772,'Rend',1,kind or 'DEBUFF')
end
function MOCK.hit(unit,source,event)
    MOCK.log(event or 'SWING_DAMAGE',assert(UnitGUID(unit)),UnitName(unit),source)
end
local function contains(frame,x,y)
    local l,b,w,h=rect(frame); return w>0 and h>0 and x>=l and x<=l+w and y>=b and y<=b+h
end
function MouseIsOver(frame)
    return MOCK.pointerX and frame:IsVisible() and contains(frame,MOCK.pointerX,MOCK.pointerY) or false
end
function MOCK.hover(frame)
    if not frame then MOCK.pointerX,MOCK.pointerY=nil,nil; return end
    local l,b,w,h=frame:GetRect(); MOCK.pointerX,MOCK.pointerY=l+w/2,b+h/2
end
function MOCK.click(frame)
    local l,b,w,h=frame:GetRect(); return MOCK.clickAt(l+w/2,b+h/2)
end
function MOCK.clickAt(x,y)
    local found
    for unit,p in pairs(MOCK.plates) do
        local d=data(unit)
        if p:IsVisible() and d and not d.dead and not d.behind and contains(p,x,y) then
            local left,right,bottom,top
            for _,binding in ipairs(p.hitPoints) do
                local r=binding.relativeTo; local rx,ry,rw,rh=rect(r); local f=fractions[binding.relativePoint]
                local px,py=rx+rw*f[1]+(binding.offsetX or 0),ry+rh*f[2]+(binding.offsetY or 0)
                left=left and math.min(left,px) or px; right=right and math.max(right,px) or px
                bottom=bottom and math.min(bottom,py) or py; top=top and math.max(top,py) or py
            end
            local inset=MOCK.insets[d.friendly and 0 or 1]
            if x>=left+inset[1] and x<=right-inset[2] and y>=bottom+inset[4] and y<=top-inset[3] then
                assert(not found,'Overlapping native hit areas'); found=d.guid; MOCK.units.target=d
            end
        end
    end
    return found
end
