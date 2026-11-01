from fixture import create_vm
vm,A=create_vm()
vm.execute(r'''
MOCK.spells={
 [772]={name='Rend',ready=true}, [6343]={name='Thunder Clap',ready=true},
 [999]={name='Other debuff',ready=true},
}
C_Spell={GetSpellInfo=function(id)
 if type(id)=='string' then for key,s in pairs(MOCK.spells)do if s.name==id then id=key;break end end end
 local s=MOCK.spells[id];if s then return {name=s.name,spellID=id,iconID=id} end
end,
IsSpellUsable=function(id)local s=MOCK.spells[id];return s~=nil and not s.noPower,s and s.noPower==true end,
GetSpellCooldown=function(id)
 local s=MOCK.spells[id]
 if id==61304 then return {startTime=MOCK.gcd and MOCK.time-0.2 or 0,duration=MOCK.gcd and 1.5 or 0,isEnabled=true} end
 return {startTime=s and not s.ready and MOCK.time-1 or 0,duration=s and not s.ready and 6 or 0,isEnabled=true}
end}
function IsPlayerSpell(id)return MOCK.spells[id]~=nil end
function UnitAffectingCombat(unit)return MOCK.combat end
function UnitPower(unit,power)return power==1 and 15 or power==0 and 100 or 50 end
MOCK.start()
A.db.rules={} -- this suite explicitly chooses its own dynamic priorities
local a=MOCK.mob('nameplate1','Creature-a','A')
local b=MOCK.mob('nameplate2','Creature-b','B')
local c=MOCK.mob('nameplate3','Creature-c','C')
local untouched=MOCK.mob('nameplate4','Creature-d','Untouched');untouched.health=1
local function effect(unit,id,seconds)
 local aura=MOCK.aura(unit,id,seconds or 20);aura.name=MOCK.spells[id].name
 MOCK.event('UNIT_AURA',unit);return aura
end
local function choose(unit,rule)
 A.Update(false)
 if not unit then assert(A.priorityTarget==nil,'Unexpected implicit priority');return end
 assert(A.priorityTarget==A.units[unit],'Expected priority '..unit)
 assert(A.priorityTarget.suggestedRule==rule,'Wrong rule')
end
MOCK.hit('nameplate1');MOCK.hit('nameplate2');MOCK.hit('nameplate3')
a.health=80;b.health=90;c.health=25
-- Observing abilities only fills the catalog, never creates priority rules.
effect('nameplate1',772);effect('nameplate1',6343);effect('nameplate2',6343)
assert(#A.db.rules==0 and A.db.learnedDebuffs[772] and A.db.learnedDebuffs[6343])
choose(nil)
local thunder=A.Rules.Add(6343);A.db.rules[thunder].aoe=true
A.Rules.Add(772)
A.Rules.Add("lowest_health")
choose('nameplate3',1) -- ready AoE is the first rule
MOCK.spells[6343].ready=false
choose('nameplate2',2) -- Rend prefers partial coverage over untouched lower HP
MOCK.spells[6343].noPower=true;MOCK.spells[772].noPower=true
choose('nameplate3',3) -- no resources -> lowest HP
MOCK.spells[6343].noPower=false;MOCK.spells[772].noPower=false
MOCK.spells[6343].ready=true
A.Rules.Move(1,1);choose('nameplate2',1) -- explicit order overrides AoE metadata
A.Rules.Move(2,-1);MOCK.spells[6343].ready=false
A.db.rules[2].preferCovered=false;choose('nameplate3',2)
A.db.rules[2].preferCovered=true
MOCK.spells[772].ready=false;choose('nameplate3',3)
MOCK.spells[772].ready=true
choose('nameplate2',2);effect('nameplate2',772);choose('nameplate3',2)
-- With no health-threshold rule, a critical mob does not override a matching debuff.
a.health=1;choose('nameplate3',2)
a.health=80;c.health=25
MOCK.units.target=c;MOCK.event('PLAYER_TARGET_CHANGED');choose('nameplate3',2)
-- Limits, refresh thresholds and GCD handling.
A.db.rules[2].minEnemies=4;choose('nameplate3',3) -- untouched mob is not counted
A.db.rules[2].minEnemies=1;A.db.rules[2].minMissing=2;choose('nameplate3',3)
A.db.rules[2].minMissing=1
local rend=effect('nameplate3',772,2)
choose('nameplate3',3)
A.db.rules[2].refresh=3;choose('nameplate3',2)
A.db.rules[2].refresh=0
MOCK.gcd=true
local oldCooldown=C_Spell.GetSpellCooldown
C_Spell.GetSpellCooldown=function(id)
 if id==772 then return oldCooldown(61304) end
 return oldCooldown(id)
end
assert(A.Spells.Ready(772))
C_Spell.GetSpellCooldown=oldCooldown;MOCK.gcd=false
-- Public charges and duration-object API; private values fail closed.
C_Spell.GetSpellCharges=function(id)if id==772 then return {currentCharges=0,maxCharges=2} end end
assert(not A.Spells.Ready(772))
C_Spell.GetSpellCharges=function(id)if id==772 then return {currentCharges=1,maxCharges=2} end end
assert(A.Spells.Ready(772));C_Spell.GetSpellCharges=nil
C_Spell.GetSpellCooldownDuration=function(id,ignore)
 assert(ignore==true);return {GetRemainingDuration=function()return 0 end}
end
assert(A.Spells.Ready(772));C_Spell.GetSpellCooldownDuration=nil
local private={};issecretvalue=function(v)return v==private end
C_Spell.GetSpellCharges=function()return private end
assert(not A.Spells.Ready(772));C_Spell.GetSpellCharges=nil
C_Spell.IsSpellUsable=function()return private,private end
assert(not A.Spells.Ready(772))
-- Restore ordinary spell usability for editor/readiness checks.
C_Spell.IsSpellUsable=function(id)return MOCK.spells[id]~=nil,false end
local C=A.Conditions
local function cond(metric,op,value,join,opens,closes,id)
 return {metric=metric,op=op,value=value,join=join or 'AND',opens=opens or 0,closes=closes or 0,spellID=id or 0}
end
local r=A.db.rules[2];local rec=A.units.nameplate3;local ctx={now=GetTime(),enemies=3,missing=1}
local function match(rows)
 local clean,err=C.Validate(rows);assert(clean,err);return C.Match(clean,rec,r,ctx)
end
assert(match({cond('health_pct','<',30),cond('rage','>=',15)}))
assert(not match({cond('health_pct','<',20),cond('rage','>=',15)}))
assert(match({cond('health_pct','<',20),cond('rage','>=',15,'OR')}))
assert(match({cond('health_pct','<',20),cond('rage','>=',15,'OR'),cond('enemies','>=',3)}))
assert(not match({cond('health_pct','>',20,'AND',1),cond('rage','>',99,'OR',0,1),cond('enemies','>',3)}))
assert(match({cond('aura','==',1,'AND',0,0,772),cond('remaining','<=',3)}))
assert(match({cond('aura','==',0,'AND',0,0,999)}))
assert(not C.Validate({cond('health_pct','<',20,'AND',1)}))
assert(not C.Validate({cond('health_pct','<',20,'AND',0,1)}))
assert(not C.Validate({cond('health_pct','run code',20)}))
local oldPower=UnitPower;UnitPower=function()return private end
assert(not match({cond('rage','~=',0)}));UnitPower=oldPower
rec.aurasKnown=false;assert(not match({cond('aura','==',0)}));rec.aurasKnown=true
-- Conditions are applied by the engine, not only by the standalone evaluator.
c.auras={};MOCK.event('UNIT_AURA','nameplate3')
r.conditions=assert(C.Validate({cond('rage','>',50)}));choose('nameplate3',3)
r.conditions={};choose('nameplate3',2)
-- Settings operate on validated copies; changes persist only on Save.
A.Command('');assert(A.Settings.frame:IsShown())
local U=A.Settings
U.selected=2;U.Refresh()
U.fields.minHealth:SetValue(101);U.Save();assert(A.db.rules[2].minHealth==0)
U.fields.minHealth:SetValue(10);U.Save();assert(A.db.rules[2].minHealth==10)
A.ConditionEditor.Open();local E=A.ConditionEditor
assert(E.frame:IsShown() and #E.draft.conditions==0)
E.draft.conditions={cond('enemies','>=',2)};E.Refresh();assert(E.Save())
assert(A.db.rules[2].conditions[1].value==2)
E.Open();E.draft.conditions[1].value=999;E.frame:Hide()
assert(A.db.rules[2].conditions[1].value==2)
-- Invalid parentheses are rejected without altering saved rules.
E.Open();E.draft.conditions[1].opens=1;E.Refresh();assert(E.Save()==false)
assert(A.db.rules[2].conditions[1].opens==0)
-- The dropdown changes the selected row, including when reused for a different field.
E.rows[1].metric:GetScript('OnClick')(E.rows[1].metric)
A.Dropdown.popup.rows[5]:GetScript('OnClick')(A.Dropdown.popup.rows[5])
assert(E.rows[1].metric.value=='rage')
E.rows[1].op:GetScript('OnClick')(E.rows[1].op)
A.Dropdown.popup.rows[4]:GetScript('OnClick')(A.Dropdown.popup.rows[4])
assert(E.rows[1].op.value=='>=')
-- Main manager dropdowns append independent rules; Save edits only the selected entry.
E.frame:Hide()
local first=A.db.rules[1]
U.addSpell:GetScript('OnClick')(U.addSpell)
local picked=false
for _,row in ipairs(A.Dropdown.popup.rows) do
 if row.item and row.item[1]==6343 then row:GetScript('OnClick')(row);picked=true;break end
end
assert(picked and U.addSpell.value==6343)
U.addButton:GetScript('OnClick')(U.addButton)
U.addButton:GetScript('OnClick')(U.addButton)
assert(#A.db.rules==5 and A.db.rules[1]==first and U.selected==5)
U.fields.enabled:GetScript('OnClick')(U.fields.enabled)
A.Dropdown.popup.rows[2]:GetScript('OnClick')(A.Dropdown.popup.rows[2])
U.saveButton:GetScript('OnClick')(U.saveButton)
assert(A.db.rules[5].enabled==false and U.fields.enabled.value==false)
assert(U.fields.enabled.label:GetText()=='Disabled')
U.duplicateButton:GetScript('OnClick')(U.duplicateButton)
assert(#A.db.rules==6 and A.db.rules[6]~=A.db.rules[5] and A.db.rules[6].enabled==false)
U.Move(-1);assert(U.selected==5);U.Remove();assert(#A.db.rules==5)
for i=1,10 do U.addButton:GetScript('OnClick')(U.addButton) end
assert(#A.db.rules==15 and U.rows[9].index==15 and U.rows[9]:IsShown())
U.rows[1]:GetScript('OnClick')(U.rows[1]);assert(U.selected==7)
-- Numeric options page correctly and preserve their values on Save.
U.fields.maxHealth:GetScript('OnClick')(U.fields.maxHealth)
assert(A.Dropdown.popup:IsShown())
A.Dropdown.popup.previous:GetScript('OnClick')(A.Dropdown.popup.previous)
local id=A.Dropdown.popup.rows[1].item[1]
A.Dropdown.popup.rows[1]:GetScript('OnClick')(A.Dropdown.popup.rows[1])
assert(U.fields.maxHealth.value==id)
-- The cast picker can include learned spells before they are observed as debuffs.
GetNumSpellTabs=function()return 1 end
GetSpellTabInfo=function()return 'Abilities',1,0,2 end
GetSpellBookItemInfo=function(slot)return 'SPELL',slot==1 and 772 or 6343 end
IsPassiveSpell=function()return false end
assert(#A.Spells.Book()==2)
C_SpellBook={GetNumSpellBookSkillLines=function()return 1 end,
 GetSpellBookSkillLineInfo=function()return {itemIndexOffset=0,numSpellBookItems=2}end,
 GetSpellBookItemInfo=function(slot,bank)return {spellID=slot==1 and 772 or 6343,isPassive=slot==2}end}
local book=A.Spells.Book();assert(#book==1 and book[1].id==772)
C_SpellBook.GetSpellBookItemInfo=function()return private end
assert(#A.Spells.Book()==0)
C_SpellBook=nil
-- Legacy named debuff imports once, and same-name spell ranks remain covered.
A.Command('debuff Rend');assert(#A.db.rules==1 and A.db.rules[1].spellID==772)
local higher=MOCK.aura('nameplate3',6546,20);higher.name='Rend';MOCK.event('UNIT_AURA','nameplate3')
assert(not A.Rules.Missing(rec,A.db.rules[1],GetTime()))
A.Command('debuff any');assert(#A.db.rules==0)
A.db.watchDebuff='Rend';A.db.ruleSchema=nil;A.Rules.Initialize();assert(#A.db.rules==3)
A.Rules.Initialize();assert(#A.db.rules==3)
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
''')
print('Rules/editor checks passed: A/B/C debuffs, cooldowns/resources/GCD/charges, strict rule order, dynamic priorities, explicit health fallback, learning, conditions, private data, save/cancel/validation, multiple rules, dropdown paging, spellbook options and migration.')
