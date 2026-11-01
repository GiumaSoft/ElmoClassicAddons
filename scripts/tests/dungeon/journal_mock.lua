-- Extend the strict 1.x API fixture with the actual Frame/Slider methods used by the journal.
local methods=getmetatable(UIParent).__index
local noop=function() end
for _,key in ipairs({"SetTextInsets","SetAutoFocus","SetMaxLetters"}) do methods[key]=noop end
function methods:ClearFocus() self.focus=false end
local setText=methods.SetText
function methods:SetText(value)
    setText(self,value)
    if self.kind=='EditBox' and self.scripts.OnTextChanged then self.scripts.OnTextChanged(self,false) end
end
for _,key in ipairs({"SetJustifyV","SetShadowColor","SetShadowOffset","SetFont","SetVertexColor",
    "SetAlpha","SetOrientation","SetValueStep","SetFrameLevel","SetScale"}) do methods[key]=noop end
function methods:SetFont(path,size,flags) self.font,self.fontSize,self.fontFlags=path,size,flags end
function methods:SetTextColor(r,g,b) self.color={r,g,b} end
function methods:SetVertexColor(r,g,b,a) self.vertexColor={r,g,b,a} end
function methods:SetAlpha(a) self.alpha=a end
function methods:SetBackdropColor(r,g,b,a) self.backColor={r,g,b,a} end
function methods:SetBackdropBorderColor(r,g,b,a) self.borderColor={r,g,b,a} end
function methods:SetTexture(path) self.texture=path end
function methods:GetFrameLevel() return 1 end
function methods:GetPoint() return unpack(self.point or {"CENTER",UIParent,"CENTER",0,0}) end
function methods:SetMinMaxValues(a,b) self.low,self.high=a,b end
function methods:SetValue(v)
    if self.value==v then return end
    self.value=v
    if self.scripts.OnValueChanged then self.scripts.OnValueChanged(self,v) end
end
function methods:GetValue() return self.value or 0 end
function methods:SetThumbTexture(path) self.thumb=self:CreateTexture();self.thumb:SetTexture(path) end
function methods:GetThumbTexture() return self.thumb end
function methods:SetOwner(owner,anchor) self.owner,self.anchor=owner,anchor end
function methods:GetStringHeight()
    local visible=tostring(self.text or ''):gsub('|c%x%x%x%x%x%x%x%x',''):gsub('|r','')
    local cols=math.max(1,math.floor((self.width or 200)/((self.fontSize or 12)*.56)))
    local lines=0
    for line in (visible..'\n'):gmatch('(.-)\n') do lines=lines+math.max(1,math.ceil(#line/cols)) end
    return lines*(self.fontSize or 12)*1.12
end
function methods:AddLine(s) self.lines=self.lines or {};self.lines[#self.lines+1]=s end
local make=CreateFrame
MOCK.frames={}
function CreateFrame(...)
    local f=make(...);MOCK.frames[#MOCK.frames+1]=f;f.mockID=#MOCK.frames
    f.anchors={}
    return f
end
function methods:CreateTexture(name,layer,template,sub)
    local t=CreateFrame('Texture',name,self);t.layer,t.sub=layer,sub;return t
end
local point=methods.SetPoint
function methods:SetPoint(...)
    point(self,...);self.anchors=self.anchors or {};self.anchors[#self.anchors+1]={...}
end
function methods:ClearAllPoints() self.point=nil;self.anchors={} end
function methods:SetAllPoints(target) self.allPoints=target or self.parent end
UIParent:SetSize(1440,900)
UISpecialFrames={};tinsert=table.insert
BackdropTemplateMixin={}
MOCK.faction='Alliance';MOCK.race=3
local classIds={WARRIOR=1,PALADIN=2,HUNTER=3,ROGUE=4,PRIEST=5,SHAMAN=7,MAGE=8,WARLOCK=9,DRUID=11}
function UnitClass() return MOCK.class,MOCK.class,classIds[MOCK.class] end
function UnitFactionGroup() return MOCK.faction end
function UnitRace() return 'Dwarf','Dwarf',MOCK.race end
C_Map={GetMapInfo=function() return nil end}
C_QuestLog={IsQuestFlaggedCompleted=function(id) return (MOCK.completed or {})[id] or false end,
    GetLogIndexForQuestID=function(id) return (MOCK.log or {})[id] and 1 or 0 end}
function GetQuestDifficultyColor(level)
    if level>=MOCK.level+5 then return {r=1,g=.1,b=.1} end
    if level>=MOCK.level+3 then return {r=1,g=.5,b=.25} end
    return {r=1,g=1,b=0}
end
function IsModifiedClick() return MOCK.shift or false end
function ChatEdit_InsertLink(link) MOCK.inserted=link end
C_Timer={After=function(_,fn) fn() end}
C_TooltipInfo=nil -- Exercise Era's GameTooltip adapter, not beta tooltip APIs.
ITEM_QUALITY_COLORS={
    [0]={r=.62,g=.62,b=.62},[1]={r=1,g=1,b=1},[2]={r=.12,g=1,b=0},
    [3]={r=0,g=.44,b=.87},[4]={r=.64,g=.21,b=.93},[5]={r=1,g=.5,b=0},
}
