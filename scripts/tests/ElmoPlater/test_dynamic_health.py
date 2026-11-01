from fixture import create_vm
vm,A=create_vm()
vm.execute(r'''
C_Spell={GetSpellInfo=function(id)if id==772 then return {name='Rend',spellID=id,iconID=id} end end,
 IsSpellUsable=function()return not MOCK.noPower,MOCK.noPower==true end,
 GetSpellCooldown=function()return {startTime=0,duration=0,isEnabled=true}end}
IsPlayerSpell=function(id)return id==772 end
ElmoPlaterDB={ruleSchema=1,rules={{spellID=772,auraID=772,enabled=true,aoe=false,
 minEnemies=1,minMissing=1,minHealth=0,maxHealth=100,refresh=0,preferCovered=true,
 conditions={{metric='enemies',op='>=',value=1,join='AND',opens=0,closes=0,spellID=0}}}}}
MOCK.start()
assert(#A.db.rules==3)
assert(A.db.rules[1].kind=='health_below' and A.db.rules[1].threshold==20)
assert(A.db.rules[2].kind=='debuff' and A.db.rules[2].spellID==772 and #A.db.rules[2].conditions==1)
assert(A.db.rules[3].kind=='lowest_health' and A.db.ruleSchema==2)
A.Rules.Initialize();assert(#A.db.rules==3,'Migration duplicated health rules')
local a=MOCK.mob('nameplate1','Creature-a','A')
local b=MOCK.mob('nameplate2','Creature-b','B')
local c=MOCK.mob('nameplate3','Creature-c','Untouched')
a.health=10;b.health=50;c.health=1
local aura=MOCK.aura('nameplate1',772,20);aura.name='Rend';MOCK.event('UNIT_AURA','nameplate1')
MOCK.hit('nameplate1');MOCK.hit('nameplate2')
local function chosen(unit,index)
 A.Update(false)
 if not unit then assert(A.priorityTarget==nil,'Hidden priority was applied');return end
 assert(A.priorityTarget==A.units[unit],'Wrong dynamic priority target')
 assert(A.priorityTarget.suggestedRule==index,'Wrong first matching rule')
end
chosen('nameplate1',1)
-- A rule above the health rule wins, even when its mob is above 20% HP.
A.Rules.Move(2,-1);chosen('nameplate2',1)
-- Disabled / deleted health rules do not survive as implicit priorities.
MOCK.noPower=true;A.db.rules[2].enabled=false;chosen('nameplate1',3)
A.db.rules[3].enabled=false;chosen(nil)
A.db.rules={};chosen(nil)
A.Rules.Initialize();assert(#A.db.rules==0,'Deleted rules were recreated after schema migration')
-- Strict boundary, editable threshold, ordinary conditions and minimum mob limits.
A.Rules.Add('health_below');a.health=20;chosen(nil)
A.db.rules[1].threshold=30;chosen('nameplate1',1)
A.db.rules[1].minEnemies=3;chosen(nil)
A.db.rules[1].minEnemies=1
A.db.rules[1].conditions=assert(A.Conditions.Validate({{metric='health',op='<',value=15,join='AND',opens=0,closes=0,spellID=0}}))
chosen(nil);a.health=10;chosen('nameplate1',1)
A.db.rules[1].enabled=false;chosen(nil)
-- An explicit lowest-HP rule compares absolute remaining HP, only among attacked mobs.
A.Rules.Add('lowest_health');a.health=30;a.maxHealth=1000;b.health=25;b.maxHealth=100
chosen('nameplate2',2)
-- Equal HP has stable GUID ties; percentage is not a hidden ordering criterion.
a.health=25;chosen('nameplate1',2)
-- An explicit aura condition is supported on health rules without a cast requirement.
A.db.rules[2].conditions=assert(A.Conditions.Validate({{metric='aura',op='==',value=1,join='AND',opens=0,closes=0,spellID=772}}))
chosen('nameplate1',2)
A.db.rules[2].conditions[1].spellID=0;chosen(nil) -- no implicit spell for a health rule
A.db.rules[2].conditions={}
local oldReady=A.Spells.Ready
A.Spells.Ready=function()error('Health rule checked cast readiness')end
chosen('nameplate1',2);A.Spells.Ready=oldReady
-- Health priority does not need readable auras, but does need readable identity/HP.
A.units.nameplate1.aurasKnown=false;chosen('nameplate1',2)
local secret={};issecretvalue=function(v)return v==secret end
local oldHealth=UnitHealth
UnitHealth=function(unit)if unit=='nameplate1' then return secret end;return oldHealth(unit)end
chosen('nameplate2',2);UnitHealth=oldHealth
-- UI offers both health rules even with no learned debuffs or saved rules.
A.Clear();A.db.rules={};A.db.learnedDebuffs={};A.Command('')
local U=A.Settings;assert(#U.NewOptions()==2)
U.addSpell:GetScript('OnClick')(U.addSpell)
A.Dropdown.popup.rows[1]:GetScript('OnClick')(A.Dropdown.popup.rows[1])
U.addButton:GetScript('OnClick')(U.addButton)
assert(A.db.rules[1].kind=='health_below' and U.fields.threshold:IsShown())
assert(not U.fields.spellID:IsShown() and not U.fields.auraID:IsShown() and not U.fields.minMissing:IsShown())
U.fields.threshold:SetValue(40);U.Save();assert(A.db.rules[1].threshold==40)
A.ConditionEditor.Open();local E=A.ConditionEditor
E.draft.conditions={{metric='enemies',op='>=',value=2,join='AND',opens=0,closes=0,spellID=0}}
E.Refresh();assert(E.Save())
U.Duplicate();assert(#A.db.rules==2 and A.db.rules[1].conditions~=A.db.rules[2].conditions)
U.fields.kind:SetValue('lowest_health');U.fields.kind.changed();U.Save()
assert(A.db.rules[2].kind=='lowest_health' and not U.fields.threshold:IsShown())
U.Move(-1);assert(A.db.rules[1].kind=='lowest_health')
U.Remove();assert(#A.db.rules==1 and A.db.rules[1].kind=='health_below')
-- A deliberately empty v1 list must not resurrect its old legacy watch setting.
local saved=A.db
A.db={ruleSchema=1,rules={},learnedDebuffs={},watchDebuff='Rend'}
A.Rules.Initialize();assert(#A.db.rules==2 and A.db.rules[2].kind=='lowest_health')
A.db=saved
assert(MOCK.restrictedReads==0 and MOCK.foreignWrites==0 and MOCK.hookAttempts==0)
''')
print('Dynamic health checks passed: one-time migration, rule order, strict/editable threshold, disable/delete/no fallback, conditions, attacked-only absolute HP, resource-independent health and manager controls.')
