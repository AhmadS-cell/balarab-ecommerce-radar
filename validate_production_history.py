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
assert re.search(r'<option value="all" selected>',review),"All eligible references must be the default"
assert "$('review').value='all'" in page,"Reset must restore the full library"
print("PASS: all eligible references are selected by default and after reset.")

# Historical records stay archived while every visible route uses the eligibility pool.
audit=json.loads((root/'library-language-review.json').read_text(encoding='utf-8'))
assert set(audit['retained_original_ids']) <= set(lookup),'Historical references were removed'
assert set(audit['new_ids']) <= set(lookup),'New source references are missing'
eligible=[r for r in rows if r.get('visibleEligible') is True]
assert all(r['contentLanguage']=='en' and r['ecommerceFit'] in ['high','medium'] for r in eligible)
assert len(eligible)==audit['eligible_count']
assert len(rows)==audit['archived_total']
assert audit['hidden_count']==len(rows)-len(eligible)
assert all(r.get('languageBasis') and r.get('eligibilityCheckedAt') for r in rows)
assert 'const ELIGIBLE=REELS.filter(r=>r.visibleEligible===true)' in page
assert 'visible=ELIGIBLE.filter(r=>' in page
assert 'new Set(ELIGIBLE.map(r=>r.brand))' in page
assert 'new Set(ELIGIBLE.map(r=>r.category))' in page
assert 'https://www.youtube-nocookie.com/embed/' in page
for id in ['DerYEm6Cn4f','DewhU2NqgZQ','DSkP5UODUZb','DZXwMw5Bo37','DeEAfmdhsHH','C8r1GHCSVKp']:
 assert not lookup[id]['visibleEligible'],'A reviewed non-English video became visible'
print('PASS: English and ecommerce eligibility, archive preservation and YouTube preview support.')
