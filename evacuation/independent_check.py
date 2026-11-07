"""Read-only independent evaluation of saved OOXML and separate exact-rational flow model."""
from pathlib import Path
import csv,datetime as dt,hashlib,importlib.util,json,math,re,shutil,sys,zipfile,copy
import xml.etree.ElementTree as ET
import os,tempfile
from fractions import Fraction as Q
sys.dont_write_bytecode=True
SRC=Path(os.environ.get('EVAC_MODEL_DIR',str(Path(__file__).resolve().parent)))
_TEMP=tempfile.TemporaryDirectory(prefix='jinling-evac-qa-')
OUT=Path(os.environ.get('EVAC_QA_OUTPUT',_TEMP.name))
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def colnum(s):
 n=0
 for c in s:n=n*26+ord(c)-64
 return n
def colstr(n):
 s=''
 while n:n,r=divmod(n-1,26);s=chr(65+r)+s
 return s
def refs(a,b):
 ca,ra=re.fullmatch(r'([A-Z]+)(\d+)',a).groups();cb,rb=re.fullmatch(r'([A-Z]+)(\d+)',b).groups()
 return [f'{colstr(c)}{r}' for r in range(int(ra),int(rb)+1) for c in range(colnum(ca),colnum(cb)+1)]
TOKEN=re.compile(r'''\s*(?:(?P<ref>(?:'(?:[^']|'')+'!)?\$?[A-Z]+\$?\d+(?::\$?[A-Z]+\$?\d+)?)|(?P<string>"(?:[^"]|"")*")|(?P<num>\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)|(?P<name>[A-Z_][A-Z_0-9.]*)|(?P<op><=|>=|<>|[+*/(),=<>-]))''')
class Parser:
 def __init__(self,s):
  self.ts=[];pos=0
  while pos<len(s):
   m=TOKEN.match(s,pos)
   if not m:raise ValueError(('unparsed',s[pos:]))
   self.ts.append((m.lastgroup,m.group(m.lastgroup)));pos=m.end()
  self.ts.append(('end',''));self.i=0
 def peek(self):return self.ts[self.i][1]
 def pop(self):x=self.ts[self.i];self.i+=1;return x
 def parse(self,level=0):
  if level==3:
   typ,val=self.pop()
   if val=='-':return ('neg',self.parse(3))
   if val=='(':
    x=self.parse();assert self.pop()[1]==')';return x
   if typ=='num':return ('lit',float(val))
   if typ=='string':return ('lit',val[1:-1].replace('""','"'))
   if typ=='ref':return ('ref',val.replace('$',''))
   if typ=='name':
    if val in ('TRUE','FALSE') and self.peek()!='(':return ('lit',val=='TRUE')
    assert self.pop()[1]=='(';args=[]
    if self.peek()!=')':
     args.append(self.parse())
     while self.peek()==',':self.pop();args.append(self.parse())
    assert self.pop()[1]==')';return ('func',val,args)
   raise ValueError((typ,val))
  node=self.parse(level+1);ops=[('=','<>','<','>','<=','>='),('+','-'),('*','/')][level]
  while self.peek() in ops:op=self.pop()[1];node=('op',op,node,self.parse(level+1))
  return node
def flat(x):
 if isinstance(x,list):
  for y in x:yield from flat(y)
 else:yield x
def number(x):return x is not None and isinstance(x,(int,float)) and not isinstance(x,bool)
def num(x):return 0 if x is None or x=='' else x
class Book:
 def __init__(self,p):
  self.cells={};self.formula_count=0;self.errors=[];self.asts={};self.overrides={};self.cache={};self.active=set()
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   ss=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
   names=[s.attrib['name'] for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets',NS)]
   for i,name in enumerate(names,1):
    for c in ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')).findall('.//m:c',NS):
     address=c.attrib['r'];t=c.attrib.get('t');v=c.findtext('m:v',None,NS);f=c.findtext('m:f',None,NS)
     if t=='e':self.errors.append((name,address,v))
     if t=='s':v=ss[int(v)] if v is not None else None
     elif t=='b':v=bool(int(v))
     elif t not in ('str','inlineStr') and v is not None:v=float(v)
     if t=='inlineStr':v=''.join(c.find('m:is',NS).itertext())
     self.cells[name,address]={'f':f,'v':v}
     if f:
      p=Parser(f);ast=p.parse();assert p.peek()=='';self.asts[name,address]=ast;self.formula_count+=1
 def reset(self,changes=None):self.overrides=changes or {};self.cache={};self.active=set()
 def cell(self,s,a):
  key=(s,a)
  if key in self.overrides:return self.overrides[key]
  if key in self.cache:return self.cache[key]
  if key in self.active:raise ValueError('cycle '+str(key))
  self.active.add(key);c=self.cells.get(key,{'v':None,'f':None})
  value=self.eval(self.asts[key],s) if c['f'] else c['v'];self.cache[key]=value;self.active.remove(key);return value
 def eval(self,x,s):
  typ=x[0]
  if typ=='lit':return x[1]
  if typ=='neg':return -num(self.eval(x[1],s))
  if typ=='ref':
   ref=x[1]
   if '!' in ref:s,ref=ref.split('!');s=s[1:-1].replace("''", "'")
   if ':' in ref:a,b=ref.split(':');return [self.cell(s,r) for r in refs(a,b)]
   return self.cell(s,ref)
  if typ=='op':
   op=x[1];a=num(self.eval(x[2],s));b=num(self.eval(x[3],s))
   return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b,'=':lambda:a==b,'<>':lambda:a!=b,'<':lambda:a<b,'>':lambda:a>b,'<=':lambda:a<=b,'>=':lambda:a>=b}[op]()
  name,args=x[1:]
  if name=='IF':return self.eval(args[1] if self.eval(args[0],s) else args[2],s)
  values=[self.eval(a,s) for a in args];allv=list(flat(values));nums=[v for v in allv if number(v)]
  if name=='AND':return all(allv)
  if name=='OR':return any(allv)
  if name=='COUNT':return len(nums)
  if name=='SUM':return sum(nums)
  if name=='MIN':return min(nums,default=0)
  if name=='MAX':return max(nums,default=0)
  if name=='INT':return math.floor(num(values[0]))
  if name=='ISNUMBER':return number(values[0])
  if name=='ROUNDUP':return math.ceil(abs(num(values[0]))*10**values[1])/10**values[1]*(1 if values[0]>=0 else -1)
  if name=='DATE':return (dt.date(*(int(v) for v in values))-dt.date(1899,12,30)).days
  raise ValueError('unknown function '+name)

def exact_model(data,case):
 # Separately follows documented resource and population ledgers, using rationals.
 p={r['key']:Q(str(r['value'])) for r in data['common_parameters']};p.update({r['key']:Q(str(r['values'][case])) for r in data['organization_parameters']})
 floor=lambda q:q.numerator//q.denominator if isinstance(q,Q) else math.floor(q)
 ceiling=lambda q:-floor(-q)
 waiting=int(p['demand']);ships=int(p['boats']);far=0;pending_land=pending_bank=complete=departures=0;daily=[]
 for day in range(43):
  land=p['start_day']<=day<=p['land_end'];water=p['start_day']<=day<=p['boat_end']
  per_rail=floor(floor(p['rail_seats']*p['load'])*p['civil_share'])
  per_car=floor(floor(p['car_seats']*p['load'])*p['civil_share'])
  per_boat_load=floor(p['boat_seats']*p['load']);per_boat=floor(per_boat_load*p['civil_share'])
  car_trips=floor(p['road_work']*p['weather']/(p['road_out']+p['road_return']+p['road_handling'])) if land else 0
  boat_trips=0
  if water:
   if p['return_enabled']:boat_trips=floor(p['boat_work']*p['weather']/(p['boat_out']+p['boat_return']+p['boat_handling']))
   else:boat_trips=int(p['boat_work']*p['weather']>=p['boat_out']+p['boat_handling'])
  ship_fleet=min(ships,int(p['boat_dispatch']));available_voyages=ship_fleet*boat_trips
  if per_boat_load:available_voyages=min(available_voyages,floor(p['dock_cap']/per_boat_load))
  else:available_voyages=0
  capacities=[floor(p['rail_slots']*p['weather'])*per_rail*land,floor(p['cars']*p['fuel'])*car_trips*per_car,available_voyages*per_boat,floor(floor(p['walk_cap']*p['weather'])*p['walk_org'])*land]
  allocations=[];gate=int(p['gate_cap'])
  for cap in capacities:
   chosen=min(int(cap),gate,waiting);allocations.append(chosen);gate-=chosen;waiting-=chosen
  train,car,boat,walk=allocations;sent=sum(allocations);departures+=sent
  actual_trips=ceiling(Q(boat,per_boat)) if boat and per_boat else 0;used=ceiling(Q(actual_trips,boat_trips)) if actual_trips else 0
  assert used<=ships and actual_trips<=available_voyages
  if not p['return_enabled']:ships-=used;far+=used
  onward=min(floor(boat*p['handoff']),int(p['handoff_cap']));landdone=floor(walk*p['walk_finish']);done=train+car+onward+landdone
  complete+=done;pending_bank+=boat-onward;pending_land+=walk-landdone
  assert p['demand']==waiting+complete+pending_bank+pending_land
  assert ships+far==p['boats']
  daily.append({'departures':sent,'chain_completed':done,'completed_cumulative':complete,'pending_walk':pending_land,'pending_shore':pending_bank,'demand_end':waiting,'boat_origin_end':ships,'boat_far_shore_end':far,'boats_used':used,'boat_voyages':actual_trips,'rail_departures':train,'car_departures':car,'boat_departures':boat,'walk_departures':walk})
 return dict(departures=departures,conditional_chain_completed=complete,pending_walk=pending_land,pending_shore=pending_bank,origin_waiting=waiting),daily

def main():
 OUT.mkdir(exist_ok=True,parents=True);checks=[];issues=[]
 def ck(name,ok,detail=None):
  checks.append({'name':name,'passed':bool(ok),'detail':detail})
  if not ok:issues.append(name)
 inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()}
 data=json.loads((SRC/'model_data.json').read_text());b=Book(SRC/'evacuation_model.xlsx')
 ck('OOXML ZIP integrity and error cells',not b.errors,{'formula_count':b.formula_count,'errors':b.errors})
 # All saved formulas evaluated independently against exported caches.
 mism=[]
 for key in b.asts:
  v=b.cell(*key);cached=b.cells[key]['v']
  if v!=cached:mism.append({'sheet':key[0],'cell':key[1],'calculated':v,'cached':cached})
 ck('all saved formula caches independently calculated',not mism,{'compared':len(b.asts),'mismatches':mism[:12]})
 spec=importlib.util.spec_from_file_location('ev_recalc',SRC/'recalculate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 pr={r['key']:i+9 for i,r in enumerate(data['common_parameters'])};org={r['key']:i+38 for i,r in enumerate(data['organization_parameters'])}
 expected_keys=['land_open','water_open','rail_services','car_ready','car_cycles','boat_cycles','boat_origin_start','boat_loaded_seats','boat_civil_seats','boat_voyage_offer','rail_offer','car_offer','boat_offer','walk_offer','demand_start','rail_departures','car_departures','boat_departures','walk_departures','departures','boat_voyages','boats_used','boats_returned','boat_origin_end','boat_far_shore_end','boat_onward','walk_completed','chain_completed','completed_cumulative','pending_walk','pending_shore','demand_end','people_balance','boat_balance']
 summaries=[]
 for i,case in enumerate(['EV-B-C01','EV-B-C02','EV-B-C03'],1):
  exact,ed=exact_model(data,case);orig=m.calculate(data,case)
  ck(case+' exact-rational independent ledgers',all(orig['totals'][k]==v for k,v in exact.items()) and all(all(orig['daily'][j][k]==v for k,v in r.items()) for j,r in enumerate(ed)),exact)
  b.reset({('B条件输入','C3'):i});diff=[]
  for day in range(43):
   for col,k in enumerate(expected_keys,3):
    got=b.cell('逐日资源与人群',colstr(col)+str(day+6));want=orig['daily'][day][k]
    if got!=want:diff.append((day,k,got,want))
  ck(case+' exported formula matrix',not diff,{'cells':43*34,'mismatch':diff[:10]})
  ck(case+' no pre-activation throughput',all(r['departures']==0 for r in orig['daily'][:8]) and all(r['departures']==0 for r in orig['daily'][19:]))
  ck(case+' outputs retain historical unknown',all(orig['totals'][k] is None for k in ['historical_actual_transported','historical_arrived_safely','historical_saved']))
  summaries.append(exact)
 # All independent exact-rational sensitivity comparisons against saved CSV.
 sr=list(csv.DictReader((SRC/'sensitivity.csv').open(encoding='utf-8-sig')));sensdiff=[]
 for r in sr:
  changed=m.mutate(data,r['changed_parameter'],float(r['changed_value']));exact,_=exact_model(changed,'EV-B-C02');b.reset({('B条件输入','C3'):2,('B条件输入',('C'+str(pr[r['changed_parameter']]) if r['changed_parameter'] in pr else 'E'+str(org[r['changed_parameter']]))):float(r['changed_value'])})
  vals=(exact['departures'],exact['conditional_chain_completed'],b.cell('结果与口径','B7'),b.cell('结果与口径','B8'))
  if vals!=(int(r['departures']),int(r['conditional_chain_completed']),int(r['departures']),int(r['conditional_chain_completed'])):sensdiff.append((r['changed_parameter'],r['changed_value'],vals))
 ck('23 sensitivity exact model plus exported formulas',not sensdiff,{'cases':len(sr),'mismatch':sensdiff})
 # Invalid inputs, valid zero and case-local blanks tested from actual formula graph.
 workbook_cases=[('zero demand',{'C9':0},0),('zero fleet',{'C20':0},None),('blank demand',{'C9':None},''),('negative boats',{'C20':-1},''),('fractional fleet',{'C20':1.5},''),('bad ratio',{'C27':1.01},''),('zero window',{'C27':0},0),('bad date',{'C31':19,'C33':18},''),('invalid selector',{'C3':4},''),('unselected blank',{'C3':2,'D38':None},36598),('selected blank',{'C3':1,'D38':None},''),('valid selected zero',{'C3':1,'D38':0},None)]
 for name,ov,expected in workbook_cases:
  b.reset({('B条件输入','C3'):2}|{('B条件输入',k):v for k,v in ov.items()});got=b.cell('结果与口径','B7');ck('OOXML '+name,got==expected if expected is not None else number(got),{'value':got})
 b.reset({('B条件输入','C12'):41});ck('comparison snapshot invalidates on input edit',b.cell('三案与敏感性','C3')=='参数已改变：请刷新')
 b.reset({('B条件输入','C3'):3});ck('comparison snapshot independent of selector',b.cell('三案与敏感性','C3')=='参数与快照一致')
 for key,val in [('boats',None),('boats',-1),('boats',.5),('weather',1.5),('boat_out',0),('return_enabled',3),('demand',True),('start_day',43)]:
  try:m.calculate(m.mutate(data,key,val));ok=False
  except (ValueError,TypeError):ok=True
  ck('Python rejects '+key+' '+repr(val),ok)
 # Portability: run original standalone script in isolated directory, no research tree imports.
 isolated=OUT/'standalone';isolated.mkdir(exist_ok=True)
 for fn in ['recalculate.py','model_data.json']:shutil.copy2(SRC/fn,isolated/fn)
 import subprocess
 p=subprocess.run([sys.executable,str(isolated/'recalculate.py')],capture_output=True,text=True)
 ck('standalone standard-library recalculation',p.returncode==0,{'returncode':p.returncode,'stderr':p.stderr})
 ck('standalone result identical',json.loads((isolated/'python_results.json').read_text())==json.loads((SRC/'python_results.json').read_text()))
 ck('F numeric overrides remain unset',data['fiction_approved_numeric_overrides'] is None)
 ck('all numeric parameters explicitly I',all(r['record_role']=='I' for r in data['common_parameters']+data['organization_parameters']))
 ck('A evidence sheet has no model formulas',not any(s=='A历史证据' for s,a in b.asts))
 ck('all source/model input files unchanged',inputs=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()})
 result={'scope':'Read-only independent model audit','tested_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'input_sha256':inputs,'checks':checks,'failed':issues,'passed':not issues,'case_totals':summaries,'xlsx_formula_engine':'Independent limited interpreter of saved OOXML formula graph; not Excel native','independent_calculation':'Separate exact-rational fleet/person ledgers','native_excel_tested':False,'limitations':['Population and resource parameters are I assumptions, not historical observations.','Waiting boat/foot cohorts are intentionally not cleared on subsequent days; this suppresses completion and is documented.','All routes have different modeled endpoints; no comparable safe-arrival/ultimate-survival meaning.','Original builder promises artifact-tool checks; this independent audit verifies exported formulas mathematically, not native Microsoft Excel rendering/recalculation.']}
 (OUT/'evac_independent_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'checks':len(checks),'failed':issues,'formula_count':b.formula_count,'case_totals':summaries},ensure_ascii=False))
if __name__=='__main__':main()
