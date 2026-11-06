"""Validate current V0.2 tables and file integrity; no historical truth inference.

Run from any directory: python3 scripts/validate_archive_v02.py
The PR #1 validator and its frozen fixture remain historical closeout checks;
this validator allows reviewed additions without rewriting that fixture.
"""
from pathlib import Path
import csv,hashlib,json,re,sys

ROOT=Path(__file__).resolve().parents[1]
errors=[];checks=0;tables={}
def check(value,msg):
 global checks
 checks+=1
 if not value: errors.append(msg)
def csvread(p):
 with p.open(encoding='utf-8-sig',newline='') as f:
  rr=list(csv.reader(f))
 check(bool(rr),str(p)+' empty CSV')
 if not rr:return []
 check(len(rr[0])==len(set(rr[0])),str(p)+' duplicate columns')
 for i,r in enumerate(rr[1:],2):check(len(r)==len(rr[0]),str(p)+f' row {i} column count')
 return [dict(zip(rr[0],r)) for r in rr[1:]]

for p in sorted(ROOT.rglob('*.csv')):tables[p.relative_to(ROOT).as_posix()]=csvread(p)
for p in sorted(ROOT.rglob('*.json')):
 try:json.loads(p.read_text(encoding='utf-8-sig'));check(True,'')
 except Exception as e:check(False,f'{p.relative_to(ROOT)} JSON: {e}')

sources=tables['sources/SOURCE_REGISTER.csv'];byid={r['source_id']:r for r in sources}
check(len(byid)==len(sources),'duplicate source IDs')
check(len(sources)>=143,'lost baseline sources')
for r in sources:
 check(bool(re.fullmatch(r'SRC-\d{4}',r['source_id'])),'bad source ID '+r['source_id'])
 check(r['source_nature'] in {'P','S','T','unknown'},'bad nature '+r['source_id'])
fixture=json.loads((ROOT/'scripts/fixtures/source_nature_closeout_baseline.json').read_text())
for sid,nature in fixture['original_source_nature'].items():
 check(sid in byid,'missing baseline source '+sid)
 if nature=='U':check(byid.get(sid,{}).get('source_nature_original')=='U','lost original U '+sid)
details=json.loads((ROOT/'sources/SOURCE_DETAILS.json').read_text())
detailrows=details['records'];check(details['count']==len(detailrows)==len(sources),'detail count mismatch')
check({r['source_id'] for r in detailrows}==set(byid),'details/register IDs mismatch')
for name,rr in tables.items():
 for i,r in enumerate(rr,2):
  for k,v in r.items():
   if k in {'source_ids','canonical_source_ids','historical_source_ids','current_read_source_ids','from_source_id','to_source_id'}:
    for sid in re.findall(r'SRC-\d{4}',v):check(sid in byid,f'{name}:{i} missing source {sid}')
   if 'source' in k.lower():check(not re.search(r'NEW-(?:AT|TL|INT|MIL|TR|EV)[-\w]*',v),f'{name}:{i} provisional source in {k}')

q=tables.get('unresolved/OPEN_QUESTIONS.csv',[])
expected={*(f'TL-U{i:02}' for i in range(1,10)),*(f'B-U{i:02}' for i in range(1,9)),*(f'TRU{i:02}' for i in range(1,8)),*(f'INT-U{i:02}' for i in range(1,6)),*(f'AT-U{i:02}' for i in range(1,6))}
check(len(q)==34,'question count is not 34')
check({r.get('original_id') for r in q}==expected,'question IDs changed')
for r in q:
 check(bool(r.get('original_question')),'missing original question '+r.get('original_id',''))
 check(bool(r.get('task002_original_status')),'missing original status '+r.get('original_id',''))
 if r.get('resolved')=='true':check(bool(r.get('resolution_scope')) and bool(r.get('new_evidence_this_round')),'unsupported closure '+r.get('original_id',''))

timeline=tables.get('timeline/南京保卫战统一时间线.csv',[])
check(bool(timeline),'missing timeline events')
check(len({r['event_id'] for r in timeline})==len(timeline),'duplicate event IDs')
required=['date_start','date_end','time_precision','location','actors','event_description','claim_status','source_ids','citation_locator','limitations','counterevidence','source_family','last_reviewed']
for r in timeline:
 for k in required:check(k in r,'timeline missing field '+k)
 check(bool(r.get('source_ids')) and bool(r.get('citation_locator')),'event lacks source/locator '+r['event_id'])
 for k in ['date_start','date_end']:
  d=r.get(k,'')
  if d:check('1937-11-19'<=d[:10]<='1937-12-31','out of range '+r['event_id']+':'+d)
 check(r.get('record_role') not in {'F','fiction'},'F in historical timeline '+r['event_id'])
js=json.loads((ROOT/'timeline/NANJING_1937_TIMELINE.json').read_text())
if isinstance(js,dict):js=js.get('events',js.get('records',[]))
check({r['event_id'] for r in js}=={r['event_id'] for r in timeline},'timeline CSV/JSON IDs differ')

ff=tables.get('fiction-boundary/FICTION_EVENTS.csv',[]);fids={r['fiction_event_id'] for r in ff}
check(len(ff)==len(fids)==9,'F event count/identity')
for r in ff:
 check(r['record_role']=='F','fiction role missing')
 for dep in filter(None,r['dependencies'].split(';')):check(dep in fids and dep<r['fiction_event_id'],'bad F dependency')

for p in ROOT.rglob('*.md'):
 for match in re.finditer(r'(?<!!)\[[^\]\n]+\]\(([^\)]+)\)',p.read_text()):
  link=match.group(1).split('#')[0].strip('<>')
  if not link or re.match(r'^[a-zA-Z][\w+.-]*:',link):continue
  check((p.parent/link).exists(),f'broken relative link {p.relative_to(ROOT)}: {link}')

manifest=ROOT/'SHA256SUMS.txt';seen=set()
for line in manifest.read_text().splitlines():
 if not line:continue
 digest,rel=line.split('  ',1);p=ROOT/rel
 check(rel not in seen,'duplicate manifest '+rel);seen.add(rel)
 check(p.is_file() and ROOT in p.resolve().parents,'missing/unsafe manifest '+rel)
 if p.is_file():check(hashlib.sha256(p.read_bytes()).hexdigest()==digest,'hash mismatch '+rel)
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p!=manifest and '__pycache__' not in p.parts}
check(seen==actual,'manifest coverage differs')
result={'checks':checks,'errors':errors,'passed':not errors,'sources':len(sources),'timeline_events':len(timeline),'questions':len(q),'fiction_events':len(ff),'files':len(actual)+1}
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(bool(errors))
