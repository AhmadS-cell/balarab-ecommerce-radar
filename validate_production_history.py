from pathlib import Path
import json,re
root=Path(__file__).parent
registry=json.loads((root/'production-history.json').read_text(encoding='utf-8'))
page=(root/'docs/index.html').read_text(encoding='utf-8')
rows=json.loads(re.search(r'const REELS = (\[.*?\]);\n',page,re.S).group(1))
lookup={x['id']:x for x in rows}
assert len(registry['ideas'])==len({x['idea_id'] for x in registry['ideas']}),'Duplicate production idea ID'
assert 'كاروسيل' not in page,'An active adaptation still uses carousel format'
for idea in registry['ideas']:
 assert idea['format']=='Reel'
 assert isinstance(idea['selected_week'],int) and idea['selected_week']>0
 assert idea['source_id'] in lookup
 row=lookup[idea['source_id']]
 assert row['ideaId']==idea['idea_id']
 assert row['selectedWeek']==idea['selected_week']
 assert row['productionState']==idea['state']
 assert any(event.get('type')=='selected_for_week' for event in idea['events'])
 if idea['state'] in ['script_draft','queued','existing_work_in_progress']:
  assert idea['produced_week'] is None and idea['published_week'] is None,'A draft was marked produced or published'
 if idea.get('script_page'):
  assert (root/'docs'/idea['script_page']).is_file()
assert len(registry['ideas'])>=5
print('PASS: weekly identity, Reels-only output, linked prior work and separate draft/produced/published states.')

review=re.search(r'<select id="review">(.*?)</select>',page,re.S).group(1)
assert re.search(r'<option value="all" selected>',review),"Full library must be the default"
assert "$('review').value='all'" in page,"Reset must restore the full library"
print("PASS: full library is visible by default and after reset.")
