from pathlib import Path
import csv
import gzip
import json
import re
import hashlib
from datetime import date
from lupa.lua51 import LuaRuntime

WORKSPACE = Path(__file__).resolve().parents[3]
ROOT = WORKSPACE / '.build/catalog-sources'
OUTPUT = WORKSPACE / 'ElmoDungeonLoot'

SOURCES = {
    'data.lua': ('https://raw.githubusercontent.com/Hoizame/AtlasLootClassic/8e99341e4e779328460bf7684c0d5b22ce50ddf1/AtlasLootClassic_DungeonsAndRaids/data.lua',
                 'ab12de3f642620ff52e5bb0c47139e4146e3c7021be99d55af76e5eae7bda557'),
    'classic-db.sql.gz': ('https://raw.githubusercontent.com/cmangos/classic-db/603ece109099ce44a5447a1b1cffd65c7272d71c/Full_DB/ClassicDB_1_12_1_z2815.sql.gz',
                         '4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0'),
}

def fetch_sources():
    import urllib.request
    ROOT.mkdir(parents=True,exist_ok=True)
    for name,(url,expected) in SOURCES.items():
        path=ROOT/name
        if not path.exists():
            path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, 'Source hash mismatch: '+name
    (ROOT/'Hoizame-revision.txt').write_text('8e99341e4e779328460bf7684c0d5b22ce50ddf1')
    (ROOT/'classic-db-revision.txt').write_text('603ece109099ce44a5447a1b1cffd65c7272d71c')

def atlas_data():
    source = (ROOT / 'data.lua').read_text()
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
    os,io,package,require,dofile = nil,nil,nil,nil,nil
    local identity=setmetatable({}, {__index=function(_,k) return k end})
    DB={}
    function DB:AddDifficulty(name) return name end
    function DB:AddItemTableType(name) return name end
    function DB:AddExtraItemTableType(name) return name end
    function DB:AddContentType(name) return name end
    AtlasLoot={CLASSIC_VERSION_NUM=1,BC_VERSION_NUM=2,WRATH_VERSION_NUM=3,
        Locales=identity,IngameLocales=identity,ItemDB={}}
    function AtlasLoot.ItemDB:Add() return DB end
    function AtlasLoot.ReturnForGameVersion(classic) return classic end
    function AtlasLoot:GameVersion_GE(v,y,n) if 1>=v then return y else return n end end
    function AtlasLoot:GameVersion_LT(v,y,n) if 1<v then return y else return n end end
    function UnitFactionGroup() return 'Alliance' end
    C_Map={GetAreaInfo=function(id) return 'Area '..id end}
    FACTION_ALLIANCE,FACTION_HORDE='Alliance','Horde'
    ''')
    for key in set(re.findall(r'\bATLASLOOT_[A-Z_0-9]+', source)):
        lua.globals()[key] = key
    lua.execute(source)
    return lua, lua.globals().DB

def sql_rows(text):
    quote = escape = False
    start = None
    for i, char in enumerate(text):
        if escape:
            escape = False
        elif quote and char == '\\':
            escape = True
        elif char == "'":
            quote = not quote
        elif not quote:
            if char == '(':
                start = i + 1
            elif char == ')' and start is not None:
                yield next(csv.reader([text[start:i]], quotechar="'", escapechar='\\', doublequote=False))
                start = None

def item_metadata():
    columns = []
    schema = False
    result = {}
    with gzip.open(ROOT / 'classic-db.sql.gz', 'rt', encoding='utf-8') as source:
        for line in source:
            if line.startswith('CREATE TABLE `item_template`'):
                schema = True
            elif schema:
                match = re.match(r'\s+`([^`]+)`', line)
                if match:
                    columns.append(match[1])
                if line.startswith(')'):
                    schema = False
            elif line.startswith('INSERT INTO `item_template` VALUES '):
                for values in sql_rows(line.partition(' VALUES ')[2]):
                    assert len(values) == len(columns), (len(values), len(columns))
                    row = dict(zip(columns, values))
                    result[int(row['entry'])] = row
    assert len(result) > 10000, len(result)
    return result

LOCATIONS = {1:'HEAD',2:'NECK',3:'SHOULDER',5:'CHEST',6:'WAIST',7:'LEGS',8:'FEET',
    9:'WRIST',10:'HAND',11:'FINGER',12:'TRINKET',13:'WEAPON',14:'SHIELD',15:'RANGED',
    16:'CLOAK',17:'2HWEAPON',20:'ROBE',21:'WEAPONMAINHAND',22:'WEAPONOFFHAND',
    23:'HOLDABLE',25:'THROWN',26:'RANGEDRIGHT',28:'RELIC'}
DUNGEONS = [
    ('Ragefire','ragefire-chasm','Ragefire Chasm',389),
    ('WailingCaverns','wailing-caverns','Wailing Caverns',43),
    ('TheDeadmines','the-deadmines','The Deadmines',36),
    ('ShadowfangKeep','shadowfang-keep','Shadowfang Keep',33),
    ('BlackfathomDeeps','blackfathom-deeps','Blackfathom Deeps',48),
    ('TheStockade','the-stockade','The Stockade',34),
    ('Gnomeregan','gnomeregan','Gnomeregan',90),
    ('RazorfenKraul','razorfen-kraul','Razorfen Kraul',47),
    ('ScarletMonasteryGraveyard','scarlet-monastery-graveyard','Scarlet Monastery Graveyard',189),
    ('ScarletMonasteryLibrary','scarlet-monastery-library','Scarlet Monastery Library',189),
    ('ScarletMonasteryArmory','scarlet-monastery-armory','Scarlet Monastery Armory',189),
    ('ScarletMonasteryCathedral','scarlet-monastery-cathedral','Scarlet Monastery Cathedral',189),
    ('RazorfenDowns','razorfen-downs','Razorfen Downs',129),
    ('Uldaman','uldaman','Uldaman',70),
    ("Zul'Farrak",'zulfarrak',"Zul'Farrak",209),
    ('Maraudon','maraudon','Maraudon',349),
    ("TheTempleOfAtal'Hakkar",'sunken-temple','Sunken Temple',109),
    ('BlackrockDepths','blackrock-depths','Blackrock Depths',230),
    ('DireMaulEast','dire-maul-east','Dire Maul East',429),
    ('LowerBlackrockSpire','lower-blackrock-spire','Lower Blackrock Spire',229),
    ('DireMaulNorth','dire-maul-north','Dire Maul North',429),
    ('DireMaulWest','dire-maul-west','Dire Maul West',429),
    ('Scholomance','scholomance','Scholomance',289),
    ('Stratholme','stratholme-main-gate','Stratholme Main Gate',329),
    ('Stratholme','stratholme-service-gate','Stratholme Service Gate',329),
    ('UpperBlackrockSpire','upper-blackrock-spire','Upper Blackrock Spire',229),
]

def literal(value):
    if value is None: return 'nil'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value, str): return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, list): return '{'+','.join(map(literal,value))+'}'
    return '{'+','.join('['+literal(k)+']='+literal(v) for k,v in sorted(value.items(),key=lambda x:str(x[0])))+'}'

def build():
    vm, source = atlas_data()
    metadata = json.loads((ROOT/'item-metadata.json').read_text()) if (ROOT/'item-metadata.json').exists() else item_metadata()
    metadata = {int(k):v for k,v in metadata.items()}
    items, dungeons, instances = {}, {}, {}
    missing = set()
    for source_key, slug, name, instance in DUNGEONS:
        dungeon = source[source_key]
        assert dungeon and dungeon.ContentType == 'Dungeons', source_key
        assert dungeon.InstanceID is None or dungeon.InstanceID == instance, (slug,dungeon.InstanceID)
        bosses = []
        undead = False
        for index, boss in sorted(dungeon['items'].items()):
            if not isinstance(index, int): continue
            boss_name = boss.name.strip()
            if boss_name == 'Magistrate Barthilas': undead = True
            if source_key == 'Stratholme':
                shared = boss_name in ('Trash','Plans')
                live_extra = boss_name.startswith("Sothos and Jarien")
                want_undead = slug.endswith('service-gate')
                if not shared and (live_extra and want_undead or not live_extra and undead != want_undead): continue
            if boss.specialType in ('quest','scourgeInvasion') or boss.TableType == 'Set': continue
            if boss_name in ("Shen'dralar Provisioner",'Henry Stern','Atiesh','Keys','Books'): continue
            loot = []
            seen = set()
            for _, row in sorted((boss.NORMAL or vm.table()).items(), key=lambda x:(not isinstance(x[0],int),x[0])):
                if not hasattr(row, 'items'): continue
                item_id = row[2]
                if not isinstance(item_id, int) or item_id in seen: continue
                fact = metadata.get(item_id)
                if not fact:
                    missing.add(item_id); continue
                loc = LOCATIONS.get(int(fact['InventoryType']))
                if int(fact['class']) not in (2,4) or not loc: continue
                seen.add(item_id)
                items[item_id] = {'id':item_id,'name':fact['name'],'quality':int(fact['Quality']),
                    'level':int(fact['RequiredLevel']),'loc':'INVTYPE_'+loc,'classID':int(fact['class']),
                    'subclassID':int(fact['subclass']),'unique':int(fact['maxcount'])==1,
                    'effects':int(fact['itemset'])>0 or any(int(fact['spellid_'+str(i)])>0 and
                        int(fact['spelltrigger_'+str(i)]) in (0,2) for i in range(1,6))}
                loot.append({'id':item_id})
            # Non-equipment tables (keys, quest objects, recipes) are not comparison rows.
            if not loot: continue
            kind = 'rare' if boss.specialType == 'rare' else 'boss'
            if 'trash' in boss_name.lower(): kind = 'trash'
            elif any(s in boss_name.lower() for s in ('cache','chest','coffer','tribute','strongbox','heirlooms')): kind = 'object'
            row = {'name':boss_name,'kind':kind,'loot':loot}
            if isinstance(boss.npcID,int): row['npcID'] = boss.npcID
            bosses.append(row)
        levels = list(dungeon.LevelRange.values())
        dungeons[slug] = {'name':name,'levels':levels[1:],'minimumLevel':levels[0],
            'bosses':bosses,'source':'AtlasLootClassic / Classic Era','new':False}
        instances.setdefault(instance,[]).append(slug)
    assert not missing, sorted(missing)
    meta = {'date':str(date.today()),'client':'Classic Era 1.15.9','dungeonCount':len(dungeons),
        'lootDungeonCount':sum(bool(d['bosses']) for d in dungeons.values()),'items':len(items),
        'groups':sum(len(d['bosses']) for d in dungeons.values()),
        'atlasRevision':(ROOT/'Hoizame-revision.txt').read_text(),
        'metadataRevision':(ROOT/'classic-db-revision.txt').read_text(),
        'sourceSHA256':hashlib.sha256((ROOT/'data.lua').read_bytes()).hexdigest()}
    output = OUTPUT
    output.mkdir(parents=True,exist_ok=True)
    lines = ['-- Generated Classic Era loot associations; see SOURCES.md.', 'local _, CD = ...',
        'CD.Catalog = {}','local D = CD.Catalog','D.meta = '+literal(meta),
        'D.order = '+literal([d[1] for d in DUNGEONS]),'D.instances = '+literal(instances),'D.items = {']
    lines.extend('    ['+str(k)+'] = '+literal(v)+',' for k,v in sorted(items.items()))
    lines += ['}','D.dungeons = {']
    for slug,dungeon in dungeons.items():
        details = {k:v for k,v in dungeon.items() if k != 'bosses'}
        lines.append('    ['+literal(slug)+'] = '+literal(details)[:-1]+',["bosses"]={')
        lines.extend('        '+literal(boss)+',' for boss in dungeon['bosses'])
        lines.append('    }},')
    lines.append('}')
    (output/'Catalog.lua').write_text('\n'.join(lines)+'\n')
    (ROOT/'catalog_stats.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta,indent=2))

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Rebuild the Classic Era-only loot catalogue from pinned sources.')
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args()
    OUTPUT=args.output
    fetch_sources()
    build()
