"""Exercise the installed or staged dungeon journal using real Lua 5.1 and explicit mocks."""
from pathlib import Path
import argparse
from time import perf_counter
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).parent
parser=argparse.ArgumentParser()
parser.add_argument('--addon',type=Path,default=Path(__file__).resolve().parents[3]/'ElmoDungeonLoot')
args=parser.parse_args()
vm=LuaRuntime(unpack_returned_tuples=True)
messages=[]
vm.globals().print=lambda *args: messages.append(' '.join(map(str,args)))
for file in ['wow_mock.lua','journal_mock.lua']: vm.execute((HERE/file).read_text())
ns=vm.table()
load=vm.eval('function(s,name,ns) assert(loadstring(s,"@"..name))("ElmoDungeonLoot",ns) end')
start=perf_counter()
try:
    for line in (args.addon/'ElmoDungeonLoot.toc').read_text().splitlines():
        if line.endswith('.lua'): load((args.addon/line).read_text(),line,ns)
    vm.globals().CD=ns
    vm.execute((HERE/'tests_journal.lua').read_text())
    if (args.addon/'Search.lua').exists(): vm.execute((HERE/'tests_search.lua').read_text())
except Exception:
    print('\n'.join(messages[-5:]));raise
print('\n'.join(m for m in messages if m.startswith(('JOURNAL','SEARCH'))))
print(f'Lua 5.1 passed in {perf_counter()-start:.2f}s. Client, rendering and tooltip APIs are simulated.')
