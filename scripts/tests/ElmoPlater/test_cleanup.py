"""Retire old configuration while preserving nameplate display preferences."""
from pathlib import Path
from fixture import create_vm
import os

vm, _ = create_vm()
vm.execute('''
ElmoPlaterDB={rules={{kind='lowest_health'}},ruleSchema=2,watchDebuff='Rend',
    learnedDebuffs={[772]={id=772,name='Rend'}},questKills=false,plateAuraSize=30}
local saved=ElmoPlaterDB
MOCK.start()
assert(A.db==saved and not A.db.questKills and A.db.plateAuraSize==30)
assert(A.db.rules==nil and A.db.ruleSchema==nil and A.db.watchDebuff==nil and A.db.learnedDebuffs==nil)
local mob,plate=MOCK.mob('nameplate1','Creature-cleanup','Enemy')
local record=A.units.nameplate1
assert(record.frame:IsShown()and record.frame.bar.value==1)
local _,_,_,height=MOCK.worldRect(record.frame)
mob.health=10;MOCK.units.target=mob;MOCK.event('PLAYER_TARGET_CHANGED')
local _,_,_,selectedHeight=MOCK.worldRect(record.frame)
assert(height==selectedHeight and record.borderSize==2)
MOCK.units.target=nil;MOCK.event('PLAYER_TARGET_CHANGED');assert(record.borderSize==1)
A.Initialize();assert(A.db==saved and A.db.rules==nil)
''')

addon=Path(os.environ.get('ELMO_TEST_ADDON',Path(__file__).resolve().parents[3]/'ElmoPlater'))
retired={'Rules.lua','Conditions.lua','ConditionEditor.lua','Dropdown.lua','Spells.lua'}
manifest=(addon/'ElmoPlater.toc').read_text()
for name in retired:
    assert name not in manifest and not (addon/name).exists(), name
print('Cleanup checks passed: obsolete settings/modules removed, display preferences and selected-target border preserved.')
