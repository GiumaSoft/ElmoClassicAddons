MOCK = {time=100, frames={}, requests={}, sent={}, invited={}, routing={}, who={}, members={}, raidMembers={}, categories={}, permissions=true, groupCount=0}
local methods = {}
function methods:SetScript(key, fn) self.scripts[key]=fn end
function methods:GetScript(key) return self.scripts[key] end
function methods:HookScript(key, fn)
    local old=self.scripts[key]
    self.scripts[key]=function(...) if old then old(...) end; fn(...) end
end
function methods:RegisterEvent(event) self.events[event]=true end
function methods:SetSize(w,h) self.w,self.h=w,h end
function methods:SetWidth(w) self.w=w end
function methods:SetHeight(h) self.h=h end
function methods:GetWidth() return self.w or 0 end
function methods:GetHeight() return self.h or 0 end
function methods:GetVertexColor() return 1,1,1,1 end
function methods:GetEffectiveScale() return 1 end
function methods:GetCenter() return 100,100 end
function methods:GetParent() return self.parent end
function methods:LockHighlight() self.highlightLocked=true end
function methods:UnlockHighlight() self.highlightLocked=false end
function methods:CreateAnimationGroup()
    local group={Stop=function()end,Play=function()end,SetToFinalAlpha=function()end}
    function group:CreateAnimation() return CreateFrame("Animation") end
    return group
end
function methods:SetPoint(...) self.point={...} end
function methods:GetPoint() return unpack(self.point or {"CENTER",UIParent,"CENTER",0,0}) end
function methods:ClearAllPoints() self.point=nil end
function methods:SetText(text)
    text=tostring(text or "")
    if self.text==text then return end
    self.text=text
    if self.scripts.OnTextChanged then self.scripts.OnTextChanged(self,false) end
end
function methods:GetText() return self.text or "" end
function methods:SetTexture(texture) self.texture=texture end
function methods:SetTextColor(...) self.color={...} end
function methods:SetFontObject(font) self.font=font end
function methods:SetFontString(font) self.fontString=font end
function methods:SetBackdrop(data) self.backdrop=data end
function methods:SetBackdropColor(...) self.background={...} end
function methods:SetBackdropBorderColor(...) self.border={...} end
function methods:SetChecked(value) self.checked=value==true end
function methods:GetChecked() return self.checked end
function methods:SetEnabled(value) self.enabled=not not value end
function methods:IsEnabled() return self.enabled~=false end
function methods:SetHighlightTexture(texture) self.highlight=CreateFrame("Texture",nil,self);self.highlight.texture=texture end
function methods:GetHighlightTexture() return self.highlight end
function methods:CreateTexture() return CreateFrame("Texture",nil,self) end
function methods:CreateFontString(_,_,font) local f=CreateFrame("FontString",nil,self);f.font=font;return f end
function methods:SetScrollChild(child) self.scrollChild=child end
function methods:SetShown(value)
    value=not not value
    if self.shown==value then return end
    self.shown=value
    local fn=self.scripts[value and "OnShow" or "OnHide"]
    if fn then fn(self) end
end
function methods:Show() self:SetShown(true) end
function methods:Hide() self:SetShown(false) end
function methods:IsShown() return self.shown and (not self.parent or self.parent:IsShown()) end
function methods:ClearFocus()
    local hadFocus=self.focused
    self.focused=false
    if hadFocus and self.scripts.OnEditFocusLost then self.scripts.OnEditFocusLost(self) end
end
function methods:SetFocus()
    for _,f in ipairs(MOCK.frames)do if f~=self and f.focused then f:ClearFocus() end end
    if self.focused then return end
    self.focused=true
    if self.scripts.OnEditFocusGained then self.scripts.OnEditFocusGained(self) end
end
function methods:HasFocus() return self.focused==true end
function methods:SetCursorPosition(position) self.cursor=position end
function methods:GetCursorPosition() return self.cursor or #self:GetText() end
function methods:Insert(text)
    local current,position=self:GetText(),self:GetCursorPosition()
    self:SetText(current:sub(1,position)..text..current:sub(position+1))
    self.cursor=position+#text
end
function methods:HighlightText() self.highlighted=true end
function methods:AddLine(text) self.lines=self.lines or {};self.lines[#self.lines+1]=text end
function CreateFrame(kind,name,parent,template)
    local f={kind=kind,name=name,parent=parent,template=template,scripts={},events={},shown=true}
    setmetatable(f,{__index=function(_,key)
        if methods[key] then return methods[key] end
        if key:match("^Set") or key:match("^Enable") or key:match("^Register") or key=="StartMoving" or key=="StopMovingOrSizing" then
            return function(self,...) self[key.."Args"]={...} end
        end
        if key:match("^[A-Z]") then error("Unknown frame method: "..key) end
    end})
    MOCK.frames[#MOCK.frames+1]=f
    if name then _G[name]=f end
    if template and template:find("InputBoxTemplate",1,true) then
        f.Left=CreateFrame("Texture",nil,f);f.Middle=CreateFrame("Texture",nil,f);f.Right=CreateFrame("Texture",nil,f)
    end
    return f
end
UIParent=CreateFrame("Frame")
UIParent:SetSize(1920,1080)
Minimap=CreateFrame("Frame",nil,UIParent);Minimap:SetSize(160,160)
WOW_PROJECT_ID,WOW_PROJECT_MAINLINE=2,1
function securecallfunction(fn,...) return fn(...) end
local function packed(...) return {n=select("#",...),...} end
function hooksecurefunc(target,name,hook)
    if type(target)=="string" then target,name,hook=_G,target,name end
    local original=target[name]
    assert(type(original)=="function","Cannot hook missing function")
    target[name]=function(...)
        local result=packed(original(...));hook(...)
        return unpack(result,1,result.n)
    end
end
function IsModifiedClick(binding) return binding=="CHATLINK" and MOCK.shift==true end
SettingsPanel=CreateFrame("Frame",nil,UIParent)
function HideUIPanel(panel) panel:Hide() end
GameTooltip=CreateFrame("GameTooltip",nil,UIParent)
UISpecialFrames,SlashCmdList={},{}
DEFAULT_CHAT_FRAME={AddMessage=function(_,text) MOCK.printed=text end}
RAID_CLASS_COLORS={MAGE={r=.25,g=.78,b=.92},PRIEST={r=1,g=1,b=1}}
function MOCK.fire(event,...)
    for _,f in ipairs(MOCK.frames) do if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f,event,...) end end
end
function MOCK.start() MOCK.fire("ADDON_LOADED","ElmoLFM");MOCK.fire("PLAYER_LOGIN") end
function MOCK.advance(dt)
    MOCK.time=MOCK.time+dt
    for _,f in ipairs(MOCK.frames) do if f.scripts.OnUpdate then f.scripts.OnUpdate(f,dt) end end
end
function MOCK.click(button,which)
    assert(button:IsEnabled(),"Disabled button clicked")
    which=which or "LeftButton"
    if which=="RightButton" then
        local registered=false
        for _,value in ipairs(button.RegisterForClicksArgs or {})do
            if value=="RightButtonUp" or value=="AnyUp" then registered=true end
        end
        assert(registered,"Button does not receive native right-clicks")
    end
    if button.kind=="CheckButton" and which=="LeftButton" then button:SetChecked(not button:GetChecked()) end
    assert(button.scripts.OnClick)(button,which)
end
function MOCK.button(text)
    for _,f in ipairs(MOCK.frames)do if f.kind=="Button" and f:GetText()==text then return f end end
    error("Missing button "..text)
end
function MOCK.row(name)
    for _,f in ipairs(MOCK.frames)do if f.kind=="Button" and f.player and f.player.name==name then return f end end
    error("Missing player row "..name)
end
function MOCK.player(name, level, zone, class)
    return {fullName=name,level=level or 39,area=zone or "Alterac Mountains",classStr=class or "Mage",filename="MAGE",fullGuildName="Test guild"}
end
function MOCK.results(players,total)
    MOCK.who=players;MOCK.total=total or #players;MOCK.fire("WHO_LIST_UPDATE")
end
function MOCK.search(players)
    assert(A.Search("Alterac Mountains",38,40));MOCK.enterChat();MOCK.results(players)
end
function MOCK.enterChat()
    assert(MOCK.chatCommand and MOCK.chatCommand:sub(1,5)=="/who ")
    MOCK.requests[#MOCK.requests+1]=MOCK.chatCommand:sub(6)
    MOCK.chatCommand=nil
end
function MOCK.selectAll() for _,p in ipairs(A.results)do A.selected[p.key]=true end end
function GetTime() return MOCK.time end
function GetCursorPosition() return MOCK.cursorX or 0, MOCK.cursorY or 100 end
function GetNormalizedRealmName() return "MyRealm" end
function GetRealmName() return "My Realm" end
function UnitFullName() return "Tester","MyRealm" end
UnitName=UnitFullName
function UnitLevel() return 39 end
function GetRealZoneText() return "Alterac Mountains" end
function IsInGroup() return MOCK.groupCount>0 end
function IsInRaid() return MOCK.raid==true end
function GetNumGroupMembers() return MOCK.groupCount end
function UnitIsGroupLeader() return MOCK.permissions end
function UnitIsGroupAssistant() return false end
function UnitInParty(name) return MOCK.members[A.NameKey(name)]==true end
function UnitInRaid(name) return MOCK.raidMembers[A.NameKey(name)] end
C_FriendList={
    SendWho=function() error("Addons cannot invoke WHO in this fixture") end,
    SetWhoToUi=function(value) MOCK.routing[#MOCK.routing+1]=value end,
    GetNumWhoResults=function() return MOCK.privateCount or #MOCK.who,MOCK.total or #MOCK.who end,
    GetWhoInfo=function(index) return MOCK.who[index] end,
}
ChatFrameUtil={OpenChat=function(command)
    if MOCK.openChatError then error("Chat unavailable") end
    MOCK.chatCommand=command
end,InsertLink=function(text)
    MOCK.nativeLink=text
    return false
end}
function ChatEdit_GetActiveWindow() return MOCK.nativeChat end
ChatEdit_InsertLink=ChatFrameUtil.InsertLink
function MOCK.questie()
    local data={GetQuestLink=function(quest)
        return "[["..quest.level.."] "..quest.name.." ("..quest.Id..")]"
    end}
    local line=CreateFrame("Button",nil,UIParent)
    line.Quest={Id=555,level=31,name="Soothing Turtle Bisque"}
    function line:SetOnClick()
        self:SetScript("OnClick",function(self,button)
            MOCK.questNormalClicks=(MOCK.questNormalClicks or 0)+1
            if button=="LeftButton" and IsModifiedClick("CHATLINK") then
                if ChatEdit_GetActiveWindow() then ChatEdit_InsertLink(data.GetQuestLink(self.Quest))
                else MOCK.untracked=(MOCK.untracked or 0)+1 end
            end
        end)
    end
    line:SetOnClick();MOCK.questRow=line
    local pool={GetLine=function(index) if index==1 then return line end end}
    QuestieLoader={ImportModule=function(_,name)
        return name=="TrackerLinePool" and pool or name=="TrackerData" and data or nil
    end}
end
C_ChatInfo={SendChatMessage=function(message,kind,language,target)
    assert(kind=="WHISPER","No public announcements are allowed")
    if MOCK.sendError or MOCK.hardwareOnly and not MOCK.hardware then error("Whisper blocked") end
    MOCK.sent[#MOCK.sent+1]={message=message,target=target,time=MOCK.time}
    if MOCK.informImmediately then MOCK.fire("CHAT_MSG_WHISPER_INFORM",message,target) end
end}
C_PartyInfo={
    CanInvite=function() return MOCK.permissions end,
    InviteUnit=function(name)
        if MOCK.inviteError then error("Invite blocked") end
        MOCK.invited[#MOCK.invited+1]=name
    end,
}
Enum={SocialWhoOrigin={Social=1}}
Settings={
    RegisterCanvasLayoutCategory=function(panel,name)
        local category={panel=panel,name=name,GetID=function()return 123 end}
        MOCK.categories[#MOCK.categories+1]=category;return category
    end,
    RegisterAddOnCategory=function(category) category.registered=true end,
    OpenToCategory=function(id) MOCK.openCategory=id end,
}
local secrets={}
function MOCK.secret()
    local value=setmetatable({},{
        __tostring=function()error("Private tostring")end,
        __index=function()error("Private indexing")end,
        __lt=function()error("Private comparison")end,
        __add=function()error("Private arithmetic")end})
    secrets[value]=true;return value
end
function issecretvalue(value) return secrets[value]==true end
function canaccessvalue(value) return not issecretvalue(value) end
function canaccesstable(value) return value~=MOCK.blockedTable end
function MOCK.legacy()
    SendWho,SetWhoToUI,GetNumWhoResults=C_FriendList.SendWho,C_FriendList.SetWhoToUi,C_FriendList.GetNumWhoResults
    GetWhoInfo=function(index)
        local p=MOCK.who[index]
        if p then return p.fullName,p.fullGuildName,p.level,p.raceStr,p.classStr,p.area,p.filename end
    end
    SendChatMessage,InviteUnit=C_ChatInfo.SendChatMessage,C_PartyInfo.InviteUnit
    ChatFrame_OpenChat,ChatFrameUtil=ChatFrameUtil.OpenChat,nil
    C_FriendList,C_ChatInfo,C_PartyInfo=nil,nil,nil
end
