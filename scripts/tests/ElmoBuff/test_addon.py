"""Run real addon Lua 5.1 with explicit aura, native-frame and secure-click mocks."""
from pathlib import Path
import os
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[3]
ADDON = Path(os.environ.get('ELMO_TEST_ADDON', ROOT / 'ElmoBuff'))
STUB = r'''
MOCK={time=100,frames={},units={},spells={},book={},categories={},messages={},casts={},
 combat=false,secure=false,hardware=false,auraCalls=0,writes=0,target='enemy'}
SlashCmdList={};STANDARD_TEXT_FONT='Fonts/FRIZQT__.TTF';BOOKTYPE_SPELL='spell'
Enum={SpellBookSpellBank={Player=0}}
local methods={}
local function mutable(f)
 assert(not f.native,'Native frames must remain untouched')
 assert(not(f.protected and MOCK.combat and not MOCK.secure),'Protected mutation in combat')
end
function methods:SetSize(w,h)mutable(self);self.width,self.height=w,h end
function methods:SetWidth(w)self.width=w end
function methods:SetFont(path,size,flags)self.font,self.fontSize=path,size end
function methods:SetTextColor(...)self.color={...}end
function methods:SetPoint(...)mutable(self);self.point={...}end
function methods:ClearAllPoints()mutable(self);self.point=nil end
function methods:SetAllPoints()end
function methods:SetFrameStrata(v)self.strata=v end
function methods:SetJustifyH()end
function methods:SetAutoFocus()end
function methods:SetNumeric()end
function methods:SetMaxLetters()end
function methods:SetBackdrop()end
function methods:SetBackdropColor(...)self.background={...}end
function methods:SetBackdropBorderColor(...)self.border={...}end
function methods:SetTexCoord()end
function methods:SetColorTexture(...)self.color={...}end
function methods:SetDesaturated(v)self.desaturated=v end
function methods:SetTexture(v)self.texture=v end
function methods:SetScript(k,v)
 assert(not(self.secureButton and k=='OnClick'),'Replacing native secure OnClick')
 self.scripts[k]=v
end
function methods:GetScript(k)return self.scripts[k]end
function methods:RegisterForClicks(...)self.clicks={...}end
function methods:SetAttribute(k,v)
 mutable(self);self.attributes[k]=v;MOCK.writes=MOCK.writes+1
end
function methods:GetAttribute(k)return self.attributes[k]end
function methods:Click()error('Synthetic click forbidden')end
function methods:SetText(v)self.text=tostring(v)end
function methods:GetText()return self.text or ''end
function methods:Show()mutable(self);self.shown=true end
function methods:Hide()
 mutable(self);local was=self.shown;self.shown=false
 if was and self.scripts.OnHide then self.scripts.OnHide(self)end
end
function methods:SetShown(v)if v then self:Show()else self:Hide()end end
function methods:IsShown()return self.shown end
function methods:IsVisible()return self.shown and(not self.parent or self.parent:IsVisible())end
function methods:IsForbidden()return self.forbidden==true end
function methods:SetChecked(v)self.checked=v==true end
function methods:GetChecked()return self.checked end
function methods:CreateFontString()return CreateFrame('FontString',nil,self)end
function methods:CreateTexture()return CreateFrame('Texture',nil,self)end
function methods:SetOwner(owner,anchor)self.owner,self.anchor=owner,anchor end
function methods:GetOwner()return self.owner end
function methods:ClearLines()self.lines={}end
function methods:AddLine(line)self.lines=self.lines or {};self.lines[#self.lines+1]=line end
function methods:RegisterEvent(event)
 assert(event~='COMBAT_LOG_EVENT_UNFILTERED');self.events[event]=true;return true
end
function CreateFrame(kind,name,parent,template)
 local f=setmetatable({kind=kind,name=name,parent=parent,template=template,scripts={},events={},
  attributes={},drivers={},shown=true},{__index=methods})
 f.protected=template and template:find('Secure',1,true)~=nil or false
 f.secureButton=template and template:find('SecureActionButtonTemplate',1,true)~=nil or false
 if f.secureButton then
  f.scripts.OnClick=function(self,button,down)
   assert(MOCK.hardware,'Template needs a hardware event')
   if not down or not self:IsVisible()or self.attributes.type~='spell'then return end
   MOCK.casts[#MOCK.casts+1]={spell=self.attributes.spell,unit=self.attributes.unit}
  end
 end
 MOCK.frames[#MOCK.frames+1]=f;if name then _G[name]=f end;return f
end
UIParent=CreateFrame('Frame')
PlayerFrame=CreateFrame('Frame','PlayerFrame',UIParent);PlayerFrame.native=true
PartyFrame=CreateFrame('Frame','PartyFrame',UIParent);PartyFrame.native=true
for i=1,4 do
 local f=CreateFrame('Frame','PartyMemberFrame'..i,PartyFrame)
 f.native=true;PartyFrame['MemberFrame'..i]=f
end
function PartyFrame:GetPartyMemberFrame(i)return self['MemberFrame'..i]end
DEFAULT_CHAT_FRAME={AddMessage=function(_,v)MOCK.messages[#MOCK.messages+1]=v end}
function GetTime()return MOCK.time end
function InCombatLockdown()return MOCK.combat end
function IsInRaid()return MOCK.raid==true end
local secrets={}
function MOCK.secret()
 local v=setmetatable({},{__tostring=function()error('Private tostring')end,
  __index=function()error('Private traversal')end,__lt=function()error('Private comparison')end,
  __add=function()error('Private arithmetic')end})
 secrets[v]=true;return v
end
function issecretvalue(v)return rawget(secrets,v)==true end
function canaccessvalue(v)return not issecretvalue(v)end
function canaccesstable(v)return v~=MOCK.unreadable end
local function field(u,k,fallback)local d=MOCK.units[u];if d then return d[k]end;return fallback end
function UnitExists(u)return field(u,'exists',false)end
function UnitClass(u)return field(u,'class'),field(u,'class')end
function UnitName(u)return field(u,'name')end
function UnitLevel(u)return field(u,'level')end
function UnitIsConnected(u)return field(u,'connected',false)end
function UnitIsDeadOrGhost(u)return field(u,'dead',false)end
function UnitCanAssist(_,u)return field(u,'assist',false)end
function MOCK.member(u,name,class,level)
 MOCK.units[u]={exists=true,connected=true,dead=false,assist=true,name=name or u,
  class=class or'PRIEST',level=level or 60,auras={},range=true}
 return MOCK.units[u]
end
function MOCK.learn(id,name,rank,level,unknown)
 MOCK.spells[id]={name=name,iconID=id,rank=rank,level=level,known=not unknown}
 MOCK.book[#MOCK.book+1]=id
end
function MOCK.alias(id,name)MOCK.spells[id]={name=name,iconID=id}end
MOCK.member('player','Cedric','PRIEST',60)
MOCK.member('party1','Joey','WARRIOR',60)
MOCK.learn(1243,'Power Word: Fortitude',1,1)
MOCK.learn(1244,'Power Word: Fortitude',2,12)
MOCK.learn(1245,'Power Word: Fortitude',3,24)
MOCK.learn(2791,'Power Word: Fortitude',4,36)
MOCK.alias(21562,'Prayer of Fortitude')
C_Spell={GetSpellInfo=function(id)return MOCK.spells[id]end,
 GetSpellLevelLearned=function(id)return MOCK.spells[id]and MOCK.spells[id].level end,
 IsSpellInRange=function(id,u)return field(u,'range')end}
C_SpellBook={GetNumSpellBookSkillLines=function()return 1 end,
 GetSpellBookSkillLineInfo=function()return {itemIndexOffset=0,numSpellBookItems=#MOCK.book}end,
 GetSpellBookItemInfo=function(i)
  local id=MOCK.book[i];return id and{spellID=id,isPassive=false}end,
 GetSpellBookItemName=function(i)local s=MOCK.spells[MOCK.book[i]];return s.name,'Rank '..s.rank end,
 GetSpellBookItemLevelLearned=function(i)return MOCK.spells[MOCK.book[i]].level end,
 IsSpellKnown=function(id)return MOCK.spells[id]and MOCK.spells[id].known or false end}
function MOCK.aura(u,name,remaining,id,source)
 if not id then
  for i=#MOCK.book,1,-1 do
   local candidate=MOCK.book[i]
   if MOCK.spells[candidate].name==name and MOCK.spells[candidate].known then id=candidate;break end
  end
 end
 local d=MOCK.units[u];d.auras[#d.auras+1]={name=name,spellId=id,sourceUnit=source or'player',
  expirationTime=remaining and MOCK.time+remaining or 0}
end
C_Secrets={ShouldAurasBeSecret=function()return MOCK.secretAuras==true end}
C_UnitAuras={GetUnitAuras=function(u,filter,max)
 assert(not MOCK.combat,'Aura query in combat');assert(filter=='HELPFUL'and max==255)
 MOCK.auraCalls=MOCK.auraCalls+1
 if MOCK.auraError then error('Aura access unavailable')end
 return field(u,'auras')
end}
Settings={RegisterCanvasLayoutCategory=function(panel,name)
 assert(not MOCK.categories[name]);local c={panel=panel,name=name}
 function c:GetID()return self.name end;MOCK.categories[name]=c;return c
end,RegisterAddOnCategory=function(c)c.registered=true end,
 OpenToCategory=function(id)MOCK.openCategory=id end}
local function driver(f,key)
 MOCK.secure=true
 if key=='visibility'then f:SetShown(not MOCK.combat and not MOCK.raid)
 else
  local source=assert(f:GetAttribute('_onstate-'..key))
  assert(loadstring('return function(self,newstate)'..source..' end'))()(f,MOCK.combat and'1'or'0')
 end
 MOCK.secure=false
end
function RegisterStateDriver(f,key,condition)
 assert(not MOCK.combat);f.drivers[key]=condition;driver(f,key)
end
function MOCK.event(event,...)
 for _,f in ipairs(MOCK.frames)do
  if f.events[event]and f.scripts.OnEvent then f.scripts.OnEvent(f,event,...)end
 end
end
function MOCK.combatState(value)
 MOCK.combat=value
 for _,f in ipairs(MOCK.frames)do for key in pairs(f.drivers)do driver(f,key)end end
 MOCK.event(value and'PLAYER_REGEN_DISABLED'or'PLAYER_REGEN_ENABLED')
end
function MOCK.tick(delta)
 MOCK.time=MOCK.time+delta
 for _,f in ipairs(MOCK.frames)do if f.scripts.OnUpdate then f.scripts.OnUpdate(f,delta)end end
end
function MOCK.press(b)
 MOCK.hardware=true;b.scripts.OnClick(b,'LeftButton',true);b.scripts.OnClick(b,'LeftButton',false)
 MOCK.hardware=false
end
for _,name in ipairs({'CastSpellByID','CastSpellByName','TargetUnit','SetBinding','SetOverrideBinding',
 'SetCVar','SendChatMessage','hooksecurefunc','UnitHealth','CombatLogGetCurrentEventInfo'})do
 _G[name]=function()error('Forbidden or unsolicited API '..name)end
end
'''


def create_vm(setup='', saved=None):
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute(STUB)
    if saved is not None:
        vm.globals().ElmoBuffDB = vm.table_from(saved, recursive=True)
    if setup:
        vm.execute(setup)
    ns = vm.table()
    load = vm.eval('function(s,n,a)assert(loadstring(s,"@"..n))("ElmoBuff",a)end')
    for name in (ADDON / 'ElmoBuff.toc').read_text().splitlines():
        if name.endswith('.lua'):
            load((ADDON / name).read_text(), name, ns)
    vm.globals().A = ns
    vm.execute("MOCK.event('ADDON_LOADED','ElmoBuff')")
    return vm


class BuffTests(unittest.TestCase):
    def test_foreign_equivalent_or_higher_rank_never_enables_an_unnecessary_cast(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        for _,id in ipairs({2791,10937})do
          MOCK.units.party1.auras={}
          MOCK.aura('party1','Power Word: Fortitude',5,id,'party2')
          A.Update();assert(not b:IsShown()and b.state=='covered'and b.attributes.type==nil)
          MOCK.press(b);assert(#MOCK.casts==0)
        end
        MOCK.tick(6);assert(b:IsVisible()and b.state=='missing')
        MOCK.press(b);assert(#MOCK.casts==1)
        ''')

    def test_group_variant_and_different_own_rank_stay_covered_until_they_expire(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        MOCK.aura('party1','Prayer of Fortitude',15,21564,'player')
        A.Update();assert(not b:IsShown()and b.state=='covered')
        MOCK.units.party1.auras={}
        MOCK.aura('party1','Power Word: Fortitude',15,10938,'player')
        A.Update();assert(not b:IsShown()and b.state=='covered')
        MOCK.units.party1.auras[1].spellId=MOCK.secret()
        A.Update();assert(not b:IsShown()and b.state=='covered')
        MOCK.tick(16);assert(b:IsShown()and b.state=='missing')
        ''')

    def test_multiple_auras_do_not_overwrite_coverage_with_an_expiring_own_buff(self):
        vm = create_vm()
        vm.execute('''
        MOCK.aura('party1','Power Word: Fortitude',900,10938,'party2')
        MOCK.aura('party1','Power Word: Fortitude',10,2791,'player')
        local b=A.UI.groups[2].buttons[1]
        A.Update();assert(not b:IsShown()and b.state=='covered')
        MOCK.units.party1.auras[1].sourceUnit=MOCK.secret()
        A.Update();assert(not b:IsShown()and b.state=='covered')
        MOCK.units.party1.auras={MOCK.units.party1.auras[2]}
        A.Update();assert(b:IsShown()and b.state=='refresh')
        ''')

    def test_click_casts_on_member_without_retargeting_and_only_confirmed_aura_hides(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        assert(b:IsVisible()and b.point[2]==PartyMemberFrame1 and b.attributes.spell==2791)
        assert(#MOCK.casts==0)
        MOCK.press(b);assert(#MOCK.casts==1 and MOCK.casts[1].unit=='party1')
        assert(MOCK.casts[1].spell==2791 and MOCK.target=='enemy'and b:IsVisible())
        MOCK.tick(1);assert(b:IsVisible()and #MOCK.casts==1)
        MOCK.aura('party1','Power Word: Fortitude',1800);MOCK.event('UNIT_AURA','party1')
        assert(not b:IsShown()and b.attributes.type==nil)
        MOCK.tick(1801);assert(b:IsVisible()and b.state=='missing')
        ''')

    def test_active_group_alias_and_refresh_threshold(self):
        vm = create_vm("MOCK.aura('party1','Prayer of Fortitude',1800)")
        vm.execute('''
        local b=A.UI.groups[2].buttons[1];assert(not b:IsShown())
        MOCK.units.party1.auras[1].expirationTime=GetTime()+45;MOCK.tick(.5)
        assert(not b:IsShown()and b.state=='covered'and b.attributes.type==nil)
        MOCK.units.party1.auras={};MOCK.aura('party1','Power Word: Fortitude',45)
        A.Update();assert(b:IsVisible()and b.state=='refresh'and b.label:GetText()=='45s')
        A.db.refresh=0;A.Update();assert(not b:IsShown())
        MOCK.units.party1.auras={};A.Update();assert(b:IsShown()and b.state=='missing')
        ''')

    def test_out_of_range_icon_stays_visible_and_can_retry_after_moving(self):
        vm = create_vm("MOCK.units.party1.range=false")
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        assert(b:IsVisible()and b.attributes.type==nil and b.label:GetText()=='!')
        MOCK.press(b);assert(#MOCK.casts==0)
        b.scripts.OnEnter(b);assert(A.UI.tooltip:IsShown())
        assert(table.concat(A.UI.tooltip.lines,' '):find('Out of range',1,true))
        MOCK.units.party1.range=true;MOCK.tick(.5);MOCK.press(b)
        assert(#MOCK.casts==1 and b:IsVisible())
        MOCK.units.party1.range=nil;A.Update();assert(b.attributes.type=='spell')
        ''')

    def test_rank_selection_ignores_future_spells_and_respects_target_level(self):
        vm = create_vm("""
        MOCK.learn(10937,'Power Word: Fortitude',5,48,true)
        MOCK.units.party1.level=10
        """)
        vm.execute('''
        local b=A.UI.groups[2].buttons[1];assert(b.attributes.spell==1244)
        assert(A.UI.groups[1].buttons[1].attributes.spell==2791)
        MOCK.units.party1.level=MOCK.secret();A.Update();assert(b.attributes.spell==1243)
        MOCK.units.party1.level=60;MOCK.spells[10937].known=true
        MOCK.event('SPELLS_CHANGED');assert(b.attributes.spell==10937)
        ''')

    def test_mana_buffs_exclude_non_mana_classes_and_other_members_update_independently(self):
        vm = create_vm("""
        MOCK.learn(14752,'Divine Spirit',1,30);MOCK.alias(27681,'Prayer of Spirit')
        MOCK.member('party2','Mage','MAGE',60)
        """)
        vm.execute('''
        assert(not A.UI.groups[2].buttons[2]:IsShown())
        local mage=A.UI.groups[3].buttons[2];assert(mage:IsVisible())
        MOCK.aura('party2','Prayer of Spirit',1800);MOCK.event('UNIT_AURA','party2')
        assert(not mage:IsShown()and A.UI.groups[3].buttons[1]:IsVisible())
        ''')

    def test_dead_offline_absent_and_ineligible_members_have_no_buttons(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        for _,key in ipairs({'dead','connected','assist','exists'})do
          local d=MOCK.units.party1;local old=d[key];d[key]=key=='dead';A.Update()
          assert(not b:IsShown()and b.attributes.type==nil);d[key]=old
        end
        A.Update();assert(b:IsVisible())
        ''')

    def test_private_or_failed_aura_reads_are_unknown_and_not_missing(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        MOCK.auraError=true;A.Update();assert(not b:IsShown()and A.counts.unknown>0)
        MOCK.auraError=false
        MOCK.units.party1.auras={{name=MOCK.secret(),expirationTime=0}}
        A.Update();assert(not b:IsShown())
        MOCK.units.party1.auras={{name='Power Word: Fortitude',expirationTime=MOCK.secret()}}
        A.Update();assert(not b:IsShown()and b.state=='active')
        MOCK.units.party1.auras={};MOCK.unreadable=MOCK.units.party1.auras
        A.Update();assert(not b:IsShown()and b.state=='unknown')
        MOCK.unreadable=nil;MOCK.units.party1.auras=MOCK.secret();A.Update();assert(not b:IsShown())
        MOCK.units.party1.auras={};local before=MOCK.auraCalls;MOCK.secretAuras=true;A.Update()
        assert(MOCK.auraCalls==before and not b:IsShown())
        ''')

    def test_partial_private_snapshot_cannot_enable_an_early_refresh(self):
        vm = create_vm()
        vm.execute('''
        MOCK.aura('party1','Power Word: Fortitude',20,2791,'player')
        MOCK.units.party1.auras[2]={name=MOCK.secret(),expirationTime=0}
        A.Update();local b=A.UI.groups[2].buttons[1]
        assert(not b:IsShown()and b.state=='unknown'and b.attributes.type==nil)
        MOCK.units.party1.auras[2]=nil;A.Update();assert(b:IsShown()and b.state=='refresh')
        ''')

    def test_combat_uses_secure_drivers_and_never_probes_or_mutates_from_addon_lua(self):
        vm = create_vm()
        vm.execute('''
        local b=A.UI.groups[2].buttons[1]
        MOCK.combatState(true);assert(not b:IsVisible()and b.attributes.type==nil)
        local reads,writes=MOCK.auraCalls,MOCK.writes
        MOCK.units.party1=MOCK.member('party1','Replacement','PRIEST',10)
        MOCK.event('UNIT_AURA','party1');MOCK.event('GROUP_ROSTER_UPDATE');MOCK.tick(3)
        MOCK.event('SPELLS_CHANGED');assert(A.pending)
        assert(MOCK.auraCalls==reads and MOCK.writes==writes)
        MOCK.press(b);assert(#MOCK.casts==0)
        MOCK.combatState(false)
        assert(b:IsVisible()and b.attributes.spell==1244 and not A.pending)
        MOCK.press(b);assert(MOCK.casts[1].unit=='party1'and MOCK.casts[1].spell==1244)
        ''')

    def test_compact_party_is_bound_by_unit_and_hidden_native_parents_do_not_float_icons(self):
        vm = create_vm("""
        MOCK.member('party2','Mage','MAGE',60)
        CompactPartyFrame=CreateFrame('Frame',nil,UIParent)
        local a=CreateFrame('Frame',nil,CompactPartyFrame);a.unit='party2';a.native=true
        local b=CreateFrame('Frame',nil,CompactPartyFrame);b.unit='party1';b.native=true
        CompactPartyFrame.memberUnitFrames={a,b}
        """)
        vm.execute('''
        assert(A.UI.groups[2].buttons[1].point[2]==CompactPartyFrame.memberUnitFrames[2])
        assert(A.UI.groups[3].buttons[1].point[2]==CompactPartyFrame.memberUnitFrames[1])
        CompactPartyFrame.shown=false;A.Update()
        assert(A.UI.groups[2].buttons[1].point[2]==PartyMemberFrame1)
        PartyFrame.shown=false;A.Update();assert(not A.UI.groups[2].buttons[1]:IsVisible())
        ''')

    def test_legacy_spellbook_and_indexed_or_legacy_aura_fallbacks(self):
        vm = create_vm("""
        C_SpellBook=nil
        function GetNumSpellTabs()return 1 end
        function GetSpellTabInfo()return 'Priest',1,0,#MOCK.book end
        function GetSpellBookItemInfo(i)return 'SPELL',MOCK.book[i]end
        function GetSpellBookItemName(i)local s=MOCK.spells[MOCK.book[i]];return s.name,'Rank '..s.rank end
        C_UnitAuras={GetAuraDataByIndex=function(u,i)return MOCK.units[u].auras[i]end}
        """)
        vm.execute('''
        local b=A.UI.groups[2].buttons[1];assert(b:IsVisible()and b.attributes.spell==2791)
        C_UnitAuras=nil
        function UnitBuff(u,i)
          local a=MOCK.units[u].auras[i]
          if a then return a.name,1,0,nil,1800,a.expirationTime end
        end
        MOCK.aura('party1','Power Word: Fortitude',1800);A.Update();assert(not b:IsShown())
        ''')

    def test_options_and_commands_change_only_owned_icons_and_persist_settings(self):
        vm = create_vm(saved={'size': 39})
        vm.execute('''
        assert(MOCK.categories.ElmoBuff.registered)
        A.Command('');assert(MOCK.openCategory=='ElmoBuff')
        local p=A.Settings.panel;p.scripts.OnShow(p)
        p.size.scripts.OnClick();assert(A.db.size==40)
        p.size.scripts.OnClick();assert(A.db.size==20)
        p.side.scripts.OnClick();assert(A.db.side=='LEFT')
        assert(A.UI.groups[2].buttons[1].point[1]=='RIGHT')
        p.refresh:SetText('0');p.apply.scripts.OnClick();assert(A.db.refresh==0)
        p.buffs[1]:SetChecked(false);p.buffs[1].scripts.OnClick(p.buffs[1])
        assert(not A.UI.groups[2].buttons[1]:IsShown())
        p.buffs[1]:SetChecked(true);p.buffs[1].scripts.OnClick(p.buffs[1])
        p.self:SetChecked(false);p.self.scripts.OnClick(p.self)
        assert(not A.UI.groups[1].buttons[1]:IsShown()and A.UI.groups[2].buttons[1]:IsShown())
        A.Command('off');assert(not A.UI.groups[2].buttons[1]:IsShown())
        A.Command('on');assert(A.UI.groups[2].buttons[1]:IsShown())
        MOCK.combatState(true);p.enabled:SetChecked(false);p.enabled.scripts.OnClick(p.enabled)
        assert(A.db.enabled and p.enabled:GetChecked())
        MOCK.combatState(false);A.Command('status')
        ''')

    def test_paladin_selects_one_learned_blessing_instead_of_replacing_each_other(self):
        vm = create_vm("""
        MOCK.units.player.class='PALADIN';MOCK.book={}
        MOCK.learn(19740,'Blessing of Might',1,4)
        MOCK.learn(19742,'Blessing of Wisdom',1,14)
        MOCK.alias(25782,'Greater Blessing of Might');MOCK.alias(25894,'Greater Blessing of Wisdom')
        """)
        vm.execute('''
        assert(#A.Spells.active==1 and A.Spells.active[1].key=='might')
        A.Settings.panel.blessing.scripts.OnClick()
        assert(A.db.blessing=='wisdom'and #A.Spells.active==1)
        assert(A.UI.groups[2].buttons[1].attributes.spell==19742)
        assert(not A.UI.groups[2].buttons[2]:IsShown())
        MOCK.aura('party1','Greater Blessing of Wisdom',900);A.Update()
        assert(not A.UI.groups[2].buttons[1]:IsShown())
        ''')

    def test_raid_and_unsupported_classes_do_not_produce_rebuff_buttons(self):
        vm = create_vm("MOCK.raid=true")
        vm.execute('''
        assert(not A.UI.groups[2].buttons[1]:IsVisible())
        MOCK.raid=false;MOCK.combatState(false);assert(A.UI.groups[2].buttons[1]:IsVisible())
        MOCK.units.player.class='WARRIOR';MOCK.event('SPELLS_CHANGED')
        assert(#A.Spells.active==0 and not A.UI.groups[2].buttons[1]:IsShown())
        ''')

    def test_loading_in_combat_defers_protected_creation(self):
        vm = create_vm("MOCK.combat=true")
        vm.execute('''
        assert(A.UI.root==nil and MOCK.auraCalls==0)
        MOCK.combatState(false);assert(A.UI.groups[2].buttons[1]:IsVisible())
        ''')

    def test_all_supported_class_families_can_match_localized_names(self):
        for cls, spell_id, group_id, label in [
            ('MAGE', 1459, 23028, 'Intelletto Arcano'),
            ('DRUID', 1126, 21849, 'Marchio Selvaggio'),
        ]:
            with self.subTest(cls=cls):
                vm = create_vm(f"""
                MOCK.units.player.class='{cls}';MOCK.units.party1.class='PRIEST';MOCK.book={{}}
                MOCK.learn({spell_id},'{label}',1,1);MOCK.alias({group_id},'Buff di gruppo')
                """)
                vm.execute('''
                local b=A.UI.groups[2].buttons[1];assert(b:IsVisible())
                MOCK.aura('party1','Buff di gruppo',1800);A.Update();assert(not b:IsShown())
                ''')


if __name__ == '__main__':
    unittest.main()
