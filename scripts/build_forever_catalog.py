"""Compile the pinned Forever loot and quest snapshots (not used by normal builds).

Inputs are development snapshots, never read from another installed addon at runtime.
Only factual records are emitted; unknown levels/coordinates stay unknown.
Requires lupa.lua51, as do the journal's other data tools.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import os
import re
from pathlib import Path
from lupa.lua51 import LuaRuntime, lua_type

ROOT = Path(__file__).resolve().parent.parent
AREA = {
    'hall-of-thanes':16919,'ruins-of-lordaeron':16611,'excavation-site':16732,
    'city-of-dalaran':16544,'ragefire-chasm':2437,'wailing-caverns':718,
    'the-deadmines':1581,'shadowfang-keep':209,'blackfathom-deeps':719,
    'the-stockade':717,'gnomeregan':721,'razorfen-kraul':491,
    'razorfen-downs':722,'uldaman':1337,'zulfarrak':1176,'maraudon':2100,
    'sunken-temple':1477,'blackrock-depths':1584,'lower-blackrock-spire':1583,
    'upper-blackrock-spire':1583,'scholomance':2057,
}
AREA.update({f'scarlet-monastery-{wing}':796 for wing in ['graveyard','library','armory','cathedral']})
AREA.update({f'dire-maul-{wing}':2557 for wing in ['east','west','north']})
AREA.update({f'stratholme-{wing}-gate':2017 for wing in ['main','service']})
LOC = dict(zip(['Head','Neck','Shoulder','Back','Chest','Wrist','Hands','Waist','Legs','Feet',
    'Finger','Trinket','Main Hand','One-Hand','Off Hand','Two-Hand','Shield','Held In Off-hand',
    'Ranged','Thrown','Relic'], ['HEAD','NECK','SHOULDER','CLOAK','CHEST','WRIST','HAND','WAIST',
    'LEGS','FEET','FINGER','TRINKET','WEAPONMAINHAND','WEAPON','WEAPONOFFHAND','2HWEAPON',
    'SHIELD','HOLDABLE','RANGED','THROWN','RELIC']))
STATS = {0:'mana',1:'health',3:'agi',4:'str',5:'int',6:'spirit',7:'sta',
    12:'defense',13:'dodge',14:'parry',15:'block',16:'hit',17:'hit',18:'spellhit',
    19:'crit',20:'crit',21:'spellcrit',31:'hit',32:'crit',36:'haste',37:'expertise',
    38:'ap',39:'rap',40:'feralap',41:'healing',42:'damage',43:'mp5',45:'sp',
    46:'hp5',47:'spellpen',48:'blockValue',50:'armor',51:'fireRes',52:'frostRes',
    53:'holyRes',54:'shadowRes',55:'natureRes',56:'arcaneRes'}

def lua(x):
    if x is None:return 'nil'
    if isinstance(x,bool):return 'true' if x else 'false'
    if isinstance(x,str):return json.dumps(x,ensure_ascii=False)
    if isinstance(x,(int,float)):return str(x)
    if isinstance(x,list):return '{'+','.join(map(lua,x))+'}'
    return '{'+','.join('['+lua(k)+']='+lua(v) for k,v in sorted(x.items(),key=lambda p:str(p[0])))+'}'

def py(x):
    return {k:py(v) for k,v in x.items()} if lua_type(x)=='table' else x

def array(x):return list(x.values()) if isinstance(x,dict) else x or []

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loot',type=Path,required=True)
    p.add_argument('--quests',type=Path,required=True)
    p.add_argument('--database',type=Path,required=True,help='Pinned QuestieDB checkout, read only')
    args=p.parse_args()
    source=json.loads(args.loot.read_text())
    vm=LuaRuntime(unpack_returned_tuples=True);ns=vm.table()
    vm.eval('function(s,n) assert(loadstring(s))("Snapshot",n) end')(args.quests.read_text(),ns)
    data=py(ns.Data)
    assert data['revision']=='e9a67d1a2753a0e64c4c96bf7864788fac7b765f'
    assert hashlib.sha256(args.loot.read_bytes()).hexdigest()=='ab3d3342dbebd379151ead0d14380e30fa9a8da962461202cae14f275330793f'
    catalog={'dungeons':{},'items':{},'order':[],'instances':{},'meta':{
        'client':'forever','date':source['retrieved'][:10],'sourceBuild':source['sourceBuild'],
        'lootSHA256':hashlib.sha256(args.loot.read_bytes()).hexdigest(),
        'questSHA256':hashlib.sha256(args.quests.read_bytes()).hexdigest(),
        'questRevision':data['revision']}}
    levels=defaultdict(list)
    oldcwd=Path.cwd()
    try:
        os.chdir(args.database)
        db=LuaRuntime(unpack_returned_tuples=True)
        db.execute('client=dofile("emulator/client.lua");client.install({expansion="Forever"});'
            'Lib=dofile("emulator/metadata.lua").loadAddon("QuestieDB.toc","QuestieDB");'
            'UnitFactionGroup=function()return "Alliance" end;'
            'UnitClassBase=function()return "WARRIOR",1 end;Lib.ApplyRegisteredCorrections("QuestieDB")')
        npcs=db.globals().Lib.Npc
        for id in npcs.GetAllIds().values():
            name=npcs.Get(id,'name')
            for field in ['minLevel','maxLevel']:
                value=npcs.Get(id,field)
                if name and value and value>0:levels[name].append(value)
    finally:
        os.chdir(oldcwd)
    for npc in data['npcs'].values():
        if npc.get('mobLevel'):levels[npc['name']].append(npc['mobLevel'])
    for quest in data['quests'].values():
        for obj in array(quest.get('objectives')):
            if obj.get('type')=='kill' and obj.get('mobLevel'):levels[obj['name']].append(obj['mobLevel'])
    for d in source['dungeons']:
        slug=d['id'];area=AREA.get(slug);guide=data['dungeons'].get(area,{})
        entry={'name':d['name'],'levels':d['levels'],'minimumLevel':guide.get('minLevel'),
            'bosses':[],'sharedLoot':[],'quests':array(guide.get('quests')),'source':d['source']}
        for b in d['bosses']:
            if b['kind']=='quest':continue
            group={'name':b['name'],'kind':b['kind'],'loot':[],'npcIDs':[]}
            if levels[b['name']]:group.update(minLevel=min(levels[b['name']]),maxLevel=max(levels[b['name']]))
            for raw in b.get('items',[]):
                id=raw['i'];lines=raw.get('x') or []
                item={'id':id,'name':raw['n'],'level':raw.get('r',0),'itemLevel':raw.get('l'),
                    'quality':raw.get('q',1),'classID':raw.get('c'),'subclassID':raw.get('u'),
                    'loc':'INVTYPE_'+LOC[raw['s']] if raw.get('s') in LOC else '',
                    'stats':{STATS[int(k)]:v for k,v in raw.get('v',{}).items() if int(k) in STATS},
                    'effects':any(x.startswith(('Equip:','Use:','Chance on hit:')) for x in lines)}
                for line in lines:
                    match=re.search(r'\(([\d.]+) damage per second\)',line)
                    if match:item['dps']=float(match[1])
                    match=re.search(r'([\d.]+) - ([\d.]+) Damage\s+Speed ([\d.]+)',line)
                    if match:item.update(zip(['damageMin','damageMax','weaponSpeed'],map(float,match.groups())))
                if id not in catalog['items'] or raw.get('w'):catalog['items'][id]=item
                if id not in [x['id'] for x in group['loot']]:group['loot'].append({'id':id})
            entry['sharedLoot' if b['kind']=='trash' else 'bosses'].append(group)
        catalog['dungeons'][slug]=entry;catalog['order'].append(slug)
    for instance,area in data['instanceDungeons'].items():
        slugs=[s for s,a in AREA.items() if a==area and s in catalog['dungeons']]
        if slugs:catalog['instances'][instance]=slugs
    relevant={id for d in catalog['dungeons'].values() for id in d['quests']}
    variants=[data['quests'],data['horde'],*data['classes'].values()]
    pending=list(relevant)
    while pending:
        id=pending.pop()
        for table in variants:
            row=table.get(id,{})
            for parent in array(row.get('preAll'))+array(row.get('preAny'))+[row.get('parent',0)]:
                parent=abs(parent)
                if parent and parent not in relevant and any(parent in t for t in variants):
                    relevant.add(parent);pending.append(parent)
    def convert(q):
        givers={}
        for point in array(q.get('start')):
            key=(point.get('entity'),point.get('id'),point.get('name'))
            giver=givers.setdefault(key,{'id':point.get('id'),'name':point['name'],
                'kind':'object' if point.get('entity')=='Object' else 'npc','locations':[]})
            giver['locations'].append({'map':point['m'],'x':point['x']*100,'y':point['y']*100})
        if not givers and q.get('dungeonPickup'):
            name=q['dungeonPickup'].split(' · ')[0]
            givers[('pickup',)]={'name':name,'kind':'object' if q.get('startItems') else 'npc','locations':[]}
        for id in array(q.get('startItems')):
            givers[('item',id)]={'id':id,'kind':'item','name':catalog['items'].get(id,{}).get('name',f'Item #{id}'),'locations':[]}
        return {'id':q['id'],'name':q['name'],'level':q['level'],'minLevel':q['min'],
            'maxLevel':q.get('max',0),'faction':q['side'] if q['side']!='both' else None,
            'races':q.get('races',0),'classes':q.get('classes',0),'givers':list(givers.values()),
            'previousAll':[abs(x) for x in array(q.get('preAll'))],
            'previousAny':[abs(x) for x in array(q.get('preAny'))],
            'activeParent':abs(q.get('parent',0)),'repeatable':q.get('repeatable',False),
            'exclusive':array(q.get('exclusive')),'skill':array(q.get('skill')),
            'minRep':array(q.get('minRep')),'maxRep':array(q.get('maxRep'))}
    quests={'quests':{id:convert(q) for id,q in data['quests'].items() if id in relevant},
        'horde':{id:convert(q) for id,q in data['horde'].items() if id in relevant},
        'classes':{k:{id:convert(q) for id,q in rows.items() if id in relevant} for k,rows in data['classes'].items()},
        'areaMaps':{},'areaNames':{},'mapNames':{},
        'factionMasks':{'Alliance':4294967373,'Horde':8589934770}}
    out=ROOT/'ElmoDungeonLoot'
    for name,value in [('CatalogForever',catalog),('QuestCatalogForever',quests)]:
        var='Catalog' if name=='CatalogForever' else 'QuestCatalog'
        (out/(name+'.lua')).write_text('-- Generated Forever facts; see SOURCES.md.\nlocal _,CD=...\nCD.'+var+'='+lua(value)+'\n')
    print(f"Forever: {len(catalog['dungeons'])} dungeons, {len(catalog['items'])} items, {len(quests['quests'])} quests including prerequisites")

if __name__=='__main__':main()
