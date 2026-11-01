from pathlib import Path
from lupa.lua51 import LuaRuntime
P=Path(__file__).resolve().parents[2]
cases=[('ElmoLeveling','ClassicLeveling','classic'),('ElmoLeveling','ClassicLevelingForever','forever'),('ElmoPlater','ClassicPlater',None),('ElmoDungeonLoot','ClassicDungeon',None),('ElmoSpellTracker','ClassicSpellsTracker',None)]
for new,old,flavor in cases:
 for existing in [False,True]:
  vm=LuaRuntime(unpack_returned_tuples=True);ns=vm.table();ns.flavor=flavor
  vm.execute(old+'DB={xp=123,customMessage="keep",marker="old"}; old='+old+'DB')
  if existing:vm.execute(new+'DB={marker="new"}; current='+new+'DB')
  vm.eval('function(s,ns) assert(loadstring(s))("Test",ns) end')((P/new/'Migration.lua').read_text(),ns)
  ns.MigrateSettings();vm.globals().result=vm.globals()[new+'DB']
  vm.execute('assert(result=='+('current and result.marker=="new"' if existing else 'old and result.customMessage=="keep"')+')')
  ns.MigrateSettings()
  vm.execute('assert(result=='+new+'DB)')
print('10 old/new profile precedence and idempotent migration checks passed (simulated SavedVariables).')
