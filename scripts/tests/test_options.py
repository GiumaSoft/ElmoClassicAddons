"""Exercise actual addon settings callbacks with native Settings API fixtures."""
import ast
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import unittest

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
ADDONS = ("ElmoLeveling", "ElmoPlater", "ElmoSpellTracker", "ElmoLFG", "ElmoQuestEnhanced")
CLIENT_ROOT = Path(os.environ.get("ELMO_TEST_ROOT", ROOT))
SETTINGS = r'''
optionsCategories={}
local originalCreateFrame=CreateFrame
function CreateFrame(kind,...)
 local f=originalCreateFrame(kind,...)
 if kind=='CheckButton' then
  function f:SetChecked(value)self.checked=value==true end
  function f:GetChecked()return self.checked end
 end
 return f
end
SettingsPanel=CreateFrame('Frame')
function HideUIPanel(panel)panel:Hide()end
Settings={VarType={Boolean='boolean'}}
function Settings.RegisterCanvasLayoutCategory(panel,name)
 assert(not optionsCategories[name],'Duplicate category '..name)
 local category={panel=panel,name=name}
 function category:GetID()return self.name end
 optionsCategories[name]=category;return category
end
function Settings.RegisterVerticalLayoutCategory(name)
 local category=Settings.RegisterCanvasLayoutCategory(CreateFrame('Frame'),name)
 category.vertical=true;return category
end
function Settings.RegisterAddOnCategory(category)category.addon=true end
function Settings.RegisterAddOnSetting(category,variable,key,db,kind,label,default)
 local setting={db=db,key=key}
 function setting:SetValue(value)self.db[self.key]=value end
 function setting:GetValue()return self.db[self.key]end
 return setting
end
function Settings.CreateCheckbox()end
function Settings.OpenToCategory(id)openedCategory=id end
function optionsClick(button)
 local fn=assert(button:GetScript('OnClick'),'Missing options action');fn(button)
end
function optionsShow(name)
 local category=assert(optionsCategories[name],'Missing category '..name)
 assert(category.addon,'Category is not in Options > AddOns')
 Settings.OpenToCategory(category:GetID())
 if not category.vertical then
  category.panel:Show()
  local show=category.panel:GetScript('OnShow');if show then show(category.panel)end
 end
 return category.panel
end
'''


def lua_literal(path, name):
    for item in ast.parse(path.read_text()).body:
        if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in item.targets):
            return ast.literal_eval(item.value)
    raise AssertionError(name)


@contextmanager
def fixture_environment(addon, forever):
    previous = {key: os.environ.get(key) for key in ('ELMO_TEST_ADDON', 'ELMO_TEST_FOREVER')}
    os.environ['ELMO_TEST_ADDON'] = str(CLIENT_ROOT / addon)
    os.environ.pop('ELMO_TEST_FOREVER', None)
    if forever:
        os.environ['ELMO_TEST_FOREVER'] = '1'
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_addon(addon, forever):
    if addon == 'ElmoPlater':
        spec = importlib.util.spec_from_file_location('plater_options_fixture', HERE / 'ElmoPlater/fixture.py')
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        with fixture_environment(addon, forever):
            vm, _ = fixture.create_vm()
        vm.execute(SETTINGS)
        vm.execute('MOCK.start()')
        return vm
    vm = LuaRuntime(unpack_returned_tuples=True)
    if addon == 'ElmoLeveling':
        vm.execute((HERE / 'leveling_forever/wow_mock.lua').read_text())
        if forever:
            vm.execute('MOCK.forever()')
    elif addon == 'ElmoSpellTracker':
        vm.execute((HERE / 'ElmoSpellTracker/wow_mock.lua').read_text())
    elif addon == 'ElmoLFG':
        vm.execute(lua_literal(HERE / 'ElmoLFG/test_core.py', 'WOW_STUB'))
        vm.execute(lua_literal(HERE / 'ElmoLFG/test_ui.py', 'FRAMES'))
    else:
        vm.execute(lua_literal(HERE / 'ElmoQuestEnhanced/test_addon.py', 'STUB'))
    vm.execute(SETTINGS)
    ns = vm.table()
    vm.globals().A = ns
    loader = vm.eval('function(s,n,name,ns)assert(loadstring(s,"@"..n))(name,ns)end')
    source = CLIENT_ROOT / addon
    names = ('Data.lua', 'Core.lua', 'Roles.lua', 'Theme.lua', 'UI.lua') if addon == 'ElmoLFG' else (
        line for line in (source / (addon + '.toc')).read_text().splitlines() if line.endswith('.lua'))
    for name in names:
        loader((source / name).read_text(), name, addon, ns)
    if addon == 'ElmoLeveling':
        ns.flavor = 'forever' if forever else 'classic'
        vm.execute('MOCK.start()')
    elif addon == 'ElmoSpellTracker':
        vm.execute('MOCK.start()')
    else:
        vm.execute("fire('ADDON_LOADED','" + addon + "')")
    return vm


class OptionsTests(unittest.TestCase):
    def test_addons_have_exactly_one_addons_category(self):
        for forever in (False, True):
            for addon in ADDONS:
                with self.subTest(client='forever' if forever else 'classic', addon=addon):
                    vm = load_addon(addon, forever)
                    vm.execute("optionsShow('" + addon + "')")
                    vm.execute('local n=0;for _ in pairs(optionsCategories)do n=n+1 end;assert(n==1)')
                    if addon == 'ElmoLFG':
                        vm.execute('assert(not A.announcing and #sent==0 and #invited==0)')
                    elif addon == 'ElmoQuestEnhanced':
                        vm.execute('assert(#sent==0)')

    def test_leveling_controls_apply_to_existing_state(self):
        for forever in (False, True):
            vm = load_addon('ElmoLeveling', forever)
            vm.execute('''local p=optionsShow('ElmoLeveling')
            p.visible:SetChecked(false);optionsClick(p.visible);assert(A.db.hidden and not A.UI.panel:IsShown())
            optionsClick(p.center);assert(not A.db.hidden and A.UI.panel:IsShown() and A.db.position==nil and p.visible:GetChecked())
            p.locked:SetChecked(true);optionsClick(p.locked);assert(A.db.locked)
            p.expanded:SetChecked(true);optionsClick(p.expanded);assert(A.db.mobExpanded)
            A.db.xp=123;optionsClick(p.clear);assert(A.db.xp==123 and #A.db.kills==0)
            optionsClick(p.reset);assert(A.db.xp==0)
            A.Command('unlock');p=optionsShow('ElmoLeveling');assert(not p.locked:GetChecked())''')

    def test_plater_knife_icon_size_and_native_options(self):
        for forever in (False, True):
            vm = load_addon('ElmoPlater', forever)
            vm.execute('''local p=optionsShow('ElmoPlater')
            p.questKills:SetChecked(false);optionsClick(p.questKills);assert(not A.db.questKills)
            A.Command('questkills on');p=optionsShow('ElmoPlater');assert(p.questKills:GetChecked())
            p.auraSize:SetText('30');optionsClick(p.apply);assert(A.db.plateAuraSize==30)
            p.auraSize:SetText('99');optionsClick(p.apply);assert(A.db.plateAuraSize==30 and p.auraSize:GetText()=='30')
            assert(p.showMana:GetChecked() and p.showCast:GetChecked())
            p.showMana:SetChecked(false);optionsClick(p.showMana);assert(not A.db.showMana)
            p.showCast:SetChecked(false);optionsClick(p.showCast);assert(not A.db.showCast)
            p=optionsShow('ElmoPlater');assert(not p.showMana:GetChecked() and not p.showCast:GetChecked())
            p.showMana:SetChecked(true);optionsClick(p.showMana);assert(A.db.showMana)
            p.showCast:SetChecked(true);optionsClick(p.showCast);assert(A.db.showCast)
            assert(p.healthTest==nil and p.open==nil and A.Rules==nil)
            A.Command('');assert(openedCategory==A.Settings.optionsCategory:GetID())''')

    def test_spell_tracker_capacity_lock_removal_clear_and_editor(self):
        for forever in (False, True):
            vm = load_addon('ElmoSpellTracker', forever)
            vm.execute('''local p=optionsShow('ElmoSpellTracker')
            p.locked:SetChecked(true);optionsClick(p.locked);assert(A.db.locked)
            p.limit:SetText('12');optionsClick(p.apply);assert(A.db.maxSkills==12)
            p.limit:SetText('99');optionsClick(p.apply);assert(A.db.maxSkills==12 and p.limit:GetText()=='12')
            MOCK.spell(100);MOCK.cooldown(100,8);MOCK.cast(100);MOCK.advance(.1)
            assert(#A.db.spells==1);p.removeIndex:SetText('1');optionsClick(p.remove);assert(#A.db.spells==0)
            MOCK.cast(100);MOCK.advance(.1);optionsClick(p.clear);assert(#A.db.spells==0)
            optionsClick(p.open);assert(A.UI.settings:IsShown() and not SettingsPanel:IsShown())
            A.Command('unlock');p=optionsShow('ElmoSpellTracker');assert(not p.locked:GetChecked())''')

    def test_lfg_opens_all_settings_without_starting_recruitment(self):
        for forever in (False, True):
            vm = load_addon('ElmoLFG', forever)
            vm.execute('''local p=optionsShow('ElmoLFG')
            p.autoJoin:SetChecked(false);optionsClick(p.autoJoin)
            assert(not A.db.autoJoin and not ElmoLFGFrame.autoJoin:GetChecked())
            optionsClick(p.open);assert(ElmoLFGFrame:IsShown() and not SettingsPanel:IsShown())
            optionsClick(p.open);assert(ElmoLFGFrame:IsShown())
            assert(not A.announcing and #sent==0 and #invited==0)''')



if __name__ == '__main__':
    unittest.main()
