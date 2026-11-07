"""EV-B-003-01. Pure Python, deterministic conditional model; no historical outcome estimate."""
import csv, copy, datetime as dt, hashlib, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END = dt.date(1937,11,19), dt.date(1937,12,31)

def validate(data, scenario):
    if scenario not in ('EV-B-C01','EV-B-C02','EV-B-C03'):
        raise ValueError('invalid scenario')
    p={x['key']:x['value'] for x in data['common_parameters']}
    o={x['key']:x['values'][scenario] for x in data['organization_parameters']}
    required={'demand','rail_slots','rail_seats','cars','car_seats','road_work','road_out','road_return','fuel','walk_cap','walk_finish','boats','boat_seats','boat_dispatch','boat_out','boat_return','boat_work','return_enabled','weather','dock_cap','handoff_cap','gate_cap','start_day','land_end','boat_end'}
    if set(p)!=required or set(o)!={'load','civil_share','road_handling','boat_handling','walk_org','handoff'}:
        raise ValueError('missing or unexpected input')
    for k,v in (p|o).items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:
            raise ValueError('invalid nonnegative input: '+k)
    for k in ('fuel','walk_finish','weather'):
        if p[k]>1: raise ValueError('ratio exceeds one: '+k)
    for k in ('load','civil_share','walk_org','handoff'):
        if o[k]>1: raise ValueError('ratio exceeds one: '+k)
    for k in ('demand','rail_slots','rail_seats','cars','car_seats','walk_cap','boats','boat_seats','boat_dispatch','dock_cap','handoff_cap','gate_cap','start_day','land_end','boat_end'):
        if int(p[k])!=p[k]: raise ValueError('integer required: '+k)
    if p['return_enabled'] not in (0,1): raise ValueError('return flag must be 0 or 1')
    if p['road_out']+p['road_return']<=0 or p['boat_out']<=0 or p['boat_return']<=0:
        raise ValueError('travel time must be positive')
    if not 0<=p['start_day']<=p['land_end']<=42 or not p['start_day']<=p['boat_end']<=42:
        raise ValueError('calendar bounds/order')
    return p,o

def calculate(data, scenario='EV-B-C02'):
    p,o=validate(data,scenario)
    remaining=int(p['demand']); origin=int(p['boats']); pending_walk=pending_shore=completed=0
    rows=[]
    for i in range(43):
        land=int(p['start_day']<=i<=p['land_end']); water=int(p['start_day']<=i<=p['boat_end'])
        rail_services=math.floor(p['rail_slots']*p['weather'])*land
        car_ready=math.floor(p['cars']*p['fuel'])
        car_cycles=math.floor(p['road_work']*p['weather']/(p['road_out']+p['road_return']+o['road_handling']))*land
        boat_cycles=(math.floor(p['boat_work']*p['weather']/(p['boat_out']+p['boat_return']+o['boat_handling'])) if p['return_enabled'] else int(p['boat_work']*p['weather']>=p['boat_out']+o['boat_handling']))*water
        boat_load=math.floor(p['boat_seats']*o['load']); boat_civil=math.floor(boat_load*o['civil_share'])
        rail_cap=rail_services*math.floor(math.floor(p['rail_seats']*o['load'])*o['civil_share'])
        car_cap=car_ready*car_cycles*math.floor(math.floor(p['car_seats']*o['load'])*o['civil_share'])
        boat_voyages=min(min(origin,p['boat_dispatch'])*boat_cycles, math.floor(p['dock_cap']/boat_load) if boat_load else 0)
        boat_cap=boat_voyages*boat_civil
        walk_cap=math.floor(math.floor(p['walk_cap']*p['weather'])*o['walk_org'])*land
        day_start=remaining; gate=p['gate_cap']; assigned=[]
        for capacity in (rail_cap,car_cap,boat_cap,walk_cap):
            n=min(capacity,remaining,gate); assigned.append(n); remaining-=n; gate-=n
        rail,car,boat,walk=assigned
        voyages=math.ceil(boat/boat_civil) if boat_civil else 0
        used=math.ceil(voyages/boat_cycles) if boat_cycles else 0
        returned=used*p['return_enabled']; origin_start=origin; origin=origin-used+returned
        onward=min(math.floor(boat*o['handoff']),p['handoff_cap'])
        walk_done=math.floor(walk*p['walk_finish'])
        pending_walk+=walk-walk_done; pending_shore+=boat-onward
        chain=rail+car+onward+walk_done; completed+=chain
        row=dict(day=i,date=(START+dt.timedelta(days=i)).isoformat(),land_open=land,water_open=water,rail_services=rail_services,car_ready=car_ready,car_cycles=car_cycles,boat_cycles=boat_cycles,boat_origin_start=origin_start,boat_loaded_seats=boat_load,boat_civil_seats=boat_civil,boat_voyage_offer=boat_voyages,rail_offer=rail_cap,car_offer=car_cap,boat_offer=boat_cap,walk_offer=walk_cap,demand_start=day_start,rail_departures=rail,car_departures=car,boat_departures=boat,walk_departures=walk,departures=sum(assigned),boat_voyages=voyages,boats_used=used,boats_returned=returned,boat_origin_end=origin,boat_far_shore_end=p['boats']-origin,boat_onward=onward,walk_completed=walk_done,chain_completed=chain,completed_cumulative=completed,pending_walk=pending_walk,pending_shore=pending_shore,demand_end=remaining,people_balance=p['demand']-remaining-completed-pending_walk-pending_shore,boat_balance=p['boats']-origin-(p['boats']-origin))
        assert row['people_balance']==row['boat_balance']==0
        assert origin>=0 and remaining>=0 and row['departures']<=p['gate_cap']
        assert used<=origin_start and voyages<=boat_voyages
        rows.append(row)
    totals=dict(model_id=data['model_id'],scenario_id=scenario,departures=sum(r['departures'] for r in rows),conditional_chain_completed=completed,pending_walk=pending_walk,pending_shore=pending_shore,origin_waiting=remaining,boats_origin=origin,boats_far_shore=p['boats']-origin,historical_actual_transported=None,historical_arrived_safely=None,historical_saved=None)
    # Nominal first-leg slots, not actual passengers; shared fleet counted once unless a return cycle is assumed.
    days=p['land_end']-p['start_day']+1; waterdays=p['boat_end']-p['start_day']+1
    nominal_road_cycles=math.floor(p['road_work']/(p['road_out']+p['road_return']+o['road_handling']))
    nominal_boat_cycles=math.floor(p['boat_work']/(p['boat_out']+p['boat_return']+o['boat_handling'])) if p['return_enabled'] else int(p['boat_work']>=p['boat_out']+o['boat_handling'])
    nominal_boat_voyages=min(p['boats'],p['boat_dispatch']*waterdays)*nominal_boat_cycles if not p['return_enabled'] else min(p['boats'],p['boat_dispatch'])*nominal_boat_cycles*waterdays
    totals['nominal_first_leg_slots']=days*(p['rail_slots']*p['rail_seats']+p['cars']*p['car_seats']*nominal_road_cycles+p['walk_cap'])+nominal_boat_voyages*p['boat_seats']
    return {'totals':totals,'daily':rows}

def mutate(data,key,value,scenario='EV-B-C02'):
    d=copy.deepcopy(data)
    for item in d['common_parameters']:
        if item['key']==key: item['value']=value; return d
    for item in d['organization_parameters']:
        if item['key']==key: item['values'][scenario]=value; return d
    raise KeyError(key)

def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def test(data):
    checks=[]
    def ok(name,condition):
        assert condition,name; checks.append({'test':name,'passed':True})
    for c in ('EV-B-C01','EV-B-C02','EV-B-C03'):
        x=calculate(data,c);ok(c+' daily conservation',all(r['people_balance']==r['boat_balance']==0 for r in x['daily']))
    bad=[('missing',None),('negative',('boats',-1)),('fractional fleet',('boats',1.2)),('ratio',('weather',1.1)),('zero trip',('boat_out',0)),('invalid return',('return_enabled',2)),('blank',('cars',None)),('infinite',('gate_cap',float('inf'))),('calendar',('land_end',50))]
    for name,change in bad:
        d=copy.deepcopy(data)
        if change: d=mutate(d,*change)
        else:d['common_parameters'].pop()
        try: calculate(d)
        except ValueError: ok('reject '+name,True)
        else:raise AssertionError(name)
    try:calculate(data,'invalid')
    except ValueError:ok('reject invalid scenario',True)
    else:raise AssertionError('invalid scenario accepted')
    zero=calculate(mutate(data,'demand',0));ok('zero demand uses no ships',zero['totals']['boats_origin']==100 and zero['totals']['departures']==0)
    small=calculate(mutate(data,'demand',100));ok('demand capped across days',small['totals']['departures']==100)
    gate=calculate(mutate(data,'gate_cap',1));ok('shared gate capacity',all(r['departures']<=1 for r in gate['daily']))
    ret=calculate(mutate(data,'return_enabled',1));ok('return keeps boats at origin',ret['totals']['boats_origin']==100)
    nofuel=calculate(mutate(data,'fuel',0));ok('no ready cars',sum(r['car_departures'] for r in nofuel['daily'])==0)
    noweather=calculate(mutate(data,'weather',0));ok('no operating window',noweather['totals']['departures']==0)
    walk=calculate(mutate(data,'walk_finish',0));ok('walk pending not lost',walk['totals']['pending_walk']>0 and walk['daily'][-1]['people_balance']==0)
    advance=calculate(mutate(data,'start_day',7));ok('date mutation adds modeled day',advance['totals']['departures']>calculate(data)['totals']['departures'])
    return checks

def main():
    data=json.loads((HERE/'model_data.json').read_text())
    results=[calculate(data,c) for c in ('EV-B-C01','EV-B-C02','EV-B-C03')]
    (HERE/'python_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    write_csv(HERE/'scenario_results.csv',[x['totals'] for x in results])
    write_csv(HERE/'daily_medium.csv',results[1]['daily'])
    sensitivity=[]
    for key,vals in {'road_work':[600,660,1200],'gate_cap':[2000,5000,8000],'handoff_cap':[50,200,500],'civil_share':[.5,.6,.75],'return_enabled':[0,1],'boats':[50,100,150],'weather':[.6,.75,.9],'start_day':[7,8,9]}.items():
        for value in vals:
            result=calculate(mutate(data,key,value))['totals']; sensitivity.append({'scenario_id':'EV-B-C02','changed_parameter':key,'changed_value':value,**result})
    write_csv(HERE/'sensitivity.csv',sensitivity)
    checks=test(data)
    (HERE/'python_tests.json').write_text(json.dumps({'model_id':data['model_id'],'tests':checks,'passed':len(checks),'failed':0},ensure_ascii=False,indent=2))
    print(json.dumps({'scenario_totals':[x['totals'] for x in results],'tests_passed':len(checks)},ensure_ascii=False))

if __name__=='__main__': main()
