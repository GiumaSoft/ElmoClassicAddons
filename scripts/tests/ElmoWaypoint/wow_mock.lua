local methods={}
function methods:CreateLine() return CreateFrame('Line',nil,self) end
function methods:SetThickness(value) self.thickness=value end
function methods:SetStartPoint(...) self.start={...} end
function methods:SetEndPoint(...) self.finish={...} end
function methods:SetColorTexture(...) self.color={...} end
function methods:GetCenter() return self.centerX or 100,self.centerY or 100 end
function methods:CreateMaskTexture() return CreateFrame('MaskTexture',nil,self) end
function methods:AddMaskTexture(mask) self.mask=mask end
function methods:IsVisible() return self:IsShown() end
function methods:UnregisterAllEvents() self.events={} end
function methods:GetScale() return 1 end
function methods:GetZoom() return self.zoom or 0 end
function methods:SetZoom(zoom) self.zoom=zoom end
function methods:SetParent(parent) self.parent=parent end
function methods:SetOwner(owner,anchor) self.owner,self.anchor=owner,anchor;self.lines={} end
function methods:IsOwned(owner) return self.owner==owner end
function methods:SetVertexColor(...) self.vertex={...} end
local originalCreateFrame=CreateFrame
function CreateFrame(...)
    local frame=originalCreateFrame(...)
    for key,method in pairs(methods)do frame[key]=method end
    return frame
end
for _,frame in ipairs(MOCK.frames)do for key,method in pairs(methods)do frame[key]=method end end
MOCK.maps={
    [1]={name='Duskwood',continent=0,north=10000,west=20000,width=1000,height=2000},
    [2]={name='Elwynn Forest',continent=0,north=10000,west=18000,width=1000,height=2000},
    [3]={name='Darkshore',continent=1,north=11000,west=24000,width=1000,height=2000},
    [4]={name='Eastern Kingdoms',continent=0,north=20000,west=30000,width=20000,height=30000},
}
Enum.UIMapType={Cosmic=0,World=1,Continent=2,Zone=3,Dungeon=4,Micro=5}
WOW_PROJECT_CLASSIC,WOW_PROJECT_CAMELOT=2,99
for id,map in pairs(MOCK.maps)do map.mapID=id;map.mapType=Enum.UIMapType.Zone;map.parentMapID=0 end
MOCK.maps[1].parentMapID,MOCK.maps[2].parentMapID=4,4
MOCK.maps[4].mapType=Enum.UIMapType.Continent
MOCK.map,MOCK.px,MOCK.py,MOCK.facing=1,.5,.5,0
MOCK.mapReads=0
function CreateVector2D(x,y)
    return {x=x,y=y,GetXY=function(self)return self.x,self.y end}
end
C_Map={
    GetBestMapForUnit=function(unit)assert(unit=='player');return MOCK.map end,
    GetMapInfo=function(id)return MOCK.maps[id] end,
    GetPlayerMapPosition=function(id,unit)
        assert(unit=='player' and id==MOCK.map)
        MOCK.mapReads=MOCK.mapReads+1
        if MOCK.noPosition then return nil end
        if MOCK.secretPosition then return MOCK.secretPosition end
        return CreateVector2D(MOCK.px,MOCK.py)
    end,
    GetWorldPosFromMapPos=function(id,position)
        if MOCK.noWorld then return nil end
        local map=MOCK.maps[id]
        if not map then return end
        if MOCK.secretWorld then return map.continent,MOCK.secretWorld end
        return map.continent,CreateVector2D(map.north-position.y*map.height,map.west-position.x*map.width)
    end,
}
function GetPlayerFacing()return MOCK.facing end
C_Map.GetMapChildrenInfo=function()return {}end
C_Map.GetMapGroupID=function()end
function UnitPosition(unit)
    assert(unit=='player');local m=MOCK.maps[MOCK.map]
    if not m or MOCK.noPosition then return end
    return m.north-MOCK.py*m.height,m.west-MOCK.px*m.width,0,m.continent
end
MOCK.cvars={rotateMinimap='0',minimapZoom='0',minimapInsideZoom='1'}
function GetCVar(key)return MOCK.cvars[key]or'0'end
function IsLoggedIn()return false end
C_Timer={After=function()end}
function Mixin(target,...)
    for i=1,select('#',...)do for k,v in pairs(select(i,...))do target[k]=v end end
    return target
end
function CreateFromMixins(...)return Mixin({},...)end
MapCanvasDataProviderMixin={GetMap=function(self)return self.owningMap end}
MapCanvasPinMixin={SetPosition=function(self,x,y)self.position={x,y}end,
    UseFrameLevelType=function()end,SetScalingLimits=function()end}
function CreateFramePool()return {}end
WorldMapFrame=CreateFrame('Frame',nil,UIParent)
WorldMapFrame.pinPools,WorldMapFrame.pins={},{}
MOCK.browsedMap=3
function WorldMapFrame:GetMapID()return MOCK.browsedMap end
function WorldMapFrame:GetCanvas()return self end
function WorldMapFrame:AddDataProvider(provider)provider.owningMap=self;self.provider=provider end
function WorldMapFrame:AcquirePin(template,...)
    local pin=self.pinPools[template].createFunc()
    pin.template=template;pin:OnLoad();pin:OnAcquired(...)
    self.pins[#self.pins+1]=pin
    return pin
end
function WorldMapFrame:RemovePin(pin)
    for i,p in ipairs(self.pins)do if p==pin then table.remove(self.pins,i);break end end
    self.pinPools[pin.template].resetFunc(nil,pin)
end
function WorldMapFrame:EnumeratePinsByTemplate(template)
    local snapshot={};for _,p in ipairs(self.pins)do if p.template==template then snapshot[#snapshot+1]=p end end
    local i=0;return function()i=i+1;return snapshot[i]end
end
function WorldMapFrame:RemoveAllPinsByTemplate(template)
    for pin in self:EnumeratePinsByTemplate(template)do self:RemovePin(pin)end
end
function MOCK.browse(id)
    MOCK.browsedMap=id;WorldMapFrame.provider:RefreshAllData()
end
local proxy={}
SlashCmdList=setmetatable({},{__index=proxy})
MOCK.slash={}
local function import()
    local names={}
    for name in pairs(SlashCmdList)do names[#names+1]=name end
    for _,name in ipairs(names)do
        local fn=SlashCmdList[name]
        local i=1
        while _G['SLASH_'..name..i]do
            MOCK.slash[_G['SLASH_'..name..i]:upper()]=fn
            i=i+1
        end
        proxy[name]=fn;rawset(SlashCmdList,name,nil)
    end
end
ChatFrameUtil.ImportAllListsToHash=import
function MOCK.runSlash(command,text)
    local f=ChatFrameUtil and ChatFrameUtil.ImportAllListsToHash or ChatFrame_ImportAllListsToHash
    f();assert(MOCK.slash[command:upper()])(text or '')
end
function MOCK.start()
    MOCK.fire('ADDON_LOADED','ElmoWaypoint');MOCK.fire('PLAYER_LOGIN')
    MOCK.fire('PLAYER_ENTERING_WORLD',true,false)
end
function MOCK.legacyWaypoint()
    ChatFrame_ImportAllListsToHash=ChatFrameUtil.ImportAllListsToHash
    ChatFrameUtil,Settings=nil,nil
    function InterfaceOptions_AddCategory(panel)MOCK.legacyCategory=panel end
    function InterfaceOptionsFrame_OpenToCategory(panel)MOCK.openLegacy=panel end
end
