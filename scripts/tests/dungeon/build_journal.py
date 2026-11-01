"""Build the Era dungeon journal from pinned AtlasLoot, ClassicDB and Questie data.

Runtime has no dependency on those addons or on a network connection.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
from lupa.lua51 import LuaRuntime
import build_catalog as legacy

ROOT = legacy.ROOT
OUT = legacy.OUTPUT
QUESTIE = ROOT / 'questie-source'
AREA = {
    'ragefire-chasm': [2437], 'wailing-caverns': [718], 'the-deadmines': [1581, 10029],
    'shadowfang-keep': [209], 'blackfathom-deeps': [719], 'the-stockade': [717],
    'gnomeregan': [721, 133], 'razorfen-kraul': [491, 1717],
    'scarlet-monastery-graveyard': [796], 'scarlet-monastery-library': [796],
    'scarlet-monastery-armory': [796], 'scarlet-monastery-cathedral': [796],
    'razorfen-downs': [722], 'uldaman': [1337, 1517], 'zulfarrak': [1176, 978],
    'maraudon': [2100, 10000], 'sunken-temple': [1477, 1417],
    'blackrock-depths': [1584, 1585], 'lower-blackrock-spire': [1583],
    'upper-blackrock-spire': [1583], 'dire-maul-east': [2557],
    'dire-maul-west': [2557], 'dire-maul-north': [2557], 'scholomance': [2057],
    'stratholme-main-gate': [2017, 10001, 10002],
    'stratholme-service-gate': [2017, 10001, 10002],
}
# Encounters without a curated equipment table must still appear in the journal.
# Their NPC levels and quest-only drops come from the same pinned ClassicDB snapshot.
EXTRA_BOSSES = {
    'ragefire-chasm': [11517, 11519],
    'the-stockade': [1696, 1717, 1663, 1716],
    'blackfathom-deeps': [12902],
    'razorfen-kraul': [6168],
}


def sql_tables(wanted):
    columns, result, active, name = {}, {k: [] for k in wanted}, False, ''
    with gzip.open(ROOT / 'classic-db.sql.gz', 'rt') as source:
        for line in source:
            if line.startswith('CREATE TABLE '):
                name = line.split('`')[1]
                active = name in wanted
                if active: columns[name] = []
            elif active:
                match = re.match(r'\s+`([^`]+)`', line)
                if match: columns[name].append(match[1])
                if line.startswith(')'): active = False
            elif line.startswith('INSERT INTO `'):
                name = line.split('`')[1]
                if name in wanted:
                    for row in legacy.sql_rows(line.partition(' VALUES ')[2]):
                        assert len(row) == len(columns[name]), name
                        result[name].append(dict(zip(columns[name], row)))
    return result


def load_questie():
    manifest = json.loads((QUESTIE / 'sources.json').read_text())
    assert manifest['revision'] == '7901fee2753cecb577a72c2e4b7126198e05baec'
    for entry in manifest['files']:
        assert hashlib.sha256((QUESTIE / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
    vm = LuaRuntime(unpack_returned_tuples=True)
    vm.execute('DB={}; QuestieLoader={ImportModule=function() return DB end}; os,io,require,package=nil,nil,nil,nil')
    for kind in ('Quest', 'Npc', 'Object', 'Item'):
        path = QUESTIE / f'data/Classic/classic{kind}DB.lua'
        vm.execute(path.read_text())
        key = kind.lower()
        vm.globals().DB[key + 'Data'] = vm.execute(vm.globals().DB[key + 'Data'])
    return vm, vm.globals().DB


def values(table):
    return list(table.values()) if table is not None else []


def ints(table):
    return sorted({int(n) for n in values(table) if isinstance(n, (int, float)) and n != 0})


def build():
    legacy.fetch_sources()
    vm, atlas = legacy.atlas_data()
    _, qdb = load_questie()
    tables = sql_tables({'item_template', 'quest_template', 'creature_template', 'creature_loot_template'})
    rawitems = {int(x['entry']): x for x in tables['item_template']}
    rawquests = {int(x['entry']): x for x in tables['quest_template']}
    npcs = {int(x['Entry']): x for x in tables['creature_template']}
    questloot = collections.defaultdict(set)
    for row in tables['creature_loot_template']:
        item = rawitems.get(int(row['item']))
        if item and int(row['mincountOrRef']) > 0 and (
                float(row['ChanceOrQuestChance']) < 0 or int(item['startquest']) > 0):
            questloot[int(row['entry'])].add(int(row['item']))

    items, dungeons, instances = {}, {}, {}
    def add_item(item_id):
        if item_id in items: return True
        raw = rawitems.get(item_id)
        if not raw: return False
        statkeys = {0: 'mana', 1: 'health', 3: 'agi', 4: 'str', 5: 'int', 6: 'spirit', 7: 'sta'}
        stats = {}
        for i in range(1, 11):
            key, val = statkeys.get(int(raw[f'stat_type{i}'])), int(raw[f'stat_value{i}'])
            if key and val: stats[key] = stats.get(key, 0) + val
        if int(raw['armor']): stats['armor'] = int(raw['armor'])
        for school in ('holy', 'fire', 'nature', 'frost', 'shadow', 'arcane'):
            if int(raw[school + '_res']): stats[school + 'Res'] = int(raw[school + '_res'])
        if int(raw['block']): stats['blockValue'] = int(raw['block'])
        low = sum(float(raw[f'dmg_min{i}']) for i in range(1, 6))
        high = sum(float(raw[f'dmg_max{i}']) for i in range(1, 6))
        speed = int(raw['delay']) / 1000
        loc = legacy.LOCATIONS.get(int(raw['InventoryType']))
        record = {'id': item_id, 'name': raw['name'], 'quality': int(raw['Quality']),
            'level': int(raw['RequiredLevel']), 'itemLevel': int(raw['ItemLevel']),
            'classID': int(raw['class']), 'subclassID': int(raw['subclass']),
            'loc': 'INVTYPE_' + loc if loc else '', 'stats': stats,
            'classes': int(raw['AllowableClass']), 'races': int(raw['AllowableRace']),
            'skill': int(raw['RequiredSkill']), 'skillRank': int(raw['RequiredSkillRank']),
            'spell': int(raw['requiredspell']), 'quest': int(raw['startquest']),
            'effects': int(raw['itemset']) > 0 or any(int(raw[f'spellid_{i}']) > 0 for i in range(1, 6))}
        if speed and high:
            record.update(damageMin=low, damageMax=high, weaponSpeed=speed, dps=round((low + high) / (2 * speed), 1))
        items[item_id] = record
        return True

    for key, slug, name, instance in legacy.DUNGEONS:
        src = atlas[key]
        bosses, other, undead = [], [], False
        for _, group in sorted(src['items'].items()):
            title = group.name.strip()
            if title == 'Magistrate Barthilas': undead = True
            if key == 'Stratholme':
                shared = title in ('Trash', 'Plans')
                extra = title.startswith('Sothos and Jarien')
                want = slug.endswith('service-gate')
                if not shared and (extra and want or not extra and undead != want): continue
            if group.specialType in ('quest', 'scourgeInvasion') or group.TableType == 'Set': continue
            if title in ("Shen'dralar Provisioner", 'Henry Stern', 'Atiesh', 'Keys', 'Books'): continue
            ids = [int(group.npcID)] if isinstance(group.npcID, int) else ints(group.npcID)
            loot = {int(r[2]) for r in values(group.NORMAL) if hasattr(r, 'items') and isinstance(r[2], int)}
            for npc in ids:
                if npc in npcs: loot.update(questloot.get(int(npcs[npc]['LootId']), set()))
            loot = [{'id': n} for n in sorted(loot) if add_item(n)]
            if not loot and not ids: continue
            kind = 'rare' if group.specialType == 'rare' else 'boss'
            if 'trash' in title.lower() or title == 'Plans': kind = 'trash'
            elif not ids or any(x in title.lower() for x in ('coffer', 'chest', 'tribute', 'cache', 'guzzler')): kind = 'object'
            levels = [(int(npcs[n]['MinLevel']), int(npcs[n]['MaxLevel'])) for n in ids if n in npcs]
            entry = {'name': title, 'kind': kind, 'loot': loot, 'npcIDs': ids}
            if levels: entry.update(minLevel=min(a for a, _ in levels), maxLevel=max(b for _, b in levels))
            (other if kind == 'trash' else bosses).append(entry)
        known = {n for group in bosses for n in group['npcIDs']}
        for npc in EXTRA_BOSSES.get(slug, []):
            if npc in known: continue
            record = npcs[npc]
            loot = [{'id': n} for n in sorted(questloot.get(int(record['LootId']), set())) if add_item(n)]
            bosses.append({'name': record['Name'], 'kind': 'boss', 'npcIDs': [npc],
                'minLevel': int(record['MinLevel']), 'maxLevel': int(record['MaxLevel']), 'loot': loot})
        levels = list(src.LevelRange.values())
        dungeons[slug] = {'name': name, 'levels': levels[1:], 'minimumLevel': levels[0],
            'bosses': bosses, 'sharedLoot': other, 'areas': AREA[slug]}
        instances.setdefault(instance, []).append(slug)

    # Associate objectives, their item sources, and quest starters with dungeon areas.
    # This catches dungeon quests sorted under a class or an outdoor zone as well.
    def entity_areas(entity, kind):
        row = qdb[kind + 'Data'][entity]
        index = 7 if kind == 'npc' else 4
        return set(int(k) for k in row[index].keys()) if row and row[index] else set()

    def item_areas(item_id):
        fact = rawitems.get(item_id)
        # Wool, leather, herbs and other ordinary materials also drop in dungeons.
        # Their outdoor/profession turn-ins are not dungeon quests.
        if not fact or (int(fact['class']) != 12 and int(fact['startquest']) == 0):
            return set()
        row = qdb.itemData[item_id]
        result = set()
        if row:
            if int(fact['class']) != 12 and len(ints(row[2])) > 12:
                return set()  # A world-drop quest starter is not dungeon-specific.
            for n in ints(row[2]): result.update(entity_areas(n, 'npc'))
            for n in ints(row[3]): result.update(entity_areas(n, 'object'))
        return result

    relevant, questzones, questnpcs = {}, {}, {}
    for quest_id in rawquests:
        row = qdb.questData[quest_id]
        if not row: continue
        zones, targets = set(), set()
        if row[17] and row[17] > 0: zones.add(int(row[17]))
        objectives = row[10]
        if objectives:
            for n, kind in ((1, 'npc'), (2, 'object')):
                for objective in values(objectives[n]):
                    entity = objective[1]
                    if isinstance(entity, int):
                        zones.update(entity_areas(entity, kind))
                        if kind == 'npc': targets.add(entity)
            for objective in values(objectives[3]):
                if isinstance(objective[1], int):
                    zones.update(item_areas(objective[1]))
                    item = qdb.itemData[objective[1]]
                    if item: targets.update(ints(item[2]))
        start = row[2]
        if start:
            for n in ints(start[1]): zones.update(entity_areas(n, 'npc'))
            for n in ints(start[2]): zones.update(entity_areas(n, 'object'))
            for n in ints(start[3]): zones.update(item_areas(n))
        questzones[quest_id], questnpcs[quest_id] = zones, targets
        relevant[quest_id] = row

    questids = set()
    for slug, dungeon in dungeons.items():
        family = [d for d in dungeons.values() if d['areas'] == dungeon['areas']]
        own = {n for g in dungeon['bosses'] for n in g['npcIDs']}
        siblings = {n for d in family for g in d['bosses'] for n in g['npcIDs']} - own
        guide = []
        for quest_id, zones in questzones.items():
            if not zones.intersection(dungeon['areas']): continue
            targets = questnpcs[quest_id]
            if targets.intersection(siblings) and not targets.intersection(own): continue
            guide.append(quest_id)
        dungeon['quests'] = sorted(guide, key=lambda n: (relevant[n][5] or 0, n))
        questids.update(guide)

    # Include the entire transitive prerequisite graph, not merely the previous ID.
    def dependencies(row):
        result = ints(row[12]) + ints(row[13])
        if row[25]: result.append(int(row[25]))
        return {abs(n) for n in result if abs(n) in relevant}
    pending = list(questids)
    while pending:
        for parent in dependencies(relevant[pending.pop()]):
            if parent not in questids: questids.add(parent); pending.append(parent)

    # Zone names from the source SQL; all needed outdoor zones have stable English names.
    zone_names = {}
    zonefile = QUESTIE / 'Localization/lookups/lookupZones.lua'
    if zonefile.exists():
        for m in re.finditer(r'\[(\d+)\]\s*=\s*"([^"]+)"', zonefile.read_text().partition('l10n.zoneLookup =')[2]):
            zone_names.setdefault(int(m[1]), m[2])
    # The game's map names are resolved at runtime; these cover areas without a client map.
    for dungeon in dungeons.values():
        for area in dungeon['areas']: zone_names.setdefault(area, dungeon['name'])

    quests, giver_ids = {}, set()
    def giver(kind, entity):
        dbkind = 'npc' if kind == 'npc' else 'object' if kind == 'object' else 'item'
        row = qdb[dbkind + 'Data'][entity]
        result = {'kind': kind, 'id': entity, 'name': row[1] if row else f'{kind.title()} #{entity}', 'locations': []}
        if kind == 'item':
            for n in ints(row[2] if row else None):
                npc = qdb.npcData[n]
                if npc:
                    result.setdefault('sources', []).append(npc[1])
                    for zone, coords in (npc[7].items() if npc[7] else []):
                        for pos in values(coords)[:1]:
                            loc = {'zone': int(zone), 'source': npc[1]}
                            if pos[1] >= 0 and pos[2] >= 0: loc.update(x=pos[1], y=pos[2])
                            result['locations'].append(loc)
            return result
        spawns = row[7 if kind == 'npc' else 4] if row else None
        for zone, coords in sorted(spawns.items() if spawns else []):
            for pos in values(coords)[:1]:
                loc = {'zone': int(zone)}
                if pos[1] >= 0 and pos[2] >= 0: loc.update(x=pos[1], y=pos[2])
                result['locations'].append(loc)
        return result

    for quest_id in sorted(questids):
        row = relevant[quest_id]
        start, givers = row[2], []
        if start:
            for index, kind in ((1, 'npc'), (2, 'object'), (3, 'item')):
                for entity in ints(start[index]): givers.append(giver(kind, entity))
        record = {'id': quest_id, 'name': row[1], 'level': row[5] or 0, 'minLevel': row[4] or 0,
            'races': row[6] or 0, 'classes': row[7] or 0, 'givers': givers,
            'previousAll': [abs(n) for n in ints(row[12])], 'previousAny': [abs(n) for n in ints(row[13])],
            'activeParent': abs(int(row[25])) if row[25] else 0,
            'repeatable': bool(row[24] and int(row[24]) % 2),
            'skill': [row[18][1], row[18][2]] if row[18] else [],
            'minRep': [row[19][1], row[19][2]] if row[19] else [],
            'maxRep': [row[20][1], row[20][2]] if row[20] else [],
            'exclusive': ints(row[16]), 'maxLevel': row[32] or 0}
        quests[quest_id] = record

    # Runtime map lookup uses Era's AreaTable -> UiMap mapping, never world-space coordinates.
    map_vm = LuaRuntime(unpack_returned_tuples=True)
    map_vm.execute('Z={private={}}; QuestieLoader={ImportModule=function() return Z end}')
    map_vm.execute((QUESTIE / 'support/Zones/areaIdToUiMapId.lua').read_text())
    maps = map_vm.execute(map_vm.globals().Z.private.areaIdToUiMapId)
    needed = {loc['zone'] for q in quests.values() for g in q['givers'] for loc in g['locations']}
    area_maps = {n: int(maps[n]) for n in needed if isinstance(maps[n], int) and maps[n] > 0}
    meta = {'version': 2, 'dungeons': len(dungeons), 'bosses': sum(len(d['bosses']) for d in dungeons.values()),
        'items': len(items), 'dungeonQuests': len({q for d in dungeons.values() for q in d['quests']}),
        'questsWithPrerequisites': len(quests), 'questieRevision': '7901fee2753cecb577a72c2e4b7126198e05baec'}
    header = '-- Generated Classic Era data; factual source associations are documented in SOURCES.md.\nlocal _, CD = ...\n'
    (OUT / 'Catalog.lua').write_text(header + 'CD.Catalog = ' + legacy.literal({
        'meta': meta, 'order': [d[1] for d in legacy.DUNGEONS], 'instances': instances,
        'items': items, 'dungeons': dungeons}) + '\n')
    (OUT / 'QuestCatalog.lua').write_text(header + 'CD.QuestCatalog = ' + legacy.literal({
        'quests': quests, 'areaMaps': area_maps, 'areaNames': zone_names}) + '\n')
    (ROOT / 'journal_stats.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output
    OUT.mkdir(parents=True, exist_ok=True)
    build()
