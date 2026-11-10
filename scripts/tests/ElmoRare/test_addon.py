"""Real addon Lua with explicit public/secret and secure-click mocks; no live input."""
from pathlib import Path
import os
import unittest
import xml.etree.ElementTree as ET
from lupa.lua51 import LuaRuntime

ROOT=Path(__file__).resolve().parents[3]
ADDON=Path(os.environ.get('ELMO_TEST_ADDON',ROOT/'ElmoRare'))
STUB=r'''
MOCK={time=100,frames={},units={},plates={},sounds={},messages={},categories={},combat=false,
 forbidden=0,marks={},attributeWrites=0,hardware=false}
SlashCmdList={};STANDARD_TEXT_FONT='Fonts/FRIZQT__.TTF';BackdropTemplateMixin={}
SOUNDKIT={RAID_WARNING=8959};SECURE_ACTIONS={raidtarget=function()error('Do not call native handlers from addon Lua')end}
local methods={}
local function noop()end
for _,k in ipairs({'SetJustifyH','SetFrameStrata','SetClampedToScreen','SetMovable','RegisterForDrag',
 'SetBackdrop','SetBackdropColor','SetBackdropBorderColor','StartMoving','StopMovingOrSizing'})do methods[k]=noop end
function methods:SetSize(w,h)self.width,self.height=w,h end
function methods:SetWidth(w)self.width=w end
function methods:SetHeight(h)self.height=h end
function methods:SetFont(path,size,flags)self.font,self.fontSize=path,size end
function methods:SetTextColor(...)self.color={...}end
function methods:SetPoint(...)self.point={...}end
function methods:ClearAllPoints()self.point=nil end
function methods:GetPoint()return unpack(self.point or {})end
function methods:SetWordWrap(v)self.wrap=v end
function methods:SetScript(k,v)
 assert(not(self.secure and k=='OnClick'),'Never replace the secure OnClick handler')
 self.scripts[k]=v
end
function methods:GetScript(k)return self.scripts[k]end
function methods:RegisterForClicks(...)self.clicks={...}end
function methods:SetAttribute(k,v)
 assert(not MOCK.combat,'Secure attributes changed during combat')
 self.attributes[k]=v;MOCK.attributeWrites=MOCK.attributeWrites+1
end
function methods:Click()MOCK.forbidden=MOCK.forbidden+1;error('Addon must not synthesize clicks')end
function methods:EnableMouse(v)self.mouse=v end
function methods:SetText(v)self.text=tostring(v)end
function methods:GetText()return self.text or ''end
function methods:Show()self.shown=true end
function methods:Hide()
 local was=self.shown;self.shown=false
 if was and self.scripts.OnHide then self.scripts.OnHide(self)end
end
function methods:IsShown()return self.shown end
function methods:SetChecked(v)self.checked=v==true end
function methods:GetChecked()return self.checked end
function methods:CreateFontString()return CreateFrame('FontString',nil,self)end
function methods:CreateTexture()return CreateFrame('Texture',nil,self)end
function methods:SetTexture(v)self.texture=v end
function methods:SetOwner(owner,anchor)self.owner,self.anchor=owner,anchor end
function methods:ClearLines()self.lines={}end
function methods:AddLine(line)self.lines=self.lines or {};self.lines[#self.lines+1]=line end
function methods:RegisterEvent(event)
 assert(event~='COMBAT_LOG_EVENT_UNFILTERED');self.events[event]=true;return true
end
function methods:GetUnit()return self.unitToken end
function methods:IsForbidden()return self.forbidden==true end
function CreateFrame(kind,name,parent,template)
 local f=setmetatable({kind=kind,name=name,parent=parent,template=template,scripts={},events={},
 attributes={},shown=true},{__index=methods})
 if template=='SecureActionButtonTemplate'then
  f.secure=true
  f.scripts.OnClick=function(self,button,down)
   assert(MOCK.hardware,'Only a real test hardware click can dispatch the template')
   assert(self.attributes.type=='raidtarget'and self.attributes.unit=='target')
   if not down then return end
   local target=MOCK.units.target
   if target and target.marker~=self.attributes.marker and MOCK.permission~=false then
    target.marker=self.attributes.marker;MOCK.marks[#MOCK.marks+1]=target.guid
   end
  end
 end
 MOCK.frames[#MOCK.frames+1]=f;if name then _G[name]=f end;return f
end
UIParent=CreateFrame('Frame')
DEFAULT_CHAT_FRAME={AddMessage=function(_,m)MOCK.messages[#MOCK.messages+1]=m end}
function GetTime()return MOCK.time end
function InCombatLockdown()return MOCK.combat end
local hidden={}
function MOCK.secret()
 local v=setmetatable({},{__tostring=function()error('Private tostring')end,
  __index=function()error('Private traversal')end,__lt=function()error('Private compare')end,
  __add=function()error('Private arithmetic')end})
 hidden[v]=true;return v
end
function issecretvalue(v)return rawget(hidden,v)==true end
function canaccessvalue(v)return not issecretvalue(v)end
function canaccesstable(v)return v~=MOCK.unreadableTable end
local function field(unit,key,default)
 local d=MOCK.units[unit];if not d then return default end
 return d[key]
end
function UnitExists(u)return field(u,'exists',false)end
function UnitClassification(u)return field(u,'classification')end
function UnitGUID(u)return field(u,'guid')end
function UnitName(u)return field(u,'name')end
function UnitLevel(u)return field(u,'level')end
function UnitIsDeadOrGhost(u)return field(u,'dead',false)end
function UnitPlayerControlled(u)return field(u,'controlled',false)end
function PlaySound(id,channel)MOCK.sounds[#MOCK.sounds+1]={id=id,channel=channel};return true end
C_NamePlate={GetNamePlates=function()
 if MOCK.plateList then return MOCK.plateList end
 local list={};for _,p in pairs(MOCK.plates)do list[#list+1]=p end;return list
end}
Settings={RegisterCanvasLayoutCategory=function(panel,name)
 assert(not MOCK.categories[name],'Duplicate addon category')
 local c={panel=panel,name=name};function c:GetID()return self.name end
 MOCK.categories[name]=c;return c
end,RegisterAddOnCategory=function(c)c.registered=true end,
 OpenToCategory=function(id)MOCK.openCategory=id end}
function MOCK.event(event,...)
 for _,f in ipairs(MOCK.frames)do
  if f.events[event]and f.scripts.OnEvent then f.scripts.OnEvent(f,event,...)end
 end
end
function MOCK.tick(delta)
 MOCK.time=MOCK.time+delta
 for _,f in ipairs(MOCK.frames)do if f.scripts.OnUpdate then f.scripts.OnUpdate(f,delta)end end
end
function MOCK.mob(unit,id,name,classification,spawn,silent)
 local d={exists=true,guid='Creature-0-1-2-3-'..id..'-'..(spawn or'01'),name=name or'Rare Wolf',
  classification=classification or'rare',level=25,dead=false,controlled=false}
 MOCK.units[unit]=d
 if unit:match('^nameplate%d+$')then
  local p=CreateFrame('NamePlate');p.unitToken=unit;MOCK.plates[unit]=p
  if not silent then MOCK.event('NAME_PLATE_UNIT_ADDED',unit)end
 end
 return d
end
function MOCK.remove(unit)
 MOCK.event('NAME_PLATE_UNIT_REMOVED',unit);MOCK.units[unit]=nil;MOCK.plates[unit]=nil
end
function MOCK.press()
 local b=assert(ElmoRareMarkTargetButton);MOCK.hardware=true
 b.scripts.OnClick(b,'LeftButton',true);b.scripts.OnClick(b,'LeftButton',false)
 MOCK.hardware=false
end
for _,name in ipairs({'SetRaidTarget','TargetUnit','SetBinding','SetOverrideBinding','SetOverrideBindingClick',
 'SetCVar','SendChatMessage','hooksecurefunc','UnitHealth','UnitHealthMax','CombatLogGetCurrentEventInfo'})do
 _G[name]=function()MOCK.forbidden=MOCK.forbidden+1;error('Forbidden or unsolicited API '..name)end
end
'''


def create_vm(setup='',saved=None):
    vm=LuaRuntime(unpack_returned_tuples=True);vm.execute(STUB)
    if saved is not None:vm.globals().ElmoRareDB=vm.table_from(saved,recursive=True)
    if setup:vm.execute(setup)
    ns=vm.table();loader=vm.eval('function(s,name,ns)assert(loadstring(s,"@"..name))("ElmoRare",ns)end')
    for name in (ADDON/'ElmoRare.toc').read_text().splitlines():
        if name.endswith('.lua'):loader((ADDON/name).read_text(),name,ns)
    vm.globals().A=ns;vm.execute("MOCK.event('ADDON_LOADED','ElmoRare')")
    return vm


class RareTests(unittest.TestCase):
    def test_existing_nearby_rare_alerts_without_a_target_or_mouseover(self):
        vm=create_vm("MOCK.mob('nameplate1',123,'Rare Wolf','rare',nil,true)")
        vm.execute('''
        assert(#MOCK.sounds==1 and A.UI.banner:IsShown()and A.last.name=='Rare Wolf')
        assert(not MOCK.units.target and not MOCK.units.mouseover)
        assert(A.last.npcID==123 and A.UI.name:GetText()=='Rare Wolf')
        assert(MOCK.sounds[1].channel=='Master'and #MOCK.marks==0 and MOCK.forbidden==0)
        ''')

    def test_nameplate_target_mouseover_and_repeated_scans_deduplicate_same_spawn(self):
        vm=create_vm()
        vm.execute('''
        local mob=MOCK.mob('nameplate1',123)
        MOCK.units.target=mob;MOCK.units.mouseover=mob
        MOCK.event('PLAYER_TARGET_CHANGED');MOCK.event('UPDATE_MOUSEOVER_UNIT')
        for i=1,100 do MOCK.tick(.5)end
        assert(#MOCK.sounds==1 and #MOCK.marks==0)
        MOCK.event('PLAYER_ENTERING_WORLD');assert(#MOCK.sounds==1)
        MOCK.mob('nameplate2',123,'Rare Wolf','rare','02');assert(#MOCK.sounds==2)
        ''')

    def test_rare_elites_work_but_normals_elites_bosses_dead_and_controlled_units_do_not(self):
        vm=create_vm()
        vm.execute('''
        for i,rank in ipairs({'normal','elite','worldboss','minus'})do MOCK.mob('nameplate'..i,i,nil,rank)end
        assert(#MOCK.sounds==0)
        local d=MOCK.mob('target',55);d.dead=true;MOCK.event('PLAYER_TARGET_CHANGED');assert(#MOCK.sounds==0)
        d.dead=false;d.controlled=true;MOCK.event('PLAYER_TARGET_CHANGED');assert(#MOCK.sounds==0)
        d.controlled=false;d.guid='Pet-0-1-2-3-55-01';MOCK.event('PLAYER_TARGET_CHANGED');assert(#MOCK.sounds==0)
        d.guid='Creature-0-1-2-3-55-01';d.classification='rareelite';MOCK.event('PLAYER_TARGET_CHANGED')
        assert(#MOCK.sounds==1 and A.UI.detail:GetText():find('Rare elite',1,true))
        ''')

    def test_private_or_unavailable_identity_and_classification_are_retried_safely(self):
        vm=create_vm()
        vm.execute('''
        local d=MOCK.mob('target',12);local original=d.guid
        for _,key in ipairs({'classification','guid','name','dead','controlled','exists'})do
          local old=d[key];d[key]=MOCK.secret();A.Probe('target');assert(#MOCK.sounds==0);d[key]=old
        end
        d.name=nil;A.Probe('target');assert(#MOCK.sounds==0)
        d.name='Loaded Rare';d.level=MOCK.secret();MOCK.event('PLAYER_TARGET_CHANGED')
        assert(#MOCK.sounds==1 and A.UI.detail:GetText():find('??',1,true))
        A.UI.Tooltip();assert(A.UI.tooltip:IsShown()and MOCK.forbidden==0)
        ''')

    def test_delayed_nameplate_data_and_recycled_token_produce_the_correct_new_alert(self):
        vm=create_vm()
        vm.execute('''
        local d=MOCK.mob('nameplate1',77,nil,'normal');assert(#MOCK.sounds==0)
        d.classification='rare';d.name=nil;MOCK.tick(.5);assert(#MOCK.sounds==0)
        d.name='Late Rare';MOCK.tick(.5);assert(#MOCK.sounds==1 and A.last.name=='Late Rare')
        MOCK.remove('nameplate1');assert(not A.units.nameplate1)
        MOCK.mob('nameplate1',88,'Different Rare','rare','new');assert(#MOCK.sounds==2 and A.last.npcID==88)
        ''')

    def test_no_repeat_while_present_rearm_after_absence_and_cache_bound(self):
        vm=create_vm()
        vm.execute('''
        MOCK.mob('nameplate1',123)
        for i=1,650 do MOCK.tick(.5)end;assert(#MOCK.sounds==1)
        MOCK.remove('nameplate1');MOCK.tick(301)
        MOCK.mob('nameplate1',123);assert(#MOCK.sounds==2)
        for i=1,300 do MOCK.mob('target',1000+i);A.Probe('target')end
        local n=0;for _ in pairs(A.seen)do n=n+1 end;assert(n<=256)
        ''')

    def test_sound_popup_and_detection_switches_apply_independently(self):
        vm=create_vm(saved={'enabled':True,'sound':False,'popup':True})
        vm.execute('''
        MOCK.mob('nameplate1',1);assert(#MOCK.sounds==0 and A.UI.banner:IsShown())
        A.db.sound=true;A.db.popup=false;A.UI.Hide();MOCK.mob('nameplate2',2)
        assert(#MOCK.sounds==1 and not A.UI.banner:IsShown())
        A.Command('off');MOCK.mob('nameplate3',3);MOCK.tick(.5);assert(#MOCK.sounds==1)
        A.db.popup=true;A.Command('on');assert(A.db.enabled and #MOCK.sounds==4)
        assert(MOCK.forbidden==0)
        ''')

    def test_preview_tooltip_dismiss_expiry_and_last_sighting(self):
        vm=create_vm()
        vm.execute('''
        A.Command('test');assert(#MOCK.sounds==1 and not A.last and not next(A.seen))
        A.UI.banner.scripts.OnEnter();assert(A.UI.tooltip.lines[1]=='Rare alert preview')
        A.UI.banner.scripts.OnLeave();assert(not A.UI.tooltip:IsShown())
        MOCK.tick(12);assert(not A.UI.banner:IsShown())
        MOCK.mob('nameplate1',44,'A Rare');A.UI.banner.scripts.OnEnter()
        local text=table.concat(A.UI.tooltip.lines,string.char(10));assert(text:find('NPC ID: 44',1,true))
        A.UI.banner.scripts.OnMouseUp(A.UI.banner,'RightButton');assert(not A.UI.banner:IsShown()and not A.UI.tooltip:IsShown())
        A.Command('last');assert(A.UI.banner:IsShown()and A.UI.name:GetText()=='A Rare')
        assert(#MOCK.marks==0 and MOCK.forbidden==0)
        ''')

    def test_native_options_commands_and_position_are_available(self):
        vm=create_vm()
        vm.execute('''
        local c=MOCK.categories.ElmoRare;assert(c.registered)
        A.Command('');assert(MOCK.openCategory=='ElmoRare')
        local p=c.panel;p.scripts.OnShow();assert(p.enabled:GetChecked()and p.sound:GetChecked()and p.popup:GetChecked())
        p.sound:SetChecked(false);p.sound.scripts.OnClick(p.sound);assert(not A.db.sound)
        p.test.scripts.OnClick();assert(A.UI.banner:IsShown()and #MOCK.sounds==0)
        A.UI.banner:SetPoint('TOPLEFT',UIParent,'TOPLEFT',20,-30)
        A.UI.banner.scripts.OnDragStop(A.UI.banner)
        assert(A.db.position.x==20 and A.db.position.y==-30)
        p.reset.scripts.OnClick();assert(A.db.position==nil and A.UI.banner.point[1]=='TOP')
        A.Settings.Register();assert(SlashCmdList.ELMORARE==A.Command)
        ''')

    def test_secure_marker_is_static_separate_and_requires_user_input(self):
        vm=create_vm()
        vm.execute('''
        local b=A.UI.marker;assert(b and b.parent==UIParent and b.parent~=A.UI.banner)
        assert(b.attributes.type=='raidtarget'and b.attributes.unit=='target'and b.attributes.marker==8)
        assert(b.attributes.action=='set'and b.attributes.useOnKeyDown==true and b.mouse==false)
        assert(b.scripts.OnClick and b.point[2]==UIParent)
        local writes=MOCK.attributeWrites
        MOCK.combat=true;local rare=MOCK.mob('nameplate1',14)
        A.Command('test');A.Scan();MOCK.tick(.5);assert(#MOCK.marks==0 and MOCK.attributeWrites==writes)
        MOCK.units.target=rare;MOCK.press();assert(#MOCK.marks==1 and rare.marker==8)
        MOCK.press();assert(#MOCK.marks==1,'Set action must not toggle the skull off')
        local other=MOCK.mob('target',99);MOCK.press();assert(MOCK.marks[2]==other.guid)
        MOCK.permission=false;MOCK.mob('target',100);MOCK.press();assert(#MOCK.marks==2)
        assert(MOCK.forbidden==0 and MOCK.attributeWrites==writes)
        ''')

    def test_secure_marker_creation_is_deferred_during_combat_and_optional_when_unsupported(self):
        vm=create_vm('MOCK.combat=true')
        vm.execute('''
        assert(not A.UI.marker and MOCK.attributeWrites==0)
        MOCK.mob('nameplate1',11);assert(#MOCK.sounds==1)
        MOCK.combat=false;MOCK.event('PLAYER_REGEN_ENABLED');assert(A.UI.marker)
        local n=MOCK.attributeWrites;MOCK.event('PLAYER_REGEN_ENABLED');assert(MOCK.attributeWrites==n)
        ''')
        vm=create_vm('SECURE_ACTIONS=nil')
        vm.execute("MOCK.mob('nameplate1',12);assert(#MOCK.sounds==1 and not A.UI.marker)")

    def test_binding_has_one_implicit_load_path_and_searchable_label(self):
        vm=create_vm()
        bindings=ET.parse(ADDON/'Bindings.xml').getroot().findall('Binding')
        self.assertEqual(len(bindings),1)
        self.assertEqual(bindings[0].attrib,{'name':'CLICK ElmoRareMarkTargetButton:LeftButton','category':'ElmoRare'})
        self.assertNotIn('Bindings.xml',(ADDON/'ElmoRare.toc').read_text().splitlines())
        label=vm.globals()['BINDING_NAME_'+bindings[0].attrib['name']]
        self.assertIn('ElmoRare',label)
        self.assertIn('current target',label)

    def test_initial_discovery_ignores_private_and_forbidden_plate_data(self):
        vm=create_vm("local p=MOCK.mob('nameplate1',12,nil,nil,nil,true);MOCK.plates.nameplate1.forbidden=true")
        vm.execute('''
        assert(#MOCK.sounds==0)
        MOCK.plateList=MOCK.secret();A.Discover();assert(#MOCK.sounds==0)
        MOCK.plateList={};MOCK.unreadableTable=MOCK.plateList;A.Discover();assert(#MOCK.sounds==0)
        assert(MOCK.forbidden==0)
        ''')

    def test_saved_preferences_and_late_loads_are_idempotent(self):
        vm=create_vm(saved={'enabled':False,'sound':'invalid','popup':False,
            'position':{'point':'TOPLEFT','relativePoint':'TOPLEFT','x':23,'y':-40}})
        vm.execute('''
        assert(not A.db.enabled and A.db.sound==true and A.db.popup==false)
        assert(A.UI.banner.point[1]=='TOPLEFT'and A.UI.banner.point[4]==23)
        local frames=#MOCK.frames;MOCK.event('ADDON_LOADED','ElmoRare');assert(#MOCK.frames==frames)
        assert(not next(A.seen)and not A.last and ElmoRareDB==A.db)
        ''')


if __name__=='__main__':unittest.main()
