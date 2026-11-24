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
assert 'const ELIGIBLE=REELS.filter(r=>r.visibleEligible===true&&r.teachingEligible===true)' in page
assert 'visible=ELIGIBLE.filter(r=>' in page
assert 'new Set(ELIGIBLE.map(r=>r.brand))' in page
assert 'new Set(ELIGIBLE.map(r=>r.category))' in page
assert 'https://www.youtube-nocookie.com/embed/' in page
for id in ['DerYEm6Cn4f','DewhU2NqgZQ','DSkP5UODUZb','DZXwMw5Bo37','DeEAfmdhsHH','C8r1GHCSVKp']:
 assert not lookup[id]['visibleEligible'],'A reviewed non-English video became visible'
print('PASS: English and ecommerce eligibility, archive preservation and YouTube preview support.')

# Shorts are verified sources, with numeric dated observations and a dedicated filter.
for id in audit['shorts_ids']:
 r=lookup[id]
 assert r['platform']=='youtube' and r['sourceFormat']=='shorts'
 if r['visibleEligible']: assert r['teachingEligible']
 assert isinstance(r['views'],int) and r['views']>=0 and r['capturedAt']
 assert 0<r['durationSeconds']<=180
 assert r['url'].startswith('https://www.youtube.com/shorts/')
assert '<option value="shorts">YouTube Shorts</option>' in page
assert "$('format').value==='all'||r.sourceFormat===$('format').value" in page
assert "['market','brand','platform','collection','format'].forEach" in page
assert "new URLSearchParams(location.search).get('format')==='shorts'" in page
print('PASS: Shorts format, dated view counts, direct filter and reset behavior.')

# A source must itself teach the merchant; founder/case clips remain archived and hidden.
assert all(r.get('teachingEligible') is True and r.get('merchantProblem') and r.get('sourceTakeaway') and r.get('sourceAction') for r in eligible)
for id in ['IWaTcbTZJ6w','dY1RBYqT9MQ','xV8lunF9Dw8','313GvO3pScc','8ZCJwh6kSvs']:
 assert id in lookup and not lookup[id]['visibleEligible'] and not lookup[id]['teachingEligible']
for id in audit['teaching_batch_ids']:
 assert lookup[id]['visibleEligible'] and lookup[id]['teachingEligible'] and lookup[id]['tipsBatch']
assert '<option value="tips">دفعة النصائح التعليمية الجديدة</option>' in page
assert "get('review')==='tips'" in page
assert "cleanURL.searchParams.delete('review')" in page
print('PASS: direct teaching evidence, retained-but-hidden founder/case records, and new teaching collection.')

# New short-tip collection never substitutes long lectures or loses prior production state.
assert '<option value="shorttips">' in page
assert "get('review')==='shorttips'" in page
for id in audit['short_tips_batch_ids']:
 r=lookup[id]
 assert r['visibleEligible'] and r['teachingEligible'] and r['shortTipsBatch']
 assert r['sourceFormat'] in ['reel','shorts'] and 0<r['durationSeconds']<=60
 assert r['views']>=100000 and r['contentLanguage']=='en' and r['capturedAt']
 assert r['animationVerified'] and r['visualSampleSeconds']==[3,18,32]
 assert r['visualReviewAt'] and r['factCheckStatus']
 assert 'selectedWeek' not in r and 'producedWeek' not in r
assert lookup['DenaEc2ICUK']['relatedIdeaIds']==['BR-W001-02']
print('PASS: new short merchant tips, dated high views, sampled animation evidence and no duplicate production.')

# The operations collection adds new creators without inventing animation or production.
assert '<option value="operations">' in page and "get('review')==='operations'" in page
assert len({lookup[id]['brand'] for id in audit['operations_tips_batch_ids']})>=2
for id in audit['operations_tips_batch_ids']:
 r=lookup[id]
 assert r['platform']=='youtube' and r['sourceFormat']=='shorts' and r['operationsTipsBatch']
 assert r['visibleEligible'] and r['teachingEligible'] and r['contentLanguage']=='en'
 assert 0<r['durationSeconds']<=60 and r['views']>=100000 and r['capturedAt']
 assert r['brand']!='decoyreport' and not r['animationVerified'] and r['visualStyle']
 assert r['older'] and r['visualSampleSeconds'] and r['factCheckLinks']
 if r.get('selectedWeek'):
  assert id=='bOEUyr63h_k' and r['selectedWeek']==2 and r['productionState']=='proposed'
 assert not r.get('producedWeek')
print('PASS: new non-decoy financial Shorts, actual visual style, dated views and preserved production history.')

# Company research is evidence-backed and never changes the existing production ledger.
import statistics
companies_data=json.loads(re.search(r'id="company-research-data">(.*?)</script>',page,re.S).group(1))
assert len(companies_data['companies'])==14
assert companies_data['coverage']['native_youtube_shorts']==189
assert len(audit['agency_batch_ids'])==6
for c in companies_data['companies']:
 assert c['official_url'].startswith('https://') and c['reason_ar'] and c['limitations_ar']
 for surface in ['instagram','youtube']:
  st=c[surface];a=st['sample'];v=[x['views'] for x in a if x.get('views') is not None]
  assert st['n']==len(a) and st['views_available']==len(v)
  assert st['median_views']==(statistics.median(v) if v else None)
for id in audit['agency_batch_ids']:
 r=lookup[id];bm=r['benchmark']
 assert r['agencyBatch'] and r['visibleEligible'] and r['teachingEligible'] and r['contentLanguage']=='en'
 assert r['companyReason'] and r['benchmarkText'] and r['capturedAt'] and r['durationSeconds']<=120
 assert not r.get('selectedWeek') and not r.get('producedWeek')
 assert id not in bm['peer_ids'] and bm['peer_n']==len(bm['peer_ids'])
 assert abs(bm['visible_er']-100*(r['likes']+r['comments'])/r['views'])<1e-9
 if bm['views_ratio'] is not None:
  assert bm['peer_n']>=5 and abs(bm['views_ratio']-r['views']/bm['peer_median_views'])<1e-9
 assert not r['animationVerified']
assert '<option value="agencies">' in page and "get('review')==='agencies'" in page
print('PASS: company sample denominators, missing values, source exclusion, engagement formulas and no new production states.')

# Owner-provided seeds are retained without trusting anomalous like counts or duplicating production.
assert len(audit['seed_batch_ids'])==5
for id in audit['seed_batch_ids']:
 r=lookup[id]
 assert r['seedBatch'] and r['animationVerified'] and r['visualSampleSeconds']==[3,18,32]
 assert r['contentLanguage']=='en' and r['visibleEligible'] and r['teachingEligible']
 assert not r.get('selectedWeek') and not r.get('producedWeek')
 if r['author']=='advertizingly':
  assert r['likes'] is None and r['rawReportedLikes']==3 and r['benchmark']['visible_er'] is None
  assert r['metricsCaveat']
assert 'CmD-QnWOTSA' in lookup['DeXEiZTTGWl']['relatedSourceIds']
assert 'CmD-QnWOTSA' in lookup['DeFKrBSyYRJ']['relatedSourceIds']
assert len([r for r in rows if r['id']=='Dd8J1LcSaTP'])==1
assert len([r for r in rows if r['id']=='DeICJ7cTS--'])==1
assert '<option value="seeds">' in page and "get('review')==='seeds'" in page
print('PASS: owner seeds, sampled motion, uncertain engagement, deduplication and source links.')

# W002 preserves the complete source library and separates proposals from production.
assert len(rows)==audit["archived_total"] and len(eligible)==audit["eligible_count"]
assert set(audit['weekly_batch_ids'])=={'DfKErm-MuAR','DfF4ncwMGAG','Dez7qxrsRNi','bOEUyr63h_k'}
for id in audit['weekly_batch_ids']:
 r=lookup[id]
 assert r['weeklyBatch']=='W002' and r['selectedWeek']==2
 assert (r['productionState']=='approved_scheduled' and r['producedWeek']==4 and r['publishedWeek'] is None) if id=='DfF4ncwMGAG' else (r['productionState']=='proposed' and r['producedWeek'] is None and r['publishedWeek'] is None)
 assert r['weeklyIdea']['example'] and r['weeklyIdea']['measure'] and r['weeklyIdea']['duplicateReview']
 assert r['teachingEligible'] and r['contentLanguage']=='en' and r['visibleEligible']
assert len([x for x in registry['ideas'] if x['selected_week']==2])==4
assert next(x for x in registry['weeks'] if x['number']==2)['period_start']=='2026-11-01'
assert lookup['bOEUyr63h_k']['published'].startswith('2022') and lookup['bOEUyr63h_k']['older']
assert '<option value="w002">' in page and "get('review')==='w002'" in page
assert 'id="week-1"' in page and 'id="week-2"' in page
for r in rows[:91]:
 assert any(o['at'].startswith('2026-11-01') for o in r['metricObservations']) and r['metricsRefreshNote']
 if r['latestMetricReview']=='refreshed':assert r['capturedAt']==r['metricObservations'][-1]['at']
print('PASS: W002 proposal provenance, archive reuse, all91 saved-ID observations and hidden records.')

# W003 distinguishes comparative engagement from useful visual inspiration.
assert len(rows)==audit['archived_total'] and len(eligible)==audit['eligible_count']
assert len([r for r in rows if r.get('weeklyBatch')=='W003'])==2
assert set(audit['week_3_ids'])=={'DfSbF3njB1z','DfXqH7bK9gy'}
assert len([x for x in registry['ideas'] if x['selected_week']==3])==2
for id in audit['week_3_ids']:
 r=lookup[id];q=r['quality_assessment']
 assert r['selectedWeek']==3 and r['weeklyBatch']=='W003' and r['productionState']=='proposed'
 assert r['producedWeek'] is None and r['publishedWeek'] is None
 assert r['contentLanguage']=='en' and r['teachingEligible'] and r['animationVerified']
 assert r['visualSampleSeconds']==[3,18,32,50]
 assert r['weeklyIdea']['factCheckLinks'] and r['weeklyIdea']['duplicateReview'] and r['weeklyIdea']['measure']
 assert q['fit_status']=='fits_client' and q['observed_at']=='2026-11-08'
 if q['status']=='strong_candidate':
  p=q['peers'];assert len(p)>=5 and all(x['id']!=id and x['creator']==r['author'] and x['observed_at']==q['observed_at'] for x in p)
  o=next(x for x in r['metricObservations'] if x['at']=='2026-11-08');assert q['metric_snapshot']==o['likes']+o['comments']
  assert q['metric_snapshot']>=2*statistics.median(x['metric_value'] for x in p)
assert lookup['DfSbF3njB1z']['quality_assessment']['status']=='strong_candidate'
assert lookup['DfXqH7bK9gy']['quality_assessment']['status']=='visual_reference'
for r in rows[:94]:assert any(o['at']=='2026-11-08' for o in r['metricObservations']) and r['metricsRefreshNote']
assert 'id="week-2-section"' in page and 'id="week-3"' in page and "get('review')==='w003'" in page
print('PASS: W003 proposal-only status, engagement evidence, English teaching, preservation and dated refresh.')

# W004 appends useful English teaching references without claiming broad reach.
assert len(rows)==audit['archived_total'] and len(eligible)==audit['eligible_count']
assert set(audit['week_4_ids'])=={'DfuzRgmqQ2w','Dft23Hms9xI'}
assert len([x for x in registry['ideas'] if x['selected_week']==4])>=2
assert next(x for x in registry['weeks'] if x['number']==4)['period_start']=='2026-11-15'
for id in audit['week_4_ids']:
 r=lookup[id]
 assert r['weeklyBatch']=='W004' and r['selectedWeek']==4 and r['productionState']=='proposed'
 assert r['producedWeek'] is None and r['publishedWeek'] is None
 assert r['teachingEligible'] and r['contentLanguage']=='en' and r['visibleEligible']
 assert r['visualSampleSeconds'] and r['weeklyIdea']['factCheckLinks'] and r['weeklyIdea']['measure']
 assert r['quality_assessment']['status']=='visual_reference'
 assert any(o['at']=='2026-11-15' for o in r['metricObservations'])
for r in rows[:96]:
 assert any(o['at']=='2026-11-15' for o in r['metricObservations'])
 assert r['metricsRefreshNote']
assert 'id="week-3-section"' in page and 'id="week-4"' in page
assert "get('review')==='w004'" in page and '<option value="w004">' in page
print('PASS: W004 preservation, English teaching, limited reach, dated refresh and proposal-only states.')

# Targeted source expansion18November preserves all earlier source and idea records.
assert len(rows)>=103 and len(eligible)>=76
added={'DfvWPhWI4Sz','Dfp2HSAIQ03','DfxFZtvsBJG','DfpQxlxOK90','Dfm990dBBih'}
assert set(audit['source_review_batches']['SOURCE-20261118'])==added
newids={'BR-W004-03','BR-W004-04','BR-W004-05'}
assert {x['idea_id'] for x in registry['ideas'] if x['idea_id'] in newids}==newids
assert len([x for x in registry['ideas'] if x['selected_week']==4])==5
for id in added:
 r=lookup[id]
 assert r['contentLanguage']=='en' and r['teachingEligible'] and r['visibleEligible']
 assert r['sourceBatch']=='SOURCE-20261118' and r['producedWeek'] is None and r['publishedWeek'] is None
 assert any(o['at']=='2026-11-18' for o in r['metricObservations']) and r['visualSampleSeconds'] and r['weeklyIdea']['factCheckLinks']
 if r['ideaId']:assert r['productionState']=='proposed'
 else:assert r['productionState']=='reference_only'
for id in ['DfxFZtvsBJG','DfpQxlxOK90']:
 assert lookup[id]['comments'] is None and lookup[id]['rawReportedComments']==0
 assert lookup[id]['uiObservedComments']>0
for id in ['DfvWPhWI4Sz','Dfp2HSAIQ03']:
 q=lookup[id]['quality_assessment']
 assert q['status']=='strong_candidate' and len(q['peers'])>=5
 assert q['metric_snapshot']>=2*statistics.median(x['metric_value'] for x in q['peers'])
assert 'id="source-review-18"' in page and '<option value="sources18">' in page
print('PASS: targeted18November additions, comparative evidence, unknown conflicting counts and proposal-only states.')

# W005 uses relative views as descriptive evidence, without a fixed reach or ratio gate.
assert len(rows)==110 and len(eligible)==83
assert len(registry['ideas'])==21 and len([x for x in registry['ideas'] if x['selected_week']==5])==5
assert set(audit['week_5_ids'])=={'DfwVVFiNpZf','DfzDVl6oTYY','Df2CqH6veLZ','DgAgJPJhj-K'}
for id in audit['week_5_ids']:
 r=lookup[id];q=r['quality_assessment'];peers=q['peers']
 assert r['weeklyBatch']=='W005' and r['selectedWeek']==5 and r['productionState']=='proposed'
 assert r['producedWeek'] is None and r['publishedWeek'] is None
 assert r['contentLanguage']=='en' and r['teachingEligible'] and r['visibleEligible']
 assert r['animationVerified'] and r['visualSampleSeconds'] and r['weeklyIdea']['factCheckLinks']
 assert q['candidate_excluded'] and len(peers)==q['sample_n'] and all(x['id']!=id and x['creator']==r['author'] and x['platform']=='instagram' for x in peers)
 assert statistics.median(x['views'] for x in peers)==q['median_views']
 assert statistics.mean(x['views'] for x in peers)==q['mean_views']
 assert r['weeklyIdea']['duplicateReview'] and r['weeklyIdea']['measure'] and len(r['hooks'])>=3
assert lookup['Df2CqH6veLZ']['quality_assessment']['sample_n']==1
assert 'id="week-5"' in page and '<option value="w005">' in page and "get('review')==='w005'" in page
assert 'id="source-review-18-section"' in page
assert 'id="photography-objects"' in page and 'id="photography-fashion-model"' in page
assert next(x for x in registry['ideas'] if x['idea_id']=='BR-W002-02')['produced_week']==4
assert lookup['DfF4ncwMGAG']['productionState']=='approved_scheduled' and lookup['DfF4ncwMGAG']['publishedWeek'] is None
assert lookup['DefpY3hou6y']['productionState']!='approved_scheduled'
tips=(root/'docs/tips.html').read_text(encoding='utf-8')
t=json.loads(re.search(r'<script[^>]*id="tips-methods-data"[^>]*>(.*?)</script>',tips,re.S).group(1))
assert len(t['methods'])==16 and len({m['method_id'] for m in t['methods']})==16
assert t['inventory']['posts']==254 and t['inventory']['videos']==249 and t['inventory']['transcripts_reviewed']==14
assert t['inventory']['inventory_only_videos']==235 and t['inventory']['visual_review_pending']==0
for m in t['methods']:
 assert m['experiment']['status']=='not_tested'
 if m['method_id'] in ['TIP-003','TIP-004','TIP-009']:
  assert m['experiment']['trials'][0]['trial_id']=='BR-EXP-GIFT-TIP004-20261120'
  assert m['experiment']['trials'][0]['results'] is None
  assert m['experiment']['phase']=='approved_scheduled_unmeasured'
assert 'DfamuA6xFRK' in next(m for m in t['methods'] if m['method_id']=='TIP-006')['source_ids']
assert '<meta name="robots" content="noindex' in tips
print('PASS: W005 relative-view evidence, preservation, independent production stages and Tips trial history.')

# Acuisight24November append keeps prior weekly selections and independent stages.
assert set(audit["source_review_batches"]["ACUISIGHT-20261124"])=={"DgFRh8mtbUm","Df2Q8RwtM4m","Df9jWclt--z"}
for source in audit["source_review_batches"]["ACUISIGHT-20261124"]:
 r=lookup[source]
 assert r["contentLanguage"]=="en" and r["teachingEligible"] and r["visibleEligible"]
 assert r["producedWeek"] is None and r["publishedWeek"] is None
assert lookup["DgFRh8mtbUm"]["productionState"]=="proposed"
assert all(lookup[x]["productionState"]=="reference_only" for x in ["Df2Q8RwtM4m","Df9jWclt--z"])
assert "id=\"acuisight-ideas\"" in page
print("PASS: Acuisight source review and support-only deduplication.")
