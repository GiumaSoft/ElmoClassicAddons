"""Interaction smoke checks with mock WoW frames; no visual/client verification."""
import unittest
from lupa.lua51 import LuaRuntime
from test_core import ROOT, WOW_STUB

FRAMES = r'''
frames, UISpecialFrames, SlashCmdList = {}, {}, {}
local methods = {}
function methods:SetScript(k,fn) self.scripts[k]=fn end
function methods:GetScript(k) return self.scripts[k] end
function methods:HookScript(k,fn)
 local old=self.scripts[k]
 self.scripts[k]=function(...) if old then old(...) end;fn(...) end
end
function methods:RegisterEvent(ev) self.events[ev]=true end
function methods:SetSize(w,h)self.w,self.h=w,h end
function methods:GetWidth()return self.w or 100 end
function methods:GetHeight()return self.h or 100 end
function methods:SetWidth(w)self.w=w end
function methods:SetHeight(h)self.h=h end
function methods:SetScale(s)self.scale=s end
function methods:GetScale()return self.scale or 1 end
function methods:GetPoint()return 'CENTER',UIParent,'CENTER',0,0 end
function methods:SetText(s)
 s=tostring(s or '')
 if self.text==s then return end
 self.text=s
 if self.scripts.OnTextChanged then self.scripts.OnTextChanged(self,false)end
end
function methods:GetText()return self.text or '' end
function methods:GetNumber()return tonumber(self:GetText())or 0 end
function methods:SetMultiLine(v)self.multiLine=v end
function methods:SetChecked(v)self.checked=not not v end
function methods:GetChecked()return self.checked end
function methods:SetEnabled(v)self.enabled=not not v end
function methods:IsEnabled()return self.enabled~=false end
function methods:HasFocus()return false end
function methods:SetShown(v)
 v=not not v
 if self.shown==v then return end
 self.shown=v
 local fn=self.scripts[v and 'OnShow' or 'OnHide'];if fn then fn(self)end
end
function methods:Show()self:SetShown(true)end
function methods:Hide()self:SetShown(false)end
function methods:IsShown()return self.shown end
function methods:SetVerticalScroll(v)self.scroll=v end
function methods:GetVerticalScroll()return self.scroll or 0 end
function methods:SetHighlightTexture()self.highlight=CreateFrame('Texture',nil,self)end
function methods:GetHighlightTexture()return self.highlight end
function methods:CreateTexture()return CreateFrame('Texture',nil,self)end
function methods:CreateFontString()return CreateFrame('FontString',nil,self)end
function methods:LockHighlight()self.locked=true end
function methods:UnlockHighlight()self.locked=false end
function CreateFrame(kind,name,parent,template)
 local frame={kind=kind,name=name,parent=parent,scripts={},events={},shown=true,text=''}
 setmetatable(frame,{__index=function(_,k)
  if methods[k]then return methods[k]end
  if k:match('^Set')or k:match('^Enable')or k:match('^Clear')or k:match('^Add')or k:match('^Register')or k:match('^Start')or k:match('^Stop')then return function()end end
 end})
 frames[#frames+1]=frame;if name then _G[name]=frame end
 if template and template:find('InputBoxTemplate',1,true)then
  frame.Left=CreateFrame('Texture');frame.Middle=CreateFrame('Texture');frame.Right=CreateFrame('Texture')
 end
 return frame
end
function fire(ev,...)
 for _,f in ipairs(frames)do if f.events[ev]and f.scripts.OnEvent then f.scripts.OnEvent(f,ev,...)end end
end
function click(text)
 for _,f in ipairs(frames)do if f.kind=='Button'and f.text==text and f.scripts.OnClick then f.scripts.OnClick(f);return f end end
 error('Missing button '..text)
end
UIParent=CreateFrame('Frame');UIParent:SetSize(1920,1080)
GameTooltip=CreateFrame('GameTooltip')
C_Timer={NewTicker=function(_,fn)ticker=fn end,After=function(_,fn)fn()end}
function IsLoggedIn()return true end
function UIDropDownMenu_SetText(frame,text)frame.label=text end
function UIDropDownMenu_SetWidth()end
function UIDropDownMenu_Initialize(frame,fn)frame.menu=fn end
function UIDropDownMenu_CreateInfo()return {}end
function UIDropDownMenu_AddButton()end
function JoinChannelByName()end
function wipe(t)for k in pairs(t)do t[k]=nil end end
QuestDifficultyColors={trivial={r=.5,g=.5,b=.5}}
function GetQuestDifficultyColor()return {r=1,g=1,b=0}end
local libs={
 ['LibDataBroker-1.1']={NewDataObject=function(_,name,obj)return obj end},
 ['LibDBIcon-1.0']={Register=function()end},
}
function LibStub(name)return assert(libs[name])end
function print()end
'''

class ElmoLFGUITests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(WOW_STUB)
        self.lua.execute(FRAMES)
        self.lua.execute('A={}')
        for file in ('Data.lua','Core.lua','Roles.lua','Theme.lua','UI.lua'):
            self.lua.execute((ROOT/file).read_text(),'ElmoLFG',self.lua.globals().A)
        self.lua.execute("fire('ADDON_LOADED','ElmoLFG'); A.Toggle()")

    def test_role_dialog_assignments_update_the_composer(self):
        self.lua.execute('''
            A.db.selected['d:dm']=true;A.SetPlayerRole('tank')
            setParty({{name='Priest',class='PRIEST'}})
            fire('GROUP_ROSTER_UPDATE')
            click('Group roles');assert(ElmoLFGGroupRoles:IsShown())
            local row
            for _,f in ipairs(frames)do if f.member and f.member.name=='Priest-Realm'then row=f end end
            assert(row and row.member.role==nil)
            row.buttons.Healer.scripts.OnClick(row.buttons.Healer)
            assert(A.DungeonRoleText()=='3 Dps')
            assert(ElmoLFGGroupRoles.summary:GetText()=='Open: 3 Dps')
            local preview=ElmoLFGAnnouncementPreview.text
            assert(preview and preview:GetText()=='LFM The Deadmines need 3 Dps - /w me inv role (tank, heal, dps)(autojoin)')
            row.buttons.Auto.scripts.OnClick(row.buttons.Auto)
            assert(A.GroupComposition().unknown==1)
            ElmoLFGFrame:Hide();assert(not ElmoLFGGroupRoles:IsShown())
        ''')

    def test_whisper_and_roster_events_update_recruitment_without_sending_replies(self):
        self.lua.execute('''
            A.db.selected['d:dm']=true;A.SetPlayerRole('dps');assert(A.StartAnnouncing())
            fire('CHAT_MSG_WHISPER','inv tank','Alice-Realm')
            assert(#invited==1 and #sent==1)
            setParty({{name='Alice'}});fire('GROUP_ROSTER_UPDATE')
            assert(A.DungeonRoleText()=='1 Heal/2 Dps')
            local preview=ElmoLFGAnnouncementPreview.text
            assert(preview:GetText():find('need 1 Heal | 2 Dps',1,true))
            assert(#sent==1)
        ''')

if __name__=='__main__':unittest.main(verbosity=2)
